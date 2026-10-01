#!/usr/bin/env python3
"""Read-only summary of settled H02 S/A root and Controller handoff."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02_pair as pair  # noqa: E402
import task_executor  # noqa: E402
import dispatch_budget  # noqa: E402


row = json.loads(pair.MANIFEST_PATH.read_text(encoding="utf-8"))
out = {}
for arm in ("S", "A"):
    actor = pair.actor_path(row, arm)
    state = task_executor.TaskExecutor(actor, None).status(pair.root_id(row, arm))
    handoffs = list(actor.rglob("worker-handoff.json"))
    dispatches = list(actor.rglob("dispatch-state.json"))
    dispatch_summary = []
    for path in dispatches:
        dispatch = json.loads(path.read_text(encoding="utf-8"))
        controller_result = dispatch.get("controller_result") or {}
        run_dir = Path(controller_result.get("controller_run_dir", "/nonexistent"))
        packet_path = run_dir / "controller-evidence.json"
        packet = json.loads(packet_path.read_text(encoding="utf-8")) if packet_path.is_file() else {}
        budget_path = run_dir / "dispatch-budget.json"
        budget = dispatch_budget.DispatchBudget(budget_path).snapshot() if budget_path.is_file() else {}
        report_path = run_dir / "REPORT.md"
        report = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""
        ledger_path = run_dir / "ledger.jsonl"
        ledger = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()] if ledger_path.is_file() else []
        frames = [record for record in ledger if record.get("type") == "FrameRecord"]
        problems = [record for record in ledger if record.get("type") == "ProblemRecord"]
        rejections_path = run_dir / "rejections.jsonl"
        rejections = [json.loads(line) for line in rejections_path.read_text(encoding="utf-8").splitlines()] if rejections_path.is_file() else []
        calls = []
        for invocation in budget.get("invocations", {}).values():
            telemetry = invocation.get("telemetry") or {}
            calls.append({"cost_usd": invocation.get("cost_usd"),
                          "role": (invocation.get("metadata") or {}).get("role"),
                          "cell": (invocation.get("metadata") or {}).get("cell"),
                          "identity_valid": (telemetry.get("identity") or {}).get("identity_valid"),
                          "tool_use_names": telemetry.get("tool_use_names")})
        dispatch_summary.append({"stage": dispatch.get("stage"),
                                 "controller_run_dir": str(run_dir),
                                 "report_excerpt": report[:2500],
                                 "controller_invocations": dispatch.get("controller_invocations"),
                                 "controller_cost_usd": controller_result.get("cost_usd"),
                                 "packet_outcome": packet.get("outcome"),
                                 "packet_readiness": packet.get("readiness"),
                                 "packet_acceptance_source": packet.get("acceptance_source"),
                                 "problem_acceptance_criteria": problems[0].get("acceptance_criteria") if problems else None,
                                 "frame_acceptance_criteria": frames[0].get("acceptance_criteria") if frames else None,
                                 "rejection_count": len(rejections),
                                 "rejection_reasons": [str(item)[:400] for item in rejections[:3]],
                                 "role_budget_unresolved": budget.get("unresolved"),
                                 "role_budget_breached": budget.get("breached"),
                                 "role_calls": calls})
    out[arm] = {
        "state": state["state"],
        "public_assessment_status": (state.get("public_assessment") or {}).get("status"),
        "controller_admission": {k: (state.get("controller_admission") or {}).get(k)
                                 for k in ("status", "invocation_id", "cost_usd")},
        "routing_effective_action": ((state.get("routing_decision") or {}).get("decision") or {}).get("effective_action"),
        "attempts": [{"verification_status": (a.get("verification") or {}).get("status"),
                      "receipt": {k: (a.get("receipt") or {}).get(k) for k in
                                  ("actual_model", "identity_valid", "terminal",
                                   "writer_stopped", "cost_usd")}}
                     for a in state["attempts"]],
        "handoffs": [{"path": str(path),
                      "data": {k: json.loads(path.read_text(encoding="utf-8")).get(k)
                               for k in ("controller_used", "readiness", "verified_findings",
                                         "rejected_hypotheses", "remaining_uncertainties",
                                         "safe_next_action", "controller_packet_digest")}}
                     for path in handoffs],
        "dispatches": dispatch_summary,
    }
print(json.dumps(out, sort_keys=True, indent=2))
