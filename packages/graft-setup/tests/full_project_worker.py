"""Verify an existing full-project graph with optional owned filesystem load."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--cache", required=True, help="Existing repository-relative cache; no rebuild")
    parser.add_argument("--runtime-json", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seconds", type=int, default=300)
    args = parser.parse_args()
    if not 0 <= args.workers <= 16 or not 1 <= args.seconds <= 300:
        parser.error("Use 0..16 workers and 1..300 seconds")
    package = Path(__file__).resolve().parents[1]
    root = args.repo.resolve()
    if not root.is_dir() or root == Path(root.anchor) or root == Path.home().resolve():
        parser.error("Select an existing project root")
    runtime = json.loads(args.runtime_json.read_text(encoding="utf-8"))["launcher"]
    env = dict(os.environ, DO_NOT_TRACK="1", GRAFT_API_KEY="", OPENROUTER_API_KEY="")
    if sys.platform == "linux":
        env["PATH"] = str(Path(runtime[0]).parent) + ":/usr/local/bin:/usr/bin:/bin"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    load = None
    started = time.monotonic()
    with args.output.with_suffix(".load.log").open("wb") as loadlog:
        if args.workers:
            parent = root / ".graft"
            if not parent.is_dir() or parent.is_symlink() or parent.is_junction():
                parser.error("Use an existing, ordinary .graft scratch directory")
            load = subprocess.Popen([sys.executable, str(package / "graft-setup/scripts/fs_probe.py"),
                                     "--parent", str(parent), "--workers", str(args.workers),
                                     "--interval-ms", "1", "--seconds", str(args.seconds),
                                     "--output", str(args.output.with_suffix(".load.json"))],
                                    env=env, stdout=loadlog, stderr=loadlog, stdin=subprocess.DEVNULL)
        command = [sys.executable, str(package / "graft-setup/scripts/trace.py"), "diagnose", "--isolate-imports",
                   "--repo", str(root), "--cache", args.cache, "--check", "--timeout", "180",
                   "--launcher-json", json.dumps(runtime)]
        with args.output.with_suffix(".stdout.json").open("wb") as stdout, args.output.with_suffix(".trace.jsonl").open("wb") as stderr:
            result = subprocess.run(command, env=env, cwd=root, stdout=stdout, stderr=stderr, timeout=350)
        report = {"platform": sys.platform, "started_unix": time.time() - (time.monotonic() - started),
                  "elapsed_seconds": round(time.monotonic() - started, 3), "exit_code": result.returncode,
                  "command_deadline_seconds": 180, "workers": args.workers, "load_seconds": args.seconds,
                  "provider_calls": 0, "cache_rebuilt": False}
        data = json.loads(args.output.with_suffix(".stdout.json").read_text(encoding="utf-8"))
        report.update(ok=result.returncode == 0 and data.get("ok", False), diagnosis=data)
        if load:
            report["load_exit_code"] = load.wait(timeout=350)
            report["load_report"] = json.loads(args.output.with_suffix(".load.json").read_text(encoding="utf-8"))
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode())
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
