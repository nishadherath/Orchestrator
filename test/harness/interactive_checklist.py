#!/usr/bin/env python3
"""Prepare a consumer project for Jeb's interactive session and read back
what it produced (docs/PLAN-4.md Stage D, task D.1).

Responsible for: closing E31 (does `autoCompactWindow` take effect at
project scope) and E32 (does `context_window_size` report the model's
native window or the configured one, D69) as direct observation, rather
than documentation, and capturing `tokenSamples`' real shape and
`.claude/session.json`'s behaviour in an interactive session for the
first time (every prior observation, D71 through D77, came from a
headless `claude -p` run, where the status line never fires at all:
`docs/FINDINGS.md`, "statusLine and subagentStatusLine do not fire in a
headless claude -p run").

Two subcommands. `--prepare` resets the project to a known state and
seeds T12 (the same fixture Stage B measured, for continuity) so the
session has one thing to point at. `--check` reads back everything the
session should have produced and prints a FINDINGS-ready table; run it
after Stage D's task D.2, not before.

Deliberately does not: run any `claude -p` call itself, spawn anything,
or touch this repository. D.1's own cost is zero; the live spend Stage D
projects (USD 0.5 to 2) is entirely D.2's interactive session, which
this script only prepares for and reads back from. Also does not, and
cannot, observe what `/autocompact` prints to the terminal: that value
never reaches any file, so `--check` takes it as an optional argument
Jeb reports from what he saw on screen, rather than guessing or leaving
it silently blank with no indication that a human still owes it.

Usage:
    python3 test/harness/interactive_checklist.py --prepare --project ~/orchestrator-scratch
    ... Jeb's session (docs/PLAN-4.md Stage D, task D.2) ...
    python3 test/harness/interactive_checklist.py --check --project ~/orchestrator-scratch \\
        --autocompact-readback 130000
    python3 test/harness/interactive_checklist.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import benchmark  # noqa: E402

TASK_ID = "T12"
CELL = "worker-sonnet-low"
WINDOW = 130000
CONTEXT_USAGE_REL = ".claude/context-usage.json"
SESSION_POINTER_REL = ".claude/session.json"
CLAUDE_MD_POINTER = "Read ORCHESTRATOR.md before delegating any task."


def merge_autocompact_window(project: Path, window: int) -> str:
    """Sets `autoCompactWindow` in `<project>/.claude/settings.json` at
    project scope, per E31's own question (`test/harness/empirical-checklist.md`):
    whether the project-scope key takes effect at all, which this
    session's own `/autocompact` readback (D.2) answers directly. Merges
    rather than overwrites, so `settings.fragment.json`'s own keys
    (statusLine, subagentStatusLine, hooks) already in place survive.
    Returns a one-line status string for `--prepare`'s own report."""
    path = project / ".claude" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    before = data.get("autoCompactWindow")
    data["autoCompactWindow"] = window
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return (f"autoCompactWindow already {before} in {path}, left at {window}" if before == window else
            f"autoCompactWindow set to {window} in {path} (was {before!r})")


def ensure_orchestrator_pointer(project: Path) -> str:
    """Confirms `CLAUDE.md` carries the standard "Read ORCHESTRATOR.md
    before delegating any task" pointer line (`src/README.md`'s own
    install instruction), appending it only if absent. This is the
    "instructions appended" D.1 names; it is not the compact-instructions
    section D77 removed, which this script never adds."""
    path = project / "CLAUDE.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if CLAUDE_MD_POINTER in text:
        return f"{path} already carries the ORCHESTRATOR.md pointer"
    text = (text.rstrip("\n") + "\n\n" + CLAUDE_MD_POINTER + "\n") if text.strip() else (CLAUDE_MD_POINTER + "\n")
    path.write_text(text, encoding="utf-8", newline="\n")
    return f"{path}: appended the ORCHESTRATOR.md pointer (was missing)"


def remove_if_exists(project: Path, rel: str) -> str:
    path = project / rel
    if not path.exists():
        return f"{path}: already absent"
    path.unlink()
    return f"{path}: removed"


