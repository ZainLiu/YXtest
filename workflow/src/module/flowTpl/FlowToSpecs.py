import json
import pickle
from base64 import b64encode, b64decode
from enums.FlowEnums import SpecsNodeType


class FlowToSpecs(object):
    workflow_json = None

    def open_json(self, file_name):
        with open(file_name) as fp:
            json_data = fp.read()

        self.workflow_json = json.loads(json_data)

    def loads(self, _to_load):
        self.workflow_json = _to_load
        return self

    def _find_tree_from_input_id(self, d_id=None):
        _link = []
        for _f_l in self.workflow_json["linkList"]:
            if _f_l.get("endId") == d_id:
                _link.append(_f_l.get("startId"))

        return _link

    def _find_tree_from_output_id(self, d_id=None):
        _link = []
        for _f_l in self.workflow_json["linkList"]:
            if _f_l.get("startId") == d_id:
                _link.append(_f_l.get("endId"))

        return _link

    def get_link_end_from_node(self, node_id, start_id_begin):
        for _f_l in self.workflow_json["linkList"]:
            if str(_f_l.get("endId")) == node_id and start_id_begin == str(_f_l.get("startId")):
                return _f_l

        return None

    @staticmethod
    def encode_pickle(v):
        return str(b64encode(pickle.dumps(v, protocol=pickle.HIGHEST_PROTOCOL)), encoding="utf-8")

    def params_ags(self, cond, output):

        # print(cond)

        # [{'after': 1, 'after_type': 2, 'front': 'a', 'front_type': 0, 'logical_operator': 0, 'relational_operator': '>'}]

        ags = []
        for _node_link_cond in cond:
            class_op = []
            operators = _node_link_cond.get("relational_operator")
            if operators == ">=" or operators == ">":
                class_op.append("GreaterThan")
                if operators == ">=":
                    class_op.append("Equal")
            if operators == "<=" or operators == "<":
                class_op.append("LessThan")
                if operators == "<=":
                    class_op.append("Equal")
            if operators == "==":
                class_op.append("Equal")
            if operators == "!=":
                class_op.append("NotEqual")

            for _cond_class in class_op:
                left_type = "Attrib" if _node_link_cond.get("front_type") == 0 else "value"
                right_type = "Attrib" if _node_link_cond.get("after_type") == 0 else "value"
                ags.append(
                    [
                        [
                            "libs.SpiffWorkflow.operators.{}".format(_cond_class),
                            [
                                [left_type, _node_link_cond.get("front")],
                                [right_type, _node_link_cond.get("after")]
                            ]
                        ], output
                    ]
                )

        return ags

    def to_json(self):
        _to = dict()
        _to["task_specs"] = dict()
        _to["name"] = ""
        _to["description"] = ""
        _to["file"] = None

        _spec = _to["task_specs"]
        for _o in self.workflow_json["nodeList"]:
            _meta = _o.get("meta")

            node_obj = SpecsNodeType.get_type(int(_meta.get("node_type")))

            _spec[_o.get("id")] = {
                "id": _o.get("id"),
                "name": _o.get("id"),
                "class": node_obj.get("class"),
                "manual": node_obj.get("manual", True),
            }

            _spec[_o.get("id")]["inputs"] = [] if node_obj.get(
                "id") == SpecsNodeType.Start.get_id() else self._find_tree_from_input_id(_o.get("id"))
            _spec[_o.get("id")]["outputs"] = self._find_tree_from_output_id(_o.get("id"))

            # 节点配置参数
            _spec[_o.get("id")]["data"] = {
                "user_id": self.encode_pickle(_meta.get("backlog_user").get("id")),
                "user_name": self.encode_pickle(_meta.get("backlog_user").get("name")),
                "role_list": self.encode_pickle(_meta.get("role_list", [])),
                "node_desc": self.encode_pickle(_meta.get("node_name", "")),
                "node_activity_name": self.encode_pickle(_meta.get("node_activity_name", "")),

                # 节点类型
                "node_type": self.encode_pickle(node_obj.get("id")),

                # 领导节点标签
                "user_id_tag": self.encode_pickle(_meta.get("user_id_tag", "")),

                # leader的类型
                "leader_type": self.encode_pickle(_meta.get("leader_type", "")),

                # 提示信息
                "tip_title": self.encode_pickle(_meta.get("tip_title", "")),

                # 通知信息 - 用于知会
                "message_title": self.encode_pickle(_meta.get("message_title", "")),

                # 变量 绑定 控件值
                "node_tpl_bind_field": self.encode_pickle(_meta.get("form_field", [])),

                # 控件显示，禁用状态
                "node_tpl_constraints": self.encode_pickle(_meta.get("constraints", {})),

                # 之前审批过是否直接跳过
                "is_skip": self.encode_pickle(_meta.get("is_skip", 0)),

                # 每个项目每个节点自定义的信息
                "customized_information": self.encode_pickle(_meta.get("customized_information", {}))
            }

            # 并行、排它。线节点条件
            if node_obj.get("id") in [SpecsNodeType.Exclusive.get_id(), SpecsNodeType.Multi.get_id()]:
                # 查找，outputs节点的 end 线的条件

                _spec[_o.get("id")]["choice"] = None
                _spec[_o.get("id")]["default_task_spec"] = ""
                _spec[_o.get("id")]["cond_task_specs"] = []

                for _output_node in _spec[_o.get("id")]["outputs"]:
                    _link_obj = self.get_link_end_from_node(_output_node, _o.get("id"))

                    _link_obj_meta = _link_obj.get("meta")

                    if _link_obj_meta is not None:

                        if _link_obj_meta.get("disabled"):
                            # 节点默认条件
                            _spec[_o.get("id")]["default_task_spec"] = _output_node
                        elif len(_link_obj_meta.get("operation")) > 0:
                            # 添加节点条件
                            for _cond in self.params_ags(_link_obj_meta.get("operation"), _output_node):
                                _spec[_o.get("id")]["cond_task_specs"].append(
                                    _cond
                                )

            # 并行后的合并线
            if node_obj.get("id") == SpecsNodeType.Join.get_id():
                _spec[_o.get("id")]["threshold"] = ""
                _spec[_o.get("id")]["cancel"] = True
                _spec[_o.get("id")]["split_task"] = {}

        return json.loads(json.dumps(_to))
