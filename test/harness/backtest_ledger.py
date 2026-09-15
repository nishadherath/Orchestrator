#!/usr/bin/env python3
"""Feed the recorded benchmark outcomes into the ledger, in recorded order,
and check the learned rung activations reproduce D42 and D45, nothing else.

    python3 test/harness/backtest_ledger.py
    python3 test/harness/backtest_ledger.py --record

Responsible for: docs/ROUTING-2-DESIGN.md section 5 (docs/PLAN-2.md Stage
2.4, D64). Maps each benchmark task (T1 to T11) to the bucket it was built
for (docs/FRONTIERS.md), reconstructs one RoutingLedgerEntry per recorded
attempt from every per-run row in test/results/*benchmark*.md, and runs
them through tools/route.py's posterior() with the shipped priors. No live
claude -p call: this replays cost and pass/fail figures already paid for
and recorded when the benchmark ran.

The reconstruction benchmark.py's own staircase never recorded directly:
it measures a cell's aggregate pass rate over N independent same-cell
runs, not a single task's own sequential escalation. This script
approximates the latter from the former in the one way that preserves
the marginal counts posterior() actually needs: for each task, every
floor row that passed becomes its own ledger entry with no escalation;
every floor row that failed is paired, in encounter order, with the next
unused row from the next costliest cell the task's own results contain,
continuing up the ladder until a pass or the task's recorded cells are
exhausted. This never invents a pass or a fail that was not recorded; it
only decides which recorded floor failure a given recorded higher-cell
attempt is credited to, which the ledger's schema requires and the
underlying benchmark protocol does not distinguish.

Deliberately does not: touch T9's or T10's Stage 9.8 B0-brief runs (a
different arm, not the ladder this backtest reconstructs) or any routing
verdict (that is replay_routing.py's job).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "test" / "results"

sys.path.insert(0, str(REPO_ROOT / "tools"))
import route  # noqa: E402
import claudep  # noqa: E402

# docs/FRONTIERS.md's own per-task shape statement. T9's brief-arm runs
# and T10's brief-arm runs (Stage 9.8) are a different arm (B0 with a
# brief prepended) and are excluded below by cell name, not by task,
# since the same task's raw-handover rows are still wanted.
TASK_BUCKET = {
    "T1": "mechanical/short/contained", "T2": "mechanical/long/contained",
    "T3": "structured/short/contained", "T4": "structured/long/contained",
    "T5": "open/short/contained", "T8": "open/short/contained",
    "T9": "open/medium/contained", "T10": "open/medium/contained",
    "T6": "open/long/contained", "T7": "open/long/contained", "T11": "open/long/contained",
}

TASK_RE = re.compile(r"^## Task (T\d+)")
ROW_RE = re.compile(r"^\| (worker-[a-z]+-[a-z]+) \| (\d+) \| (yes|no) \| USD (\d+\.\d+) \| (\d+\.\d+) \|")


# Files a prior decision entry already invalidated, excluded here on that
# citation rather than on this script's own judgement: D16 disregards
# 2026-09-07-benchmark-04d2acc-original.md's T4 result outright (a fixture
# docstring tripped its own grader on every failing run; 25 of 25 failures
# across every sonnet cell up to xhigh cited the identical false-positive
# message). Found while building this backtest: feeding that file's T4
# rows in unfiltered chains three floor failures through to a spurious
# five-of-twelve worker-sonnet-xhigh sample, activating a rung docs/
# FRONTIERS.md's own reviewed conclusion says T4 has no frontier above the
# floor for. The replication run (after the grader fix) is not excluded:
# its T4 floor rows are 12 of 12 pass, the corrected measurement D16 asked for.
INVALIDATED_FILES = {"2026-09-07-benchmark-04d2acc-original.md"}


def collect_task_cell_rows(files: list[Path]) -> dict[str, dict[str, list[bool]]]:
    """{task: {cell: [pass_bool, ...]}}, in file and encounter order, pooled
    across every benchmark result file. Excludes files whose name contains
    'brief' (the B0-brief arm, a different measurement, D47) and
    INVALIDATED_FILES (data a prior decision entry already disregarded)."""
    out: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for path in files:
        if "brief" in path.name or path.name in INVALIDATED_FILES:
            continue
        task = None
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = TASK_RE.match(line)
            if m:
                task = m.group(1)
                continue
            m = ROW_RE.match(line)
            if m and task and task in TASK_BUCKET:
                cell, _run, ok, _cost, _wall = m.groups()
                out[task][cell].append(ok == "yes")
    return out


def reconstruct_ledger(task_cells: dict[str, dict[str, list[bool]]]) -> list[dict]:
    """One RoutingLedgerEntry per recorded floor attempt (see module
    docstring for the pairing rule). Escalation cells within a task are
    tried in tools/route.py's COST_ORDER."""
    entries: list[dict] = []
    for task, cells in task_cells.items():
        bucket = TASK_BUCKET[task]
        floor_rows = list(cells.get("worker-sonnet-low", []))
        higher_cells = [c for c in route.COST_ORDER if c != "worker-sonnet-low" and c in cells]
        cursors = {c: 0 for c in higher_cells}
        for passed in floor_rows:
            if passed:
                entries.append({"bucket": bucket, "first_cell": "worker-sonnet-low",
                                 "escalations": [], "final_outcome": "pass"})
                continue
            escalations = []
            for cell in higher_cells:
                rows = cells[cell]
                if cursors[cell] >= len(rows):
                    continue
                ok = rows[cursors[cell]]
                cursors[cell] += 1
                escalations.append({"cell": cell, "outcome": "pass" if ok else "fail"})
                if ok:
                    break
            entries.append({"bucket": bucket, "first_cell": "worker-sonnet-low",
                             "escalations": escalations, "final_outcome": "unknown" if not escalations else escalations[-1]["outcome"]})
    return entries


