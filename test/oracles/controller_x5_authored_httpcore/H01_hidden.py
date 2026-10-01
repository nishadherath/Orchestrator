"""Protected second schedule for the authored H01 development case."""

from __future__ import annotations

import unittest

import httpcore
from httpcore._async.connection_pool import AsyncConnectionPool
from httpcore._sync.connection_pool import ConnectionPool, PoolRequest


class IdleConnection:
    def __init__(self, origin, expired=False):
        self.origin = origin
        self.expired = expired
        self.closed = False

    def is_closed(self):
        return self.closed

    def has_expired(self):
        return self.expired

    def is_idle(self):
        return not self.closed

    def can_handle_request(self, origin):
        return self.origin == origin

    def is_available(self):
        return not self.closed


class PendingRequest:
    """Pool queue item without starting an event loop or network I/O."""

    def __init__(self, url):
        self.request = httpcore.Request("GET", url)
        self.connection = None

    def is_queued(self):
        return self.connection is None

    def assign_to_connection(self, connection):
        self.connection = connection


class ProtectedPoolTests(unittest.TestCase):
    def test_surplus_cleanup_preserves_assigned_connection(self):
        first = PoolRequest(httpcore.Request("GET", "https://a.example/"))
        assigned = IdleConnection(first.request.url.origin)
        pool = ConnectionPool(max_connections=2, max_keepalive_connections=1)
        pool._connections = [assigned]
        pool._requests = [first]
        self.assertEqual(pool._assign_requests_to_connections(), [])
        self.assertIs(first.connection, assigned)

        surplus = IdleConnection(httpcore.Request("GET", "https://b.example/").url.origin)
        pool._connections.append(surplus)
        closing = pool._assign_requests_to_connections()
        self.assertNotIn(assigned, closing)
        self.assertIn(assigned, pool._connections)
        self.assertIn(surplus, closing)
        self.assertNotIn(surplus, pool._connections)

    def test_unassigned_expired_connection_is_cleaned_up(self):
        pool = ConnectionPool(max_connections=2, max_keepalive_connections=2)
        stale = IdleConnection(httpcore.Request("GET", "https://a.example/").url.origin,
                               expired=True)
        pool._connections = [stale]
        self.assertEqual(pool._assign_requests_to_connections(), [stale])
        self.assertEqual(pool._connections, [])

    def test_async_pool_keeps_assigned_connection_at_capacity(self):
        first = PendingRequest("https://a.example/")
        original = IdleConnection(first.request.url.origin)
        pool = AsyncConnectionPool(max_connections=1, max_keepalive_connections=1)
        pool._connections = [original]
        pool._requests = [first]
        self.assertEqual(pool._assign_requests_to_connections(), [])
        self.assertIs(first.connection, original)

        second = PendingRequest("https://b.example/")
        pool._requests.append(second)
        closing = pool._assign_requests_to_connections()
        self.assertNotIn(original, closing)
        self.assertIn(original, pool._connections)
        self.assertTrue(second.is_queued())
        self.assertLessEqual(len(pool._connections), 1)


if __name__ == "__main__":
    unittest.main()
