#!/usr/bin/env python3
"""Audit disputed public contracts without changing frozen Q3 grades or actors.

The root process copies stopped, hash-bound submissions and evaluates diagnostics
inside fresh Q1 namespaces. This is retrospective sensitivity evidence, never a
replacement grade or an estimate of performance on unseen tasks.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

from worker_adapter import digest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "test/results/2026-09-25-worker-q3-expansion-evidence.json"
OUTPUT = ROOT / "test/results/2026-09-25-worker-q3-contract-audit.json"

# Return observations, not the frozen oracle's exact-wording predicate. Candidate
# imports execute only inside run_isolated, never in the privileged audit process.
PROBES = {
    "P03": '''import json
import click
from click.testing import CliRunner
runner = CliRunner()
@click.group()
def group(): pass
for name in ("declare", "refine", "deploy"):
    group.command(name=name)(lambda: click.echo("ran"))
@click.command()
@click.option("--bound")
@click.option("--count")
def options(bound, count): click.echo(f"{bound}:{count}")
rows = {}
for key, command, args in (
    ("multiple_commands", group, ["decline"]),
    ("multiple_options", options, ["--bounds"]),
    ("valid_command", group, ["declare"]),
    ("valid_options", options, ["--bound", "1", "--count", "2"]),
    ("unrelated", group, ["quartz"]),
):
    result = runner.invoke(command, args)
    rows[key] = {"exit_code": result.exit_code, "output": result.output}
rows["has_NoSuchCommand"] = hasattr(click, "NoSuchCommand")
print(json.dumps(rows, sort_keys=True))
''',
    "P07": '''import json
from packaging.markers import Marker
from packaging.requirements import Requirement
rows = {}
for key, cls, state in (("invalid_marker", Marker, "not valid marker text"),
                         ("invalid_requirement", Requirement, 42)):
    obj = cls.__new__(cls)
    try:
        obj.__setstate__(state)
    except Exception as exc:
        rows[key] = {"rejected": True, "exception": type(exc).__name__,
                     "is_value_error": isinstance(exc, ValueError)}
    else:
        rows[key] = {"rejected": False, "exception": None, "is_value_error": False}
print(json.dumps(rows, sort_keys=True))
''',
}


def assess(task_id: str, observed: dict) -> dict:
    """Interpret narrowly declared probes; do not infer general correctness."""
    if task_id == "P03":
        checks = {}
        for key, expected in (("multiple_commands", ["declare", "refine"]),
                              ("multiple_options", ["--bound", "--count"])):
            row = observed[key]
            # Both observed wording variants express the same sorted suggestion
            # set. Retain exact output in evidence so this judgement is reviewable.
            suggestion = ", ".join(repr(name) for name in expected)
            checks[key] = row["exit_code"] != 0 and any(
                f"Did you mean one of{separator} {suggestion}?" in row["output"]
                for separator in ("", ":"))
        checks["normal_parsing"] = all(observed[key]["exit_code"] == 0
            for key in ("valid_command", "valid_options"))
        checks["unrelated_has_no_hint"] = (
            observed["unrelated"]["exit_code"] != 0
            and "Did you mean" not in observed["unrelated"]["output"])
        return {"checks": checks, "disputed_weight": 45,
                "contract_sensitivity_supported": all(checks.values()),
                "reason": "35 points require punctuation; 10 require an undisclosed exception API"}
    if task_id == "P07":
        checks = {key: observed[key]["rejected"] is True
                  for key in ("invalid_marker", "invalid_requirement")}
        return {"checks": checks, "disputed_weight": 10,
                "contract_sensitivity_supported": all(checks.values()),
                "reason": "public issue requires rejection, not a specific exception class"}
    raise ValueError(f"unsupported audit task: {task_id}")


def run() -> dict:
    """Use root-owned stopped submissions; never invoke a model or edit grades."""
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("the contract audit requires the Q1 WSL root host")
    # Linux-only boundary modules are imported lazily for offline unit tests.
    from worker_q3_public_catalogue import FIXTURES, sha
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q2_verify import (
        UncertainActorError, copy_package, dispose, run_isolated)
    from worker_wsl_q3_public import _candidate_overlay, frozen

    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if evidence.get("status") != "complete" or evidence.get("state_sha256") != digest(
            {key: value for key, value in evidence.items() if key != "state_sha256"}):
        raise RuntimeError("Q3 expansion evidence is incomplete or changed")
    rows = []
    for task_id, code in PROBES.items():
        matches = [row for row in evidence["rows"] if row["task_id"] == task_id]
        if len(matches) != 1 or matches[0]["state"] != "graded":
            raise RuntimeError(f"{task_id}: no unique graded episode")
        episode = matches[0]["episode"]
        task = frozen(task_id)
        grade = episode["hidden_grade"]
        if (grade["task_sha256"] != task["task_sha256"]
                or grade["grade_sha256"] != digest({
                    key: value for key, value in grade.items() if key != "grade_sha256"})
                or not grade["source_workspace_unchanged"]
                or not all(attempt["writer_stopped"] for attempt in episode["attempts"])):
            raise RuntimeError(f"{task_id}: unbound grade or writer still active")
        workspace = Path(episode["workspace"])
        with tempfile.TemporaryDirectory(prefix="q3-audit-overlay-", dir=SEEDS) as raw:
            overlay = Path(raw)
            before = _candidate_overlay(task, workspace, overlay)
            if {name: before[name] for name in task["editable_paths"]} != grade["candidate_edit_sha256"]:
                raise RuntimeError(f"{task_id}: candidate differs from frozen graded revision")
            package, manifest_path, manifest = copy_package(FIXTURES / task_id / "actor", overlay)
            uncertain = False
            try:
                expected = {**task["actor_files"], **grade["candidate_edit_sha256"]}
                if {row["path"]: row["sha256"] for row in manifest["files"]} != expected:
                    raise RuntimeError(f"{task_id}: copied package differs from graded revision")
                result = run_isolated(package, manifest_path, manifest,
                                     ["/usr/bin/python3", "-B", "-c", code])
                if result.returncode:
                    raise RuntimeError(f"{task_id}: diagnostic probe failed: {result.stderr[:500]}")
                observed = json.loads(result.stdout)
                if any(sha(workspace / name) != value for name, value in before.items()):
                    raise RuntimeError(f"{task_id}: stopped source changed during audit")
                rows.append({"task_id": task_id, "task_sha256": task["task_sha256"],
                             "original_grade_sha256": grade["grade_sha256"],
                             "candidate_edit_sha256": grade["candidate_edit_sha256"],
                             "probe_sha256": digest(code), "observed": observed,
                             "assessment": assess(task_id, observed),
                             "frozen_quality": grade["quality"],
                             "frozen_hidden_acceptance": grade["hidden_acceptance"],
                             "source_workspace_unchanged": True})
            except UncertainActorError:
                uncertain = True
                raise
            finally:
                if not uncertain:
                    dispose(package, SEEDS)
                    manifest_path.unlink(missing_ok=True)
    value = {"schema_version": 1, "kind": "retrospective-contract-sensitivity",
             "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "source_evidence_sha256": sha(EVIDENCE), "audit_source_sha256": sha(Path(__file__)),
             "provider_calls": 0, "provider_cost_usd": 0, "rows": rows,
             "frozen_grades_modified": False,
             "result": "PASS" if all(row["assessment"]["contract_sensitivity_supported"]
                                      for row in rows) else "REVIEW"}
    value["audit_sha256"] = digest(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args()
    if OUTPUT.exists():
        raise RuntimeError("preserve existing audit evidence; output already exists")
    value = run()
    # Exclusive creation prevents concurrent audits overwriting the evidence.
    with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print(value["result"], value["audit_sha256"])
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
