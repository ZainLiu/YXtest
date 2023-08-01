import json

a = """name:戴尔R730
brand_id:1
unit:台
model:R730
specification:16GB 2TB 8核
mark:2333
mc_id:4
can_cab:1
has_sn_no:1
type:1
front_view:[]
rear_view:[]
"""
b = a.split()
e = dict()
for c in b:
    d = c.split(":")
    # e[d[0]] = d[1]
    print(d)
print(json.dumps(e, ensure_ascii=False))

ee = {"name": "戴尔R730", "brand_id": 1, "unit": "台", "model": "R730", "mark": "2333",
      "mc_id": 1, "can_cab": 1, "has_sn_no": 1, "type": 1, "front_view": [], "rear_view": [],
      "specification": "16GB 2TB 8核"}

a = [{"value": "400", "field_name": "额定电压(V)", "field_type": 2, "is_required": 2}]
b = [{"field_name": "SM码", "field_type": 2, "is_required": 2}]
