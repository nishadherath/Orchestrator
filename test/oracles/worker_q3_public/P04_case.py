"""Root-owned per-case probe; no external sockets are opened."""
import json
import sys

from urllib3 import HTTPConnectionPool, PoolManager, ProxyManager
from urllib3.util import parse_url


def run(row):
    kind = row["kind"]
    if kind == "netloc":
        return parse_url(row["url"]).netloc
    if kind == "pool":
        with PoolManager() as manager:
            return manager.connection_from_host("node.test", row["port"], row["scheme"]).port
    if kind == "proxy":
        with ProxyManager(row["url"]) as manager:
            return manager.proxy.port
    if kind == "same":
        with HTTPConnectionPool("node.test", port=row["port"]) as pool:
            return [pool.is_same_host(url) for url in row["urls"]]
    raise ValueError(kind)


print(json.dumps(run(json.loads(sys.stdin.read())), sort_keys=True))
