import json

a = {
    "year": 2022,
    "eq_sys_id": 58,
    "group_id": 7,
    "annex": [],
    "mark": "xxx",
    "detail_info": [
        {
            "emi_id": 6,
            "conf_info": {
                "monthly": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            }

        },
        {
            "emi_id": 10,
            "conf_info": {
                "monthly": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            }
        },
    ]
}
print(json.dumps(a))
