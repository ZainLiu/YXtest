from flask import current_app
from ly_kernel.db.BaseMarshmallow import *

from models.maintenance_item import EquipmentSubSystemMaintenanceItem
from utils.flow_base_serializer import WithBacklogSerializer, WithFlowDataStatusSerializer

"""序列化器"""


class ESSMIBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    class Meta:
        model = EquipmentSubSystemMaintenanceItem

    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    end_time = fields.DateTime(format=current_app.config['APP_DATE_FORMAT'])
    version_no = fields.Method(serialize="get_version_no", dump_only=True)
    mt_cycle = fields.Method(serialize="get_mt_cycle", dump_only=True)

    equipment_sub_system_id = fields.Int()

    def get_version_no(self, obj):
        return f"v{obj.version_no}"

    def get_mt_cycle(self, obj):
        cycle_list = []
        if obj.monthly_template:
            cycle_list.append("月度（M）")
        if obj.quarterly_template:
            cycle_list.append("季度（Q）")
        if obj.semiannually_template:
            cycle_list.append("半年度（H）")
        if obj.annually_template:
            cycle_list.append("年度（Y）")
        return ";".join(cycle_list)


class ESSMIListSerializer(ESSMIBaseSerializer):
    """维保项目列表序列化器"""

    class Meta:
        exclude = ("monthly_template", "quarterly_template", "semiannually_template", "annually_template", "end_date",
                   "batch_conf")

    equipment_sub_system_name = fields.Method(serialize="get_eq_sub_sys_name", dump_only=True)


    def get_eq_sub_sys_name(self, obj):
        return f"{obj.equipment_sub_system.equipment_system.name}/{obj.equipment_sub_system.name}"



class ESSMIDetailSerializer(ESSMIBaseSerializer):
    """设备子系统维保项目详情序列化器"""
    equipment_sub_system_id = fields.Int()
    equipment_sub_system_name = fields.Method(serialize="get_eq_sub_sys_name", dump_only=True)
    supplier_id = fields.Int()
    supplier_name = fields.Method(serialize="get_supplier_name", dump_only=True)

    def get_supplier_name(self, obj):
        if obj.supplier_id:
            return obj.supplier.name
        else:
            return ""

    def get_eq_sub_sys_name(self, obj):
        return f"{obj.equipment_sub_system.equipment_system.name}/{obj.equipment_sub_system.name}"
