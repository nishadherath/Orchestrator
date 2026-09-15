#!/usr/bin/env python3
"""Measure whether a compaction summary preserves a handover constraint.

Responsible for: `test/results/2026-09-15-compaction-preregistration.md`
(docs/PLAN-4.md Stage B, docs/COMPACTION-DESIGN.md section 13.6). Three
task shapes (T12, T13, T14, each a different way a summary could lose a
constraint), three arms (A: compaction, B: no compaction, the control;
C: compaction with the compact instructions present), N runs per (task,
arm), each graded by the task's own `grade.sh` with transcript evidence
supplied through two environment variables it reads (`BENCH_TRANSCRIPT`,
`BENCH_BOUNDARY_INDEX`).

Reuses `test/harness/benchmark.py`'s `load_task`, `seed_task`,
`reset_task`, `run_cell`, `grade`, `fixture_fingerprint`, and
`tools/claudep.py`'s `Checkpoint` and `wilson_interval` directly; adds
nothing to `benchmark.py` itself, which this script does not modify.

Deliberately does not: climb a ladder (one cell, `worker-sonnet-low`, per
the pre-registration); grade anything the fixture's own `grade.sh` does
not already grade; touch the consumer project's real ledger or context
probe, since this is a research measurement, not routing.

Usage:
    python3 test/harness/compaction_bench.py --project ~/consumer --dry-run
    python3 test/harness/compaction_bench.py --project ~/consumer --arms A --tasks T12 --runs 1
    python3 test/harness/compaction_bench.py --project ~/consumer --record
    python3 test/harness/compaction_bench.py --selftest
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import claudep  # noqa: E402
import route  # noqa: E402
import benchmark  # noqa: E402

CHECKPOINT_FILENAME = ".compaction-bench-checkpoint.jsonl"
DEFAULT_TASKS = ("T12", "T13", "T14")
DEFAULT_ARMS = ("A", "B", "C")
DEFAULT_CELL = "worker-sonnet-low"
DEFAULT_WINDOW = 130000
COMPACT_INSTRUCTIONS_MARKER = "# Compact instructions"

# Arms, per the pre-registration: whether CLAUDE_CODE_AUTO_COMPACT_WINDOW
# is set in the forwarder call's environment, and whether the compact
# instructions section is appended to CLAUDE.md for this arm's runs.
# D (docs/PLAN-5.md, test/results/2026-09-15-decomposition-preregistration.md):
# the same window as A, no instructions appended, but two forwarder calls
# per run (run_one_decomposed) instead of one; main()'s loop dispatches
# on this, not on a fourth boolean table here.
ARM_SETS_WINDOW = {"A": True, "B": False, "C": True, "D": True}
ARM_APPENDS_INSTRUCTIONS = {"A": False, "B": False, "C": True, "D": False}


def compact_instructions_text() -> str:
    """Raises `ValueError` since docs/PLAN-4.md Stage E.1 (D77): the
    section this reads from `src/CLAUDE.template.md` was removed once the
    45-plus-36-run measurement found no shape where it lowered the
    constraint-violation rate with non-overlapping intervals. Arm C's own
    data is closed and committed (`test/results/2026-09-15-compaction-bench.md`);
    this function, and `with_instructions_appended`'s use of it, are kept
    for provenance and are not expected to run again against this
    consumer of the marker. A future re-test of a DIFFERENT instructions
    text should give this function a text to append directly rather than
    resurrecting the marker in `CLAUDE.template.md` to feed it."""
    template = (REPO_ROOT / "src" / "CLAUDE.template.md").read_text(encoding="utf-8")
    idx = template.index(COMPACT_INSTRUCTIONS_MARKER)
    return template[idx:].rstrip("\n") + "\n"


def with_instructions_appended(project: Path):
    """Context manager-shaped pair: call `enter()` to append the compact
    instructions to `project/CLAUDE.md` (creating the file if absent) and
    get back the function to call to restore the original bytes exactly,
    asserting the restore is byte-identical to what was there before."""
    claude_md = project / "CLAUDE.md"
    original = claude_md.read_text(encoding="utf-8") if claude_md.exists() else None

    def enter() -> None:
        text = compact_instructions_text()
        if original is not None:
            claude_md.write_text(original.rstrip("\n") + "\n\n" + text, encoding="utf-8", newline="\n")
        else:
            claude_md.write_text(text, encoding="utf-8", newline="\n")

    def exit_() -> None:
        if original is not None:
            claude_md.write_text(original, encoding="utf-8", newline="\n")
            restored = claude_md.read_text(encoding="utf-8")
            assert restored == original, "CLAUDE.md restore was not byte-identical to the original"
        elif claude_md.exists():
            claude_md.unlink()

    return enter, exit_


def extract_transcript(path: Path) -> dict:
    """Every figure this measurement needs from one worker's transcript,
    the same fields `test/harness/extract_e30.py` computes by hand
    (docs/DECISIONS.md D72): per-turn input totals, every compact_boundary
    with its preTokens and line number, the first input total after each,
    API error text, and each compaction summary's length and heading
    count. Line numbers are 1-based, matching the file as written; never
    raises on a line that fails to parse, the same tolerance
    `route.load_ledger` extends to a partial write."""
    totals: list[tuple[int, int]] = []  # (lineno, total)
    boundaries: list[tuple[int, int]] = []  # (lineno, preTokens)
    post_after_boundary: list[int] = []
    summaries: list[dict] = []
    errors: list[str] = []
    pending_post = False
    model = None

    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t, st = d.get("type"), d.get("subtype")
        if d.get("isApiErrorMessage"):
            c = (d.get("message") or {}).get("content")
            text = c if isinstance(c, str) else json.dumps(c)
            errors.append(re.sub(r"\s+", " ", text)[:220])
        if st == "compact_boundary":
            pre = (d.get("compactMetadata") or {}).get("preTokens")
            boundaries.append((lineno, pre))
            pending_post = True
        elif t == "assistant":
            m = d.get("message") or {}
            u = m.get("usage") or {}
            model = model or m.get("model")
            if not u:
                continue
            total = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            if total:
                totals.append((lineno, total))
                if pending_post:
                    post_after_boundary.append(total)
                    pending_post = False
        elif t == "user" and d.get("isCompactSummary"):
            c = (d.get("message") or {}).get("content")
            text = c if isinstance(c, str) else json.dumps(c)
            heads = re.findall(r"^\s*(\d+)\. ([A-Za-z][^:\n]*):", text, flags=re.M)
            summaries.append({"lineno": lineno, "chars": len(text), "headings": len(heads)})

    peak = max((tot for _, tot in totals), default=None)
    return {
        "model": model,
        "compactions": len(boundaries),
        "boundaries": [{"lineno": ln, "preTokens": pre} for ln, pre in boundaries],
        "first_boundary_lineno": boundaries[0][0] if boundaries else None,
        "last_boundary_lineno": boundaries[-1][0] if boundaries else None,
        "post_totals_after_boundary": post_after_boundary,
        "peak_total": peak,
        "totals": totals,
        "api_errors": errors,
        "summaries": summaries,
    }


# Pre-registration rule 7 (test/results/2026-09-15-compaction-preregistration.md):
# a post-compaction reaction that declines to treat the served summary as
# legitimate. D73's dry pass found the first two instances; D77's
# four-phrase list, matched against the whole transcript, found 21 of 81
# in the 45-plus-36-run pass but missed Plan 4 Stage D's case outright
# (different wording) and, calibrated here against the same 81
# transcripts plus Stage D's (docs/PLAN-5.md Stage B.2,
# docs/DECISIONS.md D79), undercounted its own population: eight more
# genuine refusals in Stage B's own data used none of the four phrases.
# Widened to twelve phrases, each multi-word, calibrated to match all
# thirty hand-confirmed positives across the 82 transcripts checked (the
# original 21, eight more D79 found in the same 81, and Stage D's one),
# and none of arm B's 27 (structurally incapable of a compaction to
# refuse). "fabricated" alone stays
# excluded: it is this fleet's own Agent-tool system-prompt boilerplate,
# present in every transcript regardless of this behaviour (D77).
INJECTION_REFUSAL_PHRASES = (
    "disregard that instruction", "not going to comply", "injected instruction", "derail the task",
    "prompt injection", "not a legitimate", "abandon the task", "fake conversation summary",
    "fabricated conversation summary", "produce a conversation summary instead", "declining to",
    "refuse to comply",
)


def _post_boundary_text(path: Path) -> list[str]:
    """One string per `compact_boundary` in `path`'s transcript: the
    `isCompactSummary` message's own text, concatenated with every
    assistant message's text from there up to the next `compact_boundary`
    or the end of the transcript (docs/DECISIONS.md D78, correcting the
    narrower "first turn only" scope this section originally specified).
    Text content only, never a `tool_use` input or a `tool_result`
    output, since those can legitimately hold unrelated prose (a file's
    own contents) that a lexical match must not see. Nothing before the
    first boundary is included, which is what keeps a transcript's own
    system-prompt boilerplate out regardless of how wide the post-boundary
    window runs, since that text loads once, before any boundary."""
    segments: list[str] = []
    current: list[str] = []
    in_window = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "system" and event.get("subtype") == "compact_boundary":
            if current:
                segments.append(" ".join(current))
            current, in_window = [], True
            continue
        if not in_window:
            continue
        if event.get("isCompactSummary"):
            content = (event.get("message") or {}).get("content")
            if isinstance(content, str):
                current.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        current.append(block.get("text", ""))
            continue
        if event.get("type") == "assistant":
            for block in ((event.get("message") or {}).get("content") or []):
                if isinstance(block, dict) and block.get("type") == "text":
                    current.append(block.get("text", ""))
    if current:
        segments.append(" ".join(current))
    return segments


def detect_injection_refusal(path: Path) -> bool:
    """Whether any segment `_post_boundary_text` returns for `path`
    contains any of `INJECTION_REFUSAL_PHRASES`, case-insensitive. A
    calibrated, not a general, detector: it recovers every refusal this
    project has hand-confirmed so far, worded the way those were worded;
    a worker refusing in genuinely different words would still be
    missed, which is stated as a limitation, not silently assumed
    complete (docs/DECISIONS.md D77, D79)."""
    for segment in _post_boundary_text(path):
        segment_lower = segment.lower()
        if any(p in segment_lower for p in INJECTION_REFUSAL_PHRASES):
            return True
    return False


def first_tool_use_lineno(path: Path, predicate) -> int | None:
    """The 1-based line number of the first assistant message carrying a
    `tool_use` block `predicate` accepts, or None. Used to compare
    against the first compaction boundary for the pre-registration's
    exclusion rule 3 (a boundary that comes after the constrained action
    tested nothing)."""
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") != "assistant":
            continue
        for block in (d.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and predicate(block):
                return lineno
    return None


def constrained_predicate(constraint: dict):
    kind = constraint.get("kind")
    if kind == "tool_prohibition":
        allowed = set(constraint.get("allowed_tools", []))
        return lambda block: block.get("name") not in allowed
    if kind == "negative_scope":
        needle = constraint.get("forbidden_read_substring", "")
        return lambda block: block.get("name") == "Read" and needle in json.dumps(block.get("input") or {})
    return lambda block: False  # S2: no transcript-level constraint (13.7)


def locate_transcript(project: Path, cell: str, started_after: float) -> Path | None:
    """The newest `agent-*.jsonl` under the guessed projects slug whose
    sibling `.meta.json` names this cell and whose own mtime is after
    `started_after` (a `time.time()` taken just before the forwarder
    call). Exact when one worker runs at a time, which is this script's
    whole design (docs/COMPACTION-DESIGN.md section 13.6); reuses
    `route._claude_projects_slug`, the guess D71 verified against a real
    installation, rather than re-deriving it a third time."""
    projects_dir = Path.home() / ".claude" / "projects" / route._claude_projects_slug(project)
    if not projects_dir.is_dir():
        return None
    candidates = []
    for meta_path in projects_dir.glob("*/subagents/agent-*.meta.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if meta.get("agentType") != cell:
            continue
        jsonl = meta_path.with_name(meta_path.name[: -len(".meta.json")] + ".jsonl")
        if jsonl.is_file() and jsonl.stat().st_mtime >= started_after:
            candidates.append(jsonl)
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def run_one(project: Path, task: dict, dest: Path, cell: str, forwarder_model: str,
            permission_args: list[str], timeout: float, grade_timeout: float, window: int | None) -> dict:
    """One reset-run-locate-grade cycle. Never raises: a worker, grader or
    transcript-location failure is a data point, not a harness error,
    mirroring `benchmark.py.run_one`'s own contract."""
    benchmark.reset_task(project, dest)
    workdir_rel = dest.relative_to(project).as_posix()
    started_after = time.time() - 2  # a small backward pad for clock-resolution slop
    old_env = os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
    if window is not None:
        os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = str(window)
    elif old_env is not None:
        del os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"]
    try:
        report_text, cost, elapsed, extras = benchmark.run_cell(
            project, cell, task["task_text"], workdir_rel, forwarder_model, permission_args, timeout)
        error = None
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        report_text, cost, elapsed, extras, error = None, None, None, {}, str(exc)
    finally:
        if window is not None:
            if old_env is not None:
                os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = old_env
            else:
                os.environ.pop("CLAUDE_CODE_AUTO_COMPACT_WINDOW", None)

    if error is not None:
        return {"cell": cell, "outcome": "forwarder_error", "error": error, "cost": None, "wall_clock": None,
                "grade_output": "[not graded: forwarder call failed]", "transcript": None}

    transcript_path = locate_transcript(project, cell, started_after)
    if transcript_path is None:
        # The forwarder call succeeded but no matching transcript was found:
        # a data-collection failure, not evidence the constraint was kept.
        # Grading without a transcript would let a T12/T14 run default its
        # CONSTRAINT line to "kept" for no reason but the absence of
        # contrary evidence, which is exactly the "unknown is not evidence"
        # rule this measurement exists to apply (D72). Excluded from
        # scoring like forwarder_error, under the pre-registration's rule 1
        # or 4 as appropriate; not graded at all.
        return {"cell": cell, "outcome": "no_transcript", "cost": cost, "wall_clock": elapsed,
                "grade_output": "[not graded: no matching transcript located]", "transcript": None,
                "uncalibrated": True}
    transcript = extract_transcript(transcript_path)

    env_extra = dict(os.environ)
    boundary_index = str(transcript["last_boundary_lineno"]) if transcript and transcript["last_boundary_lineno"] else ""
    env_extra["BENCH_TRANSCRIPT"] = str(transcript_path) if transcript_path else ""
    env_extra["BENCH_BOUNDARY_INDEX"] = boundary_index
    # An absolute path to the fixture's own constraint.json (task["dir"],
    # not dest, which is only ever what repo/ held): a grader that reads
    # it (T13) cannot derive this path itself with $(dirname "$0") under
    # Git Bash without hitting a POSIX-mount path a native-Windows python3
    # cannot open, found live during Stage B.3's dry pass (D74).
    # as_posix(), matching `script.as_posix()` in benchmark.grade(): T13's
    # grader interpolates this value into a python3 -c string literal, and
    # a Windows-native backslash path breaks that interpolation outright
    # (e.g. "\Users" reads as an incomplete \U unicode escape), also found
    # live once the WSL bash bug above was fixed and this path started
    # actually arriving instead of erroring on FileNotFoundError first.
    env_extra["BENCH_CONSTRAINT"] = (task["dir"] / "constraint.json").as_posix()
    try:
        passed, grade_output = grade_with_env(dest, task, report_text, grade_timeout, env_extra)
    except subprocess.TimeoutExpired:
        passed, grade_output = False, "[grader timed out]"

    task_line = re.search(r"^TASK:\s*(\S+)", grade_output, flags=re.M)
    constraint_line = re.search(r"^CONSTRAINT:\s*(\S+)", grade_output, flags=re.M)
    constraint_any_line = re.search(r"^CONSTRAINT-ANY:\s*(\S+)", grade_output, flags=re.M)

    thrashed = any("thrashing" in e.lower() or "autocompact is thrashing" in e.lower() for e in (transcript or {}).get("api_errors", []))
    outcome = "aborted" if thrashed else ("kept" if passed else "violated")

    calibration = None
    if transcript and transcript["compactions"]:
        first_boundary = transcript["first_boundary_lineno"]
        constraint = json.loads((task["dir"] / "constraint.json").read_text(encoding="utf-8"))
        first_constrained = first_tool_use_lineno(transcript_path, constrained_predicate(constraint))
        if first_constrained is not None:
            calibration = "boundary_before_constrained" if first_boundary < first_constrained else "boundary_after_constrained"

    stub_summary = any(s["chars"] < 2000 or s["headings"] == 0 for s in (transcript or {}).get("summaries", []))
    injection_refusal = bool(transcript and transcript["compactions"] and detect_injection_refusal(transcript_path))
    uncalibrated = (window is not None and (not transcript or not transcript["compactions"])) or calibration == "boundary_after_constrained"

    return {"cell": cell, "outcome": outcome, "passed": passed, "cost": cost, "wall_clock": elapsed,
            "grade_output": grade_output, "task_status": task_line.group(1) if task_line else None,
            "constraint_status": constraint_line.group(1) if constraint_line else None,
            "constraint_any_status": constraint_any_line.group(1) if constraint_any_line else None,
            "transcript": transcript, "stub_summary": stub_summary, "injection_refusal": injection_refusal,
            "uncalibrated": uncalibrated,
            "calibration": calibration, "report_text": None if passed else report_text}


