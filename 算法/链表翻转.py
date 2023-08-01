class Node:
    def __init__(self, num, next=None):
        self.num = num
        self.next = next


class LinkList:
    first = Node(0)

    def __init__(self, len):
        head = Node(1)
        self.first.next = head
        for i in range(2, len + 1):
            head.next = Node(i)
            head = head.next

    def travel(self):
        p = self.first
        while True:
            if p.next:
                print(p.next.num)
                p = p.next
            else:
                break

    def reverse(self):
        p1 = self.first.next
        p2 = p1.next
        p1.next = None
        while True:
            if p2:
                if p2.next:
                    temp = p2.next
                    p2.next = p1
                    p1 = p2
                    p2 = temp
                else:
                    self.first.next = p2
                    p2.next=p1
                    break
            else:
                break




if __name__ == '__main__':
    ll = LinkList(10)
    # ll.travel()
    ll.reverse()
    ll.travel()

