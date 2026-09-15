#!/usr/bin/env python3
"""Replay every recorded routing verdict through the ledger-aware resolver.

    python3 test/harness/replay_routing.py
    python3 test/harness/replay_routing.py --record

Responsible for: docs/ROUTING-2-DESIGN.md section 4 (docs/PLAN-2.md Stage
2.3, D64). Extracts every fixture's recorded assessment line from
test/results/*routing*.md (both the two-stage design's five-field format
and the prose router's three-field format), resolves each through
tools/route.py's plan() with an empty ledger, and compares the result
against test/fixtures/routing.jsonl's expected_cell (F16 is scored on the
recorded action against "clarify" instead, since a two-stage line cannot
express clarify at all and never appears for that fixture). No live
claude -p call: every verdict replayed here was already paid for and
recorded when the batch that produced it ran.

Deliberately does not: gate on anything but the recorded two-stage opus
batch's pooled agreement. Prose batches (made with the destination table
in context) are the attractor's own record (D44), not the new resolver's,
and are reported for visibility only.

D65 (docs/DECISIONS.md), found while building this: `expected_cell` in
test/fixtures/routing.jsonl was fixed against the pre-Plan-2, floor-only
table (D45) and was never revised to expect the policy dial's deliberate
proactive-Controller divergence on an open+consequential assessment
(D64). Comparing a policy-fired row against `expected_cell` conflates
"the policy fired as designed" with "the assessment was wrong", and on
the gating batch every one of 27 disagreements was exactly this, not a
classifier regression (with them excluded, agreement is 125/125). The
gate below therefore excludes policy-fired rows from the agreement
count and reports the policy fire rate as its own, non-gating column.

Usage:
    python3 test/harness/replay_routing.py            human-readable, exit
                                                        0 if PASS_CONDITION
                                                        holds, 1 otherwise
    python3 test/harness/replay_routing.py --record    also write
                                                        test/results/<date>-replay-routing.md
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "test" / "results"
FIXTURES_PATH = REPO_ROOT / "test" / "fixtures" / "routing.jsonl"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import route  # noqa: E402 (path must be set first)
import claudep  # noqa: E402

# D40's measured cell agreement for the two-stage classifier at opus,
# reporting grade, 153 verdicts (docs/DECISIONS.md). The pass condition
# this harness gates on: the new resolver, on the same recorded verdicts,
# must not fall below what the classifier itself was measured at.
GATE_MIN_AGREEMENT = 0.922
GATING_GLOB = "2026-09-11-routing-opus-d65b476-two-stage-3axis-run*-of-9.md"

# A markdown table row's last cell, whichever table format produced it
# (docs/ROUTING-2-DESIGN.md section 1): both formats' raw verdict always
# starts with "assessment:" and is the final column before the closing "|".
ROW_RE = re.compile(r"^\|\s*(?P<fixture>F\d{2})\s*\|.*\|\s*(?P<raw>assessment:\s*[^|]*?)\s*\|\s*$")
ACTION_RE = re.compile(r"action:\s*(\w+)", re.IGNORECASE)


def load_fixtures() -> dict[str, dict]:
    fixtures = {}
    for line in FIXTURES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            row = json.loads(line)
            fixtures[row["id"]] = row
    return fixtures


def extract_rows(text: str) -> list[tuple[str, str]]:
    return [(m["fixture"], m["raw"].strip()) for line in text.splitlines() if (m := ROW_RE.match(line))]


def score_row(fixture_id: str, raw: str, fixtures: dict, priors: dict, costs: dict) -> dict:
    fx = fixtures.get(fixture_id)
    if fx is None:
        return {"fixture": fixture_id, "scored": False, "reason": "unknown fixture id"}

    if fx.get("expected_action") == "clarify":
        m = ACTION_RE.search(raw)
        if not m:
            return {"fixture": fixture_id, "scored": False, "reason": "two-stage line, no action field"}
        return {"fixture": fixture_id, "scored": True, "agree": m.group(1).lower() == "clarify",
                "first": None, "controller": False, "policy_fired": False, "blast": None}

    try:
        a = route.parse_assessment_line(raw)
    except route.AssessmentLineError:
        return {"fixture": fixture_id, "scored": False, "reason": "unparsed assessment line"}
    try:
        p = route.plan(a["sensitivity"], a["horizon"], a["blast"], a["self_directed"], a["prior_failure"],
                        priors=priors, ledger=[], costs=costs)
    except route.NoRuleMatches as exc:
        return {"fixture": fixture_id, "scored": False, "reason": f"no bucket: {exc}"}
    controller_fired = p["first"] == "controller"
    # D65: the policy dial's deliberate divergence from the floor (any
    # bucket assessed open+consequential, by design, D64) is not a
    # classifier error, and test/fixtures/routing.jsonl's expected_cell
    # was never revised to expect it (it reflects the pre-Plan-2, all-floor
    # table, D45). Comparing a policy-fired row against expected_cell
    # conflates "the policy worked as designed" with "the assessment was
    # wrong". Tag it, and exclude it from the agreement gate below rather
    # than count it as a disagreement.
    policy_fired = controller_fired and p["controller"] is not None and p["controller"]["reason"] == "policy"
    return {"fixture": fixture_id, "scored": True, "agree": p["first"] == fx.get("expected_cell"),
            "first": p["first"], "controller": controller_fired, "policy_fired": policy_fired, "blast": a["blast"]}


def score_file(path: Path, fixtures: dict, priors: dict, costs: dict) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [score_row(fixture_id, raw, fixtures, priors, costs) for fixture_id, raw in extract_rows(text)]


def batch_key(path: Path) -> str:
    """Group per-run files into their batch; a standalone file is its own
    batch. Strips a trailing '-runN-of-M' (any M) before the extension."""
    return re.sub(r"-run\d+-of-\d+$", "", path.stem)


def render(batches: dict[str, list[dict]], gate: dict, git_rev: str) -> str:
    lines = [f"# Routing replay, {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} at {git_rev}", "",
             "Every recorded routing verdict (test/results/*routing*.md) replayed through "
             "tools/route.py's plan() with an empty ledger (docs/ROUTING-2-DESIGN.md section 4, "
             "docs/PLAN-2.md Stage 2.3, D65). No live claude -p call.", "",
             f"**Gate**: pooled agreement on `{GATING_GLOB}` (D40's measured two-stage opus batch, "
             f"153 verdicts) at or above {GATE_MIN_AGREEMENT:.1%}, **excluding rows where the policy "
             f"dial fired** (D65: that is a deliberate divergence from the floor-only table "
             f"`expected_cell` was fixed against, D45, not a classifier error), and zero "
             f"`first: controller` on any contained fixture, pooled across every batch below.", "",
             f"Gate result: {'PASS' if gate['pass'] else 'FAIL'}. Gating batch agreement "
             f"{gate['gating_agree']}/{gate['gating_n']} ({gate['gating_rate']:.1%}) after excluding "
             f"{gate['gating_policy_excluded']} policy-fired row(s). "
             f"Controller-on-contained violations: {gate['contained_controller_violations']}.", ""]
    lines.append("| Batch | Scored | Agree (excl. policy) | Rate | 95% Wilson | Unparsed/skipped | Policy fires | Other controller fires |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for key in sorted(batches):
        rows = batches[key]
        scored = [r for r in rows if r["scored"]]
        non_policy = [r for r in scored if not r.get("policy_fired")]
        agree = sum(1 for r in non_policy if r["agree"])
        n = len(non_policy)
        lo, hi = claudep.wilson_interval(agree, n) if n else (0.0, 0.0)
        skipped = len(rows) - len(scored)
        policy_fires = sum(1 for r in scored if r.get("policy_fired"))
        other_controller_fires = sum(1 for r in scored if r.get("controller") and not r.get("policy_fired"))
        rate = f"{agree / n:.1%}" if n else "n/a"
        lines.append(f"| {key} | {n} | {agree} | {rate} | [{lo:.1%}, {hi:.1%}] | {skipped} | {policy_fires} | {other_controller_fires} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args(argv)

    fixtures = load_fixtures()
    priors = route.load_priors()
    costs = route.load_cost_table()

    files = sorted(RESULTS_DIR.glob("*routing*.md"))
    batches: dict[str, list[dict]] = {}
    for path in files:
        rows = score_file(path, fixtures, priors, costs)
        if rows:
            batches.setdefault(batch_key(path), []).extend(rows)

    gating_rows: list[dict] = []
    for path in files:
        if fnmatch.fnmatch(path.name, GATING_GLOB):
            gating_rows.extend(score_file(path, fixtures, priors, costs))
    gating_scored = [r for r in gating_rows if r["scored"]]
    gating_non_policy = [r for r in gating_scored if not r.get("policy_fired")]
    gating_agree = sum(1 for r in gating_non_policy if r["agree"])
    gating_n = len(gating_non_policy)
    gating_rate = gating_agree / gating_n if gating_n else 0.0
    gating_policy_excluded = len(gating_scored) - gating_n

    all_rows = [r for rows in batches.values() for r in rows]
    # A policy-fired row is by definition open+consequential (D64's proactive_policy.when),
    # never contained, so it cannot itself violate this; the check exists for
    # the expected-cost path, which D64 measured firing nowhere on the shipped priors.
    contained_violations = sum(1 for r in all_rows if r["scored"] and r.get("controller") and r.get("blast") == "contained")

    gate = {"gating_agree": gating_agree, "gating_n": gating_n, "gating_rate": gating_rate,
            "gating_policy_excluded": gating_policy_excluded,
            "contained_controller_violations": contained_violations,
            "pass": gating_n > 0 and gating_rate >= GATE_MIN_AGREEMENT and contained_violations == 0}

    import subprocess
    git_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=REPO_ROOT).stdout.strip() or "no-git"

    report = render(batches, gate, git_rev)
    print(report)

    if args.record:
        RESULTS_DIR.mkdir(exist_ok=True)
        out = claudep.unique_path(RESULTS_DIR / f"{dt.datetime.now().strftime('%Y-%m-%d')}-replay-routing.md")
        out.write_text(report, encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")

    return 0 if gate["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
