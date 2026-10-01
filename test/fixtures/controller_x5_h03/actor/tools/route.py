#!/usr/bin/env python3
"""Resolve a task assessment to a worker cell, from data, not from a prompt.

Responsible for: the routing function `docs/CLASSIFIER-DESIGN.md` specifies
(D39, `docs/DECISIONS.md`). Reads `src/routing_table.json`, an ordered list
of rules, and returns the first rule whose conditions match the given
assessment. The table is data so `generate_workers.py`, `check.py` and this
script share one source instead of three parsers of `ROUTING.md`'s prose.

Deliberately does not: read `ROUTING.md` itself, decide the mechanism a
live session uses to obtain an assessment (that is `ROUTING.md` section 1's
job; this module only resolves one once it has it), or validate that the
table itself is well-formed beyond what resolution needs (`check.py`'s
ROUTE-TOTAL and ROW-BACKED checks do that).

The one non-obvious thing, current since D44/D45 collapsed the table to
two rules (`docs/AUDIT-2026-09-16.md` audit A8, correcting a docstring
that still described the eleven-rule table D44 replaced): `frontier`
matches only `prior_failure: failed_at_xhigh` and is listed first so it
overrides everything else; `floor` names no conditions at all and so
matches every triple that reaches it, which is every triple that is not
the frontier case. `self_directed` is still accepted and still recorded
in a `--record`/`--spawn` ledger entry (`docs/DECISIONS.md` D64: kept for
the record, a schema-forced classifier measured it firing on 38 percent
of sonnet's verdicts against a 6 percent base rate, so it is not trusted
input), but it is not an input to resolution any more: no rule in the
current table names it in its conditions. Everything above the floor
that a task ever reaches now comes from `plan()`'s ledger-aware ladder
below, not from a second static rule.

Usage:
    python3 tools/route.py --sensitivity structured --horizon short --blast contained
    python3 tools/route.py --sensitivity open --horizon long --blast consequential
        (both resolve to worker-sonnet-low: the floor matches every triple)
    python3 tools/route.py --sensitivity open --horizon long --blast consequential \\
        --prior-failure failed_at_xhigh
        (the frontier rule: worker-opus-max, reachable only this way)

    Ledger-aware routing and outcome recording (docs/PLAN-2.md Stage 2,
    docs/ROUTING-2-DESIGN.md) and pending-worker tracking across a
    compaction (docs/PLAN-3.md Stage B, docs/COMPACTION-DESIGN.md):
    python3 tools/route.py --from-line "<assessment line>" --project . --explain
    python3 tools/route.py --spawn --from-line "<line>" --project . \\
        --task-slug refactor-parser --first-cell worker-sonnet-low --worker-name refactor-parser \\
        --acceptance-contract acceptance-contract.json
    python3 tools/route.py --record --pending led-042 --project . \\
        --outcome pass --cost-usd 0.17 --wall-clock-s 52 \\
        --attempt-json '{"requested_cell":"worker-sonnet-low",...}'
    python3 tools/route.py --review-acceptance led-042 --project . \\
        --review-decision pass --reviewer "operator" --review-notes "Rubric met"
    python3 tools/route.py --recover --project .

    Explicit version-2 migration and byte-exact reversal:
    python3 tools/route.py --project . --migrate-ledger-v2 --dry-run
    python3 tools/route.py --project . --migrate-ledger-v2
    python3 tools/route.py --project . --restore-ledger-backup \\
        .claude/routing-ledger.jsonl.pre-v2.bak

    The session pointer, written from a SessionStart hook's own stdin
    (docs/COMPACTION-DESIGN.md section 13.4), so fill_context can scope a
    transcript search to the current session rather than every session
    under the project:
    python3 tools/route.py --session-pointer --project . < hook-input.json
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterator, Literal, TypedDict

import acceptance as acceptance_lib

REPO_ROOT = Path(__file__).resolve().parent.parent
TABLE_PATH = REPO_ROOT / "src" / "routing_table.json"

Sensitivity = Literal["mechanical", "structured", "open"]
Horizon = Literal["short", "medium", "long"]
Blast = Literal["contained", "consequential"]
PriorFailure = Literal["none", "failed_at_xhigh"]


class Rule(TypedDict, total=False):
    id: str
    text: str
    conditions: dict[str, list]
    worker: str
    also_acceptable: list[str]
    escalation_only: bool


class RoutingError(Exception):
    """Base for every error this module raises. Never caught by callers with
    a bare except; each subclass carries the offending value."""


class UnknownAxisValue(RoutingError):
    def __init__(self, axis: str, value: str, allowed: list[str]) -> None:
        super().__init__(f"{axis}={value!r} is not one of {allowed}")
        self.axis, self.value, self.allowed = axis, value, allowed


class NoRuleMatches(RoutingError):
    """A documented gap (docs/DECISIONS.md) or an undocumented one; the
    caller distinguishes the two via `documented_gap_reason`."""
    def __init__(self, sensitivity: str, horizon: str, blast: str, reason: str | None) -> None:
        self.sensitivity, self.horizon, self.blast = sensitivity, horizon, blast
        self.documented_gap_reason = reason
        msg = (f"no rule covers ({sensitivity}, {horizon}, {blast})"
               + (f"; documented gap: {reason}" if reason else "; UNDOCUMENTED gap"))
        super().__init__(msg)


def load_table(path: Path = TABLE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_axes(table: dict, sensitivity: str, horizon: str, blast: str,
                    self_directed: bool, prior_failure: str) -> None:
    axes = table["axes"]
    checks = (("sensitivity", sensitivity, axes["sensitivity"]),
              ("horizon", horizon, axes["horizon"]),
              ("blast", blast, axes["blast"]),
              ("prior_failure", prior_failure, axes["prior_failure"]))
    for name, value, allowed in checks:
        if value not in allowed:
            raise UnknownAxisValue(name, value, allowed)
    if not isinstance(self_directed, bool):
        raise UnknownAxisValue("self_directed", str(self_directed), ["true", "false"])


def _matches(rule: Rule, values: dict[str, object]) -> bool:
    """A rule matches when, for every axis it names in `conditions`, the
    given value is in the rule's allowed list. An axis the rule does not
    name matches any value ("any horizon" in ROUTING.md's own words)."""
    for axis, allowed in rule.get("conditions", {}).items():
        if values[axis] not in allowed:
            return False
    return True


def matching_rules(sensitivity: Sensitivity, horizon: Horizon, blast: Blast,
                    self_directed: bool = False, prior_failure: PriorFailure = "none",
                    table: dict | None = None) -> list[Rule]:
    """Every rule matching this assessment, in table order, not just the first.

    `resolve` below only needs the first, but the harness's ROUTE-TOTAL check
    uses this to assert the table is a genuine partition at the values that
    are supposed to be unambiguous: at most one non-frontier rule should ever
    match a given (sensitivity, horizon, blast, self_directed) combination.
    More than one would mean two rules silently overlap and the answer
    depends on list order, which first-match-wins would hide rather than
    catch.
    """
    table = table if table is not None else load_table()
    _validate_axes(table, sensitivity, horizon, blast, self_directed, prior_failure)
    values = {"sensitivity": sensitivity, "horizon": horizon, "blast": blast,
              "self_directed": self_directed, "prior_failure": prior_failure}
    return [rule for rule in table["rules"] if _matches(rule, values)]


def resolve(sensitivity: Sensitivity, horizon: Horizon, blast: Blast,
            self_directed: bool = False, prior_failure: PriorFailure = "none",
            table: dict | None = None) -> Rule:
    """Return the first rule matching this assessment, or raise NoRuleMatches.

    Raises UnknownAxisValue for any value outside the table's own enumerated
    axes (`table["axes"]`) rather than silently falling through to a gap,
    since an unrecognised value is an input defect, not routing coverage.
    """
    table = table if table is not None else load_table()
    matches = matching_rules(sensitivity, horizon, blast, self_directed, prior_failure, table)
    if matches:
        return matches[0]
    reason = None
    for gap in table.get("documented_gaps", []):
        gc = gap["conditions"]
        if (gc.get("sensitivity", sensitivity) == sensitivity
                and gc.get("horizon", horizon) == horizon
                and gc.get("blast", blast) == blast):
            reason = gap["reason"]
            break
    raise NoRuleMatches(sensitivity, horizon, blast, reason)


# Cost order for posterior()'s rung sort below (D64). Identical to
# benchmark.py's own LADDER; duplicated rather than shared, because both
# scripts are meant to stand alone (the same rationale generate_workers.py's
# bundle_tag() and score_routing.py's wilson_interval() already give for
# their own duplicated helpers). Does not include worker-opus-max or
# worker-fable-max (the frontier row, reached only via prior_failure, never
# a ladder rung) or the cells ROUTING.md's constraints call rarely right
# (worker-sonnet-max, worker-fable-low, worker-fable-medium), since no
# bucket's default ladder or steering activation ever names those five.
#
# Formerly also served resolve_two_axis(), the two-axis classifier variant
# (docs/CLASSIFIER-DESIGN.md), deleted here (2026-09-16, docs/PLAN-6.md
# D.1, audit A9, A21, A22): D40 rejected the two-axis design and nothing
# but that function and score_routing.py's --axes 2 mode ever called it.
COST_ORDER = (
    "worker-sonnet-low",
    "worker-sonnet-medium",
    "worker-sonnet-high",
    "worker-sonnet-xhigh",
    "worker-opus-high",
    "worker-opus-xhigh",
    "worker-fable-xhigh",
)


# --------------------------------------------------------------------------
# Complexity routing with a per-project ledger (docs/PLAN-2.md Stage 2,
# docs/ROUTING-2-DESIGN.md, D64). The functions above resolve an assessment
# to a cell from the static table alone; everything below additionally
# reads src/routing_priors.json (Beta priors per bucket, seeded from the
# benchmark) and a project's own `.claude/routing-ledger.jsonl`, so the
# same assessment can resolve differently once a project has outcomes of
# its own. Nothing above this line is used by, or changed by, what follows.

PRIORS_PATH = REPO_ROOT / "src" / "routing_priors.json"
COST_TABLE_PATH = REPO_ROOT / "src" / "cost_table.json"
LEDGER_FILENAME = ".claude" + "/" + "routing-ledger.jsonl"

# The two assessment-line formats the replay harness's recorded results
# actually contain (docs/ROUTING-2-DESIGN.md section 1): the two-stage
# design's own five-field line, and the prose router's three-field line
# with a worker name and an action instead of self_directed/prior_failure.
# Identical to score_routing.py's TWO_STAGE_RE_3AXES and VERDICT_RE; not
# imported from there because route.py is meant to stand alone (the same
# reason bundle_tag() and wilson_interval() were duplicated before they
# moved to claudep.py).
_TWO_STAGE_LINE_RE = re.compile(
    r"assessment:\s*(?P<sensitivity>\w+)\s*,\s*(?P<horizon>\w+)\s*,\s*(?P<blast>\w+)\s*;\s*"
    r"self_directed:\s*(?P<self_directed>true|false)\s*;\s*"
    r"prior_failure:\s*(?P<prior_failure>none|failed_at_xhigh)",
    re.IGNORECASE,
)
_PROSE_LINE_RE = re.compile(
    r"assessment:\s*(?P<sensitivity>\w+)\s*,\s*(?P<horizon>\w+)\s*,\s*(?P<blast>\w+)\s*;\s*"
    r"worker:\s*(?P<worker>[\w-]+)\s*;\s*action:\s*(?P<action>\w+)",
    re.IGNORECASE,
)


class AssessmentLineError(RoutingError):
    def __init__(self, line: str) -> None:
        super().__init__(f"could not parse an assessment from: {line!r}")
        self.line = line


def parse_assessment_line(line: str) -> dict:
    """Parse either recorded assessment-line format into the five fields
    `plan()` needs. The prose format carries no self_directed field, which
    defaults to the common case (false), the same default `resolve()`
    already uses for a caller with only the three assessment axes.

    The prose format also carries no prior_failure field: the frontier row
    was reached in that format by the model directly naming
    `worker-opus-max` or `worker-fable-max`, not by any axis (found while
    building the replay harness, docs/PLAN-2.md Stage 2.3, D65: F14's
    recorded prose lines all read "open, long, contained", never
    consequential, and never carry a failure signal on the triple at all).
    A prose line naming one of those two workers is therefore treated as
    prior_failure="failed_at_xhigh"; naming any other worker is "none",
    since nothing else in the prose format can express it."""
    m = _TWO_STAGE_LINE_RE.search(line)
    if m:
        return {"sensitivity": m["sensitivity"].lower(), "horizon": m["horizon"].lower(),
                "blast": m["blast"].lower(), "self_directed": m["self_directed"].lower() == "true",
                "prior_failure": m["prior_failure"].lower()}
    m = _PROSE_LINE_RE.search(line)
    if m:
        worker = m["worker"].lower()
        prior_failure = "failed_at_xhigh" if worker in ("worker-opus-max", "worker-fable-max") else "none"
        return {"sensitivity": m["sensitivity"].lower(), "horizon": m["horizon"].lower(),
                "blast": m["blast"].lower(), "self_directed": False, "prior_failure": prior_failure}
    raise AssessmentLineError(line)


def load_priors(path: Path = PRIORS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_cost_table(path: Path = COST_TABLE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def default_ledger_path(project: Path) -> Path:
    return project / LEDGER_FILENAME


def load_ledger(path: Path) -> list[dict]:
    """Read a routing ledger (docs/ROUTING-2-DESIGN.md section 2). A
    missing file is an empty ledger, the correct state for a project with
    no routed tasks yet, not an error. A line that fails to parse is
    skipped with a warning, as `claudep.Checkpoint.load` treats a partial
    write from an interrupted append, rather than aborting the whole load."""
    if not path.exists():
        return []
    entries = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            print(f"warning: {path} line {lineno} did not parse (a partial write from an "
                  "interrupted append?); ignoring it", file=sys.stderr)
            continue
        version = entry.get("ledger_version", 0) if isinstance(entry, dict) else None
        if version not in (0, 1, 2):
            raise RoutingError(
                f"cannot read {path} line {lineno}: unsupported ledger_version {version!r}; "
                "upgrade this bundle or restore a compatible ledger"
            )
        entries.append(entry)
    return entries


class LedgerLockTimeout(RoutingError):
    def __init__(self, path: Path, timeout_s: float) -> None:
        super().__init__(f"timed out after {timeout_s:.1f}s waiting for ledger lock {str(path)!r}; "
                         "retry after the other route.py process finishes")


@contextlib.contextmanager
def ledger_lock(path: Path, timeout_s: float = 10.0) -> Iterator[None]:
    """Hold a cross-process exclusive lock for one complete ledger transaction.

    The sibling lock file is persistent but the operating-system lock is not:
    it is released when the process exits, including after a crash. This avoids
    stale lock-directory recovery while keeping JSONL as the inspectable source
    of truth. Every mutating operation acquires this lock before reading IDs or
    current state and holds it through the durable write/replace.
    """
    if timeout_s < 0:
        raise ValueError(f"ledger lock timeout must be non-negative, got {timeout_s!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    deadline = time.monotonic() + timeout_s
    acquired = False
    try:
        while not acquired:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise LedgerLockTimeout(lock_path, timeout_s)
                time.sleep(0.01)
        yield
    finally:
        if acquired:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _atomic_write_ledger(path: Path, lines: list[str]) -> None:
    """Durably replace a ledger using a unique sibling temporary file."""
    data = "".join(line.rstrip("\r\n") + "\n" for line in lines).encode("utf-8")
    _atomic_write_bytes(path, data)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Durably replace one file while leaving the old bytes intact on failure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    finally:
        if tmp.exists():
            tmp.unlink()


def _ledger_rows(path: Path) -> list[tuple[dict | None, str]]:
    """Return parsed rows with their original text so rewrites preserve damage."""
    if not path.exists():
        return []
    rows: list[tuple[dict | None, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line) if line.strip() else None
        except json.JSONDecodeError:
            value = None
        rows.append((value if isinstance(value, dict) else None, line))
    return rows


def append_ledger_entry(path: Path, entry: dict) -> None:
    """Append a caller-assigned record without permitting a duplicate id."""
    if not isinstance(entry, dict) or not entry.get("id"):
        raise ValueError("ledger entry must be an object with a non-empty id")
    with ledger_lock(path):
        entries = load_ledger(path)
        if any(row.get("id") == entry["id"] for row in entries):
            raise RoutingError(f"ledger entry id {entry['id']!r} already exists in {str(path)!r}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def create_ledger_entry(path: Path, entry: dict) -> dict:
    """Assign and append the next ledger id within one locked transaction."""
    if "id" in entry:
        raise ValueError("create_ledger_entry assigns id; remove the caller-supplied id")
    with ledger_lock(path):
        completed = {**entry, "id": next_ledger_id(load_ledger(path))}
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(completed, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return completed


class LedgerEntryNotFound(RoutingError):
    def __init__(self, entry_id: str) -> None:
        super().__init__(f"no ledger entry with id {entry_id!r}")


class LedgerEntryNotPending(RoutingError):
    def __init__(self, entry_id: str, outcome: str) -> None:
        super().__init__(f"ledger entry {entry_id!r} is not pending (final_outcome already {outcome!r})")


def complete_ledger_entry(path: Path, entry_id: str, updates: dict) -> dict:
    """Complete a `--spawn`-created pending entry in place
    (docs/COMPACTION-DESIGN.md section 4), rather than appending a second
    record for the same task. The operating-system lock covers read,
    status check, merge and atomic replacement. Unparseable lines are
    retained exactly rather than disappearing during a valid update.

    Replaying the same field updates after a lost acknowledgement is
    idempotent. A conflicting second result raises LedgerEntryNotPending;
    a missing id raises LedgerEntryNotFound. A unique sibling temporary
    file avoids collisions between separate project sessions, and an
    interrupted replace leaves the original ledger intact."""
    with ledger_lock(path):
        rows = _ledger_rows(path)
        for i, (entry, original) in enumerate(rows):
            if entry is None or entry.get("id") != entry_id:
                continue
            if entry.get("final_outcome") != "unknown":
                if all(entry.get(key) == value for key, value in updates.items()):
                    return entry
                raise LedgerEntryNotPending(entry_id, entry.get("final_outcome"))
            completed = {**entry, **updates}
            rows[i] = (completed, json.dumps(completed, ensure_ascii=False))
            _atomic_write_ledger(path, [line for _, line in rows])
            return completed
        raise LedgerEntryNotFound(entry_id)


_PENDING_NOTE_PREFIX = "pending: "


def pending_worker_name(entry: dict) -> str:
    notes = entry.get("notes") or ""
    if notes.startswith(_PENDING_NOTE_PREFIX):
        return notes[len(_PENDING_NOTE_PREFIX):].strip()
    return notes.strip() or "(unnamed)"


def next_ledger_id(ledger: list[dict]) -> str:
    n = 0
    for entry in ledger:
        eid = entry.get("id", "")
        if isinstance(eid, str) and eid.startswith("led-"):
            try:
                n = max(n, int(eid[4:]))
            except ValueError:
                continue
    return f"led-{n + 1:03d}"


_ATTEMPT_INPUT_FIELDS = {
    "invocation_id", "parent_invocation_id", "requested_cell", "actual_model",
    "effort_evidence", "bundle_version", "policy_version", "started_at",
    "finished_at", "execution_status", "outcome", "wall_clock_s", "usage",
}
_TERMINAL_ATTEMPT_STATES = {"completed", "failed", "cancelled", "interrupted"}
_ATTEMPT_STATES = _TERMINAL_ATTEMPT_STATES | {"pending", "running"}


def _empty_usage(cost_usd: float | None = None, *, source: str = "unknown") -> dict:
    return {"input_tokens": None, "cache_creation_input_tokens": None,
            "cache_read_input_tokens": None, "output_tokens": None,
            "cost_usd": cost_usd, "currency": "USD" if cost_usd is not None else None,
            "cost_source": source, "price_snapshot": None, "includes_descendants": None}


def _normalise_attempt(raw: dict, sequence: int, default_cell: str,
                       default_outcome: str = "unknown") -> dict:
    """Validate and fill one version-2 attempt from CLI or migration input."""
    if not isinstance(raw, dict):
        raise RoutingError(f"attempt {sequence} must be a JSON object, got {type(raw).__name__}")
    unknown = set(raw) - _ATTEMPT_INPUT_FIELDS
    if unknown:
        raise RoutingError(f"attempt {sequence} has unsupported field(s) {sorted(unknown)}")
    cell = raw.get("requested_cell", default_cell)
    if not isinstance(cell, str) or not re.fullmatch(r"(?:controller|worker-[a-z]+-[a-z]+)", cell):
        raise RoutingError(f"attempt {sequence} requested_cell {cell!r} is not a worker cell or controller")
    outcome = raw.get("outcome", default_outcome)
    if outcome not in ("pass", "fail", "unknown"):
        raise RoutingError(f"attempt {sequence} outcome {outcome!r} is not pass, fail or unknown")
    status = raw.get("execution_status")
    if status is None:
        status = "completed" if outcome == "pass" else "failed" if outcome == "fail" else "interrupted"
    if status not in _ATTEMPT_STATES:
        raise RoutingError(f"attempt {sequence} execution_status {status!r} is not one of {sorted(_ATTEMPT_STATES)}")
    for key, limit in (("invocation_id", 200), ("parent_invocation_id", 200),
                       ("actual_model", 120), ("effort_evidence", 200),
                       ("bundle_version", 120), ("policy_version", 120)):
        value = raw.get(key)
        if value is not None and (not isinstance(value, str) or not value or len(value) > limit):
            raise RoutingError(f"attempt {sequence} {key} must be null or 1-{limit} characters, got {value!r}")
    timestamp_pattern = re.compile(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})?$")
    for key in ("started_at", "finished_at"):
        value = raw.get(key)
        if value is not None and (not isinstance(value, str) or not timestamp_pattern.fullmatch(value)):
            raise RoutingError(f"attempt {sequence} {key} must be null or an ISO 8601 timestamp, got {value!r}")
    wall = raw.get("wall_clock_s")
    if wall is not None and (isinstance(wall, bool) or not isinstance(wall, (int, float)) or wall < 0):
        raise RoutingError(f"attempt {sequence} wall_clock_s must be a non-negative number or null, got {wall!r}")
    usage = {**_empty_usage(), **(raw.get("usage") or {})}
    allowed_usage = set(_empty_usage())
    unexpected_usage = set(usage) - allowed_usage
    if unexpected_usage:
        raise RoutingError(f"attempt {sequence} usage has unsupported field(s) {sorted(unexpected_usage)}")
    for key in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
        value = usage[key]
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            raise RoutingError(f"attempt {sequence} usage.{key} must be a non-negative integer or null, got {value!r}")
    cost = usage["cost_usd"]
    if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0):
        raise RoutingError(f"attempt {sequence} usage.cost_usd must be a non-negative number or null, got {cost!r}")
    if usage["cost_source"] not in ("provider_reported", "price_derived", "measured_zero", "unknown"):
        raise RoutingError(f"attempt {sequence} usage.cost_source {usage['cost_source']!r} is invalid")
    if cost is None and usage["cost_source"] != "unknown":
        raise RoutingError(f"attempt {sequence} has no usage.cost_usd, so cost_source must be 'unknown'")
    if cost is not None and usage["cost_source"] == "unknown":
        raise RoutingError(f"attempt {sequence} has usage.cost_usd, so cost_source cannot be 'unknown'")
    if cost is not None and usage["currency"] != "USD":
        raise RoutingError(f"attempt {sequence} with usage.cost_usd must set currency to 'USD'")
    return {"id": f"att-{sequence:03d}", "sequence": sequence,
            "invocation_id": raw.get("invocation_id"),
            "parent_invocation_id": raw.get("parent_invocation_id"),
            "start_kind": "direct" if sequence == 1 else "escalation",
            "requested_cell": cell, "actual_model": raw.get("actual_model"),
            "effort_evidence": raw.get("effort_evidence"),
            "bundle_version": raw.get("bundle_version"),
            "policy_version": raw.get("policy_version"),
            "started_at": raw.get("started_at"), "finished_at": raw.get("finished_at"),
            "execution_status": status, "outcome": outcome,
            "wall_clock_s": wall, "usage": usage}


def parse_attempts(values: list[str], first_cell: str, escalations: list[dict], final_outcome: str,
                   task_cost_usd: float | None, task_wall_clock_s: float | None,
                   *, pending: bool = False) -> list[dict]:
    """Build version-2 attempts without fabricating multi-cell attribution."""
    if values:
        attempts = []
        for i, value in enumerate(values, start=1):
            try:
                raw = json.loads(value)
            except json.JSONDecodeError as exc:
                raise RoutingError(f"--attempt-json value {i} did not parse as JSON: {exc}") from exc
            default_cell = first_cell if i == 1 else (
                escalations[i - 2]["cell"] if i - 2 < len(escalations) else first_cell)
            default_outcome = ("fail" if i == 1 and escalations else
                               escalations[i - 2]["outcome"] if i > 1 and i - 2 < len(escalations) else "unknown")
            attempts.append(_normalise_attempt(raw, i, default_cell, default_outcome))
        expected_cells = [first_cell] + [item["cell"] for item in escalations]
        actual_cells = [item["requested_cell"] for item in attempts]
        if actual_cells != expected_cells:
            raise RoutingError(f"attempt cells {actual_cells!r} do not match routed cells {expected_cells!r}")
        return attempts

    if pending:
        return [_normalise_attempt({"execution_status": "pending"}, 1, first_cell)]

    cells = [first_cell] + [item["cell"] for item in escalations]
    outcomes = ["fail" if escalations else "unknown"] + [item["outcome"] for item in escalations]
    attempts = []
    for i, (cell, outcome) in enumerate(zip(cells, outcomes), start=1):
        raw: dict = {"outcome": outcome}
        if len(cells) == 1:
            raw["outcome"] = final_outcome
            raw["wall_clock_s"] = task_wall_clock_s
            raw["usage"] = _empty_usage(task_cost_usd,
                                          source="measured_zero" if task_cost_usd == 0 else
                                                 "provider_reported" if task_cost_usd is not None else "unknown")
        attempts.append(_normalise_attempt(raw, i, cell, outcome))
    return attempts


def _entry_v2_fields(first_cell: str, escalations: list[dict], final_outcome: str,
                     cost_usd: float | None, wall_clock_s: float | None,
                     attempt_values: list[str], *, pending: bool = False) -> dict:
    attempts = parse_attempts(attempt_values, first_cell, escalations, final_outcome,
                              cost_usd, wall_clock_s, pending=pending)
    status = ("running" if pending else "completed" if final_outcome == "pass" else
              "failed" if final_outcome == "fail" else "interrupted")
    return {"ledger_version": 2, "execution_status": status, "attempts": attempts,
            "acceptance": {"status": "unverified", "evidence": [],
                           "contract_version": "unverified-v1"}}


def migrate_ledger_v2(path: Path, *, dry_run: bool = False) -> dict:
    """Explicitly migrate legacy task rows to version 2 with an exact backup."""
    with ledger_lock(path):
        if not path.exists():
            raise RoutingError(f"cannot migrate missing ledger {str(path)!r}; record a task first")
        original = path.read_bytes()
        rows = _ledger_rows(path)
        invalid = [i for i, (entry, line) in enumerate(rows, start=1) if entry is None and line.strip()]
        if invalid:
            raise RoutingError(f"cannot migrate {str(path)!r}: unparseable JSON on line(s) {invalid}; "
                               "repair or preserve those rows before retrying")
        changed = 0
        migrated_lines: list[str] = []
        for entry, original_line in rows:
            if entry is None:
                migrated_lines.append(original_line)
                continue
            if entry.get("type") != "RoutingLedgerEntry":
                raise RoutingError(f"cannot migrate {str(path)!r}: record {entry.get('id')!r} has "
                                   f"unexpected type {entry.get('type')!r}")
            version = entry.get("ledger_version")
            if version == 2:
                migrated_lines.append(original_line)
                continue
            if version not in (0, 1):
                raise RoutingError(f"cannot migrate record {entry.get('id')!r}: unsupported "
                                   f"ledger_version {version!r}")
            escalations = entry.get("escalations") or []
            final_outcome = entry.get("final_outcome", "unknown")
            migrated = {**entry,
                        **_entry_v2_fields(entry.get("first_cell", ""), escalations, final_outcome,
                                           entry.get("cost_usd"), entry.get("wall_clock_s"), [],
                                           pending=final_outcome == "unknown")}
            if "context" not in migrated:
                migrated["context"] = dict(_NO_CONTEXT_OBSERVED)
            migrated_lines.append(json.dumps(migrated, ensure_ascii=False))
            changed += 1
        result = {"records": sum(1 for entry, _ in rows if entry is not None),
                  "changed": changed, "backup": None, "dry_run": dry_run}
        if dry_run or changed == 0:
            return result
        backup = path.with_suffix(path.suffix + ".pre-v2.bak")
        if backup.exists():
            if backup.read_bytes() != original:
                raise RoutingError(f"refusing to overwrite existing migration backup {str(backup)!r}; "
                                   "move or verify it before retrying")
        else:
            with backup.open("xb") as handle:
                handle.write(original)
                handle.flush()
                os.fsync(handle.fileno())
        _atomic_write_ledger(path, migrated_lines)
        result["backup"] = str(backup)
        return result


def restore_ledger_backup(path: Path, backup: Path, *, dry_run: bool = False) -> dict:
    """Restore exact backup bytes while retaining the current ledger once."""
    if not backup.is_file():
        raise RoutingError(f"ledger backup {str(backup)!r} is not a file")
    backup_bytes = backup.read_bytes()
    with ledger_lock(path):
        current = path.read_bytes() if path.exists() else b""
        result = {"ledger": str(path), "backup": str(backup), "bytes": len(backup_bytes),
                  "dry_run": dry_run}
        if dry_run:
            return result
        pre_restore = path.with_suffix(path.suffix + ".pre-restore.bak")
        if pre_restore.exists() and pre_restore.read_bytes() != current:
            raise RoutingError(f"refusing to overwrite existing pre-restore backup {str(pre_restore)!r}; "
                               "move or verify it before retrying")
        if not pre_restore.exists():
            with pre_restore.open("xb") as handle:
                handle.write(current)
                handle.flush()
                os.fsync(handle.fileno())
        _atomic_write_bytes(path, backup_bytes)
        result["pre_restore_backup"] = str(pre_restore)
        return result


def _beta_mean(alpha: float, beta: float, passes: int, fails: int) -> float:
    a, b = alpha + passes, beta + fails
    return a / (a + b)


def _is_compacted(entry: dict) -> bool:
    """True only when this entry confirms at least one compaction
    (docs/COMPACTION-DESIGN.md section 6, D68). An entry with no
    `context` at all (every `ledger_version` 0 entry, from before Stage
    C) or `context.compactions: null` (observed, but no signal found) is
    NOT compacted by this test: unknown is not evidence of no
    compaction, so it is excluded from `_is_compacted` but still counted
    normally in the capability posterior below, exactly as it was before
    this field existed."""
    return ((entry.get("context") or {}).get("compactions") or 0) >= 1


def _known_compaction_count(entry: dict) -> int | None:
    """The compaction count for the overflow posterior, or `None` when
    this entry's compaction status was never observed (`context.source
    == "none"`, or absent entirely on a `ledger_version` 0 entry): those
    entries contribute to neither the overflow successes nor its
    failures, the same "absence is not evidence" rule `_is_compacted`
    applies on the capability side."""
    context = entry.get("context")
    if not context or context.get("source") == "none":
        return None
    return context.get("compactions")


_EVIDENCE_IDENTITY_FIELDS = ("actual_model", "bundle_version", "policy_version",
                             "acceptance_contract_version")


def _parse_evidence_time(value: object) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _learning_observations(ledger: list[dict], bucket: str, *,
                           max_age_days: int | None = None,
                           now: dt.datetime | None = None) -> tuple[list[dict], dict]:
    """Return capability observations and explicit exclusion counts.

    Version-2 task claims train capability only when acceptance is pass/fail.
    Legacy rows remain a labelled compatibility population because historical
    benchmark ledgers predate acceptance fields. Cost accounting is separate
    and continues to retain failed or interrupted spending.
    """
    if max_age_days is not None and max_age_days < 0:
        raise ValueError(f"max_age_days must be non-negative or None, got {max_age_days!r}")
    reference = now or dt.datetime.now(dt.timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=dt.timezone.utc)
    cutoff = reference.astimezone(dt.timezone.utc) - dt.timedelta(days=max_age_days) if max_age_days is not None else None
    stats = {"entries_seen": 0, "compacted_excluded": 0, "unverified_excluded": 0,
             "age_excluded": 0, "unknown_outcome_excluded": 0,
             "legacy_claimed_observations": 0}
    observations: list[dict] = []

    for entry in ledger:
        if entry.get("bucket") != bucket:
            continue
        stats["entries_seen"] += 1
        if _is_compacted(entry):
            stats["compacted_excluded"] += 1
            continue
        attempts = entry.get("attempts")
        if isinstance(attempts, list):
            acceptance = entry.get("acceptance") or {}
            acceptance_status = acceptance.get("status")
            if not acceptance_lib.qualified(acceptance):
                stats["unverified_excluded"] += 1
                continue
            terminal = [a for a in attempts if isinstance(a, dict)
                        and a.get("execution_status") in _TERMINAL_ATTEMPT_STATES]
            terminal.sort(key=lambda a: a.get("sequence", 0))
            for index, attempt in enumerate(terminal):
                when = _parse_evidence_time(attempt.get("finished_at") or attempt.get("started_at"))
                if cutoff is not None and (when is None or when < cutoff):
                    stats["age_excluded"] += 1
                    continue
                outcome = attempt.get("outcome")
                if index == len(terminal) - 1:
                    outcome = acceptance_status
                if outcome not in ("pass", "fail"):
                    stats["unknown_outcome_excluded"] += 1
                    continue
                identity = {field: (acceptance.get("contract_version") if field == "acceptance_contract_version"
                                    else attempt.get(field))
                            for field in _EVIDENCE_IDENTITY_FIELDS}
                observations.append({"cell": attempt.get("requested_cell"), "outcome": outcome,
                                     "population": attempt.get("start_kind", "direct" if index == 0 else "conditional"),
                                     "identity": identity, "legacy": False})
            continue

        # Version 0/1 compatibility: these task outcomes were the only source
        # available to the existing benchmark backtest. Keep them distinct as
        # unknown-identity, claimed evidence rather than inventing verification.
        cells = [entry.get("first_cell")] + [e.get("cell") for e in (entry.get("escalations") or [])]
        outcomes = (["fail" if entry.get("escalations") else entry.get("final_outcome")]
                    + [e.get("outcome") for e in (entry.get("escalations") or [])])
        for index, (cell, outcome) in enumerate(zip(cells, outcomes)):
            if not cell or outcome not in ("pass", "fail"):
                stats["unknown_outcome_excluded"] += 1
                continue
            if cutoff is not None:
                when = _parse_evidence_time(entry.get("ts"))
                if when is None or when < cutoff:
                    stats["age_excluded"] += 1
                    continue
            observations.append({"cell": cell, "outcome": outcome,
                                 "population": "direct" if index == 0 else "conditional",
                                 "identity": {field: None for field in _EVIDENCE_IDENTITY_FIELDS},
                                 "legacy": True})
            stats["legacy_claimed_observations"] += 1
    return observations, stats


def _select_identity_observations(observations: list[dict], target: dict | None,
                                  include_incompatible: bool) -> tuple[list[dict], dict]:
    """Choose one exact identity cohort, or require an explicit override."""
    if include_incompatible:
        return observations, {"mode": "explicit_pool", "groups": len({_identity_key(o) for o in observations}),
                              "excluded": 0, "conflict": False}
    if target:
        selected = [o for o in observations
                    if all(o["identity"].get(k) == v for k, v in target.items() if v is not None)]
        return selected, {"mode": "exact", "target": target, "groups": len({_identity_key(o) for o in observations}),
                          "excluded": len(observations) - len(selected), "conflict": False}
    groups: dict[tuple, list[dict]] = {}
    for observation in observations:
        groups.setdefault(_identity_key(observation), []).append(observation)
    known = {key: rows for key, rows in groups.items() if any(value is not None for value in key)}
    if len(known) > 1:
        return [], {"mode": "exact", "groups": len(groups), "excluded": len(observations),
                    "conflict": True}
    if len(known) == 1:
        selected = next(iter(known.values()))
        return selected, {"mode": "exact", "groups": len(groups),
                          "excluded": len(observations) - len(selected), "conflict": False}
    selected = groups.get((None,) * len(_EVIDENCE_IDENTITY_FIELDS), [])
    return selected, {"mode": "legacy_unknown", "groups": len(groups),
                      "excluded": len(observations) - len(selected), "conflict": False}


def _identity_key(observation: dict) -> tuple:
    return tuple(observation["identity"].get(field) for field in _EVIDENCE_IDENTITY_FIELDS)


def posterior(priors: dict, ledger: list[dict], bucket: str, *,
              evidence_identity: dict | None = None,
              max_age_days: int | None = None,
              include_incompatible: bool = False,
              now: dt.datetime | None = None) -> dict:
    """Per-bucket posterior (docs/ROUTING-2-DESIGN.md section 3): a
    direct-start Beta mean for each cell, a separate rung mean conditional
    on every cheaper attempt having failed, and
    the active rung list in cost order, `default_ladder`'s cells plus
    any cell that has met the activation threshold from this bucket's
    own escalation history. Raises NoRuleMatches (reusing `resolve()`'s
    own exception, since it is the same kind of gap) for a bucket
    outside the eighteen `routing_priors.json` seeds.

    Version-2 capability rows require acceptance pass/fail, use exact
    model/bundle/policy/acceptance identities by default, and may be limited
    by age. Legacy rows remain a labelled unknown-identity compatibility
    population. Direct starts never update conditional escalation evidence.

    A confirmed-compacted entry (docs/COMPACTION-DESIGN.md section 6,
    D68) is excluded from the floor and rung counts above, since a
    compaction is evidence the task overflowed its cell's window, not
    evidence the cell lacked the capability to do the work; it instead
    feeds the bucket's overflow posterior, over every entry (any
    `first_cell`, any rung) whose compaction status is known at all."""
    bdata = priors["buckets"].get(bucket)
    if bdata is None:
        s, h, b = bucket.split("/") if bucket.count("/") == 2 else (bucket, bucket, bucket)
        raise NoRuleMatches(s, h, b, f"{bucket!r} is not one of the seeded buckets")

    all_entries = [e for e in ledger if e.get("bucket") == bucket]
    observations, evidence_stats = _learning_observations(
        ledger, bucket, max_age_days=max_age_days, now=now)

    by_population: dict[tuple[str, str], list[dict]] = {}
    for observation in observations:
        if observation.get("cell"):
            population = "conditional" if observation["population"] in ("conditional", "escalation") else "direct"
            by_population.setdefault((observation["cell"], population), []).append(observation)

    selected: dict[tuple[str, str], list[dict]] = {}
    identity_diagnostics: dict[str, dict] = {}
    for key, rows in by_population.items():
        chosen, diagnostic = _select_identity_observations(rows, evidence_identity, include_incompatible)
        selected[key] = chosen
        identity_diagnostics[f"{key[0]}:{key[1]}"] = diagnostic

    floor_prior = bdata["floor"]
    floor_rows = selected.get(("worker-sonnet-low", "direct"), [])
    floor_pass = sum(1 for row in floor_rows if row["outcome"] == "pass")
    floor_fail = sum(1 for row in floor_rows if row["outcome"] == "fail")
    floor_mean = _beta_mean(floor_prior["alpha"], floor_prior["beta"], floor_pass, floor_fail)

    default_weak_prior = {"alpha": 1.0, "beta": 1.0}  # uninformative: no bucket-specific
    # measurement exists for a rung the ledger alone activates, so it starts
    # at mean 0.5 and moves on that project's own evidence from there.
    rung_priors = bdata.get("rungs_given_failure_below", {})
    rungs: dict[str, dict] = {}
    seen_cells = {cell for cell, _ in by_population} | set(rung_priors)
    for cell in seen_cells:
        conditional_prior = rung_priors.get(cell, default_weak_prior)
        conditional_rows = selected.get((cell, "conditional"), [])
        direct_rows = selected.get((cell, "direct"), [])
        cp = sum(1 for row in conditional_rows if row["outcome"] == "pass")
        cf = sum(1 for row in conditional_rows if row["outcome"] == "fail")
        dp = sum(1 for row in direct_rows if row["outcome"] == "pass")
        df = sum(1 for row in direct_rows if row["outcome"] == "fail")
        conditional = {"mean": _beta_mean(conditional_prior["alpha"], conditional_prior["beta"], cp, cf),
                       "ledger_passes": cp, "ledger_fails": cf}
        direct = {"mean": _beta_mean(default_weak_prior["alpha"], default_weak_prior["beta"], dp, df),
                  "ledger_passes": dp, "ledger_fails": df}
        # Top-level values retain the legacy conditional interface used by
        # reports; new routing decisions name the population explicitly.
        rungs[cell] = {**conditional, "conditional": conditional, "direct": direct}

    steering = priors["steering"]
    base_ladder = [c for c in priors["default_ladder"] if c in COST_ORDER]
    activated = [cell for cell, m in rungs.items()
                 if cell not in base_ladder and cell in COST_ORDER
                 and (m["conditional"]["ledger_passes"] + m["conditional"]["ledger_fails"])
                     >= steering["steering_rung_activation_min_n"]
                 and m["conditional"]["mean"] >= steering["steering_rung_activation_min_pass"]]
    active_rungs = sorted(set(base_ladder) | set(activated), key=COST_ORDER.index)

    known_counts = [c for c in (_known_compaction_count(e) for e in all_entries) if c is not None]
    overflow_pass = sum(1 for c in known_counts if c >= 1)
    overflow_fail = sum(1 for c in known_counts if c == 0)
    overflow_prior = bdata["overflow"]
    overflow_mean = _beta_mean(overflow_prior["alpha"], overflow_prior["beta"], overflow_pass, overflow_fail)

    return {"bucket": bucket, "floor_mean": floor_mean, "floor_ledger_passes": floor_pass,
            "floor_ledger_fails": floor_fail, "rungs": rungs, "active_rungs": active_rungs,
            "overflow_mean": overflow_mean, "overflow_n": overflow_pass + overflow_fail,
            "overflow_compacted": overflow_pass,
            "evidence": {**evidence_stats, "max_age_days": max_age_days,
                         "identity_target": evidence_identity,
                         "include_incompatible": include_incompatible,
                         "identity_populations": identity_diagnostics}}


def _rung_pass_mean(post: dict, cell: str, population: str = "conditional") -> float:
    if cell == "worker-sonnet-low":
        return post["floor_mean"]
    rung = post["rungs"].get(cell, {})
    return (rung.get(population) or {"mean": rung.get("mean", 0.5)})["mean"]


def ledger_cell_means(ledger: list[dict], ledger_overrides_after: int, *,
                      evidence_identity: dict | None = None,
                      include_incompatible: bool = False) -> dict[str, dict]:
    """Per-cell `{cost_per_run_usd, wall_clock_s}` from a project's own
    version-2 attempts (any bucket), only for a compatible identity cohort
    and a cell with at least
    `ledger_overrides_after` measured terminal attempts (`routing_priors.json`
    `steering.ledger_overrides_after`, the same threshold `plan()` below
    now applies to its own projection). A cell short of that is absent
    from the return value, so the caller falls back to
    `src/cost_table.json` for it. Pending/running work and null measurements
    are excluded. Version 0/1 task totals remain usable only when one cell
    ran; multi-cell totals cannot be attributed honestly and are excluded.

    Moved here from `tools/handoff.py` (audit A5, docs/AUDIT-2026-09-16.md):
    `handoff.py`'s own projections already called this, but `plan()`'s
    `expected_ladder_cost`/`controller_decision` arithmetic, which
    `--explain` prints, read only `src/cost_table.json` and never this
    project's own measured costs, so a project could accumulate a
    hundred outcomes and `--explain` would still project against the
    generic priors this repository shipped. `handoff.py` now imports
    this function instead of defining its own copy."""
    if ledger_overrides_after < 1:
        raise ValueError(f"ledger_overrides_after must be at least 1, got {ledger_overrides_after!r}")
    per_cell: dict[str, list[dict]] = {}
    for entry in ledger:
        attempts = entry.get("attempts")
        if isinstance(attempts, list):
            acceptance = entry.get("acceptance") or {}
            for attempt in attempts:
                if not isinstance(attempt, dict) or attempt.get("execution_status") not in _TERMINAL_ATTEMPT_STATES:
                    continue
                cell = attempt.get("requested_cell")
                usage = attempt.get("usage") or {}
                cost, wall = usage.get("cost_usd"), attempt.get("wall_clock_s")
                if cell and cost is not None and wall is not None:
                    identity = {field: (acceptance.get("contract_version")
                                        if field == "acceptance_contract_version" else attempt.get(field))
                                for field in _EVIDENCE_IDENTITY_FIELDS}
                    per_cell.setdefault(cell, []).append({"cost": cost, "wall": wall,
                                                          "identity": identity})
            continue

        # Version 0/1 stored only a task total. It is attributable when
        # exactly one cell ran; multi-cell totals stay unknown by cell.
        if entry.get("final_outcome") not in ("pass", "fail"):
            continue
        if entry.get("escalations"):
            continue
        cell, cost, wall = entry.get("first_cell"), entry.get("cost_usd"), entry.get("wall_clock_s")
        if cell and cost is not None and wall is not None:
            per_cell.setdefault(cell, []).append({
                "cost": cost, "wall": wall,
                "identity": {field: None for field in _EVIDENCE_IDENTITY_FIELDS},
            })
    means = {}
    for cell, rows in per_cell.items():
        selected, _ = _select_identity_observations(
            rows, evidence_identity, include_incompatible)
        if len(selected) >= ledger_overrides_after:
            means[cell] = {"cost_per_run_usd": sum(r["cost"] for r in selected) / len(selected),
                           "wall_clock_s": sum(r["wall"] for r in selected) / len(selected),
                           "attempts_measured": len(selected)}
    return means


def expected_ladder_cost(post: dict, costs: dict, start_cell: str | None = None) -> dict:
    """Sequential expected cost and wall clock from the selected active rung:
    cost(rung) x P(reach rung), where P(reach) is the product of the
    failure probabilities of preceding execution rungs (the benchmark
    staircase only ever climbed after a failure, so a rung's measured
    rate already is this conditional; docs/ROUTING-2-DESIGN.md section 3,
    D64 point 2). A rung with no cost row (the frontier cells) is skipped
    in the sum and named in `unpriced_rungs`, not silently treated as
    free."""
    active = list(post["active_rungs"])
    if start_cell is None:
        start_cell = active[0] if active else "worker-sonnet-low"
    execution_rungs = active[active.index(start_cell):] if start_cell in active else [start_cell]
    e_cost, e_wall, p_reach = 0.0, 0.0, 1.0
    p_reach_by_rung: dict[str, float] = {}
    unpriced: list[str] = []
    for index, cell in enumerate(execution_rungs):
        row = costs["cells"].get(cell, {})
        cost, wall = row.get("cost_per_run_usd"), row.get("wall_clock_s")
        p_reach_by_rung[cell] = p_reach
        if cost is None:
            unpriced.append(cell)
        else:
            e_cost += cost * p_reach
            e_wall += (wall or 0) * p_reach
        p_reach *= (1 - _rung_pass_mean(post, cell, "direct" if index == 0 else "conditional"))
    return {"e_ladder_usd": round(e_cost, 4), "e_ladder_wall_s": round(e_wall, 1),
            "p_fail_all": round(p_reach, 4), "p_reach_by_rung": {k: round(v, 4) for k, v in p_reach_by_rung.items()},
            "unpriced_rungs": unpriced, "start_cell": start_cell,
            "execution_rungs": execution_rungs}


def controller_decision(priors: dict, post: dict, costs: dict, bucket: str,
                        start_cell: str | None = None) -> dict:
    """Whether the Controller pre-empts the ladder for this bucket
    (docs/ROUTING-2-DESIGN.md section 3, D64): a labelled risk-appetite
    policy naming sensitivity and blast, checked first, or expected-cost
    arithmetic otherwise. On the priors this repository ships, the
    arithmetic fires in no bucket; only the policy dial does, and only
    where it is enabled."""
    rule = priors["controller_rule"]
    ladder = expected_ladder_cost(post, costs, start_cell)
    controller_row = costs["controller"]
    controller_cost = controller_row["quick_mode_run_usd"] + controller_row["instantiation_usd"]
    unknown_terms = []
    if not controller_row.get("failed_runs_included", False):
        unknown_terms.append("controller failed-run cost is excluded from the measured mean")
    if controller_row.get("failure_retry_cost_usd") is None:
        unknown_terms.append("controller failure/retry cost is unmeasured")
    if controller_row.get("verification_cost_usd") is None:
        unknown_terms.append("acceptance verification cost is unmeasured")
    completeness = {"projection_complete": not unknown_terms and not ladder["unpriced_rungs"],
                    "unknown_terms": unknown_terms}
    sensitivity, horizon, blast = bucket.split("/")

    policy = rule["proactive_policy"]
    if (policy["enabled"] and sensitivity in policy["when"].get("sensitivity", ())
            and blast in policy["when"].get("blast", ())):
        return {**ladder, **completeness, "proactive": True, "reason": "policy", "controller_cost_usd": round(controller_cost, 4),
                "failure_cost_usd": None, "label": policy["label"]}

    failure_cost = (rule["failure_cost"]["consequential_usd"] if blast == "consequential"
                    else ladder["e_ladder_usd"])
    fires = ladder["e_ladder_usd"] + ladder["p_fail_all"] * failure_cost > controller_cost
    return {**ladder, **completeness, "proactive": fires, "reason": "expected_cost" if fires else "none",
            "controller_cost_usd": round(controller_cost, 4), "failure_cost_usd": round(failure_cost, 4),
            "label": None}


def plan(sensitivity: Sensitivity, horizon: Horizon, blast: Blast,
         self_directed: bool = False, prior_failure: PriorFailure = "none",
         priors: dict | None = None, ledger: list[dict] | None = None,
         costs: dict | None = None, *, evidence_identity: dict | None = None,
         max_evidence_age_days: int | None = None,
         include_incompatible_evidence: bool = False,
         use_qualified_default: bool = True) -> dict:
    """The one function an orchestrator calls (docs/ROUTING-2-DESIGN.md
    section 3): resolves an assessment plus a project's own ledger to the
    cell (or `"controller"`) to try first, the rest of the active ladder,
    the Controller's decision and why, and a cost/time projection. Falls
    straight to the frontier rung on `prior_failure`, exactly as
    `resolve()` already does, since that mechanism is unchanged by any of
    this. The first executed rung uses its direct posterior; later rungs use
    their conditional posterior.

    The projection uses this project's own measured cost and wall clock
    for a cell once its ledger holds `steering.ledger_overrides_after`
    entries there, via `ledger_cell_means()`, falling back to
    `src/cost_table.json` for any cell short of that (audit A5,
    docs/AUDIT-2026-09-16.md: this used to be true only of
    `tools/handoff.py`'s own projections, never of `--explain`'s). Capability
    evidence can be selected by exact identity and bounded by age; cost and
    capability eligibility remain separate.

    The shipped W09 default is the reserved-qualified B0 policy. It always
    starts at worker-sonnet-low, permits one same-cell repair, then one
    worker-opus-high fallback, and never invokes the Controller. The adaptive
    posterior remains available for diagnostics and historical B1 replay only;
    it cannot alter a default dispatch while `qualified_default` is enabled."""
    priors = priors if priors is not None else load_priors()
    costs = costs if costs is not None else load_cost_table()
    ledger = ledger if ledger is not None else []
    qualified = priors.get("qualified_default") or {}
    fixed_default = bool(
        use_qualified_default
        and qualified.get("policy_id") == "B0"
        and qualified.get("adaptive_routing_enabled") is False
    )

    if prior_failure == "failed_at_xhigh" and not fixed_default:
        frontier = resolve(sensitivity, horizon, blast, self_directed, prior_failure, table=None)["worker"]
        return {"first": frontier, "bucket": None, "ladder": [], "controller": None, "posterior": None,
                "overflow": None,
                "projection": {"cost_usd_expected": None, "wall_clock_s_expected": None,
                               "note": "frontier rung from prior_failure; unmeasured (src/cost_table.json)"}}

    bucket = f"{sensitivity}/{horizon}/{blast}"
    post = posterior(priors, ledger, bucket, evidence_identity=evidence_identity,
                     max_age_days=max_evidence_age_days,
                     include_incompatible=include_incompatible_evidence)
    ledger_means = ledger_cell_means(
        ledger, priors["steering"]["ledger_overrides_after"],
        evidence_identity=evidence_identity,
        include_incompatible=include_incompatible_evidence)
    effective_costs = costs
    if ledger_means:
        effective_costs = dict(costs)
        effective_costs["cells"] = {**costs["cells"], **ledger_means}
    if fixed_default:
        first = qualified["first_cell"]
        repair = qualified["repair_cell"]
        fallback = qualified["fallback_cell"]
        sequence = [first, repair, fallback]
        floor_row = effective_costs["cells"].get(first, {})
        fallback_row = effective_costs["cells"].get(fallback, {})
        floor_cost = floor_row.get("cost_per_run_usd")
        fallback_cost = fallback_row.get("cost_per_run_usd")
        floor_wall = floor_row.get("wall_clock_s")
        fallback_wall = fallback_row.get("wall_clock_s")
        p_fail = 1 - post["floor_mean"]
        expected_cost = None if floor_cost is None or fallback_cost is None else round(
            floor_cost + p_fail * floor_cost + p_fail * p_fail * fallback_cost, 4)
        expected_wall = None if floor_wall is None or fallback_wall is None else round(
            floor_wall + p_fail * floor_wall + p_fail * p_fail * fallback_wall, 1)
        steering = priors["steering"]
        advisory = (post["overflow_mean"] >= steering["overflow_advisory_min_mean"]
                    and post["overflow_n"] >= steering["overflow_advisory_min_n"])
        overflow = {
            "mean": round(post["overflow_mean"], 4),
            "n": post["overflow_n"],
            "advisory": advisory,
            "text": (f"{post['overflow_compacted']} of {post['overflow_n']} attempts in this "
                     f"bucket compacted; split the task or trim the handover before spawning {first}"
                     if advisory else None),
        }
        return {
            "first": first,
            "bucket": bucket,
            "policy": "B0",
            "ladder": sequence,
            "execution_ladder": sequence,
            "controller": None,
            "posterior": post,
            "overflow": overflow,
            "projection": {
                "cost_usd_expected": expected_cost,
                "wall_clock_s_expected": expected_wall,
                "note": "B0 fixed fallback: floor, one floor repair, then opus-high",
            },
        }
    min_pass = priors["steering"]["steering_first_rung_min_pass"]
    selected_worker = next(
        (c for c in post["active_rungs"] if _rung_pass_mean(post, c, "direct") >= min_pass),
        post["active_rungs"][0] if post["active_rungs"] else "worker-sonnet-low")
    decision = controller_decision(priors, post, effective_costs, bucket, selected_worker)

    if decision["proactive"]:
        first = "controller"
    else:
        first = selected_worker

    controller_cost = costs["controller"]["quick_mode_run_usd"] + costs["controller"]["instantiation_usd"]
    controller_wall = costs["controller"]["wall_clock_s"] + costs["controller"]["instantiation_wall_s"]
    if first == "controller":
        cost_expected, wall_expected = controller_cost, controller_wall
    else:
        cost_expected, wall_expected = decision["e_ladder_usd"], decision["e_ladder_wall_s"]

    steering = priors["steering"]
    advisory = (post["overflow_mean"] >= steering["overflow_advisory_min_mean"]
                and post["overflow_n"] >= steering["overflow_advisory_min_n"])
    overflow = {"mean": round(post["overflow_mean"], 4), "n": post["overflow_n"], "advisory": advisory,
                "text": (f"{post['overflow_compacted']} of {post['overflow_n']} attempts in this bucket "
                         f"compacted; split the task or trim the handover before spawning {first}"
                         if advisory else None)}

    return {"first": first, "bucket": bucket, "policy": "adaptive",
            "ladder": post["active_rungs"],
            "execution_ladder": decision["execution_rungs"], "controller": decision,
            "posterior": post, "overflow": overflow,
            "projection": {"cost_usd_expected": round(cost_expected, 4),
                            "wall_clock_s_expected": round(wall_expected, 1)}}


def plan_rigour(assessment: dict, project: Path, *, explicit_mode: str | None = None,
                session_id: str | None = None, selected_cell: str = "worker-sonnet-low",
                controller_profile: str = "standard", prior_controller_invocations: int = 0,
                public_passed: bool = False) -> dict:
    """Versioned R4 adapter; existing ``plan`` remains the qualified B0 API."""
    import controller_control
    import controller_policy

    task_revision = assessment.get("task_revision") if isinstance(assessment, dict) else None
    control = controller_control.resolve(
        project, explicit_mode=explicit_mode, session_id=session_id,
        task_revision=task_revision,
    )
    return controller_policy.decide(
        assessment, control, selected_cell=selected_cell,
        controller_profile=controller_profile,
        prior_controller_invocations=prior_controller_invocations,
        public_passed=public_passed,
    )


MAIN_USAGE_FILENAME = ".claude/context-main.json"
TASKS_USAGE_FILENAME = ".claude/context-tasks.json"
SESSION_POINTER_FILENAME = ".claude/session.json"


def default_main_usage_path(project: Path) -> Path:
    return project / MAIN_USAGE_FILENAME


def default_tasks_usage_path(project: Path) -> Path:
    return project / TASKS_USAGE_FILENAME


def default_session_pointer_path(project: Path) -> Path:
    return project / SESSION_POINTER_FILENAME


_NO_CONTEXT_OBSERVED = {"peak_tokens": None, "window": None, "compactions": None, "source": "none"}


def _claude_projects_slug(project: Path) -> str:
    """Best-effort guess at the directory name Claude Code derives under
    `~/.claude/projects/` from a project's absolute path: colons and path
    separators replaced with hyphens, matching this session's own
    observed project directory name. `src/LIFECYCLE.md`'s transcript path
    is itself observed, not documented (E7); this guess inherits the same
    caveat and is never the only source `fill_context` tries."""
    return re.sub(r"[:\\/]", "-", str(project.resolve()))


def _read_session_pointer(project: Path) -> dict | None:
    """Reads `.claude/session.json` (docs/COMPACTION-DESIGN.md section
    13.4), the file `--session-pointer` writes from a `SessionStart`
    hook's own input: `{"session_id", "transcript_path", "cwd", "event",
    "written_at"}`. Returns `None`, never raises, if the file does not
    exist or does not parse as a JSON object: this is the common case
    until a session actually runs the hook (the hook is new in this
    stage; every project this repository has run against so far has no
    such file), and every caller of this function must tolerate that
    gracefully rather than treat its absence as an error."""
    path = default_session_pointer_path(project)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _write_session_pointer(payload: dict, project: Path) -> None:
    """`--session-pointer`'s write side (docs/COMPACTION-DESIGN.md section
    13.4): takes a `SessionStart` hook's own JSON input (already parsed)
    and writes `.claude/session.json` under `project` as `{"session_id",
    "transcript_path", "cwd", "event", "written_at"}`. `event` is the
    hook input's `source` field (`docs/en/hooks`' common input fields;
    for `SessionStart` this carries the matcher value, `startup`,
    `resume`, `compact` or `clear`, matching the matcher names
    `src/settings.fragment.json` wires this same hook under). Atomic
    write, temp file then rename, the same shape
    `tools/context_probe.py`'s `_atomic_write_json` already uses, so a
    reader never sees a half-written file. Never raises on a payload
    missing expected keys: `.get` on an absent field just writes `None`,
    which `_read_session_pointer`'s callers already treat as license to
    fall back rather than a reason to error."""
    pointer = {
        "session_id": payload.get("session_id"),
        "transcript_path": payload.get("transcript_path"),
        "cwd": payload.get("cwd"),
        "event": payload.get("source"),
        "written_at": dt.datetime.now().isoformat(),
    }
    path = default_session_pointer_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(pointer, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def _resolve_transcript(project: Path, cell: str | None) -> Path | None:
    """Locates this cell's most recent subagent transcript
    (docs/COMPACTION-DESIGN.md section 13.1, D72). When
    `.claude/session.json` names a session whose `transcript_path`
    resolves to a real `subagents/` directory next to it, the search is
    scoped to that directory alone, so a decoy transcript from a
    different, unrelated session already sitting under the same projects
    slug is never picked by accident. Only when no pointer exists, or the
    one that does exist does not resolve to a real directory, does this
    fall back to searching every session under the guessed projects slug
    by cell and recency, exactly as D71 shipped (the design this section
    supersedes; see the retired `_find_transcript_compactions`'s own
    docstring, kept in git history, for why matching is on `cell`
    (`agentType`) rather than the worker's assigned name).

    Returns the sibling `.jsonl` of the newest matching
    `agent-*.meta.json`, or `None` if nothing matches; never raises."""
    if not cell:
        return None

    scoped_dir: Path | None = None
    pointer = _read_session_pointer(project)
    if pointer and pointer.get("transcript_path"):
        candidate = Path(pointer["transcript_path"]).parent / "subagents"
        if candidate.is_dir():
            scoped_dir = candidate

    if scoped_dir is not None:
        meta_paths = list(scoped_dir.glob("agent-*.meta.json"))
    else:
        projects_dir = Path.home() / ".claude" / "projects" / _claude_projects_slug(project)
        if not projects_dir.is_dir():
            return None
        meta_paths = list(projects_dir.glob("*/subagents/agent-*.meta.json"))

    matches = []
    for meta_path in meta_paths:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if meta.get("agentType") == cell:
            matches.append(meta_path)
    if not matches:
        return None
    newest = max(matches, key=lambda p: p.stat().st_mtime)
    transcript = newest.with_name(newest.name[: -len(".meta.json")] + ".jsonl")
    return transcript if transcript.is_file() else None


def _transcript_context_stats(project: Path, cell: str | None) -> dict | None:
    """The `transcript` source (docs/COMPACTION-DESIGN.md section 13.1,
    D72), now the first precedence level `fill_context` tries rather than
    the last: a worker's own `agent-*.jsonl` carries a strictly richer
    context history than the status line (every assistant message's
    `usage` and `model`), and it works headless, where the status line
    never fires at all.

    Returns `{"compactions": int, "peak_tokens": int | None, "window":
    int | None}`, or `None` only if the transcript itself cannot be
    located (`_resolve_transcript`); a located transcript always returns
    a dict, even one with `compactions: 0` and both other fields `None`,
    since a transcript that exists but is silent about tokens is still
    evidence the cell ran, distinct from no transcript at all.

    `compactions` is the count of lines containing
    `"subtype":"compact_boundary"` (unchanged from the retired
    `_find_transcript_compactions`). `peak_tokens` is the largest value
    among every `compactMetadata.preTokens` found in a `compact_boundary`
    system event and every assistant message's `input_tokens +
    cache_read_input_tokens + cache_creation_input_tokens` (a missing
    field counts as 0 for that sum). `window` is the model's native
    context window, looked up by the first assistant message's
    `message.model` in `src/cost_table.json`'s `context.model_windows`
    table (`load_cost_table`); `None` if no assistant message is found or
    its model id is not in that table, never a guess. A line that fails
    to parse as JSON is skipped, the same tolerance the meta-file reads
    already use."""
    transcript = _resolve_transcript(project, cell)
    if transcript is None:
        return None
    try:
        text = transcript.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    compactions = text.count('"subtype":"compact_boundary"')
    model_windows = load_cost_table().get("context", {}).get("model_windows", {})
    peak_tokens: int | None = None
    first_model: str | None = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        event_type = event.get("type")
        if event_type == "system" and event.get("subtype") == "compact_boundary":
            pre_tokens = (event.get("compactMetadata") or {}).get("preTokens")
            if isinstance(pre_tokens, (int, float)):
                peak_tokens = int(pre_tokens) if peak_tokens is None else max(peak_tokens, int(pre_tokens))
        elif event_type == "assistant":
            message = event.get("message") or {}
            usage = message.get("usage") or {}
            total = (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0) \
                + (usage.get("cache_creation_input_tokens") or 0)
            if total:
                peak_tokens = int(total) if peak_tokens is None else max(peak_tokens, int(total))
            if first_model is None and message.get("model"):
                first_model = message["model"]

    window = model_windows.get(first_model) if first_model is not None else None
    return {"compactions": compactions, "peak_tokens": peak_tokens, "window": window}


def fill_context(project: Path, worker_name: str | None, cell: str | None = None) -> dict:
    """The `context` field for a `--record` entry. Precedence reversed
    from the design's first cut (docs/COMPACTION-DESIGN.md section 13.1,
    D72, superseding section 5): the worker's own transcript first
    (`_transcript_context_stats`), `tools/context_probe.py`'s status-line
    record second, nothing observed last. The reversal is because D72's
    live transcripts showed the status line is not just a secondary
    source but the wrong one to prefer: it never populates headless, and
    the transcript carries `peak_tokens` and `window` the status line
    cannot give at all. Never raises; a missing file, an unmatched name
    or cell, or a data source that cannot be located each fall through to
    the next precedence level rather than failing the whole `--record`
    call, since a worker's outcome is worth recording even when its
    context usage is not observable. `worker_name=None` (no
    `--worker-name` given to a plain `--record`) skips straight to
    `source: "none"`, unchanged from before this revision."""
    if worker_name is None:
        return dict(_NO_CONTEXT_OBSERVED)

    stats = _transcript_context_stats(project, cell)
    if stats is not None:
        return {"peak_tokens": stats["peak_tokens"], "window": stats["window"],
                "compactions": stats["compactions"], "source": "transcript"}

    tasks_path = default_tasks_usage_path(project)
    if tasks_path.exists():
        try:
            data = json.loads(tasks_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        task = (data.get("tasks") or {}).get(worker_name)
        if task and task.get("peak_tokens") is not None:
            return {"peak_tokens": task.get("peak_tokens"), "window": task.get("contextWindowSize"),
                    "compactions": task.get("compactions"), "source": "statusline"}

    return dict(_NO_CONTEXT_OBSERVED)


def _resolve_autocompact_window(project: Path) -> tuple[int | None, str | None]:
    """Resolves the configured auto-compact window in the documented
    precedence (docs/COMPACTION-DESIGN.md section 13.2): the
    `CLAUDE_CODE_AUTO_COMPACT_WINDOW` environment variable first, else the
    first `autoCompactWindow` key found across `.claude/settings.local.json`,
    `.claude/settings.json` (both under `project`) and
    `~/.claude/settings.json`, in that order. Returns `(None, None)` when
    nothing is configured anywhere.

    This duplicates `tools/context_probe.py`'s function of the same name
    (itself a cited duplicate of `src/preflight.py`'s
    `_resolved_autocompact_window`). `route.py` does not import its
    sibling `tools/` modules anywhere else in this file, even though both
    ship together in `dist/tools/`: every existing helper here
    (`_claude_projects_slug`, the session-pointer functions) is
    self-contained so `--selftest` never depends on another module's own
    behaviour. This is the same reasoning, applied a third time, not an
    oversight."""
    env = os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
    if env is not None:
        try:
            return int(env), "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
        except ValueError:
            return None, None
    for path in (project / ".claude" / "settings.local.json", project / ".claude" / "settings.json",
                 Path.home() / ".claude" / "settings.json"):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if "autoCompactWindow" in data:
            return data["autoCompactWindow"], str(path)
    return None, None


def _orchestrator_transcript_stats(transcript_path: Path) -> dict | None:
    """The orchestrator's OWN transcript (not a subagent's), named by
    `.claude/session.json`'s `transcript_path` (docs/COMPACTION-DESIGN.md
    section 13.3, 13.4): the last assistant message's input total
    (`input_tokens + cache_read_input_tokens + cache_creation_input_tokens`)
    and its model id. Returns `None` only if the file cannot be read; a
    file with no assistant message yet returns both fields `None`, since
    that is still distinct from no transcript at all. A line that fails
    to parse as JSON is skipped, the same tolerance
    `_transcript_context_stats` already uses for a subagent's own
    transcript."""
    if not transcript_path.is_file():
        return None
    try:
        text = transcript_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    last_total: int | None = None
    last_model: str | None = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") != "assistant":
            continue
        message = event.get("message") or {}
        usage = message.get("usage") or {}
        total = (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0) \
            + (usage.get("cache_creation_input_tokens") or 0)
        if total:
            last_total = int(total)
        if message.get("model"):
            last_model = message["model"]
    return {"last_total": last_total, "model": last_model}


def context_explain_line(project: Path, priors: dict) -> str:
    """The `--explain` context line (docs/COMPACTION-DESIGN.md section 4,
    superseded where it conflicts by section 13.3): reads
    `tools/context_probe.py`'s output and compares its `used_percentage`
    against `steering.handoff_context_percent`, against the two
    documented status-line fields verbatim (D69: whether those fields
    already account for a configured `autoCompactWindow` smaller than the
    model's native window is unverified, E32; this does not attempt to
    correct for it, and says so in the docstring rather than guessing).

    Section 13.3's addition: when `.claude/context-main.json` (before
    Stage B.8 of `docs/PLAN-6.md`, a `main` key inside the single shared
    `.claude/context-usage.json`; audit A12 split the two apart so
    `--main` and `--tasks` can no longer race on one file) is absent
    entirely (never populated, the common case for a headless
    orchestrator with no status line wired up), falls back to the
    orchestrator's own transcript through `.claude/session.json` (13.4)
    before giving up to `unknown`, so a headless orchestrator gets the
    threshold for the first time. This fallback fires only on an absent
    file, not a stale or not-yet-populated one: the plan text this
    implements (`docs/PLAN-4.md` Stage C.3) names the absent case
    specifically, and widening it to the other two is a separate,
    untested change this function does not make speculatively.

    Absent, stale, or not-yet-populated data all print `unknown` or
    `stale` rather than a wrong number: a headless session with no
    status line, a session before its first API response, and a session
    that has been idle past `steering.context_stale_s` are three
    different reasons the number cannot be trusted, and the caller
    should not have to guess which."""
    steering = priors["steering"]
    threshold = steering["handoff_context_percent"]
    stale_s = steering["context_stale_s"]
    path = default_main_usage_path(project)
    if not path.exists():
        pointer = _read_session_pointer(project)
        transcript_path = Path(pointer["transcript_path"]) if pointer and pointer.get("transcript_path") else None
        if transcript_path is not None:
            stats = _orchestrator_transcript_stats(transcript_path)
            if stats and stats["last_total"] is not None:
                model_windows = load_cost_table().get("context", {}).get("model_windows", {})
                native_window = model_windows.get(stats["model"]) if stats["model"] else None
                resolved, _source = _resolve_autocompact_window(project)
                candidates = [w for w in (native_window, resolved) if w is not None]
                effective_window = min(candidates) if candidates else None
                if effective_window:
                    used = stats["last_total"] / effective_window * 100
                    age_str = "age unknown"
                    try:
                        age_s = dt.datetime.now().timestamp() - transcript_path.stat().st_mtime
                        age_str = "stale" if age_s > stale_s else f"{age_s:.0f} s ago"
                    except OSError:
                        pass
                    verdict = "WRITE A HANDOFF BEFORE THIS TASK" if used >= threshold else "not yet"
                    return (f"context: {used:.0f}% of {effective_window:,} effective (transcript, {age_str}); "
                            f"handoff above {threshold:.0f}%: {verdict}")
        return "context: unknown (no .claude/context-main.json; expected in a headless session)"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "context: unknown (.claude/context-main.json did not parse)"
    main = data.get("main") or {}
    used, window = main.get("used_percentage"), main.get("context_window_size")
    if used is None or window is None:
        return "context: unknown (no usage recorded yet in this session)"
    age_str = "age unknown"
    sampled_at = main.get("sampled_at")
    if sampled_at:
        try:
            age_s = (dt.datetime.now() - dt.datetime.fromisoformat(sampled_at)).total_seconds()
            age_str = "stale" if age_s > stale_s else f"{age_s:.0f} s ago"
        except ValueError:
            pass
    verdict = "WRITE A HANDOFF BEFORE THIS TASK" if used >= threshold else "not yet"
    return f"context: {used:.0f}% of {window:,} (statusline, {age_str}); handoff above {threshold:.0f}%: {verdict}"


def pending_workers_lines(project: Path) -> list[str]:
    """"Pending workers (spawned, outcome not recorded):" plus one line per
    entry, or "(none)". Shared by `recover_report` and
    `tools/handoff.py --pending-workers` (docs/COMPACTION-DESIGN.md
    sections 4 and 10), so a handoff's "Unresolved questions" section and
    the hook's own report can never drift into two different formats for
    the same fact."""
    lines = ["Pending workers (spawned, outcome not recorded):"]
    ledger = load_ledger(default_ledger_path(project))
    pending = [e for e in ledger if e.get("final_outcome") == "unknown"]
    if not pending:
        lines.append("  (none)")
    else:
        for e in pending:
            ts = e.get("ts", "")
            try:
                spawned = dt.datetime.fromisoformat(ts).strftime("%H:%M:%S")
            except ValueError:
                spawned = ts
            lines.append(f"  {e.get('id')}  {e.get('first_cell')}  {e.get('bucket')}  "
                         f"spawned {spawned}  name: {pending_worker_name(e)}")
    return lines


def recover_report(project: Path) -> str:
    """The `SessionStart(compact)` hook's whole output
    (docs/COMPACTION-DESIGN.md section 4): the routing rule in one line,
    every pending ledger entry (spawned, outcome not yet recorded), the
    newest handoff, and the re-read reminder. Zero model calls; every
    line comes from the ledger and the `handoffs/` directory, so this
    runs the same way whether or not compaction actually touched
    anything the ledger depends on."""
    lines = [
        "Context was compacted. Routing rule: assess in one line, resolve with",
        'python3 tools/route.py --from-line "<line>" --project . --explain, spawn',
        "what it names (ORCHESTRATOR.md section 2).",
    ]
    lines.extend(pending_workers_lines(project))
    ledger = load_ledger(default_ledger_path(project))
    acceptance_lines = [line for entry in ledger for line in acceptance_lib.diagnostic(project, entry)]
    missing_context = [entry.get("id", "(unknown)") for entry in ledger
                       if entry.get("final_outcome") == "unknown"
                       and (entry.get("context") or {}).get("source") in (None, "none")]
    lines.append("Acceptance and recovery actions:")
    lines.extend([f"  {line}" for line in acceptance_lines] or ["  (none)"])
    if missing_context:
        lines.append("Missing lifecycle evidence: " + ", ".join(missing_context)
                     + "; no hook/status output was observed, so do not infer an outcome.")
    handoffs_dir = project / "handoffs"
    handoff_files = sorted(handoffs_dir.glob("*.md")) if handoffs_dir.is_dir() else []
    newest = max(handoff_files, key=lambda p: p.stat().st_mtime) if handoff_files else None
    lines.append(f"Newest handoff: handoffs/{newest.name}" if newest else "Newest handoff: none")
    lines.append("If ORCHESTRATOR.md is not part of CLAUDE.md, read it now before the next task.")
    return "\n".join(lines)


def _selftest(verbose: bool = False) -> tuple[bool, list[str]]:
    """Scripted checks for the ledger-aware additions, no file I/O outside
    a temp directory (docs/ROUTING-2-DESIGN.md section 3, scenarios a-g;
    docs/COMPACTION-DESIGN.md adds scenario h, the spawn/record/recover
    round trip (section 4), i, the --explain context line (section 4),
    j, the overflow advisory firing (section 6), k, it not firing on
    uncompacted failures (section 6), l, transcript-first `fill_context`
    and the session-pointer round trip (section 13.1, 13.4, D72), and m,
    `context_explain_line`'s own transcript fallback through the same
    pointer when the status line never populated (section 13.3)."""
    import tempfile

    problems: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            problems.append(msg)
        elif verbose:
            print(f"ok: {msg}")

    priors = load_priors()
    costs = load_cost_table()

    # (a) empty ledger matches resolve()'s cell for every fixture triple,
    # with `first` at the floor except the one measured frontier bucket.
    for bucket, expect_floor in (("mechanical/short/contained", True), ("structured/long/contained", True),
                                  ("open/long/contained", True)):
        s, h, b = bucket.split("/")
        p = plan(s, h, b, priors=priors, ledger=[], costs=costs)
        check(p["first"] == "worker-sonnet-low",
              f"(a) empty ledger, {bucket}: expected the floor first, got {p['first']!r}")

    # (b) three floor failures escalating to worker-opus-high in one bucket
    # raise P(floor fail) and, since opus-high's own posterior is already
    # high in this seeded bucket, move `first` to it.
    bucket = "open/medium/contained"
    s, h, b = bucket.split("/")
    ledger_b = [{"bucket": bucket, "first_cell": "worker-sonnet-low",
                 "escalations": [{"cell": "worker-opus-high", "outcome": "pass"}], "final_outcome": "pass"}] * 3
    p_before = plan(s, h, b, priors=priors, ledger=[], costs=costs)
    p_after = plan(s, h, b, priors=priors, ledger=ledger_b, costs=costs)
    check(p_after["posterior"]["floor_mean"] < p_before["posterior"]["floor_mean"],
          f"(b) three floor failures should lower the floor's posterior mean, got "
          f"{p_before['posterior']['floor_mean']} -> {p_after['posterior']['floor_mean']}")

    # (c) three worker-sonnet-xhigh passes as escalations in a bucket with
    # no prior rung there activate it and insert it before worker-opus-high.
    bucket = "mechanical/short/contained"
    s, h, b = bucket.split("/")
    ledger_c = [{"bucket": bucket, "first_cell": "worker-sonnet-low",
                 "escalations": [{"cell": "worker-sonnet-xhigh", "outcome": "pass"}], "final_outcome": "pass"}] * 3
    post_c = posterior(priors, ledger_c, bucket)
    check("worker-sonnet-xhigh" in post_c["active_rungs"],
          f"(c) three sonnet-xhigh passes should activate that rung, active_rungs={post_c['active_rungs']}")
    if "worker-sonnet-xhigh" in post_c["active_rungs"] and "worker-opus-high" in post_c["active_rungs"]:
        check(post_c["active_rungs"].index("worker-sonnet-xhigh") < post_c["active_rungs"].index("worker-opus-high"),
              "(c) an activated cheaper rung should sort before a dearer one")

    # (d) The reserved-qualified B0 default cannot be pre-empted by the
    # historical Controller policy. The adaptive engine remains replayable
    # only when a diagnostic caller opts out of the qualified default.
    p_policy = plan("open", "long", "consequential", priors=priors, ledger=[], costs=costs)
    check(p_policy["first"] == "worker-sonnet-low" and p_policy["controller"] is None
          and p_policy["execution_ladder"]
          == ["worker-sonnet-low", "worker-sonnet-low", "worker-opus-high"],
          f"(d) qualified B0 must use its fixed sequence, got {p_policy}")
    import copy
    priors_off = copy.deepcopy(priors)
    p_policy_legacy = plan("open", "long", "consequential", priors=priors_off,
                           ledger=[], costs=costs, use_qualified_default=False)
    check(p_policy_legacy["first"] == "controller"
          and p_policy_legacy["controller"]["reason"] == "policy",
          f"(d) historical adaptive replay should retain its policy result, got {p_policy_legacy}")

    # (e) enough opus-high failures push the expected-cost rule to fire. A
    # contained bucket cannot: its failure_cost is E_ladder itself, which
    # this repository's own unit costs bound below the Controller's price
    # even at total failure (D64's "fires nowhere on current evidence" is
    # this arithmetic, not an assertion). Consequential's failure_cost is
    # the fixed policy dial (10.0), which repeated failure can exceed; a
    # mechanical/structured bucket keeps the proactive_policy dial (which
    # only names open/consequential) out of the way, isolating the
    # arithmetic this scenario is testing.
    bucket = "mechanical/short/consequential"
    s, h, b = bucket.split("/")
    ledger_e = [{"bucket": bucket, "first_cell": "worker-sonnet-low",
                 "escalations": [{"cell": "worker-opus-high", "outcome": "fail"}], "final_outcome": "fail"}] * 8
    p_e = plan(s, h, b, priors=priors, ledger=ledger_e, costs=costs,
               use_qualified_default=False)
    check(p_e["controller"]["reason"] == "expected_cost",
          f"(e) repeated opus-high failure on a consequential bucket should fire the expected-cost rule, "
          f"got reason {p_e['controller']['reason']!r}, e_ladder={p_e['controller']['e_ladder_usd']}, "
          f"p_fail_all={p_e['controller']['p_fail_all']}")

    # (f) --record round-trips through load_ledger, and a malformed line is
    # skipped, not fatal.
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        ledger_path = Path(tmp) / "routing-ledger.jsonl"
        entry = {"type": "RoutingLedgerEntry", "id": "led-001", "ledger_version": 0, "references": [],
                 "ts": dt.datetime.now().isoformat(), "task_slug": "selftest", "bucket": "mechanical/short/contained",
                 "self_directed": False, "first_cell": "worker-sonnet-low", "escalations": [],
                 "final_outcome": "pass", "cost_usd": 0.1, "wall_clock_s": 10.0,
                 "controller_run_dir": None, "winning_technique": None, "notes": ""}
        append_ledger_entry(ledger_path, entry)
        ledger_path.write_text(ledger_path.read_text(encoding="utf-8") + "not json\n", encoding="utf-8")
        loaded = load_ledger(ledger_path)
        check(len(loaded) == 1 and loaded[0]["id"] == "led-001",
              f"(f) a malformed line should be skipped, not fatal; got {len(loaded)} entrie(s)")
        check(next_ledger_id(loaded) == "led-002", f"(f) next id should be led-002, got {next_ledger_id(loaded)!r}")

    # (g) The qualified default ignores the historical frontier signal and
    # retains B0. Historical replay keeps the old frontier behaviour.
    p_g = plan("open", "long", "consequential", prior_failure="failed_at_xhigh",
               priors=priors, ledger=ledger_e, costs=costs)
    check(p_g["first"] == "worker-sonnet-low",
          f"(g) qualified B0 should ignore frontier routing, got {p_g['first']!r}")
    p_g_legacy = plan("open", "long", "consequential", prior_failure="failed_at_xhigh",
                      priors=priors, ledger=ledger_e, costs=costs,
                      use_qualified_default=False)
    check(p_g_legacy["first"] == "worker-opus-max",
          f"(g) historical replay should retain the frontier, got {p_g_legacy['first']!r}")

    # (h) --spawn writes a pending entry excluded from posterior() (its
    # final_outcome is "unknown"), --record --pending completes it in
    # place without appending a second record, and recover_report() lists
    # it while pending and stops listing it once complete.
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        project = Path(tmp)
        ledger_path = default_ledger_path(project)
        spawned = {"type": "RoutingLedgerEntry", "id": "led-001", "ledger_version": 0, "references": [],
                   "ts": dt.datetime.now().isoformat(), "task_slug": "selftest-h", "bucket": "mechanical/short/contained",
                   "self_directed": False, "first_cell": "worker-sonnet-low", "escalations": [],
                   "final_outcome": "unknown", "cost_usd": 0, "wall_clock_s": 0,
                   "controller_run_dir": None, "winning_technique": None, "notes": "pending: selftest-worker"}
        append_ledger_entry(ledger_path, spawned)
        with ledger_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("not json; preserve this interrupted row\n")
        pending_ledger = load_ledger(ledger_path)
        post_h = posterior(priors, pending_ledger, "mechanical/short/contained")
        check(post_h["floor_ledger_passes"] == 0 and post_h["floor_ledger_fails"] == 0,
              f"(h) a pending entry (final_outcome unknown) must not count toward the posterior, "
              f"got passes={post_h['floor_ledger_passes']} fails={post_h['floor_ledger_fails']}")
        report_pending = recover_report(project)
        check("led-001" in report_pending and "selftest-worker" in report_pending and "(none)" not in report_pending,
              f"(h) recover_report should list the pending entry by id and worker name, got:\n{report_pending}")
        completed = complete_ledger_entry(ledger_path, "led-001",
                                           {"final_outcome": "pass", "cost_usd": 0.12, "wall_clock_s": 30.0,
                                            "notes": "done"})
        check(completed["final_outcome"] == "pass" and completed["id"] == "led-001",
              f"(h) complete_ledger_entry should return the merged entry, got {completed}")
        after = load_ledger(ledger_path)
        check(len(after) == 1, f"(h) completing in place should not append a second record, got {len(after)} entries")
        report_done = recover_report(project)
        check("Pending workers (spawned, outcome not recorded):\n  (none)" in report_done
              and "execution pending" not in report_done,
              f"(h) recover_report should list no pending execution once completed, got:\n{report_done}")
        repeated = complete_ledger_entry(ledger_path, "led-001", {"final_outcome": "pass"})
        check(repeated["id"] == "led-001",
              "(h) replaying an identical completion should be idempotent")
        check("not json; preserve this interrupted row" in ledger_path.read_text(encoding="utf-8"),
              "(h) completing an entry should preserve an unparseable ledger row byte-for-byte")
        try:
            complete_ledger_entry(ledger_path, "led-001", {"final_outcome": "fail"})
            check(False, "(h) a conflicting second completion should raise LedgerEntryNotPending")
        except LedgerEntryNotPending:
            pass
        try:
            complete_ledger_entry(ledger_path, "led-999", {"final_outcome": "pass"})
            check(False, "(h) completing an unknown id should raise LedgerEntryNotFound")
        except LedgerEntryNotFound:
            pass

    # (i) context_explain_line: absent file, under threshold, over
    # threshold, and a stale sample all print the right thing rather than
    # a wrong number (docs/COMPACTION-DESIGN.md section 4). context-main.json
    # and context-tasks.json are separate files since the A12 split (audit
    # A12, docs/PLAN-6.md Stage B.8): context_explain_line reads only the
    # main file, fill_context (below) only the tasks file.
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        project = Path(tmp)
        line_absent = context_explain_line(project, priors)
        check(line_absent.startswith("context: unknown") and "no .claude/context-main.json" in line_absent,
              f"(i) an absent context-main.json should print 'unknown', got {line_absent!r}")

        main_path = default_main_usage_path(project)
        main_path.parent.mkdir(parents=True, exist_ok=True)
        threshold = priors["steering"]["handoff_context_percent"]
        main_path.write_text(json.dumps({"main": {"used_percentage": threshold - 5, "context_window_size": 200000,
                                                    "sampled_at": dt.datetime.now().isoformat()}}), encoding="utf-8")
        line_under = context_explain_line(project, priors)
        check("not yet" in line_under, f"(i) below the threshold should print 'not yet', got {line_under!r}")

        main_path.write_text(json.dumps({"main": {"used_percentage": threshold + 5, "context_window_size": 200000,
                                                    "sampled_at": dt.datetime.now().isoformat()}}), encoding="utf-8")
        line_over = context_explain_line(project, priors)
        check("WRITE A HANDOFF" in line_over, f"(i) at or above the threshold should recommend a handoff, got {line_over!r}")

        stale_s = priors["steering"]["context_stale_s"]
        old_ts = (dt.datetime.now() - dt.timedelta(seconds=stale_s + 60)).isoformat()
        main_path.write_text(json.dumps({"main": {"used_percentage": threshold + 5, "context_window_size": 200000,
                                                    "sampled_at": old_ts}}), encoding="utf-8")
        line_stale = context_explain_line(project, priors)
        check("stale" in line_stale and "WRITE A HANDOFF" in line_stale,
              f"(i) a stale sample should print 'stale' but still make the threshold comparison, got {line_stale!r}")

        # fill_context (docs/COMPACTION-DESIGN.md section 5): no name given,
        # a name present in the probe's tasks key, and a name present
        # nowhere all resolve to the documented source and never raise.
        none_ctx = fill_context(project, None)
        check(none_ctx["source"] == "none" and none_ctx["peak_tokens"] is None,
              f"fill_context(None) should report source 'none' with nothing observed, got {none_ctx}")

        tasks_path = default_tasks_usage_path(project)
        tasks_path.write_text(json.dumps({"tasks": {"probe-worker": {"peak_tokens": 91000, "contextWindowSize": 200000,
                                                                       "compactions": 2}}}), encoding="utf-8")
        statusline_ctx = fill_context(project, "probe-worker")
        check(statusline_ctx == {"peak_tokens": 91000, "window": 200000, "compactions": 2, "source": "statusline"},
              f"fill_context should read a matching name from context-tasks.json's tasks key, got {statusline_ctx}")

        missing_ctx = fill_context(project, "no-such-worker")
        check(missing_ctx["source"] == "none",
              f"fill_context should fall through to 'none' for a name the probe never saw, got {missing_ctx}")

        # A --main write to context-main.json above must never leak into
        # fill_context's read of context-tasks.json, and vice versa: the
        # two files are independent, which is the whole point of the split.
        check(json.loads(main_path.read_text(encoding="utf-8")).get("tasks") is None,
              "(i) context-main.json must never carry a tasks key")
        check(json.loads(tasks_path.read_text(encoding="utf-8")).get("main") is None,
              "(i) context-tasks.json must never carry a main key")

    # (j) four compacted floor attempts, no other history: the capability
    # posterior (floor_mean) is untouched (D68: a compaction is a horizon
    # signal, not evidence the cell lacks capability), while the overflow
    # posterior crosses the advisory threshold on the shipped prior (0.5,
    # 9.5). Three compacted attempts alone give a mean of about 0.269,
    # under the 0.3 threshold; four are used here, matching the arithmetic
    # rather than section 6's illustrative round number.
    bucket = "structured/short/contained"
    s, h, b = bucket.split("/")
    p_empty_j = plan(s, h, b, priors=priors, ledger=[], costs=costs)
    ledger_j = [{"bucket": bucket, "first_cell": "worker-sonnet-low", "escalations": [], "final_outcome": "unknown",
                 "context": {"peak_tokens": 190000, "window": 200000, "compactions": 1, "source": "statusline"}}] * 4
    p_j = plan(s, h, b, priors=priors, ledger=ledger_j, costs=costs)
    check(p_j["posterior"]["floor_mean"] == p_empty_j["posterior"]["floor_mean"],
          f"(j) compacted attempts should not move the floor's capability posterior, got "
          f"{p_empty_j['posterior']['floor_mean']} -> {p_j['posterior']['floor_mean']}")
    check(p_j["overflow"]["advisory"] and p_j["overflow"]["mean"] >= priors["steering"]["overflow_advisory_min_mean"],
          f"(j) four compacted attempts should cross the overflow advisory threshold, got {p_j['overflow']}")
    check(p_j["first"] == "worker-sonnet-low", f"(j) the overflow advisory should not change 'first', got {p_j['first']!r}")

    # (k) three uncompacted floor failures lower the floor's capability
    # posterior exactly as scenario (b) does, while the overflow
    # posterior stays near its prior and the advisory does not fire.
    bucket = "structured/medium/contained"
    s, h, b = bucket.split("/")
    p_empty_k = plan(s, h, b, priors=priors, ledger=[], costs=costs)
    ledger_k = [{"bucket": bucket, "first_cell": "worker-sonnet-low",
                 "escalations": [{"cell": "worker-opus-high", "outcome": "pass"}], "final_outcome": "pass",
                 "context": {"peak_tokens": 40000, "window": 200000, "compactions": 0, "source": "statusline"}}] * 3
    p_k = plan(s, h, b, priors=priors, ledger=ledger_k, costs=costs)
    check(p_k["posterior"]["floor_mean"] < p_empty_k["posterior"]["floor_mean"],
          f"(k) three uncompacted floor failures should lower the floor's posterior mean, got "
          f"{p_empty_k['posterior']['floor_mean']} -> {p_k['posterior']['floor_mean']}")
    check(not p_k["overflow"]["advisory"] and p_k["overflow"]["mean"] < priors["steering"]["overflow_advisory_min_mean"],
          f"(k) three uncompacted attempts should not cross the overflow advisory threshold, got {p_k['overflow']}")

    # (l) fill_context's transcript-first precedence (docs/COMPACTION-DESIGN.md
    # section 13.1, D72) and the session-pointer round trip (section 13.4).
    # A synthetic subagent transcript with one assistant message (a known
    # usage sum and model id) and one compact_boundary (a known preTokens)
    # should resolve peak_tokens to the larger of the two, window from the
    # model id via cost_table.json's new context.model_windows table, and
    # compactions from the boundary count. A decoy transcript for the same
    # cell, in a different session with larger numbers throughout and a
    # newer mtime, proves the scoping: without a pointer, the every-session
    # fallback prefers the decoy on recency; with a pointer naming the
    # correct session, fill_context must find only that session's own
    # transcript, never falling through to the decoy.
    import time
    from unittest import mock

    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        fake_home = Path(tmp) / "home"
        project = Path(tmp) / "project"
        project.mkdir(parents=True)
        projects_dir = fake_home / ".claude" / "projects" / _claude_projects_slug(project)

        def make_transcript(session_id: str, model: str, input_tokens: int, pre_tokens: int) -> Path:
            subagents_dir = projects_dir / session_id / "subagents"
            subagents_dir.mkdir(parents=True)
            meta_path = subagents_dir / f"agent-{session_id}.meta.json"
            meta_path.write_text(json.dumps({"agentType": "worker-sonnet-low"}), encoding="utf-8")
            transcript_path = subagents_dir / f"agent-{session_id}.jsonl"
            # separators=(",", ":") matches the platform's own compact
            # JSONL encoding (no space after the colon), which is what
            # `compactions`'s literal substring count assumes, the same
            # as every real transcript this repository has read.
            lines = [
                json.dumps({"type": "assistant", "message": {
                    "model": model,
                    "usage": {"input_tokens": input_tokens, "cache_read_input_tokens": 0,
                              "cache_creation_input_tokens": 0}}}, separators=(",", ":")),
                json.dumps({"type": "system", "subtype": "compact_boundary",
                            "compactMetadata": {"preTokens": pre_tokens}}, separators=(",", ":")),
            ]
            transcript_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return meta_path

        with mock.patch.object(Path, "home", return_value=fake_home):
            correct_meta = make_transcript("session-correct", "claude-sonnet-5", 50000, 80000)
            decoy_meta = make_transcript("session-decoy", "claude-sonnet-5", 999000, 999000)
            now = time.time()
            for meta_path, mtime in ((correct_meta, now - 100), (decoy_meta, now)):
                transcript_path = meta_path.with_name(meta_path.name[: -len(".meta.json")] + ".jsonl")
                os.utime(meta_path, (mtime, mtime))
                os.utime(transcript_path, (mtime, mtime))

            no_pointer_ctx = fill_context(project, "some-worker", "worker-sonnet-low")
            check(no_pointer_ctx["source"] == "transcript" and no_pointer_ctx["peak_tokens"] == 999000,
                  f"(l) with no session pointer, fill_context should fall back to the newest transcript "
                  f"across every session (the decoy), got {no_pointer_ctx}")

            correct_session_dir = projects_dir / "session-correct"
            hook_input = {"session_id": "session-correct",
                          "transcript_path": str(correct_session_dir / "session-correct.jsonl"),
                          "cwd": str(project), "source": "compact"}
            _write_session_pointer(hook_input, project)
            pointer = _read_session_pointer(project)
            check(pointer is not None and pointer.get("session_id") == "session-correct"
                  and pointer.get("event") == "compact" and pointer.get("cwd") == str(project),
                  f"(l) _read_session_pointer should read back what --session-pointer wrote, got {pointer}")

            scoped_ctx = fill_context(project, "some-worker", "worker-sonnet-low")
            check(scoped_ctx == {"peak_tokens": 80000, "window": 1000000, "compactions": 1, "source": "transcript"},
                  f"(l) with a session pointer in place, fill_context should resolve only the pointed-to "
                  f"session's transcript, not the newer decoy in a different session, got {scoped_ctx}")

    # (m) context_explain_line's transcript fallback when
    # .claude/context-main.json is absent (docs/COMPACTION-DESIGN.md
    # section 13.3): with no session pointer at all, 'unknown' is
    # unchanged from (i); with a pointer naming a real transcript, the
    # last assistant message's input total against the effective window
    # (the model's native window from cost_table.json, capped by a
    # configured CLAUDE_CODE_AUTO_COMPACT_WINDOW) should print instead.
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        fake_home = Path(tmp) / "home"
        project = Path(tmp) / "project"
        project.mkdir(parents=True)
        session_dir = fake_home / ".claude" / "projects" / _claude_projects_slug(project) / "session-main"
        session_dir.mkdir(parents=True)
        transcript_path = session_dir / "session-main.jsonl"
        lines = [
            json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-5",
                        "usage": {"input_tokens": 60000, "cache_read_input_tokens": 40000,
                                  "cache_creation_input_tokens": 0}}}, separators=(",", ":")),
            # the LAST assistant message is what should be used, not the
            # first or the largest: 120000 + 8000 = 128000.
            json.dumps({"type": "assistant", "message": {"model": "claude-sonnet-5",
                        "usage": {"input_tokens": 120000, "cache_read_input_tokens": 8000,
                                  "cache_creation_input_tokens": 0}}}, separators=(",", ":")),
        ]
        transcript_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with mock.patch.object(Path, "home", return_value=fake_home):
            no_pointer_line = context_explain_line(project, priors)
            check(no_pointer_line.startswith("context: unknown") and "no .claude/context-main.json" in no_pointer_line,
                  f"(m) with no session pointer and no context-main.json, the line should stay "
                  f"'unknown', got {no_pointer_line!r}")

            _write_session_pointer({"session_id": "session-main", "transcript_path": str(transcript_path),
                                     "cwd": str(project), "source": "startup"}, project)
            os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = "200000"
            try:
                fallback_line = context_explain_line(project, priors)
            finally:
                del os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"]
            # effective window: min(1,000,000 native for claude-sonnet-5,
            # 200,000 configured) = 200,000; 128,000 / 200,000 = 64%.
            check("64% of 200,000 effective" in fallback_line and "(transcript" in fallback_line,
                  f"(m) the transcript fallback should compute the last assistant message's total "
                  f"against the effective (capped) window, got {fallback_line!r}")

    # (n) three floor failures recorded with no escalation at all
    # (`--record --outcome fail` with no `--escalation` flag, a legal
    # call `ORCHESTRATOR.md` section 2 invites) lower the floor's
    # posterior mean exactly as an escalated failure does (D81/A4,
    # `docs/AUDIT-2026-09-16.md`). Before the fix these moved neither
    # `floor_pass` nor `floor_fail` and the ledger silently ignored them.
    bucket = "structured/long/contained"
    s, h, b = bucket.split("/")
    ledger_n = [{"bucket": bucket, "first_cell": "worker-sonnet-low",
                 "escalations": [], "final_outcome": "fail"}] * 3
    p_before_n = plan(s, h, b, priors=priors, ledger=[], costs=costs)
    p_after_n = plan(s, h, b, priors=priors, ledger=ledger_n, costs=costs)
    check(p_after_n["posterior"]["floor_mean"] < p_before_n["posterior"]["floor_mean"],
          f"(n) three unescalated floor failures should lower the floor's posterior mean, got "
          f"{p_before_n['posterior']['floor_mean']} -> {p_after_n['posterior']['floor_mean']}")

    # (o) plan()'s own --explain projection now uses a project's own
    # measured cost for a cell once its ledger crosses
    # steering.ledger_overrides_after entries there, not only
    # tools/handoff.py's projections (audit A5, docs/AUDIT-2026-09-16.md).
    # Direct unit check on ledger_cell_means first: task totals cannot be
    # divided evenly when the version-2 attempts carry exact unequal costs.
    # Then an end-to-end check confirms plan() consumes those exact means.
    exact_attempts = parse_attempts([
        json.dumps({"requested_cell": "worker-sonnet-low", "outcome": "fail", "wall_clock_s": 10.0,
                    "usage": {**_empty_usage(0.10, source="provider_reported")}}),
        json.dumps({"requested_cell": "worker-opus-high", "outcome": "pass", "wall_clock_s": 90.0,
                    "usage": {**_empty_usage(1.90, source="provider_reported")}}),
    ], "worker-sonnet-low", [{"cell": "worker-opus-high", "outcome": "pass"}], "pass", 2.0, 100.0)
    ledger_o = [{"bucket": "open/medium/contained", "first_cell": "worker-sonnet-low",
                 "escalations": [{"cell": "worker-opus-high", "outcome": "pass"}],
                 "final_outcome": "pass", "cost_usd": 2.0, "wall_clock_s": 100.0,
                 "ledger_version": 2, "execution_status": "completed", "attempts": exact_attempts}] * 5
    means_o = ledger_cell_means(ledger_o, priors["steering"]["ledger_overrides_after"])
    check(means_o.get("worker-sonnet-low") == {"cost_per_run_usd": 0.1, "wall_clock_s": 10.0,
                                                "attempts_measured": 5}
          and means_o.get("worker-opus-high") == {"cost_per_run_usd": 1.9, "wall_clock_s": 90.0,
                                                   "attempts_measured": 5},
          f"(o) ledger_cell_means should preserve USD 0.10 and USD 1.90 attempts, got {means_o}")
    p_before_o = plan("open", "medium", "contained", priors=priors, ledger=[], costs=costs,
                      use_qualified_default=False)
    p_after_o = plan("open", "medium", "contained", priors=priors, ledger=ledger_o, costs=costs,
                     use_qualified_default=False)
    check(p_after_o["controller"]["e_ladder_usd"] > p_before_o["controller"]["e_ladder_usd"],
          f"(o) plan()'s expected ladder cost should rise when the exact measured opus cost "
          f"exceeds cost_table.json's figure, got "
          f"{p_before_o['controller']['e_ladder_usd']} -> {p_after_o['controller']['e_ladder_usd']}")

    # (p) pending records and unknown measurements never become zero-cost
    # evidence; a measured zero remains a real observation.
    pending_p = [{"first_cell": "worker-sonnet-low", "escalations": [], "final_outcome": "unknown",
                  "cost_usd": 0, "wall_clock_s": 0}] * 5
    check(ledger_cell_means(pending_p, 5) == {},
          f"(p) pending records must not override cost/time, got {ledger_cell_means(pending_p, 5)}")
    zero_attempt = parse_attempts([], "worker-sonnet-low", [], "pass", 0.0, 0.0)
    measured_zero_p = [{"first_cell": "worker-sonnet-low", "escalations": [], "final_outcome": "pass",
                        "ledger_version": 2, "attempts": zero_attempt}] * 5
    zero_means = ledger_cell_means(measured_zero_p, 5)
    check(zero_means.get("worker-sonnet-low", {}).get("cost_per_run_usd") == 0.0,
          f"(p) measured zero must remain distinct from unknown, got {zero_means}")

    # (q) separate route.py processes allocate IDs while holding the same
    # operating-system lock. No process may lose a row or reuse an ID.
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        project = Path(tmp)
        contract_path = project / "acceptance.json"
        contract_path.write_text(json.dumps({
            "version": 1, "kind": "command", "criteria": ["selftest"],
            "constraints": [], "required_outputs": ["result.txt"],
            "protected_paths": [], "command": [sys.executable, "-c", "raise SystemExit(0)"],
            "rubric": [], "timeout_s": 30,
        }), encoding="utf-8")
        line = "assessment: mechanical, short, contained; self_directed: false; prior_failure: none"
        processes = []
        import subprocess
        for i in range(6):
            processes.append(subprocess.Popen([
                sys.executable, str(Path(__file__).resolve()), "--spawn", "--from-line", line,
                "--project", str(project), "--task-slug", f"concurrent-{i}",
                "--first-cell", "worker-sonnet-low", "--worker-name", f"worker-{i}",
                "--acceptance-contract", str(contract_path),
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        results = [process.communicate(timeout=30) + (process.returncode,) for process in processes]
        concurrent_rows = load_ledger(default_ledger_path(project))
        ids = [row.get("id") for row in concurrent_rows]
        check(all(code == 0 for _, _, code in results) and len(ids) == 6 and len(set(ids)) == 6,
              f"(q) concurrent creates should retain 6 unique rows, got ids={ids!r}, results={results!r}")

    # (r) migration is explicit, dry-run safe, byte-backed, idempotent and
    # exactly restorable. A failed atomic replace leaves the original intact.
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        ledger_path = Path(tmp) / "routing-ledger.jsonl"
        legacy = {"type": "RoutingLedgerEntry", "id": "led-001", "ledger_version": 0,
                  "references": [], "ts": "2026-09-17T00:00:00Z", "task_slug": "legacy",
                  "bucket": "mechanical/short/contained", "self_directed": False,
                  "first_cell": "worker-sonnet-low", "escalations": [], "final_outcome": "pass",
                  "cost_usd": 0.25, "wall_clock_s": 12.0, "controller_run_dir": None,
                  "winning_technique": None, "notes": ""}
        original = (json.dumps(legacy) + "\n").encode("utf-8")
        ledger_path.write_bytes(original)
        preview = migrate_ledger_v2(ledger_path, dry_run=True)
        check(preview["changed"] == 1 and ledger_path.read_bytes() == original
              and not ledger_path.with_suffix(ledger_path.suffix + ".pre-v2.bak").exists(),
              f"(r) migration dry-run must change no bytes, got {preview}")
        migrated = migrate_ledger_v2(ledger_path)
        backup = Path(migrated["backup"])
        rows = load_ledger(ledger_path)
        check(backup.read_bytes() == original and rows[0]["ledger_version"] == 2
              and rows[0]["attempts"][0]["usage"]["cost_usd"] == 0.25,
              f"(r) migration should preserve an exact backup and attributable single-cell cost, got {migrated}")
        second = migrate_ledger_v2(ledger_path)
        check(second["changed"] == 0 and backup.read_bytes() == original,
              f"(r) migration should be idempotent, got {second}")
        restored = restore_ledger_backup(ledger_path, backup)
        check(ledger_path.read_bytes() == original and Path(restored["pre_restore_backup"]).is_file(),
              f"(r) restore should reproduce the original bytes and retain migrated bytes, got {restored}")

    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        from unittest import mock
        ledger_path = Path(tmp) / "routing-ledger.jsonl"
        original = (json.dumps(legacy) + "\n").encode("utf-8")
        ledger_path.write_bytes(original)
        try:
            with mock.patch.object(Path, "replace", side_effect=OSError("injected replace failure")):
                migrate_ledger_v2(ledger_path)
            check(False, "(r) injected replace failure should escape migration")
        except OSError:
            pass
        check(ledger_path.read_bytes() == original,
              "(r) interrupted migration must leave the original ledger bytes intact")

    # (s) Ordinary reads reject a future schema rather than silently learning
    # from fields whose meaning this bundle does not know.
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        future_path = Path(tmp) / "routing-ledger.jsonl"
        future_path.write_text(json.dumps({"type": "RoutingLedgerEntry", "id": "led-001",
                                           "ledger_version": 99}) + "\n",
                               encoding="utf-8", newline="\n")
        try:
            load_ledger(future_path)
        except RoutingError as exc:
            future_rejected = "unsupported ledger_version 99" in str(exc)
        else:
            future_rejected = False
        check(future_rejected, "(s) ordinary reads must reject unsupported future ledger versions")

    # (t) Direct starts and conditional escalations are distinct capability
    # populations. Acceptance, rather than a worker claim, supplies the final
    # task verdict for version-2 evidence.
    def evidence_entry(cell: str, outcome: str, *, start_kind: str = "direct",
                       model: str = "model-a", acceptance: str | None = None,
                       finished_at: str = "2026-09-17T00:00:00Z") -> dict:
        attempt = {"sequence": 1, "requested_cell": cell, "start_kind": start_kind,
                   "actual_model": model, "bundle_version": "bundle-a",
                   "policy_version": "policy-a", "execution_status": "completed",
                   "outcome": outcome, "finished_at": finished_at,
                   "usage": {"cost_usd": 0.2}, "wall_clock_s": 10.0}
        contract = {"version": 1, "kind": "command", "criteria": ["fixture"],
                    "constraints": [], "required_outputs": ["result.txt"],
                    "protected_paths": [], "command": ["fixture-check"],
                    "rubric": [], "timeout_s": 30.0}
        status = acceptance or outcome
        command_evidence = {"kind": "command", "command": {"exit_code": 0 if status == "pass" else 1},
                            "artefacts": {}, "protected": {}, "protected_unchanged": True,
                            "blocked_reason": None}
        command_evidence["result_digest"] = acceptance_lib.digest(command_evidence)
        acceptance_record = ({"status": status, "contract_version": acceptance_lib.CONTRACT_VERSION,
                              "contract": contract, "contract_digest": acceptance_lib.digest(contract),
                              "protected_baseline": {"files": [], "missing": [], "digest": acceptance_lib.digest({})},
                              "evidence": command_evidence,
                              "review": None}
                             if status in ("pass", "fail") else
                             {"status": status, "evidence": [], "contract_version": "unverified-v1"})
        return {"bucket": "mechanical/short/contained", "first_cell": cell,
                "final_outcome": outcome, "attempts": [attempt],
                "acceptance": acceptance_record}

    direct_failures = [evidence_entry("worker-opus-high", "fail") for _ in range(20)]
    post_t = posterior(priors, direct_failures, "mechanical/short/contained")
    opus_t = post_t["rungs"]["worker-opus-high"]
    check(opus_t["direct"]["ledger_fails"] == 20
          and opus_t["conditional"]["ledger_fails"] == 0,
          f"(t) direct failures must update only the direct population, got {opus_t}")
    conditional_failures = [evidence_entry("worker-opus-high", "fail", start_kind="escalation")
                            for _ in range(20)]
    post_t2 = posterior(priors, conditional_failures, "mechanical/short/contained")
    opus_t2 = post_t2["rungs"]["worker-opus-high"]
    check(opus_t2["conditional"]["ledger_fails"] == 20
          and opus_t2["direct"]["ledger_fails"] == 0,
          f"(t) escalation failures must update only the conditional population, got {opus_t2}")

    # (u) Unverified and stale evidence is excluded. Incompatible exact
    # identity cohorts cannot silently pool; an explicit target can select one.
    unverified = evidence_entry("worker-opus-high", "pass", acceptance="unverified")
    post_u = posterior(priors, [unverified], "mechanical/short/contained")
    check(post_u["rungs"]["worker-opus-high"]["direct"]["ledger_passes"] == 0
          and post_u["evidence"]["unverified_excluded"] == 1,
          f"(u) unverified evidence must not train capability, got {post_u['evidence']}")
    conflicting = ([evidence_entry("worker-opus-high", "pass", model="model-a") for _ in range(10)]
                   + [evidence_entry("worker-opus-high", "fail", model="model-b") for _ in range(10)])
    post_conflict = posterior(priors, conflicting, "mechanical/short/contained")
    direct_conflict = post_conflict["rungs"]["worker-opus-high"]["direct"]
    diagnostic = post_conflict["evidence"]["identity_populations"]["worker-opus-high:direct"]
    check(direct_conflict["ledger_passes"] == 0 and direct_conflict["ledger_fails"] == 0
          and diagnostic["conflict"],
          f"(u) incompatible identities must retain the prior and report conflict, got {direct_conflict}, {diagnostic}")
    post_exact = posterior(priors, conflicting, "mechanical/short/contained",
                           evidence_identity={"actual_model": "model-a"})
    check(post_exact["rungs"]["worker-opus-high"]["direct"]["ledger_passes"] == 10,
          f"(u) exact identity selection should use only model-a, got {post_exact['rungs']['worker-opus-high']}")
    post_old = posterior(priors, [evidence_entry("worker-opus-high", "pass", finished_at="2020-01-01T00:00:00Z")],
                         "mechanical/short/contained", max_age_days=30,
                         now=dt.datetime(2026, 9, 17, tzinfo=dt.timezone.utc))
    check(post_old["evidence"]["age_excluded"] == 1,
          f"(u) stale evidence should be excluded, got {post_old['evidence']}")

    # (v) Cost accounting retains terminal failed/interrupted spend even if
    # the outer task is unresolved. Capability eligibility remains separate.
    unresolved_costs = [evidence_entry("worker-opus-high", "fail") for _ in range(5)]
    for row in unresolved_costs:
        row["final_outcome"] = "unknown"
    means_v = ledger_cell_means(unresolved_costs, 5)
    check(means_v.get("worker-opus-high", {}).get("cost_per_run_usd") == 0.2,
          f"(v) terminal spend from unresolved tasks must remain in cost means, got {means_v}")

    # (w) A selected elevated start pays that cell in full and projects only
    # later rungs. Missing Controller failure/retry and verification terms are
    # explicit rather than silently treated as zero.
    selected_w = plan("mechanical", "short", "contained", priors=priors,
                      ledger=direct_failures, costs=costs,
                      evidence_identity={"actual_model": "model-a"})
    check(selected_w["first"] == "worker-sonnet-low"
          or selected_w["controller"]["start_cell"] == selected_w["first"],
          f"(w) projection must begin at the selected worker, got {selected_w}")
    synthetic_post = posterior(priors, [], "mechanical/short/contained")
    synthetic_post["rungs"]["worker-opus-high"]["direct"] = {
        "mean": 0.9, "ledger_passes": 9, "ledger_fails": 1}
    ladder_w = expected_ladder_cost(synthetic_post, costs, "worker-opus-high")
    check(ladder_w["execution_rungs"][0] == "worker-opus-high"
          and ladder_w["p_reach_by_rung"]["worker-opus-high"] == 1.0
          and ladder_w["e_ladder_usd"] >= costs["cells"]["worker-opus-high"]["cost_per_run_usd"],
          f"(w) selected-start projection must charge the selected rung in full, got {ladder_w}")
    decision_w = controller_decision(priors, synthetic_post, costs,
                                     "mechanical/short/contained", "worker-opus-high")
    check(not decision_w["projection_complete"]
          and any("failure/retry" in term for term in decision_w["unknown_terms"])
          and any("verification" in term for term in decision_w["unknown_terms"]),
          f"(w) missing Controller terms must be exposed, got {decision_w}")

    return (not problems, problems)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sensitivity", choices=("mechanical", "structured", "open"))
    ap.add_argument("--horizon", choices=("short", "medium", "long"),
                     help="required with plain --sensitivity/--blast/--horizon (or pass --from-line)")
    ap.add_argument("--blast", choices=("contained", "consequential"))
    ap.add_argument("--self-directed", action="store_true",
                     help="the task demands sustained, self-directed investigation "
                          "that reshapes its own plan (ROUTING.md section 2's tie-break)")
    ap.add_argument("--prior-failure", choices=("none", "failed_at_xhigh"), default="none",
                     help="a documented failure at xhigh on this same task (the frontier row)")
    ap.add_argument("--from-line", help="parse sensitivity/horizon/blast/self_directed/prior_failure "
                                        "from a recorded assessment line instead of the flags above")
    ap.add_argument("--project", type=Path, default=Path("."),
                     help="consumer project root; the ledger defaults to <project>/.claude/routing-ledger.jsonl")
    ap.add_argument("--ledger", type=Path, help="override the ledger path")
    ap.add_argument("--explain", action="store_true",
                     help="use the priors and ledger (docs/PLAN-2.md Stage 2) and print the "
                          "posterior, the expected-cost arithmetic and the decision, one line each")
    ap.add_argument("--evidence-model",
                    help="select only evidence from this exact served model identity")
    ap.add_argument("--evidence-bundle-version",
                    help="select only evidence from this exact worker bundle version")
    ap.add_argument("--evidence-policy-version",
                    help="select only evidence from this exact routing policy version")
    ap.add_argument("--evidence-acceptance-version",
                    help="select only evidence from this exact acceptance-contract version")
    ap.add_argument("--evidence-max-age-days", type=int,
                    help="exclude capability evidence older than this many days")
    ap.add_argument("--include-incompatible-evidence", action="store_true",
                    help="explicitly pool different model/bundle/policy/acceptance identities")
    ap.add_argument("--record", action="store_true", help="append an outcome to the ledger instead of resolving, "
                                                            "or complete a --pending entry in place")
    ap.add_argument("--spawn", action="store_true",
                     help="write a pending ledger entry at spawn time (docs/COMPACTION-DESIGN.md section 4); "
                          "needs --task-slug, --first-cell, --worker-name and an assessment")
    ap.add_argument("--worker-name", help="--spawn: the name the Agent call gave this worker, "
                                           "so --recover can name it after a compaction. --record (no --pending): "
                                           "optional, looked up in tools/context_probe.py's data to fill context; "
                                           "omit to record context as unobserved. --record --pending always uses "
                                           "the name recorded at --spawn time instead")
    ap.add_argument("--pending", metavar="LED-ID",
                     help="--record: complete this --spawn entry in place instead of appending a new one")
    ap.add_argument("--acceptance-contract", type=Path,
                    help="--spawn/--record: version-1 JSON contract frozen before work starts")
    ap.add_argument("--review-acceptance", metavar="LED-ID",
                    help="settle a rubric contract after explicit human review")
    ap.add_argument("--review-decision", choices=("pass", "fail"))
    ap.add_argument("--reviewer", help="identity of the human making --review-decision")
    ap.add_argument("--review-notes", default="", help="review provenance, at most 1000 characters")
    ap.add_argument("--recover", action="store_true",
                     help="print the SessionStart(compact) hook's report: pending workers and the newest "
                          "handoff, zero model calls (docs/COMPACTION-DESIGN.md section 4)")
    ap.add_argument("--migrate-ledger-v2", action="store_true",
                    help="explicitly migrate version 0/1 rows to per-attempt version 2; creates an exact backup")
    ap.add_argument("--restore-ledger-backup", type=Path, metavar="PATH",
                    help="restore exact ledger bytes from PATH, retaining the current ledger as a pre-restore backup")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --migrate-ledger-v2 or --restore-ledger-backup, report without writing")
    ap.add_argument("--session-pointer", action="store_true",
                     help="SessionStart hook mode (docs/COMPACTION-DESIGN.md section 13.4): read the hook's "
                          "own JSON input from stdin and write .claude/session.json under --project; "
                          "never raises on malformed stdin, prints one line to stderr and exits 1 instead")
    ap.add_argument("--task-slug", help="--record/--spawn: short name for the routed task")
    ap.add_argument("--first-cell", help="--record/--spawn: the cell, or 'controller', tried first")
    ap.add_argument("--outcome", choices=("pass", "fail", "unknown"), help="--record: final_outcome")
    ap.add_argument("--cost-usd", type=float,
                    help="--record: total cost across every rung tried; omit when unknown, never substitute zero")
    ap.add_argument("--wall-clock-s", type=float,
                    help="--record: total wall clock across every rung tried; omit when unknown")
    ap.add_argument("--attempt-json", action="append", default=[], metavar="JSON",
                    help="--record: repeatable per-attempt object, in routed order; records exact cell, "
                         "served model, status, usage and wall time without allocating the task total")
    ap.add_argument("--escalation", action="append", default=[], metavar="CELL:OUTCOME",
                     help="--record: repeatable, one later rung tried, in order")
    ap.add_argument("--controller-run-dir", help="--record: the Controller's runs/<id>, if it ran")
    ap.add_argument("--winning-technique", choices=("b0", "subtract", "re-represent", "abduce", "other"),
                     help="--record: from the Controller's SolutionRecord, if it ran and produced one")
    ap.add_argument("--notes", default="", help="--record/--spawn: free text, max 300 characters")
    ap.add_argument("--json", action="store_true", help="print the full matched rule or plan, not just the cell name")
    ap.add_argument("--rigour-assessment", type=Path,
                    help="R4: resolve a version-1 RigourAssessment without dispatching work")
    ap.add_argument("--controller", choices=("auto", "on", "off"),
                    help="R4 explicit per-invocation Controller mode; does not persist or dispatch")
    ap.add_argument("--session-id", help="R4 control lookup for --rigour-assessment")
    ap.add_argument("--worker-cell", default="worker-sonnet-low",
                    help="R4 selected downstream worker cell")
    ap.add_argument("--controller-profile", default="standard",
                    help="R4 Controller role profile")
    ap.add_argument("--prior-controller-invocations", type=int, default=0,
                    help="R4 Controller count for this task revision")
    ap.add_argument("--public-passed", action="store_true",
                    help="R4 visible acceptance passed; unresolved consequential rigour still gates")
    ap.add_argument("--selftest", action="store_true", help="run the scripted ledger scenarios; no file I/O outside a temp directory")
    args = ap.parse_args(argv)

    if args.selftest:
        ok, problems = _selftest(verbose=args.json)
        if ok:
            print("selftest: PASS, 23 scenarios")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.rigour_assessment:
        incompatible = (args.record or args.spawn or args.recover or args.review_acceptance
                        or args.migrate_ledger_v2 or args.restore_ledger_backup or args.session_pointer)
        if incompatible:
            ap.error("--rigour-assessment cannot be combined with ledger mutation or recovery modes")
        try:
            value = json.loads(args.rigour_assessment.read_text(encoding="utf-8"))
            decision = plan_rigour(
                value, args.project, explicit_mode=args.controller,
                session_id=args.session_id, selected_cell=args.worker_cell,
                controller_profile=args.controller_profile,
                prior_controller_invocations=args.prior_controller_invocations,
                public_passed=args.public_passed,
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            ap.error(f"rigour assessment failed: {exc}")
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0

    if args.session_pointer:
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except json.JSONDecodeError as exc:
            print(f"route.py --session-pointer: stdin did not parse as JSON: {exc}", file=sys.stderr)
            return 1
        if not isinstance(payload, dict):
            print("route.py --session-pointer: stdin did not parse as a JSON object", file=sys.stderr)
            return 1
        _write_session_pointer(payload, args.project)
        return 0

    if args.migrate_ledger_v2 and args.restore_ledger_backup:
        ap.error("choose only one of --migrate-ledger-v2 and --restore-ledger-backup")
    if args.dry_run and not (args.migrate_ledger_v2 or args.restore_ledger_backup):
        ap.error("--dry-run needs --migrate-ledger-v2 or --restore-ledger-backup")
    if args.migrate_ledger_v2 or args.restore_ledger_backup:
        ledger_path = args.ledger or default_ledger_path(args.project)
        try:
            result = (migrate_ledger_v2(ledger_path, dry_run=args.dry_run)
                      if args.migrate_ledger_v2 else
                      restore_ledger_backup(ledger_path, args.restore_ledger_backup, dry_run=args.dry_run))
        except (OSError, RoutingError, ValueError) as exc:
            print(f"route.py ledger operation failed for {str(ledger_path)!r}: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(result, indent=2 if args.json else None))
        return 0

    if args.recover:
        print(recover_report(args.project))
        return 0

    if args.review_acceptance:
        if not args.review_decision or not args.reviewer:
            ap.error("--review-acceptance needs --review-decision and --reviewer")
        ledger_path = args.ledger or default_ledger_path(args.project)
        with ledger_lock(ledger_path):
            rows = _ledger_rows(ledger_path)
            for i, (entry, original) in enumerate(rows):
                if entry is None or entry.get("id") != args.review_acceptance:
                    continue
                try:
                    resolved = acceptance_lib.review(args.project, entry.get("acceptance") or {},
                                                     args.review_acceptance, args.review_decision,
                                                     args.reviewer, args.review_notes)
                except acceptance_lib.AcceptanceError as exc:
                    print(f"acceptance review failed: {exc}", file=sys.stderr)
                    return 1
                updated = {**entry, "acceptance": resolved}
                rows[i] = (updated, json.dumps(updated, ensure_ascii=False))
                _atomic_write_ledger(ledger_path, [line for _, line in rows])
                print(args.review_acceptance)
                return 0
        print(str(LedgerEntryNotFound(args.review_acceptance)), file=sys.stderr)
        return 1

    def resolve_assessment() -> tuple[str, str, str, bool, str]:
        if args.from_line:
            try:
                a = parse_assessment_line(args.from_line)
            except AssessmentLineError as exc:
                # ap.error() prints "usage: ..." plus the message to
                # stderr and exits 2, the same contract every other
                # input defect in this function already uses, rather
                # than a Python traceback with no exit code an
                # orchestrator's own "if route.py cannot run" fallback
                # (ROUTING.md section 2) can act on (audit A7,
                # docs/AUDIT-2026-09-16.md).
                ap.error(str(exc))
            return a["sensitivity"], a["horizon"], a["blast"], a["self_directed"], a["prior_failure"]
        if not args.sensitivity or not args.horizon or not args.blast:
            ap.error("--sensitivity, --horizon and --blast are required (or pass --from-line)")
        return args.sensitivity, args.horizon, args.blast, args.self_directed, args.prior_failure

    ledger_aware = args.record or args.explain or args.ledger is not None or args.from_line is not None

    if args.spawn:
        if not all((args.task_slug, args.first_cell, args.worker_name, args.acceptance_contract)):
            ap.error("--spawn needs --task-slug, --first-cell, --worker-name and --acceptance-contract")
        sensitivity, horizon, blast, self_directed, _ = resolve_assessment()
        if horizon is None:
            ap.error("--spawn needs --horizon (or a --from-line that carries one)")
        ledger_path = args.ledger or default_ledger_path(args.project)
        notes = _PENDING_NOTE_PREFIX + args.worker_name
        if args.notes:
            notes += f"; {args.notes}"
        try:
            acceptance = acceptance_lib.load_contract(args.project, args.acceptance_contract)
        except acceptance_lib.AcceptanceError as exc:
            ap.error(str(exc))
        entry = {"type": "RoutingLedgerEntry", "references": [],
                 "ts": dt.datetime.now().isoformat(), "task_slug": args.task_slug,
                 "bucket": f"{sensitivity}/{horizon}/{blast}", "self_directed": self_directed,
                 "first_cell": args.first_cell, "escalations": [], "final_outcome": "unknown",
                 "cost_usd": None, "wall_clock_s": None, "controller_run_dir": None, "winning_technique": None,
                 "notes": notes[:300], "context": dict(_NO_CONTEXT_OBSERVED),
                 **_entry_v2_fields(args.first_cell, [], "unknown", None, None, [], pending=True),
                 "acceptance": acceptance}
        entry = create_ledger_entry(ledger_path, entry)
        print(entry["id"])
        return 0

    if args.record and args.pending:
        if args.outcome is None:
            ap.error("--record --pending needs --outcome; omit unknown cost or duration instead of using zero")
        ledger_path = args.ledger or default_ledger_path(args.project)
        pending_entry = next((e for e in load_ledger(ledger_path) if e.get("id") == args.pending), None)
        if pending_entry is None:
            print(str(LedgerEntryNotFound(args.pending)), file=sys.stderr)
            return 1
        escalations = []
        for item in args.escalation:
            cell, _, outcome = item.partition(":")
            if outcome not in ("pass", "fail", "unknown"):
                ap.error(f"--escalation {item!r} must be CELL:pass|fail|unknown")
            escalations.append({"cell": cell, "outcome": outcome})
        context = fill_context(args.project, pending_worker_name(pending_entry), pending_entry.get("first_cell"))
        try:
            version_fields = _entry_v2_fields(pending_entry["first_cell"], escalations, args.outcome,
                                              args.cost_usd, args.wall_clock_s, args.attempt_json)
        except RoutingError as exc:
            ap.error(str(exc))
        if pending_entry.get("final_outcome") != "unknown":
            proposed = {"escalations": escalations, "final_outcome": args.outcome,
                        "cost_usd": args.cost_usd, "wall_clock_s": args.wall_clock_s,
                        "controller_run_dir": args.controller_run_dir,
                        "winning_technique": args.winning_technique,
                        "execution_status": version_fields["execution_status"],
                        "attempts": version_fields["attempts"]}
            if args.notes:
                proposed["notes"] = args.notes[:300]
            if all(pending_entry.get(key) == value for key, value in proposed.items()):
                print(pending_entry["id"])
                print("context: existing terminal event reused; verification was not rerun")
                return 0
            print(str(LedgerEntryNotPending(args.pending, pending_entry.get("final_outcome"))), file=sys.stderr)
            return 1
        try:
            acceptance = acceptance_lib.verify(args.project, pending_entry.get("acceptance") or {}, args.pending)
        except acceptance_lib.AcceptanceError as exc:
            ap.error(str(exc))
        updates = {"escalations": escalations, "final_outcome": args.outcome,
                   "cost_usd": args.cost_usd, "wall_clock_s": args.wall_clock_s,
                   "controller_run_dir": args.controller_run_dir, "winning_technique": args.winning_technique,
                   "context": context, **version_fields, "acceptance": acceptance}
        if args.notes:
            updates["notes"] = args.notes[:300]
        try:
            completed = complete_ledger_entry(ledger_path, args.pending, updates)
        except (LedgerEntryNotFound, LedgerEntryNotPending) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(completed["id"])
        print(f"context: {context['source']}")
        return 0

    if args.record:
        if not all((args.task_slug, args.first_cell, args.outcome is not None, args.acceptance_contract)):
            ap.error("--record needs --task-slug, --first-cell, --outcome and --acceptance-contract; "
                     "omit unknown cost or duration instead of using zero")
        sensitivity, horizon, blast, self_directed, _ = resolve_assessment()
        if horizon is None:
            ap.error("--record needs --horizon (or a --from-line that carries one)")
        ledger_path = args.ledger or default_ledger_path(args.project)
        escalations = []
        for item in args.escalation:
            cell, _, outcome = item.partition(":")
            if outcome not in ("pass", "fail", "unknown"):
                ap.error(f"--escalation {item!r} must be CELL:pass|fail|unknown")
            escalations.append({"cell": cell, "outcome": outcome})
        context = fill_context(args.project, args.worker_name, args.first_cell)
        try:
            acceptance = acceptance_lib.load_contract(args.project, args.acceptance_contract)
        except acceptance_lib.AcceptanceError as exc:
            ap.error(str(exc))
        entry = {"type": "RoutingLedgerEntry", "references": [],
                 "ts": dt.datetime.now().isoformat(), "task_slug": args.task_slug,
                 "bucket": f"{sensitivity}/{horizon}/{blast}", "self_directed": self_directed,
                 "first_cell": args.first_cell, "escalations": [], "final_outcome": "unknown",
                 "cost_usd": None, "wall_clock_s": None,
                 "controller_run_dir": None, "winning_technique": None,
                 "notes": args.notes[:300], "context": context,
                 **_entry_v2_fields(args.first_cell, [], "unknown", None, None, [], pending=True),
                 "acceptance": acceptance}
        try:
            entry = create_ledger_entry(ledger_path, entry)
            version_fields = _entry_v2_fields(args.first_cell, escalations, args.outcome,
                                              args.cost_usd, args.wall_clock_s, args.attempt_json)
            acceptance = acceptance_lib.verify(args.project, acceptance, entry["id"])
            entry = complete_ledger_entry(ledger_path, entry["id"], {
                "escalations": escalations, "final_outcome": args.outcome,
                "cost_usd": args.cost_usd, "wall_clock_s": args.wall_clock_s,
                "controller_run_dir": args.controller_run_dir,
                "winning_technique": args.winning_technique,
                "context": context, **version_fields, "acceptance": acceptance})
        except (RoutingError, acceptance_lib.AcceptanceError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(entry["id"])
        print(f"context: {context['source']}")
        return 0

    sensitivity, horizon, blast, self_directed, prior_failure = resolve_assessment()

    if ledger_aware:
        ledger_path = args.ledger or default_ledger_path(args.project)
        ledger = load_ledger(ledger_path)
        evidence_identity = {
            key: value for key, value in {
                "actual_model": args.evidence_model,
                "bundle_version": args.evidence_bundle_version,
                "policy_version": args.evidence_policy_version,
                "acceptance_contract_version": args.evidence_acceptance_version,
            }.items() if value is not None
        } or None
        try:
            result = plan(
                sensitivity, horizon, blast, self_directed, prior_failure, ledger=ledger,
                evidence_identity=evidence_identity,
                max_evidence_age_days=args.evidence_max_age_days,
                include_incompatible_evidence=args.include_incompatible_evidence)
        except NoRuleMatches as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.explain:
            post = result["posterior"]
            print(f"bucket: {result['bucket']}")
            if post:
                print(f"floor posterior mean: {post['floor_mean']:.3f} "
                      f"(ledger: {post['floor_ledger_passes']} pass, {post['floor_ledger_fails']} fail)")
                if result.get("policy") == "B0":
                    print(f"qualified default B0 sequence: {result['execution_ladder']}")
                    print("adaptive posterior is diagnostic only; Controller disabled")
                else:
                    print(f"active rungs, cost order: {post['active_rungs']}")
                for cell, m in sorted(post["rungs"].items()):
                    direct, conditional = m["direct"], m["conditional"]
                    print(f"  {cell}: direct {direct['mean']:.3f} "
                          f"({direct['ledger_passes']} pass, {direct['ledger_fails']} fail); "
                          f"conditional {conditional['mean']:.3f} "
                          f"({conditional['ledger_passes']} pass, {conditional['ledger_fails']} fail)")
                evidence = post["evidence"]
                conflicts = sorted(name for name, diagnostic in evidence["identity_populations"].items()
                                   if diagnostic.get("conflict"))
                print(f"evidence: {evidence['entries_seen']} entries; "
                      f"excluded unverified={evidence['unverified_excluded']}, "
                      f"old={evidence['age_excluded']}, compacted={evidence['compacted_excluded']}; "
                      f"identity target={evidence['identity_target'] or 'automatic exact cohort'}")
                if conflicts:
                    print(f"evidence identity conflicts (prior retained): {conflicts}")
            if result["controller"]:
                c = result["controller"]
                print(f"expected ladder from {c['start_cell']}: {c['execution_rungs']}; "
                      f"cost USD {c['e_ladder_usd']:.4f}, wall clock {c['e_ladder_wall_s']:.0f} s, "
                      f"P(fail all) {c['p_fail_all']:.3f}")
                print(f"Controller cost: USD {c['controller_cost_usd']:.4f}; decision: "
                      f"{'proactive' if c['proactive'] else 'not proactive'} ({c['reason']})")
                if c["label"]:
                    print(f"  {c['label']}")
                if c["unknown_terms"]:
                    print(f"projection incomplete: {'; '.join(c['unknown_terms'])}")
            print(f"projection: USD {result['projection']['cost_usd_expected']}, "
                  f"{result['projection']['wall_clock_s_expected']} s")
            if result["overflow"] and result["overflow"]["advisory"]:
                print(f"overflow: {result['overflow']['text']}")
            print(context_explain_line(args.project, load_priors()))
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(result["first"])
        return 0

    try:
        rule = resolve(sensitivity, horizon, blast, self_directed, prior_failure)
    except NoRuleMatches as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UnknownAxisValue as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(rule, indent=2))
    else:
        print(rule["worker"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
