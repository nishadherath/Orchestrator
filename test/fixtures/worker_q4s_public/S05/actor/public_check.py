"""Public smoke test for zero-cache lookahead."""
import unittest

from more_itertools import seekable


class SeekableTest(unittest.TestCase):
    def test_repeated_peek_keeps_next_value(self):
        stream = seekable(range(3), maxlen=0)
        for _ in range(5):
            self.assertEqual(stream.peek(), 0)
            self.assertTrue(stream)
        self.assertEqual(list(stream), [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
