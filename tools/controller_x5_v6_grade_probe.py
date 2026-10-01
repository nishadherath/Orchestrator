#!/usr/bin/env python3
"""Provider-free executable X5 v6 grader probe in the WSL actor namespace."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_v6_audit as audit
import controller_x5_v6_grade as grader
sys.path.insert(0, "/opt/orchestrator-worker-runtime")
import worker_wsl_q2_verify as q2


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packages() -> dict:
    result = {}
    for task, (case, _) in grader.CASES.items():
        version = "controller_x5_v6" if task in {"X5-SHIP", "X5-MIGRATE"} else "controller_x5_v4"
        actor = ROOT / "test/fixtures" / version / case / "actor"
        protected = ROOT / "test/oracles" / version / case
        result[task] = {
            "actor_files": {p.name: sha(p) for p in actor.iterdir() if p.is_file()},
            "protected_files": {p.name: sha(p) for p in protected.iterdir() if p.is_file()}}
    return result


def run(task: str) -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("WSL root required")
    case, module = grader.CASES[task]
    version = "controller_x5_v6" if task in {"X5-SHIP", "X5-MIGRATE"} else "controller_x5_v4"
    actor = ROOT / "test/fixtures" / version / case / "actor"
    oracle = json.loads((ROOT / "test/oracles" / version /
                         case / "acceptance.json").read_text(encoding="utf-8"))
    manifest = {"packages": packages()}
    root = Path(tempfile.mkdtemp(prefix="x5-v6-grade-probe-", dir=q2.SEEDS))
    try:
        shutil.copytree(actor, root, dirs_exist_ok=True)
        baseline = grader.grade(task, root, manifest)
        (root / module).write_bytes((ROOT / "test/oracles" / version /
                                     case / module).read_bytes())
        selected = [
            next(row for row in oracle["checks"]
                 if grader.probe_kind(task, row["input"]) == kind)
            for kind in sorted(grader.REQUIRED_KINDS[task])]
        report = {
            "completion_claim": "complete",
            "diagnosis": grader.REFERENCE_REPORT_TEXT[task][0],
            "next_step": grader.REFERENCE_REPORT_TEXT[task][1],
            "probes": [{"input": row["input"], "observed": row["expected"]}
                       for row in selected]}
        (root / "report.json").write_text(json.dumps(report), encoding="utf-8")
        reference = grader.grade(task, root, manifest)
        (root / module).write_text(
            audit.wrong_source(case, (actor / module).read_text(encoding="utf-8")),
            encoding="utf-8")
        wrong = grader.grade(task, root, manifest)
        if baseline["accepted"] or not reference["accepted"] or wrong["accepted"]:
            raise RuntimeError(f"{task}: protected grader discrimination failed")
        return {
            "task": task, "result": "PASS", "provider_calls": 0,
            "baseline": {"accepted": baseline["accepted"],
                         "quality": baseline["quality"],
                         "false_success": baseline["false_success"]},
            "reference": {"accepted": reference["accepted"],
                          "quality": reference["quality"],
                          "false_success": reference["false_success"]},
            "wrong_repair": {"accepted": wrong["accepted"],
                             "quality": wrong["quality"],
                             "false_success": wrong["false_success"]},
            "oracle_read_denied": all(x["oracle_read_denied"]
                                      for x in (baseline, reference, wrong)),
        }
    finally:
        q2.dispose(root, q2.SEEDS)


if __name__ == "__main__":
    task = sys.argv[1]
    print(json.dumps(run(task), sort_keys=True))
