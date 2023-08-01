class JosephusProblem:

    def __init__(self, people_num, num):
        self.people_num = people_num
        self.num = num
        self.first = Node(1)
        self.init_cycle()

    def init_cycle(self):
        head = self.first
        for i in range(2, self.people_num + 1):
            temp = Node(i)
            head.next = temp
            head = temp
            if i == self.people_num:
                head.next = self.first

    def len(self):
        len = 1
        temp = self.first
        while True:
            temp = temp.next
            if temp is self.first:
                break
            else:
                len += 1
        return len

    def rand_kill(self):
        pointer = self.first
        cnt = 1
        while True:
            len = self.len()
            if len >= self.num:
                temp = pointer
                pointer = pointer.next
                cnt += 1
                if cnt == self.num:
                    if pointer is self.first:
                        self.first = pointer.next
                    del_node = temp.next
                    temp.next = pointer.next
                    pointer = pointer.next
                    del del_node
                    cnt = 1
            else:
                break


class Node:
    def __init__(self, num, next=None):
        self.num = num
        self.next = next


if __name__ == '__main__':
    jb = JosephusProblem(41, 3)
    print(jb.len())
    jb.rand_kill()
    print(jb.len())
    node = jb.first
    for i in range(jb.len()):
        print(node.num)
        node = node.next

