from flask import current_app
from ly_kernel.db.BaseMarshmallow import *
from models.maintenance_plan_timetable import EquipmentSubSystemMtPlanTimetable
from utils.flow_base_serializer import WithBacklogSerializer, WithFlowDataStatusSerializer

"""序列化器"""


class ESSMPTBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    """维保计划时间表列表序列化器基类"""

    class Meta:
        model = EquipmentSubSystemMtPlanTimetable

    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    eq_sys_name = fields.Method(serialize="get_eq_sys_name", dump_only=True)

    def get_eq_sys_name(self, obj):
        return obj.eq_sys.name


class ESSMPTListSerializer(ESSMPTBaseSerializer):
    """维保计划时间表列表序列化器"""
    pass


class ESSMPTDetailSerializer(ESSMPTBaseSerializer):
    pass
