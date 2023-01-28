from flask import g, request
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc, and_, or_
from model_to_view.rostering_work_exchange.schema import WorkExchangeListSchema, WorkExchangeCreateSchema, \
    WorkExchangeUpdateSchema, WorkExchangeConfirmSchema, WorkExchangeDetailByIdSchema, WorkExchangeSaveDraftSchema
from model_to_view.rostering_work_exchange.serializer import WorkExchangeListSerialize
from models import IsValid, OperationType, IsActive, IsDraft, FlowStatus, YesOrNo
from models.rostering.work_exchange import WorkExchangeApply, WorkExchangeApplyDetail, ApplyType, ConfirmType, \
    ApplyStatus
from models.rostering.work_type import WorkType, Type
from models.upcoming import Upcoming, UpcomingType
from module.rostering_people_group.service.people_group_service import PeopleGroupService
from module.rostering_work_exchange.flow_service import FlowServiceWorkExchange
from utils.flow_decorator import flow_decorator
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id


class WorkExchangeModule(ModuleBasic):
    """调班/调休管理"""

    @request_url(WorkExchangeListSchema)
    def work_exchange_list(self, form_data):
        """查询调班/调休列表"""
        id = form_data.get('id')
        serial_number = form_data.get('serial_number')
        flow_status = form_data.get('flow_status')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [WorkExchangeApply.data_center_id == data_center_id, WorkExchangeApply.is_valid != IsValid.Deleted]
        if id:
            query_list.append(WorkExchangeApply.id == id)
        if serial_number:
            query_list.append(WorkExchangeApply.serial_number.like(f'%{serial_number}%'))
        if flow_status:
            query_list.append(WorkExchangeApply.flow_status == flow_status)

        # 只展示【自己创建的草稿】或者【别人创建的受理中/已完成】
        work_set = WorkExchangeApply.query.filter(
            and_(*query_list, or_(
                and_(
                    WorkExchangeApply.creator_id == g.uid,
                    WorkExchangeApply.is_draft == IsDraft.Draft
                ),
                and_(
                    WorkExchangeApply.apply_status.in_([ApplyStatus.DOING, ApplyStatus.DONE]))
            )
                 )
        ).order_by(desc(WorkExchangeApply.id))

        count = work_set.count()
        work_set = work_set.paginate(page, size)

        data = WorkExchangeListSerialize(many=True).dump(work_set.items)

        return self.report.table(*(data, count))

    @request_url(WorkExchangeDetailByIdSchema)
    def work_exchange_detail(self, form_data):
        """获取调班/调休详情"""
        id = form_data.get('id')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            WorkExchangeApply.data_center_id == data_center_id,
            WorkExchangeApply.is_valid != IsValid.Deleted,
            WorkExchangeApply.id == id
        ]

        work_exchange = WorkExchangeApply.query.filter(*query_list).first()
        if not work_exchange:
            return self.report.error("找不到该id的调班/调休")

        data = WorkExchangeListSerialize().dump(work_exchange)

        # 补充调班人分组
        target_group_info = PeopleGroupService.get_user_people_group(data_center_id, work_exchange.target_user_id)
        if target_group_info:
            data['target_group_id'] = target_group_info.get('id')
            data['target_group_name'] = target_group_info.get('name')

        return self.report.post(data)

    @request_url(WorkExchangeCreateSchema)
    @flow_decorator(FlowServiceWorkExchange)
    def work_exchange_create(self, form_data):
        """新增调班/调休"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        # 找到当前数据中心的休息班次id
        rest_work_type = WorkType.query.filter_by(data_center_id=data_center_id, type=Type.REST,
                                                  is_active=IsActive.Active).first()
        if not rest_work_type:
            return self.report.error('当前数据中心没有设置【休息】班次')

        # 检查传入数据，如果是调班，子项中调班和申请必须要有一个是休息班次
        if form_data['type'] == ApplyType.Exchange:
            # 调班必须要有休息班次
            for item in form_data['detail_set']:
                check = True
                self_work_type_id = item['self_work_type_id']
                target_work_type_id = item['target_work_type_id']
                self_exchange_work_type_id = item['self_exchange_work_type_id']
                target_exchange_work_type_id = item['target_exchange_work_type_id']
                if self_work_type_id != rest_work_type.id and target_work_type_id != rest_work_type.id:
                    check = False
                if self_exchange_work_type_id != rest_work_type.id and target_exchange_work_type_id != rest_work_type.id:
                    check = False
                if not check:
                    return self.report.error('当前数据中心没有设置【休息】班次')
            # 调班时，检查调班人是否存在【锁定中】的调休
            query_list = [
                WorkExchangeApply.type == ApplyType.Rest,
                WorkExchangeApply.is_lock == YesOrNo.YES,
                WorkExchangeApply.user_id == form_data['target_user_id']
            ]
            has_apply = WorkExchangeApply.query.filter(*query_list).first()
            if has_apply:
                return self.report.error('调班人当前存在【审批中】的调休，不允许申请调班')

        else:
            # 调休时，检查申请人是否存在【锁定中】的调班
            query_list = [WorkExchangeApply.type == ApplyType.Exchange, WorkExchangeApply.is_lock == YesOrNo.YES]
            has_apply = WorkExchangeApply.query.filter(
                and_(*query_list, or_(
                    and_(WorkExchangeApply.user_id == g.uid),
                    and_(WorkExchangeApply.target_user_id == g.uid)
                ))).frist()
            if has_apply:
                return self.report.error('当前存在【审批中】的调班，不允许申请调休')

        # 注入数据
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(WorkExchangeApply, 'TB')

        form_data['is_draft'] = IsDraft.NORMAL
        if form_data['type'] == ApplyType.Exchange:
            form_data['apply_status'] = ApplyStatus.DOING
        else:
            form_data['apply_status'] = ApplyStatus.DONE
        detail_set = form_data.pop('detail_set')
        try:
            instance = WorkExchangeApply(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 创建调班/调休明细
            for detail in detail_set:
                detail.pop('operation')
                detail['id'] = None
                detail['exchange_id'] = instance.id

                detail_instance = WorkExchangeApplyDetail(**detail)
                LieYingApp.db.session.add(detail_instance)

            if form_data['type'] == ApplyType.Exchange:
                # 给调班人添加待办
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = get_user_current_data_center_id(g.uid)
                upcoming_obj.upcoming_type = UpcomingType.EXCHANGE_CONFIRM
                upcoming_obj.title = f'调班确认-{instance.serial_number}'
                upcoming_obj.form_code = WorkExchangeApply.__name__
                upcoming_obj.form_id = instance.id
                upcoming_obj.user_id = form_data['target_user_id']
                LieYingApp.db.session.add(upcoming_obj)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('新增调班/调休成功')

    @request_url(WorkExchangeUpdateSchema)
    @flow_decorator(FlowServiceWorkExchange)
    def work_exchange_update(self, form_data):
        """编辑调班/调休"""
        exchange_set = WorkExchangeApply.query.filter_by(id=form_data['id'])
        instance = exchange_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的调班/调休记录')

        form_data['is_draft'] = IsDraft.NORMAL
        if form_data['type'] == ApplyType.Exchange:
            form_data['apply_status'] = ApplyStatus.DOING
        else:
            form_data['apply_status'] = ApplyStatus.DONE
        detail_set = form_data.pop('detail_set')
        try:
            exchange_set.update(form_data)
            LieYingApp.db.session.flush()

            # 遍历处理明细
            for detail in detail_set:
                operation = detail.pop('operation')
                if operation == OperationType.ADD:
                    detail['id'] = None
                    detail['exchange_id'] = instance.id

                    detail_instance = WorkExchangeApplyDetail(**detail)
                    LieYingApp.db.session.add(detail_instance)
                elif operation == OperationType.UPDATE:
                    WorkExchangeApplyDetail.query.filter_by(id=detail['id']).update(detail)
                elif operation == operation == OperationType.DELETE:
                    WorkExchangeApplyDetail.query.filter_by(id=detail['id']).delete()

            if form_data['type'] == ApplyType.Exchange:
                # 给调班人添加待办
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = get_user_current_data_center_id(g.uid)
                upcoming_obj.upcoming_type = UpcomingType.EXCHANGE_CONFIRM
                upcoming_obj.title = f'调班确认-{instance.serial_number}'
                upcoming_obj.form_code = WorkExchangeApply.__name__
                upcoming_obj.form_id = instance.id
                upcoming_obj.user_id = form_data['target_user_id']
                LieYingApp.db.session.add(upcoming_obj)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('修改调班/调休成功')

    @request_url(WorkExchangeConfirmSchema)
    @flow_decorator(FlowServiceWorkExchange)
    def work_exchange_confirm(self, form_data):
        """调班人确认"""
        exchange_set = WorkExchangeApply.query.filter_by(id=form_data['id'])
        instance = exchange_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的调班/调休记录')

        if instance.target_user_id != g.uid:
            return self.report.error('你不是该记录的调班人，不能进行确认')

        # 删除待办记录
        Upcoming.query.filter_by(form_code=WorkExchangeApply.__name__, form_id=form_data['id'], user_id=g.uid) \
            .update({'is_valid': IsValid.Deleted})

        if form_data['operation'] == ConfirmType.BACK:
            # 回退，给申请人创建回退待办
            upcoming_obj = Upcoming()
            upcoming_obj.data_center_id = get_user_current_data_center_id(g.uid)
            upcoming_obj.upcoming_type = UpcomingType.EXCHANGE_BACK
            upcoming_obj.title = f'调班回退-{instance.serial_number}'
            upcoming_obj.form_code = WorkExchangeApply.__name__
            upcoming_obj.form_id = instance.id
            upcoming_obj.user_id = instance.user_id
            LieYingApp.db.session.add(upcoming_obj)

            # 表单恢复成草稿状态
            instance.is_draft = IsDraft.Draft
            instance.apply_status = ApplyStatus.NOT_CONFIRM
            LieYingApp.db.session.add(instance)

        g.fid = instance.id
        return self.report.suc('确认成功')

    @request_url(WorkExchangeSaveDraftSchema)
    def work_exchange_draft_save(self, form_data):
        """保存草稿"""
        id = form_data.get('id')
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        if not id:
            # 注入数据
            InjectionDataService(form_data).inject_data_center()
            InjectionDataService(form_data).inject_creator()
            InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(WorkExchangeApply, 'TB')

            form_data['apply_status'] = ApplyStatus.NOT_CONFIRM
            detail_set = form_data.pop('detail_set')
            try:
                instance = WorkExchangeApply(**form_data)
                LieYingApp.db.session.add(instance)
                LieYingApp.db.session.flush()

                # 创建调班/调休明细
                for detail in detail_set:
                    detail.pop('operation')
                    detail['id'] = None
                    detail['exchange_id'] = instance.id

                    detail_instance = WorkExchangeApplyDetail(**detail)
                    LieYingApp.db.session.add(detail_instance)

            except Exception as e:
                LieYingApp.db.session.rollback()
                raise e
        else:
            exchange_set = WorkExchangeApply.query.filter_by(id=form_data['id'])
            instance = exchange_set.first()
            if not instance:
                return self.report.error('执行更新时找不到对应id的调班/调休记录')

            detail_set = form_data.pop('detail_set')
            try:
                exchange_set.update(form_data)
                LieYingApp.db.session.flush()

                # 遍历处理明细
                for detail in detail_set:
                    operation = detail.pop('operation')
                    if operation == OperationType.ADD:
                        detail['id'] = None
                        detail['exchange_id'] = instance.id

                        detail_instance = WorkExchangeApplyDetail(**detail)
                        LieYingApp.db.session.add(detail_instance)
                    elif operation == OperationType.UPDATE:
                        WorkExchangeApplyDetail.query.filter_by(id=detail['id']).update(detail)
                    elif operation == operation == OperationType.DELETE:
                        WorkExchangeApplyDetail.query.filter_by(id=detail['id']).delete()

            except Exception as e:
                LieYingApp.db.session.rollback()
                raise e

        return self.report.suc('保存调班/调休草稿成功')


work_exchange_module = WorkExchangeModule()
