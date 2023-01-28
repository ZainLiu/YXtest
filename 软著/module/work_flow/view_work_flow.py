import logging

from flask import g, current_app
from ly_kernel.Module import ModuleBasic, request_url
from ly_service.request.RpcFunc import RpcFuncService
from sqlalchemy import desc

from models import IsValid, FlowStatus
from models.work_flow import WorkFlow, WorkFlowDetail
from model_to_view.work_flow.schema import FlowHandleSchema, FlowRevokeSchema, FlowLaunchSchema, FlowListSchema, \
    WithFormSchema
from model_to_view.work_flow.serializer import FlowListSerialize
from utils.flow_manager import FlowManager
from utils.msg_push import MsgPushService


class FlowModule(ModuleBasic):
    """审批相关操作"""

    @request_url(FlowLaunchSchema)
    def launch(self):
        """审批发起"""
        return self.report.post({"desc": "发起审批"})

    @request_url(FlowHandleSchema)
    def handle(self, req_data):
        """审批处理"""
        try:
            flow_id, push_list = FlowManager().flow_handle()
            # if flow_id and push_list:
            #     MsgPushService().push_msg(push_list)
            return self.report.suc('流程处理成功')
        except Exception as e:
            logging.exception(e)
            return self.report.error(f'流程处理失败，原因：{e}')

    @request_url(FlowRevokeSchema)
    def revoke(self, req_data):
        """审批撤回"""
        try:
            FlowManager().flow_revoke()
            return self.report.suc('流程撤回成功')
        except Exception as e:
            logging.exception(e)
            return self.report.error(f'流程撤回失败，原因：{e}')

    @request_url(FlowListSchema)
    def list(self, req_data):
        """审批列表"""
        id = req_data.get('id')
        query_type = req_data.get('query_type')
        title = req_data.get('title')
        creator_name = req_data.get('creator_name')
        page = req_data.get('page')
        size = req_data.get('size')

        query_list = []
        if id:
            query_list.append(WorkFlow.id == id)
        if query_type:
            if query_type == 'backlog':
                detail_queryset = WorkFlowDetail.query.filter(*[
                    WorkFlowDetail.state == None,
                    WorkFlowDetail.creator_id == g.uid
                ]).all()
                flow_id_list = [detail.detail_flow_id for detail in detail_queryset]
                query_list.append(WorkFlow.id.in_(flow_id_list))
                query_list.append(WorkFlow.is_valid == IsValid.Invalid)

            if query_type == 'sent':
                query_list.append(WorkFlow.creator_id == g.uid)
                query_list.append(WorkFlow.is_valid.in_([IsValid.Valid, IsValid.Invalid, IsValid.LoseValid]))

            if query_type == 'done':
                detail_queryset = WorkFlowDetail.query.filter(*[
                    WorkFlowDetail.state != None,
                    WorkFlowDetail.creator_id == g.uid
                ]).all()
                flow_id_list = [detail.detail_flow_id for detail in detail_queryset]
                query_list.append(WorkFlow.id.in_(flow_id_list))

        if title:
            query_list.append(WorkFlow.title.like(f'%{title}%'))
        if creator_name:
            data = RpcFuncService(1, 'centerApp').get_user_list_by_user_name(creator_name)
            query_ids = [item['id'] for item in data['data'] if item.get('id')]
            query_list.append(WorkFlow.creator_id.in_(query_ids))

        query_set = WorkFlow.query.filter(*query_list).order_by(desc(WorkFlow.id))
        count = query_set.count()

        try:
            query_set = query_set.paginate(page, size)
        except:
            query_set = query_set.paginate(1, size)

        data = FlowListSerialize(many=True).dump(query_set.items)

        return self.report.table(*(data, count))

    @request_url(WithFormSchema)
    def with_form(self, req_data):
        """根据表单查询电子流"""
        form = req_data.get('form')
        form_id = req_data.get('form_id')

        form_info = current_app.register_flow.get(form)
        if not form_info:
            return self.report.error('form不存在，检查是否被加载')
        model = form_info.get('model')
        instance = model.query.filter_by(id=form_id).first()
        if not instance:
            return self.report.error('表单对象不存在')

        work_flow_set = WorkFlow.query.filter_by(form_code=form, form_id=form_id).order_by(WorkFlow.create_time)
        data = {
            # 本单的所有流程
            "flow": FlowListSerialize(many=True).dump(work_flow_set),
            "sub_flow": []
        }

        sub_queryset = None
        if hasattr(instance, 'parent_id'):
            sub_queryset = model.query.filter_by(parent_id=instance.id, is_valid=IsValid.Invalid,
                                                 flow_status=FlowStatus.OnGoing)
        if sub_queryset:
            # 子单流程
            if sub_queryset.count() > 1:
                return self.report.error('请检查数据，同时只能存在一个在流转中的子单流程')
            sub_instance = sub_queryset.first()
            if sub_instance:
                sub_flow_queryset = WorkFlow.query.filter_by(form_code=form, form_id=sub_instance.id).order_by(
                    WorkFlow.create_time)

                data['sub_flow'] = FlowListSerialize(many=True).dump(sub_flow_queryset)

        return self.report.post(data)


flow_module = FlowModule()
