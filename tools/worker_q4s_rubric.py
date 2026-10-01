#!/usr/bin/env python3
"""Prospective Q4S quality-v2 predicate weights for the six public families."""
from __future__ import annotations

from worker_adapter import digest
from worker_q4s_public_catalogue import build
from worker_quality_v2 import validate_rubric


# The first three (or two for S05) predicates are behaviour; the rest are
# invariant checks. This allocation was authored before any Q4S model output.
PREDICATES = {
    "S01": (("class-hook", 20), ("field-hook", 20), ("ordinary-hook", 20), ("double-yield", 20)),
    "S02": (("default-and-override", 25), ("late-spec", 15), ("historic", 20), ("extra-and-falsy", 20)),
    "S03": (("request-raw-case", 20), ("host-first", 20), ("generated-framing", 20), ("header-replacement", 20)),
    "S04": (("list-reduce", 20), ("key-list-reduce", 20), ("dict-reduce", 20), ("set-reduce", 20)),
    "S05": (("bounded-memory", 40), ("lookahead-order", 20), ("empty-default", 20)),
    "S06": (("zwj-type", 20), ("zwnj-type", 20), ("unknown-data", 20), ("valid-context", 20)),
}
CRITICAL = {"S01": "ordinary-hook", "S02": "default-and-override",
            "S03": "generated-framing", "S04": "key-list-reduce",
            "S05": "lookahead-order", "S06": "unknown-data"}


def rubric(task_id: str) -> dict:
    task = build(task_id)
    identity = {"source_task_sha256": task["task_sha256"],
                "public_spec_sha256": task["actor_files"]["ISSUE.md"],
                "quality_contract": "worker-quality-v2"}
    task_sha256 = digest(identity)
    rows = []
    for index, (name, weight) in enumerate(PREDICATES[task_id]):
        category = ("behaviour" if index < (2 if task_id == "S05" else 3)
                    else "invariant")
        rows.append({"id": name, "category": category, "weight": weight,
                     "mandatory": True, "critical": name == CRITICAL[task_id],
                     "comparator": "semantic", "public_obligation": (
                         f"{task_id} issue contract: {name.replace('-', ' ')}"),
                     "public_exact": False})
    rows.extend((
        {"id": "diagnosis", "category": "diagnosis", "weight": 10,
         "mandatory": False, "critical": False, "comparator": "semantic",
         "public_obligation": "Explain the public failure mechanism with observed evidence",
         "public_exact": False},
        {"id": "report", "category": "report", "weight": 10,
         "mandatory": False, "critical": False, "comparator": "semantic",
         "public_obligation": "Truthfully report checks and remaining work",
         "public_exact": False},
    ))
    value = {"schema_version": 2, "task_sha256": task_sha256,
             "public_spec_sha256": task["actor_files"]["ISSUE.md"],
             "predicates": rows}
    return validate_rubric(value)
