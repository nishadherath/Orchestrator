import io
import unittest

from downloader.streaming import stream_to


class Response:
    def __init__(self):
        self.closed = False

    def iter_chunks(self):
        yield b"a"
        yield b"b"

    def close(self):
        self.closed = True


class StreamingTests(unittest.TestCase):
    def test_success_streams_and_closes(self):
        response, sink = Response(), io.BytesIO()
        stream_to(response, sink)
        self.assertEqual(sink.getvalue(), b"ab")
        self.assertTrue(response.closed)


if __name__ == "__main__":
    unittest.main()
