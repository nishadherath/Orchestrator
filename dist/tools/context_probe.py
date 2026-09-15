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
numeric value found in it, whatever shape it turns out to have.

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


def main_record(payload: dict) -> dict:
    """The `main` key's shape (section 2), read from one status line
    invocation's JSON. Every field is `None` when the platform has not
    populated it yet (before the first API response, or again right
    after `/compact` until the next one, `docs/en/statusline`)."""
    cw = payload.get("context_window") or {}
    return {
        "sampled_at": _now_iso(),
        "model": (payload.get("model") or {}).get("display_name"),
        "used_percentage": cw.get("used_percentage"),
        "total_input_tokens": cw.get("total_input_tokens"),
        "context_window_size": cw.get("context_window_size"),
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
    task's last known peak is exactly what `route.py --record` wants)."""
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


def run_main(payload: dict, usage_path: Path) -> str:
    data = _load_usage_file(usage_path)
    record = main_record(payload)
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
    not a live capture (E30 replaces it with one when Stage E runs)."""
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
        usage_path = Path(tmp) / USAGE_FILENAME

        line = run_main(sample["main"], usage_path)
        check("Opus" in line and "8%" in line, f"(a) --main should render the model and used_percentage, got {line!r}")
        data = _load_usage_file(usage_path)
        check(data.get("main", {}).get("used_percentage") == 8, "(a) main.used_percentage should round-trip")
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
        # most recent reading.
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
        run_main(sample["main_over_threshold"], usage_path)
        data = _load_usage_file(usage_path)
        check(data["main"]["used_percentage"] == 73, "(d) a second --main call should overwrite the main key, not merge it")

    # (e) a payload the platform has not populated yet (no API response so
    # far) should not crash and should record every field as absent.
    with tempfile.TemporaryDirectory(prefix="context-probe-selftest-") as tmp:
        empty_line = run_main({"model": {"display_name": "Sonnet"}, "context_window": {}},
                               Path(tmp) / USAGE_FILENAME)
    check("ctx ?" in empty_line, f"(e) an unpopulated context_window should render 'ctx ?', got {empty_line!r}")

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
            print("selftest: PASS, 5 scenarios")
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
        print(run_main(payload, usage_path))
    else:
        run_tasks(payload, usage_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
