import codecs
import os
import socket
import time

from usage_reporting import reportConnected, startUsageReporting

class ChatClient:
    def __init__(self, host, port, usage=None):
        self.host = host
        self.port = port
        # the trace client from usage_reporting, or None to report nothing
        self.usage = usage

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
            except OSError:
                # the address cannot be resolved (socket.gaierror), or the host or network
                # cannot be reached; report it rather than retrying
                s.close()
                raise

        if self.usage is not None:
            reportConnected(self.usage)

        # a multi-byte character can span two recv() chunks; the decoder holds the
        # incomplete tail over to the next chunk instead of failing on it
        decoder = codecs.getincrementaldecoder("utf-8")()
        with s:
            while(True):
                # get user input; an empty message would put nothing on the wire and leave
                # both sides waiting for the other, so prompt again instead of sending it
                userInput = ""
                while not userInput:
                    try:
                        userInput = input("Client: ")
                    except EOFError:
                        print("\nInput closed. Exiting.")
                        return
                try:
                    s.sendall(userInput.encode())
                    data = s.recv(1024)
                except (ConnectionResetError, BrokenPipeError):
                    # the server went away abruptly between prompts
                    data = b""
                if not data:
                    # an empty recv means the server closed the connection
                    print("Server disconnected. Exiting.")
                    return
                print(f"Server: {decoder.decode(data)!r}")
                print("")


if __name__ == "__main__":
    print(" === Chat Client === ")
    ip = os.environ.get("CHAT_SERVER_IP")
    
    if ip is None:
        print("CHAT_SERVER_IP environment variable not set. Exiting.")
        exit(1)
    
    usage = startUsageReporting()
    port = 36578
    client = ChatClient(ip, port, usage)
    try:
        client.connect()
    except KeyboardInterrupt:
        # Ctrl-C at the prompt, in recv() or while retrying; the with block closes the socket
        print("\nInterrupted. Exiting.")
    except socket.gaierror as error:
        # a mistyped IP or an unknown host name in CHAT_SERVER_IP
        print(f"Could not resolve CHAT_SERVER_IP {ip!r}: {error.strerror}. Exiting.")
        exit(1)
    except OSError as error:
        # an unreachable host or network when dialing, or a connection that fails mid-chat
        # in a way other than a reset; an OSError raised without an errno has no strerror
        print(f"Connection to {ip}:{port} failed: {error.strerror or error}. Exiting.")
        exit(1)