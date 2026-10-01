#!/usr/bin/env python3
"""Provider-free T07 calibration; Q4S grades are retained for untouched tasks."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
import tempfile
from pathlib import Path

from worker_adapter import digest
from worker_q4s_public_grade import run
from worker_q4t_public import FIXTURES, ORACLES, ROOT, build, rubric, sha


OUTPUT = ROOT / "test/results/2026-09-26-worker-q4t-public-calibration.json"
SOURCE = "tools/worker_q4t_public_grade.py"


def variant(label: str) -> dict:
    task = build("T07")
    oracle = json.loads((ORACLES / task["oracle_file"]).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="q4t-t07-grade-") as temporary:
        actor = Path(temporary)
        shutil.copytree(FIXTURES / "T07/actor", actor, dirs_exist_ok=True)
        if label != "baseline":
            shutil.copytree(FIXTURES / "T07" / label, actor, dirs_exist_ok=True)
        public = run([sys.executable, "-B", "public_check.py"], actor)
        cases = []
        for row in oracle["cases"]:
            result = run([sys.executable, "-B", str(ORACLES / task["case_file"])],
                         actor, stdin=json.dumps(row["input"]))
            try:
                passed = result.returncode == 0 and json.loads(result.stdout) == row["expected"]
            except (ValueError, TypeError):
                passed = False
            cases.append({"milestone": row["milestone"], "passed": passed,
                          "weight": row["weight"], "exit_code": result.returncode})
        return {"variant": label, "public_pass": public.returncode == 0,
                "cases": cases, "executable_score": sum(
                    row["weight"] for row in cases if row["passed"]),
                "quality_rubric_sha256": digest(rubric("T07"))}


def build_evidence() -> dict:
    task = build("T07")
    grades = [variant(label) for label in ("baseline", "partial", "reference")]
    scores = [row["executable_score"] for row in grades]
    if (not scores[0] < scores[1] < scores[2] or scores[2] != 100
            or grades[0]["public_pass"] or not grades[2]["public_pass"]):
        raise RuntimeError(f"T07 calibration separation failed: {scores}")
    value = {"schema_version": 1,
             "date_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
             "provider_calls": 0, "provider_cost_usd": 0,
             "source_sha256": {name: sha(ROOT / name) for name in
                               (SOURCE, "tools/worker_q4t_public.py")},
             "task_id": "T07", "task_sha256": task["task_sha256"],
             "grades": grades}
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
            if OUTPUT.exists() or OUTPUT.is_symlink():
                raise RuntimeError("refusing to overwrite T07 calibration")
            OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")
        elif json.loads(OUTPUT.read_text(encoding="utf-8")) != value:
            raise RuntimeError("T07 calibration differs from frozen evidence")
        print(f"PASS: T07 calibration {value['evidence_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f"BLOCKED: T07 calibration: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
