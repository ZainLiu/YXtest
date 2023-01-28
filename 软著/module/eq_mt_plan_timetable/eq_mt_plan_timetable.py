from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.eq_mt_timetable.schema import EMPTSaveSchema, EMPTListSchema, EMPTDetailSchema
from model_to_view.eq_mt_timetable.serializer import EMPTListSerializer, EMPTDetailSerializer
from models import FlowStatus, IsActive, db
from models.maintenance_plan_timetable import EquipmentMtPlanTimetable, EquipmentMtPlanTimetableDetail
from models.rostering.people_group import PeopleGroup, GroupType
from module.eq_mt_plan_timetable.flow_service import FlowServiceEMPT
from utils.flow_decorator import flow_decorator
from utils.injection_data import set_creator_and_belong_user_info
from utils.rpc_func import get_user_current_data_center_id
from utils.serial_number_service import get_serial_number_with_dc_code


class EquipmentMtPlanTimetableModule(ModuleBasic):

    def save_eq_mt_plan_time_table(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        if not form_data.get("detail_info"):
            return self.report.error("detail_info不能为空")
        try:
            if form_data.get("id"):
                empt = EquipmentMtPlanTimetable.query.filter_by(id=form_data["id"]).first()
                if empt.flow_status not in FlowStatus.CAN_APPROVAL:
                    return self.report.error("非草稿状态下禁止提交修改")
                for detail in form_data["detail_info"]:
                    emptd = EquipmentMtPlanTimetableDetail.query.filter_by(id=detail["id"]).first()
                    emptd.conf_info = detail["conf_info"]
                    db.session.add(emptd)

            else:
                empt = EquipmentMtPlanTimetable()
                empt.serial_number = get_serial_number_with_dc_code(EquipmentMtPlanTimetable, "WBSJBM", dc_id)
                empt.leader_id = g.uid
                empt.leader_name = g.account
                empt.pg_id = form_data["pg_id"]
                empt.year = form_data["year"]
                empt.mark = form_data["mark"]
                empt.annex = form_data["annex"]
                empt.data_center_id = dc_id
                empt.eq_sys_id = form_data["eq_sys_id"]
                # empt.flow_status = FlowStatus.Draft
                set_creator_and_belong_user_info(empt)
                db.session.add(empt)
                db.session.flush()
                for detail in form_data["detail_info"]:
                    emptd = EquipmentMtPlanTimetableDetail()
                    emptd.emi_id = detail["emi_id"]
                    emptd.empt_id = empt.id
                    emptd.conf_info = detail["conf_info"]
                    db.session.add(emptd)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"保存失败，错误信息：{e}")
        db.session.commit()
        g.fid = empt.id
        return self.report.suc("保存成功")

    @request_url(EMPTSaveSchema)
    def empt_save(self, form_data):
        return self.save_eq_mt_plan_time_table(form_data)

    @request_url(EMPTSaveSchema)
    @flow_decorator(FlowServiceEMPT)
    def empt_submit(self, form_data):
        return self.save_eq_mt_plan_time_table(form_data)

    @request_url(EMPTListSchema)
    def empt_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        filter_cond = [EquipmentMtPlanTimetable.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentMtPlanTimetable.serial_number == form_data["serial_number"])
        if form_data.get("year"):
            filter_cond.append(EquipmentMtPlanTimetable.year == form_data["year"])
        if form_data.get("leader_name"):
            filter_cond.append(EquipmentMtPlanTimetable.leader_name == form_data["leader_name"])
        if form_data.get("eq_sys_id"):
            filter_cond.append(EquipmentMtPlanTimetable.eq_sys_id == form_data["eq_sys_id"])

        empt_set = EquipmentMtPlanTimetable.query.filter(*filter_cond).order_by(
            EquipmentMtPlanTimetable.id.desc()).paginate(form_data["page"],
                                                         form_data["size"])
        data = EMPTListSerializer(many=True).dump(empt_set.items)
        return self.report.table(data, empt_set.total)

    def empt_userinfo(self):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        pg = PeopleGroup.query.filter_by(leader_id=g.uid, type=GroupType.Major, is_active=IsActive.Active,
                                         data_center_id=dc_id).first()
        if not pg:
            return self.report.error("你还不是该数据中心的任何系统专业组的负责人，无权发起年度维保计划")
        resp_data = {
            "leader_id": pg.leader_id,
            "leader_name": pg.leader_name,
            "group_name": pg.name,
            "group_id": pg.id,
            "eq_sys_name": pg.equipment_system.name,
            "eq_sys_id": pg.equipment_system_id
        }
        return self.report.post(resp_data)

    @request_url(EMPTDetailSchema)
    def empt_detail(self, form_data):
        empt = EquipmentMtPlanTimetable.query.filter_by(id=form_data["id"]).first()
        if not empt:
            return self.report.error("相关数据不存在")
        resp_data = EMPTDetailSerializer().dump(empt)
        resp_data["eq_sys_name"] = empt.eq_sys.name
        resp_data["pg_name"] = empt.pg.name
        resp_data["pg_id"] = empt.pg.id
        emptd_info = []
        for emptd in empt.emptd_set.all():
            emptd_info.append({
                "id": emptd.id,
                "emi_id": emptd.emi.id,
                "mt_serial_number": emptd.emi.serial_number,
                "mt_type": emptd.emi.mt_type,
                "conf_info": emptd.conf_info
            })
        resp_data["detail_info"] = emptd_info
        return self.report.post(resp_data)


empt_module = EquipmentMtPlanTimetableModule()
