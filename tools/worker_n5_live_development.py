#!/usr/bin/env python3
"""Run an exactly approved N5 development campaign through TaskExecutor.

Each episode has its own root task and budget. A separate campaign ledger
prevents aggregate oversubscription. A started worker intent without a durable
receipt blocks on restart; this driver never retries it automatically.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import acceptance
import dispatch_budget
import route
import worker_evaluation
import worker_n5_development as plan
from task_executor import TaskExecutor, EXPERIMENTAL_POLICY
from worker_adapter import digest
from worker_wsl_transport import WslWorkerAdapter, grade_isolated, wsl_public_command_runner


class LiveDevelopmentError(RuntimeError):
    """The campaign cannot safely admit another worker episode."""


def _save(path: Path, state: dict) -> None:
    body = {key: value for key, value in state.items() if key != "state_sha256"}
    state["state_sha256"] = digest(body)
    route._atomic_write_bytes(path, (json.dumps(state, indent=2, sort_keys=True,
                                               allow_nan=False) + "\n").encode())


def _load(path: Path, manifest_sha256: str) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LiveDevelopmentError("campaign checkpoint is unreadable; preserve it") from exc
    body = {key: value for key, value in state.items() if key != "state_sha256"}
    if (state.get("schema_version") != 1
            or state.get("manifest_sha256") != manifest_sha256
            or state.get("state_sha256") != digest(body)
            or state.get("status") not in {"running", "blocked", "complete"}
            or type(state.get("next_sequence")) is not int
            or not isinstance(state.get("rows"), list)):
        raise LiveDevelopmentError("campaign checkpoint is invalid or foreign")
    return state


def _invocation_id(manifest: dict, sequence: int) -> str:
    return digest({"manifest": manifest["manifest_sha256"],
                   "sequence": sequence})[:32]


def _public_hashes(actor: Path) -> dict[str, str]:
    if actor.is_symlink() or not actor.is_dir():
        raise LiveDevelopmentError("actor is missing or redirected")
    result = {}
    for name in plan.PUBLIC:
        path = actor / name
        if path.is_symlink() or not path.is_file():
            raise LiveDevelopmentError(f"public actor file is missing or redirected: {name}")
        result[name] = plan.sha(path)
    return result


class LiveDevelopment:
    """One serial, checkpointed campaign over the frozen development rows."""

    def __init__(self, manifest: dict, approval: dict, output: Path, *,
                 adapter=None, grader=None, command_runner=None,
                 check_host: bool = True, corpus: Path = plan.CORPUS,
                 screen_run: Path = plan.SCREEN_RUN):
        plan.validate_authorisation(manifest, approval, corpus=corpus,
                                    screen_run=screen_run, check_host=check_host)
        self.manifest = manifest
        self.corpus = corpus.resolve()
        self.screen_run = screen_run.resolve()
        self.output = output.resolve()
        if (output.is_symlink() or self.output == self.corpus
                or self.output.is_relative_to(self.corpus)
                or self.corpus.is_relative_to(self.output)
                or self.output == screen_run.resolve()
                or self.output.is_relative_to(screen_run.resolve())):
            raise LiveDevelopmentError("output overlaps frozen corpus or screen")
        if adapter is None:
            if not check_host:
                raise LiveDevelopmentError("an explicit fake adapter is required offline")
            adapter = WslWorkerAdapter(subscription=True)
        elif check_host and (not isinstance(adapter, WslWorkerAdapter)
                             or not adapter.host.subscription):
            raise LiveDevelopmentError("live dispatch requires WSL subscription adapter")
        elif not check_host and getattr(adapter, "offline_fake", False) is not True:
            raise LiveDevelopmentError("offline injection requires an explicit fake")
        self.adapter = adapter
        self.grader = grader or grade_isolated
        self.command_runner = command_runner or wsl_public_command_runner
        self.check_host = check_host
        self.catalogue = {task["id"]: task for task in
                          worker_evaluation.load_catalogue(self.corpus)["tasks"]
                          if task["split"] == "development"}
        self.state_path = self.output / "campaign.json"
        self.budget_path = self.output / "budget.json"

    def _block(self, state: dict, reason: str,
               budget: dispatch_budget.DispatchBudget) -> dict:
        state.update(status="blocked", block=reason)
        _save(self.state_path, state)
        budget.cancel()
        return state

    def _actor(self, row: dict) -> Path:
        actor = self.output / "actors" / f"row-{row['sequence']:03d}"
        if actor.exists() or actor.is_symlink():
            raise LiveDevelopmentError("orphan actor exists without checkpoint")
        task = self.catalogue[row["task_id"]]
        source = worker_evaluation._inside(self.corpus, task["actor"])
        actor.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, actor)
        shutil.copyfile(worker_evaluation._inside(self.corpus, task["issue"], file=True),
                        actor / "ISSUE.md")
        shutil.copyfile(worker_evaluation._inside(self.corpus, task["acceptance"], file=True),
                        actor / "acceptance.json")
        expected = self.manifest["corpus_files"]
        for name in plan.PUBLIC:
            corpus_name = (f"{task['actor']}/{name}" if name in {"app.py", "public_check.py"}
                           else task["issue"] if name == "ISSUE.md" else task["acceptance"])
            if plan.sha(actor / name) != expected[corpus_name]:
                raise LiveDevelopmentError("materialised actor differs from frozen corpus")
        if set(p.name for p in actor.iterdir()) != set(plan.PUBLIC):
            raise LiveDevelopmentError("actor package contains unexpected entries")
        return actor

    def _executor(self, actor: Path) -> TaskExecutor:
        return TaskExecutor(actor, self.adapter,
                            command_runner=self.command_runner,
                            campaign_prompt=plan.CAMPAIGN_PROMPT)

    def _admit_root(self, executor: TaskExecutor, row: dict, actor: Path,
                    root_id: str, authority_id: str) -> None:
        task = self.catalogue[row["task_id"]]
        experimental = None
        if row["arm"] != "B0":
            experimental = {
                "schema_version": 1, "arm": row["arm"],
                "manifest_sha256": self.manifest["manifest_sha256"],
                "assessment": self.manifest["assessments"][row["task_id"]],
                "alternative_cell": (plan.ALTERNATIVE_BY_COMPLEXITY[
                                     task["assessment"]["complexity"]]
                                     if row["arm"] == "alternative" else None),
                "fallback_cell": plan.FALLBACK_CELL,
                "cost_ceiling_usd": row["maximum_usd"]}
        executor.admit(goal=(actor / "ISSUE.md").read_text(encoding="utf-8"),
                       scope=task["allowed_edits"], permissions=["read", "edit"],
                       acceptance_path=actor / "acceptance.json",
                       budget_usd=row["maximum_usd"], authority_id=authority_id,
                       actor="n5-development", root_id=root_id,
                       input_paths=["ISSUE.md", "public_check.py", "acceptance.json"],
                       experimental_dispatch=experimental)

    def _finish(self, state: dict, budget: dispatch_budget.DispatchBudget) -> bool:
        """Resume a root safely, then settle and independently grade it."""
        item = state["inflight"]
        row = self.manifest["rows"][item["sequence"] - 1]
        actor = self.output / "actors" / f"row-{row['sequence']:03d}"
        if not actor.is_dir() or actor.is_symlink():
            self._block(state, "inflight actor is missing or redirected", budget)
            return False
        executor = self._executor(actor)
        root_id = item["root_id"]
        if not executor._path(root_id).exists():
            outer = budget.snapshot()["invocations"].get(item["invocation_id"])
            if outer is None or outer["state"] != "reserved":
                self._block(state, "campaign intent lacks a safe root admission", budget)
                return False
            try:
                self._admit_root(executor, row, actor, root_id, item["authority_id"])
            except Exception as exc:
                self._block(state, f"root admission failed: {exc}", budget)
                return False
        root_before = executor.status(root_id)
        task = self.catalogue[row["task_id"]]
        definition = root_before["definition"]
        expected_inputs = ["ISSUE.md", "public_check.py", "acceptance.json"]
        if (root_before["root_id"] != root_id
                or root_before["admission"]["authority_id"] != item["authority_id"]
                or root_before["admission"]["actor"] != "n5-development"
                or definition["goal"] != (actor / "ISSUE.md").read_text(encoding="utf-8")
                or definition["scope"] != task["allowed_edits"]
                or definition["permissions"] != ["read", "edit"]
                or definition["input_revision"]["input_paths"] != expected_inputs
                or definition["input_revision"]["content"] !=
                acceptance.snapshot(actor, expected_inputs)
                or root_before["admission"]["policy"] !=
                ("B0" if row["arm"] == "B0" else EXPERIMENTAL_POLICY)
                or root_before["ladder"] != row["ladder"]
                or root_before["admission"]["campaign_prompt_digest"] !=
                digest(plan.CAMPAIGN_PROMPT)
                or (row["arm"] != "B0" and root_before["experimental_policy"][
                    "manifest_sha256"] != self.manifest["manifest_sha256"])):
            self._block(state, "root does not match the frozen campaign row", budget)
            return False
        outer = budget.snapshot()["invocations"][item["invocation_id"]]
        if outer["state"] == "settled" and root_before["state"] not in {
                "accepted", "failed", "partial"}:
            self._block(state, "settled campaign charge cannot relaunch a root", budget)
            return False
        if outer["state"] == "reserved":
            budget.start(item["invocation_id"])
        try:
            result = executor.run(root_id)
        except Exception as exc:
            self._block(state, f"executor error; reconcile root before resume: {exc}", budget)
            return False
        if result["state"] not in {"accepted", "failed", "partial"}:
            self._block(state, f"root stopped in {result['state']}; no replay", budget)
            return False
        root_budget = result["budget"]
        if root_budget["unresolved"] or root_budget["breached"]:
            self._block(state, "root has unresolved or breached spend", budget)
            return False
        spent = root_budget["spent_usd"]
        if (type(spent) not in (int, float) or not math.isfinite(spent)
                or spent < 0 or spent > row["maximum_usd"]):
            self._block(state, "root cost exceeds the episode allowance", budget)
            return False
        receipts = [attempt.get("receipt") for attempt in result["attempts"]]
        if any(not isinstance(receipt, dict) or receipt.get("terminal") is not True
               or receipt.get("writer_stopped") is not True or
               receipt.get("cost_usd") is None for receipt in receipts):
            self._block(state, "root has an incomplete attempt receipt", budget)
            return False
        root_record_digest = digest({key: value for key, value in result.items()
                                     if key != "budget"})
        outer = budget.snapshot()["invocations"][item["invocation_id"]]
        if outer["state"] == "settled":
            if outer["cost_usd"] != spent:
                self._block(state, "campaign and root charges differ", budget)
                return False
        else:
            budget.settle(item["invocation_id"], spent, final=True,
                          telemetry={"root_id": root_id, "attempts": len(receipts)},
                          evidence=f"root:{root_record_digest}")
        if budget.snapshot()["breached"]:
            self._block(state, "campaign allocation breached", budget)
            return False
        current = _public_hashes(actor)
        if any(current[name] != item["before"][name]
               for name in set(plan.PUBLIC) - set(self.catalogue[row["task_id"]]["allowed_edits"])):
            self._block(state, "protected public actor file changed", budget)
            return False
        oracle = worker_evaluation._inside(self.corpus, task["oracle"], file=True)
        oracle_sha = self.manifest["corpus_files"][task["oracle"]]
        try:
            grade = self.grader(actor, oracle, oracle_sha, current["app.py"],
                                result["state"])
        except Exception as exc:
            self._block(state, f"isolated grade failed: {exc}", budget)
            return False
        if (not isinstance(grade, dict)
                or grade.get("oracle_sha256") != oracle_sha
                or grade.get("actor_app_sha256") != current["app.py"]
                or type(grade.get("acceptance")) is not bool
                or type(grade.get("quality")) not in (int, float)
                or not math.isfinite(grade["quality"])
                or not 0 <= grade["quality"] <= 100
                or _public_hashes(actor) != current):
            self._block(state, "isolated grade is invalid or actor changed", budget)
            return False
        state["rows"].append({"sequence": row["sequence"], "task_id": row["task_id"],
                              "arm": row["arm"], "root_state": result["state"],
                              "grade": grade, "spent_usd": spent,
                              "attempts": len(receipts),
                              "requested_cells": [attempt["requested_cell"] for attempt in
                                                  result["attempts"]],
                              "root_record_digest": root_record_digest,
                              "actor_app_sha256": current["app.py"]})
        state["next_sequence"] += 1
        state["inflight"] = None
        _save(self.state_path, state)
        return True

    def run(self) -> dict:
        self.output.mkdir(parents=True, exist_ok=True)
        with route.ledger_lock(self.state_path):
            plan.validate_manifest(self.manifest, corpus=self.corpus,
                                   screen_run=self.screen_run,
                                   check_host=self.check_host)
            if self.state_path.exists():
                state = _load(self.state_path, self.manifest["manifest_sha256"])
                if state["next_sequence"] != len(state["rows"]) + 1:
                    raise LiveDevelopmentError("campaign sequence is inconsistent")
                if not self.budget_path.exists():
                    raise LiveDevelopmentError("campaign budget is missing; never recreate it")
            else:
                if self.budget_path.exists() or (self.output / "actors").exists():
                    raise LiveDevelopmentError("campaign output has orphan state")
                state = {"schema_version": 1,
                         "manifest_sha256": self.manifest["manifest_sha256"],
                         "status": "running", "next_sequence": 1,
                         "rows": [], "inflight": None}
                _save(self.state_path, state)
            budget = dispatch_budget.DispatchBudget(
                self.budget_path, self.manifest["cost"]["maximum_usd"],
                scope="task_dispatch")
            rows = state["rows"]
            inflight = state["inflight"]
            if len(rows) > len(self.manifest["rows"]) or (
                    inflight is not None and (not isinstance(inflight, dict)
                    or inflight.get("sequence") != state["next_sequence"])):
                raise LiveDevelopmentError("campaign progress exceeds the frozen schedule")
            for index, observed in enumerate(rows, 1):
                planned = self.manifest["rows"][index - 1]
                if (observed.get("sequence") != index
                        or observed.get("task_id") != planned["task_id"]
                        or observed.get("arm") != planned["arm"]):
                    raise LiveDevelopmentError("campaign result does not match the frozen row")
            expected_ids = {_invocation_id(self.manifest, index)
                            for index in range(1, len(rows) + 1)}
            if inflight is not None:
                if inflight.get("invocation_id") != _invocation_id(
                        self.manifest, inflight["sequence"]):
                    raise LiveDevelopmentError("inflight identity differs from frozen row")
                expected_ids.add(inflight["invocation_id"])
            ledger = budget.snapshot()["invocations"]
            if set(ledger) != expected_ids or any(
                    ledger[_invocation_id(self.manifest, index)]["state"] != "settled"
                    for index in range(1, len(rows) + 1)):
                raise LiveDevelopmentError("campaign budget does not match completed rows")
            if state["status"] != "running":
                return state
            if state["inflight"] is not None and not self._finish(state, budget):
                return state
            while state["next_sequence"] <= len(self.manifest["rows"]):
                plan.validate_manifest(self.manifest, corpus=self.corpus,
                                       screen_run=self.screen_run,
                                       check_host=self.check_host)
                row = self.manifest["rows"][state["next_sequence"] - 1]
                actor = self._actor(row)
                invocation_id = _invocation_id(self.manifest, row["sequence"])
                if invocation_id in budget.snapshot()["invocations"]:
                    return self._block(state, "prior episode exists without a result", budget)
                try:
                    budget.reserve(invocation_id, row["maximum_usd"],
                                   row["maximum_usd"],
                                   {"manifest_sha256": self.manifest["manifest_sha256"],
                                    "sequence": row["sequence"], "arm": row["arm"]})
                except dispatch_budget.BudgetError as exc:
                    return self._block(state, f"campaign cannot reserve episode: {exc}", budget)
                token = digest({"episode": invocation_id})[:20]
                state["inflight"] = {"sequence": row["sequence"],
                                     "invocation_id": invocation_id,
                                     "root_id": f"episode_{token}",
                                     "authority_id": f"grant_{token}",
                                     "before": _public_hashes(actor)}
                _save(self.state_path, state)
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
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        parser.error("--execute is required; a manifest alone never launches workers")
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        approval = json.loads(args.approval.read_text(encoding="utf-8-sig"))
        result = LiveDevelopment(manifest, approval, args.output).run()
    except (OSError, ValueError, plan.DevelopmentError, LiveDevelopmentError) as exc:
        print(f"N5 development launch blocked: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": result["status"], "next_sequence": result["next_sequence"],
                      "completed_rows": len(result["rows"]),
                      "manifest_sha256": result["manifest_sha256"]}, sort_keys=True))
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
