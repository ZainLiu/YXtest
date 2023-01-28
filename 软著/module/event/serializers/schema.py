from ly_kernel.db.BaseMarshmallow import *
from model_to_view import BaseSchemaWithPaging


class EventSubmitSchema(BaseSchema):
    id = fields.Integer(required=False)
    occur_time = fields.DateTime(required=True)
    eq_sys_id = fields.Integer(required=True)
    level = fields.Integer(required=True)
    type = fields.Integer(required=True)
    room_id = fields.Integer(required=False)
    eq_id = fields.Integer(required=False)
    description = fields.Str(required=True)
    annex = fields.List(fields.Dict, required=False, missing=[])
    form_id = fields.Integer(required=False)
    form_code = fields.Str(required=False)
    solve_time = fields.DateTime(required=False)


class EventSaveSchema(BaseSchema):
    id = fields.Integer(required=False)
    occur_time = fields.DateTime(required=False)
    eq_sys_id = fields.Integer(required=False)
    level = fields.Integer(required=False)
    type = fields.Integer(required=True, error_messages={"required": "事件类型必传"})
    room_id = fields.Integer(required=False)
    eq_id = fields.Integer(required=False)
    description = fields.Str(required=False)
    annex = fields.List(fields.Dict, required=False, missing=[])
    solve_time = fields.DateTime(required=False)
    form_id = fields.Int(required=False)
    form_code = fields.Str(required=False)


class EventAcceptSchema(BaseSchema):
    id = fields.Int(required=True)


class EventProcessDetailSchema(BaseSchema):
    id = fields.Int(required=True)
    estimated_recovery_time = fields.DateTime(required=False)
    # end_time = fields.DateTime(required=True)
    description = fields.Str(required=True)
    annex = fields.List(fields.Dict, required=False, missing=[])
    # operate_type = fields.Int(required=True)


class EventFallbackSchema(BaseSchema):
    id = fields.Int(required=True)


class EventUpdateSchema(BaseSchema):
    id = fields.Int(required=True)


class EventSuspendedSchema(BaseSchema):
    id = fields.Int(required=True)
    reason = fields.String(required=True)


class EventListSchema(BaseSchemaWithPaging):
    serial_number = fields.String(required=False)
    eq_sys_id = fields.Int(required=False)
    occur_start_time = fields.DateTime(required=False)
    occur_end_time = fields.DateTime(required=False)
    recovery_start_time = fields.DateTime(required=False)
    recovery_end_time = fields.DateTime(required=False)


class EventListSimpleSchema(BaseSchemaWithPaging):
    serial_number = fields.String(required=False)
    eq_sys_id = fields.Int(required=False)
    level = fields.Int(required=False)


class EventDetailSchema(BaseSchema):
    id = fields.Int(required=False)


class EventSuspendedWorkflowDetailSchema(BaseSchema):
    id = fields.Int(required=False)
