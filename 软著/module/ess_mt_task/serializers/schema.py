from ly_kernel.db.BaseMarshmallow import *
from model_to_view import BaseSchemaWithPaging


class ESSMTDetailSchema(BaseSchema):
    id = fields.Integer(required=True)


class ESSMTListSchema(BaseSchemaWithPaging):
    serial_number = fields.Str(required=False)
    year_month = fields.Str(required=False)
    eq_sys_id = fields.Int(required=False)


class ESSMTAssignSchema(BaseSchema):
    assign_info = fields.List(fields.Dict, required=True)
    id = fields.Integer(required=True)


class ESSMSTReassignmentSchema(BaseSchema):
    id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    user_name = fields.Str(required=True)