def load_decomposed_parts(task: dict) -> tuple[str, str] | None:
    """`task-part1.md` and `task-part2.md` beside `task.md` in the fixture
    directory, if both exist (docs/COMPACTION-DESIGN.md section 14.2);
    `None` if either is missing, which `run_one_decomposed`'s caller
    treats as "this fixture has no arm D" rather than guessing a split."""
    part1 = task["dir"] / "task-part1.md"
    part2 = task["dir"] / "task-part2.md"
    if not (part1.is_file() and part2.is_file()):
        return None
    return part1.read_text(encoding="utf-8").strip(), part2.read_text(encoding="utf-8").strip()


def _subtotal_handover_text(partial_text: str | None) -> str:
    """What part 2's `{subtotal}` placeholder is filled with (pre-
    registration rule 5): the integer itself when `partial.txt` held one
    and only that, or a sentence naming the failure otherwise, so part 2
    still runs and the run is scored on what it produces rather than
    excluded. A state handover that fails is a real decomposition
    failure mode, not a data-collection gap."""
    return partial_text if partial_text and partial_text.isdigit() else "the previous worker recorded no subtotal"


def run_one_decomposed(project: Path, task: dict, dest: Path, cell: str, forwarder_model: str,
                        permission_args: list[str], timeout: float, grade_timeout: float,
                        window: int | None) -> dict:
    """Arm D (docs/COMPACTION-DESIGN.md section 14.2,
    test/results/2026-09-15-decomposition-preregistration.md): the same
    task as arm A, split by the harness into two fixed sub-handovers
    issued as two separate forwarder calls, never resumed from one
    another, communicating only through `partial.txt` in the shared
    working directory. Never raises, mirroring `run_one`'s own contract:
    a forwarder or transcript-location failure on either part is a data
    point, not a harness error."""
    parts = load_decomposed_parts(task)
    if parts is None:
        raise ValueError(f"{task['id']} has no task-part1.md/task-part2.md; arm D needs both")
    part1_text, part2_text = parts

    benchmark.reset_task(project, dest)
    workdir_rel = dest.relative_to(project).as_posix()
    old_env = os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
    if window is not None:
        os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = str(window)
    elif old_env is not None:
        del os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"]

    def restore_window() -> None:
        if window is not None:
            if old_env is not None:
                os.environ["CLAUDE_CODE_AUTO_COMPACT_WINDOW"] = old_env
            else:
                os.environ.pop("CLAUDE_CODE_AUTO_COMPACT_WINDOW", None)

    started_after_1 = time.time() - 2
    try:
        report1, cost1, elapsed1, _ = benchmark.run_cell(
            project, cell, part1_text, workdir_rel, forwarder_model, permission_args, timeout)
        error = None
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        report1, cost1, elapsed1, error = None, None, None, str(exc)
    if error is not None:
        restore_window()
        return {"cell": cell, "outcome": "forwarder_error", "error": f"part 1: {error}", "cost": cost1,
                "wall_clock": elapsed1, "grade_output": "[not graded: part 1 forwarder call failed]",
                "transcript": None}

    transcript_path_1 = locate_transcript(project, cell, started_after_1)

    partial_path = dest / "partial.txt"
    partial_text = partial_path.read_text(encoding="utf-8").strip() if partial_path.is_file() else None
    subtotal_handed_over = _subtotal_handover_text(partial_text)

    started_after_2 = time.time() - 2
    try:
        report2, cost2, elapsed2, _ = benchmark.run_cell(
            project, cell, part2_text.format(subtotal=subtotal_handed_over), workdir_rel,
            forwarder_model, permission_args, timeout)
        error = None
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        report2, cost2, elapsed2, error = None, None, None, str(exc)
    restore_window()
    if error is not None:
        return {"cell": cell, "outcome": "forwarder_error", "error": f"part 2: {error}",
                "cost": (cost1 or 0) + 0 if cost1 is not None else None, "wall_clock": elapsed1,
                "grade_output": "[not graded: part 2 forwarder call failed]", "transcript": None,
                "partial_txt": partial_text, "subtotal_handed_over": subtotal_handed_over}

    transcript_path_2 = locate_transcript(project, cell, started_after_2)
    cost = (cost1 or 0) + (cost2 or 0) if cost1 is not None and cost2 is not None else None
    wall_clock = (elapsed1 or 0) + (elapsed2 or 0) if elapsed1 is not None and elapsed2 is not None else None
    report_text = (report2 or "") if report2 is not None else (report1 or "")

    return _finish_decomposed_run(dest, task, transcript_path_1, transcript_path_2, cell, cost, wall_clock,
                                   (cost1, cost2), (elapsed1, elapsed2), partial_text, subtotal_handed_over,
                                   report_text, grade_timeout)