def prepare(project: Path) -> None:
    print(f"Preparing {project} for Stage D's interactive session (docs/PLAN-4.md task D.1).\n")
    print(merge_autocompact_window(project, WINDOW))
    print(ensure_orchestrator_pointer(project))
    print(remove_if_exists(project, CONTEXT_USAGE_REL))
    print(remove_if_exists(project, SESSION_POINTER_REL))
    task = benchmark.load_task(TASK_ID)
    dest = benchmark.seed_task(project, task)
    print(f"{TASK_ID} seeded at {dest}")

    prompt = benchmark.BENCHMARK_INSTRUCTION.format(
        cell=CELL, workdir=dest.relative_to(project).as_posix(), task=task["task_text"])
    print("\nNow do task D.2 (docs/PLAN-4.md), by hand, in an interactive session opened on this project:\n")
    print("  1. Open a session in this project (not headless, not claude -p).")
    print("  2. Run `/autocompact` with no value and note exactly what it reports.")
    print(f"     (E31: whether the {WINDOW} just configured at project scope took effect,")
    print("      or the platform fell back to the model's native window regardless.)")
    print("  3. Give the session this handover, verbatim, to spawn the one worker D.2 names:")
    print("\n---\n" + prompt.strip() + "\n---\n")
    print("  4. Wait for the worker to finish.")
    print("  5. Exit the session.")
    print(f"\nThen run: python3 test/harness/interactive_checklist.py --check --project {project} "
          "--autocompact-readback <what step 2 reported>")


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def check(project: Path, autocompact_readback: str | None) -> None:
    usage_path = project / CONTEXT_USAGE_REL
    usage = read_json(usage_path)
    pointer_path = project / SESSION_POINTER_REL
    pointer = read_json(pointer_path)

    print(f"# Stage D task D.2 readback, {project}\n")

    print(f"## {CONTEXT_USAGE_REL}")
    if usage is None:
        print(f"Absent. The statusLine/subagentStatusLine hooks did not fire, or the session never "
              f"produced an API response (`docs/FINDINGS.md`'s headless finding would then extend to "
              f"an interactive session too, which would itself be worth recording).\n")
    else:
        main = usage.get("main") or {}
        print(f"Present, written_at {usage.get('written_at')!r}.")
        print(f"main.context_window_size: {main.get('context_window_size')!r} "
              f"(configured autoCompactWindow: {WINDOW}; model's native window per "
              f"src/cost_table.json's context.model_windows: check against main.model {main.get('model')!r})")
        print(f"main.used_percentage: {main.get('used_percentage')!r}")
        tasks = usage.get("tasks") or {}
        if not tasks:
            print("No tasks entry recorded (subagentStatusLine may not have fired, or the worker "
                  "finished before its first refresh).")
        for name, task_entry in tasks.items():
            print(f"\n### tasks[{name!r}] (verbatim, including tokenSamples' real shape)")
            print(json.dumps(task_entry, indent=2, ensure_ascii=False))
        print()

    print(f"## {SESSION_POINTER_REL}")
    if pointer is None:
        print(f"Absent. The SessionStart hook (`--session-pointer`, docs/COMPACTION-DESIGN.md section "
              f"13.4) did not fire in this interactive session, or fired before this consumer project "
              f"had the hook installed.\n")
    else:
        print(json.dumps(pointer, indent=2, ensure_ascii=False))
        print()

    print("## FINDINGS-ready table\n")
    print("| Claim | Evidence | Settles |")
    print("| :--- | :--- | :--- |")
    if autocompact_readback is not None:
        print(f"| `/autocompact` at project scope reports {autocompact_readback!r} after "
              f"`autoCompactWindow: {WINDOW}` was set in `.claude/settings.json` | Read directly from "
              f"the session, task D.2 | E31 |")
    else:
        print(f"| **TODO**: what did `/autocompact` report? | Re-run `--check` with "
              f"`--autocompact-readback <value>`, or fill this row in by hand | E31 |")
    if usage is not None:
        main = usage.get("main") or {}
        cws = main.get("context_window_size")
        print(f"| `main.context_window_size` reports {cws!r} with `autoCompactWindow` set to {WINDOW} | "
              f"`{CONTEXT_USAGE_REL}` from this session, task D.2 | E32 |")
    else:
        print(f"| **TODO**: `{CONTEXT_USAGE_REL}` was absent; re-run `--check` after a session that "
              f"produced at least one status line refresh | (no file to cite) | E32 |")
    print(f"| `.claude/session.json` {'was written' if pointer is not None else 'was NOT written'} by "
          f"the `SessionStart` hook in an interactive session | `{SESSION_POINTER_REL}` from this "
          f"session, task D.2 | whether the pointer hook (13.4) fires interactively, not just under "
          f"`claude -p` (Stage B's own runs) |")


