import os
import random
import time
import threading

task_dict = dict()

def hello(i):
    pid = threading.current_thread().ident
    print(f"{pid}say:hello-{i}")


def handle(task_dict):
    pid = threading.current_thread().ident
    task_dict[pid] = []
    while True:
        task_list = task_dict[pid]
        if task_list:
            task = task_list.pop()
            task[0](task[1])
            time.sleep(2)
        else:
            # print(f"{pid}sleep 1s")
            time.sleep(1)

if __name__ == '__main__':
    thread1 = threading.Thread(target=handle, args=(task_dict,))
    thread2 = threading.Thread(target=handle, args=(task_dict,))
    thread1.start()
    thread2.start()
    print(task_dict.keys())
    for i in range(10):
        key = random.choice(list(task_dict.keys()))
        print((i, key))
        task_dict[key].append((hello, i))
    time.sleep(5)
    for i in range(10):
        key = random.choice(list(task_dict.keys()))
        print((i, key))
        task_dict[key].append((hello, i))

    thread1.join()
    thread2.join()

