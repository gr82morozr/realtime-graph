import socket
import sys

HOST, PORT = "127.0.0.1", 10123

# SOCK_DGRAM is the socket type to use for UDP sockets
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# As you can see, there is no connect() call; UDP has no connections.
# Instead, data is directly sent to the recipient via sendto().
for i in range(1000):
  sock.sendto(bytes(str(i) + "\n", "utf-8"), (HOST, PORT))


print("Sent:     {}".format(i))
