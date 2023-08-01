# a = [2, 4, 6, 3, 1, 5, 6, 7, 1]
#
#
# def partition(arr, low, high):
#     i = low - 1
#     pivot = arr[high]
#
#     for j in range(low, high):
#         if arr[j] <= pivot:
#             i += 1
#             arr[i], arr[j] = arr[j], arr[i]
#
#     arr[i + 1], arr[high] = arr[high], arr[i + 1]
#     return i + 1
#
#
# def quick_sort(arr, low, high):
#     if low < high:
#         pi = partition(arr, low, high)
#         quick_sort(arr, low, pi - 1)
#         quick_sort(arr, pi + 1, high)
#
#
# # 测试示例
# arr = [5, 3, 8, 6, 2, 7, 1, 4]
# n = len(arr)
# quick_sort(arr, 0, n - 1)
# print(arr)


def my_quick_sort(arr, low, high):
    if low > high:
        return
    mid_data = arr[high]
    p = low - 1
    for i in range(low, high):
        if arr[i] <= mid_data:
            p += 1
            arr[i], arr[p] = arr[p], arr[i]

    arr[high], arr[p + 1] = arr[p + 1], arr[high]
    my_quick_sort(arr, low, p)
    my_quick_sort(arr, p + 2, high)


if __name__ == '__main__':
    arr = [5, 3, 8, 6, 2, 7, 1, 4]
    my_quick_sort(arr, 0, len(arr) - 1)
    print(arr)
