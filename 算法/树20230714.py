# a = [1, 0, 2, 3, 0, None, 1]
a = [1, 0, 2]

total = 0


def check(a, i):
    print(a[i])
    global total
    if a[i] is None:
        return 0, 0
    if 2 * i + 1 > len(a) - 1:
        total += abs(a[i] - 1)
        return 1, a[i]

    a1, b1 = check(a, 2 * i + 1)

    a2, b2 = check(a, 2 * i + 2)
    node_num = a1 + a2 + 1
    val_num = b1 + b2 + a[i]
    total += abs(node_num - val_num)
    return node_num, val_num


# Definition for a binary tree node.
# class TreeNode(object):
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution(object):
    """leetcode979真题答案"""
    total = 0

    def distributeCoins(self, root):
        """
        :type root: TreeNode
        :rtype: int
        """
        self.check(root)
        return self.total

    def check(self, node):
        if not node:
            return 0, 0
        if not node.left and not node.right:
            self.total += abs(node.val - 1)
            return 1, node.val
        a1, b1 = self.check(node.left)
        a2, b2 = self.check(node.right)
        node_num = a1 + a2 + 1
        val_num = b1 + b2 + node.val
        self.total += abs(node_num - val_num)
        return node_num, val_num


if __name__ == '__main__':
    c, _ = check(a, 0)
    print(f"步数为：{total}")
