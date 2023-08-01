from ly_kernel.db.BaseMarshmallow import *
from .ViewSchema import ViewSchema
from marshmallow_sqlalchemy import auto_field
from models.FlowTpl import FlowTpl
import uuid


class FlowOpCreateSchema(BaseSchema):
    tpl_id = fields.Integer()
    uid = fields.Integer()
    username = fields.String()
    params = fields.Function()


class FlowOpControlSchema(BaseSchema):
    flow_id = fields.Integer()
    approve_user_id = fields.Integer()
    node_id = fields.String()
    params = fields.Function()
    idea = fields.String()
    be_appoint_user_info = fields.Function()
    role_id = fields.List(fields.Integer, required=False)
    approve_user_name = fields.String(required=False)

    @post_load
    def post_load(self, data, **kwargs):
        data["node_id"] = uuid.UUID(data["node_id"]) if "node_id" in data else None
        return data


class FlowGetNodeCompleteList(BaseSchema):
    flow_id = fields.Integer(required=True)
    tpl_id = fields.Integer(required=True)


class FlowOpReissueSchema(BaseSchema):
    flow_id = fields.Integer(required=True)
    uid = fields.Integer(required=True)
    tpl_id = fields.Integer(required=True)
    username = fields.String(required=True)


class FlowOpNodeParamsSchema(BaseSchema):
    flow_id = fields.Integer(required=True)
    node_name = fields.String(required=True)

    class Meta:
        unknown = INCLUDE


class FlowOpFallbackSchema(BaseSchema):
    flow_id = fields.Integer(required=True)
    node_name = fields.String(required=True)
    approve_user_id = fields.Integer(required=True)

    class Meta:
        unknown = INCLUDE


class FlowOpNodeCanFallbackListSchema(BaseSchema):
    flow_id = fields.Integer(required=True)


class FlowOpFallbackPreNodeSchema(BaseSchema):
    flow_id = fields.Integer(required=True)
    node_name = fields.String(required=True)

    class Meta:
        unknown = INCLUDE
