#!/usr/bin/env python3
"""Reproduce a D01 hidden-grader trust-boundary failure without provider calls.

The probe edits only a disposable copy of an allowed actor file. It demonstrates
that importing candidate code into the grader process lets that code replace
``json.dumps`` and forge the grader's final score. The sealed source and paid
campaign remain untouched.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from worker_q4u_grade import grade
from worker_q4u_public import ROOT


TASK = "D01W"
ACTOR = ROOT / "test/fixtures/worker_q4u_public" / TASK / "actor"
EDITABLE = "src/dotenv/main.py"
PAYLOAD = (
    'import json as _grader_json\n'
    '_grader_json.dumps = lambda *args, **kwargs: '
    '\'{"schema_version":1,"score":100,"cases":{},"weights":{}}\'\n'
)


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="q4u-n7-grader-probe-") as raw:
        workspace = Path(raw) / "actor"
        shutil.copytree(ACTOR, workspace)
        baseline = grade(TASK, workspace)
        baseline_public = subprocess.run(
            [sys.executable, "-B", "public_check.py"], cwd=workspace,
            capture_output=True, timeout=30)
        target = workspace / EDITABLE
        target.write_text(PAYLOAD + target.read_text(encoding="utf-8"),
                          encoding="utf-8")
        attacked = grade(TASK, workspace)
        attacked_public = subprocess.run(
            [sys.executable, "-B", "public_check.py"], cwd=workspace,
            capture_output=True, timeout=30)
    return {"schema_version": 1, "task_id": TASK,
            "baseline_score": baseline["score"],
            "forged_score": attacked["score"],
            "forged_cases": attacked["grader_result"].get("cases"),
            "baseline_public_pass": baseline_public.returncode == 0,
            "forged_public_pass": attacked_public.returncode == 0,
            "sealed_source_mutated": False, "provider_calls": 0,
            "result": "REPRODUCED" if baseline["score"] < 100
            and attacked["score"] == 100
            and attacked["grader_result"].get("cases") == {}
            and baseline_public.returncode == 0
            and attacked_public.returncode == 0
            else "NOT_REPRODUCED"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    arguments = parser.parse_args()
    result = run()
    body = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if arguments.out is not None:
        with arguments.out.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(body)
    print(body, end="")
