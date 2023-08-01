from my_redis_test import StrictRedis

redis = StrictRedis.from_url("redis相关://127.0.0.1")
redis.publish(channel="sseTest",message="123")