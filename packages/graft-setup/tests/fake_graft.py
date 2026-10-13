"""Controlled subprocess fixture, not an implementation of Graft."""
import json
import os
import sys
import time
from pathlib import Path

args = sys.argv[1:]
mode = os.environ.get("FAKE_GRAFT_MODE", "")
if mode == "slow":
    time.sleep(3)
if "--version" in args:
    print("0.21.1")
elif "--help" in args:
    print("--only-dir --include-dir --structured --no-gitignore --no-ignore")
elif "build" in args:
    if "--deep" in args:
        raise SystemExit(99)
    if mode == "fail-build":
        raise SystemExit(2)
    root = Path(args[-1])
    cache = Path(args[args.index("--dir") + 1])
    prefixes = [args[i + 1] for i, item in enumerate(args) if item == "--only-dir"]
    paths = []
    if mode != "empty":
        for prefix in prefixes or ["src"]:
            path = root / prefix
            paths.extend(path.rglob("*.py") if path.is_dir() else [path])
    nodes = [{"id": p.relative_to(root).as_posix(), "kind": "file", "path": p.relative_to(root).as_posix(),
              "summary_state": "pending"} for p in paths]
    if mode == "outside-scope":
        nodes[0]["path"] = "fixtures/outside.py"
    (cache / ".graph").mkdir(parents=True, exist_ok=True)
    (cache / ".graph/wiring.json").write_text(json.dumps({"nodes": nodes, "edges": [], "meta": {"languages": ["python"]}}))
    if mode != "no-fingerprint":
        (cache / ".cache").mkdir(exist_ok=True)
        (cache / ".cache/fingerprint.fake.json").write_text(json.dumps({"version": 1, "extractor": "fake",
            "onlyDirs": prefixes, "files": {n["path"]: [] for n in nodes}}))
elif "check" in args:
    stale = mode == "semantic-stale"
    drift = ["src/app.py"] if mode == "structural-stale" else []
    print(json.dumps({"context": {"missing": not stale, "ok": not stale},
        "graph": {"missing": False, "added": drift, "removed": [], "changed": [], "stale": ["old"] if stale else [], "pending": 1}}))
    raise SystemExit(1 if stale or drift else 0)
elif "mcp" in args:
    for line in sys.stdin:
        if mode == "malformed":
            print("not json", flush=True)
            break
        if mode == "closed":
            break
        request = json.loads(line)
        if "id" not in request:
            continue
        if mode == "notifications":
            end = time.monotonic() + 1
            while time.monotonic() < end:
                print(json.dumps({"jsonrpc": "2.0", "method": "notice"}), flush=True)
            continue
        if mode == "stderr":
            sys.stderr.write("x" * 200000)
            sys.stderr.flush()
        print(json.dumps({"jsonrpc": "2.0", "id": request["id"],
                          "result": {"serverInfo": {"name": "graft", "version": "0.21.1"}}}), flush=True)
