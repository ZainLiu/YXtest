import datetime
from ly_kernel.LieYing import LieYingApp
from flask import g
from models import FlowStatus, IsValid, YesOrNo, IsDraft
from models.maintenance_plan import EquipmentSubSystemMaintenancePlan
from module.ess_mt_plan.serializers.serializer import ESSMPListSerializer
from module.ess_mt_plan.service import generate_ess_maintenance_task
from utils.flow_base_service import FlowBaseService


class FlowServiceESSMP(FlowBaseService):
    """维保计划"""
    model = EquipmentSubSystemMaintenancePlan
    form_serialize = ESSMPListSerializer
    serial_number = 'serial_number'
    form_name = '维保-设备子系统维保计划'

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
        generate_ess_maintenance_task(form_obj)

    def flow_refuse_func(form_obj):
        """审批拒绝后钩子"""
        form_obj.flow_status = FlowStatus.Reject
        form_obj.last_editor_id = g.uid

    def flow_revoke_func(form_obj):
        """审批撤销后钩子"""
        form_obj.flow_status = FlowStatus.WithDraw
        form_obj.last_editor_id = g.uid
