from enum import Enum


class FlowOpType(Enum):
    NORMAL = {"id": 0, "name": "待办"}
    AGREE = {"id": 1, "name": "同意"}
    REFUSE = {"id": 2, "name": "拒绝"}
    ACCEPT = {"id": 3, "name": "指派"}
    REJECT = {"id": 4, "name": "驳回"}
    REVOKE = {"id": 5, "name": "撤回"}
    OVER = {"id": 100, "name": "完结"}
    CREATE = {"id": 101, "name": "发起审批"}
    TOADD = {"id": 102, "name": "加签"}
    REISSUE = {"id": 103, "name": "重新发起"}
    AUTOAGREE = {"id": 104, "name": "自动同意"}
    FALLBACK = {"id": 105, "name": "指定回退"}
    SystemFALLBACK = {"id": 106, "name": "系统回退"}

    @classmethod
    def get_type(cls, _type):
        for v in FlowOpType:
            if v.value.get("id") == _type:
                return v.value

        return None

    def get_id(self):
        return self.value.get("id")

    def get_name(self):
        return self.value.get("name")


class SpecsNodeType(Enum):
    Start = {"id": 8, "name": "Start", "class": "libs.SpiffWorkflow.specs.StartTask.StartTask", "manual": False}
    End = {"id": 9, "name": "End", "class": "libs.SpiffWorkflow.specs.Simple.Simple", "manual": False}
    Task = {"id": 4, "name": "Task", "class": "libs.SpiffWorkflow.specs.Simple.Simple", "manual": False}
    Exclusive = {"id": 3, "name": "Exclusive", "class": "libs.SpiffWorkflow.specs.ExclusiveChoice.ExclusiveChoice",
                 "manual": False}
    Join = {"id": 6, "name": "Join", "class": "libs.SpiffWorkflow.specs.Join.Join", "manual": False}
    Message = {"id": 10, "name": "Message", "class": "libs.SpiffWorkflow.specs.Simple.Simple"}
    Dep1 = {"id": 11, "name": "Dep1", "class": "libs.SpiffWorkflow.specs.Simple.Simple"}
    Dep2 = {"id": 12, "name": "Dep2", "class": "libs.SpiffWorkflow.specs.Simple.Simple"}
    VP = {"id": 13, "name": "VP", "class": "libs.SpiffWorkflow.specs.Simple.Simple"}
    Node = {"id": 1, "name": "Simple", "class": "libs.SpiffWorkflow.specs.Simple.Simple"}
    TOADD = {"id": 101, "name": "TOADD"}
    Leader = {"id": 15, "name": "Simple", "class": "libs.SpiffWorkflow.specs.Simple.Simple"}

    # 没用使用
    Multi = {"id": 5, "name": "Multi", "class": "libs.SpiffWorkflow.specs.MultiChoice.MultiChoice", "manual": False}

    # Merge = {"id": 7, "name": "Merge", "class": "libs.SpiffWorkflow.specs.Merge.Merge", "manual": False}

    @classmethod
    def get_type(cls, id_type):
        for v in SpecsNodeType:
            if v.value.get("id") == id_type:
                return v.value

        return None

    def get_id(self):
        return self.value.get("id")

    def get_name(self):
        return self.value.get("name")


class LeaderType:
    Dep1, Dep2, Vp = 1, 2, 3


if __name__ == '__main__':
    print(SpecsNodeType.Message.get_id())
