#!/usr/bin/env python3
"""Seal the Q4 provider-free WSL launcher, adapter and report boundary."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "test/results/2026-09-25-worker-q4-wsl-host.json"
SOURCE_FILES = (
    "tools/worker_adapter.py", "tools/worker_quality_v2.py",
    "tools/worker_q4_adapter.py", "tools/worker_wsl_namespace_q4.sh",
    "tools/worker_wsl_q4_adapter.py", "tools/worker_wsl_q4_probe.py",
    "tools/worker_wsl_q4_install.sh", "tools/worker_wsl_q4_attestation.py",
)
RUNTIME_LAUNCHER = "/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace-q4"


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wsl(*args: str, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root", "--", *args],
                          capture_output=True, text=True, timeout=timeout)


def linux_root() -> str:
    result = wsl("wslpath", "-a", ROOT.as_posix(), timeout=30)
    if result.returncode or not result.stdout.strip().startswith("/mnt/"):
        raise RuntimeError("repository path unavailable inside WSL")
    return result.stdout.strip()


def source_hashes() -> dict[str, str]:
    return {name: sha(ROOT / name) for name in SOURCE_FILES}


def runtime_hash() -> str:
    result = wsl("sha256sum", RUNTIME_LAUNCHER, timeout=30)
    parts = result.stdout.split()
    if result.returncode or len(parts) != 2:
        raise RuntimeError("Q4 installed launcher hash unavailable")
    return parts[0]


def validate(value: dict, *, check_host: bool) -> bool:
    try:
        body = {key: item for key, item in value.items() if key != "evidence_sha256"}
        if (value["schema_version"] != 1 or value["result"] != "PASS"
                or value["evidence_sha256"] != hashlib.sha256(canonical(body)).hexdigest()
                or value["source_sha256"] != source_hashes()
                or value["probe"]["result"] != "PASS"
                or value["probe"]["provider_calls"] != 0
                or value["probe"]["provider_cost_usd"] != 0
                or not all(value["probe"]["checks"].values())):
            return False
        if check_host and (value["runtime_launcher_sha256"] != runtime_hash()
                           or value["runtime_launcher_sha256"] != value[
                               "source_sha256"]["tools/worker_wsl_namespace_q4.sh"]):
            return False
        return True
    except (OSError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired):
        return False


def run() -> dict:
    sources = source_hashes()
    installed = runtime_hash()
    if installed != sources["tools/worker_wsl_namespace_q4.sh"]:
        raise RuntimeError("Q4 launcher differs from source; install it again")
    repo = linux_root()
    result = wsl("python3", "-B", f"{repo}/tools/worker_wsl_q4_probe.py",
                 "--repo", repo)
    try:
        probe = json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError("Q4 probe emitted no JSON result") from exc
    if result.returncode or probe.get("result") != "PASS":
        raise RuntimeError(f"Q4 provider-free probe failed: {probe}")
    value = {"schema_version": 1,
             "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "result": "PASS", "source_sha256": sources,
             "runtime_launcher_sha256": installed, "probe": probe,
             "scope": "Q4 provider-free three-cell boundary; no live model qualified"}
    value["evidence_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    if not validate(value, check_host=True):
        raise RuntimeError("Q4 evidence failed self-validation")
    OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            value = json.loads(OUTPUT.read_text(encoding="utf-8"))
            valid = validate(value, check_host=True)
            print("PASS: Q4 host evidence current" if valid else "FAIL: Q4 host evidence stale")
            return 0 if valid else 1
        value = run()
        print(f"PASS: {len(value['probe']['checks'])} Q4 boundary checks; zero provider calls")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        print(f"FAIL: Q4 attestation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
