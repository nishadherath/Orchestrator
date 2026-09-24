#!/usr/bin/env python3
"""Run a manifest-bound N5 cell screen, one WSL worker call per row.

The campaign ledger owns screen order and at-most-once dispatch. The existing
TaskExecutor remains the owner of B0 development episodes; its fixed ladder
cannot represent the independent fifteen-cell capability screen.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import dispatch_budget
import model_registry
import route
import worker_n5_screen as screen_plan
from worker_adapter import WorkerRequest, digest
from worker_wsl_transport import grade_isolated


class LiveScreenError(RuntimeError):
    """A frozen screen cannot advance without new evidence or authority."""


def _save(path: Path, state: dict) -> None:
    body = {key: value for key, value in state.items() if key != "state_sha256"}
    state["state_sha256"] = digest(body)
    route._atomic_write_bytes(path, (json.dumps(state, indent=2, sort_keys=True,
                                               allow_nan=False) + "\n").encode())


def _load(path: Path, manifest_sha256: str) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LiveScreenError("campaign checkpoint is unreadable; preserve it") from exc
    body = {key: value for key, value in state.items() if key != "state_sha256"}
    if (state.get("schema_version") != 1 or state.get("manifest_sha256") != manifest_sha256
            or state.get("state_sha256") != digest(body)
            or state.get("status") not in {"running", "blocked", "complete"}
            or type(state.get("next_sequence")) is not int
            or not isinstance(state.get("rows"), list)
            or not isinstance(state.get("stopped_cells"), list)):
        raise LiveScreenError("campaign checkpoint is invalid or belongs to another manifest")
    return state


def _public_hashes(actor: Path) -> dict[str, str]:
    if actor.is_symlink() or not actor.is_dir():
        raise LiveScreenError("actor directory is missing or redirected")
    names = {p.name for p in actor.iterdir()}
    if names != screen_plan.PUBLIC:
        raise LiveScreenError("actor contains an unexpected file or directory")
    if any((actor / name).is_symlink() or not (actor / name).is_file()
           for name in names):
        raise LiveScreenError("actor public file is redirected")
    return {name: screen_plan.sha(actor / name) for name in sorted(names)}


class LiveScreen:
    """Checkpointed cell screen with no implicit retry of a started call."""

    def __init__(self, manifest: dict, approval: dict, output: Path, *,
                 adapter=None, grader=None, check_host: bool = True,
                 fixtures: Path = screen_plan.SCREEN):
        screen_plan.validate_authorisation(manifest, approval, screen=fixtures,
                                           check_host=check_host)
        self.manifest = manifest
        self.fixtures = fixtures.resolve()
        self.output = output.resolve()
        if (output.is_symlink() or self.output == self.fixtures
                or self.output.is_relative_to(self.fixtures)
                or self.fixtures.is_relative_to(self.output)
                or self.output == screen_plan.CORPUS.resolve()
                or self.output.is_relative_to(screen_plan.CORPUS.resolve())):
            raise LiveScreenError("campaign output overlaps frozen evaluation inputs")
        if adapter is None:
            raise LiveScreenError("WSL credential delivery is not qualified; "
                                  "live dispatch remains closed")
        self.adapter = adapter
        self.grader = grader if grader is not None else grade_isolated
        self.check_host = check_host
        self.state_path = self.output / "campaign.json"
        self.budget_path = self.output / "budget.json"

    def _actor(self, row: dict) -> Path:
        actor = self.output / "actors" / f"row-{row['sequence']:03d}"
        if actor.exists() or actor.is_symlink():
            raise LiveScreenError("row actor already exists without a completed checkpoint")
        actor.parent.mkdir(parents=True, exist_ok=True)
        actor.mkdir()
        for name in sorted(screen_plan.PUBLIC):
            shutil.copyfile(self.fixtures / row["task"] / name, actor / name)
        expected = {name: self.manifest["screen_files"][f"{row['task']}/{name}"]
                    for name in screen_plan.PUBLIC}
        if _public_hashes(actor) != expected:
            raise LiveScreenError("materialised public actor differs from the manifest")
        return actor

    def _block(self, state: dict, reason: str, budget: dispatch_budget.DispatchBudget) -> dict:
        state.update(status="blocked", block=reason)
        _save(self.state_path, state)
        budget.cancel()
        return state

    def _finish(self, state: dict, budget: dispatch_budget.DispatchBudget) -> bool:
        """Commit a durable receipt, settle cost, then grade a stopped writer."""
        item = state["inflight"]
        row = self.manifest["rows"][item["sequence"] - 1]
        receipt = item.get("receipt")
        if not isinstance(receipt, dict):
            self._block(state, "started invocation has no durable receipt", budget)
            return False
        ident = {"admission_token": item["admission_token"],
                 "invocation_id": item["invocation_id"],
                 "revision_id": item["revision_id"],
                 "decision_digest": item["decision_digest"],
                 "intent_digest": item["intent_digest"],
                 "requested_cell": row["cell"]}
        if any(receipt.get(key) != value for key, value in ident.items()):
            self._block(state, "receipt does not match the frozen invocation", budget)
            return False
        cell = model_registry.resolve_cell(row["cell"])
        if (receipt.get("requested_effort") != cell["effort"]
                or not isinstance(receipt.get("child_models"), list)):
            self._block(state, "receipt lacks requested effort or child-model evidence", budget)
            return False
        if self.check_host:
            contract = receipt.get("command_contract") or {}
            if (not isinstance(contract, dict) or
                    contract.get("host_attestation_sha256") !=
                    self.manifest["host_attestation_sha256"]
                    or contract.get("transport") != "wsl-private-mount-pid-uid65534"
                    or contract.get("filesystem_enforcement_proven") is not True):
                self._block(state, "receipt lacks the frozen WSL host contract", budget)
                return False
        if receipt.get("status") not in ("completed", "failed", "interrupted"):
            self._block(state, "receipt has an unknown worker status", budget)
            return False
        if (receipt.get("terminal") is not True or receipt.get("writer_stopped") is not True
                or receipt.get("cost_usd") is None):
            budget.settle(item["invocation_id"], receipt.get("cost_usd"), final=False,
                          telemetry=receipt.get("usage") or {},
                          evidence=f"incomplete-receipt:{digest(receipt)}")
            self._block(state, "writer termination or provider charge is uncertain", budget)
            return False
        budget.settle(item["invocation_id"], receipt["cost_usd"], final=True,
                      telemetry=receipt.get("usage") or {},
                      evidence=f"receipt:{digest(receipt)}")
        if dispatch_budget.units(receipt["cost_usd"], ceiling=True) > dispatch_budget.units(
                row["maximum_usd"]):
            self._block(state, "provider charge exceeded the row allowance", budget)
            return False
        if budget.snapshot()["breached"]:
            self._block(state, "provider charge breached the screen ceiling", budget)
            return False
        actor = self.output / "actors" / f"row-{row['sequence']:03d}"
        current = _public_hashes(actor)
        if any(current[name] != item["before"][name]
               for name in screen_plan.PUBLIC - {"app.py"}):
            self._block(state, "protected actor file changed", budget)
            return False
        if row["kind"] == "identity":
            grade = None
            if current["app.py"] != item["before"]["app.py"]:
                self._block(state, "identity call edited app.py", budget)
                return False
        else:
            screen_plan.validate_manifest(self.manifest, screen=self.fixtures,
                                          check_host=self.check_host)
            oracle = self.fixtures / "oracles" / f"{row['task']}.json"
            oracle_sha = self.manifest["screen_files"][f"oracles/{row['task']}.json"]
            grade = self.grader(actor, oracle, oracle_sha, current["app.py"],
                                "accepted" if receipt.get("status") == "completed" else "failed")
            if (not isinstance(grade, dict)
                    or grade.get("oracle_sha256") != oracle_sha
                    or grade.get("actor_app_sha256") != current["app.py"]
                    or type(grade.get("acceptance")) is not bool
                    or type(grade.get("critical_error")) is not bool
                    or type(grade.get("false_success")) is not bool
                    or type(grade.get("quality")) not in (int, float)
                    or not math.isfinite(grade["quality"])
                    or not 0 <= grade["quality"] <= 100
                    or type(grade.get("case_count")) is not int
                    or grade["case_count"] <= 0
                    or not isinstance(grade.get("milestones"), list)
                    or not all(isinstance(name, str) for name in grade["milestones"])
                    or _public_hashes(actor) != current):
                self._block(state, "isolated grade is invalid or actor changed", budget)
                return False
        identity_ok = model_registry.identity_matches(
            row["cell"], receipt.get("actual_model"), receipt["child_models"])
        stopped = (not identity_ok or
                   (row["kind"] == "identity" and receipt.get("status") != "completed"))
        if stopped and row["cell"] not in state["stopped_cells"]:
            state["stopped_cells"].append(row["cell"])
        state["rows"].append({"sequence": row["sequence"], "cell": row["cell"],
                              "task": row["task"], "status": "stopped" if stopped else "graded",
                              "receipt": receipt, "grade": grade,
                              "observed_identity_valid": identity_ok,
                              "actor_app_sha256": current["app.py"]})
        state["next_sequence"] += 1
        state["inflight"] = None
        _save(self.state_path, state)
        return True

    def run(self) -> dict:
        """Run the fixed order; a crash after intent never repeats its call."""
        self.output.mkdir(parents=True, exist_ok=True)
        with route.ledger_lock(self.state_path):
            screen_plan.validate_manifest(self.manifest, screen=self.fixtures,
                                          check_host=self.check_host)
            if self.state_path.exists():
                state = _load(self.state_path, self.manifest["manifest_sha256"])
                if (state["next_sequence"] != len(state["rows"]) + 1
                        or any(result.get("sequence") != index or
                               result.get("cell") != self.manifest["rows"][index - 1]["cell"]
                               for index, result in enumerate(state["rows"], 1))):
                    raise LiveScreenError("campaign row sequence differs from the manifest")
            else:
                if self.budget_path.exists() or (self.output / "actors").exists():
                    raise LiveScreenError("campaign output has orphan budget or actor data")
                state = {"schema_version": 1,
                         "manifest_sha256": self.manifest["manifest_sha256"],
                         "status": "running", "next_sequence": 1,
                         "rows": [], "stopped_cells": [], "inflight": None}
                _save(self.state_path, state)
            budget = dispatch_budget.DispatchBudget(
                self.budget_path, self.manifest["cost"]["maximum_usd"],
                scope="task_dispatch")
            if state["status"] != "running":
                return state
            if state["inflight"] is not None:
                if not self._finish(state, budget):
                    return state
            while state["next_sequence"] <= len(self.manifest["rows"]):
                row = self.manifest["rows"][state["next_sequence"] - 1]
                if row["cell"] in state["stopped_cells"]:
                    state["rows"].append({"sequence": row["sequence"], "cell": row["cell"],
                                          "task": row["task"], "status": "skipped"})
                    state["next_sequence"] += 1
                    _save(self.state_path, state)
                    continue
                screen_plan.validate_manifest(self.manifest, screen=self.fixtures,
                                              check_host=self.check_host)
                actor = self._actor(row)
                before = _public_hashes(actor)
                invocation_id = digest({"manifest": self.manifest["manifest_sha256"],
                                        "sequence": row["sequence"]})[:32]
                if invocation_id in budget.snapshot()["invocations"]:
                    return self._block(state, "prior invocation exists without row result", budget)
                try:
                    allowance = budget.reserve(invocation_id, row["maximum_usd"],
                                               row["maximum_usd"],
                                               {"manifest_sha256": self.manifest["manifest_sha256"],
                                                "sequence": row["sequence"],
                                                "cell": row["cell"]})
                except dispatch_budget.BudgetError as exc:
                    return self._block(state, f"budget cannot admit row: {exc}", budget)
                decision_digest = digest(row)
                intent = {"sequence": row["sequence"], "invocation_id": invocation_id,
                          "admission_token": digest({"token": invocation_id}),
                          "revision_id": self.manifest["manifest_sha256"],
                          "decision_digest": decision_digest, "before": before,
                          "receipt": None}
                intent["intent_digest"] = digest(intent)
                state["inflight"] = intent
                _save(self.state_path, state)
                budget.start(invocation_id)
                request = WorkerRequest(
                    actor, (actor / "ISSUE.md").read_text(encoding="utf-8"),
                    ("app.py",), row["cell"], allowance,
                    "One N5 capability-screen call. Complete the public task; do not delegate.",
                    timeout_s=row["timeout_seconds"],
                    admission_token=intent["admission_token"],
                    invocation_id=invocation_id, revision_id=intent["revision_id"],
                    decision_digest=decision_digest, intent_digest=intent["intent_digest"])
                try:
                    receipt = self.adapter.run(request)
                except Exception as exc:
                    budget.settle(invocation_id, None, final=False,
                                  telemetry={"exception_type": type(exc).__name__},
                                  evidence="adapter exception; charge unknown")
                    return self._block(state, f"adapter exception: {exc}", budget)
                state["inflight"]["receipt"] = receipt
                _save(self.state_path, state)  # Receipt precedes settlement.
                if not self._finish(state, budget):
                    return state
            state["status"] = "complete"
            _save(self.state_path, state)
            return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true",
                        help="reserved for the qualified WSL credential path")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute is required; inspecting a manifest never launches workers")
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        approval = json.loads(args.approval.read_text(encoding="utf-8-sig"))
        result = LiveScreen(manifest, approval, args.output).run()
    except (OSError, ValueError, LiveScreenError, screen_plan.ScreenError) as exc:
        print(f"N5 screen launch blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "next_sequence": result["next_sequence"],
                      "completed_rows": len(result["rows"]),
                      "manifest_sha256": result["manifest_sha256"]}, sort_keys=True))
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
