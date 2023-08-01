from concurrent.futures import ThreadPoolExecutor
import threading
import time


# 定义一个准备作为线程任务的函数
def action(max):
    time.sleep(1)
    t_id = threading.current_thread().ident
    print(f"{t_id}\n")
    return t_id


# 创建一个包含2条线程的线程池
pool = ThreadPoolExecutor(max_workers=3)
# 向线程池提交一个task, 50会作为action()函数的参数
future_list = []
for i in range(10):
    future = pool.submit(action, i)
    future_list.append(future)
time.sleep(5)
result_list = set()
for future in future_list:
    result_list.add(future.result())

print(result_list)

# 关闭线程池
pool.shutdown()
