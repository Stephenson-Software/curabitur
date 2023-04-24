import os
import socket

class EchoServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def listen(self):
        print(f"Listening on {self.host}:{self.port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            connection, address = s.accept()
            with connection:
                print(f"Accepted connection from {address}")
                while True:
                    data = connection.recv(1024)
                    if not data:
                        break
                    print(f"Received {data.decode()!r} from the client.")
                    print(f"Sending {data.decode()!r} back to the client.")
                    connection.sendall(data)

if __name__ == "__main__":
    print(" === Echo Server === ")
    ip = ""
    port = 36578
    server = EchoServer(ip, port)
    server.listen()