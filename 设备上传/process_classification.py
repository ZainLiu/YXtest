import pandas as pd

df = pd.read_excel("eq_classification.xlsx")

df["系统"] = df["系统"].ffill()
df["系统编号"] = df["系统编号"].ffill()
df["子系统"] = df["子系统"].ffill()
df["子系统编号"] = df["子系统编号"].ffill()

total_data = {}
head = df.keys()
extr_fields = []
for key in head:
    if key.startswith("额外字段"):
        extr_fields.append(key)
print(extr_fields)

print(head)
for index in df.index:
    row = df.loc[index]
    # 处理额外字段
    extra_fields_info = []
    for extra_field in extr_fields:
        if not pd.isnull(row[extra_field]):
            extra_field_info_list = row[extra_field].split("|")
            extra_fields_info.append({
                "field_name": extra_field_info_list[0],
                "field_type": int(extra_field_info_list[1]),
                "is_required": int(extra_field_info_list[1]),
            })
    # print(row["系统"])
    sys = total_data.get(row["系统"], {"name": row["系统"],
                                     "code": row["系统编号"],
                                     "equipment_sub_system_dict": {}
                                     })
    sub_sys = sys["equipment_sub_system_dict"].get(row["子系统"], {"name": row["子系统"],
                                                                "code": row["子系统编号"],
                                                                "equipment_type": []
                                                                })
    sub_sys["equipment_type"].append({
        "name": row["设备类型"],
        "code": row["类型编号"],
        "extra_fields_info": extra_fields_info
    })
    sys["equipment_sub_system_dict"][row["子系统"]] = sub_sys
    total_data[row["系统"]] = sys

data = []
# 处理成列表
for key, value in total_data.items():
    value["equipment_sub_system"] = []
    for sub_key, sub_value in value["equipment_sub_system_dict"].items():
        value["equipment_sub_system"].append(sub_value)
    del value["equipment_sub_system_dict"]
    data.append(value)
print(data)
