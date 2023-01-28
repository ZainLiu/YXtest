import datetime

from ly_kernel.LieYing import LieYingApp
from flask import g
from tasks.async_tasks import async_write_panel_data
from model_to_view.rostering_work_admin.serializer import WorkAdminListSerialize
from models import FlowStatus, IsValid, YesOrNo
from utils.flow_base_service import FlowBaseService
from models.rostering.work_admin import WorkAdmin


class FlowServiceWorkAdmin(FlowBaseService):
    model = WorkAdmin
    form_serialize = WorkAdminListSerialize
    serial_number = 'serial_number'
    form_name = '排班管理'

    def flow_create_func(form_obj):
        """审批创建后钩子"""
        form_obj.flow_status = FlowStatus.OnGoing
        form_obj.last_editor_id = g.uid

    def flow_pass_func(form_obj):
        """审批通过后钩子"""
        try:
            # 修改排班信息
            form_obj.current_approval_time = datetime.datetime.now()
            form_obj.is_valid = IsValid.Valid
            form_obj.flow_status = FlowStatus.Done
            form_obj.last_editor_id = g.uid

            async_write_panel_data.apply_async(args=(form_obj.id,), countdown=0, queue='async_task')


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
