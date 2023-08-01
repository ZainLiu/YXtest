import json
import time

import requests

header = {
    "Authorization": "VNXuymJnwyeIQ2T0QESj/HLtG3ULozFxFL4CcpvkebRiPkK9GlZ1kdVM9B7CbUZhM8n2V/4nP3KvWSJviN0gm153m9m49nCkMKNgmHXvfrE4RaSfigh66RuelGg1bdFs6ZlUpZc49bEpXAeDH1GeOfH3nw+snm4+3sdiY6z1IS0="}
with open("./data/cab_column.xlsx", "rb") as f:
    # print(f)
    a = time.time()
    result = requests.post("http://127.0.0.1:6000/gateway/gateway/dispatch/ops/equipment/upload_cab",
                           data={"current_project_id": 2},
                           headers=header,
                           files={"file": f})
    print(time.time()-a)
    print(result.content)
    print(json.dumps(result.json(), ensure_ascii=False))
