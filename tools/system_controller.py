#!/usr/bin/env python3
"""The Controller: a deterministic state machine that runs SYSTEM.md's eight
steps in quick mode, in code, spawning cells via `claude -p` with role
briefs and a file-based blackboard (docs/PLAN.md Stage 10).

    python3 tools/system_controller.py --problem problem.md --project <consumer> --mode quick --record
    python3 tools/system_controller.py --project <consumer> --mode quick --dry-run
    python3 tools/system_controller.py --selftest

Responsible for: `runs/<id>/` inside `--project`, holding `ledger.jsonl`
(every content record, in order), `records/<id>.json` (one file per record,
for a human to open one directly), `budget.jsonl` (every `BudgetEntry`, kept
separate from the content ledger since it is accounting, not problem-solving
state), and `digests.md` (one rendered section per phase transition). The
Scribe validates and writes content. DispatchBudget owns durable admission
in dispatch-budget.json; budget.jsonl and budget-status.json are recoverable
reporting projections. See --recover-run for recovery without replay.

Deliberately does not: implement deep mode (task 10.4 is quick mode only;
`--mode` has one choice), run Instantiate (quick mode's stop rule is
paper falsification only, per `src/System/STEPS.md`), or read `ROUTING.md`'s
table (the fleet's cells are each role's own configured prior in
`ROLES.md`, not a routing decision; see `ROLES.md` rule 6).

The one non-obvious thing: `--json-schema` and `--max-budget-usd` (E25,
docs/FINDINGS.md) are real `claude -p` flags this module is the first to
use, and their live behaviour under `--output-format json` is unverified.
`_parse_schema_result()` below tries the shapes that seem most likely from
the flag's documented purpose (the schema-matching object as `result`
directly, or as a JSON string inside it) and raises with the raw payload
attached if none of them fit, so a live run fails loudly and legibly rather
than silently misreading a shape nobody has seen yet. This is the first
thing to check against Stage 10's live toy run.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import math
import re
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM = REPO_ROOT / "src" / "System"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import claudep  # noqa: E402
import acceptance as acceptance_lib  # noqa: E402
import validate_records  # noqa: E402
from dispatch_budget import BudgetError, BudgetExhausted, DispatchBudget, units  # noqa: E402
from route import _atomic_write_bytes, ledger_lock, LedgerLockTimeout  # noqa: E402
from system_prompts import OUTPUT_RULE, as_jsonl, role_section, schema_summary, technique_brief  # noqa: E402

# --------------------------------------------------------------------------
# Configuration: quick-mode cells (src/System/ROLES.md's quick-mode column)
# and the record-type ownership single-writer rule (ROLES.md's "Rules that
# bind every role", rule 2) both live here as data so the state machine
# below is a sequence of "call this role, write with this writer" steps and
# nothing more.

# (model, effort) per role, quick mode. Kept in step with ROLES.md by hand,
# same caveat role_probe.py's CELLS carries: these are priors, not
# measurements (docs/PLAN.md Stage 9.7's E24 measured their cost; Stage 11
# measures whether the fleet built from them beats B0).
QUICK_CELLS: dict[str, tuple[str, str]] = {
    "framer": ("opus", "high"),
    "verifier": ("sonnet", "medium"),
    "generator": ("sonnet", "high"),
    "critic": ("opus", "medium"),
    "selector": ("sonnet", "medium"),
    "librarian": ("sonnet", "medium"),
    "controller": ("sonnet", "low"),
}

TECHNIQUE_FAMILIES = ("subtract", "re-represent", "abduce")

# Which role may write which record type. CandidateRecord is split: the
# Framer writes exactly the technique="b0" candidate, a Generator writes any
# other technique. Enforced in Scribe.write() by comparing this table
# against the writer_role a caller declares, not by trusting a record's own
# claim about who wrote it (ROLES.md rule 2: single writer per record type).
TYPE_WRITER: dict[str, str] = {
    "ProblemRecord": "controller",
    "PremiseRecord": "framer",
    "FrameRecord": "framer",
    "CandidateRecord": "generator",  # special-cased for technique == "b0" in Scribe.write
    "MeasurementRecord": "verifier",
    "CritiqueRecord": "critic",
    "SelectionRecord": "selector",
    "EvaluationRecord": "verifier",
    "SolutionRecord": "librarian",
    "GapReport": "librarian",
    "PhaseDigest": "controller",
    "BudgetEntry": "controller",
}

ID_PREFIX: dict[str, str] = {
    "ProblemRecord": "prob", "PremiseRecord": "prem", "FrameRecord": "frame",
    "MeasurementRecord": "meas", "CandidateRecord": "cand", "CritiqueRecord": "crit",
    "SelectionRecord": "sel", "EvaluationRecord": "eval", "SolutionRecord": "sol",
    "GapReport": "gap", "PhaseDigest": "dig", "BudgetEntry": "bud",
}

MAX_PREMISES = 40          # ROLES.md, Framer contract
MAX_REFRAMES = 3           # STEPS.md Termination; SYSTEM.md's reframe cap
MAX_VERIFY_PASSES = 2      # quick mode: one pass, plus one more if Frame's
                           # update surfaces a newly-checkable premise
MAX_RECORD_RETRIES = 1     # bounded re-ask on a Scribe rejection (E24: roles
                           # slip on shape and length caps, not on content)
ROLE_CALL_FLOOR_USD = 0.50 # below this much budget left, no role is called:
                           # the cheapest role call (Select) measured USD 0.10
                           # to 0.23 and the dearest (Framer, Critic) up to
                           # 0.9, so a call could not finish and would only
                           # spend the remainder on a partial reply (D58)
ROLE_CALL_CAP_USD = 2.0    # Upper bound, clamped to the durable reservation.


class RoleCallFailed(RuntimeError):
    """A provider call failed after its telemetry was durably accounted."""


class RoleOutputMismatch(RuntimeError):
    """A role's own reply, after the one scripted retry, still does not
    contain exactly the record `_one_of()` needed (a FrameRecord, a B0
    candidate, and so on): the role's fault, not the Controller's own
    code. run_quick turns this into a gap report with `REPORT.md`
    written, the same as `BudgetExhausted`, rather than the traceback it
    was before (audit A15, docs/AUDIT-2026-09-16.md). Kept distinct from
    a bare RuntimeError deliberately: the three internal invariant
    checks on a code-written record (ProblemRecord, SolutionRecord,
    GapReport) below stay loud raises, since those indicate a defect in
    this script's own code, not a recoverable role failure, and must not
    be swallowed into a plausible-looking "gap" outcome."""


# --------------------------------------------------------------------------
# The Scribe (task 10.3): validates, assigns ids, enforces single writer and
# ledger-version freshness, and is the only thing that touches runs/<id>/.

class RunDirs:
    def __init__(self, root: Path):
        self.root = root
        self.ledger = root / "ledger.jsonl"
        self.budget = root / "budget.jsonl"
        self.digests = root / "digests.md"
        self.records = root / "records"
        self.rejections = root / "rejections.jsonl"
        self.report = root / "REPORT.md"

    def create(self) -> None:
        self.root.mkdir(parents=True, exist_ok=False)
        self.records.mkdir()
        self.digests.write_text("# Run digests\n\n", encoding="utf-8", newline="\n")


@dataclasses.dataclass
class ScribeRejection:
    record: dict
    reasons: list[str]


class Scribe:
    """Owns id assignment, schema validation, single-writer enforcement and
    ledger-version freshness for one run. `write()` is the only way a phase
    puts a content record on the blackboard. Live budget records are a
    separate projection owned by export_budget, with their own ID prefix."""

    def __init__(self, dirs: RunDirs):
        self.dirs = dirs
        self.schemas = validate_records.load_schemas()
        self._counters: dict[str, int] = {}
        self._known_ids: set[str] = set()
        self._ledger_records: list[dict] = []   # accepted content records, in order
        self.frozen_version = 0

    def _next_id(self, record_type: str) -> str:
        prefix = ID_PREFIX[record_type]
        self._counters[prefix] = self._counters.get(prefix, 0) + 1
        return f"{prefix}-{self._counters[prefix]:03d}"

    def write(self, records: list[dict], *, writer_role: str, expected_types: set[str]) -> tuple[list[dict], list[ScribeRejection]]:
        """Validate and, for each record that passes, assign it a fresh id
        (discarding whatever id the writer proposed: with parallel
        Generators this is the only thing that prevents an id collision)
        and append it to the ledger (or the budget log for BudgetEntry).

        Rejects, without raising, a record whose type is not in
        `expected_types`, whose type's owning role is not `writer_role`
        (single-writer), or whose `ledger_version` is not the frozen one
        (for CandidateRecord only, per the Scribe's stale-version rule;
        every other type is version-tagged for provenance, not gated on
        it). Schema validation (field shapes, caps, enums, references)
        runs after those structural checks. The caller decides what a
        rejection means for its phase; the Scribe only reports it.

        Ids are assigned to the whole batch before any of it is validated.
        This is not enough on its own to make a within-batch forward
        reference resolve (a FrameRecord's `b0_candidate_id` naming the
        CandidateRecord it was written alongside, say): a live run
        (2026-09-14) showed the writer has no way to know in advance what
        id the Scribe will assign, so its own guess almost never matches,
        even when the writer is internally consistent about that guess
        (and it was not always: one reply's `b0_candidate_id` did not even
        match the `id` its own accompanying CandidateRecord claimed). So
        every reference field this batch's records carry (`references`,
        plus each type's field named in `validate_records.REF_FIELDS`) is
        rewritten first, replacing any value that matches a raw id from
        this same batch with the id the Scribe actually assigned it. A
        value that is not one of this batch's raw ids (an id from the
        existing ledger, or simply wrong) is left alone, so a genuine
        dangling reference still gets caught by validation below.

        Each record's references are then checked against the ledger plus
        every id in this batch, whether or not that batch-mate itself goes
        on to pass its own validation; a record whose only problem is a
        reference to a batch-mate that gets rejected is a known, accepted
        simplification, not a case this method resolves to a fixed
        point."""
        candidates: list[dict] = []
        rejected: list[ScribeRejection] = []
        id_map: dict[str, str] = {}
        for raw in records:
            reasons = self._check_ownership(raw, writer_role, expected_types)
            if reasons:
                rejected.append(ScribeRejection(raw, reasons))
                continue
            record = dict(raw)
            new_id = self._next_id(record["type"])
            if isinstance(raw.get("id"), str) and raw["id"] != new_id:
                id_map[raw["id"]] = new_id
            record["id"] = new_id
            candidates.append(record)

        if id_map:
            for record in candidates:
                if isinstance(record.get("references"), list):
                    record["references"] = [id_map.get(r, r) for r in record["references"]]
                for field in validate_records.REF_FIELDS.get(record["type"], []):
                    if record.get(field) in id_map:
                        record[field] = id_map[record[field]]

        accepted: list[dict] = []
        for record in candidates:
            # Validate against every OTHER record in this batch (not itself,
            # which would otherwise collide with itself on the duplicate-id
            # check below).
            other_batch = [("batch", r) for r in candidates if r["id"] != record["id"]]
            reasons = self._validate(record, extra_context=other_batch)
            if reasons:
                rejected.append(ScribeRejection(record, reasons))
                continue
            self._known_ids.add(record["id"])
            if record["type"] == "BudgetEntry":
                self._append_jsonl(self.dirs.budget, record)
            else:
                self._ledger_records.append(record)
                self._append_jsonl(self.dirs.ledger, record)
                if record["type"] == "FrameRecord":
                    self.frozen_version = record["ledger_version"]
            (self.dirs.records / f"{record['id']}.json").write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            accepted.append(record)
        if rejected:
            self._log_rejections(rejected, writer_role)
        return accepted, rejected

    def _log_rejections(self, rejected: list["ScribeRejection"], writer_role: str) -> None:
        """A rejection is not a crash, but it should never be silent: without
        this, the only trace of what a role actually returned is the count in
        _one_of's RuntimeError, and a live run's first FrameRecord rejection
        (2026-09-14) had to be re-run blind to find out why. Appended
        regardless of whether the caller retries or gives up."""
        with self.dirs.rejections.open("a", encoding="utf-8") as f:
            for rej in rejected:
                f.write(json.dumps({"writer_role": writer_role, "record": rej.record, "reasons": rej.reasons},
                                    ensure_ascii=False) + "\n")

    def _check_ownership(self, record: dict, writer_role: str, expected_types: set[str]) -> list[str]:
        rtype = record.get("type")
        reasons = []
        if rtype not in expected_types:
            reasons.append(f"type {rtype!r} is not one of the types this phase may write ({sorted(expected_types)})")
            return reasons
        if rtype == "CandidateRecord":
            owner = "framer" if record.get("technique") == "b0" else "generator"
        else:
            owner = TYPE_WRITER.get(rtype)
        if owner != writer_role:
            reasons.append(f"type {rtype!r} is owned by {owner!r}, not {writer_role!r} (single-writer rule)")
        if rtype == "CandidateRecord" and record.get("technique") != "b0" and self.frozen_version \
                and record.get("ledger_version") != self.frozen_version:
            reasons.append(f"cites ledger_version {record.get('ledger_version')}, frozen version is {self.frozen_version}")
        return reasons

    def _validate(self, record: dict, extra_context: list[tuple[str, dict]] = ()) -> list[str]:
        context = [("ledger", r) for r in self._ledger_records] + list(extra_context)
        problems = validate_records.validate_ledger(context + [("candidate", record)], self.schemas, strict=False)
        return [p.split(": ", 1)[1] if p.startswith("candidate:") else p for p in problems if p.startswith("candidate:")]

    def _append_jsonl(self, path: Path, record: dict) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def premises(self, version: int | None = None) -> list[dict]:
        v = self.frozen_version if version is None else version
        latest: dict[str, dict] = {}
        for r in self._ledger_records:
            if r["type"] == "PremiseRecord" and r["ledger_version"] <= v:
                latest[r.get("supersedes") or r["id"]] = r
        return list(latest.values())

    def latest(self, record_type: str) -> dict | None:
        for r in reversed(self._ledger_records):
            if r["type"] == record_type:
                return r
        return None

    def all_of(self, record_type: str) -> list[dict]:
        return [r for r in self._ledger_records if r["type"] == record_type]


# --------------------------------------------------------------------------
# Role runners: the abstraction that lets --selftest exercise the whole
# state machine with zero `claude -p` calls (task 10.6), and a live run use
# the real thing.

@dataclasses.dataclass
class RoleReply:
    records: list[dict]
    budget_entry: dict | None   # None for the fake runner's zero-cost calls
    unparsed: list[str] = dataclasses.field(default_factory=list)  # lines that failed to parse as JSON


class RoleRunner(Protocol):
    def __call__(self, phase: str, role: str, prompt: str, *, timeout: float) -> RoleReply: ...

    def classify(self, phase: str, prompt: str, schema: dict, default: dict) -> tuple[dict, dict | None]: ...


class LiveRoleRunner:
    """Invokes `claude -p` for the named role at its quick-mode cell,
    durably accounts for each invocation and parses JSON Lines.
    Does not validate content against the schemas; the
    Scribe does that on write().

    `classify()` is the two Controller calls (task 10.5): a
    `--json-schema`-forced call at `worker-sonnet-low`, falling back to
    `default` on any failure (a bad shape, an exception, an empty budget)
    rather than blocking the run over a classification the pipeline can
    proceed without."""

    def __init__(self, project: Path, remaining_budget: Callable[[], float], *,
                 budget: DispatchBudget | None = None, max_output_tokens: int | None = 8192,
                 permission_args: tuple[str, ...] | None = None,
                 extra_args: tuple[str, ...] = (), stream_json: bool = False,
                 require_identity: bool = False):
        self.project = project
        self.remaining_budget = remaining_budget
        self.budget = budget  # run_quick binds this before any live dispatch.
        self.max_output_tokens = max_output_tokens
        self.permission_args = (tuple(claudep.FORWARDER_PERMISSION_ARGS)
                                if permission_args is None else permission_args)
        self.extra_args = extra_args
        self.stream_json = stream_json
        self.require_identity = require_identity
        self.deadline: float | None = None

    @staticmethod
    def _identity(model: str, result: claudep.ClaudeCallResult | None) -> dict:
        expected = {"sonnet": "claude-sonnet-5", "opus": "claude-opus-5"}.get(model)
        extras = result.extras if result else {}
        root_models = extras.get("root_models") if isinstance(extras.get("root_models"), list) else []
        child_models = extras.get("child_models") if isinstance(extras.get("child_models"), list) else []
        actual = root_models[0] if len(root_models) == 1 else None
        return {
            "expected_model": expected, "actual_model": actual,
            "identity_valid": actual == expected and not child_models,
            "root_models": root_models, "child_models": child_models,
            "billed_models": extras.get("billed_models", []),
            "auxiliary_billed_models": extras.get("auxiliary_billed_models", []),
        }

    def _invoke(self, phase: str, role: str, prompt: str, *, timeout: float,
                schema: dict | None = None) -> tuple[claudep.ClaudeCallResult, str]:
        if self.budget is None:
            raise BudgetError("LiveRoleRunner needs a durable budget; use run_quick or pass budget=")
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        if self.max_output_tokens is not None and (type(self.max_output_tokens) is not int or self.max_output_tokens <= 0):
            raise ValueError("max_output_tokens must be a positive integer")
        if self.deadline is not None:
            timeout = min(timeout, self.deadline - time.monotonic())
            if timeout <= 0:
                raise BudgetExhausted("Elapsed run limit reached; no further call dispatched")
        model, effort = QUICK_CELLS[role]
        ident = uuid.uuid4().hex
        cap = min(0.10 if schema is not None else ROLE_CALL_CAP_USD, self.remaining_budget())
        minimum = 0.0 if schema is not None else ROLE_CALL_FLOOR_USD
        if cap <= 0 or cap < minimum:
            raise BudgetExhausted(f"USD {max(0, cap):.4f} available; no {role} call dispatched")
        allowance = self.budget.reserve(ident, cap, minimum, {
            "phase": _PHASE_ALIASES.get(phase, phase), "role": role,
            "cell": f"worker-{model}-{effort}", "timeout_s": timeout,
            "max_output_tokens": self.max_output_tokens,
        })
        self.budget.start(ident)
        # Admission may have waited for a competing writer. Recheck before
        # launch; at this point zero cost is provable because no child exists.
        if self.deadline is not None:
            timeout = min(timeout, self.deadline - time.monotonic())
            if timeout <= 0:
                self.budget.settle(ident, 0.0, final=True, telemetry={"status": "not_launched"},
                                   evidence="elapsed-deadline-before-subprocess")
                raise BudgetExhausted("Elapsed run limit reached before launch; unused allowance released")
        try:
            result = claudep.call_claude(
                prompt, cwd=self.project, model=model, effort=effort,
                permission_args=self.permission_args if schema is None else (),
                extra_args=self.extra_args,
                json_schema=schema, max_budget_usd=allowance, timeout=timeout,
                max_output_tokens=self.max_output_tokens, stream_json=self.stream_json)
        except BaseException as exc:
            partial = exc.partial if isinstance(exc, claudep.ClaudeCallError) else None
            # A timeout, cancellation or malformed/lost response is not proof
            # of final billing. Keep the remaining allowance even with a known
            # partial charge. Only a terminal result envelope can release it.
            final = bool(partial and partial.raw.get("type") == "result"
                         and partial.cost_usd is not None
                         and not isinstance(exc.__cause__, subprocess.TimeoutExpired))
            self._account(ident, partial, final=final, status="failed", error=str(exc)[:500],
                          identity=self._identity(model, partial))
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            raise RoleCallFailed(f"{role} invocation {ident} failed; usage recorded: {exc}") from exc
        identity = self._identity(model, result)
        self._account(ident, result, final=result.cost_usd is not None, status="completed",
                      identity=identity)
        if self.require_identity and not identity["identity_valid"]:
            raise RoleCallFailed(
                f"{role} invocation {ident} served {identity['root_models']!r}; "
                f"expected {identity['expected_model']!r}; usage recorded")
        return result, ident

    def _account(self, ident: str, result: claudep.ClaudeCallResult | None, *,
                 final: bool, status: str, error: str = "", identity: dict | None = None) -> None:
        cost = result.cost_usd if result else None
        try:
            if cost is not None:
                units(cost, ceiling=True)
        except BudgetError:
            cost, final = None, False
            error = "Invalid provider cost; reconcile from final evidence"
        # Provider metadata is untrusted. A malformed token count must not
        # prevent a known cost from reaching the durable accounting record.
        raw_usage = result.extras.get("usage") if result else None
        usage = {key: value if type(value) is int and value >= 0 else None
                 for key, value in raw_usage.items()} if isinstance(raw_usage, dict) else None
        elapsed = result.elapsed_s if result else None
        if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
            elapsed = None
        telemetry = {"status": status, "error": error,
                     "wall_clock_s": elapsed,
                     "usage": usage,
                     "result": result.result if result else None,
                     "identity": identity}
        self.budget.settle(ident, cost, final=final, telemetry=telemetry,
                           evidence="terminal-result" if final else "incomplete-usage")

    def __call__(self, phase: str, role: str, prompt: str, *, timeout: float) -> RoleReply:
        result, ident = self._invoke(phase, role, prompt, timeout=timeout)
        records, unparsed = _parse_jsonl_reply(result.result)
        # BudgetEntry is projected from the durable snapshot at finish/recovery;
        # returning another charge here would create a second cost owner.
        return RoleReply(records=records, budget_entry=None, unparsed=unparsed)

    def classify(self, phase: str, prompt: str, schema: dict, default: dict) -> tuple[dict, dict | None]:
        try:
            result, ident = self._invoke(phase, "controller", prompt, timeout=120, schema=schema)
        except (BudgetExhausted, RoleCallFailed):
            return default, None
        try:
            return _parse_schema_result(result, schema), None
        except RuntimeError:
            return default, None


class FakeRoleRunner:
    """--selftest's role runner: returns a caller-supplied script of replies
    keyed by (phase, role) in call order, with no subprocess call. A
    `NamedTuple`-free stand-in is enough since the script is small and
    entirely test-local. `classify()` reads from the same script under the
    key `(phase, "controller")`, or returns `default` if nothing was
    scripted for it, so a scenario that does not care about the
    classification result need not script one."""

    def __init__(self, script: dict[tuple[str, str], list[list[dict]]], classify_script: dict[str, dict] | None = None):
        self.script = {k: list(v) for k, v in script.items()}
        self.classify_script = dict(classify_script or {})
        self.calls: list[tuple[str, str]] = []

    def __call__(self, phase: str, role: str, prompt: str, *, timeout: float) -> RoleReply:
        self.calls.append((phase, role))
        queue = self.script.get((phase, role))
        if not queue:
            raise AssertionError(f"selftest script exhausted for (phase={phase!r}, role={role!r})")
        records = queue.pop(0)
        return RoleReply(records=records, budget_entry=None)

    def classify(self, phase: str, prompt: str, schema: dict, default: dict) -> tuple[dict, dict | None]:
        self.calls.append((phase, "controller"))
        return self.classify_script.get(phase, default), None


def _parse_jsonl_reply(text: str) -> tuple[list[dict], list[str]]:
    """Parse a reply as a sequence of JSON objects, using
    `JSONDecoder.raw_decode()` to find each object's end rather than
    splitting on newlines and calling `json.loads()` per line.

    A naive per-line split silently dropped every record in a live run
    (2026-09-14): OUTPUT_RULE asks for one JSON object per line, the
    Framer complied for its short PremiseRecords but pretty-printed its
    much longer FrameRecord across several lines, and every one of those
    lines failed `json.loads()` on its own and was skipped without a
    trace, taking the run's only FrameRecord with it. `raw_decode` consumes
    a complete object regardless of embedded newlines, so this shape parses
    correctly instead of silently vanishing. Also tolerates a code fence
    OUTPUT_RULE forbade but a role sometimes sends anyway.

    Returns `(records, unparsed_fragments)`: the second list is what did
    not parse, one entry per line skipped, so a caller can log it instead
    of it disappearing the way it did before this fix."""
    decoder = json.JSONDecoder()
    records: list[dict] = []
    unparsed: list[str] = []
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        if text[i] == "`":
            nl = text.find("\n", i)
            i = n if nl == -1 else nl + 1
            continue
        nl = text.find("\n", i)
        line_end = n if nl == -1 else nl
        if text[i] != "{":
            # raw_decode accepts any JSON value, and a numbered list's "1."
            # parses as the integer 1, which crashed the Scribe live (D56).
            # Only an object can be a record, so anything before the line's
            # first "{" is reported as a fragment and parsing resumes there;
            # a line with no "{" at all is reported whole.
            brace = text.find("{", i, line_end)
            fragment = text[i:brace if brace != -1 else line_end].strip()
            if fragment:
                unparsed.append(fragment)
            i = brace if brace != -1 else line_end + 1
            continue
        try:
            obj, end = decoder.raw_decode(text, i)
            records.append(obj)
            i = end
        except json.JSONDecodeError:
            fragment = text[i:line_end].strip()
            if fragment:
                unparsed.append(fragment)
            i = line_end + 1
    return records, unparsed


def _parse_schema_result(res: claudep.ClaudeCallResult, schema: dict) -> dict:
    """Tolerant parse for a --json-schema call's result (E25: unverified
    shape). Tries, in order: `result` already a dict matching the schema's
    top-level keys; `result` as a JSON string; the raw response envelope
    itself. Raises with the raw payload attached if none fit, so a live
    run fails loudly rather than silently misreading an unfamiliar shape."""
    candidates = [res.raw.get("structured_output"), res.raw.get("result"), res.raw]
    for candidate in candidates:
        if isinstance(candidate, str):
            try:
                candidate = json.loads(candidate)
            except json.JSONDecodeError:
                continue
        if isinstance(candidate, dict) and set(schema.get("required", [])) <= set(candidate):
            return candidate
    raise RuntimeError(f"--json-schema reply matched none of the expected shapes; raw response: {res.raw!r}")


# --------------------------------------------------------------------------
# Prompt builders. The four record-writing roles use ROLES.md's own section
# plus a compact schema summary and OUTPUT_RULE's JSONL convention (E24:
# 19 of 20 records schema-valid at first attempt this way). The two
# Controller calls are schema-forced (E25) and do not use ROLES.md, since
# they are not one of the six roles it defines.

def build_frame_prompt(problem: dict, prior_measurements: list[dict], prior_ledger: list[dict],
                        falsifying_critiques: list[dict] = ()) -> str:
    brief = role_section("Framer")
    catalogue = "empty (first run of the day; no library persists across runs in this Stage 10 build)."
    body = [brief, schema_summary("PremiseRecord", "FrameRecord", "CandidateRecord")]
    if prior_ledger:
        reason = ("Verify found new measurements" if prior_measurements
                   else "a Critique found a ledger premise false (falsifying_premise_claims below)")
        body.append(f"Prior ledger, for re-entry ({reason}; produce the next PremiseRecords with "
                     "`supersedes` set for any that changed class, and one new FrameRecord; do not "
                     "re-emit the B0 candidate):\n" + as_jsonl(prior_ledger))
        if prior_measurements:
            body.append("New measurements since the last freeze:\n" + as_jsonl(prior_measurements))
        if falsifying_critiques:
            body.append("Critiques claiming a ledger premise is false:\n" + as_jsonl(falsifying_critiques))
        body.append("Produce ledger version " + str(_next_version(prior_ledger)) + f". Copy `b0_candidate_id` "
                     "verbatim from the prior FrameRecord above; it is not being re-assigned.")
    else:
        body.append("False-premise catalogue: " + catalogue)
        body.append("Input slice (the ProblemRecord):\n" + as_jsonl([problem]))
        body.append("Produce ledger version 1: every PremiseRecord, one FrameRecord, and the B0 CandidateRecord. "
                     "The `id` you give the B0 CandidateRecord and the `b0_candidate_id` you give the FrameRecord "
                     "must be the exact same string: whichever of the two you write first, copy it into the other "
                     "field rather than choosing separately. B0 takes every stated constraint at face value, "
                     "including one you have just classified as policy or falsified: B0's `premise_operation` is "
                     "`none` and its mechanism does not remove, re-represent or add anything. A candidate that acts "
                     "on your own finding that a constraint's reason is false belongs in Generate, under a real "
                     "technique, once the pipeline gets there, not folded into B0.")
    return "\n\n".join(body) + OUTPUT_RULE


def _next_version(ledger: list[dict]) -> int:
    frames = [r["ledger_version"] for r in ledger if r["type"] == "FrameRecord"]
    return (max(frames) if frames else 0) + 1


def build_verify_prompt(problem: dict, premise: dict, project: Path) -> str:
    brief = role_section("Verifier")
    return (brief + "\n\n" + schema_summary("MeasurementRecord")
            + "\n\nInput slice (one premise to measure, and the problem's context):\n"
            + as_jsonl([problem, premise])
            + f"\n\nWorking directory: `{project}`. Quick mode: one tool call, no new code. "
              "Run the premise's cheapest_verification and write one MeasurementRecord with the "
              "artefact path or excerpt you read the result from."
            + OUTPUT_RULE)


def build_generate_prompt(family: str, ledger: list[dict], patterns: list[dict]) -> str:
    brief = role_section("Generator (template; the technique family is the parameter)")
    brief_text = technique_brief(family)
    patterns_text = ("No retrieved patterns; the library is empty." if not patterns
                      else "Retrieved patterns (at most three):\n" + as_jsonl(patterns))
    return (brief + "\n\nYour technique brief:\n" + brief_text + "\n\n" + schema_summary("CandidateRecord")
            + "\n\nInput slice (the frozen ledger, including B0):\n" + as_jsonl(ledger)
            + "\n\n" + patterns_text
            + "\n\nApply the brief against this ledger. Emit CandidateRecords, or none if the trigger "
              "question has no answer here."
            + OUTPUT_RULE)


def build_critique_prompt(ledger: list[dict], candidates: list[dict]) -> str:
    brief = role_section("Critic")
    return (brief + "\n\n" + schema_summary("CritiqueRecord")
            + "\n\nInput slice (the frozen ledger, and the tier's candidates including B0):\n"
            + as_jsonl(ledger + candidates)
            + "\n\nWrite one CritiqueRecord per candidate."
            + OUTPUT_RULE)


def build_select_prompt(candidates: list[dict], critiques: list[dict], acceptance: list[str], baseline_id: str) -> str:
    brief = role_section("Selector")
    return (brief + "\n\n" + schema_summary("SelectionRecord")
            + "\n\nAcceptance criteria:\n" + "\n".join(f"- {c}" for c in acceptance)
            + "\n\nBaseline candidate id (B0): " + baseline_id
            + "\n\nCandidates and their critiques:\n" + as_jsonl(candidates + critiques)
            + "\n\nWrite one SelectionRecord."
            + OUTPUT_RULE)


STABILITY_SCHEMA = {"type": "object", "additionalProperties": False,
                    "properties": {"stable": {"type": "boolean"}, "reasoning": {"type": "string", "maxLength": 300}},
                    "required": ["stable", "reasoning"]}

FAMILIES_SCHEMA = {"type": "object", "additionalProperties": False,
                   "properties": {"families": {"type": "array", "items": {"enum": list(TECHNIQUE_FAMILIES)}},
                                  "reasoning": {"type": "string", "maxLength": 300}},
                   "required": ["families", "reasoning"]}


def build_stability_prompt(premises: list[dict], frame: dict) -> str:
    return ("Classification only, no other output. Given this ledger's premises and the Framer's own "
            "FrameRecord, has the premise set stopped changing class since the last freeze (stable "
            "enough to move to Generate), or does at least one premise still warrant another verify "
            "pass within the mode's ceiling?\n\nPremises:\n" + as_jsonl(premises)
            + "\n\nFrameRecord (its own `stable` field is one input, not the answer; classify "
              "independently):\n" + as_jsonl([frame]))


def build_families_prompt(problem: dict, frame: dict) -> str:
    return ("Classification only, no other output. Given this problem and its FrameRecord, which of "
            "the three tier-1 technique families (subtract, re-represent, abduce) are plausibly "
            "applicable? Quick mode's default is all three; name fewer only when a family's trigger "
            "question plainly does not apply.\n\nProblem:\n" + as_jsonl([problem])
            + "\n\nFrameRecord:\n" + as_jsonl([frame]))


# --------------------------------------------------------------------------
# Digests (code, not a model; SYSTEM.md section 6, "the only summarisation
# in the system", and it must stay that way: this function has no model
# call in it, deliberately.)

# PhaseDigest.phase is an enum of SYSTEM.md's eight canonical steps; several
# of this Controller's own internal transitions (the two schema-forced
# classification calls, a mid-cycle reframe) are not one of the eight by
# name, so they map onto the step they belong to. digests.md and the
# `text` field keep the finer-grained label; only the schema-facing
# `phase` field is canonicalised.
_PHASE_ALIASES = {"controller-stability": "verify", "controller-families": "verify", "reframe": "frame"}


def write_digest(scribe: Scribe, dirs: RunDirs, phase: str, text: str, records_written: list[dict],
                  trimmed: list[str] = ()) -> dict:
    assert len(text) <= 1200, f"digest for {phase!r} is {len(text)} chars, over the 300-token-ish cap"
    record = {"type": "PhaseDigest", "phase": _PHASE_ALIASES.get(phase, phase), "text": text,
              "records_written": [r["id"] for r in records_written], "trimmed": list(trimmed),
              "ledger_version": scribe.frozen_version, "references": [r["id"] for r in records_written]}
    accepted, rejected = scribe.write([record], writer_role="controller", expected_types={"PhaseDigest"})
    assert not rejected, f"digest record rejected: {rejected}"
    with dirs.digests.open("a", encoding="utf-8") as f:
        f.write(f"## {phase}\n\n{text}\n\n")
    return accepted[0]


def write_report(dirs: RunDirs, scribe: Scribe, outcome: str, record: dict, cost_usd: float, calls: int) -> None:
    """`REPORT.md`: SYSTEM.md section 8's quick-mode output ("best plus ranked
    alternatives plus explicit unverified-premise list"), rendered from the
    ledger by code. This is the artefact a caller hands on (docs/PLAN.md
    Stage 12's worker brief returns it; Stage 11's fleet harness gives it to
    the instantiating cell, D55). Nothing here is judged; every line is a
    record's field, so the report can be checked against the ledger."""
    frame = scribe.latest("FrameRecord")
    premises = sorted(scribe.premises(), key=lambda p: p["id"])
    lines = [f"# Controller report, {dirs.root.name}", "",
             f"Outcome: {outcome}. Mode: quick. Calls: {calls}. Cost: USD {cost_usd:.4f}. "
             f"Ledger frozen at v{scribe.frozen_version}.", ""]
    if outcome == "solution":
        lines += ["## Answer", "", record["answer"], "",
                  f"Technique: {record['technique']}. Candidate: {record['candidate_id']}. "
                  f"Problem type: {record['problem_type']}.", ""]
    else:
        lines += ["## No solution", "", f"Termination: {record.get('termination', outcome)}.",
                  f"Next cheapest test: {record.get('next_cheapest_test', 'none')}", ""]
    if frame:
        lines += ["## Acceptance criteria", ""] + [f"- {c}" for c in frame["acceptance_criteria"]] + [""]
    lines += ["## Premise ledger", "", "Every premise at the frozen version, with the class verification left it in.", ""]
    lines += [f"- {p['id']} [{p['class']}, confidence {p['confidence']}]: {p['text']}" for p in premises] + [""]
    unverified_lb = [p for p in premises if p["class"] == "unverified" and p.get("load_bearing")]
    lines += ["## Unverified load-bearing premises", ""]
    lines += ([f"- {p['id']}: {p['text']} (cheapest verification: {p['cheapest_verification']})" for p in unverified_lb]
              or ["- none"]) + [""]
    selection = scribe.latest("SelectionRecord")
    candidates = {c["id"]: c for c in scribe.all_of("CandidateRecord")}
    lines += ["## Ranked alternatives", ""]
    if selection and selection["shortlist"]:
        for entry in sorted(selection["shortlist"], key=lambda e: e["rank"]):
            cand = candidates.get(entry["candidate_id"], {})
            lines.append(f"- {entry['rank']}. {entry['candidate_id']} ({cand.get('technique', '?')}, score "
                         f"{entry['score']}): {entry['basis']}")
    else:
        lines.append("- none shortlisted above the baseline")
    if selection:
        lines += [f"- excluded: {e['candidate_id']} ({e['reason']})" for e in selection["excluded"]]
    lines += ["", "## Audit trail", "", " -> ".join(record.get("audit_trail", [])) or "(none)", ""]
    dirs.report.write_text("\n".join(lines), encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------
# The state machine (task 10.4): Intake, Frame, the Verify loop, the two
# Controller calls (task 10.5), Generate (parallel), Critique (blind),
# Select, Close. No Instantiate: quick mode is paper falsification only.

class ReframeCapExceeded(Exception):
    pass


@dataclasses.dataclass
class RunResult:
    outcome: str  # "solution" | "gap" | "dissolved"
    record: dict
    run_dir: Path
    total_cost_usd: float
    calls: int
    reserved_usd: float = 0.0
    accounting_complete: bool = True


def export_budget(budget: DispatchBudget, dirs: RunDirs) -> dict:
    """Rebuild reporting artefacts from the sole dispatch authority.

    Atomic replacement makes recovery repeatable after a crash between the
    accounting write and the reporting write. Null stays null; the report's
    spent number is a known subtotal when any invocation is unresolved.
    """
    snapshot = budget.snapshot()
    rows = []
    for index, (ident, row) in enumerate(snapshot["invocations"].items(), 1):
        meta, telemetry = row["metadata"], row.get("telemetry") or {}
        usage = telemetry.get("usage") or {}
        rows.append({"type": "BudgetEntry", "id": f"bud-{index:03d}",
                     "ledger_version": 0, "references": [],
                     "phase": meta["phase"], "role": meta["role"], "cell": meta["cell"],
                     "cost_usd": row["cost_usd"], "tokens_in": usage.get("input_tokens"),
                     "tokens_out": usage.get("output_tokens"),
                     "wall_clock_s": telemetry.get("wall_clock_s"),
                     "invocation_id": ident, "accounting_status": row["state"],
                     "reserved_usd": max(0, row["allowance_units"] - row["charged_units"]) / 1e9
                     if row["state"] != "settled" else 0.0})
    for row in rows:
        _atomic_write_bytes(dirs.records / f"{row['id']}.json", (json.dumps(row, indent=2) + "\n").encode("utf-8"))
    _atomic_write_bytes(dirs.budget, "".join(json.dumps(row) + "\n" for row in rows).encode("utf-8"))
    summary = {key: snapshot[key] for key in ("scope", "limit_usd", "spent_usd", "reserved_usd",
                                             "available_usd", "breached", "cancelled", "unresolved")}
    summary["accounting_complete"] = not snapshot["unresolved"]
    summary["calls"] = len(rows)
    _atomic_write_bytes(dirs.root / "budget-status.json", (json.dumps(summary, indent=2) + "\n").encode("utf-8"))
    return summary


def write_run_status(dirs: RunDirs, execution_status: str, outcome: str | None,
                     error: str | None = None) -> None:
    """Persist one diagnosable owned-exit record for every Controller run."""
    names = ["REPORT.md", "ledger.jsonl", "budget-status.json"]
    artefacts = acceptance_lib.snapshot(dirs.root, names)
    payload = {"version": 1, "execution_status": execution_status,
               "outcome": outcome, "error": error[:1000] if error else None,
               "recorded_at": acceptance_lib.utc_now(), "artefacts": artefacts}
    _atomic_write_bytes(dirs.root / "run-status.json",
                        (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def recover_run(run_dir: Path, *, invocation_id: str | None = None,
                final_cost_usd: float | None = None, evidence: str | None = None) -> dict:
    """Recover accounting and paid output without replaying provider calls.

    Exclusive run ownership excludes reconciliation during active dispatch.
    OS locks disappear after a crash, but reservations do not. Evidence is an
    operator-supplied terminal bill/result reference, never a timeout age.
    """
    dirs = RunDirs(run_dir.resolve())
    if not (dirs.root / "dispatch-budget.json").is_file():
        raise BudgetError("No durable budget found; legacy runs cannot be silently resumed")
    if invocation_id is not None and (final_cost_usd is None or not evidence or not evidence.strip()):
        raise BudgetError("Reconciliation requires --final-cost-usd and --evidence")
    with ledger_lock(dirs.root / "controller-owner", timeout_s=0):
        budget = DispatchBudget(dirs.root / "dispatch-budget.json")
        if invocation_id is not None:
            row = budget.snapshot()["invocations"].get(invocation_id)
            if row is None:
                raise BudgetError(f"Unknown invocation {invocation_id!r}")
            budget.settle(invocation_id, final_cost_usd, final=True,
                          telemetry=row.get("telemetry") or {}, evidence=evidence)
        summary = export_budget(budget, dirs)
        lines = ["# Controller recovery", "",
                 "No provider calls were replayed. Content records and paid reply text remain intact.",
                 "Accounting recovery does not automatically continue pipeline phases.", "",
                 f"Known spend USD {summary['spent_usd']:.4f}; held USD {summary['reserved_usd']:.4f}.",
                 f"Cancelled: {summary['cancelled']}; breached: {summary['breached']}.", "",
                 "## Remaining work", "",
                 "Inspect REPORT.md, digests.md and records/ for completed work. If the process died",
                 "before a content write, dispatch-budget.json retains any received reply under telemetry.result.",
                 "Resolve each invocation below from terminal provider evidence, then explicitly scope",
                 "any follow-on run and its separate budget. Do not repeat completed side effects.", ""]
        lines += [f"- `{ident}`: unresolved; retain its allowance until final usage is known."
                  for ident in summary["unresolved"]] or ["No unresolved invocation charges."]
        _atomic_write_bytes(dirs.root / "RECOVERY.md", ("\n".join(lines) + "\n").encode("utf-8"))
        return summary


def run_quick(problem_text: str, project: Path, budget_usd: float, timeout: float,
              runner_factory: Callable[[Callable[[], float]], RoleRunner], run_id: str | None = None,
              *, elapsed_limit_s: float | None = None) -> RunResult:
    units(budget_usd)
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    if elapsed_limit_s is not None and (not math.isfinite(elapsed_limit_s) or elapsed_limit_s <= 0):
        raise ValueError("elapsed_limit_s must be finite and positive")
    deadline = time.monotonic() + elapsed_limit_s if elapsed_limit_s is not None else None
    run_id = run_id or dt.datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", run_id):
        raise ValueError("run_id must be a simple directory name")
    dirs = RunDirs(project / "runs" / run_id)
    if dirs.root.exists():
        raise BudgetError(f"Run {run_id!r} already exists; use --recover-run, never restart its paid work")
    dirs.create()
    with ledger_lock(dirs.root / "controller-owner", timeout_s=0):
        return _run_quick(problem_text, project, budget_usd, timeout, runner_factory, dirs, deadline)


def _run_quick(problem_text: str, project: Path, budget_usd: float, timeout: float,
               runner_factory: Callable[[Callable[[], float]], RoleRunner],
               dirs: RunDirs, deadline: float | None) -> RunResult:
    """Execute a fresh pipeline while holding exclusive ownership of its run."""
    scribe = Scribe(dirs)
    spent = {"usd": 0.0}
    calls = {"n": 0}
    dispatch_budget = None

    def remaining() -> float:
        if dispatch_budget is not None:
            return dispatch_budget.remaining()
        return max(0.0, budget_usd - spent["usd"])

    def finish(outcome: str, record: dict) -> RunResult:
        status = export_budget(dispatch_budget, dirs) if dispatch_budget else None
        if status:
            spent["usd"], calls["n"] = status["spent_usd"], status["calls"]
        write_report(dirs, scribe, outcome, record, spent["usd"], calls["n"])
        if status:
            with dirs.report.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(f"\n## Dispatch accounting\n\nKnown spend USD {status['spent_usd']:.4f}; "
                             f"held USD {status['reserved_usd']:.4f}; available USD {status['available_usd']:.4f}. "
                             f"Complete: {status['accounting_complete']}; breach: {status['breached']}.\n\n"
                             "Inspect budget-status.json and dispatch-budget.json. Reconcile unresolved "
                             "invocations with terminal provider evidence before reusing their allowance.\n")
        write_run_status(dirs, "completed" if outcome in ("solution", "dissolved") else "blocked", outcome)
        return RunResult(outcome, record, dirs.root, spent["usd"], calls["n"],
                         status["reserved_usd"] if status else 0.0,
                         status["accounting_complete"] if status else True)

    def check_budget(phase: str) -> RunResult | None:
        if remaining() <= 0:
            gap = _gap_report(scribe, "budget_spent")
            write_digest(scribe, dirs, phase, "No dispatch allowance remains; inspect the report's accounting section.", [])
            return finish("gap", gap)
        return None

    runner = runner_factory(remaining)
    if isinstance(runner, LiveRoleRunner):
        dispatch_budget = DispatchBudget(dirs.root / "dispatch-budget.json", budget_usd)
        runner.budget = dispatch_budget
        runner.deadline = deadline

    # Worker threads share only the locked dispatch budget. All content
    # writes and ID assignment stay on this thread, after draining futures.
    def raw_call(phase: str, role: str, prompt: str) -> RoleReply:
        call_timeout = timeout if deadline is None else min(timeout, deadline - time.monotonic())
        if call_timeout <= 0:
            raise BudgetExhausted("Elapsed run limit reached; no further call dispatched")
        return runner(phase, role, prompt, timeout=call_timeout)

    def commit_reply(reply: RoleReply) -> list[dict]:
        calls["n"] += 1
        if reply.budget_entry is not None:
            spent["usd"] += reply.budget_entry["cost_usd"]
            scribe.write([reply.budget_entry], writer_role="controller", expected_types={"BudgetEntry"})
        if reply.unparsed:
            phase = reply.budget_entry["phase"] if reply.budget_entry else "unknown"
            role = reply.budget_entry["role"] if reply.budget_entry else "unknown"
            with dirs.rejections.open("a", encoding="utf-8") as f:
                for fragment in reply.unparsed:
                    f.write(json.dumps({"phase": phase, "role": role, "unparsed_fragment": fragment[:2000]},
                                        ensure_ascii=False) + "\n")
        return reply.records

    def call(phase: str, role: str, prompt: str) -> list[dict]:
        return commit_reply(raw_call(phase, role, prompt))

    def classify(phase: str, prompt: str, schema: dict, default: dict) -> dict:
        result, entry = runner.classify(phase, prompt, schema, default)
        calls["n"] += 1
        if entry is not None:
            spent["usd"] += entry["cost_usd"]
            scribe.write([entry], writer_role="controller", expected_types={"BudgetEntry"})
        return result

    def write_with_retry(phase: str, role: str, records: list[dict], expected_types: set[str],
                          retry_prompt: Callable[[list[ScribeRejection]], str] | None) -> list[dict]:
        accepted, rejected = scribe.write(records, writer_role=role, expected_types=expected_types)
        if rejected and retry_prompt is not None:
            for _ in range(MAX_RECORD_RETRIES):
                if not rejected:
                    break
                fix_prompt = retry_prompt(rejected)
                fixed = call(phase, role, fix_prompt)
                more_accepted, rejected = scribe.write(fixed, writer_role=role, expected_types=expected_types)
                accepted += more_accepted
        return accepted

    def phases() -> RunResult:
        # ---- 1. Intake (code) ----
        problem_record = {"type": "ProblemRecord", "statement": problem_text, "context": "",
                           "constraints": [], "budget_usd": budget_usd, "mode": "quick", "acceptance_criteria": [],
                           "ledger_version": 0, "references": []}
        accepted, rej = scribe.write([problem_record], writer_role="controller", expected_types={"ProblemRecord"})
        if not accepted or rej:
            raise RuntimeError(f"ProblemRecord rejected: {rej}")
        problem = accepted[0]
        write_digest(scribe, dirs, "intake", "Problem recorded verbatim; nothing judged yet.", [problem])

        if (r := check_budget("intake")):
            return r

        # ---- 2. Frame ----
        frame_records = call("frame", "framer", build_frame_prompt(problem, [], []))
        accepted = write_with_retry("frame", "framer", frame_records, {"PremiseRecord", "FrameRecord", "CandidateRecord"},
                                     lambda rej: _retry_prompt(build_frame_prompt(problem, [], []), rej))
        frame = _one_of(accepted, "FrameRecord", "Frame")
        b0 = _one_of([r for r in accepted if r["type"] == "CandidateRecord" and r.get("technique") == "b0"],
                     None, "Frame's B0 candidate", allow_type_check=False)
        write_digest(scribe, dirs, "frame", f"Ledger v1: {len(scribe.premises(1))} premises, problem type "
                     f"{frame.get('problem_type')!r}, dissolution {frame.get('dissolution_verdict')!r}."
                     f"{_premise_cap_note(frame)}", accepted)

        if frame["dissolution_verdict"] == "dissolved":
            gap = _gap_report(scribe, "dissolved", next_test=frame.get("dissolution_reason", ""))
            return finish("dissolved", gap)
        if (r := check_budget("frame")):
            return r

        # ---- 3. Verify loop ----
        for _ in range(MAX_VERIFY_PASSES):
            unverified = [p for p in scribe.premises() if p["class"] == "unverified"]
            if not unverified:
                break
            measurements: list[dict] = []
            for premise in unverified:
                recs = call("verify", "verifier", build_verify_prompt(problem, premise, project))
                measurements += write_with_retry(
                    "verify", "verifier", recs, {"MeasurementRecord"},
                    lambda rej, premise=premise: _retry_prompt(build_verify_prompt(problem, premise, project), rej))
            if not measurements:
                break
            prior_ledger = [problem, frame, *scribe.premises(), b0]
            recs = call("frame", "framer", build_frame_prompt(problem, measurements, prior_ledger))
            accepted = write_with_retry("frame", "framer", recs, {"PremiseRecord", "FrameRecord"},
                                         lambda rej: _retry_prompt(build_frame_prompt(problem, measurements, prior_ledger), rej))
            new_frame = _one_of(accepted, "FrameRecord", "Frame re-entry")
            frame = new_frame
            write_digest(scribe, dirs, "verify", f"{len(measurements)} measurement(s); ledger v{frame['ledger_version']}, "
                         f"stable={frame['stable']}.{_premise_cap_note(frame)}", accepted + measurements)
            if frame["dissolution_verdict"] == "dissolved":
                gap = _gap_report(scribe, "dissolved", next_test=frame.get("dissolution_reason", ""))
                return finish("dissolved", gap)
            if (r := check_budget("verify")):
                return r
            if frame["stable"]:
                break

        # ---- Controller call 1: is the ledger stable enough to freeze? (10.5) ----
        stable = classify("controller-stability", build_stability_prompt(scribe.premises(), frame), STABILITY_SCHEMA,
                           default={"stable": frame["stable"], "reasoning": "fallback to FrameRecord.stable"})
        write_digest(scribe, dirs, "controller-stability", f"Controller classifies stable={stable['stable']}: "
                     f"{stable['reasoning'][:200]}", [])
        if (r := check_budget("controller-stability")):
            return r

        # ---- Controller call 2: which technique families? (10.5) ----
        families = classify("controller-families", build_families_prompt(problem, frame), FAMILIES_SCHEMA,
                             default={"families": list(TECHNIQUE_FAMILIES), "reasoning": "fallback: run all three"})
        chosen_families = families.get("families") or list(TECHNIQUE_FAMILIES)
        write_digest(scribe, dirs, "controller-families", f"Controller selects {chosen_families}: "
                     f"{families['reasoning'][:200]}", [])
        if (r := check_budget("controller-families")):
            return r

        # ---- 4-6. Generate / Critique / Select, one tier, bounded reframe ----
        reframes = 0
        while True:
            ledger_slice = [problem, frame, *scribe.premises(), b0]

            # The budget serialises admissions; content writes remain here.
            def gen_one(family: str) -> RoleReply:
                return raw_call("generate", "generator", build_generate_prompt(family, ledger_slice, []))

            # Drain every future even if one fails. Its siblings have already
            # spent money and their successful candidates must remain usable.
            replies, failures = [], []
            with ThreadPoolExecutor(max_workers=max(1, len(chosen_families))) as pool:
                futures = [pool.submit(gen_one, family) for family in chosen_families]
                for family, future in zip(chosen_families, futures):
                    try:
                        replies.append((family, future.result()))
                    except (BudgetExhausted, RoleCallFailed) as exc:
                        failures.append(exc)
            generated: list[dict] = []
            pending_repairs = []
            for family, reply in replies:
                recs = commit_reply(reply)
                accepted, rejected = scribe.write(recs, writer_role="generator", expected_types={"CandidateRecord"})
                generated += accepted
                if rejected:
                    pending_repairs.append((family, rejected))
            # Persist every usable sibling before a repair that may fail.
            if not failures:
                for family, rejected in pending_repairs:
                    for _ in range(MAX_RECORD_RETRIES):
                        if not rejected:
                            break
                        fixed = call("generate", "generator", _retry_prompt(build_generate_prompt(family, ledger_slice, []), rejected))
                        accepted, rejected = scribe.write(fixed, writer_role="generator", expected_types={"CandidateRecord"})
                        generated += accepted
            candidates = [b0] + generated
            write_digest(scribe, dirs, "generate", f"{len(candidates) - 1} candidate(s) from {chosen_families}, "
                         "plus B0.", candidates[1:])
            if failures:
                raise failures[0]
            if (r := check_budget("generate")):
                return r

            crit_records = call("critique", "critic", build_critique_prompt(ledger_slice, candidates))
            critiques = write_with_retry(
                "critique", "critic", crit_records, {"CritiqueRecord"},
                lambda rej: _retry_prompt(build_critique_prompt(ledger_slice, candidates), rej))
            write_digest(scribe, dirs, "critique", f"{len(critiques)} critique(s) for {len(candidates)} candidate(s).",
                         critiques)
            if (r := check_budget("critique")):
                return r

            falsified = [c for c in critiques if c.get("falsified_premise_claims")]
            if falsified:
                reframes += 1
                if reframes > MAX_REFRAMES:
                    candidates, critiques = [b0], []
                    break
                # SYSTEM.md section 3's control loop calls FRAME.update() on a
                # falsified premise, not a code-only patch: phase gating (the
                # generators that already ran cited the version now being
                # superseded) only holds together if the correction goes
                # through a genuine re-freeze, which is what mints the new
                # ledger_version that scribe.premises() and the next
                # Generate's stale-version check both key off. A cheaper,
                # code-only premise flip was tried first and rejected in this
                # module's own development: it leaves a corrected premise
                # sitting above the still-frozen version, invisible to
                # scribe.premises() until a FrameRecord actually advances the
                # freeze, and candidates would go on citing a version whose
                # premise set the Critic has already shown is wrong.
                prior_ledger = [problem, frame, *scribe.premises(), b0]
                recs = call("frame", "framer", build_frame_prompt(problem, [], prior_ledger, falsified))
                accepted = write_with_retry("frame", "framer", recs, {"PremiseRecord", "FrameRecord"},
                                             lambda rej: _retry_prompt(build_frame_prompt(problem, [], prior_ledger, falsified), rej))
                frame = _one_of(accepted, "FrameRecord", "Frame re-entry (reframe)")
                write_digest(scribe, dirs, "reframe", f"Reframe {reframes}/{MAX_REFRAMES}: ledger v{frame['ledger_version']} "
                             f"after {len(falsified)} falsified-premise critique(s).{_premise_cap_note(frame)}", accepted)
                if frame["dissolution_verdict"] == "dissolved":
                    gap = _gap_report(scribe, "dissolved", next_test=frame.get("dissolution_reason", ""))
                    return finish("dissolved", gap)
                if (r := check_budget("reframe")):
                    return r
                continue
            break

        accept_map = {c["candidate_id"]: c for c in critiques}
        passing = [c for c in candidates if c["id"] == b0["id"] or accept_map.get(c["id"], {}).get("verdict") == "pass"]
        # STEPS.md / task 10.4's quick-mode stop rule: the first candidate
        # surviving critique with no unverified load-bearing premise it
        # introduces, else B0.
        winner = next((c for c in passing if c["id"] != b0["id"]
                       and not any(p.get("class") == "unverified" for p in c.get("premises_introduced", []))), None)
        winner = winner or b0

        sel_records = call("select", "selector", build_select_prompt(candidates, critiques, frame["acceptance_criteria"], b0["id"]))
        selections = write_with_retry(
            "select", "selector", sel_records, {"SelectionRecord"},
            lambda rej: _retry_prompt(build_select_prompt(candidates, critiques, frame["acceptance_criteria"], b0["id"]), rej))
        write_digest(scribe, dirs, "select", f"Winner (code, per the quick-mode stop rule): {winner['id']} "
                     f"({winner.get('technique')}).", selections)
        if (r := check_budget("select")):
            return r

        # ---- 8. Close (code writes the SolutionRecord; no Instantiate in quick mode) ----
        unverified_lb = [p["id"] for p in scribe.premises() if p["class"] == "unverified" and p.get("load_bearing")]
        sol = {"type": "SolutionRecord", "candidate_id": winner["id"], "answer": winner.get("mechanism", ""),
               "technique": winner.get("technique", "b0"), "unverified_load_bearing": unverified_lb,
               "audit_trail": [problem["id"], frame["id"], winner["id"]], "problem_type": frame["problem_type"],
               "ledger_version": frame["ledger_version"], "references": [winner["id"]]}
        accepted, rej = scribe.write([sol], writer_role="librarian", expected_types={"SolutionRecord"})
        if not accepted or rej:
            raise RuntimeError(f"SolutionRecord rejected: {rej}")
        solution = accepted[0]
        write_digest(scribe, dirs, "close", f"Closed with {winner['id']}; {len(unverified_lb)} unverified "
                     "load-bearing premise(s) remain.", [solution])
        return finish("solution", solution)

    try:
        return phases()
    except BudgetExhausted as exc:
        # SYSTEM.md's termination rule "budget spent": close with a gap
        # report rather than a traceback. The first fleet batch lost three
        # runs to the traceback form (D58).
        gap = _gap_report(scribe, "budget_spent")
        write_digest(scribe, dirs, "close", f"Dispatch stopped: {exc}. Inspect the accounting summary; "
                     "stopping with a gap report.", [gap])
        return finish("gap", gap)
    except (RoleOutputMismatch, RoleCallFailed) as exc:
        # A role's reply never converged to the one record _one_of()
        # needed, after the scripted retry: close with a gap report and
        # REPORT.md written, the same shape as BudgetExhausted, rather
        # than the traceback with nothing to read this used to leave
        # (audit A15, docs/AUDIT-2026-09-16.md). The schema's four
        # termination values have no exact fit for "a role's output
        # never usable"; no_improvement is the closest: the run made no
        # progress toward a solution the ledger could act on.
        gap = _gap_report(scribe, "no_improvement", next_test=str(exc))
        write_digest(scribe, dirs, "close", f"A role's output could not be used: {exc}. "
                     "Stopping with a gap report.", [gap])
        return finish("gap", gap)
    except KeyboardInterrupt:
        if dispatch_budget:
            dispatch_budget.cancel()
        gap = _gap_report(scribe, "no_improvement", next_test="Cancelled; inspect unresolved invocation charges before continuing")
        return finish("gap", gap)
    except BaseException as exc:
        # Defects remain loud, but recovery must not have to infer whether an
        # owned Controller process vanished before writing a normal report.
        write_run_status(dirs, "interrupted", None, f"{type(exc).__name__}: {exc}")
        raise
    finally:
        # Even an internal invariant error must leave complete accounting.
        if dispatch_budget:
            export_budget(dispatch_budget, dirs)


def _premise_cap_note(frame: dict) -> str:
    """ROLES.md's Framer contract: at most 40 premises, merge above that.
    Merging is the Framer's own judgement call, not something code can do;
    this only makes the breach visible in the digest a human reads."""
    count = frame.get("premise_count", 0)
    return f" WARNING: {count} premises exceeds the {MAX_PREMISES}-premise cap; the Framer should merge."         if count > MAX_PREMISES else ""


def _one_of(records: list[dict], record_type: str | None, label: str, allow_type_check: bool = True) -> dict:
    matches = [r for r in records if not allow_type_check or r["type"] == record_type]
    if len(matches) != 1:
        raise RoleOutputMismatch(f"{label}: expected exactly one record, got {len(matches)} (after Scribe "
                                 "validation and retry); see this run's rejections.jsonl for what was rejected and why")
    return matches[0]


def _retry_prompt(original_prompt: str, rejected: list[ScribeRejection]) -> str:
    lines = "\n".join(f"- {json.dumps(r.record, ensure_ascii=False)[:200]}: {'; '.join(r.reasons)}" for r in rejected)
    return (original_prompt + "\n\nYour previous reply had records rejected by the Scribe. Resend corrected "
            f"versions of only these:\n{lines}")


def _gap_report(scribe: Scribe, termination: str, next_test: str = "") -> dict:
    """`next_test` is truncated to GapReport.next_cheapest_test's 300-character
    cap: a caller passing a FrameRecord's dissolution_reason (capped at 600)
    can overflow it, which is exactly what happened the first time this ran
    live (a genuine, correct 555-character dissolution_reason from the
    Framer got rejected here, and the ValueError from unpacking zero
    accepted records masked the real cause; fixed by checking `rej` before
    unpacking, below, as well as by truncating)."""
    frame = scribe.latest("FrameRecord")
    unmet = frame["acceptance_criteria"] if frame else []
    unverified = [p["id"] for p in scribe.premises() if p["class"] == "unverified" and p.get("load_bearing")]
    record = {"type": "GapReport", "best_candidate_id": None, "unmet_criteria": unmet,
              "unverified_load_bearing": unverified, "next_cheapest_test": (next_test or "none")[:300],
              "termination": termination, "ledger_version": scribe.frozen_version,
              "references": [frame["id"]] if frame else []}
    accepted, rej = scribe.write([record], writer_role="librarian", expected_types={"GapReport"})
    if not accepted or rej:
        raise RuntimeError(f"GapReport rejected: {rej}")
    return accepted[0]


# --------------------------------------------------------------------------
# --selftest (task 10.6): the whole state machine, canned records, a fake
# role runner, no `claude -p` calls. Asserts phase transitions, the
# stale-version and single-writer rejections, the reframe cap, and each
# termination rule. `test/harness/check.py`'s SYSTEM check invokes this.

def _canned(problem_text: str = "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
            candidate_ledger_version: int = 2) -> dict:
    """One T10-shaped scenario's worth of canned replies, with every id a
    caller will need to reference computed here rather than left as a
    placeholder: the Scribe assigns ids in the order records are written,
    which for this scenario's write order is always prem-001, prem-002,
    frame-001, cand-001 (b0) for the first Frame call, then meas-001,
    prem-003, frame-002 for the Verify loop's one re-entry, then cand-002
    for the one real Generate candidate. `candidate_ledger_version` lets a
    caller whose scenario never advances past ledger version 1 (no second
    Frame commit) pass 1 instead of the normal-flow default of 2, so the
    Scribe's stale-version check sees a candidate citing whatever version
    is actually frozen when it is written."""
    return {
        "problem": {"type": "ProblemRecord", "statement": problem_text, "context": "", "constraints": [],
                    "budget_usd": 5.0, "mode": "quick", "acceptance_criteria": ["fix the duplicate"],
                    "ledger_version": 0, "references": []},
        "frame_v1": [
            {"type": "PremiseRecord", "text": "normalise() does not strip whitespace.", "class": "verified",
             "source": "read", "confidence": 1.0, "cheapest_verification": "none", "load_bearing": True,
             "supersedes": None, "ledger_version": 1, "references": ["prob-001"]},
            {"type": "PremiseRecord", "text": "Three downstream systems depend on the exact output.", "class": "unverified",
             "source": "stated", "confidence": 0.3, "cheapest_verification": "read downstream.py",
             "load_bearing": True, "supersedes": None, "ledger_version": 1, "references": ["prob-001"]},
            {"type": "FrameRecord", "goal_ladder": ["one account per person"], "metric_interrogation": "n/a",
             "problem_type": "constraint-with-checkable-justification", "dissolution_verdict": "stands",
             "dissolution_reason": "n/a", "acceptance_criteria": ["fix the duplicate"], "b0_candidate_id": "cand-001",
             "premise_count": 2, "stable": False, "ledger_version": 1, "references": ["prob-001", "prem-001", "prem-002", "cand-001"]},
            {"type": "CandidateRecord", "technique": "b0", "premise_operation": "none",
             "mechanism": "strip in the caller, leave legacy_ids.py alone", "claimed_gain_vs_b0": "none",
             "premises_introduced": [], "falsification_test": "run the tests", "cost_estimate_usd": 0.1,
             "refines": None, "ledger_version": 1, "references": ["prem-001", "prem-002"]},
        ],
        "measurement": [{"type": "MeasurementRecord", "premise_id": "prem-002", "method": "read downstream.py",
                          "result": "all three callers strip already", "artefact": "downstream.py:12-24",
                          "outcome": "falsifies", "cost_usd": 0.0, "ledger_version": 1, "references": ["prem-002"]}],
        "frame_v2": [
            {"type": "PremiseRecord", "text": "The justification is false; stripping is a no-op downstream.",
             "class": "verified", "source": "meas-001", "confidence": 1.0, "cheapest_verification": "none",
             "load_bearing": True, "supersedes": "prem-002", "ledger_version": 2, "references": ["prem-002", "meas-001"]},
            {"type": "FrameRecord", "goal_ladder": ["one account per person"], "metric_interrogation": "n/a",
             "problem_type": "constraint-with-checkable-justification", "dissolution_verdict": "stands",
             "dissolution_reason": "n/a", "acceptance_criteria": ["fix the duplicate"], "b0_candidate_id": "cand-001",
             "premise_count": 2, "stable": True, "ledger_version": 2, "references": ["frame-001", "prem-003", "cand-001"]},
        ],
        "candidate": [{"type": "CandidateRecord", "technique": "subtract", "premise_operation": "remove",
                       "mechanism": "strip inside normalise() itself", "claimed_gain_vs_b0": "meets the pinned test",
                       "premises_introduced": [], "falsification_test": "run both suites", "cost_estimate_usd": 0.3,
                       "refines": None, "ledger_version": candidate_ledger_version, "references": ["prem-003"]}],
        "critique": [{"type": "CritiqueRecord", "candidate_id": "cand-002", "failure_modes": [],
                      "derivable": False, "falsified_premise_claims": [], "verdict": "pass",
                      "ledger_version": candidate_ledger_version, "references": ["cand-002"]},
                     {"type": "CritiqueRecord", "candidate_id": "cand-001", "failure_modes": ["derivable from the ledger"],
                      "derivable": True, "falsified_premise_claims": [], "verdict": "return",
                      "ledger_version": candidate_ledger_version, "references": ["cand-001"]}],
        "selection": [{"type": "SelectionRecord", "baseline_id": "cand-001",
                       "shortlist": [{"candidate_id": "cand-002", "rank": 1, "score": 1.0, "basis": "meets criteria"}],
                       "excluded": [{"candidate_id": "cand-001", "reason": "derivable"}],
                       "ledger_version": candidate_ledger_version, "references": ["cand-001", "cand-002"]}],
    }


def _run_id_gen():
    n = 0
    while True:
        n += 1
        yield f"selftest-{n:03d}"


def _happy_path_script() -> dict:
    c = _canned()
    return {
        ("frame", "framer"): [c["frame_v1"], c["frame_v2"]],
        ("verify", "verifier"): [c["measurement"]],
        ("generate", "generator"): [c["candidate"], [], []],
        ("critique", "critic"): [c["critique"]],
        ("select", "selector"): [c["selection"]],
    }


def _dissolved_script() -> dict:
    c = _canned()
    frame = dict(c["frame_v1"][2])
    frame["dissolution_verdict"] = "dissolved"
    frame["dissolution_reason"] = "the acceptance criteria are unsatisfiable as stated"
    return {("frame", "framer"): [[c["frame_v1"][0], c["frame_v1"][1], frame, c["frame_v1"][3]]]}


def selftest(project: Path | None = None, verbose: bool = False) -> tuple[bool, list[str]]:
    """Runs several scripted scenarios against a scratch directory, no live
    `claude -p` calls. Returns (all_passed, messages)."""
    import tempfile
    problems: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            problems.append(msg)
        elif verbose:
            print(f"ok: {msg}")

    # --- Scenario 0: _parse_jsonl_reply survives a pretty-printed record ---
    # Direct regression test for the live bug (2026-09-14): a naive
    # line-splitting parser silently dropped a FrameRecord the Framer
    # pretty-printed across several lines, while single-line PremiseRecords
    # on either side of it parsed fine. No temp directory needed.
    mixed_reply = (
        '{"type": "PremiseRecord", "id": "prem-001", "text": "short, one line"}\n'
        "```\n"  # a code fence OUTPUT_RULE forbids but is tolerated
        "{\n"
        '  "type": "FrameRecord",\n'
        '  "id": "frame-001",\n'
        '  "goal_ladder": [\n'
        '    "line one",\n'
        '    "line two"\n'
        "  ]\n"
        "}\n"
        "not json at all, a stray line\n"
        '2. {"type": "CandidateRecord", "id": "cand-001", "technique": "b0"}\n'
        "3\n"
    )
    records, unparsed = _parse_jsonl_reply(mixed_reply)
    check([r["type"] for r in records] == ["PremiseRecord", "FrameRecord", "CandidateRecord"],
          f"scenario 0: a pretty-printed record parses alongside single-line ones, got types {[r.get('type') for r in records]}")
    check(records[1].get("goal_ladder") == ["line one", "line two"],
          f"scenario 0: the pretty-printed record's own multi-line array survives intact, got {records[1].get('goal_ladder')}")
    check(all(isinstance(r, dict) for r in records) and len(records) == 3,
          f"scenario 0: a bare number is never a record (the live crash of D56), got {records}")
    check(unparsed[0] == "not json at all, a stray line" and len(unparsed) == 3,
          f"scenario 0: non-JSON lines and bare numbers are reported, not silently dropped, got {unparsed}")

    # --- Scenario 0b: schema_summary surfaces nested array-of-object shape ---
    # Direct regression test for the live bug (2026-09-14, D52): a top-level-only
    # summary told the Selector only "excluded: array", never that
    # excluded[].reason is a five-value enum, so every live SelectionRecord was
    # rejected and the run silently reached Close with no valid record for
    # Select at all. Same blindness hit CandidateRecord.premises_introduced[].
    sel_summary = schema_summary("SelectionRecord")
    check("loses_to_b0" in sel_summary and "rejected_by_critic" in sel_summary,
          f"scenario 0b: SelectionRecord's nested excluded[].reason enum is surfaced, got:\n{sel_summary}")
    cand_summary = schema_summary("CandidateRecord")
    check("premises_introduced" in cand_summary and "class" in cand_summary
          and "law/maths/policy" in cand_summary.replace("\n", " "),
          f"scenario 0b: CandidateRecord's nested premises_introduced[].class enum is surfaced, got:\n{cand_summary}")

    with tempfile.TemporaryDirectory(prefix="system-controller-selftest-") as tmp:
        tmp_path = Path(tmp)

        # --- Scenario 1: happy path, one reframe-free pass to a solution ---
        script = _happy_path_script()
        runner = FakeRoleRunner(script)
        result = run_quick("Duplicate accounts from whitespace; legacy_ids.py is frozen.", tmp_path,
                            budget_usd=5.0, timeout=30, runner_factory=lambda _r: runner, run_id="s1")
        check(result.outcome == "solution", f"scenario 1: expected outcome 'solution', got {result.outcome!r}")
        check(result.record.get("technique") == "subtract",
              f"scenario 1: expected the subtract candidate to win over B0, got {result.record.get('technique')!r}")
        check((result.run_dir / "ledger.jsonl").exists(), "scenario 1: ledger.jsonl was created")
        check((result.run_dir / "digests.md").exists(), "scenario 1: digests.md was created")
        report1 = (result.run_dir / "REPORT.md").read_text(encoding="utf-8") if (result.run_dir / "REPORT.md").exists() else ""
        check("strip inside normalise() itself" in report1 and "## Unverified load-bearing premises" in report1
              and "## Ranked alternatives" in report1 and "cand-002" in report1,
              f"scenario 1: REPORT.md carries the answer, the unverified list and the shortlist, got:\n{report1[:600]}")
        ledger_lines = result.run_dir.joinpath("ledger.jsonl").read_text(encoding="utf-8").splitlines()
        check(len(ledger_lines) > 0, "scenario 1: ledger.jsonl is non-empty")
        ids = [json.loads(l)["id"] for l in ledger_lines]
        check(len(ids) == len(set(ids)), f"scenario 1: every ledger record has a unique id (ids: {ids})")
        cand_ids = [json.loads(l)["id"] for l in ledger_lines if json.loads(l)["type"] == "CandidateRecord"]
        check(len(cand_ids) >= 2, f"scenario 1: at least B0 plus the subtract candidate on the ledger (candidate ids: {cand_ids})")

        # --- Scenario 2: dissolution short-circuit ---
        result2 = run_quick("An unsatisfiable problem.", tmp_path, budget_usd=5.0, timeout=30,
                             runner_factory=lambda _r: FakeRoleRunner(_dissolved_script()), run_id="s2")
        check(result2.outcome == "dissolved", f"scenario 2: expected 'dissolved', got {result2.outcome!r}")
        check(result2.record["termination"] == "dissolved", "scenario 2: GapReport.termination == 'dissolved'")

        # --- Scenario 3: budget exhausted before Frame even returns ---
        result3 = run_quick("Any problem.", tmp_path, budget_usd=0.0, timeout=30,
                             runner_factory=lambda _r: FakeRoleRunner(_happy_path_script()), run_id="s3")
        check(result3.outcome == "gap" and result3.record.get("termination") == "budget_spent",
              f"scenario 3: zero budget should stop at intake with termination budget_spent, got {result3.outcome}/{result3.record.get('termination')}")

        # --- Scenario 4: Scribe rejects a stale ledger_version on a CandidateRecord ---
        dirs = RunDirs(tmp_path / "runs" / "s4")
        dirs.create()
        scribe = Scribe(dirs)
        c = _canned()
        (problem,), _ = scribe.write([c["problem"]], writer_role="controller", expected_types={"ProblemRecord"})
        frame_batch = [dict(r) for r in c["frame_v1"]]
        for r in frame_batch:
            r["ledger_version"] = 1
            r["references"] = []
        accepted, rej = scribe.write(frame_batch, writer_role="framer",
                                      expected_types={"PremiseRecord", "FrameRecord", "CandidateRecord"})
        check(not rej, f"scenario 4 setup: ledger v1 frame batch should validate clean, got rejections {rej}")
        stale = dict(c["candidate"][0])
        stale["ledger_version"] = 99
        stale["references"] = []
        _, rej4 = scribe.write([stale], writer_role="generator", expected_types={"CandidateRecord"})
        check(len(rej4) == 1 and any("frozen version" in r for r in rej4[0].reasons),
              f"scenario 4: a CandidateRecord citing a stale ledger_version should be rejected, got {rej4}")

        # --- Scenario 5: single-writer rejection (a Generator tries to write a PremiseRecord) ---
        _, rej5 = scribe.write([{"type": "PremiseRecord", "text": "smuggled in", "class": "law", "source": "x",
                                  "confidence": 1.0, "cheapest_verification": "none", "load_bearing": False,
                                  "supersedes": None, "ledger_version": 1, "references": []}],
                                writer_role="generator", expected_types={"CandidateRecord", "PremiseRecord"})
        check(len(rej5) == 1 and any("single-writer" in r for r in rej5[0].reasons),
              f"scenario 5: a Generator writing a PremiseRecord should be rejected, got {rej5}")

        # --- Scenario 6: reframe cap ---
        # A dedicated fixture, not `_canned()`'s: every reframe must cite the
        # ledger version actually frozen at that point (1 for the first
        # Generate call, then 2, 3, 4 as each reframe mints a new frozen
        # FrameRecord), which `_canned()`'s single-version parameterisation
        # cannot express across a sequence of reframes. Every cross-reference
        # below points at an id that is valid from iteration 1 onward
        # (prem-001, cand-001, frame-001, from the initial Frame call), so
        # the same static templates can be reused at each version without
        # needing to track what the previous iteration actually produced.
        def always_falsifies(_r):
            c6 = _canned()

            def candidate_at(version: int) -> list[dict]:
                cand = dict(c6["candidate"][0])
                cand["ledger_version"] = version
                cand["references"] = ["prem-001"]
                return [cand]

            def critique_falsifying() -> list[dict]:
                crit = dict(c6["critique"][0])
                crit["candidate_id"] = "cand-001"
                crit["falsified_premise_claims"] = [{"premise_id": "prem-001", "reason": "still false"}]
                crit["references"] = ["cand-001"]
                return [crit]

            def frame_reentry_at(version: int) -> list[dict]:
                prem = {"type": "PremiseRecord", "text": "still false, corrected again", "class": "verified",
                        "source": "critique", "confidence": 1.0, "cheapest_verification": "none",
                        "load_bearing": True, "supersedes": "prem-001", "ledger_version": version,
                        "references": ["prem-001"]}
                frame_rec = {"type": "FrameRecord", "goal_ladder": ["one account per person"],
                             "metric_interrogation": "n/a", "problem_type": "constraint-with-checkable-justification",
                             "dissolution_verdict": "stands", "dissolution_reason": "n/a",
                             "acceptance_criteria": ["fix the duplicate"], "b0_candidate_id": "cand-001",
                             "premise_count": 2, "stable": True, "ledger_version": version,
                             "references": ["frame-001", "cand-001"]}
                return [prem, frame_rec]

            generate_queue: list[list[dict]] = []
            for version in (1, 2, 3, 4):
                generate_queue += [candidate_at(version), [], []]  # one family returns the candidate, two return nothing

            script6 = {
                ("frame", "framer"): [c6["frame_v1"], frame_reentry_at(2), frame_reentry_at(3), frame_reentry_at(4)],
                ("verify", "verifier"): [[]],
                ("generate", "generator"): generate_queue,
                ("critique", "critic"): [critique_falsifying() for _ in range(4)],
                ("select", "selector"): [c6["selection"]],
            }
            return FakeRoleRunner(script6)

        result6 = run_quick("A problem whose candidates keep getting critiqued as false.", tmp_path,
                             budget_usd=5.0, timeout=30, runner_factory=always_falsifies, run_id="s6")
        check(result6.outcome == "solution" and result6.record.get("technique") == "b0",
              f"scenario 6: exceeding the reframe cap should fall back to B0, got {result6.outcome}/{result6.record.get('technique')}")

        # --- Scenario 7: "reframed" continues the pipeline; a long
        # dissolution_reason does not crash a GapReport that never gets
        # written. Added after the live toy run (2026-09-14) hit both bugs
        # at once: the Framer correctly returned dissolution_verdict
        # "reframed" (the problem exists, just not as stated, and the same
        # FrameRecord already carries the reframed acceptance criteria),
        # but the code treated any non-"stands" verdict as a hard stop, and
        # the stop path fed a 555-character dissolution_reason into a field
        # capped at 300, which crashed on the unpacking before the
        # rejection could even be reported.
        c7 = _canned()
        reframed_frame = dict(c7["frame_v1"][2])
        reframed_frame["dissolution_verdict"] = "reframed"
        reframed_frame["dissolution_reason"] = "x" * 555
        script7 = _happy_path_script()
        script7[("frame", "framer")][0] = [c7["frame_v1"][0], c7["frame_v1"][1], reframed_frame, c7["frame_v1"][3]]
        result7 = run_quick("A problem the Framer reframes rather than dissolves.", tmp_path,
                             budget_usd=5.0, timeout=30,
                             runner_factory=lambda _r: FakeRoleRunner(script7), run_id="s7")
        check(result7.outcome == "solution",
              f"scenario 7: a 'reframed' verdict should continue the pipeline to a solution, got {result7.outcome}")

        gap_dirs = RunDirs(tmp_path / "runs" / "s7-gap")
        gap_dirs.create()
        gap = _gap_report(Scribe(gap_dirs), "dissolved", next_test="y" * 555)
        check(len(gap["next_cheapest_test"]) <= 300,
              f"scenario 7: _gap_report truncates an oversized next_test to the schema's 300-character cap, got {len(gap['next_cheapest_test'])}")

        # --- Scenario 8: a batch's own self-chosen ids get remapped ---
        # Direct regression test for the second live bug this session found
        # (2026-09-14): the Framer has no way to know the id the Scribe will
        # assign, so a FrameRecord's b0_candidate_id naming the id its own
        # co-emitted CandidateRecord chose for itself must be rewritten to
        # the id the Scribe actually assigns that candidate, not left to
        # dangle. Uses a fresh Scribe so ids start at 1, independent of the
        # id assignments any other scenario made in this same process.
        remap_dirs = RunDirs(tmp_path / "runs" / "s8-remap")
        remap_dirs.create()
        remap_scribe = Scribe(remap_dirs)
        c8 = _canned()
        problem8, prem8a, prem8b = c8["problem"], c8["frame_v1"][0], c8["frame_v1"][1]
        remap_scribe.write([problem8], writer_role="controller", expected_types={"ProblemRecord"})
        self_chosen_frame = dict(c8["frame_v1"][2])
        self_chosen_frame["id"] = "my-frame-99"
        self_chosen_frame["b0_candidate_id"] = "my-cand-42"
        self_chosen_frame["references"] = ["my-cand-42"]
        self_chosen_cand = dict(c8["frame_v1"][3])
        self_chosen_cand["id"] = "my-cand-42"
        self_chosen_cand["references"] = ["x1", "x2"]  # this batch's own self-chosen premise ids
        accepted8, rejected8 = remap_scribe.write(
            [dict(prem8a, id="x1"), dict(prem8b, id="x2"), self_chosen_frame, self_chosen_cand],
            writer_role="framer", expected_types={"PremiseRecord", "FrameRecord", "CandidateRecord"})
        check(not rejected8, f"scenario 8: a batch using its own self-chosen ids should validate after remapping, got {rejected8}")
        remapped_frame = next((r for r in accepted8 if r["type"] == "FrameRecord"), None)
        remapped_cand = next((r for r in accepted8 if r["type"] == "CandidateRecord"), None)
        check(bool(remapped_frame and remapped_cand and remapped_frame["b0_candidate_id"] == remapped_cand["id"]),
              f"scenario 8: b0_candidate_id is rewritten to the Scribe-assigned candidate id, got "
              f"{remapped_frame and remapped_frame.get('b0_candidate_id')!r} vs {remapped_cand and remapped_cand.get('id')!r}")

        # --- Scenario 9: a rejected non-Frame record recovers via retry ---
        # Direct regression test for the fourth and fifth live runs (2026-09-14,
        # D52): Select (and Verify, Generate, Critique) passed retry_prompt=None
        # to write_with_retry, so one rejected record left that phase with no
        # record at all and no second attempt, even though run_quick's own
        # stop rule never reads the SelectionRecord back and so never noticed.
        # Scripts a first SelectionRecord with a free-text excluded[].reason
        # (invalid: not one of the schema's five enum values) followed by a
        # corrected one, and asserts the run both reaches a solution and the
        # ledger actually holds a valid SelectionRecord, not zero.
        c9 = _canned()
        bad_selection = dict(c9["selection"][0])
        bad_selection["excluded"] = [{"candidate_id": "cand-001", "reason": "loses to B0 on every measured criterion"}]
        script9 = _happy_path_script()
        script9[("select", "selector")] = [[bad_selection], c9["selection"]]
        runner9 = FakeRoleRunner(script9)
        result9 = run_quick("Duplicate accounts from whitespace; legacy_ids.py is frozen.", tmp_path,
                             budget_usd=5.0, timeout=30, runner_factory=lambda _r: runner9, run_id="s9")
        check(result9.outcome == "solution", f"scenario 9: expected outcome 'solution', got {result9.outcome!r}")
        ledger9 = [json.loads(line) for line in (result9.run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
        check(any(r["type"] == "SelectionRecord" for r in ledger9),
              "scenario 9: a corrected SelectionRecord should reach the ledger after one retry, got none")

        # --- Scenario 10: a role runner out of budget closes with a gap ---
        # Direct regression test for the second fleet batch (D58): three
        # runs died with a traceback when the platform aborted their last
        # role call on budget. BudgetExhausted from the runner must end the
        # run as a GapReport with termination budget_spent, REPORT.md and
        # all, not propagate.
        class BrokeRunner(FakeRoleRunner):
            def __call__(self, phase, role, prompt, *, timeout):
                if phase == "critique":
                    raise BudgetExhausted("USD 0.2000 left, under the USD 0.50 a role call needs")
                return super().__call__(phase, role, prompt, timeout=timeout)
        runner10 = BrokeRunner(_happy_path_script())
        result10 = run_quick("Duplicate accounts from whitespace; legacy_ids.py is frozen.", tmp_path,
                              budget_usd=5.0, timeout=30, runner_factory=lambda _r: runner10, run_id="s10")
        check(result10.outcome == "gap" and result10.record.get("termination") == "budget_spent",
              f"scenario 10: BudgetExhausted closes as a budget_spent gap, got {result10.outcome!r} "
              f"{result10.record.get('termination')!r}")
        check((result10.run_dir / "REPORT.md").exists() and "budget_spent" in (result10.run_dir / "REPORT.md").read_text(encoding="utf-8"),
              "scenario 10: the gap run still writes REPORT.md naming the termination")

        # --- Scenario 11: a role's output that never converges closes as
        # a gap, REPORT.md and all, instead of the traceback it left
        # before (audit A15, docs/AUDIT-2026-09-16.md). The Framer
        # replies with zero records for the initial Frame call; since
        # nothing was rejected (there is nothing to reject), no retry
        # fires and _one_of raises RoleOutputMismatch immediately.
        script11 = {("frame", "framer"): [[]]}
        result11 = run_quick("A problem whose Framer never produces a FrameRecord.", tmp_path,
                              budget_usd=5.0, timeout=30,
                              runner_factory=lambda _r: FakeRoleRunner(script11), run_id="s11")
        check(result11.outcome == "gap" and result11.record.get("termination") == "no_improvement",
              f"scenario 11: a RoleOutputMismatch closes as a no_improvement gap, got "
              f"{result11.outcome!r} {result11.record.get('termination')!r}")
        check((result11.run_dir / "REPORT.md").exists(),
              "scenario 11: the gap run still writes REPORT.md rather than propagating the traceback")

    return (not problems, problems)


# --------------------------------------------------------------------------
# CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--problem", type=Path, help="path to a text file with the problem statement")
    ap.add_argument("--project", type=Path, help="consumer project; runs/<id>/ is created inside it")
    ap.add_argument("--mode", choices=["quick"], default="quick")
    ap.add_argument("--budget-usd", type=float, default=4.0,
                     help="default 4.0: the measured quick-mode mean is USD 2.623 with a max of 2.923 "
                          "(src/cost_table.json controller), and three recorded runs died on a 3.0 "
                          "budget with about 3 percent headroom over that max (audit A14, "
                          "docs/AUDIT-2026-09-16.md); 4.0 leaves headroom over the measured max instead")
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--elapsed-limit-s", type=float, help="run dispatch deadline; each call uses the smaller remaining timeout")
    ap.add_argument("--max-output-tokens", type=int, default=8192,
                    help="per-request Claude Code output setting (default 8192); not a total token or invoice cap")
    maintenance = ap.add_mutually_exclusive_group()
    maintenance.add_argument("--recover-run", type=Path, help="recover accounting/reporting only; never replay provider calls")
    maintenance.add_argument("--cancel-run", type=Path, help="persist cancellation; running calls retain their timeouts and allowances")
    ap.add_argument("--reconcile-invocation", help="invocation ID within --recover-run, backed by terminal billing evidence")
    ap.add_argument("--final-cost-usd", type=float)
    ap.add_argument("--evidence", help="reference to terminal provider usage; never assume timeout means zero cost")
    ap.add_argument("--record", action="store_true", help="write test/results/<date>-system-controller-<run-id>.md")
    ap.add_argument("--dry-run", action="store_true", help="print the phase plan; make no claude -p calls")
    ap.add_argument("--selftest", action="store_true", help="run the canned-record self-test; no claude -p calls")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.reconcile_invocation is not None or args.final_cost_usd is not None or args.evidence is not None:
        if not args.recover_run or not args.reconcile_invocation or args.final_cost_usd is None or not args.evidence:
            ap.error("reconciliation requires --recover-run, --reconcile-invocation, --final-cost-usd and --evidence together")
    if args.recover_run or args.cancel_run:
        try:
            if args.cancel_run:
                budget = DispatchBudget(args.cancel_run / "dispatch-budget.json")
                budget.cancel()
                print("Cancellation saved. Running calls may finish and incur charges; allowances remain held.")
            else:
                status = recover_run(args.recover_run, invocation_id=args.reconcile_invocation,
                                     final_cost_usd=args.final_cost_usd, evidence=args.evidence)
                print(json.dumps(status, indent=2))
            return 0
        except (BudgetError, LedgerLockTimeout) as exc:
            ap.error(str(exc))

    if args.selftest:
        ok, problems = selftest(verbose=args.verbose)
        if ok:
            print("selftest: PASS, 12 scenarios")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.dry_run:
        print(f"mode: {args.mode}")
        print(f"budget: USD {args.budget_usd}")
        print("phases: intake (code) -> frame (opus/high) -> verify loop, ceiling one tool call "
              "(sonnet/medium) -> controller stability check (sonnet/low, --json-schema) -> "
              "controller family selection (sonnet/low, --json-schema) -> generate x3 parallel "
              "(sonnet/high) -> critique (opus/medium) -> select (sonnet/medium) -> close (code)")
        print(f"runs/<id>/ would be created inside {args.project}" if args.project else
              "runs/<id>/ would be created inside --project (not given; pass one for a real preview)")
        return 0

    if not args.problem or not args.project:
        ap.error("--problem and --project are required unless --selftest or --dry-run is given")

    problem_text = args.problem.read_text(encoding="utf-8").strip()
    runner_factory = lambda remaining: LiveRoleRunner(args.project, remaining, max_output_tokens=args.max_output_tokens)  # noqa: E731
    try:
        result = run_quick(problem_text, args.project, args.budget_usd, args.timeout, runner_factory,
                           elapsed_limit_s=args.elapsed_limit_s)
    except (BudgetError, ValueError) as exc:
        ap.error(str(exc))

    print(f"outcome: {result.outcome}")
    print(f"run directory: {result.run_dir}")
    print(f"calls: {result.calls}, known cost: USD {result.total_cost_usd:.4f}, "
          f"reserved: USD {result.reserved_usd:.4f}, accounting complete: {result.accounting_complete}")
    if result.outcome == "solution":
        print(f"winner: {result.record['candidate_id']} ({result.record['technique']})")
    else:
        print(f"termination: {result.record.get('termination')}")

    if args.record:
        # Inside result.run_dir itself, never under REPO_ROOT / "test" /
        # "results": in an installed bundle REPO_ROOT resolves to the
        # consumer's own project root (this file's own path, two parents
        # up), which is this repository's own results layout, not
        # theirs, and every Controller fire would otherwise leave a file
        # under <consumer>/test/results/ that belongs to no one there
        # (audit A13, docs/AUDIT-2026-09-16.md). result.run_dir is
        # already unique per run id, so no collision guard is needed.
        out = result.run_dir / "RECORD.md"
        lines = [f"# Controller run, {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}, {result.run_dir.name}", "",
                 f"Outcome: {result.outcome}. Calls: {result.calls}. Cost: USD {result.total_cost_usd:.4f}. "
                 f"Run directory: `{result.run_dir}`.", "", "```json",
                 json.dumps(result.record, indent=2, ensure_ascii=False), "```"]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"recorded {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
