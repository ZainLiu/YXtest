from models.FlowTpl import FlowTpl


def get_flow_tpl_list(event_view_schema):

    page = event_view_schema.get("page")
    size = event_view_schema.get("size")
    os = event_view_schema.get("os", None)
    title = event_view_schema.get("title", None)
    id = event_view_schema.get("id", None)

    from sqlalchemy import func
    from sqlalchemy import desc

    filter = []
    if os != 0 and os is not None:
        filter.append(func.locate(os, FlowTpl.os))

    if title != "" and title is not None:
        filter.append(func.locate(title, FlowTpl.title))
    if id:
        filter.append(FlowTpl.id==id)

    db_flow_tpl = FlowTpl.query.filter(*filter).order_by(desc(FlowTpl.id)).paginate(page, size)

    return db_flow_tpl.items, db_flow_tpl.total


def get_flow_tpl_by_id(flow_tpl_id):
    return FlowTpl.query.filter(FlowTpl.id == flow_tpl_id).first()

