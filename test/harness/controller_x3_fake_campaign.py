#!/usr/bin/env python3
"""Run sealed X3 S/A pairs through production assessment and N1 workflow.

This is a provider-free boundary campaign. The interpreter, Controller and
worker are deterministic doubles; their synthetic charges exercise the real
budget ledger. Protected grading remains separate and no quality uplift is
inferred from equal reference-overlay outcomes.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_evaluation  # noqa: E402
import controller_workflow  # noqa: E402
import model_registry  # noqa: E402
import controller_x3_manifest  # noqa: E402
import evaluation_runner  # noqa: E402
from test.harness.controller_routing_r4_tests import FakeAdapter as FakeController  # noqa: E402
from test.harness.controller_x3_pair_tests import interpret_public, prepare  # noqa: E402


class X3CampaignError(RuntimeError):
    """A sealed pair could not complete its provider-free production path."""


def _episode(row: dict, run_root: Path, assessment_charge_usd: float) -> dict:
    project = run_root / "actors" / f"{row['sequence']:03d}-{row['task_id']}-{row['arm']}"
    executor, root_id, worker = prepare(project, row["task_id"])
    record = executor.status(root_id)
    editable = record["definition"]["scope"]
    source = next(path for path in editable if path != "report.json")
    sources = list(dict.fromkeys(["issue.md", "app.py", "public_check.py", source]))
    issue = (project / "issue.md").read_text(encoding="utf-8")
    heading = next(line for line in issue.splitlines() if line.startswith("# "))
    check_lines = (project / "public_check.py").read_text(encoding="utf-8").splitlines()
    assertion = next(line for line in check_lines
                     if line.lstrip().startswith("assert ") and check_lines.count(line) == 1)
    packets: list[dict] = []

    def interpreter(packet: dict) -> dict:
        packets.append(packet)
        response = interpret_public(packet)
        response["telemetry"] = {
            "provider_calls": 1, "model": model_registry.resolve_cell(
                "worker-sonnet-low")["cli_model"],
            "cost_usd": assessment_charge_usd,
            "input_tokens": 100, "output_tokens": 20,
        }
        return response

    result = controller_workflow.execute(
        executor, root_id, issue="issue.md", source_paths=sources,
        quote_requests=[{"source": "issue.md", "quote": heading},
                        {"source": "public_check.py", "quote": assertion}],
        interpreter=interpreter,
        operational={"context_tokens": 1000, "deadline_seconds": None,
                     "prior_local_repairs": 0, "required_artefacts": editable,
                     "deadline": None, "authorised_task_budget_usd": 12.0,
                     "observed_at": "2026-09-28T00:00:00Z"},
        assessment_allowance_usd=0.5,
        controller_adapter=FakeController(), explicit_mode=row["mode"],
    )
    if len(packets) != 1:
        raise X3CampaignError(f"{row['task_id']} {row['arm']}: public packet count differs")
    task = result["task"]
    if (task["state"] != "accepted" or len(worker.calls) != 1
            or task["public_assessment"]["status"] != "settled"
            or task["budget"]["unresolved"]):
        raise X3CampaignError(f"{row['task_id']} {row['arm']}: N1 did not independently accept")
    packet = packets[0]
    return {"sequence": row["sequence"], "task_id": row["task_id"],
            "arm": row["arm"], "effective_action": result["decision"]["effective_action"],
            "task_state": task["state"], "worker_attempts": len(worker.calls),
            "assessment_status": task["public_assessment"]["status"],
            "accounting_complete": (not task["budget"]["unresolved"]
                                    and task["budget"]["reserved_usd"] == 0),
            "synthetic_spend_usd": task["budget"]["spent_usd"],
            "public_sources_sha256": controller_evaluation.digest(packet["sources"]),
            "public_citations_sha256": controller_evaluation.digest(packet["citations"]),
            "actual_provider_calls": 0}


def execute(manifest_path: Path, run_root: Path) -> dict:
    """Run once in a fresh result directory; partial state is never replayed."""
    manifest_path, run_root = manifest_path.resolve(), run_root.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    controller_x3_manifest.validate(manifest)
    if (run_root.exists() or not run_root.is_relative_to(ROOT / "test" / "results")
            or manifest_path == run_root or manifest_path.is_relative_to(run_root)):
        raise X3CampaignError("X3 campaign needs a fresh test/results run root")
    run_root.mkdir(parents=True)
    state_path = run_root / "state.json"
    state = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
             "status": "running", "episodes": [], "pairs": [],
             "actual_provider_calls": 0}
    evaluation_runner.atomic_json(state_path, state)
    try:
        for row in manifest["episodes"]:
            controller_x3_manifest.validate(manifest)
            receipt = _episode(row, run_root, manifest["assessment_charge_usd"])
            state["episodes"].append(receipt)
            evaluation_runner.atomic_json(state_path, state)
        for task_id in dict.fromkeys(row["task_id"] for row in manifest["episodes"]):
            arms = {row["arm"]: row for row in state["episodes"] if row["task_id"] == task_id}
            if (set(arms) != {"S", "A"}
                    or arms["S"]["public_sources_sha256"] != arms["A"]["public_sources_sha256"]
                    or arms["S"]["public_citations_sha256"] != arms["A"]["public_citations_sha256"]):
                raise X3CampaignError(f"{task_id}: paired public evidence differs")
            state["pairs"].append({"task_id": task_id, "same_public_evidence": True,
                                   "s_action": arms["S"]["effective_action"],
                                   "a_action": arms["A"]["effective_action"],
                                   "synthetic_cost_delta_usd": round(
                                       arms["A"]["synthetic_spend_usd"]
                                       - arms["S"]["synthetic_spend_usd"], 9)})
        if (not any(row["a_action"] == "controller" for row in state["pairs"])
                or not any(row["a_action"] == "worker" for row in state["pairs"])):
            raise X3CampaignError("fake pairs did not exercise both automatic actions")
        state["status"] = "completed"
    except BaseException as exc:
        state["status"] = "stopped"
        state["stop_reason"] = f"{type(exc).__name__}: {exc}"
        evaluation_runner.atomic_json(state_path, state)
        raise
    evaluation_runner.atomic_json(state_path, state)
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    state = execute(args.manifest, args.out)
    print(json.dumps({"status": state["status"],
                      "episodes": len(state["episodes"]),
                      "pairs": state["pairs"],
                      "actual_provider_calls": state["actual_provider_calls"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