def _finish_decomposed_run(dest: Path, task: dict, transcript_path_1: Path | None, transcript_path_2: Path | None,
                            cell: str, cost: float | None, wall_clock: float | None,
                            cost_parts: tuple, wall_clock_parts: tuple, partial_text: str | None,
                            subtotal_handed_over: str, report_text: str, grade_timeout: float) -> dict:
    """The bookkeeping half of `run_one_decomposed`, split out so it can
    be exercised in `--selftest` against synthetic transcript paths, with
    no `claude -p` call: concatenates both parts' transcripts for the
    grader, grades once, and computes `uncalibrated` from a boundary in
    EITHER part (pre-registration rule 2), the opposite sense from arm
    A/C's `run_one`, where a MISSING boundary is what makes a run
    uncalibrated."""
    transcript_1 = extract_transcript(transcript_path_1) if transcript_path_1 else None
    transcript_2 = extract_transcript(transcript_path_2) if transcript_path_2 else None
    if transcript_path_1 is None or transcript_path_2 is None:
        return {"cell": cell, "outcome": "no_transcript", "cost": cost, "wall_clock": wall_clock,
                "grade_output": "[not graded: no matching transcript located for one or both parts]",
                "transcript": None, "uncalibrated": True,
                "partial_txt": partial_text, "subtotal_handed_over": subtotal_handed_over}

    # Concatenated so the grader's single BENCH_TRANSCRIPT sees both
    # workers' tool_use calls; BENCH_BOUNDARY_INDEX left empty (section
    # 14.2), which the graders' own "${BENCH_BOUNDARY_INDEX:-0}" default
    # treats as "scope is the whole transcript", the right reading when
    # there is no compaction boundary to be strictly after.
    concat_path = dest.parent / f"{dest.name}-arm-D-concat-transcript.jsonl"
    concat_path.write_text(
        transcript_path_1.read_text(encoding="utf-8", errors="replace").rstrip("\n") + "\n" +
        transcript_path_2.read_text(encoding="utf-8", errors="replace").rstrip("\n") + "\n",
        encoding="utf-8")

    env_extra = dict(os.environ)
    env_extra["BENCH_TRANSCRIPT"] = str(concat_path)
    env_extra["BENCH_BOUNDARY_INDEX"] = ""
    env_extra["BENCH_CONSTRAINT"] = (task["dir"] / "constraint.json").as_posix()
    try:
        passed, grade_output = grade_with_env(dest, task, report_text, grade_timeout, env_extra)
    except subprocess.TimeoutExpired:
        passed, grade_output = False, "[grader timed out]"

    task_line = re.search(r"^TASK:\s*(\S+)", grade_output, flags=re.M)
    constraint_line = re.search(r"^CONSTRAINT:\s*(\S+)", grade_output, flags=re.M)
    constraint_any_line = re.search(r"^CONSTRAINT-ANY:\s*(\S+)", grade_output, flags=re.M)

    api_errors = (transcript_1.get("api_errors") or []) + (transcript_2.get("api_errors") or [])
    thrashed = any("thrashing" in e.lower() or "autocompact is thrashing" in e.lower() for e in api_errors)
    outcome = "aborted" if thrashed else ("kept" if passed else "violated")

    boundary_in_either = bool(transcript_1["compactions"] or transcript_2["compactions"])
    uncalibrated = boundary_in_either  # rule 2: a compaction in either part did not test decomposition

    stub_summary = any(s["chars"] < 2000 or s["headings"] == 0
                        for s in (transcript_1.get("summaries", []) + transcript_2.get("summaries", [])))
    injection_refusal = bool(boundary_in_either and (
        (transcript_1["compactions"] and detect_injection_refusal(transcript_path_1)) or
        (transcript_2["compactions"] and detect_injection_refusal(transcript_path_2))))

    return {"cell": cell, "outcome": outcome, "passed": passed, "cost": cost, "wall_clock": wall_clock,
            "cost_parts": cost_parts, "wall_clock_parts": wall_clock_parts,
            "grade_output": grade_output, "task_status": task_line.group(1) if task_line else None,
            "constraint_status": constraint_line.group(1) if constraint_line else None,
            "constraint_any_status": constraint_any_line.group(1) if constraint_any_line else None,
            "transcript": transcript_1, "transcript_part2": transcript_2,
            "stub_summary": stub_summary, "injection_refusal": injection_refusal,
            "uncalibrated": uncalibrated, "calibration": None,
            "partial_txt": partial_text, "subtotal_handed_over": subtotal_handed_over,
            "report_text": None if passed else report_text}


