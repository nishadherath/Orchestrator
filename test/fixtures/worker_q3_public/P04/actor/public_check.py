"""Offline, actor-visible checks for the explicit port contract."""
from urllib3 import HTTPConnectionPool, PoolManager, ProxyManager
from urllib3.util import parse_url


def main() -> None:
    assert parse_url("http://example.test:0/a").netloc == "example.test:0"
    with PoolManager() as manager:
        assert manager.connection_from_host("example.test", 0, "http").port == 0
        assert manager.connection_from_host("example.test", None, "http").port == 80
    with HTTPConnectionPool("example.test", port=0) as pool:
        assert pool.is_same_host("http://example.test:0/")
        assert not pool.is_same_host("http://example.test/")
    with ProxyManager("http://proxy.test:0") as manager:
        assert manager.proxy.port == 0


if __name__ == "__main__":
    main()
