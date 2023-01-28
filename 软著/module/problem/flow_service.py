import datetime
from ly_kernel.LieYing import LieYingApp
from flask import g
from models import FlowStatus, IsValid, YesOrNo, IsDraft, db
from models.problem import Problem, Solution
from models.upcoming import Upcoming, UpcomingType
from module.problem.serializers.serializer import ProblemListSerializer, SolutionListSerializer
from utils.flow_base_service import FlowBaseService


class FlowServiceProblem(FlowBaseService):
    """问题审批流"""
    model = Problem
    form_serialize = ProblemListSerializer
    serial_number = 'serial_number'
    form_name = '问题-问题提交审批'

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
        # 审批过后给专业组组长发一条待办，让其指派人员解决问题
        upcoming_obj = Upcoming()
        upcoming_obj.data_center_id = form_obj.data_center_id
        upcoming_obj.upcoming_type = UpcomingType.ASSIGN_MT_SUB_TASK
        upcoming_obj.title = f'指派问题处理-{form_obj.serial_number}'
        upcoming_obj.form_code = Problem.__name__
        upcoming_obj.form_id = form_obj.id
        upcoming_obj.user_id = form_obj.leader_id
        db.session.add(upcoming_obj)

    def flow_refuse_func(form_obj):
        """审批拒绝后钩子"""
        form_obj.flow_status = FlowStatus.Reject
        form_obj.last_editor_id = g.uid

    def flow_revoke_func(form_obj):
        """审批撤销后钩子"""
        form_obj.flow_status = FlowStatus.WithDraw
        form_obj.last_editor_id = g.uid


class FlowServiceSolution(FlowBaseService):
    """解决方案审批流"""
    model = Solution
    form_serialize = SolutionListSerializer
    serial_number = 'serial_number'
    form_name = '问题-解决方案提交审批'

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