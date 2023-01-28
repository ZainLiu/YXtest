from ly_kernel.LieYing import LieYingApp
import copy
from flask import current_app
from models.rostering.people_group import PeopleGroupMember, PeopleGroup
from models.rostering.work_admin import WorkAdmin
from models.rostering.work_panel import WorkPanel, PanelType


class WorkPanelService:
    """排班审批通过写入排班面板(样本数据见init文件)"""

    def __init__(self, work_admin_id):
        # 排班管理id
        self.work_admin_id = work_admin_id
        # 排班实例
        self.work_admin = None
        # 排班数据
        self.preview_data = {}
        # 星期数据，key：2022_09_26 value：星期一
        self.week_data = {}
        # 排班类型 1-分组 2-人员
        self.panel_type = 0
        # 排班数据 key:用户id或分组id value：{'name':'名称','work_data':{'2022_09_26':[{'班次id':1,'班次名称':'白班','班次样式':''}...]}}
        self.work_data = {}

    def __get_preview_data(self):
        """获取排班数据"""
        LieYingApp.db.session.commit()
        if not self.work_admin_id:
            return False, '没有【work_admin_id】'
        work_admin = WorkAdmin.query.filter_by(id=self.work_admin_id).first()
        if not work_admin:
            return False, f'没有【work_admin】/【{self.work_admin_id}】'
        if not work_admin.preview_data:
            return False, '没有【work_admin.preview_data】'
        self.work_admin = work_admin
        self.preview_data = work_admin.preview_data
        return True, None

    def __check_preview_data(self):
        """校验preview_data数据"""
        if not self.preview_data:
            return False, '没有【preview_data】'
        columns = self.preview_data.get('columns')
        table_data = self.preview_data.get('table_data')
        if not columns or not table_data:
            return False, '没有【columns】或【table_data】'
        if not isinstance(columns, list):
            return False, '【columns】不是列表类型'
        if not isinstance(table_data, list):
            return False, '【table_data】不是列表类型'
        return True, None

    def __get_week_data(self):
        """获取星期数据"""
        columns = self.preview_data['columns']
        for index, item in enumerate(columns):
            # 从第一个子项取出面板类型，区分是分组还是人员排班
            if not index:
                self.panel_type = item.get('panel_type')
            title = item.get('title')
            col_key = item.get('col_key')
            week = title.split(' ')[-1]
            date = col_key.replace('date_', '')
            self.week_data[date] = week

    def __get_table_data(self):
        """获取具体排班数据"""
        table_data = self.preview_data.get('table_data')
        for column in table_data:
            target = column.get('target')
            if not target or not isinstance(target, dict):
                continue
            target_id = target.get('id')
            target_name = target.get('name')
            if not self.work_data.get(target_id):
                self.work_data[target_id] = {
                    'name': target_name,
                    'work_data': {}
                }

            for key, value in column.items():
                # 日期排班数据
                if 'date_' in key:
                    date = key.replace('date_', '')
                    self.work_data[target_id]['work_data'][date] = []
                    # 这里是一个列表，因为存在多个排班
                    for value_item in value:
                        self.work_data[target_id]['work_data'][date].append({
                            'work_type_id': value_item.get('id'),
                            'work_type_name': value_item.get('name'),
                            'work_type_style': value_item.get('style_type')
                        })

    def __get_group_by_people(self, people_ids):
        """通过人员id列表获取对应的人员分组id"""
        group_set = PeopleGroup.query.filter_by(data_center_id=self.work_admin.data_center_id).all()
        group_list = [group.id for group in group_set]
        member_set = PeopleGroupMember.query.filter(PeopleGroupMember.user_id.in_(people_ids))
        data = {}
        for member in member_set:
            if member.group_id in group_list:
                data[member.user_id] = {
                    'id': member.group_id,
                    'name': member.group.name
                }
        return data

    def __get_people_ids_by_group(self, group_ids):
        """通过人员分组列表获取下面的所有人员id列表"""
        group_set = PeopleGroup.query.filter(
            PeopleGroup.data_center_id == self.work_admin.data_center_id,
            PeopleGroup.id.in_(group_ids)
        )

        data = {}
        for group in group_set:
            member_set = group.member_set.all()
            data[group.id] = []
            for member in member_set:
                data[group.id].append({
                    'id': member.user_id,
                    'name': member.user_name
                })
        return data

    def __write_panel_group(self):
        """写入分组面板"""
        if self.panel_type != PanelType.GROUP:
            return False, f'类型不正确(1)：{self.panel_type}'
        people_dict = self.__get_people_ids_by_group(self.work_data.keys())
        if not people_dict:
            return False, f'找不到组人员：{people_dict}'

        for group_id, value in self.work_data.items():
            group_name = value.get('name')
            work_data = value.get('work_data')
            people_list = people_dict.get(group_id)
            if not group_name or not work_data or not people_list:
                continue

            for date, work_list in work_data.items():
                if not self.week_data.get(date):
                    continue

                data = {
                    'data_center_id': self.work_admin.data_center_id,
                    'group_id': group_id,
                    'group_name': group_name,
                    'date': date,
                    'week': self.week_data[date],
                    'work_type': work_list,
                    'panel_type': PanelType.GROUP
                }

                panel = WorkPanel.query.filter_by(
                    data_center_id=self.work_admin.data_center_id,
                    group_id=group_id,
                    date=date,
                    panel_type=PanelType.GROUP
                ).first()

                # 设置或者更新班组数据
                if panel:
                    WorkPanel.query.filter_by(id=panel.id).update(data)
                else:
                    panel_instance = WorkPanel(**data)
                    LieYingApp.db.session.add(panel_instance)

                # 接着遍历人员，设置到每个组员身上,设置前同样检查该数据中心、该分组
                for people in people_list:
                    temp = copy.deepcopy(data)
                    temp['user_id'] = people.get('id')
                    temp['user_name'] = people.get('name')
                    temp['panel_type'] = PanelType.STAFF

                    people_panel = WorkPanel.query.filter_by(
                        data_center_id=self.work_admin.data_center_id,
                        user_id=temp['user_id'],
                        date=date,
                        panel_type=PanelType.STAFF
                    ).first()

                    if people_panel:
                        WorkPanel.query.filter_by(id=panel.id).update(temp)
                    else:
                        people_panel_instance = WorkPanel(**temp)
                        LieYingApp.db.session.add(people_panel_instance)

        LieYingApp.db.session.commit()
        return True, None

    def __write_panel_people(self):
        """写入人员面板"""
        if self.panel_type != PanelType.STAFF:
            return False, f'类型不正确：{self.panel_type}'
        group_dict = self.__get_group_by_people(self.work_data.keys())
        # if not group_dict:
        #     return False, f'找不到用户组：{group_dict}'

        for user_id, value in self.work_data.items():
            user_name = value.get('name')
            work_data = value.get('work_data')
            group_data = group_dict.get(user_id, {})
            if not user_name or not work_data:
                continue

            for date, work_list in work_data.items():
                if not self.week_data.get(date):
                    continue

                data = {
                    'data_center_id': self.work_admin.data_center_id,
                    'group_id': group_data.get('id'),
                    'group_name': group_data.get('name'),
                    'date': date,
                    'week': self.week_data[date],
                    'user_id': user_id,
                    'user_name': user_name,
                    'work_type': work_list,
                    'panel_type': PanelType.STAFF
                }

                panel = WorkPanel.query.filter_by(
                    data_center_id=self.work_admin.data_center_id,
                    user_id=user_id,
                    date=date,
                    panel_type=PanelType.STAFF
                ).first()

                # 设置或者更新人员数据
                if panel:
                    WorkPanel.query.filter_by(id=panel.id).update(data)
                else:
                    panel_instance = WorkPanel(**data)
                    LieYingApp.db.session.add(panel_instance)

        LieYingApp.db.session.commit()
        return True, None

    def write_panel(self):
        """写入面板"""
        # 先获取排班管理的预览数据
        check, msg = self.__get_preview_data()
        if not check:
            return False, f'获取基础数据出错：{msg}'
        # 校验数据
        check, msg = self.__check_preview_data()
        if not check:
            return False, f'校验数据出错：{msg}'
        # 获取星期数据
        self.__get_week_data()
        # 获取具体排班数据
        self.__get_table_data()
        if not self.panel_type:
            return False, '准备写入面板数据时找不到面板类型'
        if self.panel_type == PanelType.GROUP:
            check_write, msg = self.__write_panel_group()
        else:
            check_write, msg = self.__write_panel_people()

        if not check_write:
            return False, msg

        return check_write, None