def render(post_by_bucket: dict[str, dict], checks: list[tuple[str, bool, str]], git_rev: str) -> str:
    lines = [f"# Ledger backtest, {dt.datetime.now().strftime('%Y-%m-%d %H:%M')} at {git_rev}", "",
             "Every recorded benchmark outcome (test/results/*benchmark*.md, excluding the B0-brief "
             "arm) fed into tools/route.py's posterior() in file order, against the shipped priors "
             "(docs/ROUTING-2-DESIGN.md section 5, docs/PLAN-2.md Stage 2.4, D64). No live claude -p call.", ""]
    lines.append("| Bucket | Floor posterior | Active rungs | Controller reason |")
    lines.append("| :--- | :--- | :--- | :--- |")
    for bucket in sorted(post_by_bucket):
        p = post_by_bucket[bucket]
        lines.append(f"| {bucket} | {p['floor_mean']:.3f} ({p['floor_ledger_passes']} pass, "
                      f"{p['floor_ledger_fails']} fail) | {p['active_rungs']} | {p['controller_reason']} |")
    lines.append("")
    lines.append("## Pass conditions (docs/ROUTING-2-DESIGN.md section 5)")
    lines.append("")
    for name, ok, detail in checks:
        lines.append(f"- {'PASS' if ok else 'FAIL'}: {name} -- {detail}")
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", action="store_true")
    args = ap.parse_args(argv)

    priors = route.load_priors()
    files = sorted(RESULTS_DIR.glob("*benchmark*.md"))
    task_cells = collect_task_cell_rows(files)
    ledger = reconstruct_ledger(task_cells)

    post_by_bucket: dict[str, dict] = {}
    for bucket in sorted(set(TASK_BUCKET.values())):
        post = route.posterior(priors, ledger, bucket)
        decision = route.controller_decision(priors, post, route.load_cost_table(), bucket)
        post["controller_reason"] = decision["reason"]
        post_by_bucket[bucket] = post

    checks: list[tuple[str, bool, str]] = []

    for bucket, post in post_by_bucket.items():
        s, h, b = bucket.split("/")
        plan = route.plan(s, h, b, priors=priors, ledger=ledger)
        ok = plan["first"] == "worker-sonnet-low"
        checks.append((f"{bucket}: first stays the floor", ok, f"got {plan['first']!r}"))

    p = post_by_bucket["open/medium/contained"]
    opus_mean = p["rungs"].get("worker-opus-high", {}).get("mean", 0.0)
    checks.append(("open/medium/contained: worker-opus-high posterior mean >= 0.9", opus_mean >= 0.9,
                    f"got {opus_mean:.3f} ({p['rungs']['worker-opus-high']['ledger_passes']} pass, "
                    f"{p['rungs']['worker-opus-high']['ledger_fails']} fail)"))

    sonnet_rungs = ("worker-sonnet-medium", "worker-sonnet-high", "worker-sonnet-xhigh")
    for bucket, post in post_by_bucket.items():
        activated = [c for c in sonnet_rungs if c in post["active_rungs"]]
        checks.append((f"{bucket}: no intermediate sonnet rung activates", not activated,
                        f"activated: {activated}" if activated else "none activated"))

    for bucket, post in post_by_bucket.items():
        s, h, b = bucket.split("/")
        if b != "contained":
            continue
        decision = route.controller_decision(priors, post, route.load_cost_table(), bucket)
        checks.append((f"{bucket}: Controller decision is not proactive", not decision["proactive"],
                        f"reason={decision['reason']!r}"))

    ok_all = all(ok for _, ok, _ in checks)

    import subprocess
    git_rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=REPO_ROOT).stdout.strip() or "no-git"
    report = render(post_by_bucket, checks, git_rev)
    print(report)

    if args.record:
        RESULTS_DIR.mkdir(exist_ok=True)
        out = claudep.unique_path(RESULTS_DIR / f"{dt.datetime.now().strftime('%Y-%m-%d')}-backtest-ledger.md")
        out.write_text(report, encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")

    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
