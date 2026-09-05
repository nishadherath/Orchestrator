#!/usr/bin/env python3
"""Score routing appropriateness: run each fixture through an orchestrator, compare the cell it picks.

Responsible for: the one signal CLAUDE.md says has no automatic source,
routing appropriateness. For every fixture in test/fixtures/routing.jsonl it
asks a non-interactive orchestrator (`claude -p`) to assess and select but
not spawn, parses the one-line verdict, and scores cell agreement, axis
agreement and provisioning direction. With --record it writes the dogfood
log the charter requires to test/results/.

Deliberately does not: spawn workers (so a run costs one orchestrator turn
per fixture and no worker tokens), install the bundle (do that first from
dist/ into the consumer project), or tune anything.

The one non-obvious thing: this script has not yet been run against a live
install. The `claude -p --output-format json` field names (`result`,
`total_cost_usd`) are taken from the documentation as of 2026-09-05. The
first live run will confirm or correct them; record that in FINDINGS.md.

Usage:
    python3 test/harness/score_routing.py --project ~/consumer --model sonnet --dry-run
    python3 test/harness/score_routing.py --project ~/consumer --model sonnet --record
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
    "worker and do not do the task. Reply with exactly one line, nothing else, in "
    "the form:\n"
    "assessment: <mechanical|structured|open>, <short|medium|long>, <contained|consequential>; "
    "worker: <worker-name or none>; action: <spawn|clarify>"
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


def render(rows: list[dict], meta: dict) -> str:
    n = len(rows)
    agreed = sum(r["agree"] for r in rows)
    over = sum(r["direction"] == "over" for r in rows)
    under = sum(r["direction"] == "under" for r in rows)
    unparsed = sum(not r["parsed"] for r in rows)
    lines = [f"# Routing score {meta['when']} at {meta['git']}", "",
             f"Orchestrator model: {meta['model'] or 'session default'}. Bundle: {meta['bundle']}. "
             f"Project: `{meta['project']}`. Fixtures reviewed by a human: {meta['reviewed']}.", "",
             f"Agreement {agreed}/{n}. Over-provisioned {over}, under-provisioned {under}, unparsed {unparsed}. "
             f"Cost reported by claude: {meta['cost']}.", "",
             "| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |",
             "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['expected']} | {r['chosen']} | {'yes' if r['agree'] else 'no'} | "
                     f"{'' if r['axes_agree'] is None else str(r['axes_agree']) + '/3'} | {r['direction']} | {r['raw'].replace('|', '/')} |")
    lines += ["", "Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4)."]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, type=Path, help="consumer project with the dist/ bundle installed")
    ap.add_argument("--model", choices=("sonnet", "opus", "fable"), help="orchestrator model passed to claude -p")
    ap.add_argument("--only", help="comma-separated fixture ids")
    ap.add_argument("--dry-run", action="store_true", help="print the commands; run nothing")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record", action="store_true", help="write test/results/<date>-routing.md")
    args = ap.parse_args(argv)

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
    rows: list[dict] = []
    total_cost = 0.0
    cost_known = True
    for fx in fixtures:
        try:
            verdict, cost, shown = run_orchestrator(project, args.model, fx["task"] + VERDICT_INSTRUCTION, args.dry_run)
        except (RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
            verdict, cost, shown = f"[error] {exc}", None, ""
        if args.dry_run:
            print(f"{fx['id']}: {shown}")
            continue
        if cost is None:
            cost_known = False
        else:
            total_cost += float(cost)
        rows.append(score(fx, verdict))
        if not args.json:
            r = rows[-1]
            print(f"{r['id']} expected {r['expected']:<20} chosen {r['chosen']:<20} {'agree' if r['agree'] else 'DISAGREE'} {r['direction']}")
    if args.dry_run:
        return 0

    git_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip() or "no-git"
    reviewed = "no" if any("pending human review" in fx.get("assigned_by", "") for fx in fixtures) else "yes"
    meta = {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "git": git_rev, "model": args.model,
            "bundle": bundle, "project": str(project), "reviewed": reviewed,
            "cost": f"USD {total_cost:.4f}" if cost_known else "not reported"}
    if args.json:
        print(json.dumps({"meta": meta, "rows": rows}, indent=2))
    else:
        print(f"\nagreement {sum(r['agree'] for r in rows)}/{len(rows)}; bundle {bundle}; fixtures human-reviewed: {reviewed}")
    if args.record:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULTS_DIR / f"{dt.datetime.now().strftime('%Y-%m-%d')}-routing-{args.model or 'default'}.md"
        out.write_text(render(rows, meta), encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
