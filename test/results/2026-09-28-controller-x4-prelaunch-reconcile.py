#!/usr/bin/env python3
"""Close the one X4 Controller prelaunch hold after exact evidence checks."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator")
sys.path.insert(0, str(ROOT / "tools"))
from task_executor import TaskExecutor  # noqa: E402

PREPARED = ROOT / "test/results/2026-09-28-controller-x4-wsl-preflight.json"
OUT = ROOT / "test/results/2026-09-28-controller-x4-prelaunch-reconciliation.json"
EXPECTED_ERROR = "acceptance contract digest does not match its content"


def main() -> int:
    if OUT.exists():
        raise RuntimeError("prelaunch reconciliation already recorded")
    prepared = json.loads(PREPARED.read_text(encoding="utf-8"))
    project = Path(prepared["seed"])
    root_id = prepared["root_id"]
    executor = TaskExecutor(project, None)
    state = executor.status(root_id)
    dispatches = list((project / ".claude/controller-dispatch").glob(
        "rtd-*/dispatch-state.json"))
    if len(dispatches) != 1:
        raise RuntimeError("expected exactly one Controller dispatch state")
    dispatch = json.loads(dispatches[0].read_text(encoding="utf-8"))
    result = dispatch.get("controller_result") or {}
    run_dir = Path(result.get("controller_run_dir", ""))
    if (state["state"] != "blocked" or state.get("attempts")
            or dispatch.get("stage") != "blocked"
            or dispatch.get("controller_invocations") != 1
            or result.get("error") != EXPECTED_ERROR
            or result.get("terminal") is not False
            or result.get("cost_usd") is not None
            or run_dir.exists()):
        raise RuntimeError("prelaunch zero-cost evidence is incomplete")
    # system_controller.run_quick freezes the acceptance contract before it
    # creates run_dir or calls runner_factory. This exact error therefore
    # occurs before any Controller child process can exist.
    controller_id = dispatch["invocation_id"]
    follow_on_id = "controller-follow-on-" + dispatch["root_revision_id"][:24]
    budget = executor._budget(root_id)
    before = budget.snapshot()
    rows = before["invocations"]
    if (rows[controller_id]["state"] != "uncertain"
            or rows[follow_on_id]["state"] != "reserved"
            or len(rows) != 3
            or rows[next(key for key in rows if key.startswith(
                "public-assessment-"))]["state"] != "settled"):
        raise RuntimeError("root budget differs from the one prelaunch failure")
    evidence = "x4-prelaunch-freeze-error:no-run-directory:stopped-writer"
    budget.settle(controller_id, 0.0, final=True,
                  telemetry={"status": "not_launched", "provider_calls": 0},
                  evidence=evidence)
    budget.settle(follow_on_id, 0.0, final=True,
                  telemetry={"status": "worker_not_launched", "provider_calls": 0},
                  evidence=evidence)
    after = budget.snapshot()
    if after["unresolved"] or after["spent_usd"] != 0.0340572:
        raise RuntimeError("root billing did not reconcile to the public call")
    receipt = {"schema_version": 1, "root_id": root_id,
               "controller_cost_usd": 0.0, "worker_cost_usd": 0.0,
               "public_assessment_cost_usd": 0.0340572,
               "total_spent_usd": after["spent_usd"],
               "reserved_usd": after["reserved_usd"],
               "unresolved": after["unresolved"],
               "root_state": executor.status(root_id)["state"],
               "evidence": evidence,
               "prelaunch_error": EXPECTED_ERROR,
               "controller_run_dir_absent": True,
               "provider_calls": 1}
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
