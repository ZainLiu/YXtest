import datetime
from ly_kernel.LieYing import LieYingApp
from flask import g
from models import FlowStatus, IsValid, YesOrNo, IsDraft, EventStatus, db
from models.event import Event, EventSuspendedWorkflow
from module.event.serializers.serializer import EventListSerializer, EventSuspendedWorkflowListSerializer
from utils.flow_base_service import FlowBaseService


class FlowServiceEvent(FlowBaseService):
    """维保子任务"""
    model = Event
    form_serialize = EventListSerializer
    serial_number = 'serial_number'
    form_name = '事件-事件完成审批'

    def flow_create_func(form_obj):
        """审批创建后钩子"""
        form_obj.flow_status = FlowStatus.OnGoing
        form_obj.last_editor_id = g.uid
        form_obj.is_draft = IsDraft.NORMAL

    def flow_pass_func(form_obj):
        """审批通过后钩子"""
        try:
            form_obj.current_approval_time = datetime.datetime.now()
            form_obj.is_valid = IsValid.Valid
            form_obj.is_lock = YesOrNo.NO
            form_obj.flow_status = FlowStatus.Done
            form_obj.last_editor_id = g.uid
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e
        LieYingApp.db.session.commit()

    def flow_refuse_func(form_obj):
        """审批拒绝后钩子"""
        form_obj.flow_status = FlowStatus.Reject
        form_obj.last_editor_id = g.uid

    def flow_revoke_func(form_obj):
        """审批撤销后钩子"""
        form_obj.flow_status = FlowStatus.WithDraw
        form_obj.last_editor_id = g.uid


class FlowServiceESW(FlowBaseService):
    """维保子任务"""
    model = EventSuspendedWorkflow
    form_serialize = EventSuspendedWorkflowListSerializer
    serial_number = 'serial_number'
    form_name = '事件-事件挂起'

    def flow_create_func(form_obj):
        """审批创建后钩子"""
        form_obj.flow_status = FlowStatus.OnGoing
        form_obj.last_editor_id = g.uid
        # 将事件置为挂起申请中状态
        event = form_obj.event
        event.status = EventStatus.Suspending
        db.session.add(event)

    def flow_pass_func(form_obj):
        """审批通过后钩子"""
        try:
            form_obj.current_approval_time = datetime.datetime.now()
            form_obj.is_valid = IsValid.Valid
            form_obj.is_lock = YesOrNo.NO
            form_obj.flow_status = FlowStatus.Done
            form_obj.last_editor_id = g.uid
            # 将事件置为挂起状态
            event = form_obj.event
            event.status = EventStatus.Suspended
            db.session.add(event)
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e
        LieYingApp.db.session.commit()

    def flow_refuse_func(form_obj):
        """审批拒绝后钩子"""
        form_obj.flow_status = FlowStatus.Reject
        form_obj.last_editor_id = g.uid

    def flow_revoke_func(form_obj):
        """审批撤销后钩子"""
        form_obj.flow_status = FlowStatus.WithDraw
        form_obj.last_editor_id = g.uid