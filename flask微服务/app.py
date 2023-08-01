import json

a = {'name': '权限的测试', 'description': '权限的测试', 'users': [{'id': 420, 'name': '周伦'}], 'permission': [
    {'module': 'share_income_customer',
     'info': {'path_list': ['/fss/share_income_customer/create', '/fss/share_income_customer/update', None],
              'data_permission': [], 'is_edit_self': False, 'field_ignore': []},
     'router_names': {'Share_income_customer_add': {'module_perm_code': []},
                      'Share_income_customer_details': {'module_perm_code': ['addBtn']}}},
    {'module': 'share_income_contract',
     'info': {'path_list': ['/fss/share_income_contract/create', '/fss/share_income_contract/update', None],
              'data_permission': [], 'is_edit_self': False, 'field_ignore': []},
     'router_names': {'Share_income_contract_add': {'module_perm_code': []},
                      'Share_income_contract_details': {'module_perm_code': ['addBtn']}}},
    {'module': 'share_income_receivable',
     'info': {'path_list': ['/fss/share_income_customer/create', '/fss/share_income_customer/update', None],
              'data_permission': [], 'is_edit_self': False, 'field_ignore': []},
     'router_names': {'Share_income_receivable_add': {'module_perm_code': []},
                      'Share_income_receivable_details': {'module_perm_code': ['addBtn']}}},
    {'module': 'share_income_budget',
     'info': {'path_list': ['/fss/share_income_budget/create', '/fss/share_income_budget/update', None],
              'data_permission': [], 'is_edit_self': False, 'field_ignore': []},
     'router_names': {'Share_income_budget_add': {'module_perm_code': []},
                      'Share_income_budget_details': {'module_perm_code': ['addBtn']}}}], 'current_project_id': 5}

print(json.dumps(a,ensure_ascii=False))
b = {
    "id": 45,
    "name": "\u6d4b\u8bd5\u89d2\u827220220505__1_2",
    "current_project_id": 1,
    "description": "2333333",
    "user_id_list": [641],
    "permission": [
        {
            "module": "order",
            "menu":[],
            "info": {
                "path_list": [
                    "/work/order/test"
                ],
                "data_permission": 1,
                "is_edit_self": 0,
                "field_ignore": []
            }
        },
        {
            "module": "order",
            "menu":[],
            "info": {
                "path_list": [
                    "/work/order/test"
                ],
                "data_permission": 1,
                "is_edit_self": 0,
                "field_ignore": []

            }
        }
    ]
}
