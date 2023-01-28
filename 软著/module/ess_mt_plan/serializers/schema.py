from ly_kernel.db.BaseMarshmallow import *

from model_to_view import BaseSchemaWithPaging


class ESSMPListSchema(BaseSchemaWithPaging):
    serial_number = fields.String(required=False)
    year = fields.Int(required=False)
    leader_name = fields.String(required=False)
    eq_sys_id = fields.Int(required=False)


class ESSMPDetailSchema(BaseSchema):
    id = fields.Int(required=False)


class ESSMPDSaveSchema(BaseSchema):
    id = fields.Int(required=True)
    detail_info = fields.List(fields.Dict, required=True)