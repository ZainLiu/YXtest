import datetime

from flask import current_app, g
from ly_kernel.Module import ModuleBasic, request_url

from models import MaintenanceCycle, EquipmentStatus, FlowStatus, db
from models.equipment import Equipment, EquipmentType, EquipmentSubSystem
from models.maintenance_plan import EquipmentSubSystemMaintenancePlan, EquipmentSubSystemMaintenancePlanDetail
from module.ess_mt_plan.flow_service import FlowServiceESSMP
from module.ess_mt_plan.serializers.schema import ESSMPListSchema, ESSMPDetailSchema, ESSMPDSaveSchema
from module.ess_mt_plan.serializers.serializer import ESSMPListSerializer, ESSMPDetailSerializer
from tasks.schedule_tasks import generate_essmp
from utils.flow_decorator import flow_decorator
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class EquipmentSubSystemMaintenancePlanModule(ModuleBasic):

    def trigger_scheduled_task(self):
        generate_essmp()
        return self.report.suc("触发成功")

    @request_url(ESSMPListSchema)
    def essmp_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentSubSystemMaintenancePlan.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentSubSystemMaintenancePlan.serial_number == form_data["serial_number"])
        if form_data.get("year"):
            filter_cond.append(
                EquipmentSubSystemMaintenancePlan.mt_date >= datetime.date(year=form_data["year"], month=1, day=1))
            filter_cond.append(
                EquipmentSubSystemMaintenancePlan.mt_date < datetime.date(year=form_data["year"] + 1, month=1, day=1))
        if form_data.get("leader_name"):
            filter_cond.append(EquipmentSubSystemMaintenancePlan.leader_name == form_data["leader_name"])
        if form_data.get("eq_sys_id"):
            filter_cond.append(EquipmentSubSystemMaintenancePlan.equipment_system_id == form_data["eq_sys_id"])
        essmp_set = EquipmentSubSystemMaintenancePlan.query.filter(*filter_cond).order_by(
            EquipmentSubSystemMaintenancePlan.id.desc()).paginate(form_data["page"],
                                                                  form_data["size"])
        data = ESSMPListSerializer(many=True).dump(essmp_set.items)
        return self.report.table(data, essmp_set.total)

    @request_url(ESSMPDetailSchema)
    def essmp_detail(self, form_data):
        """
        获取维保计划详情
        """
        essmp = EquipmentSubSystemMaintenancePlan.query.filter_by(id=form_data["id"]).first()
        resp_data = ESSMPDetailSerializer().dump(essmp)
        resp_data.update({
            "id": essmp.id,
            # "eq_sys_name": essmp.equipment_system.name,
            "mt_date": essmp.mt_date.strftime(current_app.config["APP_MONTH_FORMAT"]),
            "leader_name": essmp.leader_name,
            "pg_name": essmp.pg.name,
            "create_time": essmp.create_time.strftime(current_app.config["APP_DATETIME_FORMAT"]),
            "cycle_detail_info": []
        })
        detail_set = essmp.essmpd_set.all()
        temp_data = {
            MaintenanceCycle.Monthly: [],
            MaintenanceCycle.Quarterly: [],
            MaintenanceCycle.SemiAnnually: [],
            MaintenanceCycle.Annually: []
        }
        for detail in detail_set:
            temp_data[detail.period].append(detail)
        for key, value in temp_data.items():
            if value:
                detail_info = {
                    "cycle": key,
                    # "period_name": MaintenanceCycle.TO_CN_DICT[key],
                    "detail_info": []
                }
                for detail in value:
                    eq_sub_sys = detail.essmi.equipment_sub_system
                    detail_info["detail_info"].append({
                        "id": detail.id,
                        "start_date": detail.start_date.strftime(
                            current_app.config["APP_DATE_FORMAT"]) if detail.start_date else None,
                        "end_date": detail.end_date.strftime(
                            current_app.config["APP_DATE_FORMAT"]) if detail.start_date else None,
                        "eq_sub_sys": eq_sub_sys.name,
                        "mt_eq_num": self.get_mt_eq_num(essmp.data_center_id, eq_sub_sys.id),
                        "batch_num": detail.essmi.essmib_set.count()
                    })
                resp_data["cycle_detail_info"].append(detail_info)
        return self.report.post(resp_data)

    def get_mt_eq_num(self, dc_id, eq_sub_sys_id):
        cnt = Equipment.query.join(EquipmentType, EquipmentSubSystem).filter(Equipment.data_center_id == dc_id,
                                                                             EquipmentSubSystem.id == eq_sub_sys_id,
                                                                             Equipment.status == EquipmentStatus.Using).count()
        return cnt

    @request_url(ESSMPDSaveSchema)
    def save_empd(self, form_data):
        emp = EquipmentSubSystemMaintenancePlan.query.filter_by(id=form_data["id"]).first()
        if emp.leader_id != g.uid:
            return self.report.error("你不是该计划的负责人，不能操作该维保计划")
        if emp.flow_status not in FlowStatus.CAN_APPROVAL:
            return self.report.error("该计划非可编辑状态")
        try:
            for data in form_data["detail_info"]:
                essmpd = EquipmentSubSystemMaintenancePlanDetail.query.filter_by(id=data["id"]).first()
                essmpd.start_date = TimeUtil.get_date_from_datetime_str(data["start_date"]) if data[
                    "start_date"] else None
                essmpd.end_date = TimeUtil.get_date_from_datetime_str(data["end_date"]) if data[
                    "start_date"] else None
                db.session.add(essmpd)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"更新失败：{e}")
        db.session.commit()
        return self.report.suc("更新成功")

    @request_url(ESSMPDSaveSchema)
    @flow_decorator(FlowServiceESSMP)
    def submit_empd(self, form_data):
        emp = EquipmentSubSystemMaintenancePlan.query.filter_by(id=form_data["id"]).first()
        if emp.leader_id != g.uid:
            return self.report.error("你不是该计划的负责人，不能操作该维保计划")
        if emp.flow_status not in FlowStatus.CAN_APPROVAL:
            return self.report.error("该计划非可编辑状态")
        for data in form_data["detail_info"]:
            if not data["start_date"] or not data["end_date"]:
                return self.report.error("请把日期填完再提交审批")
        try:
            for data in form_data["detail_info"]:
                essmpd = EquipmentSubSystemMaintenancePlanDetail.query.filter_by(id=data["id"]).first()
                essmpd.start_date = TimeUtil.get_date_from_datetime_str(data["start_date"])
                essmpd.end_date = TimeUtil.get_date_from_datetime_str(data["end_date"])
                db.session.add(essmpd)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"更新失败：{e}")
        db.session.commit()
        g.fid = emp.id
        return self.report.suc("更新成功")


essmp_module = EquipmentSubSystemMaintenancePlanModule()
