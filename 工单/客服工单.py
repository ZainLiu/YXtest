import json

a = {
    "name": "物品运输",
    "code": "GT",
    "is_snap": 1,
    "tool_preparation": "2333",
    "is_associated_device": 0,
    "job_procedures": [
        {
            "name": "货物到货时核对信息",
            "is_sop": 1,
            "sjp_id": 1,
            "content": "2333"
        }
    ]
}
print(json.dumps(a, ensure_ascii=False))
