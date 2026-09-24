import socket

from usage_reporting import reportConnected, startUsageReporting

class ChatServer:
    def __init__(self, host, port, usage=None):
        self.host = host
        self.port = port
        # the trace client from usage_reporting, or None to report nothing
        self.usage = usage

    def listen(self):
        while True:
            print(f"Listening on {self.host}:{self.port}...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # allow re-binding while a previous connection is still in TIME_WAIT
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.host, self.port))
                s.listen()
                connection, address = s.accept()
                with connection:
                    print(f"Accepted connection from {address}")
                    if self.usage is not None:
                        reportConnected(self.usage)
                    while True:
                        data = connection.recv(1024)
                        if not data:
                            break
                        print(f"Client: {data.decode()!r}")
                        # get response from server
                        try:
                            userInput = input("Server: ")
                        except EOFError:
                            print("\nInput closed. Exiting.")
                            return
                        data = userInput.encode()
                        connection.sendall(data)

if __name__ == "__main__":
    print(" === Chat Server === ")
    ip = socket.getaddrinfo(socket.gethostname(), 0, socket.AF_INET)[0][4][0]
    usage = startUsageReporting()
    port = 36578
    server = ChatServer(ip, port, usage)
    try:
        server.listen()
    except KeyboardInterrupt:
        # Ctrl-C at the prompt, in accept() or in recv(); the with blocks close the sockets
        print("\nInterrupted. Exiting.")