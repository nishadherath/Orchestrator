#!/usr/bin/env python3
"""Resolve one X4 worker's proved local cap rejection without replay."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator")
sys.path.insert(0, str(ROOT / "tools"))
from task_executor import TaskExecutor  # noqa: E402
from worker_wsl_auth import CredentialStore  # noqa: E402
from worker_wsl_q1 import MANIFESTS  # noqa: E402

LIVE = ROOT / "test/results/2026-09-28-controller-x4-wsl-live-smoke-v2.json"
OUT = ROOT / "test/results/2026-09-28-controller-x4-worker-cap-reconciliation.json"


def main() -> int:
    if os.geteuid() != 0 or OUT.exists():
        raise RuntimeError("root identity and fresh reconciliation path required")
    previous = json.loads(LIVE.read_text(encoding="utf-8"))
    project = Path(previous["seed"])
    root_id = previous["root_id"]
    executor = TaskExecutor(project, None)
    state = executor.status(root_id)
    if state["state"] != "uncertain" or len(state["attempts"]) != 1:
        raise RuntimeError("the root is not the single uncertain worker attempt")
    attempt = state["attempts"][0]
    receipt = attempt.get("receipt") or {}
    invocation = attempt["invocation_id"]
    actor = "q1-" + invocation
    staged = MANIFESTS / (actor + ".json")
    if (receipt.get("returncode") != 64
            or receipt.get("terminal") is not False
            or receipt.get("cost_usd") is not None
            or receipt.get("root_models") != []
            or receipt.get("writer_stopped") is not False
            or attempt["allowance_usd"] <= 6
            or not staged.is_file()):
        raise RuntimeError("local cap rejection evidence is incomplete")
    # The frozen Q3 launcher checks the numeric --max-budget-usd <= 6 before
    # calling q1 start or beginning a credential session. Its completed exit
    # code 64 and this >6 allowance therefore prove no provider invocation.
    CredentialStore().inspect()
    evidence = "x4-q3-launcher-cap-64:allowance-gt-6:pre-start:stopped-writer"
    reconciled = executor.reconcile_uncertain(
        root_id, actor="operator", reason="Q3 worker cap rejected before start",
        cost_usd=0.0, evidence=evidence, writers_stopped=True)
    if (reconciled["state"] != "blocked"
            or reconciled["budget"]["unresolved"]
            or reconciled["budget"]["reserved_usd"] != 0.0):
        raise RuntimeError("worker reconciliation did not close the root")
    result = {"schema_version": 1, "root_id": root_id,
              "worker_cost_usd": 0.0,
              "public_assessment_cost_usd": previous["public_assessment_cost_usd"],
              "controller_cost_usd": 0.272239,
              "total_spent_usd": reconciled["budget"]["spent_usd"],
              "reserved_usd": reconciled["budget"]["reserved_usd"],
              "unresolved": reconciled["budget"]["unresolved"],
              "root_state": reconciled["state"], "evidence": evidence,
              "provider_calls": "public assessment + Controller role calls only"}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
