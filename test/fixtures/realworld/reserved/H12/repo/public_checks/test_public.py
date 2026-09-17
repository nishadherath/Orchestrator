import unittest
from adapter.codec import decode, encode


class CodecTests(unittest.TestCase):
    def test_new_round_trip(self): self.assertEqual(decode(encode("hello")), "hello")


if __name__ == "__main__": unittest.main()
