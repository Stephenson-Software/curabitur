"""Tests for ChatClient's connect loop and chat loop, and for the CHAT_SERVER_IP check in its
__main__ block. socket.socket and input() are patched, so nothing here opens a real
connection or waits on a terminal."""
import importlib.util
import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import MagicMock, patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SRC = os.path.join(_ROOT, "client", "src")
# chatClient imports usage_reporting by bare name from its own directory
sys.path.insert(0, _SRC)

_spec = importlib.util.spec_from_file_location("chatClient", os.path.join(_SRC, "chatClient.py"))
chatClient = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(chatClient)

ChatClient = chatClient.ChatClient


def _run(client, sockets, inputs):
    """Run client.connect() with socket.socket handing out the given mocks in turn and
    input() returning the given values in turn (an exception is raised instead). Returns
    what was printed."""
    out = io.StringIO()
    with patch.object(chatClient.socket, "socket", side_effect=sockets), \
         patch("builtins.input", side_effect=inputs), \
         patch.object(chatClient.time, "sleep"), \
         patch.object(chatClient, "reportConnected") as reportConnected, \
         redirect_stdout(out):
        client.connect()
    return out.getvalue(), reportConnected


class TestChatClient(unittest.TestCase):
    def test_dials_the_configured_host_and_port(self):
        sock = MagicMock()
        _run(ChatClient("10.0.0.5", 36578), [sock], [EOFError()])
        sock.connect.assert_called_once_with(("10.0.0.5", 36578))

    def test_sends_the_utf8_encoding_of_what_was_typed(self):
        sock = MagicMock()
        sock.recv.return_value = b"pong"
        _run(ChatClient("host", 1), [sock], ["héllo", EOFError()])
        sock.sendall.assert_called_once_with("héllo".encode("utf-8"))

    def test_prints_the_reply_as_a_quoted_repr(self):
        # the !r quoting is tracked in issue #8; this asserts the current behavior
        sock = MagicMock()
        sock.recv.return_value = b"pong"
        output, _ = _run(ChatClient("host", 1), [sock], ["ping", EOFError()])
        self.assertIn("Server: 'pong'", output)

    def test_retries_refused_and_timed_out_connects_with_a_fresh_socket(self):
        refused, timedOut, good = MagicMock(), MagicMock(), MagicMock()
        refused.connect.side_effect = ConnectionRefusedError("refused")
        timedOut.connect.side_effect = TimeoutError("timed out")
        output, _ = _run(ChatClient("host", 1), [refused, timedOut, good], [EOFError()])
        refused.close.assert_called_once_with()
        timedOut.close.assert_called_once_with()
        good.connect.assert_called_once_with(("host", 1))
        self.assertIn("Attempts Made: 1", output)
        self.assertIn("Attempts Made: 2", output)

    def test_closed_input_exits_cleanly(self):
        sock = MagicMock()
        output, _ = _run(ChatClient("host", 1), [sock], [EOFError()])
        self.assertIn("Input closed. Exiting.", output)
        sock.sendall.assert_not_called()

    def test_empty_recv_reports_the_server_disconnected(self):
        sock = MagicMock()
        sock.recv.return_value = b""
        output, _ = _run(ChatClient("host", 1), [sock], ["ping"])
        self.assertIn("Server disconnected. Exiting.", output)

    def test_reset_connection_reports_the_server_disconnected(self):
        for error in (ConnectionResetError(), BrokenPipeError()):
            with self.subTest(error=type(error).__name__):
                sock = MagicMock()
                sock.sendall.side_effect = error
                output, _ = _run(ChatClient("host", 1), [sock], ["ping"])
                self.assertIn("Server disconnected. Exiting.", output)

    def test_reports_connected_only_when_usage_reporting_is_on(self):
        usage = object()
        _, reportConnected = _run(ChatClient("host", 1, usage), [MagicMock()], [EOFError()])
        reportConnected.assert_called_once_with(usage)
        _, reportConnected = _run(ChatClient("host", 1), [MagicMock()], [EOFError()])
        reportConnected.assert_not_called()

    def test_exits_1_when_chat_server_ip_is_not_set(self):
        env = {k: v for k, v in os.environ.items() if k != "CHAT_SERVER_IP"}
        # the check runs before usage reporting starts, so nothing is sent or written
        result = subprocess.run([sys.executable, os.path.join(_SRC, "chatClient.py")],
                                env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertIn("CHAT_SERVER_IP environment variable not set. Exiting.", result.stdout)


if __name__ == "__main__":
    unittest.main()
