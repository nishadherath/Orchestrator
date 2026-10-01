#!/usr/bin/env python3
"""Seal Q4R's settled, transport-invalid episode without replaying its call."""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
from pathlib import Path

import dispatch_budget
import model_registry
import worker_q4r_screen as plan
import worker_q4r_screen_live as live
from task_executor import _read
from worker_adapter import digest
from worker_q3_public_catalogue import sha
from worker_wsl_q1 import SEEDS

SEQUENCE = 3
OUTPUT = plan.ROOT / "test/results/2026-09-25-worker-q4r-r1-reconciliation.json"
SNAPSHOT = plan.ROOT / "test/results/2026-09-25-worker-q4r-r1-reconciliation-files"


def run() -> dict:
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("Q4R reconciliation requires WSL root")
    if OUTPUT.exists() or SNAPSHOT.exists():
        raise RuntimeError("Q4R reconciliation evidence already exists")
    manifest = json.loads(plan.MANIFEST.read_text(encoding="utf-8"))
    campaign_path = live.RUN / "campaign.json"
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    if (campaign.get("state_sha256") != digest({
            key: value for key, value in campaign.items()
            if key != "state_sha256"})
            or campaign.get("manifest_sha256") != manifest["manifest_sha256"]
            or campaign.get("status") != "blocked"
            or campaign.get("stop_reason") != "uncertain episode"
            or len(campaign.get("rows", [])) != SEQUENCE
            or campaign["rows"][-1].get("sequence") != SEQUENCE
            or campaign["rows"][-1].get("state") != "uncertain"):
        raise RuntimeError("Q4R campaign is not the exact blocked checkpoint")
    row = manifest["rows"][SEQUENCE - 1]
    workspace = SEEDS / ("q4r-" + manifest["manifest_sha256"][:12]
                         + f"-{SEQUENCE:02d}")
    root_id = digest({"manifest": manifest["manifest_sha256"],
                      "sequence": SEQUENCE})[:24]
    root_path = workspace / ".claude/task-executor-v2" / root_id / "root.json"
    root_record_digest = json.loads(root_path.read_text(
        encoding="utf-8"))["record_digest"]
    root = _read(root_path)
    budget = dispatch_budget.DispatchBudget(root_path.parent / "budget.json",
                                            scope="task_dispatch").snapshot()
    if (root.get("state") != "blocked" or len(root.get("attempts", [])) != 1
            or budget.get("unresolved") or budget.get("breached")):
        raise RuntimeError("Q4R root or budget is not settled")
    attempt = root["attempts"][0]
    receipt = attempt.get("receipt") or {}
    invocation = budget["invocations"].get(attempt["invocation_id"], {})
    expected_model = model_registry.resolve_cell(row["first_cell"])["cli_model"]
    real_roots = sorted(model for model in receipt.get("root_models", [])
                        if model != "<synthetic>")
    report = receipt.get("evaluation_report") or {}
    transport = receipt.get("evaluation_transport") or {}
    if (row["sequence"] != SEQUENCE or row["task_id"] != "P08"
            or row["episode_label"] != "sonnet-high"
            or receipt.get("requested_cell") != row["first_cell"]
            or real_roots != [expected_model]
            or not receipt.get("terminal") or not receipt.get("writer_stopped")
            or receipt.get("timed_out") or receipt.get("status") != "failed"
            or receipt.get("returncode") == 0
            or report.get("observability") != "transport-invalid"
            or transport.get("structured_output_present") is not False
            or type(receipt.get("cost_usd")) not in (int, float)
            or not math.isfinite(receipt["cost_usd"])
            or receipt["cost_usd"] < 0
            or invocation.get("state") != "settled"
            or not math.isclose(invocation.get("cost_usd", -1),
                                receipt["cost_usd"], abs_tol=1e-8)
            or not math.isclose(budget["spent_usd"],
                                receipt["cost_usd"], abs_tol=1e-8)):
        raise RuntimeError("Q4R terminal failure cannot be safely reconciled")
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    if any(sha(workspace / name) != row["actor_files"][name]
           for name in protected):
        raise RuntimeError("Q4R protected public source changed")
    executable, quality = live.live_grade(row["task_id"], row["rubric"],
                                           workspace, "failed", report)
    if (not quality["critical_error"] or quality["report_observability"]
            != "transport-invalid"):
        raise RuntimeError("Q4R failure no longer matches the frozen stop rule")
    files = {}
    for relative in row["editable_paths"]:
        destination = SNAPSHOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(workspace / relative, destination)
        files[relative] = sha(destination)
    snapshot = {"schema_version": 1, "sequence": SEQUENCE,
                "task_id": row["task_id"],
                "episode_label": row["episode_label"], "files": files}
    snapshot["snapshot_sha256"] = digest(snapshot)
    (SNAPSHOT / "snapshot.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    value = {
        "schema_version": 1, "kind": "q4r-terminal-transport-reconciliation",
        "manifest_sha256": manifest["manifest_sha256"],
        "campaign_file_sha256": sha(campaign_path),
        "campaign_state_sha256": campaign["state_sha256"],
        "root_record_digest": root_record_digest,
        "episode_sequence": SEQUENCE, "task_id": row["task_id"],
        "episode_label": row["episode_label"],
        "expected_model": expected_model, "root_models": receipt["root_models"],
        "billed_models": receipt["billed_models"],
        "requested_effort": receipt["requested_effort"],
        "served_effort": receipt["served_effort"],
        "receipt_identity_valid": receipt["identity_valid"],
        "terminal": True, "writer_stopped": True,
        "receipt_digest": attempt["receipt_digest"],
        "provider_calls_reconciled": 1,
        "provider_cost_usd_reconciled": receipt["cost_usd"],
        "additional_provider_calls": 0, "additional_provider_cost_usd": 0,
        "budget": budget, "transport": transport, "report": report,
        "executable_grade": executable, "quality_v2": quality,
        "snapshot": snapshot,
        "protected_sha256": {name: sha(workspace / name)
                             for name in protected},
        "limits": ["The paid sequence 3 invocation was not replayed.",
                   "Observed real root model does not prove served effort.",
                   "No valid final structured report was received."],
    }
    value["evidence_sha256"] = digest(value)
    return value


def main() -> int:
    try:
        value = run()
        with OUTPUT.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(json.dumps({"result": "PASS", "evidence_sha256":
                          value["evidence_sha256"]}, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({"result": "BLOCKED", "error_type":
                          type(exc).__name__, "detail": str(exc)[:240]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
