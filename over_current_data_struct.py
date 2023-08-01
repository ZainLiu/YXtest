import json

create_data = {
    "customer_id": 1,
    "contract_number": "YXHJ-CDPZ-2023001",
    "contracts": "刘先生",
    "phone": "18675341889",
    "email": "88888@123.com",
    "start_time": "2023-06-19 10:20:33",
    "end_time": "2023-06-30 10:20:33",
    "data_center_id": 1,
    "cab_num": 10,
    "mark": "23333",
    "contract_current_value": "20.3",
    "current_warning_value": "30.6",
    "safety_threshold": "25.6",
    "over_current_judgment_rule": 1,
    "power_calculation_rule": 1,
    "over_ccv_notice": 0,
    "over_cwv_notice": 0,
    "over_st_notice": 1,
    "cab_ids": []
}

list_data = {
    "code": 1002,
    "data": {
        "count": 1,
        "data": [{
            "id": 1,
            "contract_number": "xxxx",
            "data_center_name": "xxx",
            "cab_num": 10,
            "over_current_judgment_rule": 1,
            "power_calculation_rule": 1,
            "start_time": "2023-06-19 10:20:33",
            "end_time": "2023-06-19 10:20:33",
            "mark": "xxx",
            "status": "1",
            "is_expire": 1
        }]
    },
    "message": "",
    "timestamp": "2023-06-17 11:26:53"
}
b = json.dumps(list_data, ensure_ascii=False)
print(b)

a = {
    "start_time": "",  # 采样开始时间
    "end_time": "",  # 采样结束时间
    "ocs_info": [  # 超电服务信息
        {
            "id": "",  # DCOS这边的ID，数据中台不用管，原路返回
            "contract_current_value": "",  # 超电服务合同电流值
            "cab_list": [
                {  # 机柜列表
                    "id": "",  # DCOS这边的ID，数据中台不用管，原路返回
                    "eq_code": "",  # 设备总编码，其他设备信息也可以在这里传过去
                    "records": []  # 相关的超电记录，该机柜在这段时间有超电记录就塞在这一并返回
                }
            ]
        }
    ]
}
