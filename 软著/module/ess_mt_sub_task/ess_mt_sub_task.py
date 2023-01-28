import datetime

from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from models import YesOrNo, EMSTStatus, db
from models.maintenance_task import EquipmentSubSystemMaintenanceSubTask
from module.ess_mt_sub_task.flow_service import FlowServiceESSMST
from module.ess_mt_sub_task.serializers.schema import ESSMSTListSchema, ESSMSTDetailSchema, ESSMSTAcceptSchema, \
    ESSMSTFinishSubmitSchema, ESSMSTSummarySchema
from module.ess_mt_sub_task.serializers.serializer import ESSMSTListSerializer, ESSMSTBaseSerializer
from utils.code_util import CodeUtil
from utils.flow_decorator import flow_decorator
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class ESSMSTModule(ModuleBasic):
    """设备子系统维保子任务"""

    @request_url(ESSMSTListSchema)
    def essmst_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentSubSystemMaintenanceSubTask.is_assign == YesOrNo.YES,
                       EquipmentSubSystemMaintenanceSubTask.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentSubSystemMaintenanceSubTask.serial_number == form_data["serial_number"])

        essmst_set = EquipmentSubSystemMaintenanceSubTask.query.filter(*filter_cond).order_by(
            EquipmentSubSystemMaintenanceSubTask.id.desc()).paginate(form_data["page"],
                                                                     form_data["size"])
        for essmst in essmst_set.items:
            essmst.start_date = essmst.essmt.essmpd.start_date
            essmst.essnd_date = essmst.essmt.essmpd.end_date

        resp_data = ESSMSTListSerializer(many=True).dump(essmst_set.items)
        return self.report.table(resp_data, essmst_set.total)

    @request_url(ESSMSTDetailSchema)
    def essmst_detail(self, form_data):
        """维保子任务详情"""
        essmst = EquipmentSubSystemMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not essmst:
            return self.report.error("相关数据不存在")
        resp_data = ESSMSTBaseSerializer().dump(essmst)
        resp_data.update({
            "id": essmst.id,
            "start_date": TimeUtil.get_date_str_from_date(essmst.essmt.essmpd.start_date),
            "end_date": TimeUtil.get_date_str_from_date(essmst.essmt.essmpd.end_date),
            "mt_date": TimeUtil.get_year_month_str_from_date(essmst.mt_date),
            "leader_name": essmst.essmt.essmpd.essmp.leader_name,
            "eq_sys_name": essmst.essmib.essmi.equipment_sub_system.equipment_system.name,
            "eq_sub_sys_name": essmst.essmib.essmi.equipment_sub_system.name,
            "supporting_file": essmst.essmt.essmpd.essmi.supporting_file,
            "qa_requirement": essmst.essmt.essmpd.essmi.qa_requirement,
            "batch_name": essmst.essmib.name,
            "fill_data": essmst.fill_data,
            "is_assign": essmst.is_assign,
            "status": essmst.status,
            "serial_number": essmst.serial_number,
            "is_summary": essmst.is_summary
        })
        essmibe_set = essmst.essmib.essmibe_set.all()
        mt_eq_info_dict = dict()
        for essmibe in essmibe_set:
            eq = essmibe.equipment
            dcb = eq.data_center_building
            building_info = mt_eq_info_dict.get(dcb.id, {"name": dcb.name, "id": dcb.id, "floor_info": {}})
            dcf = eq.data_center_floor
            floor_info = building_info["floor_info"].get(dcf.id, {"name": dcf.name, "id": dcf.id, "room_info": {}})
            dcr = eq.data_center_room
            room_info = floor_info["room_info"].get(dcr.id, {"name": dcr.name, "id": dcr.id, "eq_info": []})
            room_info["eq_info"].append({
                "id": eq.id,
                "name": eq.name,
                "full_code": CodeUtil.get_eq_full_code(eq),
                "eq_type":eq.equipment_type.name
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
        resp_data["eq_info"] = eq_info
        return self.report.post(resp_data)

    @request_url(ESSMSTAcceptSchema)
    def essmst_accept(self, form_data):
        essmst = EquipmentSubSystemMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()

        if not essmst:
            return self.report.error("相关数据不存在")
        if essmst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务处理人，无法受理")
        if essmst.is_accept == YesOrNo.NO:
            essmst.is_accept = YesOrNo.YES
        elif essmst.status == EMSTStatus.Suspended:
            essmst.status = EMSTStatus.Executing
        db.session.add(essmst)
        db.session.commit()
        return self.report.suc("受理成功")

    @request_url(ESSMSTAcceptSchema)
    def essmst_suspended(self, form_data):
        essmst = EquipmentSubSystemMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not essmst:
            return self.report.error("相关数据不存在")
        if essmst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务处理人，无法挂起")
        essmst.status = EMSTStatus.Suspended
        db.session.add(essmst)
        db.session.commit()
        return self.report.suc("挂起成功")

    @request_url(ESSMSTFinishSubmitSchema)
    def essmst_finish_commit(self, form_data):
        """维保人员完成提交"""
        essmst = EquipmentSubSystemMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not essmst:
            return self.report.error("相关数据不存在")
        if essmst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务维护人员，填写表单")
        if essmst.is_accept == YesOrNo.NO:
            return self.report.error("未受理任务不允许填写")
        if essmst.status == EMSTStatus.Suspended:
            return self.report.error("已挂起的表单不允许填写")
        if essmst.status == EMSTStatus.NotExecute:
            return self.report.error("不执行的表单不允许填写")
        for mt_item in form_data["fill_data"]["mt_items"]:
            for sub_item in mt_item["sub_items"]:
                if sub_item.get("value", None) == None:
                    return self.report.error("表单没填写完整禁止提交")
        essmst.fill_data = form_data["fill_data"]

        now = datetime.date.today()
        if now <= essmst.mt_date:
            essmst.status = EMSTStatus.Completed

        elif now <= essmst.essmt.empd.end_time:
            essmst.status = EMSTStatus.DelayComplete
        else:
            return self.report.error("已超过计划时间，不能再执行")

        db.session.add(essmst)
        db.session.commit()

        return self.report.suc("提交成功")

    @request_url(ESSMSTSummarySchema)
    @flow_decorator(FlowServiceESSMST)
    def essmst_summary(self, form_data):
        """维保子任务总结"""
        essmst = EquipmentSubSystemMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not essmst:
            return self.report.error("相关数据不存在")
        if essmst.is_summary:
            return self.report.error("总结只能提交一次")
        if essmst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务维护人员，不能填写总结")
        if essmst.status not in EMSTStatus.CanSummary:
            return self.report.error("该表单还不能提交总结")
        essmst.summary = form_data["summary"]
        essmst.is_summary = YesOrNo.YES
        essmst.annex = form_data["annex"]
        db.session.add(essmst)
        db.session.commit()
        g.fid = essmst.id
        return self.report.suc("提交总结成功")


essmst_module = ESSMSTModule()
