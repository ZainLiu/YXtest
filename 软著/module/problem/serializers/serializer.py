from flask import current_app
from ly_kernel.db.BaseMarshmallow import *

from models.problem import Problem, Solution
from utils.flow_base_serializer import WithBacklogSerializer, WithFlowDataStatusSerializer

"""序列化器"""


class ProblemBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    """问题列化器基类"""

    class Meta:
        model = Problem

    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    equipment_system_name = fields.Method(serialize="get_eq_sys_name", dump_only=True)
    equipment_system_id = fields.Int()

    def get_eq_sys_name(self, obj):
        return obj.equipment_system.name


class ProblemListSerializer(ProblemBaseSerializer):
    """列表"""

    class Meta:
        exclude = ["description", "affected_area", "processing_description"]


class ProblemDetailSerializer(ProblemBaseSerializer):
    """列表"""
    pass


class SolutionBaseSerializer(WithBacklogSerializer, WithFlowDataStatusSerializer):
    """解决方案序列化器基类"""
    create_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])
    update_time = fields.DateTime(format=current_app.config['APP_DATETIME_FORMAT'])

    class Meta:
        model = Solution


class SolutionListSerializer(SolutionBaseSerializer):
    """解决方案列表"""
    pass


class SolutionDetailSerializer(SolutionBaseSerializer):
    """解决方案列表"""
    problem = fields.Nested(ProblemDetailSerializer)
