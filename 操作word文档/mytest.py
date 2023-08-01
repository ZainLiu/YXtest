import requests

url = "http://192.168.200.13:8088/rack/v1/daily/excel"
rq_data = {
    "fileName": "虎牙",
    "startDate": "2023-07-01 00:00:00",
    "endDate": "2023-07-06 00:00:00",
    "cabs": [
        {
            "id": 1,
            "contractCurrentValue": 15.6,
            "eqCode": "GZHY-D1-4F05-0101"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0102"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0102"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0103"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0104"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0105"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0106"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0107"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0108"
        },
        {
            "id": 1,
            "contractCurrentValue": 15.3,
            "eqCode": "GZHY-D1-4F05-0109"
        }
    ]
}
data = requests.post(url,json=rq_data)
print(data.content)