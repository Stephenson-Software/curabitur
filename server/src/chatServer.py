import socket

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def listen(self):
        while True:
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
                        print(f"Client: {data.decode()!r}")
                        # get response from server
                        userInput = input("Server: ")
                        data = userInput.encode()
                        connection.sendall(data)

if __name__ == "__main__":
    print(" === Chat Server === ")
    ip = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET)[0][4][0]
    port = 36578
    server = ChatServer(ip, port)
    server.listen()