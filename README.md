# Curabitur
This repository is for practicing socket programming in Python by creating a simple chat application.

## Naming
The name of this repository is derived from the Latin word "curabitur" which means "to chat".

## How to Run
### Locally
1. Clone this repository
2. Run `python3 server.py` in one terminal
1. Set the `CHAT_SERVER_IP` environment variable to 0.0.0.0
3. Run `python3 client.py` in another terminal

### Docker
1. Clone this repository
1. Open a terminal and navigate to the root of the repository
1. Run the `run_server.sh` script in one terminal
1. Open another terminal and navigate to the root of the repository
1. Set the `CHAT_SERVER_IP` environment variable to the IP address of the server (displayed in server output)
1. Run the `run_client.sh` script in the second terminal

## Learning Resources
- https://realpython.com/python-sockets/
- https://docs.python.org/3/howto/sockets.html
- https://www.geeksforgeeks.org/socket-programming-python/