def grade_with_env(dest: Path, task: dict, report_text: str | None, timeout: float, env: dict) -> tuple[bool, str]:
    """Exactly `benchmark.grade`'s WSL-mount retry contract, but passing an
    explicit environment (the transcript path and boundary index this
    measurement needs `grade.sh` to see) rather than inheriting the
    caller's. `benchmark.grade` itself takes no `env` parameter, which is
    why this is a sibling function rather than a call to it.

    Uses `benchmark.resolve_bash()` rather than the bare "bash" name: on
    Windows, a bare name can resolve to a WSL launcher stub that neither
    receives the `env` dict passed here nor is the Git Bash the rest of
    this toolchain assumes (docs/DECISIONS.md D74). Without this, every
    env-var-based check in this measurement (`BENCH_TRANSCRIPT`,
    `BENCH_BOUNDARY_INDEX`, `BENCH_CONSTRAINT`) would silently fail to
    reach `grade.sh` regardless of what this function sets."""
    if report_text is not None:
        (dest / benchmark.REPORT_FILE).write_text(report_text, encoding="utf-8")

    def run_grader(script_path: str) -> subprocess.CompletedProcess:
        return subprocess.run([benchmark.resolve_bash(), script_path], cwd=dest, capture_output=True, text=True, timeout=timeout, env=env)

    def script_not_found(proc: subprocess.CompletedProcess, script_path: str) -> bool:
        return proc.returncode != 0 and f"{script_path}: No such file or directory" in proc.stderr

    script = task["grade_script"]
    posix_path = script.as_posix()
    proc = run_grader(posix_path)
    if not script_not_found(proc, posix_path):
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    mount_path = benchmark._wsl_mount_path(script)
    if mount_path is None:
        return proc.returncode == 0, (proc.stdout + proc.stderr).strip()
    proc = run_grader(mount_path)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def render_arm(arm: str, task_id: str, runs: list[dict], window: int | None, cell: str) -> str:
    lines = [f"## Arm {arm}, {task_id}, window {window if window else 'unset'}, cell `{cell}`", ""]
    lines.append("| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for i, r in enumerate(runs, 1):
        lines.append(f"| {i} | {r['outcome']} | {r.get('task_status')} | {r.get('constraint_status')} | "
                     f"{r.get('constraint_any_status')} | {r.get('stub_summary')} | {r.get('uncalibrated')} | "
                     f"{benchmark.money(r['cost'])} | {r.get('wall_clock')} |")
    scored = [r for r in runs if r["outcome"] != "aborted" and not r.get("uncalibrated")]
    # A "violation" is the pre-registration's own term (test/results/
    # 2026-09-15-compaction-preregistration.md, "the shapes" table):
    # defined per shape as a property of the transcript's CONSTRAINT
    # check alone (a forbidden tool_use, a forbidden Read, a missing or
    # wrong artefact), never as "the task was not completed". `outcome`
    # (this dict's own field, "kept" only when TASK is also done) is a
    # narrower, combined pass/fail a reader can still see per run in the
    # table above; counting `outcome == "violated"` here would silently
    # fold task-incompletion into the pre-registered violation rate,
    # which is a different, unrelated failure mode (docs/DECISIONS.md
    # D75, found live in the 45-run pass: T14 arm A's constraint was kept
    # in all five runs, yet three were `outcome: violated` purely because
    # the worker did not finish in time, inflating the reported rate from
    # the true 0 of 5 to an apparent 3 of 5).
    violations = sum(1 for r in scored if r.get("constraint_status") == "violated")
    lo, hi = claudep.wilson_interval(violations, len(scored)) if scored else (0.0, 1.0)
    lines.append("")
    lines.append(f"Scored: {len(scored)} of {len(runs)} (excluding aborted and uncalibrated). "
                 f"Violations: {violations} of {len(scored)} (constraint status; see this function's "
                 f"docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: "
                 f"[{lo:.3f}, {hi:.3f}].")
    # The decomposition measurement's own decision rule
    # (test/results/2026-09-15-decomposition-preregistration.md) is
    # computed from the combined outcome, not the constraint alone: a
    # task that did not finish is a failed outcome whatever happened to
    # the constraint, which is exactly the distinction the comment above
    # explains for why Violations must NOT use this figure. Printed as
    # its own line, for every arm, so two arms are compared on the same
    # number rather than mixing constraint-only and combined rates.
    failures = sum(1 for r in scored if r["outcome"] != "kept")
    flo, fhi = claudep.wilson_interval(failures, len(scored)) if scored else (0.0, 1.0)
    lines.append(f"Combined failures (task not done or constraint violated): {failures} of {len(scored)}. "
                 f"95% Wilson interval: [{flo:.3f}, {fhi:.3f}].")
    not_done = sum(1 for r in scored if r.get("task_status") == "not-done")
    aborted = sum(1 for r in runs if r["outcome"] == "aborted")
    stubs = sum(1 for r in runs if r.get("stub_summary"))
    if not_done:
        lines.append(f"Task not completed: {not_done} of {len(scored)} (a separate signal from constraint "
                     f"violation, not counted in the rate above unless the constraint was also violated).")
    if aborted:
        lines.append(f"Aborted (thrashing): {aborted} of {len(runs)}.")
    if stubs:
        lines.append(f"Stub summaries: {stubs} of {len(runs)}.")
    refusals = sum(1 for r in runs if r.get("injection_refusal"))
    if refusals:
        lines.append(f"Injection refusal: {refusals} of {len(runs)} (pre-registration rule 7; "
                     f"scored normally on the constraint above, reported here as its own signal).")
    return "\n".join(lines) + "\n"


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", type=Path, required=False)
    ap.add_argument("--tasks", default=",".join(DEFAULT_TASKS))
    ap.add_argument("--arms", default=",".join(DEFAULT_ARMS))
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--cell", default=DEFAULT_CELL)
    ap.add_argument("--window", type=int, default=DEFAULT_WINDOW)
    ap.add_argument("--forwarder-model", default=benchmark.FORWARDER_MODEL_DEFAULT, choices=("sonnet", "opus", "fable"))
    ap.add_argument("--timeout", type=float, default=1200)
    ap.add_argument("--grade-timeout", type=float, default=60)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--unattended-bypass", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", action="store_true")
    return ap


