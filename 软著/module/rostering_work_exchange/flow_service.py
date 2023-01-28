import datetime

from ly_kernel.LieYing import LieYingApp
from flask import g

from model_to_view.rostering_work_exchange.serializer import WorkExchangeListSerialize
from models import FlowStatus, IsValid, YesOrNo, IsActive
from models.rostering.work_panel import WorkPanel, PanelType
from models.rostering.work_type import Type, WorkType
from utils.flow_base_service import FlowBaseService
from models.rostering.work_exchange import WorkExchangeApply, ApplyType


class FlowServiceWorkExchange(FlowBaseService):
    model = WorkExchangeApply
    form_serialize = WorkExchangeListSerialize
    serial_number = 'serial_number'
    form_name = '调班/调休管理'

    @staticmethod
    def exchange(form_obj):
        """调班"""
        for item in form_obj.detail_set:
            # 调班班次
            date = item.date
            self_work_type_id = item.self_work_type_id
            target_work_type_id = item.target_work_type_id
            # 换班班次
            exchange_date = item.exchange_date
            self_exchange_work_type_id = item.self_exchange_work_type_id
            target_exchange_work_type_id = item.target_exchange_work_type_id

            # 找到申请人的调班班次
            apply_work = WorkPanel.query.filter_by(
                data_center_id=form_obj.data_center_id,
                user_id=form_obj.user_id,
                date=date,
                panel_type=PanelType.STAFF
            ).first()

            # 找到调班人的调班班次
            target_work = WorkPanel.query.filter_by(
                data_center_id=form_obj.data_center_id,
                user_id=form_obj.target_user_id,
                date=date,
                panel_type=PanelType.STAFF
            ).first()

            # 调班班次互换
            apply_work_type_list = apply_work.work_type
            target_work_type_list = target_work.work_type
            new_apply_work_type_list, new_target_work_type_list = [], []
            for item in apply_work_type_list:
                if item['work_type_id'] == self_work_type_id:
                    new_target_work_type_list.append(item)
                else:
                    new_apply_work_type_list.append(item)
            for item in target_work_type_list:
                if item['work_type_id'] == target_work_type_id:
                    new_apply_work_type_list.append(item)
                else:
                    new_target_work_type_list.append(item)
            apply_work.work_type = new_apply_work_type_list
            target_work.work_type = target_work_type_list
            LieYingApp.db.session.add(apply_work)
            LieYingApp.db.session.add(target_work)

            # 找到申请人的换班班次
            apply_work_exchange = WorkPanel.query.filter_by(
                data_center_id=form_obj.data_center_id,
                user_id=form_obj.user_id,
                date=exchange_date,
                panel_type=PanelType.STAFF
            ).first()

            # 找到调班人的换班班次
            target_work_exchange = WorkPanel.query.filter_by(
                data_center_id=form_obj.data_center_id,
                user_id=form_obj.target_user_id,
                date=exchange_date,
                panel_type=PanelType.STAFF
            ).first()

            # 换班班次互换
            apply_work_type_exchange_list = apply_work_exchange.work_type
            target_work_type_exchange_list = target_work_exchange.work_type
            new_apply_work_type_exchange__list, new_target_work_type_exchange_list = [], []
            for item in apply_work_type_exchange_list:
                if item['work_type_id'] == self_exchange_work_type_id:
                    new_target_work_type_exchange_list.append(item)
                else:
                    new_apply_work_type_exchange__list.append(item)
            for item in target_work_type_exchange_list:
                if item['work_type_id'] == target_exchange_work_type_id:
                    new_apply_work_type_exchange__list.append(item)
                else:
                    new_target_work_type_exchange_list.append(item)

            apply_work_exchange.work_type = apply_work_type_exchange_list
            target_work_exchange.work_type = target_work_type_exchange_list
            LieYingApp.db.session.add(apply_work_exchange)
            LieYingApp.db.session.add(target_work_exchange)

    def rest(form_obj):
        """调休"""
        for item in form_obj.detail_set:
            # 调班班次
            date = item.date
            self_work_type_id = item.self_work_type_id

            # 找到申请人的班次
            apply_work = WorkPanel.query.filter_by(
                data_center_id=form_obj.data_center_id,
                user_id=form_obj.user_id,
                date=date,
                panel_type=PanelType.STAFF
            ).first()

            # 找到当前数据中心的休息班次id
            rest_work_type = WorkType.query.filter_by(data_center_id=form_obj.data_center_id, type=Type.REST,
                                                      is_active=IsActive.Active).first()
            # 调班班次互换
            apply_work_type_list = apply_work.work_type
            new_apply_work_type_list, = []
            for item in apply_work_type_list:
                if item['work_type_id'] == self_work_type_id:
                    # 构建休息班次数据：{"work_type_id": 3, "work_type_name": "夜班", "work_type_style": "night-work"}
                    new_apply_work_type_list.append({
                        "work_type_id": rest_work_type.id,
                        "work_type_name": rest_work_type.name,
                        "work_type_style": "night-work"
                    })
                else:
                    new_apply_work_type_list.append(item)

            apply_work.work_type = new_apply_work_type_list
            LieYingApp.db.session.add(apply_work)

    def flow_create_func(form_obj):
        """审批创建后钩子【审批创建时锁定单】"""
        form_obj.flow_status = FlowStatus.OnGoing
        form_obj.last_editor_id = g.uid
        form_obj.is_lock = YesOrNo.YES

    def flow_pass_func(form_obj):
        """审批通过后钩子【审批通过时解锁单】"""
        try:
            # 修改调班/调休信息
            form_obj.current_approval_time = datetime.datetime.now()
            form_obj.is_valid = IsValid.Valid
            form_obj.flow_status = FlowStatus.Done
            form_obj.is_lock = YesOrNo.NO
            form_obj.last_editor_id = g.uid

            if form_obj.type == ApplyType.Exchange:
                # 调班：将双方对应的班调换
                FlowServiceWorkExchange.exchange(form_obj)

            elif form_obj.type == ApplyType.Rest:
                # 调休：将该班次替换成唯一的休息班次
                FlowServiceWorkExchange.rest(form_obj)

        except Exception as e:
            LieYingApp.db.session.rollback()
            raise e

    def flow_refuse_func(form_obj):
        """审批拒绝后钩子【审批拒绝时解锁单】"""
        form_obj.flow_status = FlowStatus.Reject
        form_obj.last_editor_id = g.uid
        form_obj.is_lock = YesOrNo.NO

    def flow_revoke_func(form_obj):
        """审批撤销后钩子【审批撤销时解锁单】"""
        form_obj.flow_status = FlowStatus.WithDraw
        form_obj.last_editor_id = g.uid
        form_obj.is_lock = YesOrNo.NO
