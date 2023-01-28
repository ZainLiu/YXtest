from ly_kernel.db.BaseMarshmallow import *
from model_to_view import BaseSchemaWithPaging


class ESSMPTSaveSchema(BaseSchema):
    id = fields.Int(required=False)
    year = fields.Int(required=True)
    eq_sys_id = fields.Int(required=True)
    mark = fields.Str(required=False, missing="")
    annex = fields.List(fields.Dict, required=False, missing=[])
    detail_info = fields.List(fields.Dict, required=True)
    pg_id = fields.Int(required=True)


class ESSMPTListSchema(BaseSchemaWithPaging):
    serial_number = fields.Str(required=False)
    year = fields.Int(required=False)
    leader_name = fields.Str(required=False)
    eq_sys_id = fields.Int(required=False)


class ESSMPTDetailSchema(BaseSchema):
    id = fields.Int(required=True)
