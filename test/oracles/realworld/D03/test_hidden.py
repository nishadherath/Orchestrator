import os
import sys
import unittest
from pathlib import Path

ACTOR_ROOT = Path(os.environ["REALWORLD_ACTOR_ROOT"])
sys.path.insert(0, str(ACTOR_ROOT))

from client.retry import ConnectionFailure, Response, request


class Clock:
    def __init__(self, now=0.0):
        self.now = now
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def sender(events, calls, advance=0.0):
    queue = list(events)

    def send(method, key):
        calls.append((method, key))
        event = queue.pop(0)
        if advance:
            advance()
        if isinstance(event, Exception):
            raise event
        return event
    return send


class HiddenRetryTests(unittest.TestCase):
    def test_get_retries_503_and_preserves_delay(self):
        clock, calls = Clock(), []
        result = request("GET", sender([Response(503), Response(200, "ok")], calls),
                         clock=clock, sleep=clock.sleep, deadline=2.0, retry_delay=0.4)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(clock.sleeps, [0.4])
        self.assertEqual(len(calls), 2)

    def test_post_is_not_repeated_without_idempotency_key(self):
        for event in (ConnectionFailure("down"), Response(503)):
            with self.subTest(event=type(event).__name__):
                clock, calls = Clock(), []
                if isinstance(event, Exception):
                    with self.assertRaises(ConnectionFailure):
                        request("POST", sender([event], calls), clock=clock, sleep=clock.sleep,
                                deadline=5.0, retry_delay=0.2)
                else:
                    self.assertEqual(request("POST", sender([event], calls), clock=clock,
                                             sleep=clock.sleep, deadline=5.0,
                                             retry_delay=0.2).status_code, 503)
                self.assertEqual(len(calls), 1)
                self.assertEqual(clock.sleeps, [])

    def test_idempotency_key_allows_write_retry_and_is_forwarded(self):
        clock, calls = Clock(), []
        result = request("POST", sender([Response(503), Response(201)], calls), clock=clock,
                         sleep=clock.sleep, deadline=3.0, retry_delay=0.1,
                         idempotency_key="job-17")
        self.assertEqual(result.status_code, 201)
        self.assertEqual(calls, [("POST", "job-17"), ("POST", "job-17")])

    def test_empty_idempotency_key_does_not_authorise_retry(self):
        clock, calls = Clock(), []
        self.assertEqual(request("POST", sender([Response(503)], calls), clock=clock,
                                 sleep=clock.sleep, deadline=3.0, retry_delay=0.1,
                                 idempotency_key="").status_code, 503)
        self.assertEqual(len(calls), 1)

    def test_deadline_prevents_late_retry(self):
        clock, calls = Clock(now=1.8), []
        response = request("GET", sender([Response(503)], calls), clock=clock,
                           sleep=clock.sleep, deadline=2.0, retry_delay=0.25)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(len(calls), 1)
        self.assertEqual(clock.sleeps, [])

    def test_slow_success_is_not_retried(self):
        clock, calls = Clock(), []

        def advance():
            clock.now += 1.5

        response = request("GET", sender([Response(200, "slow")], calls, advance),
                           clock=clock, sleep=clock.sleep, deadline=2.0, retry_delay=0.1)
        self.assertEqual(response.body, "slow")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
