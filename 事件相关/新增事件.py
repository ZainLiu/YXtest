import json

save_event = {
    "type": 1,
    "occur_time": "2022-10-25 13:37:40",
    "eq_sys_id": 58,
    "level": 1,
    "room_id": 569,
    "eq_id": 2967,
    "description": "2333小问题",
    "annex": [],
    "solve_time": "2022-10-26 13:37:40"
}

follow = {
    "id": 5,
    "epd_id": 1,
    "description": "2333",
    "annex": []
}
print(json.dumps(follow, ensure_ascii=False))
