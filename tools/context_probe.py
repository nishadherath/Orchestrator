#!/usr/bin/env python3
"""Write `.claude/context-usage.json` from Claude Code's own status line JSON,
so `tools/route.py` can read the orchestrator's context usage without a tool
that lets an agent inspect its own session (docs/PLAN-3.md Stage B,
docs/COMPACTION-DESIGN.md section 2).

Responsible for: two status line commands, wired into `statusLine` and
`subagentStatusLine` in `.claude/settings.json` (`dist/settings.fragment.json`).
`--main` reads the main status line's JSON on stdin and writes the `main`
key; `--tasks` reads the subagent status line's JSON and writes the `tasks`
key, tracking each named task's peak observed tokens across refreshes.
Each mode only ever rewrites its own key, read-modify-write via a temporary
file and rename, so a `--main` and a `--tasks` invocation racing each other
cannot clobber one another's half of the file.

Deliberately does not: read or write the routing ledger (`route.py` does
that), or assume `tokenSamples`' shape (undocumented beyond its name,
D69); it is recorded verbatim and its peak is taken by walking every
numeric value found in it, whatever shape it turns out to have. Also,
since docs/COMPACTION-DESIGN.md section 13.2 (D72), does not detect
compactions from a drop in a task's token count: that heuristic was
falsified by live transcripts (E30) and is not applied here any more;
compaction detection now lives only in the transcript
(`tools/route.py`'s `_transcript_context_stats`).

`main`'s `used_percentage` is recomputed against the effective
auto-compact window, `min(context_window_size, resolved)`, rather than
taken verbatim from the platform (section 13.2); the platform's own
figure is kept alongside it as `platform_used_percentage` so the two can
be compared.

`--main`'s stdout is the rendered status line text, since that is what
`statusLine` displays verbatim. `--tasks` prints nothing: `subagentStatusLine`
reads `{"id": ..., "content": ...}` override lines from stdout, and
emitting none keeps every row's default rendering, which is the point of
observing rather than replacing them.

Usage:
    python3 tools/context_probe.py --main --project . < statusline.json
    python3 tools/context_probe.py --tasks --project . < subagent-statusline.json
    python3 tools/context_probe.py --selftest
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

USAGE_FILENAME = ".claude/context-usage.json"


def default_usage_path(project: Path) -> Path:
    return project / USAGE_FILENAME


def _now_iso() -> str:
    return dt.datetime.now().isoformat()


def _load_usage_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # A concurrent writer's partial write, or a hand-edited file gone
        # bad. Treated as absent (route.py's own load_ledger tolerance for
        # a partial write, applied here to the same class of problem)
        # rather than raised, since a probe that crashes the status line
        # would take context_window.used_percentage down with it.
        return {}


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    tmp.replace(path)


def _numeric_leaves(obj: object) -> list[float]:
    """Every number found anywhere inside `obj`, walking dicts and lists.
    `tokenSamples`' shape is undocumented (section 2); this keeps
    `peak_tokens` correct whatever it turns out to be, a list of ints,
    a list of {"tokens": n} objects, or something else numeric."""
    out: list[float] = []
    if isinstance(obj, bool):
        return out
    if isinstance(obj, (int, float)):
        out.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(_numeric_leaves(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_numeric_leaves(v))
    return out


def _resolve_autocompact_window(project: Path) -> tuple[int | None, str | None]:
    """Resolves the configured auto-compact window in the documented
    precedence (docs/COMPACTION-DESIGN.md section 13.2): the
    `CLAUDE_CODE_AUTO_COMPACT_WINDOW` environment variable first, else the
    first `autoCompactWindow` key found across `.claude/settings.local.json`,
    `.claude/settings.json` (both under `project`) and
    `~/.claude/settings.json`, in that order. Returns `(None, None)` when
    nothing is configured anywhere, so `main_record` falls back to the
    platform's own `context_window_size`.

    This duplicates a small piece of logic `src/preflight.py`'s
    `check_autocompact_window` (and, after this stage, its shared
    `_resolved_autocompact_window` helper) already implements for the same
    purpose. `context_probe.py` cannot import `preflight.py`: this file
    ships standalone in `dist/` (its own module docstring's "Deliberately
    does not" convention), the same reason `src/preflight.py` itself gives
    for not importing `tools/cells.py`. This is therefore intentional,
    cited duplication, not an oversight."""
    env = os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
    if env is not None:
        try:
            return int(env), "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
        except ValueError:
            return None, None
    for path in (project / ".claude" / "settings.local.json", project / ".claude" / "settings.json",
                 Path.home() / ".claude" / "settings.json"):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict) and "autoCompactWindow" in data:
            return data["autoCompactWindow"], str(path)
    return None, None


def main_record(payload: dict, project: Path) -> dict:
    """The `main` key's shape (section 2, revised by section 13.2, D72).
    Every platform-reported field is `None` when the platform has not
    populated it yet (before the first API response, or again right after
    `/compact` until the next one, `docs/en/statusline`).

    `used_percentage` is recomputed against `effective_window =
    min(context_window_size, resolved)`, where `resolved` is whatever
    `_resolve_autocompact_window` finds, so a configured
    `autoCompactWindow` smaller than the model's native window is
    reflected here even where the platform's own figure (kept verbatim as
    `platform_used_percentage`) does not yet account for it (D69's own
    reversal clause; this is a no-op wherever the platform already does).
    `effective_window_source` names which of `CLAUDE_CODE_AUTO_COMPACT_WINDOW`,
    a settings file path, or `context_window_size` produced the effective
    window, or `None` when neither the resolved window nor
    `context_window_size` is known."""
    cw = payload.get("context_window") or {}
    context_window_size = cw.get("context_window_size")
    total_input_tokens = cw.get("total_input_tokens")
    resolved, resolved_source = _resolve_autocompact_window(project)

    if resolved is not None and context_window_size is not None:
        effective_window = min(context_window_size, resolved)
        effective_window_source = resolved_source if effective_window == resolved else "context_window_size"
    elif resolved is not None:
        effective_window, effective_window_source = resolved, resolved_source
    elif context_window_size is not None:
        effective_window, effective_window_source = context_window_size, "context_window_size"
    else:
        effective_window, effective_window_source = None, None

    # Rounded to a whole percentage point, matching the platform's own
    # `used_percentage` convention (an int like 8 or 73, not 7.75):
    # status_line_text's `:.0f` formatting works on either, but a reader
    # comparing this field against the platform's verbatim
    # `platform_used_percentage` should not see a spurious difference
    # that is only a rounding convention, not a real disagreement.
    used_percentage = (round(total_input_tokens / effective_window * 100)
                        if total_input_tokens is not None and effective_window else None)

    return {
        "sampled_at": _now_iso(),
        "model": (payload.get("model") or {}).get("display_name"),
        "used_percentage": used_percentage,
        "platform_used_percentage": cw.get("used_percentage"),
        "total_input_tokens": total_input_tokens,
        "context_window_size": context_window_size,
        "effective_window": effective_window,
        "effective_window_source": effective_window_source,
        "current_usage": cw.get("current_usage"),
        "prompt_cache": payload.get("prompt_cache"),
    }


def status_line_text(record: dict) -> str:
    model = record.get("model") or "?"
    used = record.get("used_percentage")
    cache = record.get("prompt_cache") or {}
    ctx = f"ctx {used:.0f}%" if isinstance(used, (int, float)) else "ctx ?"
    warm = "cache warm" if cache.get("warm") else ("cache cold" if cache else "cache unknown")
    return f"[{model}] {ctx} · {warm}"


def merge_task_record(existing: dict | None, task: dict) -> dict:
    """One task's entry in the `tasks` key (section 2). `peak_tokens` is
    the largest numeric value ever observed for this task name, across
    `tokenCount` and every leaf of `tokenSamples`, kept across refreshes
    even once the task stops appearing in the visible rows (a completed
    task's last known peak is exactly what `route.py --record` wants).

    Deliberately does not count compactions any more (docs/COMPACTION-DESIGN.md
    section 13.2, D72): the drop-past-half heuristic this function used to
    apply was falsified by E30's live transcripts (observed ratios of 0.57
    and 0.87 after a real compaction, both above the 0.5 threshold, because
    the fixed prefix never shrinks), so every real compaction it was meant
    to catch would have been missed. Compaction detection now lives only
    in the transcript, `tools/route.py`'s `_transcript_context_stats`,
    which counts the platform's own `compact_boundary` events directly
    rather than inferring one from a token-count drop."""
    candidates = [v for v in (_as_number(task.get("tokenCount")), *_numeric_leaves(task.get("tokenSamples")))
                  if v is not None]
    if existing and existing.get("peak_tokens") is not None:
        candidates.append(existing["peak_tokens"])

    return {
        "sampled_at": _now_iso(),
        "id": task.get("id"),
        "type": task.get("type"),
        "status": task.get("status"),
        "model": task.get("model"),
        "effort": task.get("effort"),
        "contextWindowSize": task.get("contextWindowSize"),
        "tokenCount": task.get("tokenCount"),
        "tokenSamples": task.get("tokenSamples"),
        "peak_tokens": _as_int_if_whole(max(candidates)) if candidates else None,
    }


def _as_int_if_whole(v: float) -> int | float:
    return int(v) if v == int(v) else v


def _as_number(v: object) -> float | None:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def run_main(payload: dict, usage_path: Path, project: Path) -> str:
    data = _load_usage_file(usage_path)
    record = main_record(payload, project)
    data["main"] = record
    data["written_at"] = _now_iso()
    data["session_id"] = payload.get("session_id")
    _atomic_write_json(usage_path, data)
    return status_line_text(record)


def run_tasks(payload: dict, usage_path: Path) -> None:
    data = _load_usage_file(usage_path)
    tasks_out = dict(data.get("tasks") or {})
    for task in payload.get("tasks", []) or []:
        name = task.get("name")
        if not name:
            continue
        tasks_out[name] = merge_task_record(tasks_out.get(name), task)
    data["tasks"] = tasks_out
    data["written_at"] = _now_iso()
    data.setdefault("session_id", payload.get("session_id"))
    _atomic_write_json(usage_path, data)


def _selftest(verbose: bool = False) -> tuple[bool, list[str]]:
    """Runs both modes against the documentation-derived sample
    (test/fixtures/system/statusline-sample.json, section 2), no network
    and no real status line invocation: the sample is what a live one
    would send, so the round trip is genuine even though the input is
    not a live capture (E30 replaces it with one when Stage E runs).

    Scenarios (a) through (e) predate docs/COMPACTION-DESIGN.md section
    13.2 (D72); (c) and its sibling (c2), which asserted the drop-past-half
    compaction heuristic, are removed rather than renumbered, since that
    heuristic itself is gone (see `merge_task_record`'s docstring).
    Scenario (f) is new in this stage: the effective-window recomputation
    of `used_percentage` against a configured `autoCompactWindow` smaller
    than the model's native window."""
    import tempfile

    problems: list[str] = []

    def check(cond: bool, msg: str) -> None:
        if not cond:
            problems.append(msg)
        elif verbose:
            print(f"ok: {msg}")

    repo_root = Path(__file__).resolve().parent.parent
    sample = json.loads((repo_root / "test" / "fixtures" / "system" / "statusline-sample.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory(prefix="context-probe-selftest-") as tmp:
        project = Path(tmp)
        usage_path = project / USAGE_FILENAME

        # (a) with no settings file in this project, _resolve_autocompact_window
        # finds nothing, so effective_window falls back to context_window_size
        # and used_percentage reproduces exactly what the platform's own
        # figure already was: today's behaviour, preserved. platform_used_percentage
        # carries the platform's verbatim figure alongside it, and
        # effective_window_source names context_window_size since nothing
        # configured overrides it.
        line = run_main(sample["main"], usage_path, project)
        check("Opus" in line and "8%" in line, f"(a) --main should render the model and used_percentage, got {line!r}")
        data = _load_usage_file(usage_path)
        main_record_out = data.get("main", {})
        check(main_record_out.get("used_percentage") == 8, "(a) main.used_percentage should round-trip")
        check(main_record_out.get("platform_used_percentage") == 8,
              f"(a) platform_used_percentage should carry the platform's own figure verbatim, "
              f"got {main_record_out.get('platform_used_percentage')!r}")
        check(main_record_out.get("effective_window_source") == "context_window_size",
              f"(a) with no configured window, effective_window_source should name context_window_size, "
              f"got {main_record_out.get('effective_window_source')!r}")
        check("tasks" not in data, "(a) a --main-only file should carry no tasks key yet")

        run_tasks(sample["tasks"], usage_path)
        data = _load_usage_file(usage_path)
        check(data.get("main", {}).get("used_percentage") == 8,
              "(b) --tasks must not disturb the main key written by (a)")
        check(set(data.get("tasks", {})) == {"refactor-parser", "audit-schemas"},
              f"(b) both named tasks should be present, got {sorted(data.get('tasks', {}))}")
        check(data["tasks"]["refactor-parser"]["peak_tokens"] == 42000,
              f"(b) peak_tokens should be the max of tokenCount and tokenSamples, "
              f"got {data['tasks']['refactor-parser']['peak_tokens']}")

        # (c) a second, lower sample for the same task must not lower its
        # recorded peak: peak_tokens tracks the maximum ever seen, not the
        # most recent reading. (Compaction counting on this same drop, the
        # original scenario (c) and (c2), is removed: see the docstring above.)
        lower = json.loads(json.dumps(sample["tasks"]))
        lower["tasks"][0]["tokenCount"] = 9000
        lower["tasks"][0]["tokenSamples"] = [9000]
        run_tasks(lower, usage_path)
        data = _load_usage_file(usage_path)
        check(data["tasks"]["refactor-parser"]["peak_tokens"] == 42000,
              f"(c) a lower later sample should not lower peak_tokens, got "
              f"{data['tasks']['refactor-parser']['peak_tokens']}")

        # (d) crossing the handoff threshold changes the rendered line's
        # warmth reporting is out of scope here (route.py --explain owns
        # the threshold); this only checks the over-threshold sample still
        # round-trips its own fields correctly.
        run_main(sample["main_over_threshold"], usage_path, project)
        data = _load_usage_file(usage_path)
        check(data["main"]["used_percentage"] == 73, "(d) a second --main call should overwrite the main key, not merge it")

    # (e) a payload the platform has not populated yet (no API response so
    # far) should not crash and should record every field as absent.
    with tempfile.TemporaryDirectory(prefix="context-probe-selftest-") as tmp:
        empty_line = run_main({"model": {"display_name": "Sonnet"}, "context_window": {}},
                               Path(tmp) / USAGE_FILENAME, Path(tmp))
    check("ctx ?" in empty_line, f"(e) an unpopulated context_window should render 'ctx ?', got {empty_line!r}")

    # (f) docs/COMPACTION-DESIGN.md section 13.8: a project whose
    # .claude/settings.json sets autoCompactWindow to 200,000, fed a
    # context_window_size of 1,000,000 and a total_input_tokens of
    # 100,000, should compute used_percentage against the smaller,
    # resolved 200,000 (a clean 50 percent) rather than the platform's own
    # 1,000,000-relative figure (kept verbatim as platform_used_percentage,
    # whatever the sample states, unrelated to this recomputation).
    with tempfile.TemporaryDirectory(prefix="context-probe-selftest-") as tmp:
        project = Path(tmp)
        settings_path = project / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps({"autoCompactWindow": 200000}), encoding="utf-8")
        usage_path = project / USAGE_FILENAME
        payload = {"model": {"display_name": "Sonnet"},
                   "context_window": {"total_input_tokens": 100000, "context_window_size": 1000000,
                                       "used_percentage": 10}}
        run_main(payload, usage_path, project)
        data = _load_usage_file(usage_path)
        record = data.get("main", {})
        check(record.get("used_percentage") == 50,
              f"(f) used_percentage should be computed against the resolved 200,000 window, not the "
              f"platform's 1,000,000, got {record.get('used_percentage')!r}")
        check(record.get("platform_used_percentage") == 10,
              f"(f) platform_used_percentage should carry the sample's own raw figure verbatim, "
              f"got {record.get('platform_used_percentage')!r}")
        check(record.get("effective_window") == 200000,
              f"(f) effective_window should be the smaller, resolved window, got {record.get('effective_window')!r}")
        check(record.get("effective_window_source") == str(settings_path),
              f"(f) effective_window_source should name the settings file that set autoCompactWindow, "
              f"got {record.get('effective_window_source')!r}")

    return (not problems, problems)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--main", action="store_true", help="the statusLine command: read stdin, write the main key")
    group.add_argument("--tasks", action="store_true", help="the subagentStatusLine command: read stdin, write the tasks key")
    group.add_argument("--selftest", action="store_true", help="run the scripted round trip against the documentation-derived sample")
    ap.add_argument("--project", type=Path, default=Path("."), help="consumer project root")
    ap.add_argument("--json", action="store_true", help="with --selftest, print each check as it runs")
    args = ap.parse_args(argv)

    if args.selftest:
        ok, problems = _selftest(verbose=args.json)
        if ok:
            print("selftest: PASS, 6 scenarios")
            return 0
        print(f"selftest: FAIL, {len(problems)} problem(s)")
        for p in problems:
            print(f"  - {p}")
        return 1

    if not (args.main or args.tasks):
        ap.error("pass --main, --tasks or --selftest")

    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        print(f"context_probe.py: stdin did not parse as JSON: {exc}", file=sys.stderr)
        return 1

    usage_path = default_usage_path(args.project)
    if args.main:
        print(run_main(payload, usage_path, args.project))
    else:
        run_tasks(payload, usage_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
