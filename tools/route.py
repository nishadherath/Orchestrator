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
import json
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
    return min(candidates, key=lambda rule: COST_ORDER.index(rule["worker"]))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sensitivity", required=True, choices=("mechanical", "structured", "open"))
    ap.add_argument("--horizon", choices=("short", "medium", "long"),
                     help="omit to use the two-axis variant (docs/CLASSIFIER-DESIGN.md): "
                          "the cheapest cell across all three horizons for this sensitivity/blast")
    ap.add_argument("--blast", required=True, choices=("contained", "consequential"))
    ap.add_argument("--self-directed", action="store_true",
                     help="the task demands sustained, self-directed investigation "
                          "that reshapes its own plan (ROUTING.md section 2's tie-break)")
    ap.add_argument("--prior-failure", choices=("none", "failed_at_xhigh"), default="none",
                     help="a documented failure at xhigh on this same task (the frontier row)")
    ap.add_argument("--json", action="store_true", help="print the full matched rule, not just the worker name")
    args = ap.parse_args(argv)

    try:
        if args.horizon is None:
            rule = resolve_two_axis(args.sensitivity, args.blast, args.self_directed, args.prior_failure)
        else:
            rule = resolve(args.sensitivity, args.horizon, args.blast, args.self_directed, args.prior_failure)
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
