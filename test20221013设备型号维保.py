import json

a = {"draft_info": {"title": "4313", "equipment_model_list": ["GZDW", "HZ-GZDW-3"], "equipment_type_id": 2487,
                    "mt_type": 1, "qa_requirement": "3131",
                    "maintenance_cycle": [1], "supporting_file": [
        {"id": 2448, "url": "https://opspre.imyunxia.com/file/2023_01_31/2023_01_31_16_42_19_518.txt",
         "name": "新建文本文档.txt", "type": "text/plain", "size": 5249, "raw": {}, "last_modified": 1674900257402}],
                    "monthly_template": {"tools_and_meters": [{"content": "1313"}], "mt_items": [{"name": "3131",
                                                                                                  "sub_items": [{
                                                                                                      "standard": "维护项标准：维护项标准说明",
                                                                                                      "selections": [
                                                                                                          {
                                                                                                              "value": 0,
                                                                                                              "label": "选项01"},
                                                                                                          {
                                                                                                              "value": 1,
                                                                                                              "label": "选项02"}],
                                                                                                      "value": None,
                                                                                                      "m_title": "01 维护项内容",
                                                                                                      "data_type": 1}]}]}},
     "current_project_id": 2}

print(json.dumps(a, ensure_ascii=False))
