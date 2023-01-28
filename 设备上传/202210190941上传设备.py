a = ["lzy", "22", "33"]
b = "发起客服工单，以下人员可受理："+"、".join([f"{i}" for i in a])
print(b)
