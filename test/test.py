import socket

HOST = "127.0.0.1"
PORT = 6006

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("Listening for PSRR packets...\n")

while True:
    data, addr = sock.recvfrom(4096)
    print(f"Received: {data.decode()}")
