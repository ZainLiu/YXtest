import pandas as pd
brand = set()
df_total = pd.read_excel("./xiaofang.xlsx", sheet_name=None)
for sheet_name, df in df_total.items():
    for index in df.index:
        row = df.loc[index]
        brand.add(row["厂商"])

df_total = pd.read_excel("./ruodian.xlsx", sheet_name=None)
for sheet_name, df in df_total.items():
    for index in df.index:
        row = df.loc[index]
        brand.add(row["厂商"])

print(list(brand))