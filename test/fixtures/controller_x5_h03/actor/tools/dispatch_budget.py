"""Durable, per-run dispatch allowances. No provider or model calls.

The snapshot is the sole authority for dispatch. BudgetEntry JSONL is a
reporting projection, never a second balance. Money uses integer nanodollars
to avoid cumulative binary-float drift. Unknown terminal usage retains the
unspent part of its allowance until evidence explicitly settles it.
"""
from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

from route import _atomic_write_bytes, ledger_lock

SCALE = 1_000_000_000


class BudgetError(RuntimeError):
    """Invalid or inconsistent durable accounting; stop dispatch."""


class BudgetExhausted(BudgetError):
    """The run cannot fund another invocation."""


class InvocationAlreadyStarted(BudgetError):
    """An invocation ID cannot authorise the same side effect twice."""


def units(value: float, *, ceiling: bool = False) -> int:
    """Validate finite non-negative USD; round limits down and charges up."""
    if type(value) not in (int, float):
        raise BudgetError(f"Invalid USD amount {value!r}; supply a finite non-negative number")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise BudgetError(f"Invalid USD amount {value!r}; supply a finite non-negative number") from exc
    if isinstance(value, bool) or not amount.is_finite() or amount < 0:
        raise BudgetError(f"Invalid USD amount {value!r}; supply a finite non-negative number")
    return int((amount * SCALE).to_integral_value(rounding=ROUND_CEILING if ceiling else ROUND_FLOOR))


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class DispatchBudget:
    """Lock, read, validate, mutate and replace one human-readable snapshot.

    Reopening never resets balances or outstanding invocations. No age-based
    refund exists: a dead local process does not prove provider billing ended.
    The OS lock is shared by all instances, threads and processes.
    """

    def __init__(self, path: Path, limit_usd: float | None = None, *, scope: str = "controller_run"):
        if scope not in ("controller_run", "task_dispatch"):
            raise BudgetError("budget scope must be controller_run or task_dispatch")
        self.path = path.resolve()
        self.scope = scope
        with ledger_lock(self.path):
            if self.path.exists():
                state = self._read()
                if limit_usd is not None and state["limit_units"] != units(limit_usd):
                    raise BudgetError("Existing budget limit differs; reopen without changing its limit")
            elif limit_usd is None:
                raise BudgetError(f"No budget at {self.path}; legacy runs require explicit migration")
            else:
                self._write({"version": 1, "currency": "USD", "scope": scope,
                             "limit_units": units(limit_usd), "baseline_limit_units": units(limit_usd),
                             "cancelled": False,
                             "created_at": utc_now(), "invocations": {}})

    def _read(self) -> dict:
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            if (state["version"] != 1 or state["currency"] != "USD"
                    or state["scope"] != self.scope
                    or type(state["limit_units"]) is not int or state["limit_units"] < 0
                    or type(state["cancelled"]) is not bool
                    or not isinstance(state["invocations"], dict)):
                raise ValueError("invalid header")
            for ident, row in state["invocations"].items():
                if (not isinstance(ident, str) or not ident
                        or row["state"] not in ("reserved", "running", "uncertain", "settled")
                        or any(type(row[k]) is not int or row[k] < 0
                               for k in ("allowance_units", "charged_units"))
                        or row["allowance_units"] == 0
                        or not isinstance(row["metadata"], dict)
                        or (row["telemetry"] is not None and not isinstance(row["telemetry"], dict))
                        or (row["cost_usd"] is None and row["charged_units"] != 0)
                        or (row["cost_usd"] is not None and units(row["cost_usd"], ceiling=True) != row["charged_units"])
                        or (row["state"] == "settled" and row["cost_usd"] is None)):
                    raise ValueError(f"invalid invocation {ident!r}")
            if "baseline_limit_units" in state:
                baseline = state["baseline_limit_units"]
                if type(baseline) is not int or baseline < 0:
                    raise ValueError("invalid baseline limit")
                prior_limit = baseline
                amendments = state.get("amendments", [])
                if not isinstance(amendments, list):
                    raise ValueError("invalid amendment ledger")
                seen: set[str] = set()
                for generation, amendment in enumerate(amendments):
                    if (not isinstance(amendment, dict)
                            or type(amendment.get("previous_limit_units")) is not int
                            or amendment["previous_limit_units"] != prior_limit
                            or type(amendment.get("new_limit_units")) is not int
                            or amendment["new_limit_units"] <= prior_limit
                            or amendment.get("expected_generation") != generation
                            or not isinstance(amendment.get("authority_id"), str)
                            or not amendment["authority_id"]
                            or amendment["authority_id"] in seen):
                        raise ValueError("invalid amendment history")
                    seen.add(amendment["authority_id"])
                    prior_limit = amendment["new_limit_units"]
                if prior_limit != state["limit_units"] or state.get("generation", 0) != len(amendments):
                    raise ValueError("limit differs from amendment history")
            continuations = state.get("continuations", [])
            if (not isinstance(continuations, list)
                    or state.get("execution_generation", 0) != len(continuations)
                    or len({row.get("authority_id") for row in continuations if isinstance(row, dict)}) != len(continuations)):
                raise ValueError("invalid continuation history")
            return state
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise BudgetError(f"Unreadable budget {self.path}: {exc}; preserve it and reconcile from evidence") from exc

    def _write(self, state: dict) -> None:
        _atomic_write_bytes(self.path, (json.dumps(state, indent=2, allow_nan=False) + "\n").encode("utf-8"))

    @staticmethod
    def _totals(state: dict) -> tuple[int, int]:
        spent = sum(row["charged_units"] for row in state["invocations"].values())
        held = sum(max(0, row["allowance_units"] - row["charged_units"])
                   for row in state["invocations"].values() if row["state"] != "settled")
        return spent, held

    def snapshot(self) -> dict:
        with ledger_lock(self.path):
            state = self._read()
        spent, held = self._totals(state)
        return {**state, "limit_usd": state["limit_units"] / SCALE,
                "spent_usd": spent / SCALE, "reserved_usd": held / SCALE,
                "available_usd": max(0, state["limit_units"] - spent - held) / SCALE,
                "breached": spent + held > state["limit_units"],
                "unresolved": [key for key, row in state["invocations"].items()
                               if row["state"] != "settled"]}

    def remaining(self) -> float:
        state = self.snapshot()
        return 0.0 if state["cancelled"] or state["breached"] else state["available_usd"]

    def reserve(self, invocation_id: str, cap_usd: float, minimum_usd: float,
                metadata: dict) -> float:
        """Return a unique allowance, clamped to available funds under lock."""
        cap, minimum = units(cap_usd), units(minimum_usd, ceiling=True)
        if not isinstance(invocation_id, str) or not invocation_id or cap <= 0 or cap < minimum:
            raise BudgetError("Reservation needs a unique non-empty ID and 0 <= minimum <= positive cap")
        with ledger_lock(self.path):
            state = self._read()
            if invocation_id in state["invocations"]:
                raise InvocationAlreadyStarted(f"Invocation {invocation_id!r} already exists; inspect it, never redispatch it")
            spent, held = self._totals(state)
            allowance = min(cap, state["limit_units"] - spent - held)
            if state["cancelled"] or allowance <= 0 or allowance < minimum:
                raise BudgetExhausted(f"Available USD {max(0, allowance) / SCALE:.4f}; "
                                      f"needs USD {minimum / SCALE:.4f}, or run cancelled")
            state["invocations"][invocation_id] = {
                "state": "reserved", "allowance_units": allowance, "charged_units": 0,
                "cost_usd": None, "reserved_at": utc_now(), "metadata": metadata,
                "telemetry": None, "resolution": None,
            }
            self._write(state)
        return allowance / SCALE

    def start(self, invocation_id: str) -> None:
        """Persist dispatch intent before subprocess launch; at most once."""
        with ledger_lock(self.path):
            state = self._read()
            row = state["invocations"][invocation_id]
            if row["state"] != "reserved":
                raise InvocationAlreadyStarted(f"Invocation {invocation_id!r} is {row['state']}; refuse duplicate launch")
            spent, held = self._totals(state)
            if state["cancelled"] or spent + held > state["limit_units"]:
                raise BudgetExhausted("Run cancelled or budget breached before launch; reservation retained")
            row.update(state="running", started_at=utc_now())
            self._write(state)

    def settle(self, invocation_id: str, cost_usd: float | None, *, final: bool,
               telemetry: dict, evidence: str) -> None:
        """Idempotent reconciliation; partial telemetry never refunds a hold.

        A caller may finalise an uncertain charge only with terminal provider
        evidence. Larger-than-allowance charges are retained, making the breach
        visible and blocking further reservations rather than capping history.
        """
        charge = units(cost_usd, ceiling=True) if cost_usd is not None else 0
        if type(final) is not bool or not isinstance(telemetry, dict) or not isinstance(evidence, str) or not evidence.strip() or (final and cost_usd is None):
            raise BudgetError("Final settlement needs a known cost and an evidence reference")
        resolution = {"cost_usd": cost_usd, "final": final, "evidence": evidence,
                      "telemetry": telemetry}
        with ledger_lock(self.path):
            state = self._read()
            row = state["invocations"][invocation_id]
            if row["resolution"] == resolution:
                return
            if row["state"] == "settled" or charge < row["charged_units"]:
                raise BudgetError(f"Conflicting settlement for {invocation_id!r}; existing evidence retained")
            if row["resolution"] is not None:
                row.setdefault("prior_resolutions", []).append(row["resolution"])
            row.update(state="settled" if final else "uncertain", charged_units=charge,
                       cost_usd=cost_usd, telemetry=telemetry, resolution=resolution,
                       updated_at=utc_now())
            self._write(state)

    def cancel(self) -> None:
        """Stop new dispatch; already running or ambiguous work stays held."""
        with ledger_lock(self.path):
            state = self._read()
            state["cancelled"] = True
            self._write(state)

    def amend_limit(self, new_limit_usd: float, *, actor: str, authority_id: str,
                    reason: str, expected_generation: int) -> dict:
        """Increase a root limit with an idempotent, generation-fenced grant.

        The amendment ledger lives beside the original v1 fields so existing
        Controller readers retain their accounting and cancellation semantics.
        """
        proposed = units(new_limit_usd)
        if not all(isinstance(x, str) and x.strip() for x in (actor, authority_id, reason)):
            raise BudgetError("amendment requires actor, authority id and reason")
        if type(expected_generation) is not int or expected_generation < 0:
            raise BudgetError("invalid expected budget generation")
        with ledger_lock(self.path):
            state = self._read()
            amendments = state.setdefault("amendments", [])
            prior = next((row for row in amendments if row["authority_id"] == authority_id), None)
            request = {"new_limit_units": proposed, "actor": actor,
                       "authority_id": authority_id, "reason": reason,
                       "expected_generation": expected_generation}
            if prior:
                if all(prior.get(k) == v for k, v in request.items()):
                    return prior
                raise BudgetError("conflicting reuse of amendment authority")
            if expected_generation != state.get("generation", 0):
                raise BudgetError("stale budget generation")
            if proposed <= state["limit_units"]:
                raise BudgetError("budget amendments must increase the limit")
            row = {**request, "previous_limit_units": state["limit_units"],
                   "recorded_at": utc_now()}
            amendments.append(row)
            state["limit_units"] = proposed
            state["generation"] = expected_generation + 1
            self._write(state)
            return row

    def continue_generation(self, *, actor: str, authority_id: str,
                            predecessor_terminal: bool, writers_stopped: bool) -> dict:
        """Reopen cancellation only after all holds settle and writers stop."""
        if not actor or not authority_id or not predecessor_terminal or not writers_stopped:
            raise BudgetError("continuation needs authority, terminal predecessor and stopped writers")
        with ledger_lock(self.path):
            state = self._read()
            continuations = state.setdefault("continuations", [])
            prior = next((row for row in continuations if row["authority_id"] == authority_id), None)
            if prior:
                if (prior["actor"] == actor and not state["cancelled"]
                        and state.get("execution_generation", 0) == prior["generation"]):
                    return prior
                raise BudgetError("conflicting continuation authority")
            if not state["cancelled"] or any(row["state"] != "settled" for row in state["invocations"].values()):
                raise BudgetError("cancelled root has unresolved holds or is not cancelled")
            row = {"actor": actor, "authority_id": authority_id,
                   "generation": state.get("execution_generation", 0) + 1,
                   "recorded_at": utc_now()}
            continuations.append(row)
            state["execution_generation"] = row["generation"]
            state["cancelled"] = False
            self._write(state)
            return row
