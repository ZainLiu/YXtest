import json

aa = {
    "title": "设备子系统测试20221028",
    "equipment_sub_system_id": 550,
    "mt_type": 1,
    "supporting_file": [],
    "qa_requirement": "低压操作证",
    "end_date": None,  # 自定义维保时传，没有传null
    "monthly_template": {
        "tools_and_meters": [  # 工具仪表
            {
                "no": 1,  # 序号
                "content": "防护用具：护目镜，劳保鞋，绝缘手套，安全帽"  # 工具仪表内容
            }
        ],
        "mt_items": [  # 维护项目
            {
                "no": 1,  # 序号
                "name": "维护前准备",  # 项目名称
                "sub_items": [  # 子项目
                    {
                        "no": 1,  # 序号
                        "content": "相关设备技术文件1",  # 维护内容
                        "standard": "相关设备技术文件准备完毕1",  # 标准
                        "data_type": 1,  # 录入数据格式：1-单选枚举，2-数字，3-文本
                        "selections": [  # 枚举项
                            {"name": "是", "id": 1},
                            {"name": "否", "id": 2}
                        ],

                    },
                    {
                        "no": 2,  # 序号
                        "content": "相关设备技术文件2",  # 维护内容
                        "standard": "相关设备技术文件准备完毕2",  # 标准
                        "data_type": 2,  # 录入数据格式：1-单选枚举，2-数字，3-文本
                    }
                ]
            }
        ]
    },
    "quarterly_template": {},
    "semiannually_template": {},
    "annually_template": {},
    "batch_conf": [
        {
            "name": "批次1",
            "eq_info": [
                {
                    "eq_type_name": "测试新增类型2",
                    "full_code": "YX-CHN-GD-GZHY-D2-F1-ECC102-D-D1-TEST2-G-2",
                    "id": 2,
                    "location": "广州汇云/汇云2栋/1楼/机房102",
                    "name": "2#发电机组"
                },
            ]
        }

    ]
}

print(json.dumps(aa, ensure_ascii=False))
print(len("EquipmentSubSystemMaintenanceItem"))
