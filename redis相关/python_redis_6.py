import socket
import threading

# 创建 TCP/IP socket
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 绑定 IP 地址和端口号
server_address = ('localhost', 8888)
print('starting up on %s port %s' % server_address)
server_socket.bind(server_address)
# 监听连接
server_socket.listen(128)
has_deal_data_list = []
has_deal_data_lock = threading.Lock()


def recv_and_deal_req(client_socket, client_address):
    """处理请求"""
    # 接收客户端发送的数据
    while True:
        data = client_socket.recv(1024)
        print('received "%s"' % data)

        if data:
            # 发送响应数据
            has_deal_data_lock.acquire()
            has_deal_data_list.append([data, client_socket, client_address])
            has_deal_data_lock.release()
            time.sleep(10)

        else:
            # 客户端断开连接
            print('no data from', client_address)
            break
        print("11111111111")


# 处理线程方法
def deal_and_return():
    """处理和返回请求"""
    time.sleep(1)
    while True:
        if has_deal_data_list:
            has_deal_data_lock.acquire()
            deal_data = has_deal_data_list.pop()
            has_deal_data_lock.release()
            data = deal_data[0]
            client_socket = deal_data[1]
            response = f'Hello, client!{str(data)}'
            client_socket.sendall(response.encode())
        else:
            time.sleep(0.1)


t1 = threading.Thread(target=deal_and_return)
t1.start()

while True:
    # 等待客户端连接
    print('waiting for a connection')
    client_socket, client_address = server_socket.accept()

    try:
        t_temp = threading.Thread(target=recv_and_deal_req, args=(client_socket, client_address))
        t_temp.setDaemon(True)
        t_temp.start()
    finally:
        # 关闭客户端连接
        client_socket.close()
