#!/usr/bin/env python3
"""Resolve a task assessment to a worker cell, from data, not from a prompt.

Responsible for: the routing function `docs/CLASSIFIER-DESIGN.md` specifies
(D39, `docs/DECISIONS.md`). Reads `src/routing_table.json`, an ordered list
of rules, and returns the first rule whose conditions match the given
assessment. The table is data so `generate_workers.py`, `check.py` and this
script share one source instead of three parsers of `ROUTING.md`'s prose.

Deliberately does not: read `ROUTING.md`, decide whether a classifier ships
(that is Stage 6's measurement and D40), or validate that the table itself
is well-formed beyond what resolution needs (`check.py`'s TABLE-PROSE and
ROUTE-TOTAL checks do that).

The one non-obvious thing: the table has five inputs, not three
(`docs/PREMISES.md`, `docs/CLASSIFIER-DESIGN.md`). `self_directed` and
`prior_failure` default to the common case (false, none) so a caller that
only has the three assessment axes still gets a correct answer for every
triple except the one row `prior_failure` alone can reach (the frontier
row) and the one row `self_directed` alone disambiguates (the fable-xhigh
tie-break within open, long, consequential). Rules are checked in the order
the JSON lists them; `frontier` is listed first because it must override
every other condition, and `open-long-consequential-self-directed` is
listed before the general `open-any-consequential` row it would otherwise
lose to.

Usage:
    python3 tools/route.py --sensitivity structured --horizon short --blast contained
    python3 tools/route.py --sensitivity open --horizon long --blast consequential --self-directed
    python3 tools/route.py --sensitivity mechanical --horizon long --blast contained
        (a documented gap: exits 1, explains why, per docs/DECISIONS.md D27)

    Ledger-aware routing and outcome recording (docs/PLAN-2.md Stage 2,
    docs/ROUTING-2-DESIGN.md) and pending-worker tracking across a
    compaction (docs/PLAN-3.md Stage B, docs/COMPACTION-DESIGN.md):
    python3 tools/route.py --from-line "<assessment line>" --project . --explain
    python3 tools/route.py --spawn --from-line "<line>" --project . \\
        --task-slug refactor-parser --first-cell worker-sonnet-low --worker-name refactor-parser
    python3 tools/route.py --record --pending led-042 --project . \\
        --outcome pass --cost-usd 0.17 --wall-clock-s 52
    python3 tools/route.py --recover --project .

    The session pointer, written from a SessionStart hook's own stdin
    (docs/COMPACTION-DESIGN.md section 13.4), so fill_context can scope a
    transcript search to the current session rather than every session
    under the project:
    python3 tools/route.py --session-pointer --project . < hook-input.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Literal, TypedDict

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


# Cost order for the two-axis collapse below: cheapest first. Identical to
# benchmark.py's own LADDER; duplicated rather than shared, because both
# scripts are meant to stand alone (the same rationale generate_workers.py's
# bundle_tag() and score_routing.py's wilson_interval() already give for
# their own duplicated helpers). Does not include worker-opus-max or
# worker-fable-max (the frontier row, reached only via prior_failure, never
# by the collapse below) or the cells ROUTING.md's constraints call rarely
# right (worker-sonnet-max, worker-fable-low, worker-fable-medium), since
# none of the six (sensitivity, blast) pairs the collapse considers reaches
# any of those five.
COST_ORDER = (
    "worker-sonnet-low",
    "worker-sonnet-medium",
    "worker-sonnet-high",
    "worker-sonnet-xhigh",
    "worker-opus-high",
    "worker-opus-xhigh",
    "worker-fable-xhigh",
)


def resolve_two_axis(sensitivity: Sensitivity, blast: Blast,
                      self_directed: bool = False, prior_failure: PriorFailure = "none",
                      table: dict | None = None) -> Rule:
    """The two-axis classifier variant (docs/CLASSIFIER-DESIGN.md): resolve on
    sensitivity and blast alone, taking the cheapest cell the three-axis
    table gives across all three horizons for that pair, per P12
    (docs/PREMISES.md, the project's own standing policy of taking the
    cheaper of two defensible cells).

    Computed from the three-axis table each call rather than a second,
    hand-maintained table, so there is exactly one source of truth and the
    collapse cannot drift from what resolve() would give per horizon.

    Raises NoRuleMatches only if every horizon is a gap for this
    (sensitivity, blast) pair; if at least one horizon resolves, the
    cheapest resolving one wins even if others are gaps (mechanical,
    contained collapses to worker-sonnet-low this way, since long is a
    documented gap but short and medium both resolve).

    Known limitation, not specially handled: self_directed genuinely
    implies a long horizon (ROUTING.md's own wording, "reshapes its own
    plan as it goes"), but this function tries it against all three
    horizons regardless, and at open/consequential the cheaper
    worker-opus-xhigh from a hypothetical short or medium horizon wins over
    worker-fable-xhigh, silently ignoring the self_directed signal rather
    than honouring it. `docs/CLASSIFIER-DESIGN.md`'s pre-registration
    already excludes the two-axis configuration from cell-agreement
    scoring for the same underlying reason (dropping an axis changes the
    correct answer), so this is recorded here rather than fixed: fixing it
    would mean deciding what the two-axis variant does with a field whose
    only defined meaning already depends on the axis being dropped.
    """
    table = table if table is not None else load_table()
    candidates: list[Rule] = []
    last_exc: NoRuleMatches | None = None
    for horizon in table["axes"]["horizon"]:
        try:
            candidates.append(resolve(sensitivity, horizon, blast, self_directed, prior_failure, table))
        except NoRuleMatches as exc:
            last_exc = exc
    if not candidates:
        raise last_exc
    # The frontier rule matches on prior_failure alone, ignoring sensitivity,
    # horizon and blast, so if prior_failure="failed_at_xhigh" it matches
    # identically at all three horizons: candidates here are either all the
    # frontier rule or none of them, never a mix. Its worker (worker-opus-max)
    # is deliberately absent from COST_ORDER (it is not a rung on the cost
    # ladder the collapse ranks), so it is returned directly rather than run
    # through cost-ranking, which would raise ValueError on the missing
    # lookup. Found live, 2026-09-11, Stage 6.3 (docs/PLAN.md): a two-stage
    # classifier call replied prior_failure: failed_at_xhigh for a real
    # fixture and crashed exactly this path before this fix. Recorded with
    # Stage 6.4's D40, which covers this same measurement run.
    escalation = next((c for c in candidates if c.get("escalation_only")), None)
    if escalation:
        return escalation
    return min(candidates, key=lambda rule: COST_ORDER.index(rule["worker"]))


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
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"warning: {path} line {lineno} did not parse (a partial write from an "
                  "interrupted append?); ignoring it", file=sys.stderr)
    return entries


def append_ledger_entry(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class LedgerEntryNotFound(RoutingError):
    def __init__(self, entry_id: str) -> None:
        super().__init__(f"no ledger entry with id {entry_id!r}")


class LedgerEntryNotPending(RoutingError):
    def __init__(self, entry_id: str, outcome: str) -> None:
        super().__init__(f"ledger entry {entry_id!r} is not pending (final_outcome already {outcome!r})")


def complete_ledger_entry(path: Path, entry_id: str, updates: dict) -> dict:
    """Complete a `--spawn`-created pending entry in place
    (docs/COMPACTION-DESIGN.md section 4), rather than appending a second
    record for the same task. Rewrites the whole file from every entry
    that parses, in order, with `entry_id`'s fields merged with `updates`;
    a line `load_ledger` could not parse is therefore dropped by this
    write path the same way `load_ledger` already drops it on read, which
    is `--record`'s existing tolerance for a partial write, not a new
    exception to it. Raises `LedgerEntryNotFound` or
    `LedgerEntryNotPending` rather than silently appending a stray
    record, since a pending entry that cannot be found or is already
    complete is a caller bug, not routine."""
    entries = load_ledger(path)
    for i, entry in enumerate(entries):
        if entry.get("id") == entry_id:
            if entry.get("final_outcome") != "unknown":
                raise LedgerEntryNotPending(entry_id, entry.get("final_outcome"))
            completed = {**entry, **updates}
            entries[i] = completed
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                for e in entries:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")
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


def posterior(priors: dict, ledger: list[dict], bucket: str) -> dict:
    """Per-bucket posterior (docs/ROUTING-2-DESIGN.md section 3): the
    floor's Beta mean, updated from every ledger entry in this bucket
    whose outcome against the floor is known (a `pass` with no
    escalations, or a `fail`, an escalated failure or not); each rung's
    Beta mean conditional on every cheaper rung having failed, updated
    from every escalation record naming that rung in this bucket; and
    the active rung list in cost order, `default_ladder`'s cells plus
    any cell that has met the activation threshold from this bucket's
    own escalation history. Raises NoRuleMatches (reusing `resolve()`'s
    own exception, since it is the same kind of gap) for a bucket
    outside the eighteen `routing_priors.json` seeds.

    A floor failure counts whether or not the orchestrator went on to
    escalate it (`final_outcome == "fail"`), or escalated it regardless
    of what the escalated attempt's own outcome ended up being (any
    non-empty `escalations`, since an escalation happens only after the
    floor has already failed). Before D81/A4 (`docs/AUDIT-2026-09-16.md`)
    only the second case counted, so a `--record --outcome fail` with no
    `--escalation` flag, a legal call `ORCHESTRATOR.md` section 2
    invites, moved neither `floor_pass` nor `floor_fail` and the ledger
    silently ignored it.

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
    entries = [e for e in all_entries if not _is_compacted(e)]

    floor_prior = bdata["floor"]
    floor_pass = sum(1 for e in entries if e.get("first_cell") == "worker-sonnet-low"
                      and not e.get("escalations") and e.get("final_outcome") == "pass")
    floor_fail = sum(1 for e in entries if e.get("first_cell") == "worker-sonnet-low"
                      and (e.get("final_outcome") == "fail" or e.get("escalations")))
    floor_mean = _beta_mean(floor_prior["alpha"], floor_prior["beta"], floor_pass, floor_fail)

    rung_counts: dict[str, list[int]] = {}
    for e in entries:
        for esc in e.get("escalations", []) or []:
            cell, outcome = esc.get("cell"), esc.get("outcome")
            if not cell or outcome not in ("pass", "fail"):
                continue
            counts = rung_counts.setdefault(cell, [0, 0])
            counts[0 if outcome == "pass" else 1] += 1

    default_weak_prior = {"alpha": 1.0, "beta": 1.0}  # uninformative: no bucket-specific
    # measurement exists for a rung the ledger alone activates, so it starts
    # at mean 0.5 and moves on that project's own evidence from there.
    rung_priors = bdata.get("rungs_given_failure_below", {})
    rungs: dict[str, dict] = {}
    seen_cells = set(rung_counts) | set(rung_priors)
    for cell in seen_cells:
        prior = rung_priors.get(cell, default_weak_prior)
        p, f = rung_counts.get(cell, (0, 0))
        rungs[cell] = {"mean": _beta_mean(prior["alpha"], prior["beta"], p, f),
                       "ledger_passes": p, "ledger_fails": f}

    steering = priors["steering"]
    base_ladder = [c for c in priors["default_ladder"] if c in COST_ORDER]
    activated = [cell for cell, m in rungs.items()
                 if cell not in base_ladder and cell in COST_ORDER
                 and (m["ledger_passes"] + m["ledger_fails"]) >= steering["steering_rung_activation_min_n"]
                 and m["mean"] >= steering["steering_rung_activation_min_pass"]]
    active_rungs = sorted(set(base_ladder) | set(activated), key=COST_ORDER.index)

    known_counts = [c for c in (_known_compaction_count(e) for e in all_entries) if c is not None]
    overflow_pass = sum(1 for c in known_counts if c >= 1)
    overflow_fail = sum(1 for c in known_counts if c == 0)
    overflow_prior = bdata["overflow"]
    overflow_mean = _beta_mean(overflow_prior["alpha"], overflow_prior["beta"], overflow_pass, overflow_fail)

    return {"bucket": bucket, "floor_mean": floor_mean, "floor_ledger_passes": floor_pass,
            "floor_ledger_fails": floor_fail, "rungs": rungs, "active_rungs": active_rungs,
            "overflow_mean": overflow_mean, "overflow_n": overflow_pass + overflow_fail,
            "overflow_compacted": overflow_pass}


