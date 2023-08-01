from ly_kernel.db.BaseMarshmallow import *
from ly_service.utils import Time


class ViewSchema(BaseSchema):
    page = fields.Integer(default=1)
    size = fields.Integer(default=10)
    sort = fields.String(default="id, asc")