def _selftest(verbose: bool = False) -> tuple[bool, list[str]]:
    """No claude -p calls, no network: exercises `--prepare` and `--check`
    against a throwaway git repository standing in for a consumer
    project, the same isolation `benchmark.py`'s own harness checks use."""
    import shutil
    import subprocess
    import tempfile

    problems: list[str] = []

    def check_(cond: bool, msg: str) -> None:
        if not cond:
            problems.append(msg)
        elif verbose:
            print(f"ok: {msg}")

    with tempfile.TemporaryDirectory(prefix="interactive-checklist-selftest-") as tmp:
        project = Path(tmp) / "project"
        project.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                         "--allow-empty", "-m", "init"], cwd=project, check=True)
        (project / "CLAUDE.md").write_text("Existing project notes.\n", encoding="utf-8")

        prepare(project)

        settings = read_json(project / ".claude" / "settings.json")
        check_(settings is not None and settings.get("autoCompactWindow") == WINDOW,
               f"(a) --prepare should set autoCompactWindow to {WINDOW}, got {settings}")
        claude_md = (project / "CLAUDE.md").read_text(encoding="utf-8")
        check_(CLAUDE_MD_POINTER in claude_md and "Existing project notes." in claude_md,
               "(a) --prepare should append the pointer without discarding existing CLAUDE.md content")
        check_((project / f"bench-{TASK_ID}").is_dir(), f"(a) --prepare should seed bench-{TASK_ID}/")

        # (b) idempotent: a second --prepare must not duplicate the pointer
        # line or disturb an already-correct autoCompactWindow.
        prepare(project)
        claude_md_2 = (project / "CLAUDE.md").read_text(encoding="utf-8")
        check_(claude_md_2.count(CLAUDE_MD_POINTER) == 1,
               f"(b) a second --prepare should not duplicate the pointer line, got:\n{claude_md_2}")

        # (c) --check on a project with no session artefacts yet should
        # report both as absent, not raise, and still emit TODO rows.
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            check(project, autocompact_readback=None)
        out = buf.getvalue()
        check_("Absent" in out and "TODO" in out,
               f"(c) --check with no session artefacts should report both files absent with TODO rows, got:\n{out[:500]}")

        # (d) --check with real artefacts present should read them back
        # verbatim, including a tokenSamples shape it has never seen
        # before (a list of dicts, not of plain ints, proving this does
        # not assume the shape).
        usage_path = project / CONTEXT_USAGE_REL
        usage_path.parent.mkdir(parents=True, exist_ok=True)
        usage_path.write_text(json.dumps({
            "main": {"context_window_size": WINDOW, "used_percentage": 12, "model": "claude-sonnet-5"},
            "tasks": {"probe-worker": {"tokenSamples": [{"t": 100}, {"t": 4200}], "peak_tokens": 4200}},
        }), encoding="utf-8")
        pointer_path = project / SESSION_POINTER_REL
        pointer_path.write_text(json.dumps({"session_id": "s1", "event": "startup"}), encoding="utf-8")
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            check(project, autocompact_readback="130000")
        out2 = buf2.getvalue()
        check_('"t": 4200' in out2, f"(d) --check should print tokenSamples verbatim whatever shape it is, got:\n{out2[:800]}")
        check_(f"context_window_size: {WINDOW}" in out2, "(d) --check should report the observed context_window_size")
        check_("| E31 |" in out2 and "130000" in out2, "(d) a supplied --autocompact-readback should appear in the FINDINGS table")
        check_('"session_id": "s1"' in out2, "(d) --check should print .claude/session.json verbatim when present")

        shutil.rmtree(project / f"bench-{TASK_ID}", ignore_errors=True)

    return (not problems, problems)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", type=Path)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--autocompact-readback", help="--check: what `/autocompact` reported on screen, "
                                                     "which no file records")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        ok, problems = _selftest(verbose=args.json)
        if ok:
            print("selftest: PASS, 4 scenarios")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    if not (args.prepare or args.check):
        ap.error("pass --prepare, --check or --selftest")
    if not args.project:
        ap.error("--project is required for --prepare/--check")

    project = args.project.expanduser().resolve()
    if args.prepare:
        prepare(project)
    else:
        check(project, args.autocompact_readback)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