def _rung_pass_mean(post: dict, cell: str) -> float:
    if cell == "worker-sonnet-low":
        return post["floor_mean"]
    return post["rungs"].get(cell, {"mean": 0.5})["mean"]


def expected_ladder_cost(post: dict, costs: dict) -> dict:
    """Sequential expected cost and wall clock down the active rungs:
    cost(rung) x P(reach rung), where P(reach) is the product of the
    failure probabilities of every cheaper active rung (the benchmark
    staircase only ever climbed after a failure, so a rung's measured
    rate already is this conditional; docs/ROUTING-2-DESIGN.md section 3,
    D64 point 2). A rung with no cost row (the frontier cells) is skipped
    in the sum and named in `unpriced_rungs`, not silently treated as
    free."""
    e_cost, e_wall, p_reach = 0.0, 0.0, 1.0
    p_reach_by_rung: dict[str, float] = {}
    unpriced: list[str] = []
    for cell in post["active_rungs"]:
        row = costs["cells"].get(cell, {})
        cost, wall = row.get("cost_per_run_usd"), row.get("wall_clock_s")
        p_reach_by_rung[cell] = p_reach
        if cost is None:
            unpriced.append(cell)
        else:
            e_cost += cost * p_reach
            e_wall += (wall or 0) * p_reach
        p_reach *= (1 - _rung_pass_mean(post, cell))
    return {"e_ladder_usd": round(e_cost, 4), "e_ladder_wall_s": round(e_wall, 1),
            "p_fail_all": round(p_reach, 4), "p_reach_by_rung": {k: round(v, 4) for k, v in p_reach_by_rung.items()},
            "unpriced_rungs": unpriced}


