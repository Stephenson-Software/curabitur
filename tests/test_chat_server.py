"""Tests for ChatServer's accept loop and chat loop. socket.socket and input() are patched,
so nothing here binds a real port or waits on a terminal."""
import importlib.util
import io
import os
import re
import socket
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "server", "src")
# chatServer imports usage_reporting by bare name from its own directory
sys.path.insert(0, _SRC)

_spec = importlib.util.spec_from_file_location("chatServer", os.path.join(_SRC, "chatServer.py"))
chatServer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chatServer)

ChatServer = chatServer.ChatServer


class _StopListening(Exception):
    """Raised by a listening socket's accept() to end the server's outer loop."""


def _listeningSocket(received=None):
    """A mock listening socket. With received, accept() hands out a connection whose recv()
    returns those chunks in turn; without it, accept() raises _StopListening."""
    sock = MagicMock()
    sock.__enter__.return_value = sock
    if received is None:
        sock.accept.side_effect = _StopListening()
        return sock, None
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.recv.side_effect = received
    sock.accept.return_value = (connection, ("10.0.0.9", 50000))
    return sock, connection


def _run(server, sockets, inputs):
    """Run server.listen() with socket.socket handing out the given mocks in turn and input()
    returning the given values in turn (an exception is raised instead). Returns what was
    printed."""
    out = io.StringIO()
    with patch.object(chatServer.socket, "socket", side_effect=sockets), \
         patch("builtins.input", side_effect=inputs), \
         patch.object(chatServer, "reportConnected") as reportConnected, \
         redirect_stdout(out):
        try:
            server.listen()
        except _StopListening:
            pass
    return out.getvalue(), reportConnected


class TestChatServer(unittest.TestCase):
    def test_binds_the_configured_host_and_port_with_reuseaddr(self):
        sock, _ = _listeningSocket()
        _run(ChatServer("10.0.0.5", 36578), [sock], [])
        sock.setsockopt.assert_called_once_with(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind.assert_called_once_with(("10.0.0.5", 36578))
        sock.listen.assert_called_once_with()

    def test_prints_the_message_as_a_quoted_repr_and_sends_the_utf8_reply(self):
        # the !r quoting is tracked in issue #8; this asserts the current behavior
        sock, connection = _listeningSocket([b"ping", b""])
        after, _ = _listeningSocket()
        output, _ = _run(ChatServer("host", 1), [sock, after], ["pöng"])
        self.assertIn("Accepted connection from ('10.0.0.9', 50000)", output)
        self.assertIn("Client: 'ping'", output)
        connection.sendall.assert_called_once_with("pöng".encode("utf-8"))

    def test_closed_input_exits_cleanly(self):
        sock, connection = _listeningSocket([b"ping"])
        output, _ = _run(ChatServer("host", 1), [sock], [EOFError()])
        self.assertIn("Input closed. Exiting.", output)
        connection.sendall.assert_not_called()

    def test_listens_again_after_the_client_disconnects(self):
        first, _ = _listeningSocket([b""])
        second, _ = _listeningSocket()
        output, _ = _run(ChatServer("host", 1), [first, second], [])
        second.bind.assert_called_once_with(("host", 1))
        self.assertEqual(output.count("Listening on host:1..."), 2)

    def test_reports_connected_only_when_usage_reporting_is_on(self):
        usage = object()
        sock, _ = _listeningSocket([b"ping"])
        _, reportConnected = _run(ChatServer("host", 1, usage), [sock], [EOFError()])
        reportConnected.assert_called_once_with(usage)
        sock, _ = _listeningSocket([b"ping"])
        _, reportConnected = _run(ChatServer("host", 1), [sock], [EOFError()])
        reportConnected.assert_not_called()

    def test_server_and_client_use_the_same_port(self):
        ports = []
        for role, name in (("server", "chatServer.py"), ("client", "chatClient.py")):
            with open(os.path.join(_ROOT, role, "src", name), "r") as f:
                ports.append(re.findall(r"^\s*port = (\d+)$", f.read(), re.MULTILINE))
        self.assertEqual(ports, [["36578"], ["36578"]])


if __name__ == "__main__":
    unittest.main()
