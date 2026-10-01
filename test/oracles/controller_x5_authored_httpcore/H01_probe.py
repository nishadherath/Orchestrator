"""Emit raw H01 pool observations; the trusted parent owns expectations."""

from __future__ import annotations

import json

import httpcore
from httpcore._async.connection_pool import AsyncConnectionPool
from httpcore._sync.connection_pool import ConnectionPool, PoolRequest


class IdleConnection:
    def __init__(self, origin, *, expired=False):
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
    def __init__(self, url):
        self.request = httpcore.Request("GET", url)
        self.connection = None

    def is_queued(self):
        return self.connection is None

    def assign_to_connection(self, connection):
        self.connection = connection


def sync_surplus():
    first = PoolRequest(httpcore.Request("GET", "https://a.example/"))
    assigned = IdleConnection(first.request.url.origin)
    pool = ConnectionPool(max_connections=2, max_keepalive_connections=1)
    pool._connections = [assigned]
    pool._requests = [first]
    initial = pool._assign_requests_to_connections()
    surplus = IdleConnection(httpcore.Request("GET", "https://b.example/").url.origin)
    pool._connections.append(surplus)
    closing = pool._assign_requests_to_connections()
    return {"initial_assignment": initial == [] and first.connection is assigned,
            "assigned_retained": assigned in pool._connections and assigned not in closing,
            "surplus_selected": surplus in closing and surplus not in pool._connections,
            "pool_count": len(pool._connections)}


def async_competing():
    first = PendingRequest("https://a.example/")
    assigned = IdleConnection(first.request.url.origin)
    pool = AsyncConnectionPool(max_connections=1, max_keepalive_connections=1)
    pool._connections = [assigned]
    pool._requests = [first]
    initial = pool._assign_requests_to_connections()
    second = PendingRequest("https://b.example/")
    pool._requests.append(second)
    closing = pool._assign_requests_to_connections()
    return {"initial_assignment": initial == [] and first.connection is assigned,
            "assigned_retained": assigned in pool._connections and assigned not in closing,
            "second_queued": second.is_queued(),
            "pool_count": len(pool._connections)}


def ordinary_cleanup():
    pool = ConnectionPool(max_connections=2, max_keepalive_connections=2)
    stale = IdleConnection(httpcore.Request("GET", "https://a.example/").url.origin,
                           expired=True)
    pool._connections = [stale]
    closing = pool._assign_requests_to_connections()
    return {"expired_selected": stale in closing,
            "expired_removed": stale not in pool._connections,
            "pool_count": len(pool._connections)}


if __name__ == "__main__":
    print(json.dumps({"sync_surplus": sync_surplus(),
                      "async_competing": async_competing(),
                      "ordinary_cleanup": ordinary_cleanup()}, sort_keys=True))