def controller_decision(priors: dict, post: dict, costs: dict, bucket: str) -> dict:
    """Whether the Controller pre-empts the ladder for this bucket
    (docs/ROUTING-2-DESIGN.md section 3, D64): a labelled risk-appetite
    policy naming sensitivity and blast, checked first, or expected-cost
    arithmetic otherwise. On the priors this repository ships, the
    arithmetic fires in no bucket; only the policy dial does, and only
    where it is enabled."""
    rule = priors["controller_rule"]
    ladder = expected_ladder_cost(post, costs)
    controller_cost = costs["controller"]["quick_mode_run_usd"] + costs["controller"]["instantiation_usd"]
    sensitivity, horizon, blast = bucket.split("/")

    policy = rule["proactive_policy"]
    if (policy["enabled"] and sensitivity in policy["when"].get("sensitivity", ())
            and blast in policy["when"].get("blast", ())):
        return {**ladder, "proactive": True, "reason": "policy", "controller_cost_usd": round(controller_cost, 4),
                "failure_cost_usd": None, "label": policy["label"]}

    failure_cost = (rule["failure_cost"]["consequential_usd"] if blast == "consequential"
                    else ladder["e_ladder_usd"])
    fires = ladder["e_ladder_usd"] + ladder["p_fail_all"] * failure_cost > controller_cost
    return {**ladder, "proactive": fires, "reason": "expected_cost" if fires else "none",
            "controller_cost_usd": round(controller_cost, 4), "failure_cost_usd": round(failure_cost, 4),
            "label": None}


