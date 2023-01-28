import json

q = [
    {
        "name": "1栋",
        "id": 1,
        "floor_info": [
            {
                "id": 1,
                "name": "1楼",
                "room_info": [
                    {
                        "id": 1,
                        "name": "SHV0101",
                        "eq_info": [
                            {
                                "id": 1,
                                "eq_name": "1#冷水机",
                                "full_code": "xxxx",
                                "mt_operator_id": 1,
                                "mt_operator_name": "233",
                                "mt_date": "2022-10-21"
                            }
                        ]
                    }
                ],
            }
        ]
    }
]

aa = {
    1: {
        "name": "1栋",
        "id": 1,
        "floor_info": {
            1: {
                "id": 1,
                "name": "1楼",
                "room_info": {
                    1: {
                        "id": 1,
                        "name": "SHV0101",
                        "eq_info": [
                            {
                                "id": 1,
                                "eq_name": "1#冷水机",
                                "full_code": "xxxx",
                                "mt_operator_id": 1,
                                "mt_operator_name": "233",
                                "mt_date": "2022-10-21"
                            }
                        ]
                    }
                },
            }
        },

    }
}

eq_info = []
for building_id, building_info in aa.items():
    floors_info = []
    for floor_id, floor_info in building_info["floor_info"].items():
        rooms_info = []
        for _, room_info in floor_info["room_info"].items():
            rooms_info.append(room_info)
        floor_info["room_info"] = rooms_info
        floors_info.append(floor_info)
    building_info["floor_info"] = floors_info
    eq_info.append(building_info)

print(eq_info)

bb = [
    {
        "name": "1栋",
        "id": 1,
        "floor_info": [
            {
                "id": 1,
                "name": "1楼",
                "room_info": [
                    {
                        "id": 1,
                        "name": "SHV0101",
                        "eq_info": [
                            {
                                "id": 1,
                                "eq_name": "1#冷水机",
                                "full_code": "xxxx",
                                "mt_operator_id": 1,
                                "mt_operator_name": "233",
                                "mt_date": "2022-10-21"
                            }
                        ]
                    }
                ]
            }
        ]
    }
]
print(json.dumps(bb, ensure_ascii=False))
