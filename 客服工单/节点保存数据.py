# 工具准备节点
import json

tool_preparation = {
    "id": 46,
    "content": {
        # "content": "2333",
        "is_need_material": 0,
        "material_info": {
            "risk_rate": 1,  # # 1:大于50% 2: 30%-50% 3:小于30%
            "mark": "测试",
            "cus_material": [],
            "self_material": [{
                # "id": 1,
                "gsf_id": 1,
                "mt_id": 1441,
                "num": 1,
                "sn_no_list": [{
                    "id": 3,
                    "sn_no": "AW3L690826200040"
                }]
            }]
        }
    }
}

# 出库设备
EqMoveOut = {
    "id": 47,
    "content": [{
        "id": 2,
        "gsf_id": 1,
        "me_id": 1,
    }]
}

jp = {
    "id": 34,
    "content": [
        {
            "id": 4,
            "is_finish": 0,
            "mark": "已完成",
            "photos": [{
                "id": 1798,
                "last_modified": 1664545488641,
                "name": "1.jpg",
                "raw": {},
                "size": 3083,
                "type": "image/jpeg",
                "url": "https://opspre.imyunxia.com/file/2022_11_30/2022_11_30_12_08_14_1.jpg"
            }],

        }
    ],
}
photo = {
    "id": 35,
    "content": [
        {
            "id": 1798,
            "last_modified": 1664545488641,
            "name": "1.jpg",
            "raw": {},
            "size": 3083,
            "type": "image/jpeg",
            "url": "https://opspre.imyunxia.com/file/2022_11_30/2022_11_30_12_08_14_1.jpg"
        },
        {
            "id": 1798,
            "last_modified": 1664545488641,
            "name": "1.jpg",
            "raw": {},
            "size": 3083,
            "type": "image/jpeg",
            "url": "https://opspre.imyunxia.com/file/2022_11_30/2022_11_30_12_08_14_1.jpg"
        }
    ]

}
confirm = {
    "id": 40,
    "content": "报告已完成"
}

UpEq = {
    "id": 1,
    "content": {
        "cser": [
            {
                "id": 1,
                "r_id": 1,
                "u_bit_id_list": [1, 2, 3]
            }
        ],
        "mter": []
    }
}
DownEq = {
    "id": 1,
    "content": [
        {
            # "id": 4,
            "r_id": 1,
            "me_id": 1,
            "u_bit_id_list": [1, 2]
        }
    ]
}

InEq = {
    "id": 1,
    "content": {
        "cser": [
            {
                "id": 1,
                "gsf_id": 1
            }
        ],
        "mter": []
    }
}
SIWarehousing = {
    "id": 1,
    "content": [
        {
            "id": 1,
            "gsf_id": 1,
            "mt_id": 1,
            "num": 1,
            "sn_no_list": []
        }
    ]
}

SIOnShelf = {
    "id": 1,
    "content": [
        {
            "id": 1,
            "mt_id": 1,
            "r_id": 1,
            "sn_no": 1,
            "u_bit_id_list": []
        }
    ]
}

print(json.dumps(tool_preparation, ensure_ascii=False))
# print(json.dumps(jp, ensure_ascii=False))
# print(json.dumps(photo, ensure_ascii=False))
# print(json.dumps(confirm, ensure_ascii=False))
# print(json.dumps(EqMoveOut, ensure_ascii=False))
