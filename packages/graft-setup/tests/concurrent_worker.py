"""Run mounted qualification with optional owned filesystem load (no WSL reset)."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--load-workers", type=int, default=0)
    parser.add_argument("--runtime-json", type=Path, required=True)
    parser.add_argument("--unit-only", action="store_true")
    parser.add_argument("--real-only", action="store_true")
    parser.add_argument("--load-interval-ms", type=float, default=1)
    parser.add_argument("--load-seconds", type=float, default=120)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--unit-case")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--isolate-imports", action="store_true")
    args = parser.parse_args()
    if args.unit_only and args.real_only:
        parser.error("Choose unit-only or real-only, not both")
    package = Path(__file__).resolve().parents[1]
    args.parent.mkdir(exist_ok=True, parents=True)
    report = {"platform": sys.platform, "started_unix": time.time(), "parent": str(args.parent.resolve()),
              "load_workers": args.load_workers, "load_interval_ms": args.load_interval_ms, "load_seconds": args.load_seconds,
              "acceptance_deadlines_changed": False, "runs": []}
    env = dict(os.environ, GRAFT_TEST_PARENT=str(args.parent.resolve()), GRAFT_API_KEY="", OPENROUTER_API_KEY="", DO_NOT_TRACK="1")
    trace_directory = args.parent / (args.output.stem + "-traces")
    if args.trace:
        env["GRAFT_TEST_TRACE_DIR"] = str(trace_directory.resolve())
    if args.isolate_imports:
        env["GRAFT_TEST_ISOLATE_IMPORTS"] = "1"
    runtime = json.loads(args.runtime_json.read_text())
    if sys.platform == "linux":
        env["PATH"] = str(Path(runtime["launcher"][0]).parent) + ":/usr/local/bin:/usr/bin:/bin"
    load = None
    native = None
    if args.load_workers:
        load = subprocess.Popen([sys.executable, str(package / "graft-setup/scripts/fs_probe.py"), "--parent", str(args.parent),
                                 "--seconds", str(args.load_seconds), "--workers", str(args.load_workers), "--interval-ms", str(args.load_interval_ms),
                                 "--output", str(args.output.with_suffix(".load.json"))], env=env)
        time.sleep(2)
        if sys.platform == "linux":
            native = subprocess.Popen([sys.executable, str(package / "graft-setup/scripts/fs_probe.py"), "--parent", "/tmp",
                                       "--seconds", str(args.load_seconds), "--workers", "1", "--interval-ms", "10",
                                       "--output", str(args.output.with_suffix(".native.json"))], env=env)
    commands = [("unit", [sys.executable, str(package / "tests/timed_unittest.py")], 300)]
    if args.unit_case:
        commands[0][1].extend(["--case", args.unit_case, "--repeat", str(args.repeat)])
    if args.real_only:
        commands = []
    if not args.unit_only:
        commands.append(("real_graft", [sys.executable, str(package / "tests/integration.py"), "--node", runtime["launcher"][0],
                         "--launcher-json", json.dumps(runtime["launcher"]), "--parent", str(args.parent),
                         "--output", str(args.output.with_suffix(".integration.json"))], 900))
    for name, command, bound in commands:
        started = time.monotonic()
        with args.output.with_suffix("." + name + ".log").open("wb") as log:
            child = subprocess.Popen(command, env=env, stdout=log, stderr=log)
            try:
                code = child.wait(timeout=bound)
                timeout = False
            except subprocess.TimeoutExpired:
                child.kill()
                code = child.wait(timeout=5)
                timeout = True
        entry = {"name": name, "exit_code": code, "timed_out": timeout, "elapsed_seconds": round(time.monotonic() - started, 3)}
        report["runs"].append(entry)
        print(json.dumps(entry), flush=True)
    if load:
        # Let the bounded probe finish and clean its own files, rather than kill
        # it and leave a fixture behind. Host orchestrators must wait before reset.
        try:
            report["load_exit_code"] = load.wait(timeout=180)
        except subprocess.TimeoutExpired:
            load.kill()
            report["load_exit_code"] = load.wait(timeout=5)
            report["load_timeout"] = True
    if native:
        try:
            report["native_exit_code"] = native.wait(timeout=180)
        except subprocess.TimeoutExpired:
            native.kill()
            report["native_exit_code"] = native.wait(timeout=5)
    if args.trace:
        traces = {path.name: path.read_text(encoding="utf-8") for path in trace_directory.glob("*.log")}
        args.output.with_suffix(".trace.json").write_bytes((json.dumps(traces, indent=2) + "\n").encode())
        report["trace_logs"] = len(traces)
    report["ok"] = all(x["exit_code"] == 0 and not x["timed_out"] for x in report["runs"]) and report.get("load_exit_code", 0) == 0
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode())
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
