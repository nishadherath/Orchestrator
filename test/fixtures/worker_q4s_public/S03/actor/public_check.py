"""Public smoke test for outgoing header casing."""
import unittest

import h11


class HeaderTest(unittest.TestCase):
    def test_request_preserves_caller_spelling(self):
        connection = h11.Connection(h11.CLIENT)
        data = connection.send(h11.Request(
            method="GET", target="/", headers=[("HoSt", "example.com")]))
        self.assertIn(b"HoSt: example.com\r\n", data)


if __name__ == "__main__":
    unittest.main()
