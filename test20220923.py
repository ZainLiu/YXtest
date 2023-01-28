import json

test_data = {"current_project_id": "2",
             "name": "测试20221008",
             "description": "测试20221008",
             "dc_user_map_list": [
                 {
                     "data_center": {"id": 1, "name": "汇云数据中心"},
                     "user_id_list": [{"id": 494, "name": "周永航"}]
                 }
             ],
             "permission": [
                 {"module": "dictionary", "info": {
                     "path_list": ["/ops/dictionary/add_parent", "/ops/dictionary/view"],
                     "data_permission": 0, "is_edit_self": False, "field_ignore": [],
                     "menu": ["dictionary", "dictionaryAddBtn", "dictionaryAddChildren", "dictionaryDelBtn"]}},
             ]}

update_data = {
    "id": 2,
    "current_project_id": "2",
    "name": "测试20221008-1",
    "description": "测试20221008-1",
    "dc_user_map_list": [
        {
            "id": 91,
            "data_center": {"id": 1, "name": "汇云数据中心"},
            "user_id_list": [{"id": 494, "name": "周永航"}, {"id": 452, "name": "陈文杰"}]
        },
        {
            "data_center": {"id": 2, "name": "飞云数据中心"},
            "user_id_list": [{"id": 460, "name": "陈建楠"}]
        }
    ],
    "permission": [
        {"module": "dictionary", "info": {
            "path_list": ["/ops/dictionary/add_parent", "/ops/dictionary/view"],
            "data_permission": 0, "is_edit_self": False, "field_ignore": [],
            "menu": ["dictionary", "dictionaryAddBtn", "dictionaryAddChildren", "dictionaryDelBtn"]}},
    ]}

user_update_data = {
    "current_project_id": 2,
    "role_id_list": [91, 92],
    "enabled": 1,
    "is_at_work": 1,
    "id": 494,
    "default_role_id": 91
}

a = {'id': 2, 'current_project_id': '2', 'name': '测试20221008-1', 'description': '测试20221008-1', 'dc_user_map_list': [{'id': 91, 'data_center': {'id': 1, 'name': '汇云数据中心'}, 'user_id_list': [{'id': 494, 'name': '周永航'}, {'id': 452, 'name': '陈文杰'}]}, {'data_center': {'id': 2, 'name': '飞云数据中心'}, 'user_id_list': [{'id': 460, 'name': '陈建楠'}]}], 'permission': [{'module': 'dictionary', 'info': {'path_list': ['/ops/dictionary/add_parent', '/ops/dictionary/view'], 'data_permission': 0, 'is_edit_self': False, 'field_ignore': [], 'menu': ['dictionary', 'dictionaryAddBtn', 'dictionaryAddChildren', 'dictionaryDelBtn']}}]}


# print(json.dumps(test_data))
# print(json.dumps(update_data))
# print(json.dumps(user_update_data))

# print(json.dumps(a, ensure_ascii=False))
print(json.dumps(a, ensure_ascii=False))