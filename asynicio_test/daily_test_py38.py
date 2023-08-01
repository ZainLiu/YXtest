import asyncio
import time
from threading import Thread


async def async_function(num):  # 异步执行的任务方法
    await asyncio.sleep(num)
    print('异步任务{}完成时间：{}秒'.format(num, time.time() - now_time))


now_time = time.time()  # 程序运行时的时间戳
events = asyncio.wait([async_function(i) for i in range(10)])
asyncio.run(events)  # 用asyncio.run直接运行协程参数为协程函数及其参数
events2 = asyncio.wait([])