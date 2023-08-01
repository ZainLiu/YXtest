import redis

conn = redis.Redis(db=1)
for i in conn.keys():
    b = i.decode()
    if b.startswith("2023"):
        print(b)

print(conn.smembers("2023-07-25_contract_current_value"))
# print(conn.smembers("2023-07-06_contract_current_value"))
conn.delete("2023-07-25_contract_current_value")
# """{"monthly": [12], "annually": [12], "quarterly": [12], "semiannually": [12]}"""
# print(conn.srem("app_route_OpsService_OpsApp", '{"server": "10.200.199.205", "port": 5220, "blueprint": "/ops"}'))
