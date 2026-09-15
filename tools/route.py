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
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
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
    `plan()` needs. The prose format carries no self_directed or
    prior_failure field; both default to the common case (false, none),
    the same default `resolve()` already uses for a caller with only the
    three assessment axes."""
    m = _TWO_STAGE_LINE_RE.search(line)
    if m:
        return {"sensitivity": m["sensitivity"].lower(), "horizon": m["horizon"].lower(),
                "blast": m["blast"].lower(), "self_directed": m["self_directed"].lower() == "true",
                "prior_failure": m["prior_failure"].lower()}
    m = _PROSE_LINE_RE.search(line)
    if m:
        return {"sensitivity": m["sensitivity"].lower(), "horizon": m["horizon"].lower(),
                "blast": m["blast"].lower(), "self_directed": False, "prior_failure": "none"}
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


def posterior(priors: dict, ledger: list[dict], bucket: str) -> dict:
    """Per-bucket posterior (docs/ROUTING-2-DESIGN.md section 3): the
    floor's Beta mean, updated from every ledger entry in this bucket
    whose outcome against the floor is known (a `pass` with no
    escalations, or a `fail` recorded as there being an escalation at
    all); each rung's Beta mean conditional on every cheaper rung having
    failed, updated from every escalation record naming that rung in this
    bucket; and the active rung list in cost order, `default_ladder`'s
    cells plus any cell that has met the activation threshold from this
    bucket's own escalation history. Raises NoRuleMatches (reusing
    `resolve()`'s own exception, since it is the same kind of gap) for a
    bucket outside the eighteen `routing_priors.json` seeds."""
    bdata = priors["buckets"].get(bucket)
    if bdata is None:
        s, h, b = bucket.split("/") if bucket.count("/") == 2 else (bucket, bucket, bucket)
        raise NoRuleMatches(s, h, b, f"{bucket!r} is not one of the seeded buckets")

    floor_prior = bdata["floor"]
    entries = [e for e in ledger if e.get("bucket") == bucket]
    floor_pass = sum(1 for e in entries if e.get("first_cell") == "worker-sonnet-low"
                      and not e.get("escalations") and e.get("final_outcome") == "pass")
    floor_fail = sum(1 for e in entries if e.get("first_cell") == "worker-sonnet-low"
                      and e.get("escalations"))
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

    return {"bucket": bucket, "floor_mean": floor_mean, "floor_ledger_passes": floor_pass,
            "floor_ledger_fails": floor_fail, "rungs": rungs, "active_rungs": active_rungs}


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

    return {"first": first, "bucket": bucket, "ladder": post["active_rungs"], "controller": decision,
            "posterior": post, "projection": {"cost_usd_expected": round(cost_expected, 4),
                                              "wall_clock_s_expected": round(wall_expected, 1)}}


def _selftest(verbose: bool = False) -> tuple[bool, list[str]]:
    """Scripted checks for the ledger-aware additions, no file I/O outside
    a temp directory (docs/ROUTING-2-DESIGN.md section 3, scenarios a-g)."""
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
    ap.add_argument("--record", action="store_true", help="append an outcome to the ledger instead of resolving")
    ap.add_argument("--task-slug", help="--record: short name for the routed task")
    ap.add_argument("--first-cell", help="--record: the cell, or 'controller', tried first")
    ap.add_argument("--outcome", choices=("pass", "fail", "unknown"), help="--record: final_outcome")
    ap.add_argument("--cost-usd", type=float, help="--record: total cost across every rung tried")
    ap.add_argument("--wall-clock-s", type=float, help="--record: total wall clock across every rung tried")
    ap.add_argument("--escalation", action="append", default=[], metavar="CELL:OUTCOME",
                     help="--record: repeatable, one later rung tried, in order")
    ap.add_argument("--controller-run-dir", help="--record: the Controller's runs/<id>, if it ran")
    ap.add_argument("--winning-technique", choices=("b0", "subtract", "re-represent", "abduce", "other"),
                     help="--record: from the Controller's SolutionRecord, if it ran and produced one")
    ap.add_argument("--notes", default="", help="--record: free text, max 300 characters")
    ap.add_argument("--json", action="store_true", help="print the full matched rule or plan, not just the cell name")
    ap.add_argument("--selftest", action="store_true", help="run the scripted ledger scenarios; no file I/O outside a temp directory")
    args = ap.parse_args(argv)

    if args.selftest:
        ok, problems = _selftest(verbose=args.json)
        if ok:
            print("selftest: PASS, 7 scenarios")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    def resolve_assessment() -> tuple[str, str | None, str, bool, str]:
        if args.from_line:
            a = parse_assessment_line(args.from_line)
            return a["sensitivity"], a["horizon"], a["blast"], a["self_directed"], a["prior_failure"]
        if not args.sensitivity or not args.blast:
            ap.error("--sensitivity and --blast are required (or pass --from-line)")
        return args.sensitivity, args.horizon, args.blast, args.self_directed, args.prior_failure

    ledger_aware = args.record or args.explain or args.ledger is not None or args.from_line is not None

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
        entry = {"type": "RoutingLedgerEntry", "id": next_ledger_id(ledger), "ledger_version": 0, "references": [],
                 "ts": dt.datetime.now().isoformat(), "task_slug": args.task_slug,
                 "bucket": f"{sensitivity}/{horizon}/{blast}", "self_directed": self_directed,
                 "first_cell": args.first_cell, "escalations": escalations, "final_outcome": args.outcome,
                 "cost_usd": args.cost_usd, "wall_clock_s": args.wall_clock_s,
                 "controller_run_dir": args.controller_run_dir, "winning_technique": args.winning_technique,
                 "notes": args.notes[:300]}
        append_ledger_entry(ledger_path, entry)
        print(entry["id"])
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
