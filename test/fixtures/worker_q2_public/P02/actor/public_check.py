"""Public smoke checks for the signed token report."""
import unittest

from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from itsdangerous.timed import TimestampSigner


class FixedClockSigner(TimestampSigner):
    now = 100

    def get_timestamp(self):
        return self.now


class TimedTokenRegressionTests(unittest.TestCase):
    def test_compressed_payload_round_trips(self):
        signer = URLSafeTimedSerializer("public-test-key")
        value = {"message": "repeat-" * 100}
        token = signer.dumps(value)
        self.assertTrue(token.startswith("."))
        self.assertEqual(value, signer.loads(token, max_age=60))

    def test_future_timestamp_is_rejected(self):
        signer = FixedClockSigner("public-test-key")
        signer.now = 120
        token = signer.sign(b"payload")
        signer.now = 100
        with self.assertRaises(SignatureExpired):
            signer.unsign(token, max_age=60)


if __name__ == "__main__":
    unittest.main()
