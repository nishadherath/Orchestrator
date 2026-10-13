"""Run one Windows/WSL pair on the existing mount; never change WSL settings."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distro", required=True)
    parser.add_argument("--linux-package", required=True, help="Absolute physical mounted package path in Linux")
    parser.add_argument("--windows-runtime", type=Path, required=True)
    parser.add_argument("--linux-runtime", required=True, help="Linux JSON path containing native Node/CLI launcher")
    parser.add_argument("--windows-parent", type=Path, required=True)
    parser.add_argument("--linux-parent", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--linux-output-directory", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--serial", action="store_true")
    parser.add_argument("--unit-only", action="store_true")
    parser.add_argument("--real-only", action="store_true")
    parser.add_argument("--interval-ms", type=float, default=1)
    parser.add_argument("--load-seconds", type=float, default=120)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--unit-case")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--warm", action="store_true", help="Probe native Python before starting load to separate cold VM startup")
    parser.add_argument("--isolate-imports", action="store_true")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Run this two-host coordinator from Windows with native Python")
    if not args.label.replace("-", "").isalnum() or not 0 <= args.workers <= 16:
        parser.error("Use an alphanumeric/hyphen label and 0..16 workers")
    args.output_directory.mkdir(parents=True, exist_ok=True)
    package = Path(__file__).resolve().parents[1]
    warm = None
    if args.warm:
        before = time.monotonic()
        probe = subprocess.run(["wsl.exe", "-d", args.distro, "--cd", "/", "--exec", "/usr/bin/python3", "--version"], capture_output=True, timeout=90, check=True)
        warm = {"seconds": round(time.monotonic() - before, 3), "output": probe.stdout.decode(errors="replace").strip()}
    extra = ["--load-workers", str(args.workers), "--load-interval-ms", str(args.interval_ms), "--load-seconds", str(args.load_seconds)] + (["--unit-only"] if args.unit_only else []) + (["--real-only"] if args.real_only else []) + (["--trace"] if args.trace else [])
    if args.unit_case:
        extra.extend(["--unit-case", args.unit_case, "--repeat", str(args.repeat)])
    if args.isolate_imports:
        extra.append("--isolate-imports")
    commands = [
        [sys.executable, str(package / "tests/concurrent_worker.py"), "--parent", str(args.windows_parent),
         "--runtime-json", str(args.windows_runtime), "--output", str(args.output_directory / (args.label + "-windows.json")), *extra],
        ["wsl.exe", "-d", args.distro, "--cd", "/", "--exec", "/usr/bin/python3", args.linux_package + "/tests/concurrent_worker.py",
         "--parent", args.linux_parent, "--runtime-json", args.linux_runtime,
         "--output", args.linux_output_directory + "/" + args.label + "-linux.json", *extra]]
    processes = []
    logs = []
    codes = []
    started = time.monotonic()
    try:
        for index, command in enumerate(commands):
            log = (args.output_directory / (args.label + f"-host-{index}.log")).open("wb")
            logs.append(log)
            process = subprocess.Popen(command, stdout=log, stderr=log, stdin=subprocess.DEVNULL)
            processes.append(process)
            if args.serial:
                codes.append(process.wait(timeout=1300))
        if not args.serial:
            codes = [process.wait(timeout=1300) for process in processes]
    finally:
        # Killing a wsl.exe client is not proof Linux children have stopped.
        # On a coordinator timeout, preserve the logs and inspect owned jobs
        # before any reset. This runner never shuts down a distro or shared VM.
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
        for log in logs:
            log.close()
    report = {"commands": commands, "serial": args.serial, "workers_per_host": args.workers,
              "started_unix": time.time() - (time.monotonic() - started), "elapsed_seconds": round(time.monotonic() - started, 3),
              "exit_codes": codes, "ok": codes == [0, 0], "wsl_configuration_changed": False}
    report["warm_probe"] = warm
    (args.output_directory / (args.label + "-pair.json")).write_bytes((json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
