import datetime
from ly_kernel.LieYing import LieYingApp
from flask import g
from models import FlowStatus, IsValid, YesOrNo, IsActive
from utils.flow_base_service import FlowBaseService
from models.check.check_task import CheckTask
from model_to_view.check_task.serializer import CheckTaskListSerialize


class FlowServiceWorkExchange(FlowBaseService):
    model = CheckTask
    form_serialize = CheckTaskListSerialize
    serial_number = 'serial_number'
    form_name = '巡检任务'

    def flow_create_func(form_obj):
        """审批创建后钩子"""
        form_obj.flow_status = FlowStatus.OnGoing
        form_obj.last_editor_id = g.uid

    def flow_pass_func(form_obj):
        """审批通过后钩子"""
        try:
            # 修改巡检任务信息
            form_obj.current_approval_time = datetime.datetime.now()
            form_obj.is_valid = IsValid.Valid
            form_obj.flow_status = FlowStatus.Done
            form_obj.is_lock = YesOrNo.NO
            form_obj.last_editor_id = g.uid

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

    def flow_refuse_func(form_obj):
        """审批拒绝后钩子"""
        form_obj.flow_status = FlowStatus.Reject
        form_obj.last_editor_id = g.uid

    def flow_revoke_func(form_obj):
        """审批撤销后钩子"""
        form_obj.flow_status = FlowStatus.WithDraw
        form_obj.last_editor_id = g.uid
