import socket

host = "127.0.0.1"
port = 9999
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
print(f"Listen on {host}:{port}")

