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

# tools/ is put on sys.path so `cells` resolves when this file runs as a script.
sys.path.insert(0, str(REPO_ROOT / "tools"))
from cells import MODELS, EFFORTS  # noqa: E402 (path must be set first)

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


def run_orchestrator(project: Path, model: str | None, prompt: str, dry_run: bool) -> tuple[str, float | None, str]:
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    if model:
        cmd += ["--model", model]
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
    run_label = f" (run {meta['run']} of {meta['runs']})" if meta.get("runs", 1) > 1 else ""
    lines = [f"# Routing score{run_label} {meta['when']} at {meta['git']}", "",
             f"Orchestrator model: {meta['model'] or 'session default'}. Bundle: {meta['bundle']}. "
             f"Project: `{meta['project']}`. Fixtures reviewed by a human: {meta['reviewed']}. "
             f"Mode: {meta.get('mode', 'assess and select')}"
             + (", so agreement means all three axes correct and no cell was chosen." if meta.get("mode") == "assessment only" else "."), "",
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
    known = [c for c in run_costs if c is not None]
    cost_line = (f" Mean cost per run: USD {sum(known) / len(known):.4f}; "
                 f"total across {len(known)} costed of {len(run_costs)} runs: USD {sum(known):.4f}."
                 if known else " Cost not reported for any run.")
    lines = [f"# Routing score summary, {meta['runs']} runs, {meta['when']} at {meta['git']}", "",
             f"Orchestrator model: {meta['model'] or 'session default'}. Bundle: {meta['bundle']}. "
             f"Project: `{meta['project']}`. Fixtures reviewed by a human: {meta['reviewed']}. "
             f"Mode: {meta.get('mode', 'assess and select')}"
             + (", so agreement means all three axes correct and no cell was chosen." if meta.get("mode") == "assessment only" else "."), "",
             f"Overall agreement {overall_successes}/{overall_n} "
             f"({overall_successes / overall_n:.1%}, 95% Wilson [{lo:.1%}, {hi:.1%}])." + cost_line, "",
             "| Fixture | Agreements | Runs | Rate | 95% Wilson interval |",
             "| :--- | :--- | :--- | :--- | :--- |"]
    for fid in fixture_ids:
        agrees = per_fixture_agree[fid]
        s, n = sum(agrees), len(agrees)
        flo, fhi = wilson_interval(s, n)
        lines.append(f"| {fid} | {s} | {n} | {s / n:.0%} | [{flo:.0%}, {fhi:.0%}] |")
    lines += ["", "A wide interval on a fixture run only a few times is sample noise, not necessarily "
              "a wrong rule; widen --runs before concluding the rubric is wrong for that cell "
              "(ROUTING.md section 4 still wants three or more disagreements on one starting cell)."]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, type=Path, help="consumer project with the dist/ bundle installed")
    ap.add_argument("--model", choices=("sonnet", "opus", "fable"), help="orchestrator model passed to claude -p")
    ap.add_argument("--only", help="comma-separated fixture ids")
    ap.add_argument("--runs", type=int, default=1,
                     help="repeat the full fixture pass this many times and aggregate with a Wilson interval (default 1)")
    ap.add_argument("--assess-only", action="store_true",
                     help="ask for the assessment triple only, not a worker; agreement then means all three axes correct")
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

    fixtures = load_fixtures(set(args.only.split(",")) if args.only else None)
    if args.assess_only:
        # A fixture with no confirmed assessment (F16, whose correct answer is to
        # clarify) cannot be scored on axes. Drop it rather than counting it as a
        # failure, which is what the first run of this mode did, understating the
        # result by three observations and spending tokens on an unscorable call.
        dropped = [fx["id"] for fx in fixtures if not fx.get("assessment")]
        fixtures = [fx for fx in fixtures if fx.get("assessment")]
        if dropped and not args.json:
            print(f"assess-only: skipping {dropped}, no confirmed assessment to score against")
    fixture_ids = [fx["id"] for fx in fixtures]

    if args.dry_run:
        for fx in fixtures:
            instruction = ASSESS_ONLY_INSTRUCTION if args.assess_only else VERDICT_INSTRUCTION
            _, _, shown = run_orchestrator(project, args.model, fx["task"] + instruction, True)
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
            instruction = ASSESS_ONLY_INSTRUCTION if args.assess_only else VERDICT_INSTRUCTION
            try:
                verdict, cost, _ = run_orchestrator(project, args.model, fx["task"] + instruction, False)
            except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
                verdict, cost = f"[error] {exc}", None
            if cost is None:
                cost_known = False
            else:
                total_cost += float(cost)
            rows.append(score_assess_only(fx, verdict) if args.assess_only else score(fx, verdict))
            if not args.json:
                r = rows[-1]
                print(f"{r['id']} expected {r['expected']:<20} chosen {r['chosen']:<20} {'agree' if r['agree'] else 'DISAGREE'} {r['direction']}")
        all_runs.append(rows)
        run_costs.append(total_cost if cost_known else None)

        run_meta = {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "git": git_rev, "model": args.model,
                    "bundle": bundle, "project": str(project), "reviewed": reviewed,
                    "cost": f"USD {total_cost:.4f}" if cost_known else "not reported",
                    "run": run_idx, "runs": args.runs,
                    "mode": "assessment only" if args.assess_only else "assess and select"}
        if not args.json:
            prefix = f"run {run_idx}/{args.runs} " if args.runs > 1 else ""
            print(f"\n{prefix}agreement {sum(r['agree'] for r in rows)}/{len(rows)}; bundle {bundle}; fixtures human-reviewed: {reviewed}")
        if args.record:
            RESULTS_DIR.mkdir(parents=True, exist_ok=True)
            suffix = "" if args.runs == 1 else f"-run{run_idx}-of-{args.runs}"
            out = unique_path(RESULTS_DIR / (f"{dt.datetime.now().strftime('%Y-%m-%d')}-routing-"
                                  f"{args.model or 'default'}-{bundle_tag(bundle)}"
                                  f"{only_tag(args.only)}"
                                  f"{'-assessonly' if args.assess_only else ''}{suffix}.md"))
            out.write_text(render(rows, run_meta), encoding="utf-8", newline="\n")
            print(f"recorded {out.relative_to(REPO_ROOT)}")

    per_fixture_agree: dict[str, list[bool]] = {fid: [] for fid in fixture_ids}
    for rows in all_runs:
        for r in rows:
            per_fixture_agree[r["id"]].append(r["agree"])
    overall_successes = sum(sum(v) for v in per_fixture_agree.values())
    overall_n = sum(len(v) for v in per_fixture_agree.values())
    summary_meta = {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "git": git_rev, "model": args.model,
                     "bundle": bundle, "project": str(project), "reviewed": reviewed, "runs": args.runs,
                     "mode": "assessment only" if args.assess_only else "assess and select"}

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
                              f"{'-assessonly' if args.assess_only else ''}-summary.md"))
        out.write_text(render_summary(fixture_ids, per_fixture_agree, overall_successes, overall_n, run_costs, summary_meta),
                        encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