def plan(sensitivity: Sensitivity, horizon: Horizon, blast: Blast,
         self_directed: bool = False, prior_failure: PriorFailure = "none",
         priors: dict | None = None, ledger: list[dict] | None = None,
         costs: dict | None = None) -> dict:
    """The one function an orchestrator calls (docs/ROUTING-2-DESIGN.md
    section 3): resolves an assessment plus a project's own ledger to the
    cell (or `"controller"`) to try first, the rest of the active ladder,
    the Controller's decision and why, and a cost/time projection. Falls
    straight to the frontier rung on `prior_failure`, exactly as
    `resolve()` already does, since that mechanism is unchanged by any of
    this."""
    priors = priors if priors is not None else load_priors()
    costs = costs if costs is not None else load_cost_table()
    ledger = ledger if ledger is not None else []

    if prior_failure == "failed_at_xhigh":
        frontier = resolve(sensitivity, horizon, blast, self_directed, prior_failure, table=None)["worker"]
        return {"first": frontier, "bucket": None, "ladder": [], "controller": None, "posterior": None,
                "overflow": None,
                "projection": {"cost_usd_expected": None, "wall_clock_s_expected": None,
                               "note": "frontier rung from prior_failure; unmeasured (src/cost_table.json)"}}

    bucket = f"{sensitivity}/{horizon}/{blast}"
    post = posterior(priors, ledger, bucket)
    decision = controller_decision(priors, post, costs, bucket)

    if decision["proactive"]:
        first = "controller"
    else:
        min_pass = priors["steering"]["steering_first_rung_min_pass"]
        first = next((c for c in post["active_rungs"] if _rung_pass_mean(post, c) >= min_pass),
                     post["active_rungs"][0] if post["active_rungs"] else "worker-sonnet-low")

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

    return {"first": first, "bucket": bucket, "ladder": post["active_rungs"], "controller": decision,
            "posterior": post, "overflow": overflow,
            "projection": {"cost_usd_expected": round(cost_expected, 4),
                            "wall_clock_s_expected": round(wall_expected, 1)}}


