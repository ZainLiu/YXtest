import threading
import time


class MyLock:
    flag = False

    def acquire_lock(self):
        if self.flag == False:
            self.flag = True
            return True
        return False

    def release(self):
        self.flag = False


lock = MyLock()


def hello(lock, thread_no):
    while True:
        flag = lock.acquire_lock()
        if flag:
            # if thread_no==2:
            print(f"{thread_no}获取锁成功")
            lock.release()
            time.sleep(1)

        # else:
        #     print(f"{thread_no}获取不到锁")


t1 = threading.Thread(target=hello, args=(lock, 1))
t2 = threading.Thread(target=hello, args=(lock, 2))
t1.start()
t2.start()
t1.join()
t2.join()


