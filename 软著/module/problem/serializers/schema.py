from ly_kernel.db.BaseMarshmallow import *

from model_to_view import BaseSchemaWithPaging


class ProblemListSchema(BaseSchemaWithPaging):
    serial_number = fields.Str(required=False)
    eq_sys_id = fields.Int(required=False)
    level = fields.Int(required=False)
    name = fields.String(required=False)


class ProblemDetailSchema(BaseSchema):
    id = fields.Int(required=True)


class ProblemSaveSchema(BaseSchema):
    id = fields.Int(required=False)
    name = fields.String(required=False)
    level = fields.Int(required=False)
    equipment_system_id = fields.Int(required=True)
    description = fields.String(required=False)
    affected_area = fields.String(required=False)
    processing_description = fields.String(required=False)
    event_id_list = fields.List(fields.Int, required=False, missing=[])


class ProblemSubmitSchema(BaseSchema):
    id = fields.Int(required=False)
    name = fields.String(required=True)
    level = fields.Int(required=True)
    equipment_system_id = fields.Int(required=True)
    description = fields.String(required=True)
    affected_area = fields.String(required=True)
    processing_description = fields.String(required=True)
    event_id_list = fields.List(fields.Int, required=False, missing=[])


class ProblemAssignSchema(BaseSchema):
    id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    user_name = fields.String(required=True)


class ProblemGetMajorPeopleListSchema(BaseSchema):
    id = fields.Int(required=True)


class SolutionAcceptSchema(BaseSchema):
    """问题受理"""
    id = fields.Int(required=True)


class SolutionFallbackSchema(BaseSchema):
    """问题受理"""
    id = fields.Int(required=True)
    fallback_reason = fields.String(required=True, error_messages={"required": "回退操作回退理由必填"})


class SolutionFillSchema(BaseSchema):
    """方案填写"""
    id = fields.Int(required=True)
    is_change = fields.Int(required=True)
    change_id = fields.Int(required=False)
    cause_analysis = fields.String(required=True)
    solution = fields.String(required=True)
    annex = fields.List(fields.Dict, required=False, missing=[])


class SolutionDetailSchema(BaseSchema):
    """解决方案详情"""
    id = fields.Int(required=True)


class SolutionSummarySchema(BaseSchema):
    """解决方案总结"""
    id = fields.Int(required=True)
    is_solved = fields.Int(required=True)
