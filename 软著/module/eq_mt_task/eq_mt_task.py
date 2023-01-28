import traceback

from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.eq_mt_sub_task.serializer import EMSTListSerializer, EMSTListInEMTSerializer
from model_to_view.eq_mt_task.schema import EMTDetailSchema, EMTAssignSchema, EMTListSchema, EMSTReassignmentSchema
from models import MaintenanceCycle, YesOrNo, EMSTStatus, db, IsValid
from models.maintenance_task import EquipmentMaintenanceTask, EquipmentMaintenanceSubTask
from models.upcoming import Upcoming, UpcomingType
from utils.code_util import CodeUtil
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class EMTModule(ModuleBasic):
    """设备维维保任务"""

    @request_url(EMTDetailSchema)
    def emt_detail(self, form_data):
        emt = EquipmentMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not emt:
            return self.report.error("相关数据不存在")
        resp_data = {
            "id": emt.id,
            "start_date": emt.empd.start_date.strftime(current_app.config["APP_DATE_FORMAT"]),
            "end_date": emt.empd.end_date.strftime(current_app.config["APP_DATE_FORMAT"]),
            "mt_month": emt.empd.emp.mt_date.strftime(current_app.config["APP_MONTH_FORMAT"]),
            "leader_name": emt.empd.emp.leader_name,
            "serial_number": emt.serial_number,
            "mt_cycle": MaintenanceCycle.TO_CN_DICT[emt.empd.period],
            "eq_sys_name": emt.empd.emp.equipment_system.name,
            "eq_type_name": emt.empd.emi.equipment_type.name,
            "eq_model": emt.empd.emi.equipment_model,
            "qa_requirement": emt.empd.emi.qa_requirement,
            "supporting_file": emt.empd.emi.supporting_file
        }
        return self.report.post(resp_data)

    @request_url(EMTDetailSchema)
    def emt_equipment_list(self, form_data):
        emst_set = EquipmentMaintenanceSubTask.query.filter_by(emt_id=form_data["id"], is_assign=YesOrNo.NO).all()
        mt_eq_info_dict = dict()
        for emst in emst_set:
            eq = emst.equipment
            dcb = eq.data_center_building
            building_info = mt_eq_info_dict.get(dcb.id, {"name": dcb.name, "id": dcb.id, "floor_info": {}})
            dcf = emst.equipment.data_center_floor
            floor_info = building_info["floor_info"].get(dcf.id, {"name": dcf.name, "id": dcf.id, "room_info": {}})
            dcr = emst.equipment.data_center_room
            room_info = floor_info["room_info"].get(dcr.id, {"name": dcr.name, "id": dcr.id, "eq_info": []})
            room_info["eq_info"].append({
                "id": emst.id,
                "eq_id": eq.id,
                "name": eq.name,
                "full_code": CodeUtil.get_eq_full_code(eq),
                "mt_operator_id": emst.mt_operator_id,
                "mt_operator_name": emst.mt_operator_name,
                "mt_date": emst.mt_date.strftime(current_app.config['APP_DATE_FORMAT']) if emst.mt_date else None,
            })
            floor_info["room_info"][dcr.id] = room_info
            building_info["floor_info"][dcf.id] = floor_info
            mt_eq_info_dict[dcb.id] = building_info
        # 处理成前端能看懂的数据格式
        eq_info = []
        for building_id, building_info in mt_eq_info_dict.items():
            floors_info = []
            for floor_id, floor_info in building_info["floor_info"].items():
                rooms_info = []
                for _, room_info in floor_info["room_info"].items():
                    rooms_info.append(room_info)
                floor_info["room_info"] = rooms_info
                floors_info.append(floor_info)
            building_info["floor_info"] = floors_info
            eq_info.append(building_info)
        resp_data = eq_info
        return self.report.post(resp_data)

    @request_url(EMTDetailSchema)
    def emt_sub_task_list(self, form_data):
        emt = EquipmentMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not emt:
            return self.report.error("相关数据不存在")
        real_emst_set = EquipmentMaintenanceSubTask.query.filter(EquipmentMaintenanceSubTask.emt_id == emt.id,
                                                                 EquipmentMaintenanceSubTask.is_assign == YesOrNo.YES).all()
        for real_empt in real_emst_set:
            real_empt.start_date = emt.empd.start_date
            real_empt.end_date = emt.empd.end_date
        real_emst_data = EMSTListInEMTSerializer(many=True).dump(real_emst_set)
        resp_data = real_emst_data
        return self.report.post(resp_data)

    @request_url(EMTListSchema)
    def emt_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentMaintenanceTask.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentMaintenanceTask.serial_number == form_data["serial_number"])
        emt_set = EquipmentMaintenanceTask.query.filter(*filter_cond).order_by(
            EquipmentMaintenanceTask.id.desc()).paginate(form_data["page"],
                                                         form_data["size"])
        resp_data = []
        for emt in emt_set.items:
            resp_data.append({
                "id": emt.id,
                "serial_number": emt.serial_number,
                "eq_sys_name": emt.empd.emp.equipment_system.name,
                "mt_date": TimeUtil.get_year_month_str_from_date(emt.empd.emp.mt_date),
                "start_date": TimeUtil.get_date_str_from_date(emt.empd.start_date),
                "end_date": TimeUtil.get_date_str_from_date(emt.empd.end_date),
                "leader_name": emt.leader_name,
                "status": emt.status
            })
        return self.report.table(resp_data, emt_set.total)

    @request_url(EMTAssignSchema)
    def assign_mt_people(self, form_data):
        emt = EquipmentMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not emt:
            return self.report.error("暂无相关数据")
        if emt.leader_id != g.uid:
            return self.report.error("你不是该计划负责人，无法分配人员")
        for emst_info in form_data["assign_info"]:
            if not emst_info.get("mt_operator_id") or not emst_info.get("mt_operator_name") or not emst_info.get(
                    "mt_operator_name"):
                return self.report.error("请填写完整的信息再提交")
        try:
            for emst_info in form_data["assign_info"]:
                emst = EquipmentMaintenanceSubTask.query.filter_by(id=emst_info["id"]).first()
                emst.mt_operator_id = emst_info["mt_operator_id"]
                emst.mt_operator_name = emst_info["mt_operator_name"]
                emst.mt_date = emst_info["mt_date"]
                emst.creator_id = emst_info["mt_operator_id"]
                emst.creator_name = emst_info["mt_operator_name"]
                emst.belong_user_id = emst_info["mt_operator_id"]
                emst.belong_user_name = emst_info["mt_operator_name"]
                emst.is_assign = YesOrNo.YES
                db.session.add(emst)
                # 生成一条待办
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = emt.data_center_id
                upcoming_obj.upcoming_type = UpcomingType.FILL_MT_SUB_TASK
                upcoming_obj.title = f'填写维保子任务-{emst.serial_number}'
                upcoming_obj.form_code = EquipmentMaintenanceSubTask.__name__
                upcoming_obj.form_id = emst.id
                upcoming_obj.user_id = emst.creator_id
                db.session.add(upcoming_obj)
            # 维保任务置为执行中
            if emt.status == EMSTStatus.Unexecuted:
                emt.status = EMSTStatus.Executing
                db.session.add(emt)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"分配失败：原因：{str(e)}")
        db.session.commit()
        return self.report.suc("操作成功")

    @request_url(EMTDetailSchema)
    def get_people_list(self, form_data):
        emt = EquipmentMaintenanceTask.query.filter_by(id=form_data["id"]).first()
        if not emt:
            return self.report.error("暂无相关数据")
        people_set = emt.empd.emp.pg.member_set.all()
        resp_data = []
        for people in people_set:
            resp_data.append({
                "id": people.user_id,
                "name": people.user_name,
                "is_leader": people.is_leader
            })
        return self.report.post(resp_data)

    @request_url(EMSTReassignmentSchema)
    def emst_reassign(self, form_data):
        emst = EquipmentMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if emst.emt.leader_id != g.uid:
            return self.report.error("你不是该计划负责人，无法分配人员")
        if not emst:
            return self.report.error("查不到相关数据")
        if emst.is_accept:
            return self.report.error("已受理的维保子任务无法转派")
        if emst.mt_operator_id == form_data["user_id"]:
            return self.report.error("无法转派给本人")
        try:
            emst.mt_operator_id = form_data["user_id"]
            emst.mt_operator_name = form_data["user_name"]
            emst.creator_id = form_data["user_id"]
            emst.creator_name = form_data["user_name"]
            emst.belong_user_id = form_data["user_id"]
            emst.belong_user_name = form_data["user_name"]
            db.session.add(emst)
            # 删除旧待办，新增新待办
            old_upcoming = Upcoming.query.filter_by(form_id=emst.id, data_center_id=emst.data_center_id,
                                                    form_code=EquipmentMaintenanceSubTask.__name__,
                                                    upcoming_type=UpcomingType.FILL_MT_SUB_TASK,
                                                    is_valid=IsValid.Valid).first()
            if old_upcoming:
                old_upcoming.is_valid=IsValid.LoseValid
                db.session.add(old_upcoming)
            # 新增待办
            upcoming_obj = Upcoming()
            upcoming_obj.data_center_id = emst.data_center_id
            upcoming_obj.upcoming_type = UpcomingType.FILL_MT_SUB_TASK
            upcoming_obj.title = f'填写维保子任务-{emst.serial_number}'
            upcoming_obj.form_code = EquipmentMaintenanceSubTask.__name__
            upcoming_obj.form_id = emst.id
            upcoming_obj.user_id = emst.creator_id
            db.session.add(upcoming_obj)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"转派失败，原因：{traceback.print_exc()}")
        db.session.commit()
        return self.report.suc("转派成功")



emt_module = EMTModule()
