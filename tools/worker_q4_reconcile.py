#!/usr/bin/env python3
"""Seal a known terminal M3 failure without replaying its paid invocation."""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
from pathlib import Path


def run(repo: Path, sequence: int) -> dict:
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("M3 reconciliation requires WSL root")
    sys.path.insert(0, str(repo / "tools"))
    import dispatch_budget
    import model_registry
    import worker_q4_screen as plan
    import worker_q4_screen_live as live
    from task_executor import _read
    from worker_adapter import digest
    from worker_q3_public_catalogue import build, sha
    from worker_wsl_q1 import SEEDS

    if sequence != 3:
        raise RuntimeError("only the stopped sequence 3 is eligible")
    manifest = json.loads(plan.MANIFEST.read_text(encoding="utf-8"))
    campaign_path = live.RUN / "campaign.json"
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    if (campaign.get("state_sha256") != digest({
            key: value for key, value in campaign.items() if key != "state_sha256"})
            or campaign.get("status") != "blocked"
            or campaign.get("stop_reason") != "uncertain episode"
            or len(campaign.get("rows", [])) != 3
            or campaign["rows"][-1].get("sequence") != sequence
            or campaign["rows"][-1].get("state") != "uncertain"):
        raise RuntimeError("predecessor campaign is not the exact blocked checkpoint")
    row = next(item for item in manifest["rows"] if item["sequence"] == sequence)
    workspace = SEEDS / f"q4-m3-{manifest['manifest_sha256'][:12]}-{sequence:02d}"
    root_id = digest({"manifest": manifest["manifest_sha256"],
                      "sequence": sequence})[:24]
    root_path = workspace / ".claude/task-executor-v2" / root_id / "root.json"
    root_record_digest = json.loads(root_path.read_text(
        encoding="utf-8"))["record_digest"]
    root = _read(root_path)
    budget = dispatch_budget.DispatchBudget(root_path.parent / "budget.json",
                                            scope="task_dispatch").snapshot()
    if (root.get("state") != "blocked" or len(root.get("attempts", [])) != 1
            or budget.get("unresolved")):
        raise RuntimeError("blocked root or budget is not settled")
    attempt = root["attempts"][0]
    receipt = attempt.get("receipt") or {}
    expected_model = model_registry.resolve_cell(row["first_cell"])["cli_model"]
    real_roots = sorted(model for model in receipt.get("root_models", [])
                        if model != "<synthetic>")
    invocation = budget["invocations"].get(attempt["invocation_id"], {})
    if (not receipt.get("terminal") or not receipt.get("writer_stopped")
            or receipt.get("status") != "failed" or receipt.get("timed_out")
            or receipt.get("returncode") == 0
            or real_roots != [expected_model]
            or receipt.get("requested_cell") != row["first_cell"]
            or type(receipt.get("cost_usd")) not in (int, float)
            or not math.isfinite(receipt["cost_usd"])
            or receipt["cost_usd"] < 0
            or invocation.get("state") != "settled"
            or not math.isclose(invocation.get("cost_usd", -1),
                                receipt["cost_usd"], abs_tol=1e-8)
            or receipt.get("evaluation_report", {}).get("observability")
                != "worker-malformed"):
        raise RuntimeError("terminal failure cannot be safely reconciled")
    task = build(row["task_id"])
    _, rubric = plan.live_rubric(row["task_id"])
    executable, quality = live.live_grade(row["task_id"], rubric, workspace,
                                          "failed", receipt["evaluation_report"])
    target = repo / "test/results/2026-09-26-worker-q4-m3-reconciliation-files"
    if target.exists():
        raise RuntimeError("reconciliation snapshot already exists")
    files = {}
    for relative in row["editable_paths"]:
        source = workspace / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        files[relative] = sha(destination)
    snapshot = {"schema_version": 1, "sequence": sequence,
                "task_id": row["task_id"],
                "episode_label": row["episode_label"], "files": files}
    snapshot["snapshot_sha256"] = digest(snapshot)
    (target / "snapshot.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    boundary = receipt.get("command_contract", {}).get("q4_boundary", {})
    projected = {"sequence": 1, "requested_cell": receipt["requested_cell"],
                 "requested_effort": receipt.get("requested_effort"),
                 "served_effort": receipt.get("served_effort"),
                 "actual_model": expected_model,
                 "receipt_identity_valid": receipt.get("identity_valid"),
                 "identity_reconciled": True,
                 "identity_evidence": "only non-synthetic root assistant model",
                 "root_models": receipt.get("root_models"),
                 "billed_models": receipt.get("billed_models"),
                 "terminal": True, "writer_stopped": True,
                 "status": "failed", "returncode": receipt.get("returncode"),
                 "cost_usd": receipt["cost_usd"], "usage": receipt.get("usage"),
                 "wall_clock_s": receipt.get("wall_clock_s"),
                 "q1_record_sha256": boundary.get("q1_record_sha256"),
                 "q1_spec_sha256": boundary.get("q1_spec_sha256"),
                 "changed_paths": boundary.get("changed_paths"),
                 "evaluation_report": receipt["evaluation_report"],
                 "evaluation_report_digest": receipt.get(
                     "evaluation_report_digest"),
                 "original_receipt_digest": attempt.get("receipt_digest")}
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    episode = {"task_id": row["task_id"],
               "episode_label": row["episode_label"], "root_id": root_id,
               "root_state": "failed", "terminal_failure": True,
               "failure_reason": "provider-response-output-limit",
               "budget": budget, "attempts": [projected],
               "executable_grade": executable, "quality_v2": quality,
               "snapshot": snapshot, "workspace": str(workspace),
               "protected_sha256": {name: sha(workspace / name)
                                    for name in protected}}
    value = {"schema_version": 1,
             "kind": "q4-m3-terminal-failure-reconciliation",
             "manifest_sha256": manifest["manifest_sha256"],
             "campaign_file_sha256": sha(campaign_path),
             "campaign_state_sha256": campaign["state_sha256"],
             "root_record_digest": root_record_digest,
             "reconciliation_provider_calls": 0,
             "reconciliation_provider_cost_usd": 0,
             "inherited_provider_calls": 1,
             "inherited_provider_cost_usd": receipt["cost_usd"],
             "episode": episode,
             "limits": ["The paid sequence 3 invocation was not replayed.",
                        "Synthetic CLI error identity is excluded only because the real root model set is exact."]}
    value["evidence_sha256"] = digest(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise RuntimeError("preserve existing reconciliation evidence")
        value = run(args.repo, args.sequence)
        args.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8", newline="\n")
        print(json.dumps({"result": "PASS", "evidence_sha256":
                          value["evidence_sha256"]}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__,
                          "detail": str(exc)[:300]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
