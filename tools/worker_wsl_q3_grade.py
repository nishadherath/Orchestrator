#!/usr/bin/env python3
"""Grade one stopped Q3 candidate with Q2's isolated hidden cases.

The candidate overlay is private to this root process. It is never copied
into the paid actor as reference or partial calibration material.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

RUNTIME = Path("/opt/orchestrator-worker-runtime")
sys.path.insert(0, str(RUNTIME))
from worker_wsl_q1 import SEEDS, path_parts  # noqa: E402
from worker_wsl_q2_verify import verify  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grade(repo: Path, workspace: Path, task_id: str, root_state: str) -> dict:
    if os.geteuid() != 0 or task_id not in {"P01", "P02"}:
        raise ValueError("WSL root and a Q3 public task are required")
    if (workspace.is_symlink() or workspace.resolve().parent != SEEDS.resolve()
            or workspace.stat().st_uid != 0 or workspace.stat().st_mode & 0o077):
        raise ValueError("candidate workspace is not a private Q3 seed")
    catalogue = json.loads((repo / "test/fixtures/worker_q2_public/catalogue.json")
                           .read_text(encoding="utf-8"))
    task = next(row for row in catalogue["tasks"] if row["id"] == task_id)
    source = repo / "test/fixtures/worker_q2_public" / task_id / "actor"
    oracle = repo / "test/oracles/worker_q2_public" / f"{task_id}.json"
    if sha(oracle) != task["oracle_sha256"]:
        raise ValueError("hidden oracle differs from frozen catalogue")
    for relative, expected in task["actor_files"].items():
        parts = path_parts(relative)
        if any(workspace.joinpath(*parts[:depth]).is_symlink()
               for depth in range(1, len(parts))):
            raise ValueError("candidate has a symlink parent")
        target = workspace / relative
        if target.is_symlink() or not target.is_file() or target.stat().st_nlink != 1:
            raise ValueError("candidate file is missing or unsafe")
        if relative not in task["editable_paths"] and sha(target) != expected:
            raise ValueError("candidate protected file changed")
    with tempfile.TemporaryDirectory(prefix="q3-grade-", dir=SEEDS) as raw:
        overlay = Path(raw)
        for relative in task["editable_paths"]:
            target = overlay.joinpath(*path_parts(relative))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((workspace / relative).read_bytes())
        before = {name: sha(workspace / name) for name in task["actor_files"]}
        # Q2's 'partial' input mode means exactly two caller-supplied overlay
        # files. This wrapper labels the graded overlay as a Q3 candidate.
        result = verify(task_id, source, overlay, oracle, root_state, "partial")
        after = {name: sha(workspace / name) for name in task["actor_files"]}
        if before != after:
            raise ValueError("candidate changed during hidden grading")
        result["variant"] = "candidate"
        result["candidate_edit_sha256"] = {
            name: before[name] for name in task["editable_paths"]}
        result["source_workspace_unchanged"] = True
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--task-id", choices=("P01", "P02"), required=True)
    parser.add_argument("--root-state", choices=("accepted", "partial", "failed"),
                        required=True)
    args = parser.parse_args()
    try:
        result = grade(args.repo, args.workspace, args.task_id, args.root_state)
    except (OSError, ValueError, RuntimeError, StopIteration) as exc:
        print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
