#!/usr/bin/env python3
"""Seal Q3's provider-free WSL proofs against source and installed runtime.

The auth check is deliberately separate from the static boundary verdict:
an expired Claude.ai login cannot turn fake-worker tests into live approval.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import worker_wsl_attestation as n4
import worker_wsl_q1_attestation as q1

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "test/results/2026-09-25-worker-q3-wsl-host.json"
SOURCE_FILES = (
    "tools/worker_wsl_namespace_q3.sh",
    "tools/worker_wsl_q3_auth.py",
    "tools/worker_wsl_q3_probe.py",
    "tools/worker_wsl_q3_auth_probe.py",
    "tools/worker_wsl_q3_adapter.py",
    "tools/worker_wsl_q3_adapter_probe.py",
    "tools/worker_wsl_q3_episode_probe.py",
    "tools/worker_wsl_q3_grade.py",
    "tools/worker_wsl_q3_grade_probe.py",
    "tools/worker_wsl_q3_install.sh",
    "tools/worker_wsl_q3_attestation.py",
)
INSTALLED = {
    "tools/worker_wsl_namespace_q3.sh":
        "/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace-q3",
    "tools/worker_wsl_q3_auth.py":
        "/opt/orchestrator-worker-runtime/worker_wsl_q3_auth.py",
    "tools/worker_wsl_q3_probe.py":
        "/opt/orchestrator-worker-runtime/worker_wsl_q3_probe.py",
}
PROBES = {
    "launcher": "tools/worker_wsl_q3_probe.py",
    "adapter": "tools/worker_wsl_q3_adapter_probe.py",
    "episode": "tools/worker_wsl_q3_episode_probe.py",
    "grader": "tools/worker_wsl_q3_grade_probe.py",
}


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wsl(*args: str, timeout: int = 90) -> subprocess.CompletedProcess:
    return subprocess.run(["wsl.exe", "-u", "root", "--", *args],
                          capture_output=True, text=True, timeout=timeout)


def linux_root() -> str:
    result = wsl("wslpath", "-a", ROOT.as_posix(), timeout=30)
    if result.returncode or not result.stdout.strip().startswith("/mnt/"):
        raise RuntimeError("repository path unavailable inside WSL")
    return result.stdout.strip()


def source_hashes() -> dict[str, str]:
    return {name: sha(ROOT / name) for name in SOURCE_FILES}


def runtime_hashes() -> dict[str, str]:
    result = wsl("sha256sum", *INSTALLED.values(), timeout=45)
    rows = [line.split() for line in result.stdout.splitlines()]
    if result.returncode or len(rows) != len(INSTALLED) or any(len(row) != 2 for row in rows):
        raise RuntimeError("Q3 installed runtime hash inventory unavailable")
    return {name: row[0] for name, row in zip(INSTALLED, rows, strict=True)}


def predecessor_digests() -> dict[str, str]:
    n4_value = json.loads(n4.OUTPUT.read_text(encoding="utf-8"))
    q1_value = json.loads(q1.OUTPUT.read_text(encoding="utf-8"))
    if not n4.validate(n4_value, check_host=True):
        raise RuntimeError("N4 host attestation is stale")
    if not q1.validate(q1_value, check_host=True):
        raise RuntimeError("Q1 host attestation is stale")
    return {"n4": n4_value["evidence_sha256"],
            "q1": q1_value["evidence_sha256"]}


def probe(script: str, repo: str, *, source: bool = False) -> dict:
    argv = ["python3", "-B", f"{repo}/{script}"]
    argv += ["--source", f"{repo}/test/fixtures/worker_q2_public/P01/actor"] \
        if source else ["--repo", repo]
    result = wsl(*argv, timeout=180)
    try:
        report = json.loads(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"Q3 {script} emitted no JSON result") from exc
    if (result.returncode or report.get("result") != "PASS"
            or report.get("provider_calls") != 0
            or report.get("provider_cost_usd") != 0
            or not isinstance(report.get("checks"), dict)
            or not all(report["checks"].values())):
        raise RuntimeError(f"Q3 {script} provider-free probe failed")
    return report


def auth_status(repo: str) -> dict:
    result = wsl("python3", "-B", f"{repo}/tools/worker_wsl_q3_auth_probe.py",
                 "--source", f"{repo}/test/fixtures/worker_q2_public/P01/actor",
                 timeout=60)
    try:
        report = json.loads(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("Q3 auth probe emitted no JSON result") from exc
    if report.get("provider_calls") != 0 or report.get("provider_cost_usd") != 0:
        raise RuntimeError("Q3 auth probe crossed a paid boundary")
    if report.get("result") not in {"PASS", "BLOCKED_AUTH"}:
        raise RuntimeError("Q3 auth probe failed ambiguously")
    if (report["result"] == "PASS") != (result.returncode == 0):
        raise RuntimeError("Q3 auth probe process status disagrees")
    return report


def validate(value: dict, *, check_host: bool, require_auth: bool = False) -> bool:
    try:
        body = {key: item for key, item in value.items() if key != "evidence_sha256"}
        if (value["schema_version"] != 1 or value["result"] != "PASS_STATIC"
                or value["evidence_sha256"] != hashlib.sha256(canonical(body)).hexdigest()
                or value["source_sha256"] != source_hashes()
                or set(value["probes"]) != set(PROBES)
                or any(row.get("result") != "PASS" or row.get("provider_calls") != 0
                       or row.get("provider_cost_usd") != 0
                       or not all(row.get("checks", {}).values())
                       for row in value["probes"].values())
                or value["auth"]["result"] not in {"PASS", "BLOCKED_AUTH"}):
            return False
        if require_auth and value["auth"]["result"] != "PASS":
            return False
        if check_host:
            if (value["runtime_sha256"] != runtime_hashes()
                    or value["predecessor_evidence_sha256"] != predecessor_digests()):
                return False
            if require_auth and auth_status(linux_root())["result"] != "PASS":
                return False
        return True
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired):
        return False


def run() -> dict:
    sources = source_hashes()
    installed = runtime_hashes()
    if any(sources[name] != installed[name] for name in INSTALLED):
        raise RuntimeError("Q3 runtime differs from source; install it again")
    prior = predecessor_digests()
    repo = linux_root()
    probes = {name: probe(path, repo, source=name == "launcher")
              for name, path in PROBES.items()}
    auth = auth_status(repo)
    value = {
        "schema_version": 1,
        "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "result": "PASS_STATIC",
        "source_sha256": sources,
        "runtime_sha256": installed,
        "predecessor_evidence_sha256": prior,
        "probes": probes,
        "auth": auth,
        "scope": "Provider-free Q3 transport and fake B0 episode; no live paid adapter qualified",
    }
    value["evidence_sha256"] = hashlib.sha256(canonical(value)).hexdigest()
    if not validate(value, check_host=True):
        raise RuntimeError("Q3 evidence failed self-validation")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8", newline="\n")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-live", action="store_true")
    args = parser.parse_args()
    try:
        if args.check or args.check_live:
            value = json.loads(OUTPUT.read_text(encoding="utf-8"))
            valid = validate(value, check_host=True, require_auth=args.check_live)
            print("PASS: Q3 host evidence current" if valid else
                  "FAIL: Q3 host evidence stale or live auth unavailable")
            return 0 if valid else 1
        value = run()
        print(f"PASS: {sum(len(row['checks']) for row in value['probes'].values())} "
              f"provider-free Q3 checks; auth {value['auth']['result']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        print(f"FAIL: Q3 attestation: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
