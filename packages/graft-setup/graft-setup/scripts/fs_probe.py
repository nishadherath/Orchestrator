"""Bounded, provider-free filesystem latency probe over disposable owned files."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from graft_common import filesystem_info


def distribution(values):
    ordered = sorted(values)
    return {"count": len(ordered), **{name: round(ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))], 6)
            for name, fraction in (("median_seconds", .5), ("p95_seconds", .95), ("p99_seconds", .99), ("max_seconds", 1))}} if ordered else {"count": 0}


def pressure():
    result = {}
    for name in ("cpu", "io", "memory"):
        try:
            result[name] = Path("/proc/pressure", name).read_text()
        except OSError:
            pass
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True, help="Existing approved scratch directory; never a cache/source directory")
    parser.add_argument("--seconds", type=float, default=20)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--interval-ms", type=float, default=10)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (0 < args.seconds <= 300 and 1 <= args.workers <= 16 and 0 <= args.interval_ms <= 1000):
        parser.error("Use 0 < seconds <= 300, 1..16 workers and 0..1000 interval-ms")
    parent = args.parent.resolve(strict=True)
    if not parent.is_dir() or parent == Path(parent.anchor) or parent == Path.home().resolve():
        parser.error("Choose an existing project scratch directory, not home or a filesystem root")
    started = time.monotonic()
    report = {"platform": platform.platform(), "python": sys.version, "parent": str(parent),
              "workers": args.workers, "interval_ms": args.interval_ms, "requested_seconds": args.seconds,
              "started_unix": time.time(), "pressure_before": pressure(), "filesystem": filesystem_info(parent)}

    def worker(number, root):
        directory = root / str(number)
        directory.mkdir()
        files = [directory / (str(i) + ".py") for i in range(16)]
        for file in files:
            file.write_bytes(b"def probe():\n    return 42\n")
        samples = {name: [] for name in ("stat", "read", "resolve", "replace", "unlink")}
        slow = []
        errors = []
        iteration = 0
        while time.monotonic() - started < args.seconds:
            file = files[iteration % len(files)]
            temporary = directory / "replacement.py"
            removed = directory / "removed.py"
            operations = (("stat", file.stat), ("read", file.read_bytes), ("resolve", file.resolve),
                          ("replace", lambda: (temporary.write_bytes(b"def probe():\n    return 42\n"), os.replace(temporary, file))),
                          ("unlink", lambda: (removed.write_bytes(b"probe"), removed.unlink())))
            for name, action in operations:
                before = time.monotonic()
                try:
                    action()
                except OSError as exc:
                    errors.append({"operation": name, "error": str(exc)})
                    return samples, slow, errors
                elapsed = time.monotonic() - before
                samples[name].append(elapsed)
                if elapsed >= .5 and len(slow) < 100:
                    slow.append({"operation": name, "seconds": round(elapsed, 6), "offset_seconds": round(before - started, 6)})
            iteration += 1
            time.sleep(args.interval_ms / 1000)
        return samples, slow, errors

    # TemporaryDirectory removes only files owned by this invocation. No existing
    # project file, cache, mount setting or provider environment is changed.
    with tempfile.TemporaryDirectory(prefix="graft-fs-probe-", dir=parent) as temporary:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(worker, i, Path(temporary)) for i in range(args.workers)]
            startups = []
            while not all(f.done() for f in futures):
                before = time.monotonic()
                try:
                    child = subprocess.run([sys.executable, "-c", "print('ready')"], capture_output=True, timeout=3)
                    startups.append({"seconds": round(time.monotonic() - before, 6), "exit_code": child.returncode})
                except subprocess.TimeoutExpired:
                    startups.append({"seconds": round(time.monotonic() - before, 6), "timeout_seconds": 3})
                time.sleep(.5)
            combined = {name: [] for name in ("stat", "read", "resolve", "replace", "unlink")}
            report["slow_operations"] = []
            report["errors"] = []
            for future in futures:
                samples, slow, errors = future.result()
                for name, values in samples.items():
                    combined[name].extend(values)
                report["slow_operations"].extend(slow)
                report["errors"].extend(errors)
            report["operations"] = {name: distribution(values) for name, values in combined.items()}
            report["child_startups"] = startups
    report["pressure_after"] = pressure()
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["ok"] = not report["errors"] and all(x.get("exit_code") == 0 for x in startups)
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps({"output": str(args.output), "ok": report["ok"], "elapsed_seconds": report["elapsed_seconds"]}))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
