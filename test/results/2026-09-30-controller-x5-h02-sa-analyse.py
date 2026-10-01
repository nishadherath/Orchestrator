#!/usr/bin/env python3
"""Reconcile the single-use H02 S/A receipts without changing either root."""

from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02_pair as pair  # noqa: E402
import dispatch_budget  # noqa: E402


def read(path):
    assert path.is_file() and not path.is_symlink(), path
    return json.loads(path.read_text(encoding="utf-8"))


def money(value):
    return Decimal(str(value))


manifest = read(pair.MANIFEST_PATH)
prepared = read(pair.RUN_DIR / "prepared.json")
assert prepared["manifest_sha256"] == manifest["manifest_sha256"]
assert read(pair.RUN_DIR / "snapshot.json") == manifest["snapshot"]
results = {arm: read(pair.RUN_DIR / f"{arm}-result.json") for arm in ("S", "A")}
for arm, result in results.items():
    assert result["manifest_sha256"] == manifest["manifest_sha256"]
    assert result["root_id"] == pair.root_id(manifest, arm)
    assert result["attempt_count"] == 1 and result["error"] is None
    assert result["state"] == "ready" and result["worker_identity_valid"] is True
    assert not result["budget"]["unresolved"] and not result["budget"]["breached"]
    assert result["budget"]["spent_usd"] <= manifest["root_limits_usd"][arm]
    plugin = pair.actor_path(manifest, arm) / pair.EDITABLE
    assert hashlib.sha256(plugin.read_bytes()).hexdigest() == result["grade"]["candidate_edit_sha256"]
    assert result["grade"]["quality"] == 30
    assert result["grade"]["checks"]["public"] is False

assert results["S"]["qualified"] is True
assert results["A"]["qualified"] is False
assert results["A"]["effective_action"] == "controller"
assert results["A"]["controller_stage"] == "worker-ready"
assert results["A"]["controller_invocations"] == 1
assert results["A"]["controller_handoff_actionable"] is False

dispatch_paths = list(pair.actor_path(manifest, "A").rglob("dispatch-state.json"))
assert len(dispatch_paths) == 1
dispatch = read(dispatch_paths[0])
assert dispatch["stage"] == "worker-ready" and dispatch["controller_invocations"] == 1
assert pair.actionable_handoff(dispatch) is False
handoff = dispatch["worker_handoff"]
assert handoff["controller_used"] is True
role_dir = Path(dispatch["controller_result"]["controller_run_dir"])
role_budget = dispatch_budget.DispatchBudget(role_dir / "dispatch-budget.json").snapshot()
assert not role_budget["unresolved"] and not role_budget["breached"]
role_rows = list(role_budget["invocations"].values())
assert len(role_rows) == 2
assert all(row["state"] == "settled" for row in role_rows)
assert all(((row["telemetry"] or {}).get("identity") or {}).get("identity_valid") is True
           for row in role_rows)
assert abs(sum((money(row["cost_usd"]) for row in role_rows), Decimal(0)) - money(
    dispatch["controller_result"]["cost_usd"])) <= Decimal("0.000000002")

unit = Decimal("0.000000001")
s_cost = money(results["S"]["budget"]["spent_usd"])
a_cost = money(results["A"]["budget"]["spent_usd"])
pair_cost = s_cost + a_cost
assert pair_cost <= money(manifest["maximum_authorised_usd"])
allocations = {}
for row in results["A"]["budget"]["invocations"].values():
    allocation = (row["metadata"] or {}).get("allocation", "worker")
    allocations[allocation] = allocations.get(allocation, Decimal(0)) + money(row["cost_usd"])
assert sum(allocations.values(), Decimal(0)).quantize(unit) == a_cost.quantize(unit)

body = {
    "schema_version": 1,
    "case_id": "H02",
    "manifest_sha256": manifest["manifest_sha256"],
    "origin": manifest["origin"],
    "producer_cost_usd": manifest["snapshot"]["producer_cost_usd"],
    "pair_cost_usd": float(pair_cost),
    "S": {"quality": results["S"]["grade"]["quality"],
          "public_passed": results["S"]["grade"]["checks"]["public"],
          "qualified": True, "spent_usd": float(s_cost),
          "candidate_sha256": results["S"]["grade"]["candidate_edit_sha256"]},
    "A": {"quality": results["A"]["grade"]["quality"],
          "public_passed": results["A"]["grade"]["checks"]["public"],
          "qualified": False, "qualification_failure": "controller_handoff_not_actionable",
          "spent_usd": float(a_cost),
          "cost_by_allocation_usd": {k: float(v) for k, v in sorted(allocations.items())},
          "controller_role_calls": len(role_rows),
          "controller_role_identity_valid": True,
          "controller_outcome": dispatch["controller_result"]["outcome"],
          "controller_handoff_readiness": handoff["readiness"],
          "controller_safe_next_action": handoff["safe_next_action"],
          "candidate_sha256": results["A"]["grade"]["candidate_edit_sha256"]},
    "observed_quality_delta_A_minus_S": 0,
    "incremental_A_cost_usd": float(a_cost - s_cost),
    "primary_uplift_qualified": False,
    "promotion_case": False,
    "interpretation": "A and S both failed public and protected completion; A's Controller stopped at a provisional gap and yielded no actionable repair handoff.",
}
body["evidence_sha256"] = hashlib.sha256(json.dumps(
    body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
out = pair.RUN_DIR / "analysis.json"
with out.open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(body, stream, sort_keys=True, indent=2)
    stream.write("\n")
print(json.dumps({k: body[k] for k in ("pair_cost_usd", "observed_quality_delta_A_minus_S",
                                       "primary_uplift_qualified", "promotion_case")},
                 sort_keys=True))
