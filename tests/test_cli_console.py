import unittest
from unittest.mock import patch

from mae_captions.cli import _configure_console_encoding_errors


class ReconfigurableStream:
    def __init__(self):
        self.calls = []

    def reconfigure(self, **kwargs):
        self.calls.append(kwargs)


class ConsoleEncodingTests(unittest.TestCase):
    def test_configures_stdout_and_stderr_to_escape_unencodable_text(self):
        stdout = ReconfigurableStream()
        stderr = ReconfigurableStream()

        with (
            patch("mae_captions.cli.sys.stdout", stdout),
            patch("mae_captions.cli.sys.stderr", stderr),
        ):
            _configure_console_encoding_errors()

        self.assertEqual(stdout.calls, [{"errors": "backslashreplace"}])
        self.assertEqual(stderr.calls, [{"errors": "backslashreplace"}])


if __name__ == "__main__":
    unittest.main()
