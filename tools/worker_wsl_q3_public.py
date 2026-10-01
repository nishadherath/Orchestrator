#!/usr/bin/env python3
"""Grade Q3 public multi-file tasks in fresh Q1 actors, with no model calls."""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from worker_adapter import digest
from worker_q3_public_catalogue import FIXTURES, ORACLES, build, sha
from worker_wsl_q2_verify import (UncertainActorError, copy_package, dispose,
                                  run_isolated)
from worker_wsl_q1 import SEEDS, path_parts


class PublicGradeError(RuntimeError):
    """The isolated public task or hidden grader is invalid."""


def frozen(task_id: str) -> dict:
    current = build(task_id)
    recorded = json.loads((FIXTURES / task_id / "task.json").read_text(
        encoding="utf-8"))
    if current != recorded:
        raise PublicGradeError(f"{task_id} source or oracle differs from frozen task")
    return current


def _candidate_overlay(task: dict, workspace: Path, overlay: Path) -> dict[str, str]:
    if (workspace.is_symlink() or workspace.resolve().parent != SEEDS.resolve()
            or workspace.stat().st_uid != 0 or workspace.stat().st_mode & 0o077):
        raise PublicGradeError("candidate workspace is not a private root-owned seed")
    before = {}
    for relative, expected in task["actor_files"].items():
        parts = path_parts(relative)
        if any(workspace.joinpath(*parts[:depth]).is_symlink()
               for depth in range(1, len(parts))):
            raise PublicGradeError(f"candidate has a symlink parent: {relative}")
        source = workspace / relative
        if source.is_symlink() or not source.is_file() or source.stat().st_nlink != 1:
            raise PublicGradeError(f"candidate file is missing or unsafe: {relative}")
        actual = sha(source)
        if relative not in task["editable_paths"] and actual != expected:
            raise PublicGradeError(f"candidate protected file changed: {relative}")
        before[relative] = actual
        if relative in task["editable_paths"]:
            target = overlay.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
    return before


def _grade(task: dict, overlay: Path | None, root_state: str,
           variant: str) -> dict:
    if os.geteuid() != 0 or root_state not in {"accepted", "partial", "failed"}:
        raise PublicGradeError("WSL root and a terminal root state are required")
    task_id = task["id"]
    source = FIXTURES / task_id / "actor"
    oracle_path = ORACLES / task["oracle_file"]
    case_path = ORACLES / task["case_file"]
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    case_code = case_path.read_text(encoding="utf-8")
    if (sha(oracle_path) != task["oracle_sha256"]
            or sha(case_path) != task["case_source_sha256"]):
        raise PublicGradeError("root-owned oracle or hidden case source changed")
    package, manifest_path, manifest = copy_package(source, overlay)
    uncertain = False
    try:
        if ({row["path"]: row["sha256"] for row in manifest["files"]}
                != {**task["actor_files"], **(
                    {} if overlay is None else
                    {name: sha(overlay / name) for name in task["editable_paths"]})}):
            raise PublicGradeError("copied grading package differs from frozen task")
        denial = run_isolated(package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "-c",
             "import sys; from pathlib import Path; "
             "p=Path(sys.argv[1]); "
             "\ntry: p.read_bytes()\nexcept OSError: print('DENIED')\n"
             "else: print('EXPOSED')", str(oracle_path)])
        if denial.returncode or denial.stdout.strip() != "DENIED":
            raise PublicGradeError("hidden oracle is visible from the actor")
        public = run_isolated(package, manifest_path, manifest,
                              ["/usr/bin/python3", "-B", "public_check.py"])
        if public.returncode not in {0, 1}:
            raise PublicGradeError("public check did not terminate normally")
        earned = 0
        cases = []
        critical = False
        for row in oracle["cases"]:
            if (set(row) != {"input", "expected", "weight", "milestone", "critical"}
                    or type(row["weight"]) is not int or row["weight"] <= 0
                    or type(row["critical"]) is not bool
                    or not isinstance(row["milestone"], str)):
                raise PublicGradeError("hidden case schema is invalid")
            result = run_isolated(package, manifest_path, manifest,
                ["/usr/bin/python3", "-B", "-c", case_code],
                json.dumps(row["input"], sort_keys=True))
            if result.returncode:
                raise PublicGradeError(
                    f"hidden case {row['milestone']} did not terminate normally")
            try:
                observed = json.loads(result.stdout.strip())
            except json.JSONDecodeError as exc:
                raise PublicGradeError("hidden case returned invalid JSON") from exc
            passed = observed == row["expected"]
            if passed:
                earned += row["weight"]
            elif row["critical"]:
                critical = True
            cases.append({"milestone": row["milestone"], "passed": passed,
                          "weight": row["weight"]})
        if sha(oracle_path) != task["oracle_sha256"] or sha(case_path) != task["case_source_sha256"]:
            raise PublicGradeError("hidden oracle changed during grading")
        accepted = earned == 100 and public.returncode == 0
        value = {"schema_version": 1, "task_id": task_id, "variant": variant,
                 "root_state": root_state, "public_pass": public.returncode == 0,
                 "hidden_acceptance": accepted, "quality": earned,
                 "critical_error": critical,
                 "false_success": root_state == "accepted" and not accepted,
                 "cases": cases, "oracle_sha256": task["oracle_sha256"],
                 "case_source_sha256": task["case_source_sha256"],
                 "task_sha256": task["task_sha256"],
                 "package_sha256": digest(manifest),
                 "oracle_read_denied": True,
                 "provider_calls": 0, "provider_cost_usd": 0}
        return {**value, "grade_sha256": digest(value)}
    except UncertainActorError:
        uncertain = True
        raise
    finally:
        if not uncertain:
            dispose(package, SEEDS)
            manifest_path.unlink(missing_ok=True)


def grade_variant(task_id: str, variant: str) -> dict:
    task = frozen(task_id)
    if variant not in {"baseline", "reference", "partial", "alternative"}:
        raise PublicGradeError("variant must be baseline, reference, partial or alternative")
    overlay = None if variant == "baseline" else FIXTURES / task_id / variant
    return _grade(task, overlay, "accepted" if variant in {"reference", "alternative"}
                  else "failed",
                  variant)


def grade_candidate(task_id: str, workspace: Path, root_state: str) -> dict:
    task = frozen(task_id)
    with tempfile.TemporaryDirectory(prefix="q3-overlay-", dir=SEEDS) as raw:
        overlay = Path(raw)
        before = _candidate_overlay(task, workspace, overlay)
        result = _grade(task, overlay, root_state, "candidate")
        if any(sha(workspace / name) != value for name, value in before.items()):
            raise PublicGradeError("candidate changed during hidden grading")
        result["candidate_edit_sha256"] = {
            name: before[name] for name in task["editable_paths"]}
        result["source_workspace_unchanged"] = True
        body = {key: value for key, value in result.items() if key != "grade_sha256"}
        result["grade_sha256"] = digest(body)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--variant", choices=["baseline", "reference", "partial",
                                               "alternative"],
                        required=True)
    args = parser.parse_args()
    try:
        result = grade_variant(args.task_id, args.variant)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, PublicGradeError,
            UncertainActorError) as exc:
        print(f"BLOCKED: Q3 public grader: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
