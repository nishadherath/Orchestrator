#!/usr/bin/env python3
"""Score routing appropriateness: run each fixture through an orchestrator, compare the cell it picks.

Responsible for: the one signal CLAUDE.md says has no automatic source,
routing appropriateness. For every fixture in test/fixtures/routing.jsonl it
asks a non-interactive orchestrator (`claude -p`) to assess and select but
not spawn, parses the one-line verdict, and scores cell agreement, axis
agreement and provisioning direction. With --runs N it repeats the full pass
N times and aggregates with a Wilson score interval. With --record it writes
the dogfood log the charter requires to test/results/.

Deliberately does not: spawn workers (so a run costs one orchestrator turn
per fixture and no worker tokens), install the bundle (do that first from
dist/ into the consumer project), or tune anything.

The one non-obvious thing: a single pass conflates model judgement with the
small-sample noise inherent in a stochastic model call, so `--runs N`
repeats the full fixture pass N times and reports a 95 percent Wilson score
interval per fixture and overall, instead of treating one pass as ground
truth. A single pass is confirmed live (E12, `docs/FINDINGS.md`), but its
recorded results predate the fixed calibration instruction (D6,
`docs/DECISIONS.md`) and are not comparable with runs made after it. With
`--json`, output nests under a top-level "runs" list even when --runs is 1,
so downstream tooling has one schema regardless of run count.

Every rendered file and summary carries a grade, `steering` below nine runs
or `reporting` at nine or more, matching `benchmark.py`'s own two-threshold
discipline (`docs/BENCHMARK-DESIGN.md`). A table or fixture change is
confirmed only on a reporting-grade run for every fixture it touches (D37,
`docs/DECISIONS.md`); below that it is steering, useful for narrowing where
to look but not for a table change. The summary also states, per fixture,
whether its 95 percent Wilson lower bound clears 0.7, the same bar
`benchmark.py` uses.

Usage:
    python3 test/harness/score_routing.py --project ~/consumer --model sonnet --dry-run
    python3 test/harness/score_routing.py --project ~/consumer --model sonnet --record
    python3 test/harness/score_routing.py --project ~/consumer --model sonnet --runs 5 --record
    python3 test/harness/score_routing.py --project ~/consumer --only F08,F15,F17 --json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "test" / "fixtures" / "routing.jsonl"
RESULTS_DIR = REPO_ROOT / "test" / "results"

# tools/ is put on sys.path so `cells` and `route` resolve when this file runs as a script.
sys.path.insert(0, str(REPO_ROOT / "tools"))
from cells import MODELS, EFFORTS  # noqa: E402 (path must be set first)
import route as route_lib  # noqa: E402 (path must be set first); the two-stage classifier's resolver (D39)

BLOCKING_ENV = ("CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")

VERDICT_INSTRUCTION = (
    "\n\nThis is a routing calibration run. Assess and select only; do not spawn a "
    "worker and do not do the task. Assume every artefact the task refers to exists, "
    "even though this project does not contain it. Reply with exactly one line, "
    "nothing else, in the form:\n"
    "assessment: <mechanical|structured|open>, <short|medium|long>, <contained|consequential>; "
    "worker: <worker-name or none>; action: <spawn|clarify>"
)
ASSESS_ONLY_INSTRUCTION = (
    "\n\nThis is a routing calibration run. Assess this task only. Do not select a "
    "worker, do not spawn one, and do not do the task. Assume every artefact the task "
    "refers to exists, even though this project does not contain it. Reply with exactly "
    "one line, nothing else, in the form:\n"
    "assessment: <mechanical|structured|open>, <short|medium|long>, <contained|consequential>"
)
ASSESS_ONLY_RE = re.compile(
    r"assessment:\s*(?P<sensitivity>\w+)\s*,\s*(?P<horizon>\w+)\s*,\s*(?P<blast>\w+)",
    re.IGNORECASE,
)
VERDICT_RE = re.compile(
    r"assessment:\s*(?P<sensitivity>\w+)\s*,\s*(?P<horizon>\w+)\s*,\s*(?P<blast>\w+)\s*;\s*"
    r"worker:\s*(?P<worker>[\w-]+)\s*;\s*action:\s*(?P<action>\w+)",
    re.IGNORECASE,
)

# The two-stage classifier's own instruction (docs/CLASSIFIER-DESIGN.md, D39):
# never mentions a destination or a worker name, asks for the five-field
# schema route.py resolves against, and, at --axes 2, drops horizon
# entirely rather than asking for it and discarding the answer, since the
# point under test is whether the model can be asked less.
TWO_STAGE_INSTRUCTION_3AXES = (
    "\n\nThis is a routing calibration run for the two-stage classifier design "
    "(docs/CLASSIFIER-DESIGN.md). Assess this task only, using all five fields "
    "below. Do not select a worker, do not spawn one, and do not do the task. "
    "Assume every artefact the task refers to exists, even though this project "
    "does not contain it. Reply with exactly one line, nothing else, in the "
    "form:\n"
    "assessment: <mechanical|structured|open>, <short|medium|long>, <contained|consequential>; "
    "self_directed: <true|false>; prior_failure: <none|failed_at_xhigh>"
)
TWO_STAGE_INSTRUCTION_2AXES = (
    "\n\nThis is a routing calibration run for the two-stage classifier design "
    "(docs/CLASSIFIER-DESIGN.md). Assess this task only, using the four fields "
    "below; horizon is deliberately not asked for. Do not select a worker, do "
    "not spawn one, and do not do the task. Assume every artefact the task "
    "refers to exists, even though this project does not contain it. Reply "
    "with exactly one line, nothing else, in the form:\n"
    "assessment: <mechanical|structured|open>, <contained|consequential>; "
    "self_directed: <true|false>; prior_failure: <none|failed_at_xhigh>"
)
TWO_STAGE_RE_3AXES = re.compile(
    r"assessment:\s*(?P<sensitivity>\w+)\s*,\s*(?P<horizon>\w+)\s*,\s*(?P<blast>\w+)\s*;\s*"
    r"self_directed:\s*(?P<self_directed>true|false)\s*;\s*"
    r"prior_failure:\s*(?P<prior_failure>none|failed_at_xhigh)",
    re.IGNORECASE,
)
TWO_STAGE_RE_2AXES = re.compile(
    r"assessment:\s*(?P<sensitivity>\w+)\s*,\s*(?P<blast>\w+)\s*;\s*"
    r"self_directed:\s*(?P<self_directed>true|false)\s*;\s*"
    r"prior_failure:\s*(?P<prior_failure>none|failed_at_xhigh)",
    re.IGNORECASE,
)


def mode_label(classifier: str, axes: int, assess_only: bool) -> str:
    if classifier == "two-stage":
        return f"two-stage, {axes} axes"
    return "assessment only" if assess_only else "assess and select"


def classifier_tag(classifier: str, axes: int) -> str:
    return f"-two-stage-{axes}axis" if classifier == "two-stage" else ""


def select_instruction(classifier: str, axes: int, assess_only: bool) -> str:
    """The one place the run loop and --dry-run agree on which instruction a
    given configuration sends, so the two paths cannot drift apart."""
    if classifier == "two-stage":
        return TWO_STAGE_INSTRUCTION_3AXES if axes == 3 else TWO_STAGE_INSTRUCTION_2AXES
    return ASSESS_ONLY_INSTRUCTION if assess_only else VERDICT_INSTRUCTION


def cell_rank(name: str | None) -> int | None:
    """Cost-order proxy: model-major, then effort. Any opus cell counts as dearer than any sonnet cell."""
    if not name:
        return None
    m = re.fullmatch(r"worker-([a-z]+)-([a-z]+)", name)
    if not m or m.group(1) not in MODELS or m.group(2) not in EFFORTS:
        return None
    return MODELS.index(m.group(1)) * len(EFFORTS) + EFFORTS.index(m.group(2))


def load_fixtures(only: set[str] | None) -> list[dict]:
    rows = [json.loads(l) for l in FIXTURES.read_text(encoding="utf-8").splitlines() if l.strip()]
    return [r for r in rows if not only or r["id"] in only]


def run_orchestrator(project: Path, model: str | None, prompt: str, dry_run: bool,
                      effort: str | None = None) -> tuple[str, float | None, str]:
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    shown = " ".join(cmd[:2]) + " <prompt> " + " ".join(cmd[3:])
    if dry_run:
        return "", None, shown
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project, timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr.strip()[-400:]}")
    data = json.loads(proc.stdout)
    return str(data.get("result", "")), data.get("total_cost_usd"), shown


def score_assess_only(fixture: dict, verdict: str) -> dict:
    """Score an assessment-only verdict: no cell is chosen, so agreement means all three axes.

    Kept separate from score() rather than folded into it because the two
    measure different things and sharing a code path would invite comparing
    numbers that are not comparable.
    """
    m = ASSESS_ONLY_RE.search(verdict)
    expected = fixture.get("assessment")
    exp_text = "/".join(expected[k] for k in ("sensitivity", "horizon", "blast")) if expected else "[no assessment]"
    if not m or not expected:
        return {"id": fixture["id"], "expected": exp_text, "chosen": "[unparsed]" if not m else "[n/a]",
                "agree": False, "axes_agree": None, "direction": "n/a", "parsed": bool(m),
                "raw": verdict.strip()[:200]}
    got = {k: m.group(k).lower() for k in ("sensitivity", "horizon", "blast")}
    axes_agree = sum(expected[k] == got[k] for k in got)
    return {"id": fixture["id"], "expected": exp_text,
            "chosen": "/".join(got[k] for k in ("sensitivity", "horizon", "blast")),
            "agree": axes_agree == 3, "axes_agree": axes_agree, "direction": "n/a",
            "parsed": True, "raw": verdict.strip()[:200]}


def score_two_stage(fixture: dict, verdict: str, axes: int) -> dict:
    """Score a two-stage classifier verdict (docs/CLASSIFIER-DESIGN.md, D39).

    Field agreement is primary and `agree` (all requested fields correct) is
    what feeds the run's overall Wilson interval and grade, per the design:
    cell agreement forgives up to a third of single-field errors
    (docs/PREMISES.md), so a run scored on cell agreement alone would
    overstate how well the model actually classified. Cell agreement is
    still computed, by resolving the model's own field values through
    route.py exactly as a real Controller would, and reported alongside,
    since it is what a consumer ultimately gets routed to.

    At axes=2 the model is never asked for horizon at all (not asked and
    scored as absent; the point under test is asking less), and cell
    resolution goes through route.resolve_two_axis() instead of
    route.resolve(). Per the pre-registration, axes=2 rows are not valid
    evidence for cell agreement, since dropping an axis changes what the
    correct cell is for four fixtures by construction; `cell_agree` is
    still computed here for completeness, and the caller must not cite it
    as confirmation either way.
    """
    pattern = TWO_STAGE_RE_3AXES if axes == 3 else TWO_STAGE_RE_2AXES
    m = pattern.search(verdict)
    expected = fixture.get("assessment")
    exp_bits = [expected["sensitivity"], expected["horizon"], expected["blast"]] if axes == 3 and expected else \
               [expected["sensitivity"], expected["blast"]] if expected else []
    exp_text = ("/".join(exp_bits) + f"; self_directed={fixture.get('self_directed', False)}"
                f"; prior_failure={fixture.get('prior_failure', 'none')}") if expected else "[no assessment]"
    if not m or not expected:
        return {"id": fixture["id"], "expected": exp_text, "chosen": "[unparsed]" if not m else "[n/a]",
                "agree": False, "fields_agree": None, "fields_total": None,
                "cell_agree": None, "cell": None, "parsed": bool(m), "raw": verdict.strip()[:200]}

    got_sensitivity = m.group("sensitivity").lower()
    got_blast = m.group("blast").lower()
    got_horizon = m.group("horizon").lower() if axes == 3 else None
    got_self_directed = m.group("self_directed").lower() == "true"
    got_prior_failure = m.group("prior_failure").lower()

    checks = [expected["sensitivity"] == got_sensitivity, expected["blast"] == got_blast]
    if axes == 3:
        checks.append(expected["horizon"] == got_horizon)
    checks.append(fixture.get("self_directed", False) == got_self_directed)
    checks.append(fixture.get("prior_failure", "none") == got_prior_failure)
    fields_agree = sum(checks)

    try:
        if axes == 3:
            rule = route_lib.resolve(got_sensitivity, got_horizon, got_blast, got_self_directed, got_prior_failure)
        else:
            rule = route_lib.resolve_two_axis(got_sensitivity, got_blast, got_self_directed, got_prior_failure)
        cell = rule["worker"]
    except (route_lib.NoRuleMatches, route_lib.UnknownAxisValue):
        cell = None
    acceptable = {fixture.get("expected_cell")} | set(fixture.get("also_acceptable", []))
    acceptable.discard(None)

    got_bits = [got_sensitivity, got_horizon, got_blast] if axes == 3 else [got_sensitivity, got_blast]
    got_text = "/".join(got_bits) + f"; self_directed={got_self_directed}; prior_failure={got_prior_failure}"
    return {"id": fixture["id"], "expected": exp_text, "chosen": got_text,
            "agree": fields_agree == len(checks), "fields_agree": fields_agree, "fields_total": len(checks),
            "cell_agree": bool(cell) and cell in acceptable, "cell": cell,
            "parsed": True, "raw": verdict.strip()[:200]}


def score(fixture: dict, verdict: str) -> dict:
    m = VERDICT_RE.search(verdict)
    chosen = None
    axes = None
    action = None
    if m:
        chosen = None if m.group("worker").lower() == "none" else m.group("worker").lower()
        axes = {k: m.group(k).lower() for k in ("sensitivity", "horizon", "blast")}
        action = m.group("action").lower()
    expected_action = fixture.get("expected_action", "spawn")
    acceptable = {fixture.get("expected_cell")} | set(fixture.get("also_acceptable", []))
    acceptable.discard(None)
    if expected_action == "clarify":
        agree = action == "clarify"
    else:
        agree = action == "spawn" and chosen in acceptable
    axes_agree = None
    if fixture.get("assessment") and axes:
        axes_agree = sum(fixture["assessment"][k] == axes[k] for k in axes)
    direction = "n/a"
    er, cr = cell_rank(fixture.get("expected_cell")), cell_rank(chosen)
    if er is not None and cr is not None:
        direction = "exact" if cr == er else ("over" if cr > er else "under")
    return {"id": fixture["id"], "expected": fixture.get("expected_cell") or f"[{expected_action}]",
            "chosen": chosen or f"[{action or 'unparsed'}]", "agree": agree, "axes_agree": axes_agree,
            "direction": direction, "parsed": bool(m), "raw": verdict.strip()[:200]}


def bundle_tag(bundle: str) -> str:
    """Short filesystem-safe identifier for a bundle, used in result filenames.

    Result files are keyed by date, model and bundle. Without the bundle, two
    runs of the same model on the same day silently overwrite each other, which
    is exactly what happened on 2026-09-06 when the attractor experiment
    clobbered the run it was meant to be compared against.
    """
    m = re.search(r"[0-9a-f]{7,40}", bundle)
    if m:
        return m.group(0)[:7]
    return re.sub(r"[^A-Za-z0-9]+", "-", bundle).strip("-")[:20] or "unknown"


def only_tag(only: str | None) -> str:
    """Short filesystem-safe suffix for a --only fixture subset, used in result
    filenames.

    Date, model and bundle are not enough to key a filename on their own: a
    targeted `--only F05 --runs 3` run against the same bundle as an earlier
    full-suite `--runs 3` run produces the identical name and silently
    overwrote the earlier run's recorded evidence, twice in one session on
    2026-09-08 (D34, docs/DECISIONS.md).
    """
    if not only:
        return ""
    return "-only-" + "+".join(sorted(set(only.split(","))))


def unique_path(path: Path) -> Path:
    """Return `path` unchanged if nothing is there yet, otherwise the first
    `-2`, `-3`, ... variant that is free.

    Last-resort guard, not a substitute for bundle_tag and only_tag above:
    two runs can still share every one of date, model, bundle and --only (an
    identical rerun later the same day). A script whose entire purpose is
    recording evidence should never silently destroy evidence it already
    recorded (D34).
    """
    if not path.exists():
        return path
    n = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not candidate.exists():
            return candidate
        n += 1


REPORTING_THRESHOLD = 9  # runs; below this a result is steering, not reporting (D37, docs/DECISIONS.md)
WILSON_BAR = 0.7  # the reporting bar's lower-bound requirement, matching benchmark.py


def run_grade(runs: int) -> str:
    """steering below REPORTING_THRESHOLD runs, reporting at or above it (D37)."""
    return "reporting" if runs >= REPORTING_THRESHOLD else "steering"


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95 percent Wilson score interval for a binomial proportion, z=1.96 by default.

    Preferred here over a normal approximation because it stays inside [0, 1]
    and is not degenerate at n=0 or at successes in {0, n}, all of which occur
    with the small run counts this script is used at.
    """
    if n == 0:
        return (0.0, 1.0)
    p_hat = successes / n
    denom = 1 + z * z / n
    centre = (p_hat + z * z / (2 * n)) / denom
    margin = (z / denom) * ((p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def render(rows: list[dict], meta: dict) -> str:
    n = len(rows)
    agreed = sum(r["agree"] for r in rows)
    over = sum(r["direction"] == "over" for r in rows)
    under = sum(r["direction"] == "under" for r in rows)
    unparsed = sum(not r["parsed"] for r in rows)
    grade = run_grade(meta.get("runs", 1))
    run_label = f" (run {meta['run']} of {meta['runs']})" if meta.get("runs", 1) > 1 else ""
    lines = [f"# Routing score, {grade}{run_label} {meta['when']} at {meta['git']}", "",
             f"Orchestrator model: {meta['model'] or 'session default'}. Bundle: {meta['bundle']}. "
             f"Project: `{meta['project']}`. Fixtures reviewed by a human: {meta['reviewed']}. "
             f"Mode: {meta.get('mode', 'assess and select')}"
             + (", so agreement means all three axes correct and no cell was chosen." if meta.get("mode") == "assessment only" else "."), "",
             f"Grade: {grade}" + (f" (fewer than {REPORTING_THRESHOLD} runs; steering only, not a basis for a table or fixture change, D37)"
                                   if grade == "steering" else f" (at or above {REPORTING_THRESHOLD} runs)") + ".", "",
             f"Agreement {agreed}/{n}. Over-provisioned {over}, under-provisioned {under}, unparsed {unparsed}. "
             f"Cost reported by claude: {meta['cost']}.", "",
             "| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |",
             "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['expected']} | {r['chosen']} | {'yes' if r['agree'] else 'no'} | "
                     f"{'' if r['axes_agree'] is None else str(r['axes_agree']) + '/3'} | {r['direction']} | {r['raw'].replace('|', '/')} |")
    lines += ["", "Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4)."]
    return "\n".join(lines) + "\n"


def render_summary(fixture_ids: list[str], per_fixture_agree: dict[str, list[bool]],
                    overall_successes: int, overall_n: int, run_costs: list[float | None], meta: dict) -> str:
    lo, hi = wilson_interval(overall_successes, overall_n)
    grade = run_grade(meta["runs"])
    known = [c for c in run_costs if c is not None]
    cost_line = (f" Mean cost per run: USD {sum(known) / len(known):.4f}; "
                 f"total across {len(known)} costed of {len(run_costs)} runs: USD {sum(known):.4f}."
                 if known else " Cost not reported for any run.")
    clears = {fid: wilson_interval(sum(per_fixture_agree[fid]), len(per_fixture_agree[fid]))[0] >= WILSON_BAR
              for fid in fixture_ids}
    clears_count = sum(clears.values())
    lines = [f"# Routing score summary, {grade}, {meta['runs']} runs, {meta['when']} at {meta['git']}", "",
             f"Orchestrator model: {meta['model'] or 'session default'}. Bundle: {meta['bundle']}. "
             f"Project: `{meta['project']}`. Fixtures reviewed by a human: {meta['reviewed']}. "
             f"Mode: {meta.get('mode', 'assess and select')}"
             + (", so agreement means all three axes correct and no cell was chosen." if meta.get("mode") == "assessment only" else "."), "",
             f"Grade: {grade}" + (f" (fewer than {REPORTING_THRESHOLD} runs; steering only, not a basis for a table or fixture change, D37)"
                                   if grade == "steering" else f" (at or above {REPORTING_THRESHOLD} runs)") + ".", "",
             f"Overall agreement {overall_successes}/{overall_n} "
             f"({overall_successes / overall_n:.1%}, 95% Wilson [{lo:.1%}, {hi:.1%}])." + cost_line, "",
             f"{clears_count} of {len(fixture_ids)} fixtures clear the {WILSON_BAR:.0%} Wilson lower bound"
             + ("." if grade == "reporting" else f", but this is steering grade (fewer than {REPORTING_THRESHOLD} runs): "
                "a fixture clearing the bar here is not yet reporting-grade confirmation."), "",
             "| Fixture | Agreements | Runs | Rate | 95% Wilson interval | Clears 0.7 |",
             "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    for fid in fixture_ids:
        agrees = per_fixture_agree[fid]
        s, n = sum(agrees), len(agrees)
        flo, fhi = wilson_interval(s, n)
        lines.append(f"| {fid} | {s} | {n} | {s / n:.0%} | [{flo:.0%}, {fhi:.0%}] | {'yes' if clears[fid] else 'no'} |")
    lines += ["", "A wide interval on a fixture run only a few times is sample noise, not necessarily "
              "a wrong rule; widen --runs before concluding the rubric is wrong for that cell "
              "(ROUTING.md section 4 still wants three or more disagreements on one starting cell). "
              "\"Clears 0.7\" is the same reporting bar benchmark.py uses; below nine runs it cannot "
              "read yes at all, even for a perfect record (eight of eight gives a lower bound of "
              "67.6 percent, nine of nine is the smallest perfect record that clears 70 percent), "
              "so a \"no\" at steering grade is structural, not evidence the rubric is wrong."]
    return "\n".join(lines) + "\n"


def render_two_stage(rows: list[dict], meta: dict) -> str:
    """Per-run render for --classifier two-stage (D39, docs/CLASSIFIER-DESIGN.md).

    Kept separate from render() rather than adding branches to it: the two
    modes score fundamentally different things (a free-text cell choice
    against field agreement on a schema the model never sees a table for),
    and score_assess_only's own docstring already gives the reason to keep
    that separation, which applies here too.
    """
    n = len(rows)
    agreed = sum(r["agree"] for r in rows)
    cell_agreed = sum(1 for r in rows if r.get("cell_agree"))
    grade = run_grade(meta.get("runs", 1))
    run_label = f" (run {meta['run']} of {meta['runs']})" if meta.get("runs", 1) > 1 else ""
    lines = [f"# Routing score, {grade}, {meta['mode']}{run_label} {meta['when']} at {meta['git']}", "",
             f"Orchestrator model: {meta['model'] or 'session default'}. Bundle: {meta['bundle']}. "
             f"Project: `{meta['project']}`. Fixtures reviewed by a human: {meta['reviewed']}.", "",
             f"Grade: {grade}" + (f" (fewer than {REPORTING_THRESHOLD} runs; steering only, not a basis for a "
                                   f"table or fixture change, D37)" if grade == "steering"
                                   else f" (at or above {REPORTING_THRESHOLD} runs)") + ".", "",
             f"All fields agree {agreed}/{n} (the primary metric, per docs/CLASSIFIER-DESIGN.md: cell agreement "
             f"forgives up to a third of single-field errors, docs/PREMISES.md). Cell agreement (derived via "
             f"tools/route.py) {cell_agreed}/{n}. Cost reported by claude: {meta['cost']}.", "",
             "| Fixture | Expected | Chosen | Fields agree | Cell agree | Raw verdict |",
             "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    for r in rows:
        fields = f"{r['fields_agree']}/{r['fields_total']}" if r.get("fields_total") else ""
        cell = "yes" if r.get("cell_agree") else ("no" if r.get("cell") is not None or r["parsed"] else "")
        lines.append(f"| {r['id']} | {r['expected']} | {r['chosen']} | {fields} | {cell} | {r['raw'].replace('|', '/')} |")
    lines += ["", "Cell agreement is reported for context, not as the grade: a model can misjudge one field "
              "and still be routed correctly by construction (the table is many-to-one), so all-fields "
              "agreement is what this run's grade and Wilson interval are computed from."]
    return "\n".join(lines) + "\n"


def render_two_stage_summary(fixture_ids: list[str], per_fixture_agree: dict[str, list[bool]],
                              per_fixture_cell_agree: dict[str, list[bool]],
                              overall_successes: int, overall_n: int, run_costs: list[float | None], meta: dict) -> str:
    lo, hi = wilson_interval(overall_successes, overall_n)
    grade = run_grade(meta["runs"])
    known = [c for c in run_costs if c is not None]
    cost_line = (f" Mean cost per run: USD {sum(known) / len(known):.4f}; "
                 f"total across {len(known)} costed of {len(run_costs)} runs: USD {sum(known):.4f}."
                 if known else " Cost not reported for any run.")
    cell_successes = sum(sum(v) for v in per_fixture_cell_agree.values())
    cell_n = sum(len(v) for v in per_fixture_cell_agree.values())
    clo, chi = wilson_interval(cell_successes, cell_n) if cell_n else (0.0, 1.0)
    clears = {fid: wilson_interval(sum(per_fixture_agree[fid]), len(per_fixture_agree[fid]))[0] >= WILSON_BAR
              for fid in fixture_ids}
    lines = [f"# Routing score summary, {grade}, {meta['mode']}, {meta['runs']} runs, {meta['when']} at {meta['git']}", "",
             f"Orchestrator model: {meta['model'] or 'session default'}. Bundle: {meta['bundle']}. "
             f"Project: `{meta['project']}`. Fixtures reviewed by a human: {meta['reviewed']}.", "",
             f"Grade: {grade}" + (f" (fewer than {REPORTING_THRESHOLD} runs; steering only, not a basis for a "
                                   f"table or fixture change, D37)" if grade == "steering"
                                   else f" (at or above {REPORTING_THRESHOLD} runs)") + ".", "",
             f"All-fields agreement (primary) {overall_successes}/{overall_n} "
             f"({overall_successes / overall_n:.1%}, 95% Wilson [{lo:.1%}, {hi:.1%}])." + cost_line, "",
             (f"Cell agreement (derived, reported for context) {cell_successes}/{cell_n} "
              f"({cell_successes / cell_n:.1%}, 95% Wilson [{clo:.1%}, {chi:.1%}])."
              if cell_n else "Cell agreement: not computed (no scored rows)."), ""]
    if "2 axes" in meta["mode"]:
        lines += ["Two-axis configuration: cell agreement above is NOT valid evidence either way "
                  "(docs/CLASSIFIER-DESIGN.md's pre-registration fixes this in advance). Dropping horizon "
                  "changes what the correct cell is for four fixtures by construction (F03, F05, F07, F10), "
                  "so a low cell-agreement figure here reflects the axis change, not classifier error.", ""]
    lines += [f"{sum(clears.values())} of {len(fixture_ids)} fixtures clear the {WILSON_BAR:.0%} Wilson lower "
              "bound on all-fields agreement" + ("." if grade == "reporting" else ", but this is steering grade: "
              "not yet reporting-grade confirmation."), "",
              "| Fixture | Fields agree | Runs | Rate | 95% Wilson interval | Cell agree rate |",
              "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    for fid in fixture_ids:
        agrees = per_fixture_agree[fid]
        s, n = sum(agrees), len(agrees)
        flo, fhi = wilson_interval(s, n)
        cell_agrees = per_fixture_cell_agree[fid]
        cell_rate = f"{sum(cell_agrees)}/{len(cell_agrees)}" if cell_agrees else "n/a"
        lines.append(f"| {fid} | {s} | {n} | {s / n:.0%} | [{flo:.0%}, {fhi:.0%}] | {cell_rate} |")
    lines += ["", "A wide interval on a fixture run only a few times is sample noise, not necessarily a wrong "
              "rule; widen --runs before drawing a conclusion. All-fields agreement, not cell agreement, is "
              "what this summary's grade is computed from, per docs/CLASSIFIER-DESIGN.md."]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, type=Path, help="consumer project with the dist/ bundle installed")
    ap.add_argument("--model", choices=("sonnet", "opus", "fable"), help="orchestrator model passed to claude -p")
    ap.add_argument("--effort", choices=EFFORTS, help="orchestrator effort level passed to claude -p's own "
                     "--effort flag (a top-level session's effort, verified 2026-09-11 via `claude -p --help`; "
                     "distinct from a subagent's frontmatter effort, invariant 1)")
    ap.add_argument("--only", help="comma-separated fixture ids")
    ap.add_argument("--runs", type=int, default=1,
                     help="repeat the full fixture pass this many times and aggregate with a Wilson interval (default 1)")
    ap.add_argument("--assess-only", action="store_true",
                     help="ask for the assessment triple only, not a worker; agreement then means all three axes correct. "
                          "Ignored if --classifier two-stage, which is always assessment-only by design")
    ap.add_argument("--classifier", choices=("prose", "two-stage"), default="prose",
                     help="prose (default): today's rubric-and-table prompt. two-stage: schema-forced assessment "
                          "with no destination table in context, resolved by tools/route.py in code (D39, "
                          "docs/CLASSIFIER-DESIGN.md). two-stage requires --project to be a dist-rubric-only/ install")
    ap.add_argument("--axes", type=int, choices=(2, 3), default=3,
                     help="two-stage only: 3 asks for horizon, 2 drops it (the two-axis variant). Ignored otherwise")
    ap.add_argument("--dry-run", action="store_true", help="print the commands; run nothing")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record", action="store_true",
                     help="write test/results/<date>-routing-<model>.md (one file per run, plus a -summary.md when --runs > 1)")
    args = ap.parse_args(argv)

    if args.runs < 1:
        print("refusing to run: --runs must be at least 1", file=sys.stderr)
        return 2
    set_env = [v for v in BLOCKING_ENV if os.environ.get(v) not in (None, "", "0")]
    if set_env:
        print(f"refusing to run: {set_env} set; unset them so frontmatter effort and model apply (CLAUDE.md invariants 1, 3, 4)", file=sys.stderr)
        return 2
    if not args.dry_run and shutil.which("claude") is None:
        print("refusing to run: `claude` not on PATH", file=sys.stderr)
        return 2
    project = args.project.expanduser().resolve()
    if not (project / ".claude" / "agents").is_dir():
        print(f"refusing to run: {project}/.claude/agents missing; install dist/ first (src/README.md)", file=sys.stderr)
        return 2
    version_file = project / ".claude" / "ORCHESTRATOR_VERSION"
    bundle = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown (no .claude/ORCHESTRATOR_VERSION)"
    # Per the pre-registration's own constraint ("the rubric-only bundle and
    # the current bundle must not both be installed in the same project
    # during a run"): refuse rather than silently score a two-stage run
    # against a project that still has the destination table in context,
    # which would invalidate the whole measurement without any visible sign.
    if args.classifier == "two-stage" and not bundle.endswith("-rubric-only"):
        print(f"refusing to run --classifier two-stage: {project}'s installed bundle ({bundle!r}) does not end "
              f"'-rubric-only'. Install dist-rubric-only/ (python3 tools/build_dist.py --rubric-only) into a "
              f"separate project first (docs/CLASSIFIER-DESIGN.md)", file=sys.stderr)
        return 2

    fixtures = load_fixtures(set(args.only.split(",")) if args.only else None)
    if args.assess_only or args.classifier == "two-stage":
        # A fixture with no confirmed assessment (F16, whose correct answer is to
        # clarify) cannot be scored on axes. Drop it rather than counting it as a
        # failure, which is what the first run of this mode did, understating the
        # result by three observations and spending tokens on an unscorable call.
        # Two-stage is assessment-only by design (it never names a worker), so
        # this applies to it exactly as it does to --assess-only.
        dropped = [fx["id"] for fx in fixtures if not fx.get("assessment")]
        fixtures = [fx for fx in fixtures if fx.get("assessment")]
        if dropped and not args.json:
            print(f"assessment-only mode: skipping {dropped}, no confirmed assessment to score against")
    fixture_ids = [fx["id"] for fx in fixtures]

    if args.dry_run:
        for fx in fixtures:
            instruction = select_instruction(args.classifier, args.axes, args.assess_only)
            _, _, shown = run_orchestrator(project, args.model, fx["task"] + instruction, True, args.effort)
            print(f"{fx['id']}: {shown}")
        print(f"--runs {args.runs}: would make {args.runs * len(fixtures)} total calls "
              f"({len(fixtures)} fixtures x {args.runs} runs)")
        return 0

    reviewed = "no" if any("pending human review" in fx.get("assigned_by", "") for fx in fixtures) else "yes"
    git_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip() or "no-git"

    all_runs: list[list[dict]] = []
    run_costs: list[float | None] = []
    for run_idx in range(1, args.runs + 1):
        rows: list[dict] = []
        total_cost = 0.0
        cost_known = True
        if args.runs > 1 and not args.json:
            print(f"=== run {run_idx}/{args.runs} ===")
        for fx in fixtures:
            instruction = select_instruction(args.classifier, args.axes, args.assess_only)
            try:
                verdict, cost, _ = run_orchestrator(project, args.model, fx["task"] + instruction, False, args.effort)
            except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
                verdict, cost = f"[error] {exc}", None
            if cost is None:
                cost_known = False
            else:
                total_cost += float(cost)
            if args.classifier == "two-stage":
                rows.append(score_two_stage(fx, verdict, args.axes))
            elif args.assess_only:
                rows.append(score_assess_only(fx, verdict))
            else:
                rows.append(score(fx, verdict))
            if not args.json:
                r = rows[-1]
                extra = f"{'agree' if r['agree'] else 'DISAGREE'} {r['direction']}" if "direction" in r \
                    else f"{'agree' if r['agree'] else 'DISAGREE'} fields {r['fields_agree']}/{r['fields_total']}" if r.get("fields_total") \
                    else ('agree' if r['agree'] else 'DISAGREE')
                print(f"{r['id']} expected {r['expected']:<20} chosen {r['chosen']:<20} {extra}")
        all_runs.append(rows)
        run_costs.append(total_cost if cost_known else None)

        run_meta = {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "git": git_rev, "model": args.model,
                    "bundle": bundle, "project": str(project), "reviewed": reviewed,
                    "cost": f"USD {total_cost:.4f}" if cost_known else "not reported",
                    "run": run_idx, "runs": args.runs,
                    "mode": mode_label(args.classifier, args.axes, args.assess_only)}
        if not args.json:
            prefix = f"run {run_idx}/{args.runs} " if args.runs > 1 else ""
            print(f"\n{prefix}agreement {sum(r['agree'] for r in rows)}/{len(rows)}; bundle {bundle}; fixtures human-reviewed: {reviewed}")
        if args.record:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            suffix = "" if args.runs == 1 else f"-run{run_idx}-of-{args.runs}"
            out = unique_path(RESULTS_DIR / (f"{dt.datetime.now().strftime('%Y-%m-%d')}-routing-"
                                  f"{args.model or 'default'}-{bundle_tag(bundle)}"
                                  f"{only_tag(args.only)}"
                                  f"{'-assessonly' if args.assess_only else ''}"
                                  f"{classifier_tag(args.classifier, args.axes)}{suffix}.md"))
            render_fn = render_two_stage if args.classifier == "two-stage" else render
            out.write_text(render_fn(rows, run_meta), encoding="utf-8", newline="\n")
            print(f"recorded {out.relative_to(REPO_ROOT)}")

    per_fixture_agree: dict[str, list[bool]] = {fid: [] for fid in fixture_ids}
    per_fixture_cell_agree: dict[str, list[bool]] = {fid: [] for fid in fixture_ids}
    for rows in all_runs:
        for r in rows:
            per_fixture_agree[r["id"]].append(r["agree"])
            if args.classifier == "two-stage":
                per_fixture_cell_agree[r["id"]].append(bool(r.get("cell_agree")))
    overall_successes = sum(sum(v) for v in per_fixture_agree.values())
    overall_n = sum(len(v) for v in per_fixture_agree.values())
    summary_meta = {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "git": git_rev, "model": args.model,
                     "bundle": bundle, "project": str(project), "reviewed": reviewed, "runs": args.runs,
                     "mode": mode_label(args.classifier, args.axes, args.assess_only)}

    if args.json:
        print(json.dumps({
            "meta": summary_meta,
            "runs": [{"run": i + 1, "cost": run_costs[i], "rows": all_runs[i]} for i in range(args.runs)],
            "overall_agreement": {"successes": overall_successes, "n": overall_n,
                                   "wilson_95": wilson_interval(overall_successes, overall_n)},
        }, indent=2))
    elif args.runs > 1:
        lo, hi = wilson_interval(overall_successes, overall_n)
        print(f"\noverall agreement {overall_successes}/{overall_n} "
              f"({overall_successes / overall_n:.1%}, 95% Wilson [{lo:.1%}, {hi:.1%}]) across {args.runs} runs")

    if args.record and args.runs > 1:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = unique_path(RESULTS_DIR / (f"{dt.datetime.now().strftime('%Y-%m-%d')}-routing-"
                              f"{args.model or 'default'}-{bundle_tag(bundle)}"
                              f"{only_tag(args.only)}"
                              f"{'-assessonly' if args.assess_only else ''}"
                              f"{classifier_tag(args.classifier, args.axes)}-summary.md"))
        if args.classifier == "two-stage":
            content = render_two_stage_summary(fixture_ids, per_fixture_agree, per_fixture_cell_agree,
                                                overall_successes, overall_n, run_costs, summary_meta)
        else:
            content = render_summary(fixture_ids, per_fixture_agree, overall_successes, overall_n, run_costs, summary_meta)
        out.write_text(content, encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
