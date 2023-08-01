from etcd3 import client

etcd = client(host="101.43.25.116")

def get_service_url(service_name):
    response = etcd.get('/services/{}'.format(service_name))

    if response[0]:
        return response[0].decode("utf8")
    return None

# 调用示例
service_name = 'test_app'
service_url = get_service_url(service_name)
if service_url:
    print('Service URL:', service_url)
else:
    print('Service not found:', service_name)


etcd.delete('/services/{}'.format(service_name))