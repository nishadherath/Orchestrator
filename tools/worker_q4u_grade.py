#!/usr/bin/env python3
"""Grade a stopped Q4U workspace with a sealed evaluator kept outside actors.

The executable score is retained even when public acceptance or a structured
report fails, so useful partial work is visible without claiming completion.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from worker_q4u_contract import build as contract
from worker_q4u_public import ROOT


ORACLES = ROOT / "test/oracles/worker_q4u_public"
IN_PROCESS = {"D01": "D01W.zip", "B02": "B02.zip"}
SHARED = {"F07": "F07.zip", "H08": "H08.zip"}


class Q4UGradeError(ValueError):
    """The candidate or hidden evaluator cannot be trusted for scoring."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def grade(task_id: str, workspace: Path) -> dict:
    """Return a bounded hidden score without copying grader bytes into actor."""
    frozen_contract = contract(task_id)
    task = json.loads((ROOT / "test/fixtures/worker_q4u_public" / task_id /
                       "task.json").read_text(encoding="utf-8"))
    if workspace.is_symlink() or not workspace.is_dir():
        raise Q4UGradeError("candidate workspace is unsafe")
    workspace = workspace.resolve()
    protected = {}
    before = {}
    for relative, expected in task["actor_files"].items():
        path = workspace / relative
        if (path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(workspace)):
            raise Q4UGradeError(f"candidate file is missing or unsafe: {relative}")
        before[relative] = sha(path.read_bytes())
        if relative in frozen_contract["protected_paths"]:
            protected[relative] = expected
            if before[relative] != expected:
                raise Q4UGradeError(f"protected actor source drifted: {relative}")
    prefix = task_id[:3]
    archive_name = IN_PROCESS.get(prefix) or SHARED.get(prefix) or f"{task_id}.zip"
    archive_path = ORACLES / archive_name
    if (archive_path.is_symlink() or not archive_path.is_file()
            or sha(archive_path.read_bytes()) != task["evaluator_zip_sha256"]):
        raise Q4UGradeError("hidden evaluator seal differs")
    with zipfile.ZipFile(archive_path) as archive:
        if "grader.py" not in archive.namelist():
            raise Q4UGradeError("hidden grader is absent")
        grader_bytes = archive.read("grader.py")
        oracle_bytes = archive.read("oracle.json")
    # The private evaluator root is never part of the actor inventory. A
    # minimal environment also excludes provider credentials by default.
    with tempfile.TemporaryDirectory(prefix="q4u-evaluator-") as raw:
        evaluator = Path(raw)
        (evaluator / "grader.py").write_bytes(grader_bytes)
        (evaluator / "oracle.json").write_bytes(oracle_bytes)
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "PYTHONNOUSERSITE": "1", "HOME": str(evaluator)}
        if prefix in IN_PROCESS:
            env["PYTHONPATH"] = str(workspace / "src") if prefix == "D01" else str(workspace)
            command = [sys.executable, "-B", "-S", "-c", grader_bytes.decode("utf-8")]
            cwd = workspace
        else:
            command = [sys.executable, "-B", "-S", str(evaluator / "grader.py"),
                       str(workspace)]
            cwd = evaluator
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                                text=True, timeout=30)
        if result.returncode:
            raise Q4UGradeError(f"hidden grader failed: {task_id}")
        try:
            outcome = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise Q4UGradeError("hidden grader returned invalid JSON") from exc
    if (not isinstance(outcome, dict) or outcome.get("schema_version") != 1
            or type(outcome.get("score")) is not int
            or not 0 <= outcome["score"] <= 100
            or any(sha((workspace / relative).read_bytes()) != value
                   for relative, value in before.items())):
        raise Q4UGradeError("hidden grade or candidate source changed")
    value = {"schema_version": 1, "task_id": task_id,
             "task_sha256": task["task_sha256"],
             "evaluator_zip_sha256": task["evaluator_zip_sha256"],
             "score": outcome["score"], "grader_result": outcome,
             "candidate_sha256": before,
             "provider_calls": 0, "provider_cost_usd": 0}
    return {**value, "grade_sha256": sha(json.dumps(value, sort_keys=True,
                      separators=(",", ":")).encode("utf-8"))}
