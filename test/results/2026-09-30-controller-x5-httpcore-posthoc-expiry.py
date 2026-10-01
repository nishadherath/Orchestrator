"""Post hoc H01 expiry schedule audit; never alters the frozen H01 grade."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_wsl_q2_verify as q2  # noqa: E402


CASE = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01"
CATALOGUE = CASE / "catalogue-h01.json"
WORKER = q2.SEEDS / "x5-h01-13ca8dd8babee755-b0"
RESULT = ROOT / "test/results/2026-09-30-controller-x5-httpcore-posthoc-expiry.json"
PROBE = r'''
import json
import httpcore
from httpcore._sync.connection_pool import ConnectionPool, PoolRequest
from httpcore._async.connection_pool import AsyncConnectionPool

class Idle:
    def __init__(self, origin, expired=False):
        self.origin = origin
        self.expired = expired
    def is_closed(self): return False
    def has_expired(self): return self.expired
    def is_idle(self): return True
    def can_handle_request(self, origin): return self.origin == origin
    def is_available(self): return True

class Pending:
    def __init__(self, url):
        self.request = httpcore.Request("GET", url)
        self.connection = None
    def is_queued(self): return self.connection is None
    def assign_to_connection(self, connection): self.connection = connection

def check(pool_type, pending_type):
    first = pending_type("https://a.example/")
    connection = Idle(first.request.url.origin)
    pool = pool_type(max_connections=1, max_keepalive_connections=1)
    pool._connections = [connection]
    pool._requests = [first]
    initially_assigned = pool._assign_requests_to_connections() == [] and first.connection is connection
    connection.expired = True
    closing = pool._assign_requests_to_connections()
    return {"initially_assigned": initially_assigned,
            "assigned_retained": connection in pool._connections and connection not in closing}

class SyncPending(PoolRequest):
    def __init__(self, url): super().__init__(httpcore.Request("GET", url))

def ordinary_expiry():
    pool = ConnectionPool(max_connections=1, max_keepalive_connections=1)
    stale = Idle(httpcore.Request("GET", "https://a.example/").url.origin, True)
    pool._connections = [stale]
    closing = pool._assign_requests_to_connections()
    return stale in closing and stale not in pool._connections

print(json.dumps({"sync": check(ConnectionPool, SyncPending),
                  "async": check(AsyncConnectionPool, Pending),
                  "ordinary_expiry": ordinary_expiry()}, sort_keys=True))
'''


def run(source: Path, overlay: Path | None) -> dict:
    package, manifest_path, manifest = q2.copy_package(source, overlay)
    uncertain = False
    try:
        result = q2.run_isolated(package, manifest_path, manifest,
                                 ["/usr/bin/python3", "-B", "-c", PROBE])
        if result.returncode or len(result.stdout) > 4096:
            raise RuntimeError("post hoc isolated probe failed")
        return json.loads(result.stdout)
    except q2.UncertainActorError:
        uncertain = True
        raise
    finally:
        if not uncertain:
            q2.dispose(package, q2.SEEDS)
            manifest_path.unlink(missing_ok=True)


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("post hoc H01 audit requires WSL root")
    rows = []
    for label in ("baseline", "partial", "reference", "alternative"):
        overlay = None if label == "baseline" else CASE / "variants" / label
        rows.append({"variant": label, "observed": run(CASE / "actor", overlay)})
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="x5-h01-posthoc-", dir=q2.SEEDS) as raw:
        copy = Path(raw).resolve()
        if not copy.is_relative_to(q2.SEEDS.resolve()):
            raise RuntimeError("post hoc copy escaped seed root")
        for name in catalogue["actor_files"]:
            target = copy / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(WORKER / name, target)
        rows.append({"variant": "settled_B0", "observed": run(copy, None)})
    expected = {"baseline": False, "partial": False, "reference": True,
                "alternative": True, "settled_B0": False}
    qualified = all(row["observed"]["sync"]["initially_assigned"]
                    and row["observed"]["async"]["initially_assigned"]
                    and row["observed"]["ordinary_expiry"]
                    and row["observed"]["sync"]["assigned_retained"] == expected[row["variant"]]
                    and row["observed"]["async"]["assigned_retained"] == expected[row["variant"]]
                    for row in rows)
    RESULT.write_text(json.dumps({"schema_version": 1, "qualified": qualified,
                                  "status": "post-hoc, outside frozen H01 acceptance",
                                  "rows": rows}, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({"qualified": qualified,
                      "rows": [{"variant": row["variant"],
                                "sync_retained": row["observed"]["sync"]["assigned_retained"],
                                "async_retained": row["observed"]["async"]["assigned_retained"]}
                               for row in rows]}, sort_keys=True))
    if not qualified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
