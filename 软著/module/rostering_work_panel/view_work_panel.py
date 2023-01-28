import datetime
import json

from flask import g
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc
from model_to_view.rostering_work_panel.schema import WorkPlanListSchema, UserWorkListSchema, TestSchema
from model_to_view.rostering_work_panel.serializer import WorkPanelListSerialize
from models.rostering.work_admin import WorkAdmin
from models.rostering.work_panel import WorkPanel, PanelType
from tasks.async_tasks import async_write_panel_data
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class WorkPanelModule(ModuleBasic):
    """排班面板管理"""

    @request_url(WorkPlanListSchema)
    def work_panel_list(self, form_data):
        """查询排班看板"""
        date = form_data.get('date')
        user_name = form_data.get('user_name')
        group_name = form_data.get('group_name')
        panel_type = form_data.get('panel_type')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [WorkPanel.data_center_id == data_center_id, WorkPanel.panel_type == panel_type]
        if date:
            # date是考勤月，传入10月，则查询9月26-10月25，传入11月，则查询10月26-11月25
            date_list = date.split('-')
            if len(date_list) != 2:
                return self.report.error(f'日期格式不正确：【date】：{date}')
            year, month = date.split('-')[0], date.split('-')[-1]
            # 获取上一个月的第一天
            last_date = datetime.date(int(year), int(month), 1)
            # 获取上一个月
            last_month = last_date - datetime.timedelta(days=1)
            last_month_str = last_month.strftime('%Y-%m')
            # 获取上个月26号 至 这个月25号的所有日期
            start_date = f'{last_month_str}-26'
            end_date = f'{year}-{month}-25'
            dates = TimeUtil.date_range(start_date, end_date)

            query_list.append(WorkPanel.date.in_(dates))
        if user_name:
            query_list.append(WorkPanel.user_name.like(f'%{user_name}%'))
        if group_name:
            query_list.append(WorkPanel.group_name.like(f'%{group_name}%'))

        panel_set = WorkPanel.query.filter(*query_list).order_by(desc(WorkPanel.id)).all()

        data = WorkPanelListSerialize(many=True).dump(panel_set)

        return self.report.post(data)

    @request_url(UserWorkListSchema)
    def get_work_by_user_ids(self, form_data):
        """获取用户指定日期的排班【仅限调班使用】"""
        date = form_data.get('date')
        user_ids = form_data.get('user_ids')

        try:
            user_ids = json.loads(user_ids)
        except Exception as e:
            return self.report.error(f'参数【user_ids】传入不合法：{user_ids},原因：{e}')

        if len(user_ids) != 2:
            return self.report.error('【user_ids】必须长度为2')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            WorkPanel.data_center_id == data_center_id,
            WorkPanel.user_id.in_(user_ids),
            WorkPanel.panel_type == PanelType.STAFF,
            WorkPanel.date == date
        ]
        panel_set = WorkPanel.query.filter(*query_list).order_by(desc(WorkPanel.id))

        data = {panel.user_id: panel.work_type for panel in panel_set}

        # 检查两个用户有相同的班次时，去除掉，否则在进行调班时，可能出现一方同一天两个相同班次的情况
        work_type_id_dict = {}
        remove_ids = []
        new_data = {user_id: [] for user_id in user_ids}
        for user_id, work_type_list in data.items():
            for item in work_type_list:
                work_type_id = item['work_type_id']
                if not work_type_id_dict.get(work_type_id):
                    work_type_id_dict[work_type_id] = 1
                else:
                    remove_ids.append(work_type_id)
        # 生成新的返回数据
        for user_id, work_type_list in data.items():
            for item in work_type_list:
                work_type_id = item['work_type_id']
                if work_type_id not in remove_ids:
                    new_data[user_id].append(item)

        return self.report.post(new_data)

    @request_url(TestSchema)
    def test(self, form_data):
        """写入排班测试数据"""
        work_admin_id = form_data.get('work_admin_id')

        work_admin = WorkAdmin.query.filter_by(id=work_admin_id).first()
        preview_data = work_admin.preview_data
        if not preview_data:
            return self.report.error('该排班没有【preview_data】字段，不能写入')

        async_write_panel_data.apply_async(args=(work_admin.id,), countdown=0, queue='async_task')

        return self.report.suc('成功')


work_panel_module = WorkPanelModule()
