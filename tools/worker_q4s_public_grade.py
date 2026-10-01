#!/usr/bin/env python3
"""Provider-free baseline, partial and reference calibration for Q4S."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from worker_adapter import digest
from worker_q4s_public_catalogue import ORACLES, ROOT, build
from worker_q4s_public_source import FIXTURES, SOURCES
from worker_q4s_rubric import rubric


OUTPUT = ROOT / "test/results/2026-09-26-worker-q4s-public-calibration.json"


def run(argv: list[str], directory: Path, *, stdin: str = "") -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(directory), "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(argv, cwd=directory, env=env, input=stdin,
                          capture_output=True, text=True, timeout=30, check=False)


def variant(task_id: str, label: str) -> dict:
    task = build(task_id)
    oracle = json.loads((ORACLES / task["oracle_file"]).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="q4s-grade-") as temporary:
        actor = Path(temporary)
        shutil.copytree(FIXTURES / task_id / "actor", actor, dirs_exist_ok=True)
        if label != "baseline":
            shutil.copytree(FIXTURES / task_id / label, actor, dirs_exist_ok=True)
        public = run([sys.executable, "-B", "public_check.py"], actor)
        cases = []
        for row in oracle["cases"]:
            case = row["input"]["case"]
            result = run([sys.executable, "-B", str(ORACLES / task["case_file"])],
                         actor, stdin=json.dumps(row["input"]))
            try:
                passed = result.returncode == 0 and json.loads(result.stdout) == row["expected"]
            except (ValueError, TypeError):
                passed = False
            cases.append({"milestone": row["milestone"], "passed": passed,
                          "weight": row["weight"], "exit_code": result.returncode})
        return {"variant": label, "public_pass": public.returncode == 0,
                "cases": cases,
                "executable_score": sum(row["weight"] for row in cases if row["passed"]),
                "quality_rubric_sha256": digest(rubric(task_id))}


def build_evidence() -> dict:
    rows = []
    for task_id in SOURCES:
        task = build(task_id)
        grades = [variant(task_id, label) for label in ("baseline", "partial", "reference")]
        scores = [row["executable_score"] for row in grades]
        if (scores[2] != 100 or not scores[0] < scores[1] < scores[2]
                or not grades[2]["public_pass"]):
            raise RuntimeError(f"{task_id}: reference/partial/baseline separation failed")
        rows.append({"task_id": task_id, "task_sha256": task["task_sha256"],
                     "grades": grades})
    value = {"schema_version": 1, "date_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
             "provider_calls": 0, "provider_cost_usd": 0,
             "source_sha256": {
                 name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                 for name in ("tools/worker_q4s_public_catalogue.py",
                              "tools/worker_q4s_public_grade.py",
                              "tools/worker_q4s_rubric.py")},
             "rows": rows}
    return {**value, "evidence_sha256": digest(value)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.prepare == args.check:
        parser.error("choose exactly one of --prepare or --check")
    try:
        value = build_evidence()
        if args.prepare:
            if OUTPUT.exists():
                raise RuntimeError("refusing to overwrite frozen calibration")
            OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")
        elif json.loads(OUTPUT.read_text(encoding="utf-8")) != value:
            raise RuntimeError("calibration differs from frozen evidence")
        print(f"PASS: Q4S six-family calibration {value['evidence_sha256']}")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError,
            subprocess.TimeoutExpired) as error:
        print(f"BLOCKED: Q4S calibration: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
