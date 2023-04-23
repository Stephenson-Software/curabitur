import os
import socket

class EchoClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        print(f"Connecting to {self.host}:{self.port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))

            while(True):
            # get user input
                userInput = input("Enter a message to send to the server: ")
                s.sendall(userInput.encode())
                data = s.recv(1024)
                print(f"Received {data.decode()!r} from the server.")
                print("")


if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 36578
    client = EchoClient(ip, port)
    client.connect()