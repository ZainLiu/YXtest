from ly_kernel.db.BaseMarshmallow import *
from .ViewSchema import ViewSchema
from marshmallow_sqlalchemy import auto_field
from models.FlowTpl import FlowTpl


class FlowTplViewSchema(ViewSchema):
    os = fields.Integer()
    title = fields.String()
    id = fields.Integer()

    @post_load
    def post_load(self, data, **kwargs):
        data["os"] = data["os"] if "os" in data else 1
        return data


# 列表
class FlowTplViewModelSchema(BaseSQLAlchemyAutoSchema):
    specs_data = auto_field(load_only=True)

    class Meta:
        model = FlowTpl


# 编辑
class FlowTplFormSchema(BaseSchema):
    id = fields.Integer(dump_only=True)
    os = fields.Integer()
    title = fields.String()
    order_tpl_id = fields.Integer(default=0)
    tpl_data = fields.Function()

    @post_load
    def post_load(self, data, **kwargs):
        data["os"] = data["os"] if "os" in data else 1
        return data

    class Meta:
        unknown = INCLUDE

