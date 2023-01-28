import datetime
import traceback

from flask import g
from ly_kernel.Module import ModuleBasic, request_url

from models import EventType, EventLevel, db, IsActive, YesOrNo, IsValid, EventStatus, EventOperateType
from models.equipment import EquipmentSystem, Equipment
from models.rostering.people_group import PeopleGroup, GroupType
from models.upcoming import Upcoming, UpcomingType
from module.event.flow_service import FlowServiceEvent, FlowServiceESW
from module.event.serializers.schema import *
from module.event.serializers.serializer import *
from module.rostering_work_handover.service import get_now_work_type
from utils.code_util import CodeUtil
from utils.flow_decorator import flow_decorator
from utils.injection_data import set_creator_and_belong_user_info
from utils.rpc_func import get_user_current_data_center_id
from utils.serial_number_service import get_serial_number_with_dc_code


class EventModule(ModuleBasic):
    """事件模块"""

    def trigger_to_do(self, eq_sys_id, dc_id, event, level, exclude_user_id_list=None):
        """触发待办"""
        pg = PeopleGroup.query.filter_by(data_center_id=dc_id, equipment_system_id=eq_sys_id,
                                         type=GroupType.Major, is_active=IsActive.Active).first()
        if pg:
            for pgm in pg.member_set.all():
                if exclude_user_id_list:
                    if pgm.user_id in exclude_user_id_list:
                        continue
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = dc_id
                upcoming_obj.upcoming_type = UpcomingType.ACCEPT_EVENT
                upcoming_obj.title = f'受理事件-{event.serial_number}'
                upcoming_obj.form_code = Event.__name__
                upcoming_obj.form_id = event.id
                upcoming_obj.user_id = pgm.user_id
                db.session.add(upcoming_obj)
        # 等级四给值班人员也发待办
        if level == EventLevel.Four:
            user_list = get_now_work_type(dc_id)
            for user_id in user_list:
                if exclude_user_id_list:
                    if user_id in exclude_user_id_list:
                        continue
                upcoming_obj = Upcoming()
                upcoming_obj.data_center_id = dc_id
                upcoming_obj.upcoming_type = UpcomingType.ACCEPT_EVENT
                upcoming_obj.title = f'受理事件-{event.serial_number}'
                upcoming_obj.form_code = Event.__name__
                upcoming_obj.form_id = event.id
                upcoming_obj.user_id = user_id
                db.session.add(upcoming_obj)

    def get_accept_user_id_list(self, event):
        upcoming_set = Upcoming.query.filter_by(data_center_id=event.data_center_id,
                                                upcoming_type=UpcomingType.ACCEPT_EVENT,
                                                form_code=Event.__name__,
                                                form_id=event.id,
                                                is_valid=IsValid.Valid).all()
        uc_user_id_list = [upcoming.user_id for upcoming in upcoming_set]
        return uc_user_id_list

    def cancel_all_upcoming(self, event):
        Upcoming.query.filter(Upcoming.data_center_id == event.data_center_id,
                              Upcoming.upcoming_type == UpcomingType.ACCEPT_EVENT,
                              Upcoming.form_code == Event.__name__,
                              Upcoming.form_id == event.id,
                              Upcoming.is_valid == IsValid.Valid).update({"is_valid": IsValid.Deleted})

    @request_url(EventSubmitSchema)
    def event_submit(self, form_data):
        # 保存数据
        if form_data["type"] == EventType.Eq and not form_data.get("eq_id"):
            return self.report.error("设备事件必传设备equipment_id字段")
        if form_data["type"] == EventType.Env and not form_data.get("room_id"):
            return self.report.error("环境事件必传设备room_id字段")

        if form_data["level"] != EventLevel.Four and not form_data.get("solve_time"):
            return self.report.error("事件等级四以上，必须填写抢通时间")

        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        try:
            if form_data.get("id"):
                event = Event.query.filter_by(id=form_data["id"]).first()
            else:
                event = Event()
                eq_sys = EquipmentSystem.query.filter_by(id=form_data["eq_sys_id"]).first()
                event.serial_number = get_serial_number_with_dc_code(Event, f"{eq_sys.code}E", dc_id)
                if form_data.get("form_id") and form_data.get("form_code"):
                    event.form_id = form_data["form_id"]
                    event.form_code = form_data["form_code"]
                event.equipment_system_id = form_data["eq_sys_id"]
                event.data_center_id = dc_id
                set_creator_and_belong_user_info(event)
            event.level = form_data["level"]
            if form_data["type"] == EventType.Eq:
                event.equipment_id = form_data["eq_id"]
            else:
                event.data_center_room_id = form_data["room_id"]
            event.type = form_data["type"]
            event.occur_time = form_data["occur_time"]
            if form_data["level"] != EventLevel.Four:
                event.solve_time = form_data["solve_time"]
            event.description = form_data["description"]
            event.annex = form_data["annex"]
            event.is_draft = YesOrNo.NO
            event.is_submit = YesOrNo.YES
            db.session.add(event)
            db.session.flush()
            # 触发待办
            self.trigger_to_do(form_data["eq_sys_id"], dc_id, event, form_data["level"])

        except Exception as e:
            db.session.rollback()
            return self.report.error(f"提交失败：{e}")
        db.session.commit()
        return self.report.suc("提交成功")

    @request_url(EventSaveSchema)
    def event_save(self, form_data):
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        if not form_data.get("type"):
            return self.report.error("事件类型必传")
        # 以下字段草稿也不能乱填
        if form_data.get("type") == EventType.Eq and not form_data.get("eq_id"):
            return self.report.error("设备事件必传设备equipment_id字段")
        if form_data.get("type") == EventType.Env and not form_data.get("room_id"):
            return self.report.error("环境事件必传设备room_id字段")

        if form_data.get("level") != EventLevel.Four and not form_data.get("solve_time"):
            return self.report.error("事件等级四以上，必须填写抢通时间")
        if form_data.get("id"):
            event = Event.query.filter_by(id=form_data["id"]).first()
        else:
            event = Event()
            eq_sys = EquipmentSystem.query.filter_by(id=form_data["eq_sys_id"]).first()
            event.serial_number = get_serial_number_with_dc_code(Event, f"{eq_sys.code}E", dc_id)
            if form_data.get("form_id") and form_data.get("form_code"):
                event.form_id = form_data["form_id"]
                event.form_code = form_data["form_code"]
            event.equipment_system_id = form_data["eq_sys_id"]
            event.data_center_id = dc_id
            set_creator_and_belong_user_info(event)
        event.level = form_data["level"]
        if form_data["type"] == EventType.Eq:
            eq = Equipment.query.filter_by(id=form_data["eq_id"]).first()
            event.equipment_id = eq.id
            event.data_center_room_id = eq.data_center_room_id
        else:
            event.data_center_room_id = form_data["room_id"]
        event.type = form_data["type"]
        event.occur_time = form_data["occur_time"]
        if form_data["level"] != EventLevel.Four:
            event.solve_time = form_data["solve_time"]
        event.description = form_data["description"]
        event.annex = form_data["annex"]
        db.session.add(event)

        return self.report.suc("保存成功")

    @request_url(EventAcceptSchema)
    def event_accept(self, form_data):
        try:
            event = Event.query.filter_by(id=form_data["id"]).first()
            if not event:
                return self.report.error("暂无相关数据")
            if event.status == EventStatus.Suspended and event.current_acceptor_id != g.uid:
                return self.report.error("挂起的事件只能挂起人自己重新受理")
            if event.status == EventStatus.Accepting:
                return self.report.error("该事件已被受理")
            uc_user_id_list = self.get_accept_user_id_list(event)
            if g.uid not in uc_user_id_list:
                return self.report.error("你不在该任务的待办列表，不能受理")
            # 加锁防重复受理
            redis_key = f"event_accept_{event.id}"
            if not LieYingApp.redis.setnx(redis_key, 1):
                return self.report.error("该事件正在受理中，请稍后再试")
            event.status = EventStatus.Accepting
            event.current_acceptor_id = g.uid
            event.current_acceptor_name = g.account
            db.session.add(event)
            # 生成一条处理明细，挂起重新受理沿用旧的处理明细
            if event.status != EventStatus.Suspended:
                epd = EventProcessingDetail()
                epd.event_id = event.id
                epd.handler_id = g.uid
                epd.handler_name = g.account
                epd.start_time = datetime.datetime.now()
                db.session.add(epd)

            # 去掉其他人的待办
            Upcoming.query.filter(Upcoming.data_center_id == event.data_center_id,
                                  Upcoming.upcoming_type == UpcomingType.ACCEPT_EVENT,
                                  Upcoming.form_code == Event.__name__,
                                  Upcoming.form_id == event.id,
                                  Upcoming.is_valid == IsValid.Valid,
                                  Upcoming.user_id != g.uid).update({"is_valid": IsValid.Deleted})
        except Exception as e:
            db.session.rollback()
            LieYingApp.redis.delete(redis_key)
            return self.report.error(f"受理失败：{traceback.print_exc()}")
        db.session.commit()
        LieYingApp.redis.delete(redis_key)
        return self.report.suc("受理成功")

    @request_url(EventProcessDetailSchema)
    @flow_decorator(FlowServiceEvent)
    def event_complete(self, form_data):
        """事件完成走审批"""
        return self.fill_event_process_detail(form_data, operate_type=EventOperateType.Complete)

    @request_url(EventProcessDetailSchema)
    def event_follow(self, form_data):
        """事件跟进不走审批"""
        return self.fill_event_process_detail(form_data, operate_type=EventOperateType.Follow)

    def fill_event_process_detail(self, form_data, operate_type):
        """填写细节"""
        event = Event.query.filter_by(id=form_data["id"]).first()
        if not event:
            return self.report.error("暂无相关事件数据")
        if event.current_acceptor_id != g.uid:
            return self.report.error("你不是当前处理人，无法操作")

        epd = EventProcessingDetail.query.filter_by(event_id=event.id, handler_id=event.current_acceptor_id).first()
        if not epd:
            return self.report.error("暂无相关事件处理明细数据")
        # if epd.handler_id != g.uid:
        #     return self.report.error("你不是时间处理明细的受理人，不能操作")
        first_detail = event.epd_set.first()
        if first_detail.id == epd.id:
            if not form_data.get("estimated_recovery_time"):
                return self.report.error("第一个处理人须填写预计恢复时间")
            else:
                epd.estimated_recovery_time = form_data.get("estimated_recovery_time")
        try:
            epd.end_time = datetime.datetime.now()
            epd.description = form_data["description"]
            epd.annex = form_data["annex"]
            epd.operate_type = operate_type
            epd.is_filled = YesOrNo.YES
            # 完成
            if operate_type == EventOperateType.Complete:
                event.status = EventStatus.Completed
                event.real_recovery_time = datetime.datetime.now()
                self.cancel_all_upcoming(event)
            # 持续跟进
            else:
                event.status = EventStatus.NonAccept
                event.is_followed = YesOrNo.YES
                # 增加其他人的待办
                self.trigger_to_do(event.equipment_system_id, event.data_center_id, event, event.level,
                                   exclude_user_id_list=[g.uid])
            db.session.add(event)
            db.session.add(epd)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"操作失败{traceback.print_exc()}")
        db.session.commit()
        g.fid = event.id
        return self.report.suc("操作成功")

    @request_url(EventFallbackSchema)
    def event_fallback(self, form_data):
        """事件回退"""
        event = Event.query.filter_by(id=form_data["id"]).first()
        if not event:
            return self.report.error("暂无相关事件数据")
        uc_user_id_list = self.get_accept_user_id_list(event)
        if g.uid not in uc_user_id_list:
            return self.report.error("非可受理人无法回退")
        if event.status != EventStatus.NonAccept:
            return self.report.error("非未受理状态下的事件不能回退")
        if event.is_followed == YesOrNo.YES:
            return self.report.error("跟进中的事件不允许回退")
        try:
            event.is_draft = YesOrNo.YES
            db.session.add(event)
            # 取消所有待办
            self.cancel_all_upcoming(event)
        except Exception as e:
            db.session.rollback()
            return self.report.error(f"回退失败{traceback.print_exc()}")
        db.session.commit()
        return self.report.error("回退成功")

    @request_url(EventUpdateSchema)
    def event_escalate_to_problem(self, form_data):
        """升级为问题"""
        event = Event.query.filter_by(id=form_data["id"]).first()
        if not event:
            return self.report.error("暂无相关事件数据")
        if g.uid != event.current_acceptor_id:
            return self.report.error("非当前受理人无法升级为问题")
        try:
            event.status = EventStatus.Closed
            db.session.add(event)
            # 取消所有待办
            self.cancel_all_upcoming(event)
            # todo 创建一个问题然后给个id跳转过去？
        except Exception as e:
            db.session.rollback()
        db.session.commit()
        return self.report.suc("问题升级成功")

    @request_url(EventSuspendedSchema)
    @flow_decorator(FlowServiceESW)
    def event_suspended(self, form_data):
        """挂起"""
        event = Event.query.filter_by(id=form_data["id"]).first()
        if not event:
            return self.report.error("暂无相关事件数据")
        if event.status != EventStatus.Accepting:
            return self.report.error("非受理中的事件不能挂起")
        if event.current_acceptor_id != g.uid:
            return self.report.error("你不是该事件当前受理人，不能挂起")
        esw = EventSuspendedWorkflow()
        esw.serial_number = get_serial_number_with_dc_code(EventSuspendedWorkflow, "SJGQ", event.data_center_id)
        esw.event_id = event.id
        esw.reason = form_data["reason"]
        db.session.add(esw)
        db.session.commit()
        g.fid = esw.id
        return self.report.suc("发起挂起申请成功")

    @request_url(EventListSchema)
    def event_list(self, form_data):
        """事件列表"""
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [Event.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(Event.serial_number == form_data["serial_number"])
        if form_data.get("eq_sys_id"):
            filter_cond.append(Event.equipment_system_id == form_data["eq_sys_id"])
        if form_data.get("occur_start_time") and form_data.get("occur_end_time"):
            filter_cond.append(Event.occur_time >= form_data["occur_start_time"])
            filter_cond.append(Event.occur_time <= form_data["occur_end_time"])
        if form_data.get("recovery_start_time") and form_data.get("recovery_end_time"):
            filter_cond.append(Event.real_recovery_time >= form_data["recovery_start_time"])
            filter_cond.append(Event.real_recovery_time <= form_data["recovery_end_time"])
        event_set = Event.query.filter(*filter_cond).order_by(Event.id.desc()).paginate(form_data["page"],
                                                                                        form_data["size"])
        resp_data = EventListSerializer(many=True).dump(event_set.items)
        return self.report.table(resp_data, event_set.total)

    @request_url(EventListSimpleSchema)
    def event_list_simple(self, form_data):
        """事件选项"""
        dc_id = get_user_current_data_center_id(g.uid)
        if not dc_id:
            return self.report.error("用户当前没有切换到任何数据中心")
        filter_cond = [Event.data_center_id == dc_id]
        if form_data.get("serial_number"):
            filter_cond.append(Event.serial_number == form_data["serial_number"])
        if form_data.get("eq_sys_id"):
            filter_cond.append(Event.equipment_system_id == form_data["eq_sys_id"])
        if form_data.get("level"):
            filter_cond.append(Event.level == form_data["level"])

        event_set = Event.query.filter(*filter_cond).order_by(Event.id.desc()).paginate(form_data["page"],
                                                                                        form_data["size"])
        resp_data = EventListSimpleSerializer(many=True).dump(event_set.items)
        return self.report.table(resp_data, event_set.total)

    @request_url(EventDetailSchema)
    def event_detail(self, form_data):
        """事件详情"""
        event = Event.query.filter_by(id=form_data["id"]).first()
        if not event:
            return self.report.error("暂无相关事件数据")
        resp_data = EventDetailSerializer().dump(event)
        if event.form_id and event.form_code:
            register_info = current_app.register_flow.get(event.form_code)
            model = register_info.get('model')
            form = model.query.filter_by(id=event.form_id).first()
            resp_data["related_form_serial_number"] = form.serial_number
        else:
            resp_data["related_form_serial_number"] = None
        if event.type == EventType.Eq:
            resp_data["eq_name"] = event.equipment.name
            resp_data["manufacturer_name"] = event.equipment.manufacturer.name
            resp_data["eq_full_code"] = CodeUtil.get_eq_full_code(event.equipment)
        else:
            resp_data["eq_name"] = ""
            resp_data["manufacturer_name"] = ""
            resp_data["eq_full_code"] = ""
        resp_data["room_full_code"] = CodeUtil.get_room_full_code(event.data_center_room)
        if event.status == EventStatus.Completed and event.real_recovery_time:
            resp_data["duration"] = (event.real_recovery_time - event.occur_time).seconds / 60
        else:
            resp_data["duration"] = None

        # 事件处理详情
        epd_set = event.epd_set.filter_by(is_filled=YesOrNo.YES).all()
        epd_info = EventProcessingDetailSerializer(many=True).dump(epd_set)
        resp_data["epd_info"] = epd_info

        # 返回能接能受理的人的id列表
        user_can_accept_id_list = self.get_accept_user_id_list(event)
        resp_data["user_can_accept_id_list"] = user_can_accept_id_list

        # 事件挂起审批流信息
        esw_set = event.esw_set.all()
        esw_info = EventSuspendedWorkflowListSerializer(many=True).dump(esw_set)
        resp_data["esw_info"] = esw_info

        return self.report.post(resp_data)

    @request_url(EventSuspendedWorkflowDetailSchema)
    def esw_detail(self, form_data):
        """事件挂起审批流详情"""
        esw = EventSuspendedWorkflow.query.filter_by(id=form_data["id"]).first()
        if not esw:
            return self.report.error("相关数据不存在")
        resp_data = EventSuspendedWorkflowDetailSerializer().dump(esw)
        return self.report.post(resp_data)


event_module = EventModule()
