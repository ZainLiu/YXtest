from flask import current_app
from ly_kernel.db.BaseMarshmallow import *
from marshmallow import validate

from model_to_view import BaseSchemaWithPaging

"""验证器"""


class EssmiSaveDraftSchema(BaseSchema):
    draft_info = fields.Dict(required=True)


class EssmiListEquipmentSchema(BaseSchema):
    id = fields.Int(required=True)


class ESSMIListSchema(BaseSchemaWithPaging):
    serial_number = fields.String(required=False)
    title = fields.String(required=False)
    eq_sys_id = fields.Int(required=False)


class ESSMIDetailSchema(BaseSchema):
    id = fields.Int(required=True)


class ESSMISwitchVersionSchema(BaseSchema):
    id = fields.Int(required=True)


class ESSMIListSimpleSchema(BaseSchema):
    eq_sys_id = fields.Integer(required=True)
    year = fields.Integer(required=True)