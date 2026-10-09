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

### Ending a Session
Press Ctrl-D at either program's prompt to close its input. Both the server and the client report `Input closed. Exiting.` and shut down cleanly.

Pressing Ctrl-C works at any point — at a prompt, while the server is waiting for a client, or while the client is retrying a connection. The program reports `Interrupted. Exiting.` and shuts down cleanly.

If the server goes away while the client is connected, the client reports `Server disconnected. Exiting.` on its next message and shuts down cleanly rather than prompting for input on a closed connection. When the client goes away, even abruptly, the server returns to waiting for a new connection.

## Usage reporting
Usage reporting is on by default: the server and the client each send the program's name (`curabitur`), its version and the events `startup` (when the program starts) and `connected` (when the server accepts a client, or the client reaches a server) to [trace](https://github.com/Stephenson-Software/trace) at `https://trace.danielstephenson.dev`. Every event carries a `role` tag saying which of the two sent it (`server` or `client`), and a random installation ID (the tag `install`) so installations can be counted rather than events. Nothing about you, your machine, your IP address, the addresses you connect to or the messages is sent. The report is made from a background thread, never blocks the chat, and is dropped silently if the service is unreachable.

The first launch of each program writes a `settings.json` next to its `src/` directory (`server/settings.json`, `client/settings.json`) and prints a one-line notice.

The installation ID is a random UUID kept in a file named `trace-install-id` in the user data directory, shared by the server and the client on the same machine: `~/.local/share/curabitur/` on Linux (or `$XDG_DATA_HOME/curabitur/`), `~/Library/Application Support/curabitur/` on macOS and `%APPDATA%\curabitur\` on Windows. It identifies no person, account or address; delete the file to get a new one. Setting the environment variable `TRACE_INSTALL_ID` sends that value instead and leaves the file alone. The file is only created while reporting is on, so every opt-out below also stops it.

To turn reporting off, any one of these is enough:

- `"usage_reporting": {"enabled": false}` in that program's `settings.json`:

  ```json
  {
    "usage_reporting": {
      "enabled": false
    }
  }
  ```

- the environment variable `TRACE_USAGE_REPORTING=off` (also `false`, `0`, `no`; case does not matter), which turns off every program that reports to trace
- the environment variable `DO_NOT_TRACK=1` (also `true`, `yes`; case does not matter; see [consoledonottrack.com](https://consoledonottrack.com))

Any other value, including an empty one, leaves the `settings.json` setting in charge.

The environment variables win over `settings.json`. Under Docker the containers are removed on exit, so a `settings.json` written inside one does not persist; `run_server.sh` and `run_client.sh` pass `TRACE_USAGE_REPORTING`, `DO_NOT_TRACK` and `TRACE_INSTALL_ID` through to the container, so `TRACE_USAGE_REPORTING=off bash run_server.sh` turns reporting off there. For the same reason a container's installation ID file does not persist either: each run gets a new ID unless `TRACE_INSTALL_ID` is set. The `endpoint` and `key` entries in the settings block select where reports go and the key they are sent with. Each program carries its own copy of the client (`src/trace_client.py`, vendored from [trace-client-python](https://github.com/Stephenson-Software/trace-client-python)) and of the settings handling (`src/usage_reporting.py`), because each is built into its own image from its own directory.

Details: https://github.com/Stephenson-Software/trace#usage-reporting

## Tests
```
python3 -m unittest discover -s tests
```
The suite covers the server's and the client's chat loops against mocked sockets and input (binding and retrying, sending and printing messages, and exiting or listening again on closed input, Ctrl-C or a lost connection), the usage-reporting settings, notice, opt-outs and events for both programs against a loopback stub (it never contacts the real service), the vendored client, and that the client's and the server's copies have not drifted apart.

## Learning Resources
- https://realpython.com/python-sockets/
- https://docs.python.org/3/howto/sockets.html
- https://www.geeksforgeeks.org/socket-programming-python/

## License
This project is licensed under the Stephenson Software Non-Commercial License (Stephenson-NC). See [LICENSE](LICENSE) for the terms, which permit non-commercial use only. The full license text is published at https://github.com/Stephenson-Software/stephenson-nc-license.
