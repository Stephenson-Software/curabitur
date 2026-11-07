"""Tests for ChatClient's connect loop and chat loop, and for the banner, usage wiring,
CHAT_SERVER_IP check and Ctrl-C handling in its __main__ block. socket.socket and input() are
patched, so nothing here opens a real connection or waits on a terminal."""
import errno
import importlib.util
import io
import os
import runpy
import socket
import subprocess
import sys
import time
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
    input() returning the given values in turn (an exception is raised instead). Pass a mock
    as sockets to record the arguments to socket.socket. Returns what was printed."""
    out = io.StringIO()
    with patch.object(chatClient.socket, "socket", side_effect=sockets), \
         patch("builtins.input", side_effect=inputs), \
         patch.object(chatClient.time, "sleep"), \
         patch.object(chatClient, "reportConnected") as reportConnected, \
         redirect_stdout(out):
        client.connect()
    return out.getvalue(), reportConnected


def _runMain(sockets, inputs, sleep=None, out=None, usageClient=None):
    """Run chatClient.py's __main__ block like _run, with CHAT_SERVER_IP set and usage
    reporting patched out so nothing is sent; startUsageReporting returns usageClient. Pass a
    mock as sleep to record the pause. Returns what was printed; pass out to read it when
    the block exits instead of returning."""
    out = out if out is not None else io.StringIO()
    usage = sys.modules["usage_reporting"]
    with patch.dict(os.environ, {"CHAT_SERVER_IP": "10.0.0.5"}), \
         patch.object(socket, "socket", side_effect=sockets), \
         patch("builtins.input", side_effect=inputs), \
         patch.object(time, "sleep", side_effect=sleep), \
         patch.object(usage, "startUsageReporting", return_value=usageClient), \
         redirect_stdout(out):
        try:
            runpy.run_path(os.path.join(_SRC, "chatClient.py"), run_name="__main__")
        except KeyboardInterrupt:
            # an escaping KeyboardInterrupt would stop the whole unittest run, so fail instead
            raise AssertionError("KeyboardInterrupt escaped the __main__ block") from None
    return out.getvalue()


class TestChatClient(unittest.TestCase):
    def test_dials_the_configured_host_and_port(self):
        sock = MagicMock()
        _run(ChatClient("10.0.0.5", 36578), [sock], [EOFError()])
        sock.connect.assert_called_once_with(("10.0.0.5", 36578))

    def test_dials_over_ipv4_tcp(self):
        factory = MagicMock(return_value=MagicMock())
        _run(ChatClient("host", 1), factory, [EOFError()])
        factory.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)

    def test_reads_a_turn_with_a_single_1024_byte_recv(self):
        sock = MagicMock()
        sock.recv.return_value = b"pong"
        _run(ChatClient("host", 1), [sock], ["ping", EOFError()])
        sock.recv.assert_called_once_with(1024)

    def test_prints_a_blank_line_after_each_reply(self):
        # ended by a disconnect, because "Input closed" starts with a newline of its own
        sock = MagicMock()
        sock.recv.side_effect = [b"pong", b""]
        output, _ = _run(ChatClient("host", 1), [sock], ["ping", "ping"])
        self.assertIn("Server: 'pong'\n\nServer disconnected. Exiting.", output)

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

    def test_a_character_split_across_two_recvs_is_decoded_whole(self):
        # issue #30: "é" is b"\xc3\xa9"; the first chunk ends after its first byte
        message = ("a" * 1023 + "é").encode("utf-8")
        sock = MagicMock()
        sock.recv.side_effect = [message[:1024], message[1024:]]
        output, _ = _run(ChatClient("host", 1), [sock], ["ping", "ping", EOFError()])
        self.assertIn("Server: '" + "a" * 1023 + "'", output)
        self.assertIn("Server: 'é'", output)

    def test_bytes_that_are_not_utf8_are_shown_as_replacement_characters(self):
        sock = MagicMock()
        sock.recv.return_value = b"\xffbad"
        output, _ = _run(ChatClient("host", 1), [sock], ["ping", EOFError()])
        self.assertIn("Server: '�bad'", output)

    def test_a_message_that_is_not_valid_text_is_not_sent_and_the_prompt_is_repeated(self):
        undecodable = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        for bad in (undecodable, "\udcff"):
            with self.subTest(bad=bad):
                sock = MagicMock()
                sock.recv.return_value = b"pong"
                output, _ = _run(ChatClient("host", 1), [sock], [bad, "ping", EOFError()])
                self.assertIn("That line is not valid text. Type it again.", output)
                sock.sendall.assert_called_once_with(b"ping")

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

    def test_pauses_one_second_between_attempts(self):
        refused, good = MagicMock(), MagicMock()
        refused.connect.side_effect = ConnectionRefusedError("refused")
        pause = MagicMock(return_value=None)
        output = _runMain([refused, good], [EOFError()], sleep=pause)
        pause.assert_called_once_with(1)
        self.assertIn("Retrying in 1 second.", output)

    def test_an_empty_message_is_not_sent_and_the_prompt_is_repeated(self):
        # issue #40: sendall(b"") puts nothing on the wire, so both sides would wait forever
        sock = MagicMock()
        sock.recv.return_value = b"pong"
        _run(ChatClient("host", 1), [sock], ["", "", "ping", EOFError()])
        sock.sendall.assert_called_once_with(b"ping")

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

    def test_reset_while_waiting_for_the_reply_reports_the_server_disconnected(self):
        sock = MagicMock()
        sock.recv.side_effect = ConnectionResetError()
        output, _ = _run(ChatClient("host", 1), [sock], ["ping"])
        sock.sendall.assert_called_once_with(b"ping")
        self.assertIn("Server disconnected. Exiting.", output)

    def test_reports_connected_only_when_usage_reporting_is_on(self):
        usage = object()
        _, reportConnected = _run(ChatClient("host", 1, usage), [MagicMock()], [EOFError()])
        reportConnected.assert_called_once_with(usage)
        _, reportConnected = _run(ChatClient("host", 1), [MagicMock()], [EOFError()])
        reportConnected.assert_not_called()

    def test_main_hands_the_usage_client_to_the_chat_client(self):
        # the role tag is not asserted: the tests share one usage_reporting module, which
        # may be the server's copy in a full run
        usageClient = MagicMock()
        _runMain([MagicMock()], [EOFError()], usageClient=usageClient)
        usageClient.report.assert_called_once()
        self.assertEqual(usageClient.report.call_args[0], ("connected",))

    def test_main_prints_the_banner(self):
        self.assertIn(" === Chat Client === ", _runMain([MagicMock()], [EOFError()]))

    def test_exits_1_when_chat_server_ip_is_not_set(self):
        env = {k: v for k, v in os.environ.items() if k != "CHAT_SERVER_IP"}
        # the check runs before usage reporting starts, so nothing is sent or written
        result = subprocess.run([sys.executable, os.path.join(_SRC, "chatClient.py")],
                                env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertIn("CHAT_SERVER_IP environment variable not set. Exiting.", result.stdout)

    def test_exits_1_when_chat_server_ip_is_empty(self):
        # issue #50: connect(("", port)) dials this machine, so an empty value used to retry forever
        # reporting is turned off in case a regression gets past the check and starts it
        env = dict(os.environ, CHAT_SERVER_IP="", TRACE_USAGE_REPORTING="off")
        result = subprocess.run([sys.executable, os.path.join(_SRC, "chatClient.py")],
                                env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertIn("CHAT_SERVER_IP environment variable not set. Exiting.", result.stdout)
        self.assertNotIn("Connecting to", result.stdout)

    def test_exits_1_when_chat_server_ip_cannot_be_resolved(self):
        unresolvable = MagicMock()
        unresolvable.connect.side_effect = socket.gaierror(-2, "Name or service not known")
        out = io.StringIO()
        with self.assertRaises(SystemExit) as exited:
            _runMain([unresolvable], [], out=out)
        self.assertEqual(exited.exception.code, 1)
        self.assertIn("Could not resolve CHAT_SERVER_IP '10.0.0.5': Name or service not known. Exiting.",
                      out.getvalue())
        self.assertNotIn("Retrying", out.getvalue())
        unresolvable.close.assert_called_once_with()

    def test_exits_1_when_the_host_or_network_is_unreachable(self):
        # issue #35: these are plain OSErrors, neither TimeoutError nor ConnectionRefusedError
        for errno_, reason in ((errno.EHOSTUNREACH, "No route to host"),
                               (errno.ENETUNREACH, "Network is unreachable")):
            with self.subTest(reason=reason):
                unreachable = MagicMock()
                unreachable.connect.side_effect = OSError(errno_, reason)
                out = io.StringIO()
                with self.assertRaises(SystemExit) as exited:
                    _runMain([unreachable], [], out=out)
                self.assertEqual(exited.exception.code, 1)
                self.assertIn(f"Connection to 10.0.0.5:36578 failed: {reason}. Exiting.",
                              out.getvalue())
                self.assertNotIn("Retrying", out.getvalue())
                unreachable.close.assert_called_once_with()

    def test_exits_1_when_the_connection_fails_mid_chat(self):
        # an OSError other than a reset is not a disconnect; an OSError without an errno has
        # no strerror, so the message falls back to the error itself
        for error, reason in ((OSError(errno.ETIMEDOUT, "Connection timed out"), "Connection timed out"),
                              (OSError("no errno"), "no errno")):
            with self.subTest(reason=reason):
                sock = MagicMock()
                sock.recv.side_effect = error
                out = io.StringIO()
                with self.assertRaises(SystemExit) as exited:
                    _runMain([sock], ["ping"], out=out)
                self.assertEqual(exited.exception.code, 1)
                self.assertIn(f"Connection to 10.0.0.5:36578 failed: {reason}. Exiting.",
                              out.getvalue())
                sock.__exit__.assert_called_once()

    def test_ctrl_c_while_retrying_exits_cleanly(self):
        refused = MagicMock()
        refused.connect.side_effect = ConnectionRefusedError("refused")
        output = _runMain([refused], [], sleep=KeyboardInterrupt())
        self.assertIn("Interrupted. Exiting.", output)
        refused.close.assert_called_once_with()

    def test_ctrl_c_at_the_prompt_exits_cleanly(self):
        sock = MagicMock()
        output = _runMain([sock], [KeyboardInterrupt()])
        self.assertIn("Interrupted. Exiting.", output)
        sock.connect.assert_called_once_with(("10.0.0.5", 36578))
        sock.__exit__.assert_called_once()

    def test_ctrl_c_while_waiting_for_the_reply_exits_cleanly(self):
        sock = MagicMock()
        sock.recv.side_effect = KeyboardInterrupt()
        output = _runMain([sock], ["ping"])
        self.assertIn("Interrupted. Exiting.", output)
        self.assertNotIn("Server disconnected", output)
        sock.sendall.assert_called_once_with(b"ping")
        sock.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
