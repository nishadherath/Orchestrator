from app import solve

assert solve({"stages": {"parse": {"count": 1, "ms": 10}, "write": {"count": 5, "ms": 3}}, "suspect": "parse"}) == {"bottleneck": "write", "contradicts_suspect": True}
