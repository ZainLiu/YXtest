import datetime
import traceback

from flask import current_app, g
from ly_kernel.Module import ModuleBasic, request_url

from models import MaintenanceCycle, YesOrNo, db, EMSTStatus, IsValid
from models.maintenance_plan import EquipmentSubSystemMaintenancePlanDetail, EquipmentSubSystemMaintenancePlan
from models.maintenance_task import EquipmentSubSystemMaintenanceTask, EquipmentSubSystemMaintenanceSubTask
from models.upcoming import Upcoming, UpcomingType
from module.ess_mt_sub_task.serializers.serializer import ESSMSTListInEMTSerializer
from module.ess_mt_task.serializers.schema import ESSMTDetailSchema, ESSMTListSchema, ESSMTAssignSchema, \
    ESSMSTReassignmentSchema
from utils.code_util import CodeUtil
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class ESSMTModule(ModuleBasic):
    """设备子系统维维保任务"""

    @request_url(ESSMTDetailSchema)
    def essmt_detail(self, form_data):
        essmt = EquipmentSubSystemMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not essmt:
            return self.report.error("相关数据不存在")
        resp_data = {
            "id": essmt.id,
            "start_date": essmt.essmpd.start_date.strftime(current_app.config["APP_DATE_FORMAT"]),
            "end_date": essmt.essmpd.end_date.strftime(current_app.config["APP_DATE_FORMAT"]),
            "mt_month": essmt.essmpd.essmp.mt_date.strftime(current_app.config["APP_MONTH_FORMAT"]),
            "leader_name": essmt.essmpd.essmp.leader_name,
            "serial_number": essmt.serial_number,
            "mt_cycle": MaintenanceCycle.TO_CN_DICT[essmt.essmpd.period],
            "eq_sys_name": essmt.essmpd.essmp.equipment_system.name,
            "eq_sub_sys_name": essmt.essmpd.essmi.equipment_sub_system.name,
            "qa_requirement": essmt.essmpd.essmi.qa_requirement,
            "supporting_file": essmt.essmpd.essmi.supporting_file
        }
        return self.report.post(resp_data)

    @request_url(ESSMTDetailSchema)
    def essmt_batch_equipment_list(self, form_data):
        essmst_set = EquipmentSubSystemMaintenanceSubTask.query.filter_by(essmt_id=form_data["id"],
                                                                          is_assign=YesOrNo.NO).all()
        resp_data = []
        for essmst in essmst_set:
            batch = essmst.essmib
            batch_info = {
                "id": batch.id,
                "name": batch.name,
                "total_num": batch.essmibe_set.count(),
                "eq_info": []
            }
            for batch_eq in batch.essmibe_set.all():
                batch_info["eq_info"].append({
                    "id": batch_eq.equipment_id,
                    "eq_type_name": batch_eq.equipment.equipment_type.name,
                    "full_code": CodeUtil.get_eq_full_code(batch_eq.equipment),
                    "name": batch_eq.equipment.name,
                    "location": CodeUtil.get_eq_location(batch_eq.equipment)
                })
            resp_data.append(batch_info)
        return self.report.post(resp_data)

    @request_url(ESSMTDetailSchema)
    def essmt_sub_task_list(self, form_data):
        essmt = EquipmentSubSystemMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not essmt:
            return self.report.error("相关数据不存在")
        real_essmst_set = EquipmentSubSystemMaintenanceSubTask.query.filter(
            EquipmentSubSystemMaintenanceSubTask.essmt_id == essmt.id,
            EquipmentSubSystemMaintenanceSubTask.is_assign == YesOrNo.YES).all()
        for real_empt in real_essmst_set:
            real_empt.start_date = essmt.essmpd.start_date
            real_empt.end_date = essmt.essmpd.end_date
        real_emst_data = ESSMSTListInEMTSerializer(many=True).dump(real_essmst_set)
        resp_data = real_emst_data
        return self.report.post(resp_data)

    @request_url(ESSMTListSchema)
    def essmt_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentSubSystemMaintenanceTask.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentSubSystemMaintenanceTask.serial_number == form_data["serial_number"])
        if form_data.get("year_month"):
            date_list = form_data["year_month"].split("-")
            filter_cond.append(
                EquipmentSubSystemMaintenancePlan.mt_date == datetime.date(year=int(date_list[0]),
                                                                           month=int(date_list[1]),
                                                                           day=1))
        if form_data.get("eq_sys_id"):
            filter_cond.append(EquipmentSubSystemMaintenancePlan.equipment_system_id == form_data["eq_sys_id"])
        essmt_set = EquipmentSubSystemMaintenanceTask.query.join(EquipmentSubSystemMaintenancePlanDetail,
                                                                 EquipmentSubSystemMaintenancePlan).filter(
            *filter_cond).order_by(
            EquipmentSubSystemMaintenanceTask.id.desc()).paginate(form_data["page"],
                                                                  form_data["size"])
        resp_data = []
        for essmt in essmt_set.items:
            resp_data.append({
                "id": essmt.id,
                "serial_number": essmt.serial_number,
                "eq_sys_name": essmt.essmpd.essmp.equipment_system.name,
                "mt_date": TimeUtil.get_date_str_from_date(essmt.essmpd.essmp.mt_date),
                "start_date": TimeUtil.get_date_str_from_date(essmt.essmpd.start_date),
                "end_date": TimeUtil.get_date_str_from_date(essmt.essmpd.end_date),
                "leader_name": essmt.leader_name,
                "status": essmt.status
            })
        return self.report.table(resp_data, essmt_set.total)

    @request_url(ESSMTDetailSchema)
    def get_people_list(self, form_data):
        essmt = EquipmentSubSystemMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not essmt:
            return self.report.error("暂无相关数据")
        people_set = essmt.essmpd.essmp.pg.member_set.all()
        resp_data = []
        for people in people_set:
            resp_data.append({
                "id": people.user_id,
                "name": people.user_name,
                "is_leader": people.is_leader
            })
        return self.report.post(resp_data)

    @request_url(ESSMTAssignSchema)
    def assign_ess_mt_people(self, form_data):
        essmt = EquipmentSubSystemMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not essmt:
            return self.report.error("暂无相关数据")
        if essmt.leader_id != g.uid:
            return self.report.error("你不是该计划负责人，无法分配人员")
        for essmst_info in form_data["assign_info"]:
            if not essmst_info.get("mt_operator_id") or not essmst_info.get("mt_operator_name") or not essmst_info.get(
                    "mt_date"):
                return self.report.error("请填写完整的信息再提交")
        try:
            for essmst_info in form_data["assign_info"]:
                essmst = EquipmentSubSystemMaintenanceSubTask.query.filter_by(id=essmst_info["id"]).first()
                essmst.mt_operator_id = essmst_info["mt_operator_id"]
                essmst.mt_operator_name = essmst_info["mt_operator_name"]
                essmst.mt_date = essmst_info["mt_date"]
                essmst.creator_id = essmst_info["mt_operator_id"]
                essmst.creator_name = essmst_info["mt_operator_name"]
                essmst.belong_user_id = essmst_info["mt_operator_id"]
                essmst.belong_user_name = essmst_info["mt_operator_name"]
                essmst.is_assign = YesOrNo.YES
                db.session.add(essmst)
                # 生成一条待办
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = essmt.data_center_id
                upcoming_obj.upcoming_type = UpcomingType.FILL_MT_SUB_TASK
                upcoming_obj.title = f'填写设备子系统维保子任务-{essmst.serial_number}'
                upcoming_obj.form_code = EquipmentSubSystemMaintenanceSubTask.__name__
                upcoming_obj.form_id = essmst.id
                upcoming_obj.user_id = essmst.creator_id
                db.session.add(upcoming_obj)
            # 维保任务置为执行中
            if essmt.status == EMSTStatus.Unexecuted:
                essmt.status = EMSTStatus.Executing
                db.session.add(essmt)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"分配失败：原因：{str(e)}")
        db.session.commit()
        return self.report.suc("操作成功")

    @request_url(ESSMSTReassignmentSchema)
    def essmst_reassign(self, form_data):
        essmst = EquipmentSubSystemMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if essmst.essmt.leader_id != g.uid:
            return self.report.error("你不是该计划负责人，无法分配人员")
        if not essmst:
            return self.report.error("查不到相关数据")
        if essmst.is_accept:
            return self.report.error("已受理的维保子任务无法转派")
        if essmst.mt_operator_id == form_data["user_id"]:
            return self.report.error("无法转派给本人")
        try:
            essmst.mt_operator_id = form_data["user_id"]
            essmst.mt_operator_name = form_data["user_name"]
            essmst.creator_id = form_data["user_id"]
            essmst.creator_name = form_data["user_name"]
            essmst.belong_user_id = form_data["user_id"]
            essmst.belong_user_name = form_data["user_name"]
            db.session.add(essmst)
            # 删除旧待办，新增新待办
            old_upcoming = Upcoming.query.filter_by(form_id=essmst.id, data_center_id=essmst.data_center_id,
                                                    form_code=EquipmentSubSystemMaintenanceSubTask.__name__,
                                                    upcoming_type=UpcomingType.FILL_MT_SUB_TASK,
                                                    is_valid=IsValid.Valid).first()
            if old_upcoming:
                old_upcoming.is_valid = IsValid.LoseValid
                db.session.add(old_upcoming)
            # 新增待办
            upcoming_obj = Upcoming()
            upcoming_obj.data_center_id = essmst.data_center_id
            upcoming_obj.upcoming_type = UpcomingType.FILL_MT_SUB_TASK
            upcoming_obj.title = f'填写维保子任务-{essmst.serial_number}'
            upcoming_obj.form_code = EquipmentSubSystemMaintenanceSubTask.__name__
            upcoming_obj.form_id = essmst.id
            upcoming_obj.user_id = essmst.creator_id
            db.session.add(upcoming_obj)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"转派失败，原因：{traceback.print_exc()}")
        db.session.commit()
        return self.report.suc("转派成功")


essmt_module = ESSMTModule()
