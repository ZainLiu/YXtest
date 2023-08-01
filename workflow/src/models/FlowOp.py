import copy

from ly_kernel.db.BaseModel import *
import pickle
from base64 import b64encode, b64decode
from enums.FlowEnums import FlowOpType,SpecsNodeType
from ly_service.utils import Time
import json



class FlowOp(BaseModel):
    """
    模板
    """
    __tablename__ = 'wf_flow'

    id = db.Column(db.Integer, primary_key=True)
    specs_data = db.Column(db.JSON, nullable=True, comment='流转过程')
    node_data = db.Column(db.JSON, nullable=True, comment='节点数据')
    is_completed = db.Column(db.Integer, default=0, nullable=True, comment='是否结束')
    is_invalid = db.Column(db.Integer, default=0, nullable=True, comment='是否作废')
    params = db.Column(db.String(1024), nullable=False, default='{}', comment='审批过程中传入的参数')
    createTime = db.Column(db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'), comment='创建时间')
    updateTime = db.Column(db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'),
                           server_onupdate=db.text('CURRENT_TIMESTAMP'), comment='更新时间')

    def __init__(self):
        self.node_data = {}

    # 作废该流程
    def invalid(self):
        self.is_invalid = 1
        self.node_data = {
            "node_ready": self.encode_pickle([]),
            "logs": self.encode_pickle([]),
        }

    def encode_pickle(self, v):
        return str(b64encode(pickle.dumps(v, protocol=pickle.HIGHEST_PROTOCOL)), encoding="utf-8")

    def decode_pickle(self, v):
        return pickle.loads(b64decode(v))

    # 获取发起者的名字
    def get_creator(self):
        creator = self.decode_pickle(self.node_data.get("logs", self.encode_pickle([])))[0]

        return {
            "uid": creator.get("uid"),
            "user": creator.get("user"),
        }

    def get_my_leader(self, my_info=None):
        if my_info is None:
            my_info = self.get_creator()

        my_leader = LieYingApp.rpc_client(1, "centerApp:/user/myleader", json_data={"uid": my_info.get("uid")},
                                          method="GET")

        return {
            "my_info": my_info,
            "my_leader": my_leader.get("data")
        }

    def find_node_ready_by_uid(self, user_id, role_id=None):

        node_ready = self.get_node_ready()
        for _node in node_ready:
            if _node.get("user").get("id") == user_id:
                return _node

            role_ids = [role["id"] for role in _node.get("role_list", [])]
            if set(role_id) & set(role_ids):
                return _node

        return None

    def find_all_node_ready(self):
        node_ready_list = self.get_node_ready()
        return node_ready_list

    def find_node_ready_noed_name(self):
        node_readys = self.get_node_ready()
        return [node_ready["node_name"] for node_ready in node_readys]

    def get_node_ready(self):
        node_ready = self.decode_pickle(self.node_data.get("node_ready")) if "node_ready" in self.node_data else []

        return node_ready

    def get_logs(self):
        logs = self.decode_pickle(self.node_data.get("logs")) if "logs" in self.node_data else []

        return logs

    # 发起者是否可以撤回流程
    def is_revoke_by_creator(self):

        def _find_node(_logs):
            is_find = False

            for _d_node in _logs:
                if type(_d_node) == list:
                    is_find = _find_node(_d_node)
                else:
                    if _d_node.get("state") == FlowOpType.AGREE.get_name():
                        return True
                    elif _d_node.get("state") == FlowOpType.REFUSE.get_name():
                        return True
                    elif _d_node.get("state") == FlowOpType.REJECT.get_name():
                        return True

                if is_find:
                    break

            return is_find

        logs = self.decode_pickle(self.node_data.get("logs", self.encode_pickle([])))

        return not _find_node(logs)

    def update_node_ready(self, node_ready, reissue_log=None, auto_complete_log=None):

        node_data = json.loads(json.dumps(self.node_data))
        if reissue_log is None:
            real_node_ready = []
            # 去掉已经完成的消息节点
            for node in node_ready:
                if node["node_type"] != SpecsNodeType.Message.get_id():
                    real_node_ready.append(node)

            node_data["node_ready"] = self.encode_pickle(real_node_ready)
        node_data["logs"] = self.encode_pickle(
            self._private_add_logs(node_ready, reissue_log=reissue_log, auto_complete_log=auto_complete_log))

        self.node_data = node_data

    def add_node_ready(self, to_add_node):
        node_data = json.loads(json.dumps(self.node_data))
        node_ready = node_data["node_ready"].append(to_add_node)
        node_data["node_ready"] = self.encode_pickle(node_ready)
        node_data["logs"] = self.encode_pickle(self._private_add_logs(node_ready))

        self.node_data = node_data

    def add_logs(self, log):
        logs = self.get_logs()
        logs.append(log)

        node_data = json.loads(json.dumps(self.node_data))
        node_data["logs"] = self.encode_pickle(logs)

        self.node_data = node_data

    # def update_logs(self, log_id, state, idea, params=None):
    #     if state.get("id") == FlowOpType.REFUSE.get_id():
    #         self.update_logs_refuse(log_id, state, idea, params)
    #     else:
    #         self.update_logs_other(log_id, state, idea, params)

    def update_logs(self, log_id, state, idea, params=None, approve_user_info=None):
        is_update = False
        logs = self.get_logs()
        for _find_id in logs:
            if type(_find_id) == list:
                for _node_s in _find_id:
                    if _node_s.get("logid") == log_id and _node_s.get("state") == FlowOpType.NORMAL.get_name():
                        is_update = True

                        if idea is not None and idea != "":
                            _node_s["idea"] = idea
                        if params is not None:
                            _node_s["params"] = params
                        if approve_user_info is not None:
                            _node_s["uid"] = approve_user_info["user_id"]
                            _node_s["user"] = approve_user_info["user_name"]
                        _node_s["state"] = state.get("name")
                        _node_s["time"] = Time.timeStampToFormatByDatetime(int(Time.currentTime()))

                        if state.get("id") == FlowOpType.REFUSE.get_id():
                            _node_s_copy = copy.deepcopy(_node_s)
                            _node_s_copy["state"] = FlowOpType.NORMAL.get_name()
                            _node_s_copy["idea"] = ""
                            _node_s_copy["params"] = {}
                            _node_s_copy["time"] = Time.timeStampToFormatByDatetime(int(Time.currentTime()))
                            _find_id.append(_node_s_copy)
                        break
                if is_update:
                    break
            else:
                if _find_id.get("logid") == log_id and _find_id.get("state") == FlowOpType.NORMAL.get_name():
                    if params is not None:
                        _find_id["params"] = params
                    if idea is not None and idea != "":
                        _find_id["idea"] = idea
                    if approve_user_info is not None:
                        _find_id["uid"] = approve_user_info["user_id"]
                        _find_id["user"] = approve_user_info["user_name"]
                    _find_id["state"] = state.get("name")
                    _find_id["time"] = Time.timeStampToFormatByDatetime(int(Time.currentTime()))
                    if state.get("id") == FlowOpType.REFUSE.get_id():
                        _find_id_copy = copy.deepcopy(_find_id)
                        _find_id_copy["state"] = FlowOpType.NORMAL.get_name()
                        _find_id_copy["idea"] = ""
                        _find_id_copy["params"] = {}
                        _find_id_copy["time"] = Time.timeStampToFormatByDatetime(int(Time.currentTime()))
                        logs.append(_find_id_copy)
                    break

        node_data = json.loads(json.dumps(self.node_data))
        node_data["logs"] = self.encode_pickle(logs)

        self.node_data = node_data

    def update_logs_refuse(self, log_id, state, idea, params=None):
        is_update_1 = False
        is_update_2 = False
        logs = self.get_logs()
        new_normal_log_list_1 = []
        will_remove_list_1 = []
        for _find_id in logs:
            if type(_find_id) == list:
                new_normal_log_list_2 = []
                will_remove_list_2 = []
                for _node_s in _find_id:
                    if _node_s.get("state") == FlowOpType.NORMAL.get_name():
                        if _node_s.get("logid") == log_id:
                            is_update_2 = True

                            if idea is not None and idea != "":
                                _node_s["idea"] = idea
                            if params is not None:
                                _node_s["params"] = params
                            _node_s["state"] = state.get("name")
                            _node_s["time"] = Time.timeStampToFormatByDatetime(int(Time.currentTime()))
                            # 拒绝完补一条待办信息，方便重新发起时使用
                            _node_s_copy = copy.deepcopy(_node_s)
                            _node_s_copy["state"] = FlowOpType.NORMAL.get_name()
                            _node_s_copy["idea"] = ""
                            _node_s_copy["params"] = {}
                            new_normal_log_list_2.append(_node_s_copy)
                        else:
                            will_remove_list_2.append(_node_s)
                            new_normal_log_list_2.append(_node_s)
                if is_update_2:
                    # 移除旧的待办节点
                    for node in will_remove_list_2:
                        _find_id.remove(node)
                    # 加上新的待办节点
                    _find_id.extend(new_normal_log_list_2)
                    # 拒绝操作将拒绝的节点补上
                    break
            else:
                if _find_id.get("state") == FlowOpType.NORMAL.get_name():
                    if _find_id.get("logid") == log_id:
                        is_update_1 = True
                        if params is not None:
                            _find_id["params"] = params
                        if idea is not None and idea != "":
                            _find_id["idea"] = idea
                        _find_id["state"] = state.get("name")
                        _find_id["time"] = Time.timeStampToFormatByDatetime(int(Time.currentTime()))
                        _find_id_copy = copy.deepcopy(_find_id)
                        _find_id_copy["state"] = FlowOpType.NORMAL.get_name()
                        _find_id_copy["idea"] = ""
                        _find_id_copy["params"] = {}
                        new_normal_log_list_1.append(_find_id_copy)
                    else:
                        will_remove_list_1.append(_find_id)
                        new_normal_log_list_1.append(_find_id)
            if is_update_1:
                for node in will_remove_list_1:
                    logs.remove(node)
                logs.extend(new_normal_log_list_1)
        # 如果是拒绝则删除其他待办节点,重新发起再加入
        # if state.get("id") == FlowOpType.REFUSE.get_id():
        #     node_will_remove_list = []
        #     for _find_id in logs:
        #         if type(_find_id) == list:
        #             node_will_remove_list_child = []
        #             for _node_s in _find_id:
        #                 if _node_s.get("state") == FlowOpType.NORMAL.get_name():
        #                     node_will_remove_list_child.append(_node_s)
        #             for node_will_remove in node_will_remove_list_child:
        #                 _find_id.remove(node_will_remove)
        #         else:
        #             if _find_id.get("state") == FlowOpType.NORMAL.get_name():
        #                 node_will_remove_list.append(_find_id)
        #             for node_will_remove in node_will_remove_list:
        #                 logs.remove(node_will_remove)

        node_data = json.loads(json.dumps(self.node_data))
        node_data["logs"] = self.encode_pickle(logs)

        self.node_data = node_data

    def _private_add_logs(self, node_ready, reissue_log=None, auto_complete_log=None):
        logs = self.get_logs()
        # 补充重新发起日志
        if reissue_log:
            logs.append(reissue_log)
        # 补充自动完成的日志
        if auto_complete_log:
            logs.extend(auto_complete_log)
        # 日志流转
        _add = dict()
        # 消息节点计数，如果返回的全是消息节点，说明流程已经结束
        msg_node_cnt = 0
        for _node in node_ready:
            input_node = _node.get("input_node")
            if input_node not in _add:
                _add[input_node] = []
            if _node.get("node_type") == SpecsNodeType.Message.get_id():
                state = FlowOpType.AGREE.get_name()
                msg_node_cnt += 1
            else:
                state = FlowOpType.NORMAL.get_name()
            _add[input_node].append({
                "logid": _node.get("node_id"),
                "uid": _node.get("user").get("id"),
                "user": _node.get("user").get("name"),
                "role_list": _node.get("role_list", []),
                "node_type": _node.get("node_type", None),
                "time": Time.timeStampToFormatByDatetime(int(Time.currentTime())),
                "state": state,
                "node_desc": _node.get('node_desc', ''),
                "node_activity_name": _node.get('node_activity_name', ''),
                "node_name": _node.get('node_name', ''),
                "node_tpl": _node.get("node_tpl", {})
            })

        if len(_add) > 0:

            def _find_node(_logs, log_id):
                is_find = False

                for _d_node in _logs:
                    if type(_d_node) == list:
                        is_find = _find_node(_d_node, log_id)
                    else:
                        if _d_node.get("logid") == log_id and _d_node.get("state") == FlowOpType.NORMAL.get_name():
                            return True

                    if is_find:
                        break

                return is_find

            for key, _add_node in _add.items():
                is_find = False
                for _log in _add_node:
                    is_find = _find_node(logs, _log.get("logid"))
                    if is_find:
                        break

                if not is_find:
                    if len(_add_node) == 1:
                        logs.append(_add_node[0])
                    else:
                        logs.append(_add_node)
            # 全是消息节点即流程结束

            if len(node_ready) == msg_node_cnt:
                logs.append({
                    "time": Time.timeStampToFormatByDatetime(int(Time.currentTime())),
                    "state": FlowOpType.OVER.get_name()
                })
        elif reissue_log is None:
            logs.append({
                "time": Time.timeStampToFormatByDatetime(int(Time.currentTime())),
                "state": FlowOpType.OVER.get_name()
            })

        return logs

    def get_toadd_node_and_skip_node(self, toadd_node=None):
        ready_nodes = self.get_node_ready()
        toadd_node_list = []
        skip_node_id_list = []
        for node in ready_nodes:
            if toadd_node and node.get('node_id') == toadd_node.get('node_id'):
                continue
            if node.get('node_type', None) == 101:
                toadd_node_list.append(node)
                skip_node_id_list.append(node.get('output_node'))
        return toadd_node_list, skip_node_id_list

    def have_ever_agree(self, uid):
        """判断用户之前是否同意过"""

        logs = self.get_logs()
        for log in logs:
            if type(log) == list:
                for log_child in log:
                    if log_child.get('uid', None) == uid and log_child.get('state',
                                                                           None) == FlowOpType.AGREE.get_name():
                        return True
            else:
                if log.get('uid', None) == uid and log.get('state', None) == FlowOpType.AGREE.get_name():
                    return True

        return False
