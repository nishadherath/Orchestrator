#!/usr/bin/env python3
"""Build a Q4U actor's real v1 command contract from its sealed task metadata.

The actor's acceptance.json is descriptive data. A live runner must materialise
this contract in the isolated workspace before TaskExecutor.admit. An
implementation requires a changed output; a correct investigation may stay
untouched and is graded separately for unnecessary edits.
"""
from __future__ import annotations

import json
from pathlib import Path

from worker_q4u_boltons import IDS as B02_IDS, check as check_b02
from worker_q4u_controls import IDS as CONTROL_IDS, check as check_control
from worker_q4u_missing import IDS as MISSING_IDS, check as check_missing
from worker_q4u_f07 import IDS as F07_IDS, check as check_f07
from worker_q4u_h08 import IDS as H08_IDS, check as check_h08
from worker_q4u_reserve import SPECS as RESERVE_IDS, check as check_reserve
from worker_q4u_public import ROOT, TASK_IDS as D01_IDS, check as check_d01


class Q4UContractError(ValueError):
    """A sealed task does not describe a safe command contract."""


def build(task_id: str) -> dict:
    """Validate the fixture and bind its editable and protected actor paths."""
    folder = ROOT / "test/fixtures/worker_q4u_public" / task_id
    if task_id in D01_IDS:
        check_d01(folder / "task.json")
    elif task_id in B02_IDS:
        check_b02(task_id)
    elif task_id in CONTROL_IDS:
        check_control(task_id)
    elif task_id in MISSING_IDS:
        check_missing(task_id)
    elif task_id in F07_IDS:
        check_f07(task_id)
    elif task_id in H08_IDS:
        check_h08(task_id)
    elif task_id in RESERVE_IDS:
        check_reserve(task_id)
    else:
        raise Q4UContractError(f"unknown Q4U task: {task_id}")
    task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
    metadata = json.loads((folder / "actor/acceptance.json").read_text(
        encoding="utf-8"))
    editable = task["editable_paths"]
    actor_paths = set(task["actor_files"])
    change_required = task_id not in CONTROL_IDS and task_id not in MISSING_IDS
    if (metadata != {"schema_version": 1,
                     "public_command": ["python3", "-B", "public_check.py"],
                     "editable_paths": editable,
                     "require_changed_output": change_required}
            or not editable or len(set(editable)) != len(editable)
            or not set(editable) < actor_paths):
        raise Q4UContractError("actor acceptance metadata differs from sealed task")
    return {"version": 1, "kind": "command",
            "criteria": ["The isolated public check passes"],
            "constraints": ["Only declared existing source files may change"],
            "required_outputs": editable,
            "protected_paths": sorted(actor_paths - set(editable)),
            "command": metadata["public_command"], "timeout_s": 30,
            "require_changed_output": change_required}
