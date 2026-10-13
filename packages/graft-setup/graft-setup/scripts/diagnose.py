"""Inspect Graft identity, graph size and scope; optionally run a bounded check."""
from __future__ import annotations

import time

from graft_common import GraftError, arguments, capabilities, check, failure, graph_summary, launcher, local_path, repo_path, report, startup_review_needed


def main() -> int:
    parser = arguments(__doc__)
    parser.add_argument("--check", action="store_true", help="Re-extract source for structural freshness; can be slow")
    args = parser.parse_args()
    try:
        if args.timeout <= 0:
            raise GraftError("Timeout must be positive.")
        root = repo_path(args.repo)
        cache = local_path(root, args.cache)
        command = launcher(args.launcher_json)
        start = time.monotonic()
        value = {"ok": True, "repo": str(root), "cache": str(cache),
                 "launcher": command, "capabilities": capabilities(command, root, args.timeout),
                 "graph": graph_summary(cache, root), "provider_calls": 0}
        value["mcp_startup_upkeep_review_needed"] = startup_review_needed(root, cache, value["capabilities"]["version"])
        value["ok"] = bool(value["graph"].get("files"))
        if args.check:
            value["freshness"] = check(command, root, cache, args.timeout)
            value["ok"] = value["freshness"]["structural_fresh"]
        value["elapsed_seconds"] = round(time.monotonic() - start, 3)
        report(value, args.output)
        return 0 if value["ok"] else 1
    except (GraftError, OSError) as exc:
        return failure(exc, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
