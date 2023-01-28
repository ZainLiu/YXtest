from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from models import FlowStatus, db, IsActive
from models.maintenance_plan_timetable import EquipmentSubSystemMtPlanTimetable, EquipmentSubSystemMtPlanTimetableDetail
from models.rostering.people_group import PeopleGroup, GroupType
from module.ess_mt_plan_timetable.flow_service import FlowServiceESSMPT
from module.ess_mt_plan_timetable.serializers.schema import ESSMPTSaveSchema, ESSMPTListSchema, ESSMPTDetailSchema
from module.ess_mt_plan_timetable.serializers.serializer import ESSMPTListSerializer, ESSMPTDetailSerializer
from utils.flow_decorator import flow_decorator
from utils.injection_data import set_creator_and_belong_user_info
from utils.rpc_func import get_user_current_data_center_id
from utils.serial_number_service import get_serial_number_with_dc_code


class EquipmentSubSystemMtPlanTimetableModule(ModuleBasic):

    def essmpt_save_or_create(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        if not form_data.get("detail_info"):
            return self.report.error("detail_info不能为空")
        try:
            if form_data.get("id"):
                essmpt = EquipmentSubSystemMtPlanTimetable.query.filter_by(id=form_data["id"]).first()
                if essmpt.flow_status not in FlowStatus.CAN_APPROVAL:
                    return self.report.error("非草稿状态下禁止提交修改")
                for detail in form_data["detail_info"]:
                    essmptd = EquipmentSubSystemMtPlanTimetableDetail.query.filter_by(id=detail["id"]).first()
                    essmptd.conf_info = detail["conf_info"]
                    db.session.add(essmptd)

            else:
                essmpt = EquipmentSubSystemMtPlanTimetable()
                essmpt.serial_number = get_serial_number_with_dc_code(EquipmentSubSystemMtPlanTimetable, "WBSJBS",
                                                                      dc_id)
                essmpt.leader_id = g.uid
                essmpt.leader_name = g.account
                essmpt.pg_id = form_data["pg_id"]
                essmpt.year = form_data["year"]
                essmpt.mark = form_data["mark"]
                essmpt.annex = form_data["annex"]
                essmpt.data_center_id = dc_id
                essmpt.eq_sys_id = form_data["eq_sys_id"]
                # essmpt.flow_status = FlowStatus.Draft
                set_creator_and_belong_user_info(essmpt)
                db.session.add(essmpt)
                db.session.flush()
                for detail in form_data["detail_info"]:
                    essmptd = EquipmentSubSystemMtPlanTimetableDetail()
                    essmptd.essmi_id = detail["essmi_id"]
                    essmptd.essmpt_id = essmpt.id
                    essmptd.conf_info = detail["conf_info"]
                    db.session.add(essmptd)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"保存失败，错误信息：{e}")
        db.session.commit()
        g.fid = essmpt.id
        return self.report.suc("保存成功")

    @request_url(ESSMPTSaveSchema)
    def essmpt_save(self, form_data):
        return self.essmpt_save_or_create(form_data)

    @request_url(ESSMPTSaveSchema)
    @flow_decorator(FlowServiceESSMPT)
    def essmpt_submit(self, form_data):
        return self.essmpt_save_or_create(form_data)

    @request_url(ESSMPTListSchema)
    def essmpt_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        filter_cond = [EquipmentSubSystemMtPlanTimetable.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentSubSystemMtPlanTimetable.serial_number == form_data["serial_number"])
        if form_data.get("year"):
            filter_cond.append(EquipmentSubSystemMtPlanTimetable.year == form_data["year"])
        if form_data.get("leader_name"):
            filter_cond.append(EquipmentSubSystemMtPlanTimetable.leader_name == form_data["leader_name"])
        if form_data.get("eq_sys_id"):
            filter_cond.append(EquipmentSubSystemMtPlanTimetable.eq_sys_id == form_data["eq_sys_id"])
        essmpt_set = EquipmentSubSystemMtPlanTimetable.query.filter(*filter_cond).order_by(
            EquipmentSubSystemMtPlanTimetable.id.desc()).paginate(form_data["page"],
                                                                  form_data["size"])
        data = ESSMPTListSerializer(many=True).dump(essmpt_set.items)
        return self.report.table(data, essmpt_set.total)

    def essmpt_userinfo(self):
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

    @request_url(ESSMPTDetailSchema)
    def essmpt_detail(self, form_data):
        essmpt = EquipmentSubSystemMtPlanTimetable.query.filter_by(id=form_data["id"]).first()
        if not essmpt:
            return self.report.error("相关数据不存在")
        resp_data = ESSMPTDetailSerializer().dump(essmpt)
        resp_data["eq_sys_name"] = essmpt.eq_sys.name
        resp_data["pg_name"] = essmpt.pg.name
        resp_data["pg_id"] = essmpt.pg.id
        essmptd_info = []
        for essmptd in essmpt.essmptd_set.all():
            essmptd_info.append({
                "id": essmptd.id,
                "essmi_id": essmptd.essmi.id,
                "mt_serial_number": essmptd.essmi.serial_number,
                "mt_type": essmptd.essmi.mt_type,
                "conf_info": essmptd.conf_info
            })
        resp_data["detail_info"] = essmptd_info
        return self.report.post(resp_data)


essmpt_module = EquipmentSubSystemMtPlanTimetableModule()
