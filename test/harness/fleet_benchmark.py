#!/usr/bin/env python3
"""Fleet versus baseline: run the Controller on the benchmark tasks and grade
the result with each task's own grader (docs/PLAN.md Stage 11, D55).

    python3 test/harness/fleet_benchmark.py --project <consumer> --tasks T10 --runs 1 --record
    python3 test/harness/fleet_benchmark.py --project <consumer> --tasks T10,T9,T11 --runs 9 --record
    python3 test/harness/fleet_benchmark.py --project <consumer> --tasks T10 --dry-run

Responsible for: one reset-controller-instantiate-grade cycle per run. The
Controller (`tools/system_controller.py`, quick mode) reads the task's
working copy and writes `runs/fleet-<task>-<n>/REPORT.md`; that report,
followed by the task's own handover, goes to one `worker-sonnet-low` through
the same forwarder path `benchmark.py` used for B0, which edits the working
copy; `grade.sh` then grades the tree exactly as it graded B0. The two arms
therefore differ in one thing only: the reasoning that precedes the floor
worker's edit (the B0 brief, or the Controller's report). Every completed
run is checkpointed the moment it finishes, and the checkpoint identity
includes a hash of the Controller's own source and prompt inputs, so a code
change between invocations is refused as a different measurement rather
than blended into one reported rate.

Deliberately does not: climb the cost ladder (the fleet's cells are
`ROLES.md`'s configured priors, not a search), tune anything on a result
(the instantiation instruction below is fixed and hashed into the
checkpoint identity before the first run), or compare against B0 here (the
comparison is the decision entry's job, from this file's numbers and the
Stage 9.8 results files).

The one non-obvious thing: quick mode's own output is paper (SYSTEM.md
section 8, "paper falsification only"), and the graders are behavioural, so
without the instantiation call nothing the fleet produces can be graded at
all. That call is the cheapest cell on the ladder on purpose: it is the same
cell B0 ran on, so any pass-rate difference is attributable to the report
it was handed, not to the cell that applied it.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HARNESS_DIR.parents[1]
sys.path.insert(0, str(HARNESS_DIR))
sys.path.insert(0, str(REPO_ROOT / "tools"))
import benchmark  # noqa: E402
import claudep  # noqa: E402
import system_controller  # noqa: E402

CHECKPOINT_FILENAME = ".fleet-checkpoint.jsonl"
INSTANTIATE_CELL = "worker-sonnet-low"
# --runs and --tasks are deliberately absent: extending one recorded pilot
# run to nine, or adding a task, is the same measurement continued (runs are
# keyed by task in the checkpoint already), exactly as benchmark.py treats
# --confirm. A fixture edit is still caught per task by its fingerprint.
CHECKPOINT_IDENTITY_FIELDS = ("forwarder_model", "permission_mode", "bundle",
                              "instantiate_cell", "budget_usd", "controller_sha", "instruction_sha")

# The Controller sees the task statement with one preface: where the code
# is. Paths in the report it writes are therefore relative to the project
# root, which is also how the B0 workers wrote theirs.
PROBLEM_PREFACE = (
    "The repository for this problem is the directory `{workdir}/` inside the current working "
    "directory; every path in the problem statement below is relative to it. Read files there and "
    "run nothing that modifies them.\n\n---\n\n"
)

# Fixed before the first run and hashed into the checkpoint identity. This is
# the whole of what the instantiating cell is told beyond the report and the
# task's own handover.
INSTANTIATE_INSTRUCTION = (
    "The report above was produced by a separate reasoning pass over this task and its repository; "
    "its premise ledger is the evidence for its answer. Your job is to apply that answer: make the "
    "changes it describes so the task's acceptance criteria below are met, and write any artefact the "
    "task asks for. Where the answer departs from a constraint the task states, the ledger records the "
    "measured reason; act on the answer and cite that reason in your report. There is no owner or "
    "reviewer to consult in this run: where the answer conditions a change on someone's approval, the "
    "ledger's measured reason stands in for it. Do not redo the analysis. If the answer cannot be "
    "applied as written, say exactly why in your report and stop."
)

# Everything that determines what the Controller does with a task, hashed so
# a change to any of it invalidates a checkpoint (the fixture fingerprint
# covers the task side; this covers the fleet side).
CONTROLLER_INPUTS = (
    REPO_ROOT / "tools" / "system_controller.py",
    REPO_ROOT / "tools" / "system_prompts.py",
    REPO_ROOT / "tools" / "claudep.py",
    REPO_ROOT / "src" / "System" / "ROLES.md",
    REPO_ROOT / "src" / "System" / "TECHNIQUES.md",
    REPO_ROOT / "src" / "System" / "schemas",
)


def controller_sha() -> str:
    h = hashlib.sha256()
    for path in CONTROLLER_INPUTS:
        files = sorted(path.rglob("*.json")) if path.is_dir() else [path]
        for f in files:
            h.update(f.relative_to(REPO_ROOT).as_posix().encode("utf-8"))
            h.update(f.read_bytes())
    return h.hexdigest()[:16]


def instruction_sha() -> str:
    return hashlib.sha256((PROBLEM_PREFACE + INSTANTIATE_INSTRUCTION).encode("utf-8")).hexdigest()[:16]


def role_edits(project: Path, dest: Path) -> str:
    """Anything a Controller role changed under the task's working copy
    before instantiation. Expected empty (six toy runs left probe-T10/ byte
    identical to its fixture); recorded rather than reset, because a run
    whose edits came from a role rather than the instantiating cell is a
    different result and must be visible as one."""
    rel = str(dest.relative_to(project))
    out = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=project,
                         capture_output=True, text=True, check=True).stdout
    # A Verifier's one tool call may run the tests, which writes
    # __pycache__/; that is a byte-code cache, not an edit (seen live, D56).
    return "\n".join(line for line in out.splitlines() if "__pycache__" not in line).strip()


def run_one(project: Path, task: dict, dest: Path, run_index: int, forwarder_model: str,
            permission_args: list[str], budget_usd: float, controller_timeout: float,
            timeout: float, grade_timeout: float) -> dict:
    """One reset-controller-instantiate-grade cycle. Never raises: a
    Controller crash, a forwarder failure and a grader timeout are each a
    recorded fail with the reason, distinguishable from a graded fail."""
    benchmark.reset_task(project, dest)
    workdir_rel = dest.relative_to(project).as_posix()
    problem_text = PROBLEM_PREFACE.format(workdir=workdir_rel) + task["task_text"]
    record: dict = {"run": run_index, "passed": False, "error": None, "grade_output": "",
                    "controller": None, "instantiate": None, "total_cost": None, "report_text": None}
    started = dt.datetime.now()
    try:
        result = system_controller.run_quick(
            problem_text, project, budget_usd, controller_timeout,
            lambda remaining: system_controller.LiveRoleRunner(project, remaining),
            run_id=f"fleet-{task['id']}-{run_index}")
    except Exception as exc:  # a data point, not an abort: the batch continues
        record["error"] = f"controller: {type(exc).__name__}: {exc}"[:1000]
        record["grade_output"] = "[not graded: controller failed]"
        return record
    controller_s = (dt.datetime.now() - started).total_seconds()
    record["controller"] = {"outcome": result.outcome, "cost": result.total_cost_usd, "calls": result.calls,
                            "technique": result.record.get("technique"), "candidate_id": result.record.get("candidate_id"),
                            "unverified_load_bearing": len(result.record.get("unverified_load_bearing", [])),
                            "run_dir": result.run_dir.name, "wall_clock": round(controller_s, 1),
                            "role_edits": role_edits(project, dest)}
    report_md = (result.run_dir / "REPORT.md").read_text(encoding="utf-8")
    handover = report_md + "\n\n---\n\n" + INSTANTIATE_INSTRUCTION + "\n\n---\n\n" + task["task_text"]
    try:
        report_text, cost, elapsed, extras = benchmark.run_cell(
            project, INSTANTIATE_CELL, handover, workdir_rel, forwarder_model, permission_args, timeout)
    except RuntimeError as exc:
        # claudep.call_claude wraps TimeoutExpired and JSONDecodeError
        # as RuntimeError itself (audit A17, docs/AUDIT-2026-09-16.md).
        record["error"] = f"instantiate: {exc}"[:1000]
        record["grade_output"] = "[not graded: forwarder call failed]"
        return record
    record["instantiate"] = {"cost": cost, "wall_clock": elapsed, "extras": extras}
    record["total_cost"] = (result.total_cost_usd + cost) if cost is not None else None
    try:
        passed, grade_output = benchmark.grade(dest, task, report_text, grade_timeout)
    except subprocess.TimeoutExpired:
        passed, grade_output = False, "[grader timed out]"
    record["passed"] = passed
    record["grade_output"] = "" if passed else grade_output
    record["report_text"] = None if passed else report_text
    return record


def summarise(runs: list[dict]) -> dict:
    n = len(runs)
    passes = sum(r["passed"] for r in runs)
    lo, hi = claudep.wilson_interval(passes, n) if n else (0.0, 0.0)
    costs = [r["total_cost"] for r in runs if r["total_cost"] is not None]
    controller_costs = [r["controller"]["cost"] for r in runs if r["controller"]]
    total = sum(costs)
    return {"n": n, "passes": passes, "lo": lo, "hi": hi, "clears": n > 0 and lo > 0.7,
            "mean_cost": total / len(costs) if costs else None,
            "mean_controller_cost": sum(controller_costs) / len(controller_costs) if controller_costs else None,
            "cost_per_solved": total / passes if passes else None, "total_cost": total,
            "controller_errors": sum(1 for r in runs if r["error"] and r["error"].startswith("controller")),
            "role_edit_runs": sum(1 for r in runs if r["controller"] and r["controller"]["role_edits"])}


def render(meta: dict, task_reports: list[dict]) -> str:
    lines = [f"# Fleet run, {meta['when']} at {meta['git']}", "",
             f"Bundle: {meta['bundle']}. Project: `{meta['project']}`. Forwarder model: {meta['forwarder_model']}. "
             f"Permission mode: {meta['permission_mode']}. Controller inputs sha256 {meta['controller_sha']}; "
             f"instruction sha256 {meta['instruction_sha']}. Controller budget USD {meta['budget_usd']} per run; "
             f"instantiation cell `{INSTANTIATE_CELL}` via the benchmark.py forwarder path. Runs per task: {meta['runs']}.", "",
             "Each run: reset the working copy; the Controller (quick mode) reads it and writes REPORT.md; the report "
             "plus the task handover goes to the instantiation cell, which edits the working copy; grade.sh grades "
             "the tree. Pass rate is reported at the same bar as B0 (95% Wilson lower bound above 0.7 over nine "
             "runs). Cost per run is the Controller's own accounting plus the instantiation call's reported "
             "total_cost_usd, which inherits benchmark.py's roll-up assumption (docs/FINDINGS.md).", ""]
    for tr in task_reports:
        s = tr["summary"]
        lines += [f"## Task {tr['task']['id']}", "",
                  "| Passes | Runs | Rate | 95% Wilson interval | Clears 0.7 lower bound | Mean cost per run | "
                  "Mean Controller cost | Cost per solved task |",
                  "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
                  f"| {s['passes']} | {s['n']} | {s['passes'] / s['n'] * 100:.0f}% | [{s['lo'] * 100:.1f}%, {s['hi'] * 100:.1f}%] | "
                  f"{'yes' if s['clears'] else 'no'} | {benchmark.money(s['mean_cost'])} | "
                  f"{benchmark.money(s['mean_controller_cost'])} | {benchmark.money(s['cost_per_solved'])} |", ""]
        if s["controller_errors"] or s["role_edit_runs"]:
            lines += [f"Controller failures: {s['controller_errors']}. Runs where a role edited the working copy "
                      f"before instantiation: {s['role_edit_runs']}.", ""]
        lines += ["### Per-run detail", "",
                  "| Run | Pass | Controller outcome | Technique | Calls | Controller cost | Instantiate cost | "
                  "Total | Controller s | Instantiate s | Run dir | Notes |",
                  "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
        for r in tr["runs"]:
            c, i = r["controller"] or {}, r["instantiate"] or {}
            note = ""
            if r["error"]:
                note = "error: " + r["error"][:300]
            elif not r["passed"]:
                note = "grader: " + r["grade_output"][:300]
                if r.get("report_text"):
                    note += " || worker: " + r["report_text"][:300]
            if c.get("role_edits"):
                note = ("ROLE EDITS before instantiation: " + c["role_edits"][:200] + " | " + note)
            note = note.replace("|", "/").replace("\n", " ")
            lines.append(f"| {r['run']} | {'yes' if r['passed'] else 'no'} | {c.get('outcome', '')} | {c.get('technique', '')} | "
                         f"{c.get('calls', '')} | {benchmark.money(c.get('cost'))} | {benchmark.money(i.get('cost'))} | "
                         f"{benchmark.money(r['total_cost'])} | {c.get('wall_clock', '')} | "
                         f"{i.get('wall_clock', '') and round(i['wall_clock'], 1)} | {c.get('run_dir', '')} | {note} |")
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, type=Path, help="consumer project with dist/ installed and bench-<task>/ seeded here")
    ap.add_argument("--tasks", required=True, help="comma-separated task ids under test/fixtures/benchmark/")
    ap.add_argument("--runs", type=int, default=9, help="runs per task (default 9, the reporting bar)")
    ap.add_argument("--budget-usd", type=float, default=3.0, help="Controller budget per run (default 3.0)")
    ap.add_argument("--forwarder-model", default=benchmark.FORWARDER_MODEL_DEFAULT, choices=("sonnet", "opus", "fable"))
    ap.add_argument("--unattended-bypass", action="store_true", help="pass --dangerously-skip-permissions (isolated VM only)")
    ap.add_argument("--controller-timeout", type=float, default=900, help="seconds per Controller role call (default 900)")
    ap.add_argument("--timeout", type=float, default=1200, help="seconds allowed for the instantiation call (default 1200)")
    ap.add_argument("--grade-timeout", type=float, default=60)
    ap.add_argument("--dry-run", action="store_true", help="print what would run; touch nothing, call nothing")
    ap.add_argument("--record", action="store_true", help="write test/results/<date>-fleet-<bundle>-tasks-<ids>.md")
    ap.add_argument("--fresh", action="store_true", help="archive any existing fleet checkpoint in --project and start over")
    args = ap.parse_args(argv)

    if args.runs < 1:
        print("refusing to run: --runs must be at least 1", file=sys.stderr)
        return 2
    set_env = [v for v in benchmark.BLOCKING_ENV if os.environ.get(v) not in (None, "", "0")]
    if set_env:
        print(f"refusing to run: {set_env} set; unset them (CLAUDE.md invariants 1, 3, 4)", file=sys.stderr)
        return 2
    if not args.dry_run and (shutil.which("claude") is None or shutil.which("bash") is None):
        print("refusing to run: `claude` and `bash` must both be on PATH", file=sys.stderr)
        return 2
    project = args.project.expanduser().resolve()
    if not (project / ".claude" / "agents").is_dir():
        print(f"refusing to run: {project}/.claude/agents missing; install dist/ first (src/README.md)", file=sys.stderr)
        return 2
    try:
        tasks = benchmark.discover_tasks(args.tasks.split(","))
    except ValueError as exc:
        print(f"refusing to run: {exc}", file=sys.stderr)
        return 2
    version_file = project / ".claude" / "ORCHESTRATOR_VERSION"
    bundle = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown"
    permission_args = claudep.BYPASS_PERMISSION_ARGS if args.unattended_bypass else claudep.FORWARDER_PERMISSION_ARGS
    permission_mode = ("bypassPermissions" if args.unattended_bypass
                       else "acceptEdits+allowedTools[" + claudep.FORWARDER_PERMISSION_ARGS[-1] + "]")
    identity = {"tasks": sorted(t["id"] for t in tasks), "fixture_hashes": {t["id"]: benchmark.fixture_fingerprint(t) for t in tasks},
                "runs": args.runs, "forwarder_model": args.forwarder_model, "permission_mode": permission_mode,
                "bundle": bundle, "instantiate_cell": INSTANTIATE_CELL, "budget_usd": args.budget_usd,
                "controller_sha": controller_sha(), "instruction_sha": instruction_sha()}

    if args.dry_run:
        for task in tasks:
            workdir = f"bench-{task['id']}"
            print(f"{task['id']}: {args.runs} run(s); each = reset {workdir}/ -> system_controller.run_quick(project, "
                  f"budget USD {args.budget_usd}) -> claude -p --model {args.forwarder_model} {' '.join(permission_args)} "
                  f"spawning {INSTANTIATE_CELL} with REPORT.md + instruction + task -> bash grade.sh")
            print(f"  Controller problem text would open:\n{PROBLEM_PREFACE.format(workdir=workdir)}{task['task_text'][:300]}\n")
        print(f"instantiation instruction (sha256 {identity['instruction_sha']}):\n{INSTANTIATE_INSTRUCTION}\n")
        print(f"controller inputs sha256 {identity['controller_sha']}; {len(tasks) * args.runs} run(s) in total, "
              f"each roughly 10 to 13 claude -p calls")
        return 0

    is_repo = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=project, capture_output=True, text=True)
    if is_repo.returncode != 0 or is_repo.stdout.strip() != "true":
        print(f"refusing to run: {project} is not a git repository; tasks are reset with git checkout/clean", file=sys.stderr)
        return 2
    git_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip() or "no-git"

    checkpoint_path = project / CHECKPOINT_FILENAME
    checkpoint, existing_meta = claudep.Checkpoint.load(checkpoint_path)
    if args.fresh:
        if checkpoint_path.exists():
            stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
            backup = checkpoint_path.with_name(checkpoint_path.name + f".abandoned-{stamp}")
            checkpoint_path.rename(backup)
            print(f"--fresh: archived the existing checkpoint to {backup.name}")
        checkpoint = claudep.Checkpoint(checkpoint_path)
        checkpoint.write_meta(identity)
    elif existing_meta is None:
        checkpoint.write_meta(identity)
    else:
        mismatches = claudep.describe_identity_mismatch(existing_meta, identity, CHECKPOINT_IDENTITY_FIELDS)
        old_hashes, new_hashes = existing_meta.get("fixture_hashes", {}), identity["fixture_hashes"]
        changed = sorted(t for t in set(old_hashes) & set(new_hashes) if old_hashes[t] != new_hashes[t])
        if changed:
            mismatches.append(f"fixture(s) edited since the checkpoint was written: {changed}")
        if mismatches:
            print(f"refusing to run: {checkpoint_path} was built with a different measurement:", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            print("pass --fresh to archive it and start over, or rerun with the original settings to resume it", file=sys.stderr)
            return 2
        if checkpoint.total_runs():
            print(f"resuming from {checkpoint_path.name}: {checkpoint.total_runs()} prior run(s) already recorded")

    task_reports = []
    for task in tasks:
        dest = benchmark.seed_task(project, task)
        print(f"=== {task['id']} ===")
        runs = list(checkpoint.prior_runs(task["id"], "fleet", INSTANTIATE_CELL))
        if runs:
            print(f"{task['id']}: {sum(r['passed'] for r in runs)}/{len(runs)} already recorded (from checkpoint)")
        for i in range(len(runs) + 1, args.runs + 1):
            record = run_one(project, task, dest, i, args.forwarder_model, permission_args, args.budget_usd,
                             args.controller_timeout, args.timeout, args.grade_timeout)
            checkpoint.record(task["id"], "fleet", INSTANTIATE_CELL, record)
            runs.append(record)
            status = "pass" if record["passed"] else ("ERROR" if record["error"] else "FAIL")
            c = record["controller"] or {}
            print(f"{task['id']} run {i}: {status}; controller {c.get('outcome', 'n/a')} ({c.get('technique', '')}), "
                  f"total {benchmark.money(record['total_cost'])}")
            if not record["passed"]:
                print(f"  {record['error'] or record['grade_output'][:500]}")
            if c.get("role_edits"):
                print(f"  ROLE EDITS before instantiation: {c['role_edits'][:300]}")
        task_reports.append({"task": task, "runs": runs, "summary": summarise(runs)})

    meta = {"when": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "git": git_rev, "bundle": bundle, "project": str(project),
            "forwarder_model": args.forwarder_model, "permission_mode": permission_mode, "runs": args.runs,
            "budget_usd": args.budget_usd, "controller_sha": identity["controller_sha"], "instruction_sha": identity["instruction_sha"]}
    for tr in task_reports:
        s = tr["summary"]
        print(f"{tr['task']['id']}: {s['passes']}/{s['n']}, Wilson [{s['lo']:.3f}, {s['hi']:.3f}], "
              f"{'clears' if s['clears'] else 'fails'} the 0.7 bar; mean cost {benchmark.money(s['mean_cost'])}, "
              f"cost per solved {benchmark.money(s['cost_per_solved'])}")
    if args.record:
        benchmark.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = claudep.unique_path(benchmark.RESULTS_DIR / (f"{dt.datetime.now().strftime('%Y-%m-%d')}-fleet-"
                                                          f"{claudep.bundle_tag(bundle)}{benchmark.tasks_tag(args.tasks)}.md"))
        out.write_text(render(meta, task_reports), encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")
    print(f"checkpoint at {checkpoint_path.name} (inside --project) retained; pass --fresh next time to start over")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
