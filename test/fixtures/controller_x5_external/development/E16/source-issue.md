`_assign_requests_to_connections` assigns an idle connection to a queued request, but the connection stays `IDLE` until the waiting thread wakes up and calls `handle_request`. In between, another thread's pass still sees it as idle and closes it (surplus keep-alive, or "close an idle connection to make room" at `max_connections`). `HTTP11Connection.close` doesn't check the state.

If the request hasn't started yet, `handle_request` raises `ConnectionNotAvailable` and the request is re-queued. If it has, the socket is closed under a request waiting for its response. On Linux the blocked `poll()` isn't woken by the close, so the request hangs until its read timeout.

Seen with the sync pool through httpx and the openai client, 342 threads, `max_connections=100`, `max_keepalive_connections=20`: 2 to 3 requests per run hang for the full read timeout. Instrumenting the pool shows the closed connection was referenced by a `PoolRequest` in `_requests` when the pass decided to close it, and `close` running on an `ACTIVE` connection at the time of each timeout.

httpcore 1.0.9 and master (10a6582). Fix in #1111.
