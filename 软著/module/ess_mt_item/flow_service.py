import datetime
from ly_kernel.LieYing import LieYingApp
from flask import g

from model_to_view.eq_mt_item.serializer import EMIListSerializer
from models import FlowStatus, IsValid, YesOrNo, MaintenanceItemStatus, IsDraft, IsActive
from models.maintenance_item import EquipmentMaintenanceItem, EquipmentSubSystemMaintenanceItem, EssmiBatch, \
    EssmiBatchEquipment
from module.ess_mt_item.serializers.serializer import ESSMIListSerializer
from utils.flow_base_service import FlowBaseService


class FlowServiceESSMI(FlowBaseService):
    """合同管理：新增、续签、变更、修改"""
    model = EquipmentSubSystemMaintenanceItem
    form_serialize = ESSMIListSerializer
    serial_number = 'serial_number'
    form_name = '维保-设备子系统维保项目'

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

            # 将旧的生效的模板置为失效,审批通过的置为生效
            EquipmentSubSystemMaintenanceItem.query.filter(EquipmentSubSystemMaintenanceItem.id != form_obj.id,
                                                           EquipmentSubSystemMaintenanceItem.serial_number == form_obj.serial_number,
                                                           EquipmentSubSystemMaintenanceItem.status == IsActive.Active).update(
                {"status": IsActive.Disable})
            form_obj.status = IsActive.Active

            # 创建批次相关信息
            for batch in form_obj.batch_conf:
                eb = EssmiBatch()
                eb.essmi_id = form_obj.id
                eb.name = batch["name"]
                LieYingApp.db.session.add(eb)
                LieYingApp.db.session.flush()
                for eq in batch.get("eq_info", []):
                    ebe = EssmiBatchEquipment()
                    ebe.equipment_id = eq["id"]
                    ebe.essmib_id = eb.id
                    LieYingApp.db.session.add(ebe)
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
