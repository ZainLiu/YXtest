import json

aa = {
    "id": 4,
    "detail_info": [
        {
            "id": 1,
            "start_date": "2022-11-1",
            "end_date": "2022-11-31"
        },
        {
            "id": 2,
            "start_date": None,
            "end_date": None
        }
    ]

}

print(json.dumps(aa))
