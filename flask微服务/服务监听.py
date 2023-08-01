from etcd3 import client

etcd = client(host="101.43.25.116")

def get_event_type(event):
    """
    根据修订版本比较来确定事件类型
    """
    if event.prev_kv is None:
        return "EventType.PUT"
    else:
        return "EventType.DELETE"
def watch_service():
    watcher,b = etcd.watch_prefix('/services/')
    for event in watcher:
        print(11111111111111111)
        # event_type = event.pre_EventType
        key = event.key.decode('utf-8')
        if hasattr(event, "event_type"):
            if event.event_type == 'DELETE':
                # 服务下线，进行相应处理，例如删除服务相关的注册信息
                print('Service offline:', key)
                delete_service_info(key)

def delete_service_info(service_key):
    etcd.delete(service_key)
    # 在此处可以执行其他与服务下线相关的操作

# 启动服务监听
watch_service()