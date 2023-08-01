import json

aa = {
    "name": "测试小问题20221108",
    "level": 1,
    "equipment_system_id": 58,
    "description": "23333",
    "affected_area": "2333",
    "processing_description": "2333"
}
print(json.dumps(aa, ensure_ascii=False))
