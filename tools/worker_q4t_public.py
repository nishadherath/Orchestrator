#!/usr/bin/env python3
"""Freeze the Q4T public corpus: five untouched upstream tasks and T07.

The five S tasks retain their Q4S bytes and grading contracts. T07 is an
authored synthetic task, deliberately labelled as such in every result.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from worker_adapter import digest
from worker_q4s_public_catalogue import ROOT, build as upstream_build
from worker_q4s_rubric import rubric as upstream_rubric
from worker_q4s_trigger import build as upstream_triggers
from worker_quality_v2 import validate_rubric


UPSTREAM = ("S01", "S02", "S04", "S05", "S06")
FAMILIES = (*UPSTREAM, "T07")
FIXTURES = ROOT / "test/fixtures/worker_q4t_public"
ORACLES = ROOT / "test/oracles/worker_q4t_public"
EDITABLE = ("eventbox/parser.py", "eventbox/state.py", "eventbox/api.py")
PREDICATES = (("amount-domain", "behaviour", 20),
              ("conflicting-duplicate", "behaviour", 20),
              ("validation-rollback", "behaviour", 20),
              ("overdraft-rollback", "invariant", 20),
              ("diagnosis", "diagnosis", 10), ("report", "report", 10))


class CorpusError(RuntimeError):
    """A prospective Q4T public input differs from its frozen contract."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor_root(task_id: str) -> Path:
    return ((ROOT / "test/fixtures/worker_q4s_public" / task_id / "actor")
            if task_id in UPSTREAM else FIXTURES / "T07/actor")


def oracle_root(task_id: str) -> Path:
    return ROOT / "test/oracles/worker_q4s_public" if task_id in UPSTREAM else ORACLES


def build(task_id: str) -> dict:
    if task_id in UPSTREAM:
        task = upstream_build(task_id)
        frozen = ROOT / "test/fixtures/worker_q4s_public" / task_id / "task.json"
        if json.loads(frozen.read_text(encoding="utf-8")) != task:
            raise CorpusError(f"{task_id}: frozen upstream task changed")
        return task
    if task_id != "T07":
        raise CorpusError(f"unknown Q4T task: {task_id}")
    from worker_q3_public_catalogue import paths

    root = FIXTURES / task_id
    actor = paths(root / "actor")
    reference = paths(root / "reference")
    partial = paths(root / "partial")
    required = {"ISSUE.md", "acceptance.json", "public_check.py",
                "eventbox/__init__.py", *EDITABLE}
    acceptance = json.loads(actor["acceptance.json"].read_text(encoding="utf-8"))
    oracle_file, case_file = "T07.json", "T07_case.py"
    oracle = json.loads((ORACLES / oracle_file).read_text(encoding="utf-8"))
    if (set(actor) != required or set(reference) != set(EDITABLE)
            or set(partial) != set(EDITABLE)
            or acceptance != {"schema_version": 1,
                              "public_command": ["python3", "-B", "public_check.py"],
                              "editable_paths": list(EDITABLE)}
            or oracle.get("schema_version") != 1
            or {row["milestone"] for row in oracle["cases"]}
               != {name for name, category, _ in PREDICATES
                   if category in {"behaviour", "invariant"}}
            or sum(row["weight"] for row in oracle["cases"]) != 100):
        raise CorpusError("T07 actor, overlay or oracle inventory differs")
    value = {"schema_version": 1, "id": task_id,
             "origin": "authored-synthetic-cross-module-atomicity-regression",
             "licence": "project-authored", "editable_paths": list(EDITABLE),
             "actor_files": {name: sha(path) for name, path in actor.items()},
             "reference_files": {name: sha(path) for name, path in reference.items()},
             "partial_files": {name: sha(path) for name, path in partial.items()},
             "oracle_file": oracle_file, "case_file": case_file,
             "oracle_sha256": sha(ORACLES / oracle_file),
             "case_source_sha256": sha(ORACLES / case_file)}
    return {**value, "task_sha256": digest(value)}


def rubric(task_id: str) -> dict:
    if task_id in UPSTREAM:
        return upstream_rubric(task_id)
    task = build(task_id)
    predicates = []
    for name, category, weight in PREDICATES:
        predicates.append({"id": name, "category": category, "weight": weight,
                           "mandatory": category in {"behaviour", "invariant"},
                           "critical": name == "overdraft-rollback",
                           "comparator": "semantic", "public_obligation":
                           f"T07 issue contract: {name.replace('-', ' ')}",
                           "public_exact": False})
    identity = {"source_task_sha256": task["task_sha256"],
                "public_spec_sha256": task["actor_files"]["ISSUE.md"],
                "quality_contract": "worker-quality-v2"}
    return validate_rubric({"schema_version": 2,
                            "task_sha256": digest(identity),
                            "public_spec_sha256": task["actor_files"]["ISSUE.md"],
                            "predicates": predicates})


def triggers() -> dict[str, dict]:
    upstream = {row["task_id"]: row for row in upstream_triggers()["rows"]}
    task = build("T07")
    actor = actor_root("T07")
    issue = (actor / "ISSUE.md").read_text(encoding="utf-8")
    if not all(name in issue for name in EDITABLE):
        raise CorpusError("T07 public issue does not identify three components")
    upstream["T07"] = {
        "task_id": "T07", "triggered": True,
        "mechanism": "Batch validation, ledger idempotency and API publication must agree on atomic commit and rollback.",
        "issue_citation": "test/fixtures/worker_q4t_public/T07/actor/ISSUE.md:3",
        "issue_sha256": task["actor_files"]["ISSUE.md"],
        "modules": list(EDITABLE),
        "source_sha256": {name: task["actor_files"][name] for name in EDITABLE},
    }
    return {task_id: upstream[task_id] for task_id in FAMILIES}
