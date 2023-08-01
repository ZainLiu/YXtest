a = [2, 4, 6, 3, 1, 5, 6, 7]

l = len(a)
for i in range(l):
    j = i + 1
    while j < l - 1:
        if a[j] < a[i]:
            a[i], a[j] = a[j], a[i]
        j += 1

print(a)