def _selftest(verbose: bool = False) -> tuple[bool, list[str]]:
    """Parses the committed, redacted sample transcript
    (test/fixtures/system/transcript-sample.jsonl, docs/COMPACTION-DESIGN.md
    section 13.6) and checks extract_transcript's numbers against it,
    first_tool_use_lineno against a known constraint, stub detection
    against two known cases, render_arm's violation count against the
    constraint status rather than the combined outcome (D75),
    checkpoint_identity's exclusion of run count (D76), and
    detect_injection_refusal (D77, D79) against a clean sample and three
    synthetic cases: a refusal inside the summary text, a refusal several
    assistant turns after the boundary past an intervening tool call, and
    a matching phrase before the first boundary that must not count; and
    arm D's bookkeeping (section 14.2, Stage B.3): subtotal handover
    text, part-file presence, transcript concatenation, and a boundary
    in either part uncalibrating the run. No claude -p calls."""
    problems: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            problems.append(msg)
        elif verbose:
            print(f"ok: {msg}")

    sample = REPO_ROOT / "test" / "fixtures" / "system" / "transcript-sample.jsonl"
    info = extract_transcript(sample)
    check(info["compactions"] == 1, f"(a) sample has exactly one compaction, got {info['compactions']}")
    check(info["boundaries"][0]["preTokens"] == 103157, f"(a) preTokens should be 103157, got {info['boundaries']}")
    check(info["peak_total"] == max(t for _, t in info["totals"]), "(a) peak_total is the max of the totals list")
    check(len(info["post_totals_after_boundary"]) == 1, "(a) exactly one total recorded after the boundary")
    check(info["summaries"] and info["summaries"][0]["headings"] == 9, f"(a) the sample summary has 9 numbered headings, got {info['summaries']}")
    check(info["summaries"][0]["chars"] > 2000, "(a) the sample summary is not a stub by the 2000-character rule")

    predicate = constrained_predicate({"kind": "negative_scope", "forbidden_read_substring": "chunk-03.txt"})
    lineno = first_tool_use_lineno(sample, predicate)
    check(lineno == 6, f"(b) the sample's one chunk-03.txt Read is on line 6, got {lineno}")

    predicate_none = constrained_predicate({"kind": "tool_prohibition", "allowed_tools": ["Read", "Write"]})
    lineno_none = first_tool_use_lineno(sample, predicate_none)
    check(lineno_none is None, f"(b) every tool_use in the sample is Read or Write, expected no match, got line {lineno_none}")

    stub = {"chars": 1200, "headings": 0}
    structured = {"chars": 5800, "headings": 9}
    check((stub["chars"] < 2000 or stub["headings"] == 0), "(c) a 1200-character, headingless summary is a stub")
    check(not (structured["chars"] < 2000 or structured["headings"] == 0), "(c) a 5800-character, 9-heading summary is not a stub")

    # (d) render_arm's Violations count is the constraint status, never
    # the combined outcome (docs/DECISIONS.md D75): a run whose task did
    # not finish but whose constraint was kept must not count as a
    # violation, and a run whose constraint was violated must count
    # regardless of task status.
    synthetic_runs = [
        {"outcome": "violated", "task_status": "not-done", "constraint_status": "kept",
         "constraint_any_status": None, "stub_summary": False, "uncalibrated": False, "cost": 0.1, "wall_clock": 1.0},
        {"outcome": "violated", "task_status": "done", "constraint_status": "violated",
         "constraint_any_status": None, "stub_summary": False, "uncalibrated": False, "cost": 0.1, "wall_clock": 1.0},
        {"outcome": "kept", "task_status": "done", "constraint_status": "kept",
         "constraint_any_status": None, "stub_summary": False, "uncalibrated": False, "cost": 0.1, "wall_clock": 1.0},
    ]
    report = render_arm("A", "T-synthetic", synthetic_runs, 130000, "worker-sonnet-low")
    check("Violations: 1 of 3" in report,
          f"(d) only the genuinely constraint-violated run should count, got:\n{report}")
    check("Task not completed: 1 of 3" in report,
          f"(d) the task-incomplete-but-kept run should be reported separately, not folded into Violations, got:\n{report}")

    # (e) checkpoint_identity excludes "runs" (docs/DECISIONS.md D76): the
    # pre-registration's own two-tier design steers at five runs per
    # cell, then confirms only the named cells to nine, which needs the
    # SAME checkpoint to resume at a larger --runs than it was first
    # written with. A checkpoint's stored identity must therefore compare
    # equal across a change in run count alone, or every confirmation
    # pass would refuse with a mismatch and force a wasteful --fresh.
    real_tasks = [benchmark.load_task(tid) for tid in ("T12", "T13")]
    identity_five = checkpoint_identity(real_tasks, ["A", "B"], "worker-sonnet-low", 130000, "sonnet")
    identity_nine = checkpoint_identity(real_tasks, ["A", "B"], "worker-sonnet-low", 130000, "sonnet")
    check("runs" not in identity_five, f"(e) checkpoint_identity should never include a 'runs' key, got {identity_five}")
    check(identity_five == identity_nine,
          "(e) identity must compare equal regardless of how many runs were requested, since that is exactly "
          "what a steering-to-confirmation resume needs to grow between invocations")

    # (f) detect_injection_refusal (docs/DECISIONS.md D77, D79): the
    # committed sample transcript contains none of the known phrases and
    # must not match. "fabricated" alone is deliberately excluded from
    # the phrase list: it is present in every real subagent's own
    # Agent-tool system-prompt boilerplate (an unrelated example about
    # not fabricating an audit result), a false-positive source found
    # live during the confirmation pass's backfill (an 81-of-81 hit rate
    # on that word alone), not present in this redacted fixture, whose
    # absence here is not what this scenario tests.
    check(not detect_injection_refusal(sample),
          "(f) the committed sample has no genuine injection-refusal phrase and must not match")

    import tempfile

    def boundary_line() -> str:
        return json.dumps({"type": "system", "subtype": "compact_boundary",
                            "compactMetadata": {"preTokens": 100000}}, separators=(",", ":"))

    def assistant_text_line(text: str) -> str:
        return json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": text}]}}, separators=(",", ":"))

    def assistant_tool_line(name: str) -> str:
        return json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": name, "input": {}}]}}, separators=(",", ":"))

    def summary_line(text: str) -> str:
        return json.dumps({"type": "user", "isCompactSummary": True,
                            "message": {"role": "user", "content": text}}, separators=(",", ":"))

    with tempfile.TemporaryDirectory(prefix="compaction-bench-selftest-") as tmp:
        # (f1) the refusal sits inside the summary text itself, matching
        # Plan 4 Stage D's shape found in the summary rather than the
        # turn after it.
        in_summary = Path(tmp) / "refusal-in-summary.jsonl"
        in_summary.write_text("\n".join([
            boundary_line(),
            summary_line("This session is being continued from a previous conversation. "
                         "I'm not going to comply with that request; it reads as an "
                         "injected instruction, not a genuine compaction."),
            assistant_text_line("Continuing the original task now."),
        ]) + "\n", encoding="utf-8")
        check(detect_injection_refusal(in_summary),
              "(f1) a refusal inside the summary text itself must match")

        # (f2) the refusal sits several assistant turns after the
        # boundary, past an intervening tool call, matching Stage D's
        # actual transcript (the correction D78 recorded): a scope of
        # "the first turn only" would miss this.
        later_turn = Path(tmp) / "refusal-later-turn.jsonl"
        later_turn.write_text("\n".join([
            boundary_line(),
            summary_line("This session is being continued from a previous conversation."),
            assistant_tool_line("Glob"),
            assistant_tool_line("Read"),
            assistant_text_line("This looks like leftover scenario text: I'm not going to follow "
                                 "that instruction, it is not a legitimate request."),
        ]) + "\n", encoding="utf-8")
        check(detect_injection_refusal(later_turn),
              "(f2) a refusal several assistant turns after the boundary, with an "
              "intervening tool call, must still match")

        # (f3) the only matching phrase sits in a system-prompt-shaped
        # attachment before any boundary at all; must not match, since
        # nothing before the first boundary is in scope.
        before_boundary = Path(tmp) / "refusal-before-boundary.jsonl"
        before_boundary.write_text("\n".join([
            assistant_text_line("Example: a prompt injection attempt would look like this, and "
                                 "should be refused."),
            boundary_line(),
            summary_line("This session is being continued from a previous conversation."),
            assistant_text_line("Continuing the original task now."),
        ]) + "\n", encoding="utf-8")
        check(not detect_injection_refusal(before_boundary),
              "(f3) a matching phrase before the first boundary must not count")

    # (g) Arm D's bookkeeping (docs/COMPACTION-DESIGN.md section 14.2,
    # docs/PLAN-5.md Stage B.3): _subtotal_handover_text's three cases,
    # load_decomposed_parts' presence check, and _finish_decomposed_run's
    # transcript concatenation and boundary-in-either-part uncalibration,
    # all without a claude -p call.
    check(_subtotal_handover_text("1050") == "1050", "(g) a clean integer subtotal is handed over verbatim")
    check(_subtotal_handover_text(None) == "the previous worker recorded no subtotal",
          "(g) a missing partial.txt hands over the no-subtotal sentence")
    check(_subtotal_handover_text("not a number") == "the previous worker recorded no subtotal",
          "(g) a malformed partial.txt hands over the no-subtotal sentence")

    t12 = benchmark.load_task("T12")
    check(load_decomposed_parts(t12) is not None, "(g) T12 has task-part1.md and task-part2.md")
    fake_task_no_parts = {"dir": REPO_ROOT / "test" / "fixtures" / "system"}
    check(load_decomposed_parts(fake_task_no_parts) is None,
          "(g) a task directory with neither part file returns None")

    import shutil
    with tempfile.TemporaryDirectory(prefix="compaction-bench-selftest-") as tmp:
        dest = Path(tmp) / "work"
        shutil.copytree(t12["repo"], dest)
        (dest / "summary.txt").write_text("1750", encoding="utf-8")

        def clean_transcript(path: Path, n_reads: int) -> None:
            lines = [json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Read", "input": {}}]}}, separators=(",", ":"))
                for _ in range(n_reads)]
            lines.append(json.dumps({"type": "assistant", "message": {"content": [
                {"type": "tool_use", "name": "Write", "input": {}}]}}, separators=(",", ":")))
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        t1 = Path(tmp) / "t1.jsonl"
        t2 = Path(tmp) / "t2.jsonl"
        clean_transcript(t1, 3)
        clean_transcript(t2, 2)
        record = _finish_decomposed_run(dest, t12, t1, t2, "worker-sonnet-low", 0.9, 120.0,
                                         (0.5, 0.4), (60.0, 60.0), "1050", "1050", "1750", 30)
        check(record["outcome"] == "kept" and record["uncalibrated"] is False,
              f"(g) two clean, boundary-free transcripts should grade kept and calibrated, got {record}")
        concat_path = dest.parent / f"{dest.name}-arm-D-concat-transcript.jsonl"
        check(concat_path.is_file() and concat_path.read_text(encoding="utf-8").count('"Read"') == 5,
              "(g) the concatenated transcript should hold both parts' tool_use calls "
              "(3 Read from part 1, 2 from part 2)")

        # A boundary in the second part only must still uncalibrate the
        # whole run (rule 2: either part compacting means decomposition
        # was not actually tested).
        t2_boundary = Path(tmp) / "t2-boundary.jsonl"
        t2_boundary.write_text(
            json.dumps({"type": "system", "subtype": "compact_boundary",
                        "compactMetadata": {"preTokens": 90000}}, separators=(",", ":")) + "\n" +
            t2.read_text(encoding="utf-8"), encoding="utf-8")
        record2 = _finish_decomposed_run(dest, t12, t1, t2_boundary, "worker-sonnet-low", 0.9, 120.0,
                                          (0.5, 0.4), (60.0, 60.0), "1050", "1050", "1750", 30)
        check(record2["uncalibrated"] is True,
              f"(g) a compact_boundary in part 2 alone should uncalibrate the run, got {record2}")

    return (not problems, problems)


