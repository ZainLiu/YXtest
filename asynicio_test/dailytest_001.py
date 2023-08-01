import asyncio
import time
from threading import Thread


def thread_new_loop(loop):  # 创建线程版洗衣机
    asyncio.set_event_loop(loop)  # 在线程中调用loop需要使用set_event_loop方法指定loop
    loop.run_forever()  # run_forever() 会永远阻塞当前线程，直到有人停止了该loop为止。


async def async_function(num):  # 异步执行的任务方法
    await asyncio.sleep(num)
    print('异步任务{}花费时间：{}秒'.format(num, time.time() - now_time))
    return '异步任务{}完成时间：{}秒'.format(num, time.time() - now_time)


now_time = time.time()  # 程序运行时的时间戳
new_loop = asyncio.new_event_loop()  # 创建一个新的loop，get_event_loop()只会在主线程创建新的event loop，其他线程中调用 get_event_loop() 则会报错
new_loop1 = asyncio.new_event_loop()  # 创建一个新的loop，get_event_loop()只会在主线程创建新的event loop，其他线程中调用 get_event_loop() 则会报错
t = Thread(target=thread_new_loop, args=(new_loop,))  # 创建线程
t1 = Thread(target=thread_new_loop, args=(new_loop1,))  # 创建线程
# t.setDaemon(True)
# t1.setDaemon(True)
t.start()  # 启动线程
t1.start()
even = asyncio.run_coroutine_threadsafe(async_function(1), new_loop1)  # 调用asyncio.run_coroutine_threadsafe实现回调
even.cancel()  # 当run_coroutine_threadsafe对象执行cancel()方法就会取消该任务事件（当速度够快有概率取消前已经执行）
asyncio.run_coroutine_threadsafe(async_function(2), new_loop)
asyncio.run_coroutine_threadsafe(async_function(3), new_loop1)
print('红后主进程运行花费时长：{}秒'.format(time.time() - now_time))

