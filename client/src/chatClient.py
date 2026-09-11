import os
import socket
import time

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def connect(self):
        print(f"Connecting to {self.host}:{self.port}...")
        connected = False
        attempts = 0
        while not connected:
            attempts += 1
            # a refused connect can leave the socket unusable, so dial with a fresh one
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self.host, self.port))
                connected = True
            except (TimeoutError, ConnectionRefusedError) as error:
                s.close()
                print(f"Connection failed: {error}. Retrying in 1 second. Attempts Made: {attempts}")
                time.sleep(1)

        with s:
            while(True):
                # get user input
                try:
                    userInput = input("Client: ")
                except EOFError:
                    print("\nInput closed. Exiting.")
                    return
                s.sendall(userInput.encode())
                data = s.recv(1024)
                print(f"Server: {data.decode()!r}")
                print("")


if __name__ == "__main__":
    print(" === Chat Client === ")
    ip = os.environ.get("CHAT_SERVER_IP")
    
    if ip is None:
        print("CHAT_SERVER_IP environment variable not set. Exiting.")
        exit(1)
    
    port = 36578
    client = ChatClient(ip, port)
    try:
        client.connect()
    except KeyboardInterrupt:
        # Ctrl-C at the prompt, in recv() or while retrying; the with block closes the socket
        print("\nInterrupted. Exiting.")