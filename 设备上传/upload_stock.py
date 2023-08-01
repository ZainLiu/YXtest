import json
import time

import requests

header = {
    "Authorization": "hxBUHw6GcB0wyfxbOQZoo4cgQLurr/maq7B8RY9F0aNJziR64XhYllbiFhs2NUbi5zLVwoK02vt3iI3V+FmWdO/QeiLH3w8gxaQzt1bU5zLxDS8r1NrTtlTph8sjiTbjBNZQgS/gYiyhTyzcgP6p9S23wpV8D38r7MapVYbjkFU="}
with open("./data/stock_info.xlsx", "rb") as f:
    # print(f)
    a = time.time()
    result = requests.post("http://127.0.0.1/ops/cus_mt_io_manage/upload",
                           data={"current_project_id": 2},
                           headers=header,
                           files={"file": f})
    print(time.time()-a)
    print(result.content)
    print(json.dumps(result.json(), ensure_ascii=False))
