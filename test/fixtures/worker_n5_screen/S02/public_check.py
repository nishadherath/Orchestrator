from app import solve

assert solve({"stock": {"a": 2}, "changes": [{"id": "x", "sku": "a", "delta": -1}]}) == {"stock": {"a": 1}, "error": None}
