from module.flowTpl.FlowTpl import flowtpl_module
from module.flowOp.FlowOpApi import flow_op_api_module
from ly_kernel.enum.Request import RequestVerify

# API接口 : api接口有平台区分
api_interface = {
    "v1": [
        {"url": "/flow/create", "comment": "创建工作流", "data_act": flow_op_api_module.create
            , "ignore": RequestVerify.login},
        {"url": "/flow/info", "comment": "流程信息", "data_act": flow_op_api_module.flow_info
            , "ignore": RequestVerify.login},
        {"url": "/flow/wfinfo", "comment": "流程原信息-测试用", "data_act": flow_op_api_module.flow_info_by_wf
            , "ignore": RequestVerify.login},
        {"url": "/flow/agree", "comment": "节点同意", "data_act": flow_op_api_module.agree
            , "ignore": RequestVerify.login},
        {"url": "/flow/refuse", "comment": "节点拒绝", "data_act": flow_op_api_module.refuse
            , "ignore": RequestVerify.login},
        {"url": "/flow/revoke", "comment": "节点撤回", "data_act": flow_op_api_module.revoke
            , "ignore": RequestVerify.login},
        {"url": "/flow/toadd", "comment": "节点加签", "data_act": flow_op_api_module.toadd
            , "ignore": RequestVerify.login},
        {"url": "/flow/node_complete_list", "comment": "完成的节点的id列表和审批模板",
         "data_act": flow_op_api_module.find_node_complete_list_with_flow_id
            , "ignore": RequestVerify.login},
        {"url": "/flow/refuse_v2", "comment": "节点拒绝v2", "data_act": flow_op_api_module.refuse_v2
            , "ignore": RequestVerify.login},
        {"url": "/flow/reissue", "comment": "重新发起", "data_act": flow_op_api_module.reissue
            , "ignore": RequestVerify.login},
        {"url": "/flow/node_config_params", "comment": "获取节点的配置参数",
         "data_act": flow_op_api_module.get_node_config_params
            , "ignore": RequestVerify.login},
        {"url": "/flow/specify_fallback", "comment": "回退到指定节点",
         "data_act": flow_op_api_module.fallback
            , "ignore": RequestVerify.login},
        {"url": "/flow/sys_fallback", "comment": "系统回退节点",
         "data_act": flow_op_api_module.fallback_to_pre_node
            , "ignore": RequestVerify.login},
    ]
}

# 分配模块URL唯一ID
request_ids = {
    'flowTpl': {
        "name": "工作流模块",
        "requests": [
            {"url": "/view", "comment": "模板界面", "data_act": flowtpl_module.view},
            {"url": "/add", "comment": "添加模板", "data_act": flowtpl_module.add, "methods": 'POST'},
            {"url": "/edit", "comment": "编辑模板", "data_act": flowtpl_module.edit, "methods": 'PUT'},
            {"url": "/del", "comment": "删除模板", "data_act": flowtpl_module.delete, "methods": 'DELETE'},
            {"url": "/node_complete_list", "comment": "完成的节点的id列表和审批模板",
             "data_act": flow_op_api_module.find_node_complete_list_with_flow_id
                , "ignore": RequestVerify.login},
            {"url": "/node_can_fallback_list", "comment": "可回退节点列表",
             "data_act": flow_op_api_module.get_node_can_fallback_list
                , "ignore": RequestVerify.login},
        ],
    },
}

