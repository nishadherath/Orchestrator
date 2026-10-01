"""Shared, durable campaign admission and cancellation for Controller screens."""
from __future__ import annotations

import json
import math
from pathlib import Path

import evaluation_runner
import controller_evaluation
import route
from dispatch_budget import DispatchBudget


class CampaignStateError(ValueError):
    """A persisted Controller campaign cannot be trusted for admission."""


def load(path: Path) -> dict:
    """Validate the entire checkpoint before it can authorise another call."""
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        recorded = state.pop("state_sha256")
        valid = (state.get("schema_version") == 2
                 and state.get("status") in {"running", "stopped", "cancelled", "completed"}
                 and isinstance(state.get("manifest_sha256"), str)
                 and isinstance(state.get("episodes"), dict)
                 and (state.get("current") is None or isinstance(state["current"], dict))
                 and recorded == controller_evaluation.digest(state))
        state["state_sha256"] = recorded
        if not valid:
            raise ValueError("unsupported version, state or digest")
        return state
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CampaignStateError(
            f"campaign checkpoint {path} is invalid or legacy; preserve it for audit") from exc


def save(path: Path, state: dict) -> dict:
    """Persist a driver update without erasing a concurrent cancellation."""
    with route.ledger_lock(path):
        if path.is_file():
            recorded = load(path)
            if recorded.get("status") == "cancelled":
                state["status"] = "cancelled"
                state["stop_reason"] = recorded.get("stop_reason")
        state["state_sha256"] = controller_evaluation.digest(
            {key: value for key, value in state.items() if key != "state_sha256"})
        evaluation_runner.atomic_json(path, state)
    return state


def cancelled(path: Path) -> bool:
    """Read cancellation at an admission boundary."""
    with route.ledger_lock(path):
        return (path.is_file() and
                load(path).get("status") == "cancelled")


def cancel(run_root: Path) -> dict:
    """Record operator cancellation while a driver owns the campaign lock."""
    path = run_root / "state.json"
    with route.ledger_lock(path):
        if not path.is_file():
            raise ValueError(f"campaign state is absent at {path}; nothing to cancel")
        state = load(path)
        if state.get("status") == "completed":
            raise ValueError("completed campaign cannot be cancelled")
        state["status"] = "cancelled"
        state["stop_reason"] = "operator cancellation recorded; active calls may still bill"
        state["state_sha256"] = controller_evaluation.digest(
            {key: value for key, value in state.items() if key != "state_sha256"})
        evaluation_runner.atomic_json(path, state)
    current = state.get("current")
    if current:
        episode = run_root / current["episode_id"]
        if episode.is_symlink() or not episode.resolve().is_relative_to(run_root.resolve()):
            raise CampaignStateError("active episode path is redirected; preserve it")
        for budget_path in episode.rglob("task-budget.json"):
            if (budget_path.is_symlink()
                    or not budget_path.resolve().is_relative_to(episode.resolve())):
                raise CampaignStateError("active budget path is redirected; preserve it")
            DispatchBudget(budget_path, scope="task_dispatch").cancel()
        matrix_budget = episode / "budget.json"
        if matrix_budget.is_file():
            DispatchBudget(matrix_budget).cancel()
    return state


def reconcile(run_root: Path, manifest_sha256: str, *, kind: str) -> dict:
    """Project durable charges without admitting an invocation or grading output.

    A predecessor checkpoint may be read after its source changes, because
    reconciliation never executes that source. The manifest identity still
    binds the checkpoint to the operator's named campaign.
    """
    if kind not in {"matrix", "pilot"}:
        raise ValueError(f"unknown Controller campaign kind: {kind!r}")
    with route.ledger_lock(run_root / "campaign-driver.json", timeout_s=0.0):
        path = run_root / "state.json"
        state = load(path)
        if state["manifest_sha256"] != manifest_sha256:
            raise CampaignStateError("reconciliation manifest differs from checkpoint")
        known, held, unresolved = 0.0, 0.0, []
        budget_spend: dict[str, float] = {}
        prefix = f"{kind}-"
        for episode in sorted(run_root.iterdir()):
            if episode.is_symlink():
                raise CampaignStateError("campaign child path is redirected")
            if not episode.is_dir() or not episode.name.startswith(prefix):
                continue
            if kind == "matrix":
                budgets = [episode / "budget.json"] if (episode / "budget.json").exists() else []
            else:
                budgets = list(episode.rglob("task-budget.json"))
            if len(budgets) > 1:
                raise CampaignStateError("episode has competing root budgets")
            for budget_path in budgets:
                if (budget_path.is_symlink()
                        or not budget_path.resolve().is_relative_to(episode.resolve())):
                    raise CampaignStateError("episode budget path is redirected")
                snapshot = DispatchBudget(
                    budget_path, scope="controller_run" if kind == "matrix"
                    else "task_dispatch").snapshot()
                budget_spend[episode.name] = snapshot["spent_usd"]
                held += snapshot["reserved_usd"]
                unresolved.extend(f"{episode.name}/{ident}" for ident in snapshot["unresolved"])
        for episode_id, result in state["episodes"].items():
            if not isinstance(result, dict):
                raise CampaignStateError("persisted episode result is malformed")
            reported = result.get("cost_usd")
            if (type(reported) in (int, float) and math.isfinite(reported)
                    and reported >= 0):
                observed = budget_spend.get(episode_id)
                if observed is None or abs(observed - reported) > 1e-9:
                    unresolved.append(f"{episode_id}/cost-ledger-disagrees")
                budget_spend[episode_id] = max(observed or 0.0, reported)
        known = sum(budget_spend.values())
        if state["current"] is not None:
            active = state["current"]["episode_id"]
            unresolved.append(f"{active}/writer-status-unproved")
            if active not in budget_spend:
                # Without a ledger even the monetary hold is unknown.
                held = None
        state["known_spend_usd"] = round(known, 9)
        state["accounting"] = {"spent_usd": round(known, 9),
                               "reserved_usd": round(held, 9) if held is not None else None,
                               "unresolved": unresolved}
        if state["status"] == "running":
            state["status"] = "stopped"
            state["stop_reason"] = "reconciled checkpoint; explicit continuation required"
        return save(path, state)
