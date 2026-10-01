#!/usr/bin/env python3
"""Save provider-free isolated grades for one frozen Q3 public task."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from worker_adapter import digest
from worker_q3_public_catalogue import FIXTURES, ROOT, build, sha

RESULTS = ROOT / "test/results"
SOURCES = (
    "tools/worker_q3_public_calibrate.py",
    "tools/worker_wsl_q3_public.py",
    "tools/worker_q3_public_catalogue.py",
    "tools/worker_wsl_q2_verify.py",
)


class CalibrationError(RuntimeError):
    """A task cannot be accepted as calibrated on this host."""


def linux_root() -> str:
    result = subprocess.run(["wsl.exe", "-d", "kali-linux", "-u", "root",
                             "--", "wslpath", "-a", ROOT.as_posix()],
                            capture_output=True, text=True, timeout=30)
    if result.returncode or not result.stdout.strip().startswith("/mnt/"):
        raise CalibrationError("project path is unavailable inside WSL")
    return result.stdout.strip()


def grade(task_id: str, variant: str, linux: str, task_sha: str) -> dict:
    command = ["wsl.exe", "-d", "kali-linux", "-u", "root", "--",
               "python3", "-B", f"{linux}/tools/worker_wsl_q3_public.py",
               task_id, "--variant", variant]
    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise CalibrationError(f"{task_id} {variant} isolated grade failed: "
                               f"{result.stderr[-300:]}")
    try:
        value = json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise CalibrationError(f"{task_id} {variant} returned invalid JSON") from exc
    body = {key: item for key, item in value.items() if key != "grade_sha256"}
    if (value.get("task_sha256") != task_sha
            or value.get("variant") != variant
            or value.get("grade_sha256") != digest(body)
            or value.get("provider_calls") != 0
            or value.get("provider_cost_usd") != 0
            or not value.get("oracle_read_denied")):
        raise CalibrationError(f"{task_id} {variant} grade is not bound or isolated")
    return value


def run(task_id: str) -> dict:
    task = build(task_id)
    frozen = json.loads((FIXTURES / task_id / "task.json").read_text(
        encoding="utf-8"))
    if frozen != task:
        raise CalibrationError(f"{task_id} task bytes differ from frozen catalogue")
    output = RESULTS / (dt.datetime.now(dt.timezone.utc).date().isoformat()
                        + f"-worker-q3-{task_id.lower()}-"
                        + task["task_sha256"][:12] + "-calibration.json")
    if output.exists():
        raise CalibrationError(f"calibration result already exists: {output}")
    linux = linux_root()
    variants = ["baseline", "partial", "reference"]
    if task["alternative_files"]:
        variants.append("alternative")
    rows = {variant: grade(task_id, variant, linux, task["task_sha256"])
            for variant in variants}
    checks = {
        "baseline_rejected": not rows["baseline"]["hidden_acceptance"],
        "partial_progress": 0 < rows["partial"]["quality"] < 100
                            and not rows["partial"]["hidden_acceptance"],
        "reference_accepted": rows["reference"]["hidden_acceptance"]
                              and rows["reference"]["quality"] == 100,
        "no_critical_or_false_success": all(
            not row["critical_error"] and not row["false_success"]
            for row in rows.values()),
        "alternative_accepted": (rows["alternative"]["hidden_acceptance"]
                                 and rows["alternative"]["quality"] == 100)
                                if "alternative" in rows else False,
    }
    value = {"schema_version": 1, "task_id": task_id,
             "task_sha256": task["task_sha256"],
             "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(
                 timespec="seconds"),
             "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
             "provider_calls": 0, "provider_cost_usd": 0,
             "checks": checks, "grades": rows,
             "result": "PASS" if all(checks.values()) else "PROVISIONAL"}
    value["evidence_sha256"] = digest(value)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    args = parser.parse_args()
    try:
        value = run(args.task_id)
        grades = value["grades"]
        print(f"{value['result']}: {args.task_id} hidden quality "
              f"baseline={grades['baseline']['quality']} "
              f"partial={grades['partial']['quality']} "
              f"reference={grades['reference']['quality']}; "
              f"evidence={value['evidence_sha256']}")
        return 0 if value["result"] == "PASS" else 3
    except (OSError, ValueError, KeyError, TypeError, CalibrationError,
            subprocess.TimeoutExpired) as exc:
        print(f"BLOCKED: Q3 public calibration: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
