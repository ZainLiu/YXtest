import datetime

from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from model_to_view.eq_mt_sub_task.schema import *
from model_to_view.eq_mt_sub_task.serializer import EMSTListSerializer, EMSTBaseSerializer
from models import YesOrNo, EMSTStatus, db
from models.maintenance_task import EquipmentMaintenanceSubTask
from module.eq_mt_sub_task.flow_service import FlowServiceEMST
from utils.code_util import CodeUtil
from utils.flow_decorator import flow_decorator
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class EMSTModule(ModuleBasic):
    """设备子任务"""

    @request_url(EMSTListSchema)
    def emst_list(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [EquipmentMaintenanceSubTask.is_assign == YesOrNo.YES,
                       EquipmentMaintenanceSubTask.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(EquipmentMaintenanceSubTask.serial_number == form_data["serial_number"])

        emst_set = EquipmentMaintenanceSubTask.query.filter(*filter_cond).order_by(
            EquipmentMaintenanceSubTask.id.desc()).paginate(form_data["page"],
                                                            form_data["size"])
        for emst in emst_set.items:
            emst.start_date = emst.emt.empd.start_date
            emst.end_date = emst.emt.empd.end_date

        resp_data = EMSTListSerializer(many=True).dump(emst_set.items)
        return self.report.table(resp_data, emst_set.total)

    @request_url(EMSTDetailSchema)
    def emst_detail(self, form_data):
        """维保子计划详情"""
        emst = EquipmentMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not emst:
            return self.report.error("相关数据不存在")
        resp_data = EMSTBaseSerializer().dump(emst)
        resp_data.update({
            "id": emst.id,
            "start_date": TimeUtil.get_date_str_from_date(emst.emt.empd.start_date),
            "end_date": TimeUtil.get_date_str_from_date(emst.emt.empd.end_date),
            "mt_date": TimeUtil.get_year_month_str_from_date(emst.mt_date),
            "leader_name": emst.emt.empd.emp.leader_name,
            "eq_sys_name": emst.equipment.equipment_type.equipment_sub_system.equipment_system.name,
            "eq_type": emst.equipment.equipment_type.name,
            "manufacturer": emst.equipment.manufacturer.name,
            "eq_model": emst.equipment.equipment_model,
            "supporting_file": emst.emt.empd.emi.supporting_file,
            "qa_requirement": emst.emt.empd.emi.qa_requirement,
            "eq_name": emst.equipment.name,
            "eq_full_code": CodeUtil.get_eq_full_code(emst.equipment),
            "eq_location": CodeUtil.get_eq_location(emst.equipment),
            "fill_data": emst.fill_data,
            "is_assign": emst.is_assign,
            "status": emst.status,
            "serial_number": emst.serial_number,
            "is_summary": emst.is_summary
        })
        return self.report.post(resp_data)

    @request_url(EMSTAcceptSchema)
    def emst_accept(self, form_data):
        emst = EquipmentMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()

        if not emst:
            return self.report.error("相关数据不存在")
        if emst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务处理人，无法受理")
        if emst.is_accept == YesOrNo.NO:
            emst.is_accept = YesOrNo.YES
        elif emst.status == EMSTStatus.Suspended:
            emst.status = EMSTStatus.Executing
        db.session.add(emst)
        db.session.commit()
        return self.report.suc("受理成功")

    @request_url(EMSTAcceptSchema)
    def emst_suspended(self, form_data):
        emst = EquipmentMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not emst:
            return self.report.error("相关数据不存在")
        if emst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务处理人，无法挂起")
        emst.status = EMSTStatus.Suspended
        db.session.add(emst)
        db.session.commit()
        return self.report.suc("挂起成功")

    @request_url(EMSTFinishSubmitSchema)
    def emst_finish_commit(self, form_data):
        """维保人员完成提交"""
        emst = EquipmentMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not emst:
            return self.report.error("相关数据不存在")
        if emst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务维护人员，填写表单")
        if emst.is_accept == YesOrNo.NO:
            return self.report.error("未受理任务不允许填写")
        if emst.status == EMSTStatus.Suspended:
            return self.report.error("已挂起的表单不允许填写")
        if emst.status == EMSTStatus.NotExecute:
            return self.report.error("不执行的表单不允许填写")
        for mt_item in form_data["fill_data"]["mt_items"]:
            for sub_item in mt_item["sub_items"]:
                if sub_item.get("value", None) == None:
                    return self.report.error("表单没填写完整禁止提交")
        emst.fill_data = form_data["fill_data"]

        now = datetime.date.today()
        if now <= emst.mt_date:
            emst.status = EMSTStatus.Completed

        elif now <= emst.emt.empd.end_time:
            emst.status = EMSTStatus.DelayComplete
        else:
            return self.report.error("已超过计划时间，不能再执行")

        db.session.add(emst)
        db.session.commit()

        return self.report.suc("提交成功")

    @request_url(EMSTSummarySchema)
    @flow_decorator(FlowServiceEMST)
    def emst_summary(self, form_data):
        """维保子任务总结"""
        emst = EquipmentMaintenanceSubTask.query.filter_by(id=form_data["id"]).first()
        if not emst:
            return self.report.error("相关数据不存在")
        if emst.is_summary:
            return self.report.error("总结只能提交一次")
        if emst.mt_operator_id != g.uid:
            return self.report.error("你不是该任务维护人员，不能填写总结")
        if emst.status not in EMSTStatus.CanSummary:
            return self.report.error("该表单还不能提交总结")
        emst.summary = form_data["summary"]
        emst.is_summary = YesOrNo.YES
        emst.annex = form_data["annex"]
        db.session.add(emst)
        db.session.commit()
        g.fid = emst.id
        return self.report.suc("提交总结成功")

emst_module = EMSTModule()
