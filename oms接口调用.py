import json

import requests


class OmsApiRequestService:

    def __init__(self):

        self.customer_info_url = "https://omspre.imyunxia.com/sales/ops_customer/list_simple"
        # 当前用户token
        self.authorization = "CiXCbSi4b+5Cq9+DGdZlz7PfsGhYSyN/fGPj8RWy4AUHSETa249kWR93cmDr/tAZcabLfoYgdZWYsnMTODLVFQtPKeK4nIHDIxo1SsMWXfw1gOoqYjww2+46CVk7o0dvE3qCiEJ3RRdcIw1fiTIax1Z2JMxPgokeQ7JQWGpC58o="

    def request_customer_info_url(self):
        """调用oms接口获取客户信息"""

        res_customer_info= requests.get(
            url=self.customer_info_url,
            headers={'Authorization': self.authorization}
        )
        res_data = res_customer_info.json()
        for data in res_data.get('data'):
            print(data)
        return res_data.get('data')


if __name__ == '__main__':
    req = OmsApiRequestService()
    data = req.request_customer_info_url()
    print(data)
