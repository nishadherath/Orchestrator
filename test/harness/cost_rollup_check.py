#!/usr/bin/env python3
"""Check whether a spawned worker's cost rolls up into the forwarder's total_cost_usd.

Responsible for: the one assumption every dollar figure in
test/harness/benchmark.py depends on and docs/FINDINGS.md still lists as
unverified: that a spawned subagent's cost is included in the parent
`claude -p --output-format json` session's reported total_cost_usd, not
billed and then dropped. Runs the same task two ways from the same project,
one turn each: SPAWN asks a forwarder to hand the task to
`worker-sonnet-low` and relay its reply verbatim; DIRECT gives the forwarder
the identical task with no spawn at all. If the assumption holds, the two
total_cost_usd figures land close together, since both pay for the same
piece of writing. If SPAWN comes back far cheaper than DIRECT, the worker's
cost is not reaching the parent's reported total, and every benchmark
figure recorded so far understates the true cost of the routed cell.

Deliberately does not: touch anything above worker-sonnet-low (the cell is
incidental to what is being measured here), vary the task across reps (the
comparison only needs the same work done two ways), or attempt the second,
independent check FINDINGS.md also names, a live session's own `/cost`
reading, which needs an interactive session this script cannot drive.

The one non-obvious thing: the task is long-form prose, not a repeated or
mechanical filler string, because a model asked to repeat a sentence
thousands of times tends to shorten or summarise rather than produce it in
full, which would understate DIRECT's true cost and bias the comparison
towards looking like SPAWN is fine when it is not.

A single call hanging or timing out no longer aborts the whole run: each
call is caught on its own, recorded as a failed row, and the remaining
calls still run. A timeout is itself a data point, not noise to discard,
since SPAWN adding a hang DIRECT does not have would itself be a finding.

Usage:
    python3 test/harness/cost_rollup_check.py --project ~/consumer --dry-run
    python3 test/harness/cost_rollup_check.py --project ~/consumer --smoke-test
    python3 test/harness/cost_rollup_check.py --project ~/consumer --reps 2 --record
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "test" / "results"

TASK = (
    "Write a detailed technical explainer, about 2000 words, of how TCP "
    "congestion control works. Cover slow start, congestion avoidance, fast "
    "retransmit and fast recovery, with worked numeric examples. Do not "
    "read or write any files; reply with the explainer text only."
)

DIRECT_PREAMBLE = (
    "This is a diagnostic run, not a real request. Do this task yourself, "
    "in this turn: do not spawn a worker, do not use the Task tool, and do "
    "not ask a clarifying question.\n\n"
)

SMOKE_TASK = (
    "Write a short explainer, about 150 words, of what TCP congestion "
    "control is. Do not read or write any files; reply with the explainer "
    "text only."
)


def spawn_prompt(task: str) -> str:
    return (
        "This is a diagnostic run, not a real request. Spawn exactly one "
        "worker with subagent_type `worker-sonnet-low`, using the Task "
        "tool, and nothing else: do not do the task yourself, do not spawn "
        "any other worker, do not ask a clarifying question, and do not "
        "pass a model parameter when spawning.\n\n"
        f"Give it this handover task verbatim:\n---\n{task}\n---\n\n"
        "Wait for the worker to finish, then reply with its final report "
        "verbatim and nothing else added."
    )


PERMISSION_ARGS = ["--permission-mode", "acceptEdits", "--allowedTools", "Bash(python3 *)"]


def run_once(project: Path, prompt: str, model: str, timeout: float) -> dict:
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", model, *PERMISSION_ARGS]
    start = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout:.0f}s", "elapsed_s": round(timeout, 1)}
    elapsed = time.monotonic() - start
    if proc.returncode != 0:
        return {"error": f"claude exited {proc.returncode}: {proc.stderr.strip()[-400:]}", "elapsed_s": round(elapsed, 1)}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {"error": f"unparseable JSON: {e}; stdout tail: {proc.stdout[-300:]!r}", "elapsed_s": round(elapsed, 1)}
    return {
        "total_cost_usd": data.get("total_cost_usd"),
        "usage": data.get("usage"),
        "num_turns": data.get("num_turns"),
        "duration_ms": data.get("duration_ms"),
        "elapsed_s": round(elapsed, 1),
        "result_chars": len(str(data.get("result", ""))),
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", required=True, type=Path, help="consumer project with the dist/ bundle installed")
    ap.add_argument("--model", default="sonnet", choices=("sonnet", "opus", "fable"), help="forwarder model")
    ap.add_argument("--reps", type=int, default=1, help="repeats per condition")
    ap.add_argument("--timeout", type=float, default=None,
                     help="per-call timeout in seconds; default 90 for --smoke-test, 600 otherwise")
    ap.add_argument("--smoke-test", action="store_true",
                     help="use a much smaller ~150 word task, one rep per condition, as a quick sanity check")
    ap.add_argument("--dry-run", action="store_true", help="print the two prompts; run nothing")
    ap.add_argument("--record", action="store_true", help="write a result file to test/results/")
    ap.add_argument("--condition", choices=("spawn", "direct", "both"), default="both",
                     help="run only one condition, e.g. to re-run a fixed DIRECT prompt without paying for SPAWN again")
    args = ap.parse_args(argv)

    task = SMOKE_TASK if args.smoke_test else TASK
    reps = 1 if args.smoke_test else args.reps
    timeout = args.timeout if args.timeout is not None else (90.0 if args.smoke_test else 600.0)
    all_conditions = (("SPAWN", spawn_prompt(task)), ("DIRECT", DIRECT_PREAMBLE + task))
    if args.condition == "both":
        conditions = all_conditions
    else:
        conditions = tuple(c for c in all_conditions if c[0].lower() == args.condition)

    if args.dry_run:
        for name, prompt in conditions:
            print(f"=== {name} prompt ===\n{prompt}\n")
        return 0

    project = args.project.expanduser().resolve()
    if not project.is_dir():
        print(f"not a directory: {project}", file=sys.stderr)
        return 2

    rows: list[dict] = []
    for condition, prompt in conditions:
        for rep in range(1, reps + 1):
            print(f"running {condition} rep {rep}/{reps} (timeout {timeout:.0f}s)...", file=sys.stderr)
            row = run_once(project, prompt, args.model, timeout)
            row["condition"] = condition
            row["rep"] = rep
            rows.append(row)
            if "error" in row:
                print(f"  FAILED: {row['error']}", file=sys.stderr)
            else:
                print(f"  total_cost_usd={row['total_cost_usd']} elapsed_s={row['elapsed_s']} "
                      f"num_turns={row['num_turns']}", file=sys.stderr)

    spawn_costs = [r["total_cost_usd"] for r in rows
                   if r["condition"] == "SPAWN" and r.get("total_cost_usd") is not None]
    direct_costs = [r["total_cost_usd"] for r in rows
                    if r["condition"] == "DIRECT" and r.get("total_cost_usd") is not None]
    failures = [r for r in rows if "error" in r]
    spawn_mean = sum(spawn_costs) / len(spawn_costs) if spawn_costs else None
    direct_mean = sum(direct_costs) / len(direct_costs) if direct_costs else None

    print("\n=== summary ===")
    print(f"SPAWN mean total_cost_usd:  {spawn_mean} (from {len(spawn_costs)} of {reps} reps)")
    print(f"DIRECT mean total_cost_usd: {direct_mean} (from {len(direct_costs)} of {reps} reps)")
    if failures:
        print(f"{len(failures)} call(s) failed:")
        for r in failures:
            print(f"  {r['condition']} rep {r['rep']}: {r['error']}")
    if spawn_mean is not None and direct_mean is not None and direct_mean > 0:
        ratio = spawn_mean / direct_mean
        print(f"ratio SPAWN/DIRECT: {ratio:.3f}")
        if ratio < 0.3:
            print("SPAWN is far cheaper than DIRECT: worker cost does not appear to roll up.")
        else:
            print("SPAWN and DIRECT are in the same range: worker cost appears to roll up.")

    if args.record:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        tag = "smoke" if args.smoke_test else "full"
        out = RESULTS_DIR / f"{dt.datetime.now().strftime('%Y-%m-%d')}-cost-rollup-check-{tag}.md"
        lines = [
            f"# Cost roll-up check ({tag}), {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"Project: `{project}`. Model: {args.model}. Reps per condition: {reps}. "
            f"Per-call timeout: {timeout:.0f}s.",
            "",
            "| Condition | Rep | total_cost_usd | num_turns | elapsed_s | Error |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in rows:
            lines.append(f"| {r['condition']} | {r['rep']} | {r.get('total_cost_usd', '')} | "
                         f"{r.get('num_turns', '')} | {r['elapsed_s']} | {r.get('error', '')} |")
        lines += [
            "",
            f"SPAWN mean: {spawn_mean}. DIRECT mean: {direct_mean}.",
            "",
            "Raw usage objects:",
            "",
            "```json",
            json.dumps([{"condition": r["condition"], "rep": r["rep"], "usage": r.get("usage")} for r in rows],
                       indent=2),
            "```",
        ]
        out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        print(f"\nwrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