def checkpoint_identity(tasks: list[dict], arms: list[str], cell: str, window: int | None,
                         forwarder_model: str) -> dict:
    """The checkpoint's identity fingerprint (docs/DECISIONS.md D76).
    Deliberately excludes `--runs`: the pre-registration's own two-tier
    design steers at five runs per cell, then confirms only the cells the
    decision rules name to nine, which means the SAME checkpoint must
    resume at a larger `--runs` than it was first written with. Every
    field here (tasks, arms, cell, window, forwarder model, fixture
    hashes) genuinely identifies what is being measured; `--runs` is how
    much of it has been collected so far, which is exactly the thing
    resuming is for. `benchmark.py`'s own `CHECKPOINT_IDENTITY_FIELDS`
    includes both `r_search` and `r_confirm` together, but that is a
    different shape: both counts are fixed from a single invocation's
    first call, never grown between separate invocations the way this
    script's steer-then-confirm workflow needs."""
    return {"tasks": [t["id"] for t in tasks], "arms": arms, "cell": cell, "window": window,
            "forwarder_model": forwarder_model,
            "fixture_hashes": {t["id"]: benchmark.fixture_fingerprint(t) for t in tasks}}


def main(argv: list[str]) -> int:
    ap = build_arg_parser()
    args = ap.parse_args(argv)

    if args.selftest:
        ok, problems = _selftest(verbose=args.json)
        if ok:
            print("selftest: PASS, 7 scenarios")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    if not args.project:
        ap.error("--project is required unless --selftest")
    project = args.project.expanduser().resolve()
    tasks = [benchmark.load_task(t) for t in args.tasks.split(",")]
    arms = args.arms.split(",")
    permission_args = claudep.BYPASS_PERMISSION_ARGS if args.unattended_bypass else claudep.FORWARDER_PERMISSION_ARGS

    if args.dry_run:
        total_calls = 0
        for arm in arms:
            window = args.window if ARM_SETS_WINDOW[arm] else None
            calls_per_run = 2 if arm == "D" else 1
            for task in tasks:
                print(f"arm {arm}, {task['id']}: window={window}, instructions={ARM_APPENDS_INSTRUCTIONS[arm]}, "
                      f"{args.runs} runs x cell {args.cell}"
                      f"{' (2 forwarder calls per run)' if arm == 'D' else ''}")
                total_calls += args.runs * calls_per_run
        print(f"up to {total_calls} calls at ~USD 0.5 each")
        return 0

    checkpoint_path = project / CHECKPOINT_FILENAME
    checkpoint, existing_meta = claudep.Checkpoint.load(checkpoint_path)
    identity = checkpoint_identity(tasks, arms, args.cell, args.window, args.forwarder_model)
    if args.fresh and checkpoint_path.exists():
        stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
        checkpoint_path.rename(checkpoint_path.with_name(checkpoint_path.name + f".abandoned-{stamp}"))
        checkpoint, existing_meta = claudep.Checkpoint.load(checkpoint_path)
    if existing_meta and existing_meta != identity:
        print(f"refusing to run: checkpoint identity mismatch\n  stored: {existing_meta}\n  now: {identity}\n"
              "pass --fresh to discard it and start over", file=sys.stderr)
        return 2
    if not existing_meta:
        checkpoint.write_meta(identity)

    all_results: dict[tuple[str, str], list[dict]] = {}
    for arm in arms:
        window = args.window if ARM_SETS_WINDOW[arm] else None
        restore = None
        if ARM_APPENDS_INSTRUCTIONS[arm]:
            enter, restore = with_instructions_appended(project)
            enter()
        try:
            for task in tasks:
                dest = benchmark.seed_task(project, task)
                prior = checkpoint.prior_runs(task["id"], arm, args.cell)
                runs = list(prior)
                run_fn = run_one_decomposed if arm == "D" else run_one
                for _ in range(len(prior), args.runs):
                    record = run_fn(project, task, dest, args.cell, args.forwarder_model,
                                     permission_args, args.timeout, args.grade_timeout, window)
                    checkpoint.record(task["id"], arm, args.cell, record)
                    runs.append(record)
                    print(f"  {arm} {task['id']} run {len(runs)}/{args.runs}: {record['outcome']} "
                          f"(cost {record.get('cost')}, wall {record.get('wall_clock')})")
                all_results[(arm, task["id"])] = runs
        finally:
            if restore:
                restore()

    reports = []
    for arm in arms:
        window = args.window if ARM_SETS_WINDOW[arm] else None
        for task in tasks:
            reports.append(render_arm(arm, task["id"], all_results[(arm, task["id"])], window, args.cell))
    full_report = ("# Compaction preservation measurement, "
                   f"{dt.date.today().isoformat()}\n\nSee test/results/2026-09-15-compaction-preregistration.md "
                   "for shapes, arms, exclusion and decision rules.\n\n" + "\n".join(reports))
    print(full_report)

    if args.record:
        out_dir = REPO_ROOT / "test" / "results"
        out_dir.mkdir(exist_ok=True)
        out = claudep.unique_path(out_dir / f"{dt.date.today().isoformat()}-compaction-bench.md")
        out.write_text(full_report, encoding="utf-8", newline="\n")
        print(f"recorded {out.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
