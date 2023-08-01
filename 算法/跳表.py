import random


class SkipListNode:
    def __init__(self, key=None, val=None, level=0):
        self.key = key
        self.val = val
        self.next = [None] * level


class SkipList:
    def __init__(self, max_level=16, p=0.5):
        self.head = SkipListNode(level=max_level)
        self.max_level = max_level
        self.p = p
        self.level = 0

    def random_level(self):
        level = 0
        while random.random() < self.p and level < self.max_level:
            level += 1
        return level

    def search(self, key):
        cur = self.head
        for i in range(self.level - 1, -1, -1):
            while cur.next[i] and cur.next[i].key < key:
                cur = cur.next[i]
        cur = cur.next[0]
        if cur and cur.key == key:
            return cur.val
        return None

    def insert(self, key, val):
        update = [None] * self.max_level
        cur = self.head
        for i in range(self.level - 1, -1, -1):
            while cur.next[i] and cur.next[i].key < key:
                cur = cur.next[i]
            update[i] = cur
        cur = cur.next[0]
        if cur and cur.key == key:
            cur.val = val
        else:
            level = self.random_level()
            if level > self.level:
                for i in range(self.level, level):
                    update[i] = self.head
                self.level = level
            node = SkipListNode(key, val, level)
            for i in range(level):
                node.next[i] = update[i].next[i]
                update[i].next[i] = node

    def delete(self, key):
        update = [None] * self.max_level
        cur = self.head
        for i in range(self.level - 1, -1, -1):
            while cur.next[i] and cur.next[i].key < key:
                cur = cur.next[i]
            update[i] = cur
        cur = cur.next[0]
        if cur and cur.key == key:
            for i in range(self.level):
                if update[i].next[i] != cur:
                    break
                update[i].next[i] = cur.next[i]
            while self.level > 0 and self.head.next[self.level - 1] is None:
                self.level -= 1

    def print_list(self):
        for i in range(self.level - 1, -1, -1):
            cur = self.head.next[i]
            print("Level {}: ".format(i), end="")
            while cur:
                print("({}, {})".format(cur.key, cur.val), end=" ")
                cur = cur.next[i]
            print("")


# test code
if __name__ == "__main__":
    sl = SkipList()
    for i in range(20):
        sl.insert(i, i * 10)
    sl.print_list()
    # sl.delete(10)
    # sl.print_list()
    print(sl.search(10))
