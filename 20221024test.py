import json

save_data = {
    "name": "2333",
    "code": "2333",
    "is_other_jp": 1,
    "tool_preparation": "tool_preparation",
    "job_procedures": [
        {
            "jp_name": "jp_name001",
            "jp_is_snap": 1,
            "jp_is_annex": 1,
            "is_sop": 0,
            "content": "content20230719",
            "related_data": [
                {
                    "type": 0, # 1: 关联设备，关联
                    "data_title": "xxx",
                    "op_type": 4  # 1:上架 2：下架 3：调整 4：开电 5关电
                }

            ],

        }
    ],
    "work_process_conf": {
        "start": [
            {
                "step": "RelatedEq",
                "status": 1
            },
            {
                "step": "RelatedMt",
                "status": 1
            },
        ],
        "before_work": [
            {
                "step": "SchemeConfirmation",
                "status": 1
            },
            {
                "step": "MaterialOutbound",
                "status": 1,
                "related_data": ""
            },
        ],
        "after_work": [
            {
                "step": "MaterialWarehousing",
                "status": 1,
                "related_data": ""
            },
            {
                "step": "WorkSummary",
                "status": 1
            },
            {
                "step": "StatementConfirmation",
                "status": 1
            },
        ]
    },
    "mark": "mark20230719",
    "other_jp": [
        {
            "name": "namexxx",
            "pre_procedures": "WorkSummary",
            "operator_pg_id": 45,
            "other_jp_list": [
                {
                    "name": "jp_name002",
                    "is_snap": 1,
                    "is_annex": 1,
                    "is_sop": 0,
                    "content": "content20230719",
                    "related_data": [
                        {
                            "type": 0,  # 1：关联设备 2：关联物资
                            "data_title": "xxx",
                            "op_type": 4  # 1:上架 2：下架 3：调整 4：开电 5关电
                        }
                    ]

                }
            ]

        }
    ],
    "summary_module": [
        {
            "name": "xxx",
            "related_data": [
                {
                    "node": "RelatedEq",
                    "title": "xxx"
                }
            ]

        }
    ]

}

if __name__ == '__main__':
    print(json.dumps(save_data))
