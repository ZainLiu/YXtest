from models.data_center import DataCenter


def get_dc_info_by_dc_ids(ids):
    filter_cond = []
    if ids:
        filter_cond.append(DataCenter.id.in_(ids))
    dc_set = DataCenter.query.filter(*filter_cond).all()
    resp_data = []
    for dc in dc_set:
        resp_data.append({
            "id": dc.id,
            "name": dc.name
        })
    return resp_data