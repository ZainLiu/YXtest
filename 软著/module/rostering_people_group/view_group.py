from flask import g
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc

from model_to_view.rostering_people_group.schema import PeopleGroupListSchema, PeopleGroupCreateSchema, \
    PeopleGroupUpdateSchema, PeopleGroupActiveSchema, PeopleGroupDetailSchema
from model_to_view.rostering_people_group.serializer import PeopleGroupListSerialize
from models import IsValid, OperationType, IsActive
from models.rostering.people_group import PeopleGroup, PeopleGroupMember
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id, get_user_list_by_data_center_id


class PeopleGroupModule(ModuleBasic):
    """人员分组"""

    @request_url(PeopleGroupListSchema)
    def people_group_list(self, form_data):
        """查询人员分组列表"""
        name = form_data.get('name')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [PeopleGroup.data_center_id == data_center_id, PeopleGroup.is_valid != IsValid.Deleted]
        if name:
            query_list.append(PeopleGroup.name.like(f'%{name}%'))

        group_set = PeopleGroup.query.filter(*query_list).order_by(desc(PeopleGroup.id))
        count = group_set.count()
        group_set = group_set.paginate(page, size)
        data = PeopleGroupListSerialize(many=True).dump(group_set.items)

        return self.report.table(*(data, count))

    @request_url(PeopleGroupDetailSchema)
    def people_group_detail(self, form_data):
        """获取人员分组详情"""
        id = form_data.get('id')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            PeopleGroup.data_center_id == data_center_id,
            PeopleGroup.is_valid != IsValid.Deleted,
            PeopleGroup.id == id
        ]

        group = PeopleGroup.query.filter(*query_list).first()
        if not group:
            return self.report.error("找不到该id的人员分组")

        data = PeopleGroupListSerialize().dump(group)

        return self.report.post(data)

    @request_url(PeopleGroupCreateSchema)
    # @flow_decorator(FlowServicePeopleGroup)
    def people_group_create(self, form_data):
        """新增人员分组"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(PeopleGroup, 'RYFZ')

        group = PeopleGroup.query.filter_by(name=form_data['name']).first()
        if group:
            return self.report.error(f"名称【{form_data['name']}】的分组已经存在")

        member_set = form_data.pop('member_set')
        # 校验所有人员是否存在于别的分组，如果有在别的分组，则不让创建
        for member in member_set:
            member_objs = PeopleGroupMember.query.filter_by(user_id=member['user_id']).all()
            for member_obj in member_objs:
                group_data_center_id = member_obj.group.data_center_id
                group_name = member_obj.group.name
                if group_data_center_id == data_center_id:
                    return self.report.error(f'用户【{member_obj.user_name}】已经存在于分组【{group_name}】')

        try:
            instance = PeopleGroup(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 创建人员分组成员
            for member in member_set:
                member.pop('operation')
                member['id'] = None
                member['group_id'] = instance.id

                member_instance = PeopleGroupMember(**member)
                LieYingApp.db.session.add(member_instance)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('新增人员分组成功')

    @request_url(PeopleGroupUpdateSchema)
    # @flow_decorator(FlowServicePeopleGroup)
    def people_group_update(self, form_data):
        """修改人员分组"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        group_set = PeopleGroup.query.filter_by(id=form_data['id'])
        instance = group_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的分组')

        group = PeopleGroup.query.filter_by(name=form_data['name']).first()
        if group and group.id != instance.id:
            return self.report.error(f"名称【{form_data['name']}】的分组已经存在")

        member_set = form_data.pop('member_set')
        # 校验所有人员是否存在于别的分组，如果有在别的分组，则不让创建
        for member in member_set:
            member_objs = PeopleGroupMember.query.filter_by(user_id=member['user_id']).all()
            for member_obj in member_objs:
                group_data_center_id = member_obj.group.data_center_id
                group_name = member_obj.group.name
                if group_data_center_id == data_center_id:
                    return self.report.error(f'用户【{member_obj.user_name}】已经存在于分组【{group_name}】')

        try:
            group_set.update(form_data)
            LieYingApp.db.session.flush()

            # 遍历处理分组成员
            for member in member_set:
                operation = member.pop('operation')
                if operation == OperationType.ADD:
                    member['id'] = None
                    member['group_id'] = instance.id

                    member_instance = PeopleGroupMember(**member)
                    LieYingApp.db.session.add(member_instance)
                elif operation == OperationType.UPDATE:
                    PeopleGroupMember.query.filter_by(id=member['id']).update(member)
                elif operation == operation == OperationType.DELETE:
                    PeopleGroupMember.query.filter_by(id=member['id']).delete()

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('修改人员分组成功')

    @request_url(PeopleGroupActiveSchema)
    def people_group_active(self, form_data):
        """激活/停用人员分组"""
        group_set = PeopleGroup.query.filter_by(id=form_data['id'])
        instance = group_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的客户')
        try:
            group_set.update(form_data)
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('成功')

    def user_list_get(self):
        """获取本数据中心下的所有用户"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        user_list = get_user_list_by_data_center_id(data_center_id)
        if not user_list:
            return self.report.error('获取不到用户列表')

        return self.report.post(user_list)

    def people_group_easy(self):
        """获取人员分组简单列表"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        query_list = [PeopleGroup.data_center_id == data_center_id, PeopleGroup.is_active == IsActive.Active]
        work_type_set = PeopleGroup.query.filter(*query_list).order_by(desc(PeopleGroup.id))

        result = []
        for work_type in work_type_set:
            result.append({
                'id': work_type.id,
                'name': work_type.name
            })

        return self.report.post(result)


people_group_module = PeopleGroupModule()
