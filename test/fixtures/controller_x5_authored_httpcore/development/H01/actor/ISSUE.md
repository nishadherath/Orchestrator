# Assigned HTTP request can stall during concurrent pool activity

Applications using either synchronous or asynchronous calls through the
bundled HTTP client sometimes reach a pool timeout while another request is
waiting to begin I/O. The symptom is easiest to reproduce with two origins
and a one-connection limit. The pool appears to grant the first request a
connection, but subsequent activity changes pool state before it starts using
that connection.

Investigate the supplied `httpcore` source and make the pool preserve an
assigned request's ability to proceed. Keep the connection limit and idle
cleanup behaviour intact. Run `python3 -B public_check.py` from this directory.
The public check covers one deterministic schedule; the evaluator also checks
another cleanup schedule, the asynchronous pool, and ordinary pool lifecycle
behaviour. Modify only `httpcore/_sync/connection_pool.py` and
`httpcore/_async/connection_pool.py`.

This is an authored development adaptation of a published httpcore concurrency
issue, not the original issue report or an independent hidden production task.
