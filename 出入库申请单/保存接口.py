import json

mt_in = {
    "type": 1,
    "business_type": 1,
    "is_self_use": 0,
    "cus_id": 111,
    "cus_name": "xxx",
    "mark": "xxx",
    "related_odd_num": [{
        "id": 40,
        "serial_number": "GZHY-NE-20221130009"
    }],
    "store_house_id": 1,
    "detail_info": [
        {
            "mt_id": 1441,
            "type": 1,
            "gsf_id": 1,
            "num": 1,
            "sn_no_list": [{
                "sn_no": "AW3L690826200041",
                "mark": "xxx"
            }]
        }
    ]
}

mt_out = {
    "type": 2,
    "business_type": 1,
    "is_self_use": 0,
    "cus_id": 111,
    "cus_name": "xxx",
    "mark": "xxx",
    "related_odd_num": [{
        "id": 40,
        "serial_number": "GZHY-NE-20221130009"
    }],
    "store_house_id": 1,
    "detail_info": [
        {
            "mt_id": 1441,
            "type": 2,
            "gsf_id": 1,
            "num": 1,
            "sn_no_list": [{
                "sn_no": "AW3L690826200041",
                "id": 4,
                "mark": "xxx"
            }]
        }
    ]
}

# print(json.dumps(mt_in, ensure_ascii=False))
print(json.dumps(mt_out, ensure_ascii=False))
