import datetime

from models import IsActive
from models.rostering.work_panel import WorkPanel, PanelType
from models.rostering.work_type import WorkType, Type


def get_now_work_type(dc_id):
    now_time = datetime.datetime.today().time()
    day_begin_clock = datetime.time()
    day_end_clock = datetime.time(hour=23, minute=59, second=59, microsecond=999999)
    wt_set = WorkType.query.filter(WorkType.data_center_id == dc_id, WorkType.is_active == IsActive.Active,
                                   WorkType.type != Type.REST).all()

    wt_list = []
    for wt in wt_set:
        if wt.work_end < wt.work_start:
            if day_begin_clock <= now_time <= wt.work_end or wt.work_start <= now_time <= day_end_clock:
                wt_list.append(wt)
        else:
            if wt.work_start <= now_time <= wt.work_end:
                wt_list.append(wt)
    if not wt_list:
        return []
    wt_id_list = [wt.id for wt in wt_list]
    user_list = []
    wp_set = WorkPanel.query.filter(WorkPanel.panel_type == PanelType.STAFF, WorkPanel.date == datetime.date.today(),
                                    WorkPanel.data_center_id == dc_id).all()
    for wp in wp_set:
        for work_type in wp.work_type:
            if work_type.get("work_type_id") in wt_id_list:
                user_list.append(wp.user_id)
    return user_list
