import pandas as pd

df = pd.read_excel("aaa.xlsx")
for index in df.index:
    row = df.loc[index]
    if row["工作地点"].count("中山") and row["专业"].count("电子商务"):
        print(row)
        print("************************************************************")