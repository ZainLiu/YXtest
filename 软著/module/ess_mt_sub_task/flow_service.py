import datetime
from ly_kernel.LieYing import LieYingApp
from flask import g
from models import FlowStatus, IsValid, YesOrNo, IsDraft
from models.maintenance_task import EquipmentSubSystemMaintenanceSubTask
from module.ess_mt_sub_task.serializers.serializer import ESSMSTListSerializer
from utils.flow_base_service import FlowBaseService


class FlowServiceESSMST(FlowBaseService):
    """维保子任务"""
    model = EquipmentSubSystemMaintenanceSubTask
    form_serialize = ESSMSTListSerializer
    serial_number = 'serial_number'
    form_name = '维保-设备子系统维保子任务总结审批'

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
            # 生成维保任务
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
