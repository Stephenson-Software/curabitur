import os
import socket

class EchoClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        print(f"Connecting to {self.host}:{self.port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            connected = False
            attempts = 0
            while not connected:
                attempts += 1
                try:
                    s.connect((self.host, self.port))
                    connected = True
                except TimeoutError:
                    print("Connection timed out. Retrying. Attempts Made: " + str(attempts))

            while(True):
                # get user input
                userInput = input("> ")
                s.sendall(userInput.encode())
                data = s.recv(1024)
                print(f"Server: {data.decode()!r}")
                print("")


if __name__ == "__main__":
    print(" === Echo Client === ")
    ip = "192.168.0.84"
    port = 36578
    client = EchoClient(ip, port)
    client.connect()