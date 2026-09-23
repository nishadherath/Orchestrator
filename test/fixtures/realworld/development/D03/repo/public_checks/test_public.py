import unittest

from client.retry import ConnectionFailure, Response, request


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class RetryTests(unittest.TestCase):
    def test_get_retries_connection_failure_with_requested_delay(self):
        events = [ConnectionFailure("offline"), Response(200, "ok")]
        calls = []

        def send(method, key):
            calls.append((method, key))
            event = events.pop(0)
            if isinstance(event, Exception):
                raise event
            return event

        clock = Clock()
        result = request("GET", send, clock=clock, sleep=clock.sleep,
                         deadline=5.0, retry_delay=0.25)
        self.assertEqual(result.body, "ok")
        self.assertEqual(calls, [("GET", None), ("GET", None)])
        self.assertEqual(clock.sleeps, [0.25])


if __name__ == "__main__":
    unittest.main()
