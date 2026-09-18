import os
import sys
import unittest

sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from downloader.streaming import stream_to


class Response:
    def __init__(self, error=None):
        self.closed = False
        self.error = error
        self.reads = 0

    def iter_chunks(self):
        self.reads += 1
        yield b"first"
        self.reads += 1
        if self.error:
            raise self.error
        yield b"second"

    def close(self):
        self.closed = True


class Sink:
    def __init__(self, fail=False):
        self.parts = []
        self.fail = fail

    def write(self, chunk):
        if self.fail:
            raise OSError("disk full")
        self.parts.append(chunk)


class HiddenStreamingTests(unittest.TestCase):
    def test_iterator_failure_closes_and_propagates(self):
        response = Response(RuntimeError("cancelled"))
        with self.assertRaisesRegex(RuntimeError, "cancelled"):
            stream_to(response, Sink())
        self.assertTrue(response.closed)

    def test_sink_failure_does_not_buffer_remaining_input(self):
        response = Response()
        with self.assertRaisesRegex(OSError, "disk full"):
            stream_to(response, Sink(fail=True))
        self.assertTrue(response.closed)
        self.assertEqual(response.reads, 1)


if __name__ == "__main__":
    unittest.main()
