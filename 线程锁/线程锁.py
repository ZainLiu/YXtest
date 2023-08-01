import threading


class Counter(object):
    count = 0
    lock = threading.Lock()

    def get_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()

    def do_count(self):
        self.lock.acquire()
        self.count += 1
        self.lock.release()

    def do_count_v2(self):
        self.count += 1

    def deal(self):
        self.count += 1


counter = Counter()


def sync_deal_obj(obj):
    obj.lock.acquire()
    obj.deal()
    obj.lock.release()


def count():
    for i in range(1000000):
        sync_deal_obj(counter)


t1 = threading.Thread(target=count)
t2 = threading.Thread(target=count)
t1.start()
t2.start()
t1.join()
t2.join()
print(counter.count)
