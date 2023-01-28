import datetime

from flask import g, request
from ly_kernel.Module import ModuleBasic, request_url, LieYingApp
from sqlalchemy import desc, and_, or_
from model_to_view.rostering_work_handover.schema import WorkHandoverListSchema, WorkHandoverCreateSchema, \
    WorkHandoverUpdateSchema, WorkHandoverConfirmSchema, WorkHandoverDetailByIdSchema, WorkHandoverGetAcceptGroupSchema, \
    WorkHandoverDraftSchema
from model_to_view.rostering_work_handover.serializer import WorkHandoverListSerialize
from models import IsValid, OperationType, IsDraft, IsActive
from models.rostering.people_group import PeopleGroup, GroupType
from models.rostering.work_handover import WorkHandover, WorkHandoverDetail, HandoverType, ConfirmType
from models.rostering.work_panel import WorkPanel, PanelType
from models.rostering.work_type import WorkType, Type
from models.upcoming import Upcoming, UpcomingType
from utils.flow_decorator import flow_decorator
from config import current_config
from utils.injection_data import InjectionDataService
from utils.rpc_func import get_user_current_data_center_id
from utils.time_util import TimeUtil


class WorkHandoverModule(ModuleBasic):
    """交接班管理"""

    @request_url(WorkHandoverListSchema)
    def work_handover_list(self, form_data):
        """查询交接班列表"""
        id = form_data.get('id')
        serial_number = form_data.get('serial_number')
        group_name = form_data.get('group_name')
        page = form_data.get('page')
        size = form_data.get('size')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [WorkHandover.data_center_id == data_center_id, WorkHandover.is_valid != IsValid.Deleted]
        if id:
            query_list.append(WorkHandover.id == id)
        if serial_number:
            query_list.append(WorkHandover.serial_number.like(f'%{serial_number}%'))
        if group_name:
            query_list.append(WorkHandover.group_name == group_name)

        # 只展示【自己创建的草稿】或者【别人创建的受理中/已完成】
        handover_set = WorkHandover.query.filter(
            and_(*query_list, or_(
                and_(
                    WorkHandover.creator_id == g.uid,
                    WorkHandover.is_draft == IsDraft.Draft
                ),
                and_(
                    WorkHandover.handover_status.in_([HandoverType.DOING, HandoverType.DONE]))
            )
                 )
        ).order_by(desc(WorkHandover.id))

        count = handover_set.count()
        handover_set = handover_set.paginate(page, size)

        data = WorkHandoverListSerialize(many=True).dump(handover_set.items)

        return self.report.table(*(data, count))

    @request_url(WorkHandoverDetailByIdSchema)
    def work_handover_detail(self, form_data):
        """获取交接班详情"""
        id = form_data.get('id')

        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        query_list = [
            WorkHandover.data_center_id == data_center_id,
            WorkHandover.is_valid != IsValid.Deleted,
            WorkHandover.id == id
        ]

        work_handover = WorkHandover.query.filter(*query_list).first()
        if not work_handover:
            return self.report.error("找不到该id的交接班")

        data = WorkHandoverListSerialize().dump(work_handover)

        return self.report.post(data)

    @request_url(WorkHandoverCreateSchema)
    def work_handover_create(self, form_data):
        """新增交接班"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        # 注入数据
        InjectionDataService(form_data).inject_now_time('hand_time')
        InjectionDataService(form_data).inject_data_center()
        InjectionDataService(form_data).inject_creator()
        InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(WorkHandover, 'JJ')
        InjectionDataService(form_data).inject_people_group('group_id', 'group_name')

        # 检查自身的班组是否是【值班组】，如果不是，不让发起
        self_group_id = form_data['group_id']
        self_group = PeopleGroup.query.filter_by(id=self_group_id).first()
        if not self_group or self_group.type != GroupType.Duty:
            return self.report.error('当前不为【值班组】成员，不让发起交班')
        # 检查接班班组是否时【值班组】，如果不是，不让发起
        accept_group_id = form_data['accept_group_id']
        accept_group = PeopleGroup.query.filter_by(id=accept_group_id).first()
        if not accept_group or accept_group.type != GroupType.Duty:
            return self.report.error('接班班组不为【值班组】，不让发起交班')

        form_data['is_draft'] = IsDraft.NORMAL
        form_data['handover_status'] = HandoverType.DOING
        detail_set = form_data.pop('detail_set')
        try:
            instance = WorkHandover(**form_data)
            LieYingApp.db.session.add(instance)
            LieYingApp.db.session.flush()

            # 创建交接班明细
            for detail in detail_set:
                detail.pop('operation')
                detail['id'] = None
                detail['handover_id'] = instance.id

                detail_instance = WorkHandoverDetail(**detail)
                LieYingApp.db.session.add(detail_instance)

            # 给交班分组所有人添加待办
            group = PeopleGroup.query.filter_by(id=instance.accept_group_id).first()
            member_set = group.member_set.all()

            for member in member_set:
                print('交班人员打印：', member.user_id)
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = get_user_current_data_center_id(g.uid)
                upcoming_obj.upcoming_type = UpcomingType.HANDOVER_CONFIRM
                upcoming_obj.title = f'交接班确认-{instance.serial_number}'
                upcoming_obj.form_code = WorkHandover.__name__
                upcoming_obj.form_id = instance.id
                upcoming_obj.user_id = member.user_id
                LieYingApp.db.session.add(upcoming_obj)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('新增交接班成功')

    @request_url(WorkHandoverUpdateSchema)
    def work_handover_update(self, form_data):
        """编辑交接班"""
        handover_set = WorkHandover.query.filter_by(id=form_data['id'])
        instance = handover_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的交接班记录')

        form_data['is_draft'] = IsDraft.NORMAL
        form_data['handover_status'] = HandoverType.DOING
        detail_set = form_data.pop('detail_set')
        try:
            handover_set.update(form_data)
            LieYingApp.db.session.flush()

            # 遍历交接班明细
            for detail in detail_set:
                operation = detail.pop('operation')
                if operation == OperationType.ADD:
                    detail['id'] = None
                    detail['handover_id'] = instance.id

                    detail_instance = WorkHandoverDetail(**detail)
                    LieYingApp.db.session.add(detail_instance)
                elif operation == OperationType.UPDATE:
                    WorkHandoverDetail.query.filter_by(id=detail['id']).update(detail)
                elif operation == operation == OperationType.DELETE:
                    WorkHandoverDetail.query.filter_by(id=detail['id']).delete()

            # 给接班分组所有人添加待办添加待办
            group = PeopleGroup.query.filter_by(id=instance.accept_group_id).first()
            member_set = group.member_set.all()

            for member in member_set:
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = get_user_current_data_center_id(g.uid)
                upcoming_obj.upcoming_type = UpcomingType.HANDOVER_CONFIRM
                upcoming_obj.title = f'交接班确认-{instance.serial_number}'
                upcoming_obj.form_code = WorkHandover.__name__
                upcoming_obj.form_id = instance.id
                upcoming_obj.user_id = member.user_id
                LieYingApp.db.session.add(upcoming_obj)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

        g.fid = instance.id
        return self.report.suc('修改交接班成功')

    @request_url(WorkHandoverDraftSchema)
    def work_handover_draft_save(self, form_data):
        """保存草稿"""
        id = form_data.get('id')
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        if not id:
            # 注入数据
            InjectionDataService(form_data).inject_now_time('hand_time')
            InjectionDataService(form_data).inject_data_center()
            InjectionDataService(form_data).inject_creator()
            InjectionDataService(form_data).inject_unique_serial_number_with_dc_code(WorkHandover, 'JJ')
            InjectionDataService(form_data).inject_people_group('group_id', 'group_name')

            form_data['handover_status'] = HandoverType.NOT_ACCEPT
            detail_set = form_data.pop('detail_set')
            try:
                instance = WorkHandover(**form_data)
                LieYingApp.db.session.add(instance)
                LieYingApp.db.session.flush()

                # 创建交接班明细
                for detail in detail_set:
                    detail.pop('operation')
                    detail['id'] = None
                    detail['handover_id'] = instance.id

                    detail_instance = WorkHandoverDetail(**detail)
                    LieYingApp.db.session.add(detail_instance)

            except Exception as e:
                LieYingApp.db.session.rollback()
                raise e
        else:
            handover_set = WorkHandover.query.filter_by(id=form_data['id'])
            instance = handover_set.first()
            if not instance:
                return self.report.error('执行更新时找不到对应id的交接班记录')

            detail_set = form_data.pop('detail_set')
            try:
                handover_set.update(form_data)
                LieYingApp.db.session.flush()

                # 遍历交接班明细
                for detail in detail_set:
                    operation = detail.pop('operation')
                    if operation == OperationType.ADD:
                        detail['id'] = None
                        detail['handover_id'] = instance.id

                        detail_instance = WorkHandoverDetail(**detail)
                        LieYingApp.db.session.add(detail_instance)
                    elif operation == OperationType.UPDATE:
                        WorkHandoverDetail.query.filter_by(id=detail['id']).update(detail)
                    elif operation == operation == OperationType.DELETE:
                        WorkHandoverDetail.query.filter_by(id=detail['id']).delete()

            except Exception as e:
                LieYingApp.db.session.rollback()
                raise e

        return self.report.suc('保存交接班草稿成功')

    @request_url(WorkHandoverConfirmSchema)
    def work_handover_confirm(self, form_data):
        """交接班确认"""
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        handover_set = WorkHandover.query.filter_by(id=form_data['id'])
        instance = handover_set.first()
        if not instance:
            return self.report.error('执行更新时找不到对应id的交接班记录')

        # 删除接班分组下所有人的待办记录
        group = PeopleGroup.query.filter_by(id=instance.accept_group_id).first()
        user_ids = [member.user_id for member in group.member_set.all()]

        # 将待办表里面的记录置为删除
        query_list = [
            Upcoming.data_center_id == data_center_id,
            Upcoming.form_code == WorkHandover.__name__,
            Upcoming.form_id == form_data['id'],
            Upcoming.user_id.in_(user_ids)
        ]
        Upcoming.query.filter(*query_list).update({'is_valid': IsValid.Deleted}, synchronize_session=False)

        if form_data['operation'] == ConfirmType.BACK:
            # 回退 申请人创建回退待办
            upcoming_obj = Upcoming()
            upcoming_obj.data_center_id = get_user_current_data_center_id(g.uid)
            upcoming_obj.upcoming_type = UpcomingType.HANDOVER_BACK
            upcoming_obj.title = f'交接班回退-{instance.serial_number}'
            upcoming_obj.form_code = WorkHandover.__name__
            upcoming_obj.form_id = instance.id
            upcoming_obj.user_id = instance.creator_id
            LieYingApp.db.session.add(upcoming_obj)

            # 表单恢复成草稿状态
            instance.is_draft = IsDraft.Draft
            instance.handover_status = HandoverType.NOT_ACCEPT
            LieYingApp.db.session.add(instance)
        else:
            # 确认
            InjectionDataService(form_data).inject_now_time('accept_time')
            InjectionDataService(form_data).inject_people_group('accept_group_id', 'accept_group_name')
            instance.handover_status = HandoverType.DONE
            instance.handover_matter = form_data['handover_matter']
            instance.user_id = g.uid
            instance.user_name = g.account
            instance.accept_group_id = form_data['accept_group_id']
            instance.accept_group_name = form_data['accept_group_name']
            LieYingApp.db.session.add(instance)

        g.fid = instance.id
        return self.report.suc('确认成功')

    @request_url(WorkHandoverGetAcceptGroupSchema)
    def work_handover_get_accept_group(self, form_data):
        """
        获取接班班组列表,查找规则，原则是【只能交接给正在上班或者即将上班的班组】
        交接班找下一个值班班组：当前值班班次结束时间的当天日期有工作班次的值班班组，且非交班班组，且接班值班班组的班次结束时间＞交班班组的班次结束时间
        如果班次下班时间小于上班时间，那说明必然已经跨天了，不考虑上班24小时后的情况，例如：上班时间当天09点，下班时间第二天的10点
        """
        data_center_id = get_user_current_data_center_id(g.uid)
        if not data_center_id:
            return self.report.error("用户当前没有切换到任何数据中心")

        InjectionDataService(form_data).inject_people_group('group_id', 'group_name')
        # 先找到【当前值班班次】
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        work_panel = WorkPanel.query.filter_by(
            data_center_id=data_center_id,
            group_id=form_data['group_id'],
            date=now_date,
            panel_type=PanelType.GROUP
        ).first()
        if not work_panel:
            return self.report.error(f"找不到该数据中心对应的的排班数据：group_id:{form_data['group_id']}/date:{now_date}")
        work_type_id_list = [item.get('work_type_id') for item in work_panel.work_type if item.get('work_type_id')]
        if not work_type_id_list:
            return self.report.error('找不到【当前值班班次】')

        now_time = datetime.datetime.now()
        now_date = datetime.datetime.now().strftime('%Y-%m-%d')
        tomorrow_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

        work_type_list = WorkType.query.filter(WorkType.id.in_(work_type_id_list)).all()
        now_work_type = None
        is_crossing = False
        for work_type in work_type_list:
            # 排除休息
            if work_type.type == Type.REST:
                continue

            work_start = work_type.work_start.strftime(current_config.APP_TIME_FORMAT)
            work_end = work_type.work_end.strftime(current_config.APP_TIME_FORMAT)

            start_hour = work_start[:2]
            end_hour = work_end[:2]

            start_time = datetime.datetime.strptime(f'{now_date} {work_start}', current_config.APP_DATETIME_FORMAT)
            if int(end_hour) < int(start_hour):
                # 如果下班时间的【时】小于上班时间的【时】，说明已经跨天
                end_time = datetime.datetime.strptime(f'{tomorrow_date} {work_end}', current_config.APP_DATETIME_FORMAT)
                is_crossing = True
            else:
                end_time = datetime.datetime.strptime(f'{now_date} {work_end}', current_config.APP_DATETIME_FORMAT)

            # 比较当时时间是否在上班时间范围内，如果是，则说明这个班次就是现在的班次
            if now_time > start_time and now_time < end_time:
                now_work_type = work_type
                break

        if not now_work_type:
            return self.report.error('找不到当前值班班次')

        # 找到符合要求的值班班组
        # 找出数据中心下所有值班班组【排除当前班组】
        duty_group_set = PeopleGroup.query.filter_by(
            data_center_id=data_center_id,
            type=GroupType.Duty,
            is_active=IsActive.Active
        ).all()
        duty_group_ids = [people_group.id for people_group in duty_group_set if
                          people_group.id != form_data['group_id']]
        if not duty_group_ids:
            return self.report.error('找不到数据中心的值班班组')

        check_date = tomorrow_date if is_crossing else now_date
        work_panel_set = WorkPanel.query.filter(
            WorkPanel.data_center_id == data_center_id,
            WorkPanel.date == check_date,
            WorkPanel.group_id.in_(duty_group_ids),
            WorkPanel.panel_type == PanelType.GROUP
        ).all()

        result = []
        for work_panel in work_panel_set:
            # 接班值班班组的班次结束时间＞交班班组的班次结束时间
            wt_id_list = [item.get('work_type_id') for item in work_panel.work_type if item.get('work_type_id')]
            work_type_list = WorkType.query.filter(WorkType.id.in_(wt_id_list)).all()
            for work_type in work_type_list:
                # 排除休息
                if work_type.type == Type.REST:
                    continue
                accept_is_crossing = False
                # 接班班组的上下班时间
                accept_work_start = work_type.work_start.strftime(current_config.APP_TIME_FORMAT)
                accept_work_end = work_type.work_end.strftime(current_config.APP_TIME_FORMAT)

                accept_start_hour = accept_work_start[:2]
                accept_end_hour = accept_work_end[:2]

                if int(accept_end_hour) < int(accept_start_hour):
                    # 如果接班下班时间的【时】小于上班时间的【时】，说明已经跨天，找到该天的下班时间
                    accept_is_crossing = True

                if is_crossing and accept_is_crossing:
                    # 交班跨天，并且接班也跨天，则接班下班日期=当前日期+2
                    accept_end_date = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime(
                        current_config.APP_DATE_FORMAT)
                elif is_crossing and not accept_is_crossing:
                    # 交班跨天，但接班未跨天，则接班下班日期=当前日期+1
                    accept_end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime(
                        current_config.APP_DATE_FORMAT)
                elif not is_crossing and accept_is_crossing:
                    # 交班未跨天，但接班跨天，则接班下班日期=当前日期+1
                    accept_end_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime(
                        current_config.APP_DATE_FORMAT)
                elif not is_crossing and not accept_is_crossing:
                    # 交班未跨天，且接班未跨天，则接班下班日期=当前日期
                    accept_end_date = datetime.datetime.now().strftime(current_config.APP_DATE_FORMAT)
                else:
                    accept_end_date = datetime.datetime.now().strftime(current_config.APP_DATE_FORMAT)

                # 如果接班班组下班时间>交班班组下班时间，则可以接班
                now_work_type_end = now_work_type.work_end.strftime(current_config.APP_TIME_FORMAT)
                end_timestamp = TimeUtil().date_str_to_utc_timestamp(f'{check_date} {now_work_type_end}')
                accept_end_timestamp = TimeUtil().date_str_to_utc_timestamp(f'{accept_end_date} {accept_work_end}')

                if accept_end_timestamp > end_timestamp:
                    group_member_list = []
                    for member in work_panel.group.member_set:
                        group_member_list.append({
                            'id': member.id,
                            'user_id': member.user_id,
                            'user_name': member.user_name
                        })

                    result.append({
                        'group_id': work_panel.group_id,
                        'group_name': work_panel.group_name,
                        'work_type_id': work_type.id,
                        'work_type_name': work_type.name,
                        'work_type_start': work_type.work_start.strftime(current_config.APP_TIME_FORMAT),
                        'work_type_end': work_type.work_end.strftime(current_config.APP_TIME_FORMAT),
                        'group_member_list': group_member_list
                    })

        return self.report.post(result)


work_handover_module = WorkHandoverModule()
