from flask import current_app
from ly_kernel.db.BaseMarshmallow import *
from models.event import Event, EventProcessingDetail, EventSuspendedWorkflow
from utils.flow_base_serializer import WithBacklogSerializer, WithFlowDataStatusSerializer

"""序列化器"""


class EventBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    """设备子系统维保子任务列化器基类"""

    class Meta:
        model = Event

    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    eq_sys_name = fields.Method(serialize="get_eq_sys_name", dump_only=True)
    eq_sys_id = fields.Int()
    occur_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    real_recovery_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    solve_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])

    def get_eq_sys_name(self, obj):
        return obj.equipment_system.name


class EventListSerializer(EventBaseSerializer):
    """"""
    pass


class EventDetailSerializer(EventBaseSerializer):
    """事件详情序列化器"""
    pass


class EventProcessingDetailSerializer(BaseSQLAlchemyAutoSchema):
    """事件处理明细序列化器"""

    class Meta:
        model = EventProcessingDetail

    event_id = fields.Int()
    start_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    end_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])


class EventSuspendedWorkflowBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    """事件挂起"""

    class Meta:
        model = EventSuspendedWorkflow

    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])


class EventSuspendedWorkflowListSerializer(EventSuspendedWorkflowBaseSerializer):
    event_id = fields.Int()


class EventSuspendedWorkflowDetailSerializer(EventSuspendedWorkflowBaseSerializer):
    event = fields.Nested(EventDetailSerializer)


class EventListSimpleSerializer(BaseSQLAlchemyAutoSchema):
    """事件选项列表序列化器"""

    class Meta:
        model = Event

    eq_sys_name = fields.Method(serialize="get_eq_sys_name", dump_only=True)
    eq_sys_id = fields.Int()
    occur_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    real_recovery_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])

    def get_eq_sys_name(self, obj):
        return obj.equipment_system.name