CONTEXT_USAGE_FILENAME = ".claude/context-usage.json"
SESSION_POINTER_FILENAME = ".claude/session.json"


def default_context_usage_path(project: Path) -> Path:
    return project / CONTEXT_USAGE_FILENAME


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

    usage_path = default_context_usage_path(project)
    if usage_path.exists():
        try:
            data = json.loads(usage_path.read_text(encoding="utf-8"))
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

    Section 13.3's addition: when `.claude/context-usage.json` is absent
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
    path = default_context_usage_path(project)
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
        return "context: unknown (no .claude/context-usage.json; expected in a headless session)"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "context: unknown (.claude/context-usage.json did not parse)"
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

    # (d) open/long/consequential returns the policy reason; disabling the
    # dial falls through to the floor.
    p_policy = plan("open", "long", "consequential", priors=priors, ledger=[], costs=costs)
    check(p_policy["first"] == "controller" and p_policy["controller"]["reason"] == "policy",
          f"(d) open/long/consequential should pre-empt on policy, got {p_policy['first']!r} "
          f"reason {p_policy['controller'].get('reason') if p_policy['controller'] else None!r}")
    import copy
    priors_off = copy.deepcopy(priors)
    priors_off["controller_rule"]["proactive_policy"]["enabled"] = False
    p_policy_off = plan("open", "long", "consequential", priors=priors_off, ledger=[], costs=costs)
    check(p_policy_off["first"] != "controller",
          f"(d) with the dial disabled, open/long/consequential should not pre-empt, got {p_policy_off['first']!r}")

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
    p_e = plan(s, h, b, priors=priors, ledger=ledger_e, costs=costs)
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

    # (g) prior_failure=failed_at_xhigh returns the frontier rung regardless
    # of the ledger.
    p_g = plan("open", "long", "consequential", prior_failure="failed_at_xhigh",
               priors=priors, ledger=ledger_e, costs=costs)
    check(p_g["first"] == "worker-opus-max", f"(g) failed_at_xhigh should return the frontier rung, got {p_g['first']!r}")

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
        check("(none)" in report_done and "led-001" not in report_done,
              f"(h) recover_report should list no pending entries once completed, got:\n{report_done}")
        try:
            complete_ledger_entry(ledger_path, "led-001", {"final_outcome": "pass"})
            check(False, "(h) completing an already-complete entry should raise LedgerEntryNotPending")
        except LedgerEntryNotPending:
            pass
        try:
            complete_ledger_entry(ledger_path, "led-999", {"final_outcome": "pass"})
            check(False, "(h) completing an unknown id should raise LedgerEntryNotFound")
        except LedgerEntryNotFound:
            pass

    # (i) context_explain_line: absent file, under threshold, over
    # threshold, and a stale sample all print the right thing rather than
    # a wrong number (docs/COMPACTION-DESIGN.md section 4).
    with tempfile.TemporaryDirectory(prefix="route-selftest-") as tmp:
        project = Path(tmp)
        line_absent = context_explain_line(project, priors)
        check(line_absent.startswith("context: unknown") and "no .claude/context-usage.json" in line_absent,
              f"(i) an absent context-usage.json should print 'unknown', got {line_absent!r}")

        usage_path = default_context_usage_path(project)
        usage_path.parent.mkdir(parents=True, exist_ok=True)
        threshold = priors["steering"]["handoff_context_percent"]
        usage_path.write_text(json.dumps({"main": {"used_percentage": threshold - 5, "context_window_size": 200000,
                                                     "sampled_at": dt.datetime.now().isoformat()}}), encoding="utf-8")
        line_under = context_explain_line(project, priors)
        check("not yet" in line_under, f"(i) below the threshold should print 'not yet', got {line_under!r}")

        usage_path.write_text(json.dumps({"main": {"used_percentage": threshold + 5, "context_window_size": 200000,
                                                     "sampled_at": dt.datetime.now().isoformat()}}), encoding="utf-8")
        line_over = context_explain_line(project, priors)
        check("WRITE A HANDOFF" in line_over, f"(i) at or above the threshold should recommend a handoff, got {line_over!r}")

        stale_s = priors["steering"]["context_stale_s"]
        old_ts = (dt.datetime.now() - dt.timedelta(seconds=stale_s + 60)).isoformat()
        usage_path.write_text(json.dumps({"main": {"used_percentage": threshold + 5, "context_window_size": 200000,
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

        usage_path.write_text(json.dumps({"tasks": {"probe-worker": {"peak_tokens": 91000, "contextWindowSize": 200000,
                                                                       "compactions": 2}}}), encoding="utf-8")
        statusline_ctx = fill_context(project, "probe-worker")
        check(statusline_ctx == {"peak_tokens": 91000, "window": 200000, "compactions": 2, "source": "statusline"},
              f"fill_context should read a matching name from the probe's tasks key, got {statusline_ctx}")

        missing_ctx = fill_context(project, "no-such-worker")
        check(missing_ctx["source"] == "none",
              f"fill_context should fall through to 'none' for a name the probe never saw, got {missing_ctx}")

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
    # .claude/context-usage.json is absent (docs/COMPACTION-DESIGN.md
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
            check(no_pointer_line.startswith("context: unknown") and "no .claude/context-usage.json" in no_pointer_line,
                  f"(m) with no session pointer and no context-usage.json, the line should stay "
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

    return (not problems, problems)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sensitivity", choices=("mechanical", "structured", "open"))
    ap.add_argument("--horizon", choices=("short", "medium", "long"),
                     help="omit, with no --ledger/--explain/--from-line, to use the two-axis "
                          "variant (docs/CLASSIFIER-DESIGN.md); required otherwise")
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
    ap.add_argument("--recover", action="store_true",
                     help="print the SessionStart(compact) hook's report: pending workers and the newest "
                          "handoff, zero model calls (docs/COMPACTION-DESIGN.md section 4)")
    ap.add_argument("--session-pointer", action="store_true",
                     help="SessionStart hook mode (docs/COMPACTION-DESIGN.md section 13.4): read the hook's "
                          "own JSON input from stdin and write .claude/session.json under --project; "
                          "never raises on malformed stdin, prints one line to stderr and exits 1 instead")
    ap.add_argument("--task-slug", help="--record/--spawn: short name for the routed task")
    ap.add_argument("--first-cell", help="--record/--spawn: the cell, or 'controller', tried first")
    ap.add_argument("--outcome", choices=("pass", "fail", "unknown"), help="--record: final_outcome")
    ap.add_argument("--cost-usd", type=float, help="--record: total cost across every rung tried")
    ap.add_argument("--wall-clock-s", type=float, help="--record: total wall clock across every rung tried")
    ap.add_argument("--escalation", action="append", default=[], metavar="CELL:OUTCOME",
                     help="--record: repeatable, one later rung tried, in order")
    ap.add_argument("--controller-run-dir", help="--record: the Controller's runs/<id>, if it ran")
    ap.add_argument("--winning-technique", choices=("b0", "subtract", "re-represent", "abduce", "other"),
                     help="--record: from the Controller's SolutionRecord, if it ran and produced one")
    ap.add_argument("--notes", default="", help="--record/--spawn: free text, max 300 characters")
    ap.add_argument("--json", action="store_true", help="print the full matched rule or plan, not just the cell name")
    ap.add_argument("--selftest", action="store_true", help="run the scripted ledger scenarios; no file I/O outside a temp directory")
    args = ap.parse_args(argv)

    if args.selftest:
        ok, problems = _selftest(verbose=args.json)
        if ok:
            print("selftest: PASS, 14 scenarios")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

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

    if args.recover:
        print(recover_report(args.project))
        return 0

    def resolve_assessment() -> tuple[str, str | None, str, bool, str]:
        if args.from_line:
            a = parse_assessment_line(args.from_line)
            return a["sensitivity"], a["horizon"], a["blast"], a["self_directed"], a["prior_failure"]
        if not args.sensitivity or not args.blast:
            ap.error("--sensitivity and --blast are required (or pass --from-line)")
        return args.sensitivity, args.horizon, args.blast, args.self_directed, args.prior_failure

    ledger_aware = args.record or args.explain or args.ledger is not None or args.from_line is not None

    if args.spawn:
        if not all((args.task_slug, args.first_cell, args.worker_name)):
            ap.error("--spawn needs --task-slug, --first-cell and --worker-name")
        sensitivity, horizon, blast, self_directed, _ = resolve_assessment()
        if horizon is None:
            ap.error("--spawn needs --horizon (or a --from-line that carries one)")
        ledger_path = args.ledger or default_ledger_path(args.project)
        ledger = load_ledger(ledger_path)
        notes = _PENDING_NOTE_PREFIX + args.worker_name
        if args.notes:
            notes += f"; {args.notes}"
        entry = {"type": "RoutingLedgerEntry", "id": next_ledger_id(ledger), "ledger_version": 1, "references": [],
                 "ts": dt.datetime.now().isoformat(), "task_slug": args.task_slug,
                 "bucket": f"{sensitivity}/{horizon}/{blast}", "self_directed": self_directed,
                 "first_cell": args.first_cell, "escalations": [], "final_outcome": "unknown",
                 "cost_usd": 0, "wall_clock_s": 0, "controller_run_dir": None, "winning_technique": None,
                 "notes": notes[:300], "context": dict(_NO_CONTEXT_OBSERVED)}
        append_ledger_entry(ledger_path, entry)
        print(entry["id"])
        return 0

    if args.record and args.pending:
        if not all((args.outcome is not None, args.cost_usd is not None, args.wall_clock_s is not None)):
            ap.error("--record --pending needs --outcome, --cost-usd and --wall-clock-s")
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
        updates = {"escalations": escalations, "final_outcome": args.outcome,
                   "cost_usd": args.cost_usd, "wall_clock_s": args.wall_clock_s,
                   "controller_run_dir": args.controller_run_dir, "winning_technique": args.winning_technique,
                   "ledger_version": 1, "context": context}
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
        if not all((args.task_slug, args.first_cell, args.outcome is not None,
                    args.cost_usd is not None, args.wall_clock_s is not None)):
            ap.error("--record needs --task-slug, --first-cell, --outcome, --cost-usd and --wall-clock-s")
        sensitivity, horizon, blast, self_directed, _ = resolve_assessment()
        if horizon is None:
            ap.error("--record needs --horizon (or a --from-line that carries one)")
        ledger_path = args.ledger or default_ledger_path(args.project)
        ledger = load_ledger(ledger_path)
        escalations = []
        for item in args.escalation:
            cell, _, outcome = item.partition(":")
            if outcome not in ("pass", "fail", "unknown"):
                ap.error(f"--escalation {item!r} must be CELL:pass|fail|unknown")
            escalations.append({"cell": cell, "outcome": outcome})
        context = fill_context(args.project, args.worker_name, args.first_cell)
        entry = {"type": "RoutingLedgerEntry", "id": next_ledger_id(ledger), "ledger_version": 1, "references": [],
                 "ts": dt.datetime.now().isoformat(), "task_slug": args.task_slug,
                 "bucket": f"{sensitivity}/{horizon}/{blast}", "self_directed": self_directed,
                 "first_cell": args.first_cell, "escalations": escalations, "final_outcome": args.outcome,
                 "cost_usd": args.cost_usd, "wall_clock_s": args.wall_clock_s,
                 "controller_run_dir": args.controller_run_dir, "winning_technique": args.winning_technique,
                 "notes": args.notes[:300], "context": context}
        append_ledger_entry(ledger_path, entry)
        print(entry["id"])
        print(f"context: {context['source']}")
        return 0

    sensitivity, horizon, blast, self_directed, prior_failure = resolve_assessment()

    if ledger_aware:
        if horizon is None:
            ap.error("the ledger-aware path needs a horizon (or a --from-line that carries one); "
                      "the two-axis variant is only available with plain --sensitivity/--blast")
        ledger_path = args.ledger or default_ledger_path(args.project)
        ledger = load_ledger(ledger_path)
        try:
            result = plan(sensitivity, horizon, blast, self_directed, prior_failure, ledger=ledger)
        except NoRuleMatches as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.explain:
            post = result["posterior"]
            print(f"bucket: {result['bucket']}")
            if post:
                print(f"floor posterior mean: {post['floor_mean']:.3f} "
                      f"(ledger: {post['floor_ledger_passes']} pass, {post['floor_ledger_fails']} fail)")
                print(f"active rungs, cost order: {post['active_rungs']}")
                for cell, m in sorted(post["rungs"].items()):
                    print(f"  {cell}: posterior mean {m['mean']:.3f} (ledger: {m['ledger_passes']} pass, {m['ledger_fails']} fail)")
            if result["controller"]:
                c = result["controller"]
                print(f"expected ladder cost: USD {c['e_ladder_usd']:.4f}, wall clock {c['e_ladder_wall_s']:.0f} s, "
                      f"P(fail all) {c['p_fail_all']:.3f}")
                print(f"Controller cost: USD {c['controller_cost_usd']:.4f}; decision: "
                      f"{'proactive' if c['proactive'] else 'not proactive'} ({c['reason']})")
                if c["label"]:
                    print(f"  {c['label']}")
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
        if horizon is None:
            rule = resolve_two_axis(sensitivity, blast, self_directed, prior_failure)
        else:
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
