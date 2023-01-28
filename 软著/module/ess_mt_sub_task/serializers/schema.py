from ly_kernel.db.BaseMarshmallow import *

from model_to_view import BaseSchemaWithPaging


class ESSMSTListSchema(BaseSchemaWithPaging):
    serial_number = fields.String(required=False)


class ESSMSTDetailSchema(BaseSchema):
    id = fields.Integer(required=True)


class ESSMSTAcceptSchema(BaseSchema):
    id = fields.Integer(required=True)


class ESSMSTFinishSubmitSchema(BaseSchema):
    id = fields.Integer(required=True)
    fill_data = fields.Dict(required=True)


class ESSMSTSummarySchema(BaseSchema):
    id = fields.Integer(required=True)
    summary = fields.String(required=False, missing="")
    annex = fields.List(fields.Dict, required=False, missing=[])