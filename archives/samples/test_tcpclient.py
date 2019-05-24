import socket
import sys

HOST, PORT = "127.0.0.1", 10123

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
  # Connect to server and send data
  sock.connect((HOST, PORT))
  for i in range(1000):
    sock.sendall(bytes(str(i) + "\n", "utf-8"))

finally:
    sock.close()

print("Sent:     {}".format(i))
