from flask import g, request
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc
from model_to_view.rostering_work_admin.schema import WorkAdminListSchema, WorkAdminCreateSchema, WorkAdminUpdateSchema, \
    WorkAdminSaveDraftSchema, WorkAdminDetailByIdSchema
from model_to_view.rostering_work_admin.serializer import WorkAdminListSerialize, WorkAdminInfoDetailSerialize
from models import IsValid, OperationType, IsDraft
from models.rostering.work_admin import WorkAdmin, WorkAdminDetail
from module.rostering_work_admin.flow_service import FlowServiceWorkAdmin
from utils.flow_decorator import flow_decorator
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id
from tasks.async_tasks import async_write_panel_data


class WorkAdminModule(ModuleBasic):
    """排班管理"""

    @request_url(WorkAdminListSchema)
    def work_admin_list(self, form_data):
        """查询排班列表"""
        id = form_data.get('id')
        serial_number = form_data.get('serial_number')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [WorkAdmin.data_center_id == data_center_id, WorkAdmin.is_valid != IsValid.Deleted]
        if id:
            query_list.append(WorkAdmin.id == id)
        if serial_number:
            query_list.append(WorkAdmin.serial_number.like(f'%{serial_number}%'))

        work_set = WorkAdmin.query.filter(*query_list).order_by(desc(WorkAdmin.id))
        count = work_set.count()
        work_set = work_set.paginate(page, size)

        data = WorkAdminListSerialize(many=True).dump(work_set.items)

        return self.report.table(*(data, count))

    @request_url(WorkAdminDetailByIdSchema)
    def work_admin_detail(self, form_data):
        """获取排班详情详情"""
        id = form_data.get('id')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            WorkAdmin.data_center_id == data_center_id,
            WorkAdmin.is_valid != IsValid.Deleted,
            WorkAdmin.id == id
        ]

        work_admin = WorkAdmin.query.filter(*query_list).first()
        if not work_admin:
            return self.report.error("找不到该id的排班")

        data = WorkAdminInfoDetailSerialize().dump(work_admin)

        return self.report.post(data)

    @request_url(WorkAdminCreateSchema)
    @flow_decorator(FlowServiceWorkAdmin)
    def work_admin_create(self, form_data):
        """新增排班"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(WorkAdmin, 'PB')
        form_data['is_draft'] = IsDraft.NORMAL

        detail_set = form_data.pop('detail_set')
        try:
            instance = WorkAdmin(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 创建排班明细
            for detail in detail_set:
                detail.pop('operation')
                detail['id'] = None
                detail['work_admin_id'] = instance.id

                detail_instance = WorkAdminDetail(**detail)
                LieYingApp.db.session.add(detail_instance)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        # todo 测试直接写入数据到面板，后续需要到审批通过后才执行本步骤
        async_write_panel_data.apply_async(args=(instance.id,), countdown=5, queue='async_task')

        g.fid = instance.id
        return self.report.suc('新增排班成功')

    @request_url(WorkAdminUpdateSchema)
    @flow_decorator(FlowServiceWorkAdmin)
    def work_admin_update(self, form_data):
        """编辑排班"""
        work_set = WorkAdmin.query.filter_by(id=form_data['id'])
        instance = work_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的排班')

        form_data['is_draft'] = IsDraft.NORMAL
        detail_set = form_data.pop('detail_set')
        try:
            work_set.update(form_data)
            LieYingApp.db.session.flush()

            # 遍历处理明细
            for detail in detail_set:
                operation = detail.pop('operation')
                if operation == OperationType.ADD:
                    detail['id'] = None
                    detail['work_admin_id'] = instance.id

                    detail_instance = WorkAdminDetail(**detail)
                    LieYingApp.db.session.add(detail_instance)
                elif operation == OperationType.UPDATE:
                    WorkAdminDetail.query.filter_by(id=detail['id']).update(detail)
                elif operation == operation == OperationType.DELETE:
                    WorkAdminDetail.query.filter_by(id=detail['id']).delete()

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        # todo 测试直接写入数据到面板,后续需要到审批通过后才执行本步骤
        async_write_panel_data.apply_async(args=(instance.id,), countdown=5, queue='async_task')

        g.fid = instance.id
        return self.report.suc('修改人员排班成功')

    @request_url(WorkAdminSaveDraftSchema)
    def work_admin_draft_save(self, form_data):
        """保存草稿"""
        id = form_data.get('id')
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        if not id:
            # 注入数据
            InjectionDataService(form_data).inject_data_center()
            InjectionDataService(form_data).inject_creator()
            InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(WorkAdmin, 'PB')

            detail_set = form_data.pop('detail_set')
            try:
                instance = WorkAdmin(**form_data)
                LieYingApp.db.session.add(instance)
                LieYingApp.db.session.flush()

                # 创建排班明细
                for detail in detail_set:
                    detail.pop('operation')
                    detail['id'] = None
                    detail['work_admin_id'] = instance.id

                    detail_instance = WorkAdminDetail(**detail)
                    LieYingApp.db.session.add(detail_instance)

            except Exception as e:
                LieYingApp.db.session.rollback()
                raise e
        else:
            work_set = WorkAdmin.query.filter_by(id=form_data['id'])
            instance = work_set.first()
            if not instance:
                return self.report.error('执行更新时找不到对应id的排班')
            detail_set = form_data.pop('detail_set')
            try:
                work_set.update(form_data)
                LieYingApp.db.session.flush()

                # 遍历处理明细
                for detail in detail_set:
                    operation = detail.pop('operation')
                    if operation == OperationType.ADD:
                        detail['id'] = None
                        detail['work_admin_id'] = instance.id

                        detail_instance = WorkAdminDetail(**detail)
                        LieYingApp.db.session.add(detail_instance)
                    elif operation == OperationType.UPDATE:
                        WorkAdminDetail.query.filter_by(id=detail['id']).update(detail)
                    elif operation == operation == OperationType.DELETE:
                        WorkAdminDetail.query.filter_by(id=detail['id']).delete()

            except Exception as e:
                LieYingApp.db.session.rollback()
                raise e

        return self.report.suc('保存排班草稿成功')


work_admin_module = WorkAdminModule()
