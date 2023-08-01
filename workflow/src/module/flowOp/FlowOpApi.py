from ly_kernel.Module import ModuleBasic, request_url
from serializers.FlowOpSchema import FlowOpCreateSchema, FlowOpControlSchema, FlowGetNodeCompleteList
import module.flowTpl.FlowTplService as flowtplService
import module.flowOp.FlowOpService as flowopService
from models.FlowTpl import FlowTpl
from models.FlowOp import FlowOp
from libs.SpiffWorkflow.specs import WorkflowSpec
from libs.SpiffWorkflow.serializer.json import JSONSerializer
from libs.SpiffWorkflow import Workflow, Task
import json
from enums.FlowEnums import FlowOpType
from ly_kernel.LieYing import LieYingApp
from ly_service.request.RpcFunc import RpcFuncService
from ly_service.utils import Time
from enums.FlowEnums import SpecsNodeType, LeaderType

# 工作流 - 流转
from serializers.FlowTplSchema import FlowTplViewModelSchema

from serializers.FlowOpSchema import FlowOpReissueSchema, FlowOpNodeParamsSchema, FlowOpFallbackSchema, \
    FlowOpNodeCanFallbackListSchema

from serializers.FlowOpSchema import FlowOpFallbackPreNodeSchema


class FlowOpApiModule(ModuleBasic):
    """
    位运算得出当前，条件的类型，用户，还是角色

    节点返回：
        {
            用户ID，用户名
            角色ID，角色名
        }
    """

    @request_url(FlowOpCreateSchema)
    def create(self, req_data):

        db_tpl: FlowTpl = flowtplService.get_flow_tpl_by_id(req_data.get("tpl_id", 0))

        if db_tpl is None:
            return self.report.error("模板不存在")

        serializer = JSONSerializer()
        spec = WorkflowSpec.deserialize(serializer, json.dumps(db_tpl.specs_data))
        workflow = Workflow(spec)

        flow_op = FlowOp()

        my_leader = flow_op.get_my_leader(
            {"uid": req_data.get("uid"), "user": req_data.get("username")}
        ).get("my_leader")
        self._auto_comleted_task_node(workflow, req_data.get("params"), my_leader=my_leader)

        flow_op.add_logs({
            "uid": req_data.get("uid"),
            "user": req_data.get("username"),
            "time": Time.timeStampToFormatByDatetime(int(Time.currentTime())),
            "state": FlowOpType.CREATE.get_name(),
        })
        node_ready, _ = self._find_node_ready(workflow, my_leader)
        flow_op.update_node_ready(node_ready)
        flow_op.is_completed = workflow.is_completed()
        flow_op.specs_data = workflow.serialize(serializer)
        flow_op.params = json.dumps(req_data.get("params", {}))
        flow_op.add()

        return self.report.post(self._report_data(flow_op, FlowOpType.CREATE, temp_node_ready=node_ready))

    @request_url(FlowOpControlSchema)
    def flow_info(self, params):
        db_flow = flowopService.get_flow_op_by_id(params.get("flow_id"))

        if db_flow is None:
            return self.report.error("数据不存在")

        return self.report.post(self._report_data(db_flow))

    @request_url(FlowOpControlSchema)
    def flow_info_by_wf(self, params):
        db_flow = flowopService.get_flow_op_by_id(params.get("flow_id"))

        if db_flow is None:
            return self.report.error("数据不存在")

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)

        workflow.dump()

        return self.report.post(self._report_data(db_flow))

    @request_url(FlowOpControlSchema)
    def agree(self, params):
        return self.__control(params, FlowOpType.AGREE)

    @request_url(FlowOpControlSchema)
    def refuse(self, params):
        return self.__control(params, FlowOpType.REFUSE)

    @request_url(FlowOpControlSchema)
    def refuse_v2(self, params):
        return self.__refuse(params, FlowOpType.REFUSE)

    @request_url(FlowOpControlSchema)
    def revoke(self, params):
        return self.__control(params, FlowOpType.REVOKE)

    @request_url(FlowOpReissueSchema)
    def reissue(self, params):
        reissue_user_id = params.get("uid")

        db_tpl: FlowTpl = flowtplService.get_flow_tpl_by_id(params.get("tpl_id", 0))

        if db_tpl is None:
            return self.report.error("模板不存在")

        db_flow = flowopService.get_flow_op_by_id(params.get("flow_id"))  # 旧的流程

        if db_flow is None:
            return self.report.error("数据不存在")

        if reissue_user_id != db_flow.get_creator().get("uid"):
            return self.report.error("你不是发起者，不能重新发起流程")

        my_leader = db_flow.get_my_leader().get("my_leader")
        origin_params = json.loads(db_flow.params)
        new_params = params.get("params", {})
        origin_params.update(new_params)

        serializer = JSONSerializer()
        old_ready_node_name_list = db_flow.find_node_ready_noed_name()

        # 新生成分一条临时审批流，判断能否走到旧的节点，如果能则沿用旧的审批流
        spec = WorkflowSpec.deserialize(serializer, json.dumps(db_tpl.specs_data))
        new_workflow = Workflow(spec)
        self._auto_comleted_task_node(new_workflow, origin_params, my_leader=my_leader)

        can_reach = self._check_can_or_not_reach_old_node(new_workflow, old_ready_node_name_list)
        # 重新发起的参数可以到达旧的节点，用原来的流程
        if can_reach:
            db_flow.is_invalid = 0
            db_flow.is_completed = 0
            # 更新待办信息
            reissue_log = {
                "state": FlowOpType.REISSUE.get_name(),
                "time": Time.timeStampToFormatByDatetime(int(Time.currentTime())),
                "uid": db_flow.get_creator().get("uid"),
                "user": db_flow.get_creator().get("user")
            }
            db_flow.update_node_ready([], reissue_log=reissue_log)
            LieYingApp.db.session.add(db_flow)
            LieYingApp.db.session.commit()
            return self.report.post(self._report_data(db_flow, FlowOpType.REISSUE))
        # 重新发起的参数到达不了旧的节点，使用新的流程
        else:
            spec = WorkflowSpec.deserialize(serializer, json.dumps(db_tpl.specs_data))
            workflow = Workflow(spec)
            self._auto_comleted_task_node(workflow, params.get("params", {}), my_leader=my_leader)
            flow_op = FlowOp()
            flow_op.add_logs({
                "uid": params.get("uid"),
                "user": params.get("username"),
                "time": Time.timeStampToFormatByDatetime(int(Time.currentTime())),
                "state": FlowOpType.REISSUE.get_name(),
            })
            node_ready, _ = self._find_node_ready(workflow, my_leader)
            flow_op.update_node_ready(node_ready)
            flow_op.is_completed = workflow.is_completed()
            flow_op.specs_data = workflow.serialize(serializer)
            flow_op.params = json.dumps(params.get("params", {}))
            flow_op.add()

            return self.report.post(self._report_data(flow_op, FlowOpType.REISSUE))

    @request_url(FlowOpControlSchema)
    def toadd(self, params):

        """
        同意，并增加节点，在自动完成里，判断当时是否还有节点
        记录，上个节点的去向节点Id。。如果找到节点，发现有该节点，就跳过，等完成，才能出现
        """

        return self.__to_add(params)

    def __control(self, params, flow_type):
        params_approve_user_id = int(params.get("approve_user_id", 0))
        params_approve_user_name = params.get("approve_user_name", "")
        role_id = params.get("role_id", [])

        db_flow = flowopService.get_flow_op_by_id(params.get("flow_id"))

        if db_flow is None:
            return self.report.error("数据不存在")

        if db_flow.is_completed:
            return self.report.error("流程已结束")

        if db_flow.is_invalid:
            return self.report.error("流程已作废")

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)

        node_task_obj_id = None
        node_type = None
        node_obj = None
        if FlowOpType.REVOKE.get_id() != flow_type.get_id():  # 撤回不走下面的判断
            if params_approve_user_id > 0:

                node_obj = db_flow.find_node_ready_by_uid(params_approve_user_id, role_id=role_id)
                if node_obj is None:
                    return self.report.error("当前没有您的审核节点")

                node_task_obj_id = node_obj.get("node_id")
                node_type = node_obj.get("node_type")
            else:
                node_task_obj = workflow.get_task(params.get("node_id"))

                if node_task_obj is None:
                    return self.report.error("审核节点不存在")

                node_task_obj_id = node_task_obj.id
        else:
            # 只有上个节点的用户，才能申请撤回，不能跳节点
            if params_approve_user_id <= 0:
                return self.report.error("撤回没有操作者id")

            if params_approve_user_id != db_flow.get_creator().get("uid"):
                return self.report.error("你不是发起者，不能撤回流程")

            if not db_flow.is_revoke_by_creator():
                return self.report.error("你已经不能撤回当前流程")

        if FlowOpType.AGREE.get_id() == flow_type.get_id() and node_type != 101:
            workflow.complete_task_from_id(node_task_obj_id)
        elif FlowOpType.REFUSE.get_id() == flow_type.get_id():
            workflow.cancel()
            db_flow.is_invalid = 1
        elif FlowOpType.REVOKE.get_id() == flow_type.get_id():
            workflow.cancel()

            db_flow.invalid()
            db_flow.save()
            return self.report.post(self._report_data(db_flow, flow_type))

        # 更新已审批节点状态
        db_flow.update_logs(
            node_task_obj_id, FlowOpType.get_type(flow_type.get_id()), params.get("idea", None),
            params.get("params", {}), {"user_id": params_approve_user_id, "user_name": params_approve_user_name}
        )
        if node_type == 101 and node_obj:
            toadd_node_list, skip_node_id_list = db_flow.get_toadd_node_and_skip_node(node_obj)
        else:
            toadd_node_list, skip_node_id_list = db_flow.get_toadd_node_and_skip_node(node_obj)
        self._auto_comleted_task_node(workflow, params.get("params", {}), skip_node=skip_node_id_list)

        my_leader = db_flow.get_my_leader().get("my_leader")
        be_appoint_user_info = params.get('be_appoint_user_info', None)
        node_ready, auto_complete_node = self._find_node_ready(workflow, my_leader, to_nodes=toadd_node_list,
                                                               db_flow=db_flow,
                                                               be_appoint_user_info=be_appoint_user_info)

        db_flow.update_node_ready(node_ready, auto_complete_log=auto_complete_node)
        db_flow.is_completed = workflow.is_completed()
        if params.get("params", {}):
            temp_params = json.loads(db_flow.params)
            temp_params.update(params.get("params", {}))
            db_flow.params = json.dumps(temp_params)
        db_flow.specs_data = workflow.serialize(serializer)
        db_flow.save()

        return self.report.post(self._report_data(db_flow, flow_type, auto_complete_node, temp_node_ready=node_ready))

    def __to_add(self, params):

        params_approve_user_id = int(params.get("approve_user_id", 0))
        params_approve_user_name = params.get("approve_user_name", "")
        params_params = params.get("params")
        role_id = params.get("role_id", [])

        db_flow = flowopService.get_flow_op_by_id(params.get("flow_id"))

        if db_flow is None:
            return self.report.error("数据不存在")

        if db_flow.is_completed:
            return self.report.error("流程已结束")

        if db_flow.is_invalid:
            return self.report.error("流程已作废")

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)

        node_obj = db_flow.find_node_ready_by_uid(params_approve_user_id, role_id=role_id)
        if node_obj is None:
            return self.report.error("当前没有您的审核节点")

        if node_obj.get("node_type") == SpecsNodeType.TOADD.get_id():
            input_node = node_obj.get("node_id")
            output_node = node_obj.get("output_node")
            node_name = node_obj.get("node_name")
        else:
            wf_input_node = workflow.get_task(node_obj.get("node_id"))
            input_node = wf_input_node.id
            output_node = wf_input_node.task_spec.outputs[0].id
            node_name = wf_input_node.task_spec.id
            workflow.complete_task_from_id(wf_input_node.id)

        # 更新节点状态
        db_flow.update_logs(node_obj.get("node_id"), FlowOpType.AGREE.value, params.get("idea", None),
                            approve_user_info={"user_id": params_approve_user_id,
                                               "user_name": params_approve_user_name})

        # 加签
        import uuid
        add_node = {
            "input_node": input_node,
            "output_node": output_node,
            "node_id": uuid.uuid4(),
            "node_type": SpecsNodeType.TOADD.get_id(),
            "node_name": node_name,
            "user": {
                "id": params_params.get("add_node").get("user_id"),
                "name": params_params.get("add_node").get("user_name")
            }
        }

        skip_node = list()
        skip_node.append(add_node.get("output_node"))
        self._auto_comleted_task_node(workflow, params.get("params"), skip_node)

        node_ready, _ = self._find_node_ready(workflow, to_nodes=[add_node])

        db_flow.specs_data = workflow.serialize(serializer)
        db_flow.update_node_ready(node_ready)
        db_flow.is_completed = workflow.is_completed()
        db_flow.save()

        return self.report.post(self._report_data(db_flow, FlowOpType.TOADD))

    def _report_data(self, flow_obj, op_type=None, auto_complete_node=None, temp_node_ready=None):
        """
        op_type : 操作类型
        输出的统一结构
        """
        if temp_node_ready:
            node_ready = temp_node_ready
        elif op_type.get_id() != FlowOpType.REFUSE.get_id():
            node_ready = flow_obj.get_node_ready()
        else:
            node_ready = []

        resp_data = {
            "flow_id": flow_obj.id,
            "op_type": {"id": op_type.get_id(), "name": op_type.get_name()} if op_type is not None else {},
            "node_ready": node_ready,
            "is_completed": flow_obj.is_completed,
            "is_invalid": flow_obj.is_invalid,
            "last_time": str(flow_obj.updateTime),
            "logs": flow_obj.get_logs(),
            "auto_complete_logs": []
        }
        if auto_complete_node:
            for node in auto_complete_node:
                resp_data["auto_complete_logs"].append(node["raw_info"])
        return resp_data

    def _auto_comleted_task_node(self, wf, params=None, skip_node=None, my_leader=None):
        stop_auto = False
        while not wf.is_completed() and not stop_auto:
            if len(wf.get_tasks(Task.READY)) <= 0:
                break

            for _ready_task in wf.get_tasks(Task.READY):
                if _ready_task.task_spec.manual is False:

                    if skip_node is not None and _ready_task.task_spec.id in skip_node:
                        # 如果有加签的，要跳过之前准备的节点
                        stop_auto = True
                        continue

                    if params is not None:
                        wf.get_task(_ready_task.id).set_data(**params)

                    if my_leader:
                        dep2 = my_leader.get("dep2").get("dep_id") if my_leader.get("dep2") else 0
                        dep1 = my_leader.get("dep1").get("dep_id") if my_leader.get("dep1") else 0
                        wf.get_task(_ready_task.id).set_data(**{"dep1": dep1, "dep2": dep2})

                    node_type = _ready_task.task_spec.get_data("node_type")
                    if node_type == SpecsNodeType.Message.get_id():
                        uid = _ready_task.task_spec.get_data("user_id", "0")
                        message = _ready_task.task_spec.get_data("message_title", "")
                        if uid != "" and int(uid) > 0:
                            self.message_push(int(uid), message)

                    _ready_task.complete()
                else:
                    stop_auto = True

    @staticmethod
    def _find_node_ready(wf, my_leader=None, to_nodes=None, db_flow=None, be_appoint_user_info=None):
        node_ready = []
        node_auto_complete = []

        has_record_task_id = set()
        skip_task_ids = set()
        if not wf.is_completed():
            while (has_record_task_id | skip_task_ids) != set([task.id for task in wf.get_tasks(Task.READY)]):
                if len(wf.get_tasks(Task.READY)) <= 0:
                    break

                for _ready_task in wf.get_tasks(Task.READY):
                    if _ready_task.id in has_record_task_id:
                        continue
                    if to_nodes is not None and str(_ready_task.task_spec.id) in [to_node.get("output_node") for to_node
                                                                                  in to_nodes]:
                        # 如果有加签的，要跳过之前准备(ready状态)的节点
                        skip_task_ids.add(_ready_task.id)
                        continue

                    node_info = {
                        "input_node": _ready_task.task_spec.inputs[0].id,
                        "node_id": _ready_task.id,
                        "node_name": _ready_task.task_spec.id,
                        "node_desc": _ready_task.task_spec.get_data('node_desc', ''),
                        "node_activity_name": _ready_task.task_spec.get_data('node_activity_name', ''),
                        "node_type": _ready_task.task_spec.get_data("node_type", SpecsNodeType.Task.get_id()),
                        "user": {
                            "id": be_appoint_user_info[
                                'id'] if be_appoint_user_info else _ready_task.task_spec.get_data("user_id"),
                            "name": be_appoint_user_info[
                                'name'] if be_appoint_user_info else _ready_task.task_spec.get_data("user_name")
                        },
                        "role_list": _ready_task.task_spec.get_data("role_list", []),
                        "node_tpl": {
                            "bind_field": _ready_task.task_spec.get_data("node_tpl_bind_field", []),
                            "constraints": _ready_task.task_spec.get_data("node_tpl_constraints", {}),
                            "tip": _ready_task.task_spec.get_data("tip_title", ""),
                            "customized_information": _ready_task.task_spec.get_data("customized_information", {}),
                        }
                    }
                    node_type = _ready_task.task_spec.get_data("node_type")
                    # 领导节点
                    if node_type == SpecsNodeType.Leader.get_id():
                        user_id_tag = _ready_task.task_spec.get_data("user_id_tag")
                        someone_uid = _ready_task.get_data(user_id_tag)
                        leader_type = _ready_task.task_spec.get_data("leader_type")
                        someone_leader = flowopService.get_someone_leader({"uid": someone_uid}).get("my_leader")

                        if someone_leader:
                            if leader_type == LeaderType.Dep1:
                                node_info["user"]["id"] = someone_leader.get("dep1").get("leader_id")
                                node_info["user"]["name"] = someone_leader.get("dep1").get("leader_name")
                            if leader_type == LeaderType.Dep2:
                                node_info["user"]["id"] = someone_leader.get("dep2").get("leader_id")
                                node_info["user"]["name"] = someone_leader.get("dep2").get("leader_name")
                            if leader_type == LeaderType.Vp:
                                node_info["user"]["id"] = someone_leader.get("vp").get("leader_id")
                                node_info["user"]["name"] = someone_leader.get("vp").get("leader_name")

                    if node_type in [SpecsNodeType.Dep2.get_id(), SpecsNodeType.Dep1.get_id(),
                                     SpecsNodeType.VP.get_id()]:
                        if my_leader is not None:
                            node_type = _ready_task.task_spec.get_data("node_type")
                            if node_type == SpecsNodeType.Dep2.get_id():
                                node_info["user"]["id"] = my_leader.get("dep2").get("leader_id")
                                node_info["user"]["name"] = my_leader.get("dep2").get("leader_name")

                            if node_type == SpecsNodeType.Dep1.get_id():
                                node_info["user"]["id"] = my_leader.get("dep1").get("leader_id")
                                node_info["user"]["name"] = my_leader.get("dep1").get("leader_name")

                            if node_type == SpecsNodeType.VP.get_id():
                                node_info["user"]["id"] = my_leader.get("vp").get("vp_id")
                                node_info["user"]["name"] = my_leader.get("vp").get("vp_name")

                    uid = node_info["user"]["id"]
                    role_list = node_info.get("role_list", [])

                    if node_type == SpecsNodeType.Message.get_id():
                        wf.complete_task_from_id(_ready_task.id)
                        # _ready_task.complete()
                        node_ready.append(node_info)
                        continue
                    else:
                        if not uid and not role_list:
                            _ready_task.complete()
                            continue

                    if _ready_task.task_spec.get_data("is_skip", 0) == 1:
                        # 判断之前是否审批过,之前审批过，生成一条自动审批日志
                        if db_flow.have_ever_agree(uid):
                            _ready_task.complete()
                            node_auto_complete.append({
                                "logid": node_info.get("node_id"),
                                "uid": node_info.get("user").get("id"),
                                "user": node_info.get("user").get("name"),
                                "time": Time.timeStampToFormatByDatetime(int(Time.currentTime())),
                                "state": FlowOpType.AUTOAGREE.get_name(),
                                "node_desc": node_info.get("node_desc", ""),
                                "node_activity_name": node_info.get("node_activity_name", ""),
                                "node_name": node_info.get("node_name", ""),
                                "raw_info": node_info
                            })
                            continue

                    node_ready.append(node_info)
                    has_record_task_id.add(_ready_task.id)

        if to_nodes is not None:
            node_ready.extend(to_nodes)

        return node_ready, node_auto_complete

    @classmethod
    def _print_node_all(cls, wf):
        for _task in wf.get_tasks(Task.ANY_MASK):
            print("{}_{}_{}".format(_task.id, _task.get_name(), _task.get_state()))

    def message_push(self, uid, message):
        if not message:
            return

        userinfo = LieYingApp.rpc_client(
            1, "centerApp:/api/v1/userinfo", json_data={"uid": uid}
            , method="GET"
        ).get("data")

        try:
            user_wx_id = userinfo[0].get('wxid')
        except:
            return

            # LieYingApp.rpc_client(1, "msgTasksApp:/api/v1/push_task", json_data=wxmsg)

        # 获取活数据配置来动态切换消息推送通道
        data = RpcFuncService(1, 'homeApp').get_config_value('MSG_PUSH_USE_V2_CHANNEL')
        try:
            msg_push_channel = data['data'].get('configValue')
        except:
            msg_push_channel = None

        if msg_push_channel:
            json_data = {
                'send_user': '0',
                'receive_user': [user_wx_id],
                'wechat_text_type': 'text',
                'content': {"message": message}
            }
            LieYingApp.rpc_client(1, "v2MsgTasksApp:/api/v1/msg_push_task", json_data=json_data)
        else:
            json_data = {
                "send_user": "0",
                "revice_weixin_user": [user_wx_id],
                "ali_enable": 0,
                "weixin_enable": 1,
                "content": message
            }
            LieYingApp.rpc_client(1, "msgTasksApp:/api/v1/push_task", json_data=json_data)

    @request_url(FlowGetNodeCompleteList)
    def find_node_complete_list_with_flow_id(self, form_data):
        tpl = FlowTpl.query.filter(FlowTpl.id == form_data['tpl_id']).first()
        if not tpl:
            return self.report.error("流程模板不存在")

        tpl_data = FlowTplViewModelSchema().dump(tpl)

        db_flow = flowopService.get_flow_op_by_id(form_data.get("flow_id"))
        if db_flow is None:
            return self.report.error("数据不存在")
        creator_uid = db_flow.get_creator().get("uid")
        creator_user = db_flow.get_creator().get("user")
        my_leader = db_flow.get_my_leader(
            {"uid": creator_uid, "user": creator_user}
        ).get("my_leader")

        logs = db_flow.get_logs()
        temp_log_data = dict()
        temp_customized_information = dict()
        for log in logs:
            node_name = log.get("node_name")

            if node_name:
                if log.get("node_tpl", {}):
                    if log["node_tpl"].get("customized_information", {}):
                        temp_customized_information[node_name] = log["node_tpl"].get("customized_information", {})
                if node_name.startswith("Dep1") or node_name.startswith("Dep2") or node_name.startswith("VP"):
                    temp_log_data[node_name] = {"id": log["uid"], "name": log["user"]}

        node_list = tpl_data["tpl_data"]["nodeList"]
        # 处理node_list
        for node in node_list:
            # VP节点
            if node["id"].startswith("VP") and my_leader.get("vp"):
                node["meta"]["backlog_user"]["id"] = my_leader["vp"]["vp_id"]
                node["meta"]["backlog_user"]["name"] = my_leader["vp"]["vp_name"]
            # 一级部长节点
            if node["id"].startswith("Dep1"):
                node["meta"]["backlog_user"]["id"] = my_leader["dep1"]["leader_id"]
                node["meta"]["backlog_user"]["name"] = my_leader["dep1"]["leader_name"]
            # 二级部长节点
            if node["id"].startswith("Dep2") and my_leader.get("dep2"):
                node["meta"]["backlog_user"]["id"] = my_leader["dep2"]["leader_id"]
                node["meta"]["backlog_user"]["name"] = my_leader["dep2"]["leader_name"]
            if node["id"] in temp_log_data.keys():
                node["meta"]["backlog_user"]["id"] = temp_log_data[node["id"]].get("id")
                node["meta"]["backlog_user"]["name"] = temp_log_data[node["id"]].get("name")
            if node["id"] in temp_customized_information.keys():
                node["meta"]["customized_information"] = temp_customized_information[node["id"]]

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)
        node_complete_list = workflow.get_tasks(Task.COMPLETED)
        have_finish_node_name = [node.task_spec.name for node in node_complete_list]
        # 处理node_link
        node_link = tpl_data["tpl_data"]["linkList"]
        link = list()
        can_reach_node = dict()
        can_not_reach_links = []

        for link in node_link:
            if link["endId"] in have_finish_node_name and link["startId"] in have_finish_node_name:
                reach_node_data = can_reach_node.get(link["endId"], [])
                reach_node_data.append([link["id"], link["startId"]])
                can_reach_node[link["endId"]] = reach_node_data
                link["can_reach"] = 1
            else:
                link["can_reach"] = 0

        for reach, link_infos in can_reach_node.items():
            if len(link_infos) > 1:
                for link_info in link_infos:
                    if link_info[1].startswith("Exclusive"):
                        can_not_reach_links.append(link_info[0])

        for link in node_link:
            if link["id"] in can_not_reach_links:
                link["can_reach"] = 0

        return self.report.post(
            {"node_complete_id_list": [node.task_spec.name for node in node_complete_list], "tpl": tpl_data})

    def __refuse(self, params, flow_type):
        params_approve_user_id = int(params.get("approve_user_id", 0))
        params_approve_user_name = params.get("approve_user_name", "")
        role_id = params.get("role_id", [])

        db_flow = flowopService.get_flow_op_by_id(params.get("flow_id"))

        if db_flow is None:
            return self.report.error("数据不存在")

        if db_flow.is_completed:
            return self.report.error("流程已结束")

        if db_flow.is_invalid:
            return self.report.error("流程已作废")

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)

        if params_approve_user_id > 0:

            node_obj = db_flow.find_node_ready_by_uid(params_approve_user_id, role_id=role_id)
            if node_obj is None:
                return self.report.error("当前没有您的审核节点")
            node_obj_id = node_obj.get("node_id")

        else:
            node_obj = workflow.get_task(params.get("node_id"))

            if node_obj is None:
                return self.report.error("审核节点不存在")
            node_obj_id = node_obj.id

        db_flow.is_invalid = 1
        db_flow.is_completed = 1
        # 更新节点状态
        db_flow.update_logs(
            node_obj_id, FlowOpType.get_type(flow_type.get_id()), params.get("idea", None),
            params.get("params", None), {"user_id": params_approve_user_id, "user_name": params_approve_user_name}
        )
        LieYingApp.db.session.add(db_flow)
        LieYingApp.db.session.commit()

        return self.report.post(self._report_data(db_flow, flow_type))

    def _check_can_or_not_reach_old_node(self, wf, old_nodes):
        """检查能不能到达旧的点"""
        try:
            while not wf.is_completed():
                ready_tasks = wf.get_tasks(Task.READY)
                for ready_task in ready_tasks:
                    if ready_task.task_spec.id in old_nodes:
                        return True
                    else:
                        ready_task.complete()
        except Exception as e:
            pass
        return False

    @request_url(FlowOpNodeParamsSchema)
    def get_node_config_params(self, form_data):
        db_flow = flowopService.get_flow_op_by_id(form_data.get("flow_id"))
        if not db_flow:
            return self.report.error("流程不存在")
        nodes_ready = db_flow.get_node_ready()
        node_config_params = dict()
        for node_ready in nodes_ready:
            # 待办节点返回配置参数
            if node_ready.get("node_name") == form_data.get('node_name') and node_ready.get("node_type", None) != 101:
                serializer = JSONSerializer()
                workflow = Workflow.deserialize(serializer, db_flow.specs_data)
                task = workflow.get_tasks_from_spec_name(form_data.get('node_name'))
                if not task:
                    return self.report.error("流程节点不存在")
                node_config_params = task[0].task_spec.data

        return self.report.post(node_config_params)

    @request_url(FlowOpFallbackSchema)
    def fallback(self, form_data):
        params_approve_user_id = form_data.get("approve_user_id")
        params_approve_user_name = form_data.get("approve_user_name")

        role_id = form_data.get("role_id", [])
        # 校验流程状态
        db_flow = flowopService.get_flow_op_by_id(form_data.get("flow_id"))
        if not db_flow:
            return self.report.error("流程不存在")
        if db_flow.is_completed:
            return self.report.error("流程已结束")
        if db_flow.is_invalid:
            return self.report.error("流程已作废")
        # 校验当前审批人是是否有审批权限
        node_obj = db_flow.find_node_ready_by_uid(params_approve_user_id, role_id=role_id)
        if node_obj is None:
            return self.report.error("当前没有您的审核节点")
        node_task_obj_id = node_obj.get("node_id")
        db_flow.update_logs(
            node_task_obj_id, FlowOpType.FALLBACK.value, form_data.get("idea", ''),
            form_data.get("params", {}), {"user_id": params_approve_user_id, "user_name": params_approve_user_name}
        )

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)
        tasks = workflow.get_tasks(Task.COMPLETED)
        complete_node_name_list = [task.task_spec.id for task in tasks]
        if form_data.get('node_name') not in complete_node_name_list:
            return self.report.error('该节点没审批过，不能回退到该节点')
        task = workflow.get_tasks_from_spec_name(form_data.get('node_name'))
        if not task:
            return self.report.error("流程节点不存在")
        fallback_node = task[0]
        try:
            workflow.reset_task_from_id(fallback_node.id, reset_data=True)
        except Exception as e:
            return self.report.error('回退失败~')
        # 修改更新日志
        my_leader = db_flow.get_my_leader().get("my_leader")
        node_ready, auto_complete_node = self._find_node_ready(workflow, my_leader, db_flow=db_flow)
        db_flow.specs_data = workflow.serialize(serializer)
        db_flow.update_node_ready(node_ready, auto_complete_log=auto_complete_node)
        db_flow.is_completed = workflow.is_completed()
        if form_data.get("params", {}):
            temp_params = json.loads(db_flow.params)
            temp_params.update(form_data.get("params", {}))
            db_flow.params = json.dumps(temp_params)
        db_flow.save()

        return self.report.post(self._report_data(db_flow, FlowOpType.FALLBACK, auto_complete_node))

    @request_url(FlowOpNodeCanFallbackListSchema)
    def get_node_can_fallback_list(self, form_data):
        # 校验流程状态
        db_flow = flowopService.get_flow_op_by_id(form_data.get("flow_id"))
        if not db_flow:
            return self.report.error("流程不存在")
        if db_flow.is_completed:
            return self.report.error("流程已结束")
        if db_flow.is_invalid:
            return self.report.error("流程已作废")

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)
        tasks = workflow.get_tasks(Task.COMPLETED)
        node_can_fallback_list = []
        # 已完成的审批日志处理
        logs = db_flow.get_logs()
        print(logs)
        agree_node_list = dict()
        for log in logs:
            # 历史遗留问题，有些旧的日志没有存node_name
            logid = log.get("logid", None)
            if logid and log.get("state") == FlowOpType.AGREE.get_name():
                agree_node_list[logid] = {
                    "user_id": log.get('uid', None),
                    "user_name": log.get('user', ''),
                    "node_desc": log.get('node_desc', ''),
                    "node_activity_name": log.get('node_activity_name', ''),
                }

        for task in tasks:
            if task.task_spec.id in ["Root", "Start", "End"] or task.task_spec.id.startswith(
                    "Exclusive_") or task.task_spec.id.startswith('_'):
                continue
            else:
                node_info = agree_node_list.get(task.id, None)
                if node_info:
                    node_info["node_name"] = task.task_spec.id
                    node_can_fallback_list.append(agree_node_list[task.id])

        return self.report.post(node_can_fallback_list)

    @request_url(FlowOpFallbackPreNodeSchema)
    def fallback_to_pre_node(self, form_data):
        # 校验流程状态
        db_flow = flowopService.get_flow_op_by_id(form_data.get("flow_id"))
        if not db_flow:
            return self.report.error("流程不存在")
        if db_flow.is_completed:
            return self.report.error("流程已结束")
        if db_flow.is_invalid:
            return self.report.error("流程已作废")

        serializer = JSONSerializer()
        workflow = Workflow.deserialize(serializer, db_flow.specs_data)
        node_ready_list = db_flow.find_all_node_ready()
        # 将原来的ready节点标记系统回退
        for node_obj in node_ready_list:
            node_task_obj_id = node_obj.get("node_id")
            if node_obj.get("node_name", "") == form_data["node_name"]:
                return self.report.suc("当前待办节点不需要回退")
            db_flow.update_logs(node_task_obj_id, FlowOpType.SystemFALLBACK.value, "系统回退", {})
        # 节点回退
        task = workflow.get_tasks_from_spec_name(form_data.get('node_name'))
        if not task:
            return self.report.error("流程节点不存在")
        fallback_node = task[0]
        try:
            workflow.reset_task_from_id(fallback_node.id, reset_data=True)
        except Exception as e:
            return self.report.error('回退失败~')
        # 回退完重新生成ready日志
        my_leader = db_flow.get_my_leader().get("my_leader")
        node_ready, auto_complete_node = self._find_node_ready(workflow, my_leader, db_flow=db_flow)
        db_flow.specs_data = workflow.serialize(serializer)
        db_flow.update_node_ready(node_ready, auto_complete_log=auto_complete_node)
        db_flow.is_completed = workflow.is_completed()
        db_flow.save()

        return self.report.post(self._report_data(db_flow, FlowOpType.SystemFALLBACK, auto_complete_node))


flow_op_api_module = FlowOpApiModule()
