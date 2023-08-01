import my_redis_test

# 创建Redis客户端
redis_client = my_redis_test.Redis(host='localhost', port=6379, db=0)
redis_client.publish('mychannel', 'Hello, LZY!')
