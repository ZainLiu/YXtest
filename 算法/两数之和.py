
def twoSum(nums, target):
    temp = dict()
    for i in range(len(nums)):
        if nums[i] <= target:
            if nums[i] in temp.keys():
                return [temp[nums[i]], i]
            else:
                temp[target-nums[i]]=i

if __name__ == '__main__':

    res = twoSum([-3,4,3,90],0)
    print(res)
