def judge_two_line_is_intersect(a, b):
    for i in range(len(a) - 1):
        a1 = a[i]
        a2 = a[i + 1]
        b1 = b[i]
        b2 = b[i + 1]

        if (a1[1] >= b1[1] and a2[1] <= b2[1]) or (a1[1] <= b1[1] and a2[1] >= b2[1]):
            return "两线相交"
    return "两线不相交"


if __name__ == '__main__':
    a = [(0, -0.045), (1, -0.018), (2, 0.117)]
    b = [(0, 0.076), (1, 0.057), (2, 0.069)]
    print(judge_two_line_is_intersect(a, b))
