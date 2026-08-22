# Curabitur
This repository is for practicing socket programming in Python by creating a simple chat application.

## Naming
The name of this repository is derived from the Latin word "curabitur" which means "to chat".

## How to Run
### Locally
1. Clone this repository
2. Run `python3 server/src/chatServer.py` in one terminal
3. Note the IP address the server prints on its `Listening on <IP>:36578...` line
4. Run `CHAT_SERVER_IP=<IP> python3 client/src/chatClient.py` in another terminal, using the address from the previous step

### Docker
1. Clone this repository
2. Open a terminal and navigate to the root of the repository
3. Run `bash run_server.sh` in that terminal
4. Note the IP address the server prints on its `Listening on <IP>:36578...` line
5. Open another terminal and navigate to the root of the repository
6. Run `bash run_client.sh <IP>` in the second terminal, using the address from step 4

## Learning Resources
- https://realpython.com/python-sockets/
- https://docs.python.org/3/howto/sockets.html
- https://www.geeksforgeeks.org/socket-programming-python/

## License
This project is licensed under the Stephenson Software Non-Commercial License (Stephenson-NC). See [LICENSE](LICENSE) for the terms, which permit non-commercial use only. The full license text is published at https://github.com/Stephenson-Software/stephenson-nc-license.