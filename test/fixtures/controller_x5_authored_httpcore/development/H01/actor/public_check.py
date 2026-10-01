"""Deterministic public schedule and lifecycle controls for the pool bug."""

from __future__ import annotations

import unittest

import httpcore
from httpcore._sync.connection_pool import ConnectionPool, PoolRequest


class IdleConnection:
    def __init__(self, origin):
        self.origin = origin
        self.closed = False

    def is_closed(self):
        return self.closed

    def has_expired(self):
        return False

    def is_idle(self):
        return not self.closed

    def can_handle_request(self, origin):
        return self.origin == origin

    def is_available(self):
        return not self.closed


def request(origin):
    return PoolRequest(httpcore.Request("GET", f"https://{origin}/"))


class PoolAssignmentTests(unittest.TestCase):
    def test_assigned_request_survives_competing_origin(self):
        first = request("a.example")
        original = IdleConnection(first.request.url.origin)
        pool = ConnectionPool(max_connections=1, max_keepalive_connections=1)
        pool._connections = [original]
        pool._requests = [first]
        self.assertEqual(pool._assign_requests_to_connections(), [])
        self.assertIs(first.connection, original)

        second = request("b.example")
        pool._requests.append(second)
        closing = pool._assign_requests_to_connections()
        self.assertNotIn(original, closing)
        self.assertIn(original, pool._connections)
        self.assertIs(first.connection, original)
        self.assertTrue(second.is_queued())
        self.assertLessEqual(len(pool._connections), 1)

        pool._requests.remove(first)
        closing = pool._assign_requests_to_connections()
        self.assertIn(original, closing)
        self.assertIsNotNone(second.connection)
        self.assertIsNot(second.connection, original)
        self.assertLessEqual(len(pool._connections), 1)

    def test_idle_connection_reused_by_same_origin(self):
        first = request("a.example")
        original = IdleConnection(first.request.url.origin)
        pool = ConnectionPool(max_connections=1, max_keepalive_connections=1)
        pool._connections = [original]
        pool._requests = [first]
        self.assertEqual(pool._assign_requests_to_connections(), [])
        self.assertIs(first.connection, original)
        pool._requests.remove(first)
        second = request("a.example")
        pool._requests.append(second)
        self.assertEqual(pool._assign_requests_to_connections(), [])
        self.assertIs(second.connection, original)


if __name__ == "__main__":
    unittest.main()
