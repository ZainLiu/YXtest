import json

a = {
    "data_center_id": 1,
    "id": 12,
    "cus_brand_id": 63,
    "cus_brand_name": "0427 - 品牌 - 文琦",
    "cus_id": 111,
    "cus_name": "IP_带宽_机柜_01",
    "contact_id": 141,
    "contact_name": "IP_带宽_机柜_01",
    "contact_phone": "13454564522",
    "service_content": "设备 SN : 6F010311 设．位宜： R720 JJHMSZI 6F010311 32 一 33 操作要求：帮忙接上显示器看下什么情况，然后，关机把内存都重新拔插下。",
    "estimated_time": "2022-12-05 10:15:15",
    "priority": 1,
    "wot_id": 5,
    "operate_type": 4,
    "sh_eq": {
        "cser": [{
            "id": 4,
            "gsf_id": 1,
            "me_id": 1,
        }],
        "mter": []
    }

    ,
    "cab_eq": {
        "cser": [{
            # "id": 4,
            "r_id": 1,
            "me_id": 1,
            "u_bit_id_list": [1, 2]
        }],
        "mter": []
    }
}

# 客服工单关联
print(json.dumps(a, ensure_ascii=False))
