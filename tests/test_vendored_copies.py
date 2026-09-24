"""The client and the server are built into separate Docker images from their own
directories, so each carries a copy of the usage-reporting module and the vendored trace
client. The copies must not drift apart."""
import os
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(role, name):
    with open(os.path.join(_ROOT, role, "src", name), "r") as f:
        return f.read()


class TestVendoredCopies(unittest.TestCase):
    def test_trace_client_copies_are_identical(self):
        self.assertEqual(_read("client", "trace_client.py"), _read("server", "trace_client.py"))

    def test_usage_reporting_copies_differ_only_in_role_wording(self):
        client = _read("client", "usage_reporting.py").splitlines()
        server = _read("server", "usage_reporting.py").splitlines()
        self.assertEqual(len(client), len(server))
        differing = [(c, s) for c, s in zip(client, server) if c != s]
        for c, s in differing:
            normalized = (c.replace("client", "ROLE").replace("it connects to a server", "WHEN")
                          .replace("to a server", "WHEN"),
                          s.replace("server", "ROLE").replace("it accepts a client's connection", "WHEN")
                          .replace("a client's connection", "WHEN"))
            self.assertEqual(normalized[0], normalized[1], "copies drifted: %r vs %r" % (c, s))


if __name__ == "__main__":
    unittest.main()
