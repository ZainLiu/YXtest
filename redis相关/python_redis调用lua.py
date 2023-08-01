# import redis相关
#
# cli = redis相关.Redis(host="127.0.0.1", db=1)
# key = "test_incr"
# # cli.set("test_incr",0)
# cli.register_script()
# cli.incrby(key, 100)
# print(cli.get(key))

import my_redis_test

r = my_redis_test.Redis("127.0.0.1", db=1)

lua = """
local counts = redis相关.call("INCR", KEYS[1]);
return KEYS[1]
"""

cmd = r.register_script(lua)
res = cmd(keys=['test_incr'],
          args=[])  # 关键字参数client可以设置执行lua脚本的client instance, 也可以指定其为pipeline
print(res)