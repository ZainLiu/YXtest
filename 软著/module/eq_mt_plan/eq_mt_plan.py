import datetime

from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.eq_mt_plan.schema import *
from model_to_view.eq_mt_plan.serializer import EMPListSerializer, EMPDetailSerializer
from models import MaintenanceCycle, EquipmentStatus, db, FlowStatus
from models.equipment import Equipment
from models.maintenance_plan import EquipmentMaintenancePlan, EquipmentMaintenancePlanDetail
from module.eq_mt_plan.flow_service import FlowServiceEMP
from tasks.schedule_tasks import generate_emp
from utils.code_util import CodeUtil
from utils.flow_decorator import flow_decorator
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class EquipmentMaintenancePlanModule(ModuleBasic):

    @request_url(EMPListSchema)
    def eq_mt_plan_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentMaintenancePlan.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentMaintenancePlan.serial_number == form_data["serial_number"])
        if form_data.get("year"):
            filter_cond.append(
                EquipmentMaintenancePlan.mt_date >= datetime.date(year=form_data["year"], month=1, day=1))
            filter_cond.append(
                EquipmentMaintenancePlan.mt_date < datetime.date(year=form_data["year"] + 1, month=1, day=1))
        if form_data.get("leader_name"):
            filter_cond.append(EquipmentMaintenancePlan.leader_name == form_data["leader_name"])
        if form_data.get("eq_sys_id"):
            filter_cond.append(EquipmentMaintenancePlan.equipment_system_id == form_data["eq_sys_id"])
        emp_set = EquipmentMaintenancePlan.query.filter(*filter_cond).order_by(
            EquipmentMaintenancePlan.id.desc()).paginate(form_data["page"],
                                                         form_data["size"])
        data = EMPListSerializer(many=True).dump(emp_set.items)
        return self.report.table(data, emp_set.total)

    @request_url(EMPDetailSchema)
    def eq_mt_plan_detail(self, form_data):
        """
        获取维保计划详情
        """
        eqmp = EquipmentMaintenancePlan.query.filter_by(id=form_data["id"]).first()
        resp_data = EMPDetailSerializer().dump(eqmp)
        resp_data.update({
            "id": eqmp.id,
            "mt_date": eqmp.mt_date.strftime(current_app.config["APP_MONTH_FORMAT"]),
            "leader_name": eqmp.leader_name,
            "pg_name": eqmp.pg.name,
            "create_time": eqmp.create_time.strftime(current_app.config["APP_DATETIME_FORMAT"]),
            "cycle_detail_info": []
        })
        detail_set = eqmp.empd_set.all()
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
                    eq_model = detail.emi.equipment_model
                    eq_type = detail.emi.equipment_type
                    detail_info["detail_info"].append({
                        "id": detail.id,
                        "start_date": detail.start_date.strftime(
                            current_app.config["APP_DATE_FORMAT"]) if detail.start_date else None,
                        "end_date": detail.end_date.strftime(
                            current_app.config["APP_DATE_FORMAT"]) if detail.start_date else None,
                        "eq_model": eq_model,
                        "eq_type": eq_type.name,
                        "eq_sub_sys": detail.emi.equipment_type.equipment_sub_system.name,
                        "mt_eq_num": self.get_mt_eq_num(eqmp.data_center_id, eq_model)
                    })
                resp_data["cycle_detail_info"].append(detail_info)
        return self.report.post(resp_data)

    def get_mt_eq_num(self, dc_id, eq_model):
        cnt = Equipment.query.filter_by(data_center_id=dc_id, equipment_model=eq_model,
                                        status=EquipmentStatus.Using).count()
        return cnt

    @request_url(EMPDEquipmentListSchema)
    def get_mt_eq_detail(self, form_data):
        empd = EquipmentMaintenancePlanDetail.query.filter_by(id=form_data["id"]).first()
        eq_set = Equipment.query.filter_by(data_center_id=empd.emp.data_center_id,
                                           equipment_model=empd.emi.equipment_model,
                                           status=EquipmentStatus.Using).all()
        resp_data = []
        for eq in eq_set:
            resp_data.append({
                "id": eq.id,
                "full_code": CodeUtil.get_eq_full_code(eq),
                "location": CodeUtil.get_eq_location(eq)
            })
        return self.report.post(resp_data)

    @request_url(EMPDSaveSchema)
    def save_empd(self, form_data):
        emp = EquipmentMaintenancePlan.query.filter_by(id=form_data["id"]).first()
        if emp.leader_id != g.uid:
            return self.report.error("你不是该计划的负责人，不能操作该维保计划")
        if emp.flow_status not in FlowStatus.CAN_APPROVAL:
            return self.report.error("该计划非可编辑状态")
        try:
            for data in form_data["detail_info"]:
                empd = EquipmentMaintenancePlanDetail.query.filter_by(id=data["id"]).first()
                empd.start_date = TimeUtil.get_date_from_datetime_str(data["start_date"]) if data[
                    "start_date"] else None
                empd.end_date = TimeUtil.get_date_from_datetime_str(data["end_date"]) if data[
                    "start_date"] else None
                db.session.add(empd)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"更新失败：{e}")
        db.session.commit()
        return self.report.suc("更新成功")

    @request_url(EMPDSaveSchema)
    @flow_decorator(FlowServiceEMP)
    def submit_empd(self, form_data):
        emp = EquipmentMaintenancePlan.query.filter_by(id=form_data["id"]).first()
        if emp.leader_id != g.uid:
            return self.report.error("你不是该计划的负责人，不能操作该维保计划")
        if emp.flow_status not in FlowStatus.CAN_APPROVAL:
            return self.report.error("该计划非可编辑状态")
        for data in form_data["detail_info"]:
            if not data["start_date"] or not data["end_date"]:
                return self.report.error("请把日期填完再提交审批")
        try:
            for data in form_data["detail_info"]:
                empd = EquipmentMaintenancePlanDetail.query.filter_by(id=data["id"]).first()
                empd.start_date = TimeUtil.get_date_from_datetime_str(data["start_date"])
                empd.end_date = TimeUtil.get_date_from_datetime_str(data["end_date"])
                db.session.add(empd)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"更新失败：{e}")
        db.session.commit()
        g.fid = emp.id
        return self.report.suc("更新成功")

    def trigger_scheduled_task(self):
        generate_emp()
        return self.report.suc("触发成功")


emp_module = EquipmentMaintenancePlanModule()
