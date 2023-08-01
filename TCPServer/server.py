import socket
import threading

host = "127.0.0.1"
port = 9999
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
print(f"Listen on {host}:{port}")

server.listen(5)


def handler_client(client_socket):
    request = client_socket.recv(1024)
    print(f"[*] Received: {request}")
    client_socket.send("hi!~".encode())
    client_socket.close()


while True:
    client, addr = server.accept()
    print(f"[*] Acception connection from {addr[0]}:{addr[1]}")
    client_handler = threading.Thread(target=handler_client, args=(client,))
    client_handler.start()
