#!/usr/bin/env python3
"""Single-use H02 B0 restart after a zero-spend pre-launch Graft failure."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time

import controller_campaign_manifest
import controller_evaluation
import controller_x5_h02_grade
import task_executor
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q4u_adapter import Q4UWslAdapter, isolated_public_runner


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02"
SOURCE = CASE / "actor"
CATALOGUE = CASE / "catalogue-h02.json"
MANIFEST_PATH = ROOT / "test/results/2026-09-30-controller-x5-h02c-producer-manifest.json"
RUN_DIR = ROOT / "test/results/2026-09-30-controller-x5-h02c-producer-run"
SCOPE = "H02 authored development B0 fresh root after two pre-launch repairs: one attempt and protected grade"
MAXIMUM_USD = 4.0


class ProducerStop(RuntimeError):
    """The H02 single-use producer cannot safely advance."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ProducerStop(f"missing or redirected record: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def exclusive(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(body, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def case() -> dict:
    catalogue = load(CATALOGUE)
    body = {key: value for key, value in catalogue.items() if key != "catalogue_sha256"}
    if (catalogue.get("catalogue_sha256")
            != controller_evaluation.digest(body)
            or catalogue.get("case_id") != "H02"
            or len(catalogue.get("editable_paths", [])) != 1):
        raise ProducerStop("H02 frozen catalogue differs")
    if set(controller_x5_h02_grade.inventory(SOURCE)) != set(catalogue["actor_files"]):
        raise ProducerStop("H02 actor file set differs")
    for name, expected in catalogue["actor_files"].items():
        path = SOURCE / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise ProducerStop(f"H02 actor source changed: {name}")
    return catalogue


def freeze() -> dict:
    row = case()
    body = {"schema_version": 1, "stage": "x5-h02c-authored-development-b0",
            "case_id": "H02", "origin": row["origin"],
            "catalogue_sha256": row["catalogue_sha256"],
            "actor_files": row["actor_files"], "editable_paths": row["editable_paths"],
            "oracle_files": row["oracle_files"],
            "grader_sha256": sha(Path(controller_x5_h02_grade.__file__).read_bytes()),
            "schedule": ["B0-only", "S/A-only-if-publicly-eligible-under-new-frozen-manifest"],
            "eligibility_rule": "public state is not accepted; protected score cannot trigger continuation",
            "worker_policy": "one B0 Sonnet-low attempt through Q4U WSL adapter",
            "per_root_maximum_usd": MAXIMUM_USD,
            "maximum_authorised_usd": MAXIMUM_USD,
            "stop_rule": "stop on uncertainty, source drift, replay, invalid identity or budget breach",
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "host": controller_campaign_manifest.host_record(),
            "credential_method": "claude-code-wsl-subscription"}
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def manifest() -> dict:
    saved = load(MANIFEST_PATH)
    if saved != freeze():
        raise ProducerStop("H02 producer manifest or runtime package changed")
    return saved


def gate(row: dict, notice: dict) -> None:
    if (notice.get("approved") is not True
            or notice.get("manifest_sha256") != row["manifest_sha256"]
            or notice.get("maximum_usd") != MAXIMUM_USD
            or notice.get("scope") != SCOPE
            or notice.get("date") != "2026-09-30"
            or not isinstance(notice.get("approval_source"), str)):
        raise ProducerStop("dated cost notice does not authorise H02 producer")


def actor_path(row: dict) -> Path:
    return SEEDS / f"x5-h02c-{row['manifest_sha256'][:16]}-b0"


def root_id(row: dict) -> str:
    return controller_evaluation.digest({"manifest": row["manifest_sha256"],
                                         "case": "H02", "arm": "B0"})[:24]


def task(row: dict) -> dict:
    return {"id": "H02", "actor_files": row["actor_files"],
            "editable_paths": row["editable_paths"]}


def entry(row: dict) -> task_executor.TaskExecutor:
    actor = actor_path(row)
    task_row = task(row)
    return task_executor.TaskExecutor(
        actor, Q4UWslAdapter(task_row),
        command_runner=isolated_public_runner(task_row))


def prepare(row: dict) -> dict:
    CredentialStore().inspect()
    if RUN_DIR.exists() or RUN_DIR.is_symlink() or actor_path(row).exists():
        raise ProducerStop("single-use H02 producer root already exists")
    actor = actor_path(row)
    actor.mkdir(mode=0o700)
    for name in row["actor_files"]:
        path = actor / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((SOURCE / name).read_bytes())
    editable = row["editable_paths"]
    protected = sorted(set(row["actor_files"]) - set(editable))
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only pytest_asyncio/plugin.py may change"],
                "required_outputs": editable, "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = actor / ".claude/h02-acceptance.json"
    contract_path.parent.mkdir(exist_ok=True)
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    rid = root_id(row)
    entry(row).admit(
        goal=(actor / "ISSUE.md").read_text(encoding="utf-8"),
        scope=editable, permissions=["read", "edit"], input_paths=protected,
        acceptance_path=contract_path, budget_usd=MAXIMUM_USD,
        authority_id=controller_evaluation.digest({"root": rid, "grant": "x5-h02c"})[:32],
        actor="x5-authored-development", root_id=rid, task_id="h02c-b0")
    RUN_DIR.mkdir(parents=True)
    exclusive(RUN_DIR / "prepared.json",
              {"manifest_sha256": row["manifest_sha256"],
               "producer_root_id": rid, "provider_calls": 0})
    return {"producer_root_id": rid, "provider_calls": 0}


def verify_actor(row: dict) -> None:
    actor = actor_path(row)
    for name, expected in row["actor_files"].items():
        path = actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise ProducerStop(f"H02 actor changed before paid dispatch: {name}")


def grade_actor(row: dict) -> dict:
    actor = actor_path(row)
    before = {name: sha((actor / name).read_bytes()) for name in row["actor_files"]}
    with tempfile.TemporaryDirectory(prefix="x5-h02c-candidate-", dir=SEEDS) as raw:
        candidate = Path(raw).resolve()
        if not candidate.is_relative_to(SEEDS.resolve()):
            raise ProducerStop("H02 grade copy escaped seed root")
        for name in row["actor_files"]:
            target = candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((actor / name).read_bytes())
        result = controller_x5_h02_grade.grade(candidate)
    if before != {name: sha((actor / name).read_bytes()) for name in row["actor_files"]}:
        raise ProducerStop("H02 actor changed during protected grading")
    return result


def producer(row: dict, notice: dict) -> dict:
    gate(row, notice)
    if load(RUN_DIR / "prepared.json")["manifest_sha256"] != row["manifest_sha256"]:
        raise ProducerStop("H02 prepared root belongs to another manifest")
    executor = entry(row)
    state = executor.status(root_id(row))
    if (state["state"] != "ready" or state["attempts"]
            or state["budget"]["spent_usd"] != 0
            or state["budget"]["unresolved"]
            or state["budget"]["limit_usd"] != MAXIMUM_USD):
        raise ProducerStop("H02 producer root is not fresh and ready")
    verify_actor(row)
    CredentialStore().inspect()
    exclusive(RUN_DIR / "producer-started.json",
              {"manifest_sha256": row["manifest_sha256"],
               "root_id": root_id(row)})
    start = time.monotonic()
    error = None
    try:
        state = executor.run(root_id(row), stop_after_attempts=1)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:400]
        state = executor.status(root_id(row))
    protected = None
    if not state["budget"]["unresolved"] and state["attempts"]:
        try:
            protected = grade_actor(row)
        except Exception as exc:
            error = (error + "; " if error else "") + "protected grade: " + str(exc)[:300]
    qualified = (error is None and protected is not None
                 and not state["budget"]["unresolved"]
                 and not state["budget"]["breached"]
                 and state["budget"]["spent_usd"] <= MAXIMUM_USD)
    eligible = qualified and state["state"] != "accepted"
    result = {"manifest_sha256": row["manifest_sha256"],
              "root_id": root_id(row), "state": state["state"],
              "budget": state["budget"], "attempt_count": len(state["attempts"]),
              "protected_grade": protected, "eligible": eligible,
              "qualified": qualified, "error": error,
              "elapsed_s": round(time.monotonic() - start, 3)}
    exclusive(RUN_DIR / "producer-result.json", result)
    return {"qualified": qualified, "eligible": eligible,
            "state": state["state"], "spent_usd": state["budget"]["spent_usd"],
            "quality": protected["quality"] if protected else None, "error": error}


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise ProducerStop("H02 producer requires WSL root")
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--freeze", action="store_true")
    modes.add_argument("--prepare", action="store_true")
    modes.add_argument("--producer", action="store_true")
    parser.add_argument("--notice", type=Path)
    args = parser.parse_args()
    if args.freeze:
        exclusive(MANIFEST_PATH, freeze())
        result = {"manifest_sha256": load(MANIFEST_PATH)["manifest_sha256"],
                  "provider_calls": 0}
    elif args.prepare:
        result = prepare(manifest())
    else:
        if args.notice is None:
            raise ProducerStop("dated H02 cost notice required")
        result = producer(manifest(), load(args.notice))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
