import my_redis_test

# 创建Redis客户端
redis_client = my_redis_test.Redis(host='localhost', port=6379, db=0)

# 创建一个PubSub对象
pubsub = redis_client.pubsub()
pubsub.subscribe('mychannel')
for message in pubsub.listen():
    print(message)
