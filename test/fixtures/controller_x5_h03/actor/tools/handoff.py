#!/usr/bin/env python3
"""Write and check a handoff file: what a fresh session needs when the model
or reasoning effort changes, or a new agent launches (docs/PLAN-2.md Stage 3,
docs/ROUTING-2-DESIGN.md section 7, Jeb's brief).

    python3 tools/handoff.py new --slug S --reason model-change --to-model sonnet --to-effort high
    python3 tools/handoff.py new --slug S --reason spawn --to-model sonnet --to-effort low \\
        --cell worker-sonnet-low --cell worker-sonnet-low --controller-runs 1
    python3 tools/handoff.py new --slug S --reason model-change --to-model sonnet --to-effort high \\
        --project . --pending-workers
    python3 tools/handoff.py check handoffs/2026-09-15-plan2-stage2.md
    python3 tools/handoff.py --selftest

Responsible for: the ten-heading template Jeb asked for (goal, decisions
made, files that matter, verified facts, work completed, unresolved
questions, exact next action, model and effort to set, and a cost and a
time projection each ending in one machine-computed "Computed:" line);
writing it (`new`) and verifying an existing one still holds it
(`check`). The computed lines come from `src/cost_table.json`'s measured
unit costs, or from a project's own `.claude/routing-ledger.jsonl` means
once it has enough entries (`--ledger-overrides`), never from guesswork,
and a `new`-written file records its own arguments in an HTML comment so
`check` can recompute the same line and compare rather than trust it.

Deliberately does not: write the prose sections (goal, decisions, and so
on). Those are the author's job; this tool only guarantees the skeleton
is complete and the two projections are arithmetic, not narrative.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shlex
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))
import route  # noqa: E402

HEADINGS = ("Goal", "Decisions already made", "Files and links that matter", "Verified facts",
            "Work completed", "Unresolved questions", "Exact next action",
            "Model and effort to set", "Cost projection", "Time projection")

# The placeholder `new` writes into each prose section it cannot fill
# itself. A section still holding this (or holding nothing at all) is
# "empty" for check's purposes: `render`'s literal reminder text left in
# place is exactly as unfilled as a blank heading, and check must catch
# both, not just the second.
PLACEHOLDERS = {
    "Goal": "(fill in: the one or two sentences a fresh session needs to know why this exists)",
    "Decisions already made": "(fill in: what is settled and must not be re-litigated, with pointers)",
    "Files and links that matter": "(fill in: paths and decision-entry numbers, not prose summaries of them)",
    "Verified facts": "(fill in: what was checked in this session, quoting the command or the number)",
    "Work completed": "(fill in: what landed, with commit hashes)",
    "Unresolved questions": "(fill in: what the next session must not assume is settled)",
    "Exact next action": "(fill in: the first concrete step, not a restatement of the goal)",
}

FRONT_MATTER_RE = re.compile(r"^<!--\s*handoff\.py new (?P<args>.*?)\s*-->\s*$", re.MULTILINE)


class HandoffError(Exception):
    """Every error this module raises; check's CLI turns one into exit 1
    naming the problem, never a bare traceback."""


def _new_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="handoff.py new", add_help=False)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--reason", required=True, choices=("model-change", "effort-change", "spawn"))
    ap.add_argument("--to-model", required=True)
    ap.add_argument("--to-effort", required=True)
    ap.add_argument("--cell", action="append", default=[], help="repeatable, one run each")
    ap.add_argument("--cells", action="append", default=[], metavar="CELL:N", help="repeatable, an explicit count")
    ap.add_argument("--controller-runs", type=int, default=0)
    ap.add_argument("--verdicts", type=int, default=0)
    ap.add_argument("--project", default=".")
    ap.add_argument("--from-model", default=None)
    ap.add_argument("--from-effort", default=None)
    ap.add_argument("--pending-workers", action="store_true",
                     help="append route.py's pending-worker listing to Unresolved questions "
                          "(docs/PLAN-3.md Stage D, docs/COMPACTION-DESIGN.md section 10)")
    return ap


def parse_new_args(argv: list[str]) -> argparse.Namespace:
    return _new_argparser().parse_args(argv)


def cell_counts(args: argparse.Namespace) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cell in args.cell:
        counts[cell] = counts.get(cell, 0) + 1
    for item in args.cells:
        cell, _, n = item.partition(":")
        counts[cell] = counts.get(cell, 0) + int(n)
    return counts


def compute_projection(counts: dict[str, int], controller_runs: int, verdicts: int,
                        costs: dict, ledger_means: dict | None = None) -> dict:
    ledger_means = ledger_means or {}
    total_cost, total_wall = 0.0, 0.0
    parts_cost: list[str] = []
    parts_wall: list[str] = []
    unpriced: list[str] = []

    for cell, n in sorted(counts.items()):
        row = ledger_means.get(cell) or costs["cells"].get(cell, {})
        cost, wall = row.get("cost_per_run_usd"), row.get("wall_clock_s")
        source = "ledger" if cell in ledger_means else "cost_table"
        if cost is None:
            unpriced.append(cell)
            continue
        total_cost += cost * n
        total_wall += (wall or 0) * n
        parts_cost.append(f"{n} x {cell} (USD {cost:.4f} each, {source})")
        parts_wall.append(f"{n} x {cell} ({wall:.0f} s each, {source})")

    if controller_runs:
        c = costs["controller"]
        ccost = c["quick_mode_run_usd"] + c["instantiation_usd"]
        cwall = c["wall_clock_s"] + c["instantiation_wall_s"]
        total_cost += ccost * controller_runs
        total_wall += cwall * controller_runs
        parts_cost.append(f"{controller_runs} x controller (USD {ccost:.4f} each)")
        parts_wall.append(f"{controller_runs} x controller ({cwall:.0f} s each)")

    if verdicts:
        v = costs["verdict"]
        vcost, vwall = v["opus_prose_router_usd"], v.get("opus_prose_router_wall_s", 0)
        total_cost += vcost * verdicts
        total_wall += vwall * verdicts
        parts_cost.append(f"{verdicts} x verdict (USD {vcost:.4f} each)")
        parts_wall.append(f"{verdicts} x verdict ({vwall:.0f} s each)")

    return {"total_cost": round(total_cost, 4), "total_wall": round(total_wall, 1),
            "parts_cost": parts_cost, "parts_wall": parts_wall, "unpriced": unpriced}


def computed_lines(args: argparse.Namespace) -> tuple[str, str]:
    """The one "Computed:" line each for the cost and time projection
    sections, deterministic from `args` and the files on disk. `new` writes
    these; `check` recomputes them from the same front-matter args and
    compares."""
    counts = cell_counts(args)
    costs = route.load_cost_table()

    if not counts and not args.controller_runs and not args.verdicts:
        # A session handoff (docs/ROUTING-2-DESIGN.md section 7): no cells
        # named, so there is nothing claude -p will spend. The only
        # computable figure is the fixed session-load estimate.
        tokens = costs["session"]["fixed_load_tokens_estimate"]
        cost_line = (f"Computed: session load ~{tokens:,} tokens ({costs['session']['provenance']}); "
                     "no claude -p calls projected for this handoff.")
        time_line = ("Computed: no claude -p wall-clock component projected; session time is not "
                     "derived from src/cost_table.json and belongs in prose above.")
        return cost_line, time_line

    overrides_after = route.load_priors()["steering"]["ledger_overrides_after"]
    # route.ledger_cell_means (audit A5, docs/AUDIT-2026-09-16.md): moved
    # there so plan()'s own --explain projection can use the same
    # per-cell means this file's projections always have; imported here
    # rather than kept as a second, hand-copied definition.
    project_ledger = route.load_ledger(route.default_ledger_path(Path(args.project)))
    ledger_means = route.ledger_cell_means(project_ledger, overrides_after)
    proj = compute_projection(counts, args.controller_runs, args.verdicts, costs, ledger_means)
    cost_line = "Computed: " + " + ".join(proj["parts_cost"]) if proj["parts_cost"] else "Computed: "
    cost_line += f" = USD {proj['total_cost']:.4f}"
    if proj["unpriced"]:
        cost_line += f" (excludes {len(proj['unpriced'])} unmeasured: {proj['unpriced']})"
    cost_line += "."
    time_line = "Computed: " + " + ".join(proj["parts_wall"]) if proj["parts_wall"] else "Computed: "
    time_line += f" = {proj['total_wall']:.0f} s."
    return cost_line, time_line


def render(args: argparse.Namespace, argv: list[str]) -> str:
    cost_line, time_line = computed_lines(args)
    today = dt.date.today().isoformat()
    reason_text = {"model-change": "model-change.", "effort-change": "effort-change.",
                   "spawn": "spawn."}[args.reason]
    model_line = (f"`/model` {args.to_model}, effort {args.to_effort}."
                  if not cell_counts(args) else
                  f"`/model` {args.to_model}, effort {args.to_effort} for the orchestrator; "
                  f"spawn: {', '.join(sorted(cell_counts(args)))}.")
    lines = [
        f"# Handoff: {args.slug}", "",
        f"<!-- handoff.py new {shlex.join(argv)} -->",
        f"Written {today} by {args.from_model or '?'}, {args.from_effort or '?'}. Reason: {reason_text}", "",
    ]
    for heading in HEADINGS:
        lines.append(f"## {heading}")
        lines.append("")
        if heading == "Model and effort to set":
            lines.append(model_line)
        elif heading == "Cost projection":
            lines.append(cost_line)
        elif heading == "Time projection":
            lines.append(time_line)
        elif heading == "Unresolved questions" and args.pending_workers:
            lines.append(PLACEHOLDERS[heading])
            lines.append("")
            lines.extend(route.pending_workers_lines(Path(args.project)))
        else:
            lines.append(PLACEHOLDERS[heading])
        lines.append("")
    return "\n".join(lines)


def parse_handoff(text: str) -> dict:
    m = FRONT_MATTER_RE.search(text)
    if not m:
        raise HandoffError("no front-matter comment (<!-- handoff.py new ... -->) found")
    argv = shlex.split(m["args"])
    try:
        args = parse_new_args(argv)
    except SystemExit as exc:
        raise HandoffError(f"front-matter arguments do not parse: {m['args']!r}") from exc

    sections: dict[str, str] = {}
    order: list[str] = []
    current = None
    body: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(body).strip()
            current = line[3:].strip()
            order.append(current)
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        sections[current] = "\n".join(body).strip()
    return {"args": args, "argv": argv, "sections": sections, "order": order}


def check_handoff(path: Path) -> list[str]:
    """Every problem found, empty if the file is sound. Never raises for a
    malformed file; a parse failure is itself one problem in the list."""
    text = path.read_text(encoding="utf-8")
    try:
        parsed = parse_handoff(text)
    except HandoffError as exc:
        return [str(exc)]

    problems: list[str] = []
    if not text.lstrip().startswith("# Handoff:"):
        problems.append("missing '# Handoff: <slug>' title line")

    order, sections = parsed["order"], parsed["sections"]
    missing = [h for h in HEADINGS if h not in order]
    if missing:
        problems.append(f"missing heading(s): {missing}")
    extra_or_reordered = [h for h in order if h in HEADINGS]
    if extra_or_reordered != [h for h in HEADINGS if h in order]:
        problems.append(f"headings out of order: {extra_or_reordered}")
    for h in HEADINGS:
        body = sections.get(h, "").strip()
        if not body:
            problems.append(f"empty section: {h!r}")
        elif h in PLACEHOLDERS and body == PLACEHOLDERS[h]:
            problems.append(f"empty section: {h!r} (unfilled placeholder)")

    try:
        cost_line, time_line = computed_lines(parsed["args"])
    except Exception as exc:
        problems.append(f"could not recompute projections from the front matter: {exc}")
        return problems
    if "Cost projection" in sections and cost_line not in sections["Cost projection"].splitlines():
        problems.append(f"Cost projection: computed line does not match; expected {cost_line!r}")
    if "Time projection" in sections and time_line not in sections["Time projection"].splitlines():
        problems.append(f"Time projection: computed line does not match; expected {time_line!r}")
    return problems


def _selftest(verbose: bool = False) -> tuple[bool, list[str]]:
    import tempfile
    problems: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            problems.append(msg)
        elif verbose:
            print(f"ok: {msg}")

    with tempfile.TemporaryDirectory(prefix="handoff-selftest-") as tmp:
        tmp_path = Path(tmp)
        argv = ["--slug", "selftest", "--reason", "model-change", "--to-model", "sonnet",
                "--to-effort", "high", "--from-model", "fable", "--from-effort", "high"]
        args = parse_new_args(argv)
        text = render(args, argv)
        f = tmp_path / "handoff.md"
        f.write_text(text, encoding="utf-8", newline="\n")

        problems_found = check_handoff(f)
        check(bool(problems_found), "a freshly written skeleton still has unfilled sections, so check should complain")
        check(any("Goal" in p or "empty" in p for p in problems_found),
              f"the empty-section complaint should be among the problems, got {problems_found}")

        # Fill every prose section with a placeholder sentence, leaving the
        # two computed lines and the model/effort line exactly as `new` wrote them.
        filled = text
        for placeholder in PLACEHOLDERS.values():
            filled = filled.replace(placeholder, "Filled in for the selftest.")
        f.write_text(filled, encoding="utf-8", newline="\n")
        problems_now = check_handoff(f)
        check(not problems_now, f"(a) a fully filled-in handoff should check clean, got {problems_now}")

        parsed = parse_handoff(filled)
        for heading in HEADINGS:
            body = parsed["sections"][heading]
            corrupted = filled.replace(f"## {heading}\n\n{body}", f"## {heading}\n\n")
            if corrupted == filled:
                check(False, f"(b) corrupting {heading!r} had no effect on the text; selftest's own replace failed")
                continue
            cf = tmp_path / f"corrupt-{heading.replace(' ', '_')}.md"
            cf.write_text(corrupted, encoding="utf-8", newline="\n")
            found = check_handoff(cf)
            check(bool(found) and any(heading in p for p in found),
                  f"(b) corrupting {heading!r} should be named in the problems, got {found}")

        no_front_matter = "\n".join(l for l in filled.splitlines() if "<!-- handoff.py new" not in l)
        nf = tmp_path / "no-front-matter.md"
        nf.write_text(no_front_matter, encoding="utf-8", newline="\n")
        check(bool(check_handoff(nf)), "(c) a missing front-matter comment should be a problem")

        argv2 = ["--slug", "cells", "--reason", "spawn", "--to-model", "sonnet", "--to-effort", "low",
                 "--cell", "worker-sonnet-low", "--cell", "worker-sonnet-low", "--controller-runs", "1",
                 "--from-model", "sonnet", "--from-effort", "high"]
        args2 = parse_new_args(argv2)
        text2 = render(args2, argv2)
        check("controller" in text2 and "worker-sonnet-low" in text2,
              "(d) a spawn handoff's computed line should name the cells and the controller")
        f2 = tmp_path / "cells.md"
        f2.write_text(text2, encoding="utf-8", newline="\n")
        for placeholder in PLACEHOLDERS.values():
            text2 = text2.replace(placeholder, "Filled in for the selftest.")
        f2.write_text(text2, encoding="utf-8", newline="\n")
        check(not check_handoff(f2), f"(d) a filled spawn handoff should check clean, got {check_handoff(f2)}")

        # (e) --pending-workers appends route.py's own pending-worker
        # listing to Unresolved questions, using the project the ledger
        # actually lives in; the section is then no longer the bare
        # placeholder, without needing the placeholder itself replaced.
        route.append_ledger_entry(route.default_ledger_path(tmp_path), {
            "type": "RoutingLedgerEntry", "id": "led-001", "ledger_version": 1, "references": [],
            "ts": dt.datetime.now().isoformat(), "task_slug": "pending-test", "bucket": "mechanical/short/contained",
            "self_directed": False, "first_cell": "worker-sonnet-low", "escalations": [], "final_outcome": "unknown",
            "cost_usd": 0, "wall_clock_s": 0, "controller_run_dir": None, "winning_technique": None,
            "notes": "pending: selftest-pending-worker",
            "context": {"peak_tokens": None, "window": None, "compactions": None, "source": "none"}})
        argv3 = ["--slug", "pending", "--reason", "model-change", "--to-model", "sonnet", "--to-effort", "medium",
                 "--project", str(tmp_path), "--pending-workers"]
        args3 = parse_new_args(argv3)
        text3 = render(args3, argv3)
        check("led-001" in text3 and "selftest-pending-worker" in text3,
              "(e) --pending-workers should list the pending entry by id and worker name")
        parsed3 = parse_handoff(text3)
        check(parsed3["sections"]["Unresolved questions"] != PLACEHOLDERS["Unresolved questions"],
              "(e) the pending-worker listing should make Unresolved questions no longer the bare placeholder")
        f3 = tmp_path / "pending.md"
        f3.write_text(text3, encoding="utf-8", newline="\n")
        found3 = check_handoff(f3)
        check(not any("Unresolved questions" in p for p in found3),
              f"(e) Unresolved questions should not be flagged once the pending listing is present, got {found3}")

    return (not problems, problems)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command")

    new_ap = sub.add_parser("new", parents=[_new_argparser()], add_help=True)
    new_ap.add_argument("--out", type=Path, default=None, help="override the output path")

    check_ap = sub.add_parser("check")
    check_ap.add_argument("file", type=Path)

    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        ok, problems = _selftest(verbose=args.json)
        if ok:
            print("selftest: PASS, 5 scenarios (a: clean file, b: corrupted sections named, "
                  "c: missing front matter, d: a spawn handoff's cell/controller cost, "
                  "e: --pending-workers)")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    if args.command == "new":
        # The front matter records this argv exactly, minus --out: --out is
        # where to write the file, not part of the handoff's own recorded
        # identity, and check() never needs it to recompute a projection.
        clean_argv = []
        skip_next = False
        for a in argv[1:]:
            if skip_next:
                skip_next = False
                continue
            if a == "--out":
                skip_next = True
                continue
            clean_argv.append(a)
        text = render(args, clean_argv)
        # <project>/handoffs/, not REPO_ROOT / "handoffs": the two
        # coincide in an installed dist/ bundle, but in this repository
        # --project <consumer> with --pending-workers read the
        # consumer's own ledger while the file landed here regardless
        # (audit A19, docs/AUDIT-2026-09-16.md).
        out = args.out or (Path(args.project) / "handoffs" / f"{dt.date.today().isoformat()}-{args.slug}.md")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {out}")
        return 0

    if args.command == "check":
        problems = check_handoff(args.file)
        if not problems:
            print(f"{args.file}: OK")
            return 0
        print(f"{args.file}: {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
