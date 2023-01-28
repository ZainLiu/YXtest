from flask import current_app
from ly_kernel.db.BaseMarshmallow import *
from models.maintenance_task import EquipmentSubSystemMaintenanceSubTask
from utils.flow_base_serializer import WithBacklogSerializer, WithFlowDataStatusSerializer

"""序列化器"""


class ESSMSTBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    """设备子系统维保子任务列化器基类"""

    class Meta:
        model = EquipmentSubSystemMaintenanceSubTask

    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    mt_date = fields.DateTime(format=current_app.config['APP_MONTH_FORMAT'])


class ESSMSTListSerializer(ESSMSTBaseSerializer):
    """设备维保子任务列化器列表"""

    class Meta:
        exclude = ["fill_data"]

    start_date = fields.DateTime(format=current_app.config['APP_DATE_FORMAT'])
    end_date = fields.DateTime(format=current_app.config['APP_DATE_FORMAT'])
    eq_sys_name = fields.Method(serialize="get_eq_sys_name", dump_only=True)

    def get_eq_sys_name(self, obj):
        return obj.essmib.essmi.equipment_sub_system.equipment_system.name


class ESSMSTListInEMTSerializer(ESSMSTBaseSerializer):
    class Meta:
        exclude = ["fill_data"]

    batch_name = fields.Method(serialize="get_batch_name", dump_only=True)
    start_date = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    end_date = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])

    def get_batch_name(self, obj):
        return obj.essmib.name