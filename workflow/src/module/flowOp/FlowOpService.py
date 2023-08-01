from ly_kernel.LieYing import LieYingApp
from models.FlowOp import FlowOp


def get_flow_op_by_id(flow_op_id):
    return FlowOp.query.filter(FlowOp.id == flow_op_id).first()


def get_someone_leader(my_info=None):
    my_leader = LieYingApp.rpc_client(1, "centerApp:/user/myleader", json_data={"uid": my_info.get("uid")},
                                      method="GET")

    return {
        "my_info": my_info,
        "my_leader": my_leader.get("data")
    }

