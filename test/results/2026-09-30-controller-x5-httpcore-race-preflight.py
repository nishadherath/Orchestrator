"""Provider-free state-window probe for an authored httpcore development case.

The published issue #1110 already gives the race diagnosis, so this probe
does not qualify that natural issue as a blind X5 treatment unit.
"""

from __future__ import annotations

import json

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


def probe(kind: str) -> dict:
    first = httpcore.Request("GET", "https://a.example/")
    connection = IdleConnection(first.url.origin)
    pool = ConnectionPool(max_connections=1, max_keepalive_connections=1)
    pool._connections = [connection]
    assigned = PoolRequest(first)
    pool._requests = [assigned]
    initial_closures = pool._assign_requests_to_connections()
    if initial_closures or assigned.connection is not connection:
        raise AssertionError("first queued request was not assigned to idle connection")

    if kind == "surplus_keepalive":
        pool._max_keepalive_connections = 0
    elif kind == "different_origin_at_capacity":
        pool._requests.append(PoolRequest(httpcore.Request("GET", "https://b.example/")))
    else:
        raise ValueError(kind)
    later_closures = pool._assign_requests_to_connections()
    return {
        "kind": kind,
        "assigned_request_still_references_connection": assigned.connection is connection,
        "assigned_connection_selected_for_close": connection in later_closures,
        "selected_close_count": len(later_closures),
    }


if __name__ == "__main__":
    print(json.dumps({"httpcore_version": httpcore.__version__,
                      "cases": [probe("surplus_keepalive"),
                                probe("different_origin_at_capacity")]}, sort_keys=True))
