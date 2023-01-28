import logging
from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url
from ly_service.request.RpcFunc import RpcFuncService
from sqlalchemy import desc, and_, or_
from models import IsValid, FlowStatus
from models.upcoming import Upcoming
from model_to_view.workbench.schema import WorkBenchListSchema
from model_to_view.workbench.serializer import UpcomingListSerialize
from models.work_flow import WorkFlow
from utils.rpc_func import get_user_current_data_center_id


class WorkBenchModule(ModuleBasic):
    """工作台"""

    @request_url(WorkBenchListSchema)
    def list(self, req_data):
        """工作台待办列表"""
        id = req_data.get('id')
        title = req_data.get('title')
        upcoming_type = req_data.get('upcoming_type')
        page = req_data.get('page')
        size = req_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            Upcoming.data_center_id == data_center_id,
            Upcoming.is_valid != IsValid.Deleted,
            Upcoming.user_id == g.uid
        ]
        if id:
            query_list.append(Upcoming.id == id)
        if title:
            query_list.append(Upcoming.title.like(f'%{title}%'))
        if upcoming_type:
            query_list.append(Upcoming.upcoming_type == upcoming_type)

        query_set = Upcoming.query.filter(*query_list).order_by(desc(Upcoming.id))
        count = query_set.count()

        try:
            query_set = query_set.paginate(page, size)
        except:
            query_set = query_set.paginate(1, size)

        data = UpcomingListSerialize(many=True).dump(query_set.items)

        # 补充flow_id到data
        form_dict = {item['form_code']: item['form_id'] for item in data if
                     item.get('form_code') and item.get('form_id')}

        flow_set = WorkFlow.query.filter(
            or_(WorkFlow.form_code.in_(form_dict.keys()), WorkFlow.form_id.in_(form_dict.values()))).all()
        flow_dict = {}
        for flow in flow_set:
            if not flow_dict.get(flow.form_code):
                flow_dict[flow.form_code] = {}
            flow_dict[flow.form_code][flow.form_id] = flow.id

        for item_data in data:
            form_code = item_data.get('form_code')
            form_id = item_data.get('form_id')

            if not form_code or not form_id:
                continue

            flow_code_dict = flow_dict.get(form_code, {})
            flow_id = flow_code_dict.get(form_id, None)

            item_data['flow_id'] = flow_id

        return self.report.table(*(data, count))


workbench_module = WorkBenchModule()
