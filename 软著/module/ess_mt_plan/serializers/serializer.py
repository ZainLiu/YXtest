from models.maintenance_plan import EquipmentSubSystemMaintenancePlan
from flask import current_app
from ly_kernel.db.BaseMarshmallow import *

from models import MaintenanceCycle
from utils.flow_base_serializer import WithBacklogSerializer, WithFlowDataStatusSerializer


class ESSMPBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    """设备维保计划列化器基类"""

    class Meta:
        model = EquipmentSubSystemMaintenancePlan

    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    mt_date = fields.DateTime(format=current_app.config['APP_MONTH_FORMAT'])
    equipment_system_name = fields.Method(serialize="get_eq_sys_name")
    mt_cycle = fields.Method(serialize="get_mt_cycle")
    task_status = fields.Method(serialize="get_task_status")

    def get_eq_sys_name(self, obj):
        return obj.equipment_system.name

    def get_mt_cycle(self, obj):
        essmpd_set = obj.essmpd_set.all()
        period_list = [essmpd.period for essmpd in essmpd_set]
        period_cn_list = []
        for i in set(period_list):
            period_cn_list.append(MaintenanceCycle.TO_CN_DICT[i])
        return ";".join(period_cn_list)

    def get_task_status(self, obj):
        return "未执行"


class ESSMPListSerializer(ESSMPBaseSerializer):
    """设备维保计划列表列化器"""
    pass


class ESSMPDetailSerializer(ESSMPBaseSerializer):
    """设备维保计划列表列化器"""
    pass
