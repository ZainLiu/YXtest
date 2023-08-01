import json

a = [i for i in range(1, 101)]
b = [{"name": "批次1", "eq_info": [{
    "eq_type_name": "直流电源屏",
    "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-DCPP-DCPP-1",
    "id": 7075,
    "location": "广州汇云/汇云1栋/1楼/SHV0101",
    "name": "2G段直流屏"
}]}]

b = [
    {
        "eq_type_name": "直流电源屏",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-DCPP-DCPP-1",
        "id": 7075,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G段直流屏"
    },
    {
        "eq_type_name": "直流电源屏",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-DCPP-DCPP-2",
        "id": 7076,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G段直流屏"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-1",
        "id": 6983,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G1(2#电源进线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-2",
        "id": 6984,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G2(计量柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-3",
        "id": 6985,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G3(联络副柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-4",
        "id": 6986,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G4(2#市电进线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-5",
        "id": 6987,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G5(2#柴发进线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-6",
        "id": 6988,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G6(11#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-7",
        "id": 6989,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G7(13#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-8",
        "id": 6990,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G8(15#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-9",
        "id": 6991,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G9(17#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH2-10",
        "id": 6992,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "2G10(19#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-10",
        "id": 6993,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G10(4#电源进线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-9",
        "id": 6994,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G9(计量柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-8",
        "id": 6995,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G8(联络副柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-7",
        "id": 6996,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G7(4#市电进线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-6",
        "id": 6997,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G6(4#柴发进线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-5",
        "id": 6998,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G5(9#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-4",
        "id": 6999,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G4(7#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-3",
        "id": 7000,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G3(1#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-2",
        "id": 7001,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G2(3#变压器出线柜)"
    },
    {
        "eq_type_name": "高压配电柜",
        "full_code": "YX-CHN-GD-GZHY-D1-1F-SHV0101-D-D1-AH-AH4-1",
        "id": 7002,
        "location": "广州汇云/汇云1栋/1楼/SHV0101",
        "name": "4G1(5#变压器出线柜)"
    }
]

c = """{
    "id": 181,
    "name": "\u6d4b\u8bd5\u65b0\u589e\u7c7b\u578b2",
    "code": "TEST2",
    "eq_sub_sys_id": 1,
    "extra_field": [
        {
            "field_name": "\u989d\u5b9a\u5bb9\u91cf\uff08AH) ",
            "is_required": 1,
            "field_type": 1
        },
        {
            "field_name": " \u7535\u6c60\u7535\u538b\uff08V\uff09",
            "is_required": 1,
            "field_type": 1
        },
        {
            "field_name": " \u5355\u7ec4\u6570\u91cf",
            "is_required": 1,
            "field_type": 1
        }
    ],
    "model_info": [
        {
            "id": 1,
            "model": "xxx",
            "manufacturer_id": 1
        },
        {
            "model": "xxx",
            "manufacturer_id": 1
        }
    ]
}"""
d = json.loads(c)
e = json.dumps(d, ensure_ascii=False)
print(e)
f = {"name": "直流电源屏", "code": "DCPP", "introduction": "", "id": 2487,
     "extra_field": [{"field_name": "交流输入(AC)", "field_type": 2, "is_required": 1},
                     {"field_name": "交流输出(AC)", "field_type": 2, "is_required": 1},
                     {"field_name": "直流输出(DC)", "field_type": 2, "is_required": 1}], "eq_sub_sys_id": 537,
     "current_project_id": 2,
     "model_info": [
         {
             "id": 201,
             "manufacturer_id": 3,
             "manufacturer_name": "厂商C",
             "model": "1231"
         },
         {
             "manufacturer_id": 3,
             "manufacturer_name": "厂商C",
             "model": "666"
         },

     ],
     }
