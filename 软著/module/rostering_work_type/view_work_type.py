from flask import g, request
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc

from config import current_config
from model_to_view.rostering_work_type.schema import WorkTypeActiveSchema, WorkTypeUpdateSchema, WorkTypeCreateSchema, \
    WorkTypeListSchema, WorkTypeEasySchema, WorkTypeDetailByIdSchema
from model_to_view.rostering_work_type.serializer import WorkTypeListSerialize
from models import IsValid, OperationType, IsActive
from models.rostering.work_type import WorkType, Type
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id


class WorkTypeModule(ModuleBasic):
    """班次"""

    @request_url(WorkTypeListSchema)
    def work_type_list(self, form_data):
        """查询班次列表"""
        id = form_data.get('id')
        name = form_data.get('name')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [WorkType.data_center_id == data_center_id]
        if id:
            query_list.append(WorkType.id == id)
        if name:
            query_list.append(WorkType.name.like(f'%{name}%'))

        work_type_set = WorkType.query.filter(*query_list).order_by(desc(WorkType.id))
        count = work_type_set.count()
        work_type_set = work_type_set.paginate(page, size)

        data = WorkTypeListSerialize(many=True).dump(work_type_set.items)

        return self.report.table(*(data, count))

    @request_url(WorkTypeDetailByIdSchema)
    def work_type_detail(self, form_data):
        """获取班次详情"""
        id = form_data.get('id')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            WorkType.data_center_id == data_center_id,
            WorkType.id == id
        ]

        work_type = WorkType.query.filter(*query_list).first()
        if not work_type:
            return self.report.error("找不到该id的班次")

        data = WorkTypeListSerialize().dump(work_type)

        return self.report.post(data)

    @request_url(WorkTypeCreateSchema)
    def work_type_create(self, form_data):
        """新增班次"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()

        name = form_data.get('name')
        work_type = WorkType.query.filter_by(data_center_id=data_center_id, name=name).first()
        if work_type:
            return self.report.error(f'名字【{name}】的班次已经存在')

        type = form_data.get('type')
        # 如果是休息班，只能存在一个
        if type == Type.REST:
            rest_work_type = WorkType.query.filter_by(data_center_id=data_center_id, type=Type.REST).first()
            if rest_work_type:
                return self.report.error('休息班次已经存在，一个数据中心只允许存在一个休息班')

        try:
            instance = WorkType(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('新增班次成功')

    @request_url(WorkTypeUpdateSchema)
    def work_type_update(self, form_data):
        """修改班次"""
        group_set = WorkType.query.filter_by(id=form_data['id'])
        instance = group_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的客户')

        try:
            group_set.update(form_data)
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('修改班次成功')

    @request_url(WorkTypeActiveSchema)
    def work_type_active(self, form_data):
        """激活/停用班次"""
        work_type_set = WorkType.query.filter_by(id=form_data['id'])
        instance = work_type_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的客户')
        try:
            work_type_set.update(form_data)
            LieYingApp.db.session.flush()
        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        return self.report.suc('成功')

    @request_url(WorkTypeEasySchema)
    def work_type_easy(self, form_data):
        """获取班次简单列表"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        query_list = [WorkType.data_center_id == data_center_id, WorkType.is_active == IsActive.Active]
        work_type_set = WorkType.query.filter(*query_list).order_by(desc(WorkType.id))

        result = []
        for work_type in work_type_set:
            result.append({
                'id': work_type.id,
                'name': work_type.name,
                'work_start': work_type.work_start.strftime(
                    current_config.APP_TIME_FORMAT) if work_type.work_start else None,
                'work_end': work_type.work_end.strftime(current_config.APP_TIME_FORMAT) if work_type.work_end else None,
                'rest_start': work_type.rest_start.strftime(
                    current_config.APP_TIME_FORMAT) if work_type.rest_start else None,
                'rest_end': work_type.rest_end.strftime(current_config.APP_TIME_FORMAT) if work_type.rest_end else None,
                'type': work_type.type,
                'style_type': work_type.style_type
            })

        return self.report.post(result)


work_type_module = WorkTypeModule()
