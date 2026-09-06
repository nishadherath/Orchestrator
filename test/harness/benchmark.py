#!/usr/bin/env python3
"""Benchmark a task against the cost ladder: find its cheapest passing cell.

Responsible for: docs/BENCHMARK-DESIGN.md's staircase protocol. For each task
under test/fixtures/benchmark/, it seeds the task's starting file tree into a
`bench-<task>/` subdirectory of a consumer project, then climbs the cost
ladder (worker-sonnet-low ... worker-fable-xhigh), asking a cheap "forwarder"
orchestrator (`claude -p`) to spawn exactly the named worker cell on the
task, deterministically grades the result with the task's own `grade.sh`,
and stops at the first cell whose pass rate clears the permissive steering
threshold. With --confirm it then re-runs the candidate and the cell below
it at a stricter, evidence-grade sample size and reports Wilson intervals
for both, per the reporting threshold in docs/BENCHMARK-DESIGN.md.

Deliberately does not: run tasks concurrently (docs/BENCHMARK-DESIGN.md
notes this as future work, at the cost of a more complicated harness), grade
anything but exit codes (a model grading a model is circular here), build
the full six-task set (only whatever task directories exist under
test/fixtures/benchmark/ are run, which for now is the pilot pair T1 and T5,
D14), or sandbox a worker's file writes to its assigned directory: the
handover tells it to stay under `bench-<task>/`, but nothing enforces that,
so a stray edit elsewhere in the project is a real possibility this script
cannot detect or undo.

The one non-obvious thing: whether a spawned worker's cost and tokens roll
up into the parent `claude -p --output-format json` call's total_cost_usd is
unverified (docs/FINDINGS.md); every cost figure this script reports
inherits that assumption, and the pilot is partly how it gets checked.

Usage:
    python3 test/harness/benchmark.py --project ~/consumer --dry-run
    python3 test/harness/benchmark.py --project ~/consumer --pilot --record
    python3 test/harness/benchmark.py --project ~/consumer --tasks T1 --confirm --record
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH_FIXTURES = REPO_ROOT / "test" / "fixtures" / "benchmark"
RESULTS_DIR = REPO_ROOT / "test" / "results"

BLOCKING_ENV = ("CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE", "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")

# The cost ladder, cheapest first, exactly as specified in
# docs/BENCHMARK-DESIGN.md's "Protocol: a staircase, not a grid". Not derived
# from tools/cells.py's MODELS x EFFORTS product: most cells in that product
# (opus-low, fable-medium, sonnet-max, and so on) are not on this ladder.
LADDER = (
    "worker-sonnet-low",
    "worker-sonnet-medium",
    "worker-sonnet-high",
    "worker-sonnet-xhigh",
    "worker-opus-high",
    "worker-opus-xhigh",
    "worker-fable-xhigh",
)

PILOT_TASKS = ("T1", "T5")
FORWARDER_MODEL_DEFAULT = "sonnet"
REPORT_FILE = "BENCHMARK_REPORT.txt"

# claude -p starts in Manual permission mode by default (docs/en/permission-modes),
# which blocks Edit and Bash with nobody present to approve them - confirmed the
# hard way on the first real pilot run, where a spawned worker correctly reported
# it had no write permission rather than silently doing nothing. acceptEdits
# auto-approves file edits in the working directory; the explicit allowedTools
# entry is for the one Bash command a task.md asks a worker to self-check with.
# Whether this propagates from the forwarder session to a worker it spawns via
# the Task tool is not confirmed by documentation alone (docs/FINDINGS.md); the
# first run against this flag is the check. --dangerously-skip-permissions is
# the documented pattern for "run fully unattended inside a container", but its
# own warning restricts it to an isolated container or VM without internet
# access, not a bare machine, so it is opt-in here, never the default.
FORWARDER_PERMISSION_ARGS = ["--permission-mode", "acceptEdits", "--allowedTools", "Bash(python3 *)"]
BYPASS_PERMISSION_ARGS = ["--dangerously-skip-permissions"]

BENCHMARK_INSTRUCTION = (
    "\n\nThis is a benchmark run, not a real request. Spawn exactly one worker "
    "with subagent_type `{cell}`, using the Task tool, and nothing else: do not "
    "do the task yourself, do not spawn any other worker, do not ask a "
    "clarifying question, and do not pass a model parameter when spawning.\n\n"
    "Its working directory for this task is `{workdir}` inside this project; "
    "tell it so as part of the handover, and that every file path in the task "
    "below is relative to that directory.\n\n"
    "Give it this handover task verbatim:\n---\n{task}\n---\n\n"
    "Wait for the worker to finish, then reply with its final report verbatim "
    "and nothing else added."
)


def load_task(task_id: str) -> dict:
    task_dir = BENCH_FIXTURES / task_id
    task_md = task_dir / "task.md"
    repo = task_dir / "repo"
    grade_script = task_dir / "grade.sh"
    if not task_md.is_file():
        raise ValueError(f"{task_md} missing (unknown task id {task_id!r}?)")
    if not repo.is_dir():
        raise ValueError(f"{repo} missing")
    if not grade_script.is_file():
        raise ValueError(f"{grade_script} missing")
    return {
        "id": task_id,
        "dir": task_dir,
        "repo": repo,
        "task_text": task_md.read_text(encoding="utf-8").strip(),
        "grade_script": grade_script,
    }


def discover_tasks(only: list[str] | None) -> list[dict]:
    if only:
        ids = only
    else:
        ids = sorted(p.name for p in BENCH_FIXTURES.iterdir() if p.is_dir() and (p / "task.md").exists())
    return [load_task(task_id) for task_id in ids]


def bundle_tag(bundle: str) -> str:
    """Identical to score_routing.py's helper. Duplicated rather than shared,
    because both scripts are meant to stand alone (see their docstrings)."""
    m = re.search(r"[0-9a-f]{7,40}", bundle)
    if m:
        return m.group(0)[:7]
    return re.sub(r"[^A-Za-z0-9]+", "-", bundle).strip("-")[:20] or "unknown"


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95 percent Wilson score interval; see score_routing.py for the same
    function with the same rationale. Duplicated, not imported, by design."""
    if n == 0:
        return (0.0, 1.0)
    p_hat = successes / n
    denom = 1 + z * z / n
    centre = (p_hat + z * z / (2 * n)) / denom
    margin = (z / denom) * ((p_hat * (1 - p_hat) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def steer_threshold(n: int, fraction: float) -> int:
    """Minimum successes to clear the permissive steering threshold: at n=3,
    fraction=2/3 gives 2, matching docs/BENCHMARK-DESIGN.md's stated '2 of 3'
    exactly. Other n scale the same ratio, rounded up."""
    return math.ceil(n * fraction)


def rmtree_if_exists(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def seed_task(project: Path, task: dict) -> Path:
    """Mirror the task's repo/ into project/bench-<id>/ and commit it, so
    reset_task has a baseline to check out back to. Recreated unconditionally
    on every invocation: cheap, and always correct, unlike a diff-based
    mirror would be."""
    dest = project / f"bench-{task['id']}"
    rel = str(dest.relative_to(project))
    rmtree_if_exists(dest)
    shutil.copytree(task["repo"], dest)
    subprocess.run(["git", "add", "-A", "--", rel], cwd=project, check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet", "--", rel], cwd=project)
    if diff.returncode != 0:
        subprocess.run(
            ["git", "-c", "user.name=benchmark-harness", "-c", "user.email=benchmark-harness@localhost",
             "commit", "-m", f"benchmark: seed {task['id']}", "--", rel],
            cwd=project, check=True,
        )
    return dest


def reset_task(project: Path, dest: Path) -> None:
    """Discard everything a worker did to dest and assert the discard worked,
    per docs/BENCHMARK-DESIGN.md's build specification ("rather than trusting
    it"). Uses `-fdx`, not the spec's literal `-fd`: `-x` also removes files
    the consumer project's own .gitignore would otherwise hide from `clean`,
    such as __pycache__, which `-fd` alone can leave behind uncleaned."""
    rel = str(dest.relative_to(project))
    subprocess.run(["git", "checkout", "--", rel], cwd=project, check=True)
    subprocess.run(["git", "clean", "-fdx", "--", rel], cwd=project, check=True)
    status = subprocess.run(["git", "status", "--porcelain", "--", rel],
                             cwd=project, capture_output=True, text=True, check=True)
    if status.stdout.strip():
        raise RuntimeError(f"reset did not clean {rel}: {status.stdout.strip()}")


def run_cell(project: Path, cell: str, task_text: str, workdir_rel: str,
             forwarder_model: str, permission_args: list[str], timeout: float) -> tuple[str, float | None, float, dict]:
    """Ask a cheap forwarder orchestrator to spawn exactly one worker of the
    given cell on the task, scoped to workdir_rel. Returns (report text, cost
    in USD or None, wall-clock seconds, raw JSON extras worth recording)."""
    prompt = BENCHMARK_INSTRUCTION.format(cell=cell, workdir=workdir_rel, task=task_text)
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", forwarder_model, *permission_args]
    start = time.monotonic()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project, timeout=timeout)
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr.strip()[-400:]}")
    data = json.loads(proc.stdout)
    extras = {k: data.get(k) for k in ("usage", "duration_ms", "num_turns") if k in data}
    return str(data.get("result", "")), data.get("total_cost_usd"), elapsed, extras


def grade(dest: Path, task: dict, report_text: str | None, timeout: float) -> tuple[bool, str]:
    if report_text is not None:
        (dest / REPORT_FILE).write_text(report_text, encoding="utf-8")
    # .as_posix(), not str(): on Windows, a native "C:\...\grade.sh" path handed
    # to git-bash as a bare argument loses its lone backslashes (MSYS's argv
    # translation treats them as escape introducers), so bash sees a path with no
    # separators at all and fails to find the file. Forward slashes survive that
    # translation on both platforms.
    proc = subprocess.run(["bash", task["grade_script"].as_posix()], cwd=dest,
                           capture_output=True, text=True, timeout=timeout)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def run_one(project: Path, task: dict, dest: Path, cell: str, forwarder_model: str,
            permission_args: list[str], timeout: float, grade_timeout: float) -> dict:
    """One reset-run-grade cycle. Never raises: a worker or grader failure is
    a data point (a fail), not an error, though a harness-level error (the
    forwarder call itself failing) is recorded distinctly so it is not
    mistaken for the worker having failed the task."""
    reset_task(project, dest)
    workdir_rel = dest.relative_to(project).as_posix()
    error = None
    report_text, cost, elapsed, extras = None, None, None, {}
    try:
        report_text, cost, elapsed, extras = run_cell(project, cell, task["task_text"], workdir_rel,
                                                        forwarder_model, permission_args, timeout)
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        error = str(exc)
    if error is not None:
        return {"cell": cell, "passed": False, "cost": None, "wall_clock": None, "error": error,
                "grade_output": "[not graded: forwarder call failed]", "extras": {}, "report_text": None}
    try:
        passed, grade_output = grade(dest, task, report_text, grade_timeout)
    except subprocess.TimeoutExpired:
        passed, grade_output = False, "[grader timed out]"
    return {"cell": cell, "passed": passed, "cost": cost, "wall_clock": elapsed, "error": None,
            "grade_output": "" if passed else grade_output, "extras": extras,
            "report_text": None if passed else report_text}


def search(project: Path, task: dict, dest: Path, r_search: int, fraction: float,
           forwarder_model: str, permission_args: list[str], timeout: float, grade_timeout: float,
           on_run=None) -> tuple[str | None, list[dict]]:
    """Climb LADDER, R_search runs per cell, stop at the first cell whose
    pass rate clears the permissive steering threshold. Returns (candidate
    cell, or None if the ladder was exhausted; per-cell log)."""
    threshold = steer_threshold(r_search, fraction)
    log = []
    for cell in LADDER:
        runs = []
        for _ in range(r_search):
            record = run_one(project, task, dest, cell, forwarder_model, permission_args, timeout, grade_timeout)
            runs.append(record)
            if on_run:
                on_run(cell, record)
        successes = sum(r["passed"] for r in runs)
        met = successes >= threshold
        log.append({"cell": cell, "successes": successes, "n": r_search, "met": met, "runs": runs})
        if met:
            return cell, log
    return None, log


def confirm(project: Path, task: dict, dest: Path, candidate: str, r_confirm: int,
            forwarder_model: str, permission_args: list[str], timeout: float, grade_timeout: float,
            on_run=None) -> dict:
    """Re-run the candidate and the cell below it at R_confirm each. The
    frontier claim requires the candidate's Wilson lower bound above 0.7 and
    the cell below to fail that same bar (docs/BENCHMARK-DESIGN.md)."""
    idx = LADDER.index(candidate)
    cells = [candidate] if idx == 0 else [candidate, LADDER[idx - 1]]
    results = {}
    for cell in cells:
        runs = []
        for _ in range(r_confirm):
            record = run_one(project, task, dest, cell, forwarder_model, permission_args, timeout, grade_timeout)
            runs.append(record)
            if on_run:
                on_run(cell, record)
        successes = sum(r["passed"] for r in runs)
        lo, hi = wilson_interval(successes, r_confirm)
        results[cell] = {"successes": successes, "n": r_confirm, "lo": lo, "hi": hi, "runs": runs}
    candidate_clears = results[candidate]["lo"] > 0.7
    below_fails = idx == 0 or results[LADDER[idx - 1]]["lo"] <= 0.7
    frontier_confirmed = candidate_clears and below_fails
    return {"cells": results, "candidate": candidate, "below": None if idx == 0 else LADDER[idx - 1],
            "frontier_confirmed": frontier_confirmed, "no_lower_rung": idx == 0}


def money(cost: float | None) -> str:
    return f"USD {cost:.4f}" if cost is not None else "not reported"


def render(meta: dict, task_reports: list[dict]) -> str:
    confirm_line = (f" R_confirm={meta['r_confirm']}, reporting threshold: 95% Wilson lower bound above "
                     "0.7, and the cell below must fail the same bar." if meta.get("confirm") else " No confirmation phase.")
    lines = [f"# Benchmark run, {meta['mode']}, {meta['when']} at {meta['git']}", "",
             f"Bundle: {meta['bundle']}. Project: `{meta['project']}`. "
             f"Forwarder model: {meta['forwarder_model']}. Permission mode: {meta['permission_mode']}. "
             f"Ladder: {' -> '.join(LADDER)}.", "",
             f"R_search={meta['r_search']}, steer threshold={steer_threshold(meta['r_search'], meta['steer_fraction'])} "
             f"of {meta['r_search']} (permissive; ceil({meta['steer_fraction']:.3f} x n); never cited as evidence, "
             f"docs/BENCHMARK-DESIGN.md)." + confirm_line, "",
             "Cost figures assume a spawned worker's cost rolls up into the forwarder's reported "
             "`total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it "
             "gets checked.", ""]
    for tr in task_reports:
        task = tr["task"]
        lines += [f"## Task {task['id']}", "", "### Search (steering only, not evidence)", "",
                  "| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |",
                  "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
        for entry in tr["search_log"]:
            costs = [r["cost"] for r in entry["runs"] if r["cost"] is not None]
            clocks = [r["wall_clock"] for r in entry["runs"] if r["wall_clock"] is not None]
            mean_cost = f"USD {sum(costs) / len(costs):.4f}" if costs else "not reported"
            mean_clock = f"{sum(clocks) / len(clocks):.1f}" if clocks else "n/a"
            lines.append(f"| {entry['cell']} | {entry['successes']} | {entry['n']} | "
                         f"{entry['successes'] / entry['n']:.0%} | {'yes' if entry['met'] else 'no'} | "
                         f"{mean_cost} | {mean_clock} |")
        if tr["candidate"]:
            lines += ["", f"Candidate frontier: `{tr['candidate']}`."]
        else:
            lines += ["", "No cell cleared the steering threshold; ladder exhausted."]
        if tr.get("confirmation"):
            c = tr["confirmation"]
            lines += ["", "### Confirmation (reporting threshold)", "",
                      "| Cell | Passes | Runs | Rate | 95% Wilson interval | Clears 0.7 lower bound |",
                      "| :--- | :--- | :--- | :--- | :--- | :--- |"]
            for cell, res in c["cells"].items():
                lines.append(f"| {cell} | {res['successes']} | {res['n']} | "
                             f"{res['successes'] / res['n']:.0%} | [{res['lo']:.1%}, {res['hi']:.1%}] | "
                             f"{'yes' if res['lo'] > 0.7 else 'no'} |")
            if c["no_lower_rung"]:
                lines += ["", f"`{c['candidate']}` is the cheapest cell on the ladder; there is no cell "
                              "below to confirm exclusivity against."]
            lines += ["", f"Frontier confirmed: {'yes' if c['frontier_confirmed'] else 'no'}."]
        lines += ["", "### Per-run detail", "", "| Cell | Run | Pass | Cost | Wall-clock (s) | Notes |",
                  "| :--- | :--- | :--- | :--- | :--- | :--- |"]
        run_no_by_cell: dict[str, int] = {}
        all_runs = [(e["cell"], r) for e in tr["search_log"] for r in e["runs"]]
        if tr.get("confirmation"):
            for cell, res in tr["confirmation"]["cells"].items():
                all_runs += [(cell, r) for r in res["runs"]]
        for cell, r in all_runs:
            run_no_by_cell[cell] = run_no_by_cell.get(cell, 0) + 1
            note = r["error"] or ("" if r["passed"] else r["grade_output"][:200].replace("|", "/").replace("\n", " "))
            wall_clock_str = "" if r["wall_clock"] is None else f"{r['wall_clock']:.1f}"
            lines.append(f"| {cell} | {run_no_by_cell[cell]} | {'yes' if r['passed'] else 'no'} | "
                         f"{money(r['cost'])} | {wall_clock_str} | {note} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, type=Path,
                     help="consumer project with the dist/ bundle installed, and a git repository")
    ap.add_argument("--tasks", help="comma-separated task ids (default: every task directory under test/fixtures/benchmark/)")
    ap.add_argument("--pilot", action="store_true",
                     help="pilot mode (D14): restricts tasks to T1,T5, defaults --r-search to 5, and refuses --confirm")
    ap.add_argument("--confirm", action="store_true", help="run the confirmation phase after the search phase")
    ap.add_argument("--r-search", type=int, default=None, help="runs per cell while searching (default 3, or 5 with --pilot)")
    ap.add_argument("--r-confirm", type=int, default=8, help="runs per cell while confirming (default 8)")
    ap.add_argument("--steer-fraction", type=float, default=2 / 3,
                     help="fraction of R_search runs that must pass to stop climbing (default 2/3, the stated '2 of 3' at n=3)")
    ap.add_argument("--forwarder-model", default=FORWARDER_MODEL_DEFAULT, choices=("sonnet", "opus", "fable"),
                     help=f"model for the trivial forwarding orchestrator, not the worker cell under test (default {FORWARDER_MODEL_DEFAULT})")
    ap.add_argument("--unattended-bypass", action="store_true",
                     help="use --dangerously-skip-permissions instead of the narrower acceptEdits default. "
                          "Anthropic's own docs restrict this to an isolated container or VM without internet "
                          "access; do not pass this against a bare machine")
    ap.add_argument("--timeout", type=float, default=1200, help="seconds allowed per claude -p call (default 1200)")
    ap.add_argument("--grade-timeout", type=float, default=60, help="seconds allowed per grade.sh call (default 60)")
    ap.add_argument("--dry-run", action="store_true", help="print what would run; touch nothing")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--record", action="store_true", help="write test/results/<date>-benchmark-<bundle tag>*.md")
    args = ap.parse_args(argv)

    if args.pilot:
        if args.tasks and set(args.tasks.split(",")) != set(PILOT_TASKS):
            print(f"refusing to run: --pilot restricts tasks to {PILOT_TASKS}, got --tasks {args.tasks}", file=sys.stderr)
            return 2
        if args.confirm:
            print("refusing to run: --pilot has no confirmation phase (D14); drop --pilot or --confirm", file=sys.stderr)
            return 2
        task_ids = list(PILOT_TASKS)
        r_search = args.r_search if args.r_search is not None else 5
    else:
        task_ids = args.tasks.split(",") if args.tasks else None
        r_search = args.r_search if args.r_search is not None else 3

    if r_search < 1 or args.r_confirm < 1:
        print("refusing to run: --r-search and --r-confirm must be at least 1", file=sys.stderr)
        return 2
    set_env = [v for v in BLOCKING_ENV if os.environ.get(v) not in (None, "", "0")]
    if set_env:
        print(f"refusing to run: {set_env} set; unset them so frontmatter effort and model apply (CLAUDE.md invariants 1, 3, 4)", file=sys.stderr)
        return 2
    if not args.dry_run and shutil.which("claude") is None:
        print("refusing to run: `claude` not on PATH", file=sys.stderr)
        return 2
    if not args.dry_run and shutil.which("bash") is None:
        print("refusing to run: `bash` not on PATH (grade.sh needs it)", file=sys.stderr)
        return 2
    project = args.project.expanduser().resolve()
    if not (project / ".claude" / "agents").is_dir():
        print(f"refusing to run: {project}/.claude/agents missing; install dist/ first (src/README.md)", file=sys.stderr)
        return 2
    if not args.dry_run:
        is_repo = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project, capture_output=True, text=True)
        if is_repo.returncode != 0 or is_repo.stdout.strip() != "true":
            print(f"refusing to run: {project} is not a git repository; benchmark.py resets tasks with git checkout/clean", file=sys.stderr)
            return 2
    version_file = project / ".claude" / "ORCHESTRATOR_VERSION"
    bundle = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown (no .claude/ORCHESTRATOR_VERSION)"

    try:
        tasks = discover_tasks(task_ids)
    except ValueError as exc:
        print(f"refusing to run: {exc}", file=sys.stderr)
        return 2
    if not tasks:
        print("refusing to run: no task directories found", file=sys.stderr)
        return 2

    permission_args = BYPASS_PERMISSION_ARGS if args.unattended_bypass else FORWARDER_PERMISSION_ARGS

    if args.dry_run:
        for task in tasks:
            preview = BENCHMARK_INSTRUCTION.format(cell=LADDER[0], workdir=f"bench-{task['id']}", task=task["task_text"])
            shown = " ".join(["claude", "-p", "<prompt>", "--output-format", "json",
                               "--model", args.forwarder_model, *permission_args])
            print(f"{task['id']}: {shown}")
            print(f"  first prompt would be:\n{preview}\n")
        max_search_calls = len(tasks) * r_search * len(LADDER)
        print(f"up to {max_search_calls} calls if every task exhausts the ladder during search "
              f"({len(tasks)} tasks x {r_search} runs x {len(LADDER)} cells)")
        if args.confirm:
            print(f"plus up to {len(tasks) * args.r_confirm * 2} calls during confirmation "
                  f"({len(tasks)} tasks x {args.r_confirm} runs x up to 2 cells)")
        return 0

    git_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip() or "no-git"
    task_reports = []
    for task in tasks:
        dest = seed_task(project, task)
        if not args.json:
            print(f"=== {task['id']} ===")

        def on_run(cell, record, task_id=task["id"]):
            if not args.json:
                status = "pass" if record["passed"] else ("ERROR" if record["error"] else "FAIL")
                print(f"{task_id} {cell}: {status}")
                if not record["passed"]:
                    if record["error"]:
                        print(f"  forwarder error: {record['error'][:500]}")
                    else:
                        print(f"  grader said: {record['grade_output'][:500]}")
                        if record.get("report_text"):
                            print(f"  worker's relayed report: {record['report_text'][:500]}")

        candidate, search_log = search(project, task, dest, r_search, args.steer_fraction,
                                        args.forwarder_model, permission_args, args.timeout, args.grade_timeout, on_run)
        report = {"task": task, "search_log": search_log, "candidate": candidate}
        if args.confirm and candidate:
            report["confirmation"] = confirm(project, task, dest, candidate, args.r_confirm,
                                              args.forwarder_model, permission_args, args.timeout, args.grade_timeout, on_run)
        task_reports.append(report)

    meta = {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "git": git_rev, "bundle": bundle,
            "project": str(project), "forwarder_model": args.forwarder_model, "r_search": r_search,
            "r_confirm": args.r_confirm, "steer_fraction": args.steer_fraction, "confirm": args.confirm,
            "mode": "pilot" if args.pilot else "full",
            "permission_mode": "bypassPermissions" if args.unattended_bypass else "acceptEdits+allowedTools"}

    if args.json:
        def strip_task(tr):
            out = dict(tr)
            out["task"] = tr["task"]["id"]
            return out
        print(json.dumps({"meta": meta, "tasks": [strip_task(tr) for tr in task_reports]}, indent=2, default=str))
    else:
        for tr in task_reports:
            status = tr["candidate"] or "none (ladder exhausted)"
            print(f"{tr['task']['id']}: candidate frontier {status}")

    if args.record:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        suffix = "-pilot" if args.pilot else ""
        out = RESULTS_DIR / (f"{dt.datetime.now().strftime('%Y-%m-%d')}-benchmark-"
                              f"{bundle_tag(bundle)}{suffix}.md")
        out.write_text(render(meta, task_reports), encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
