#!/usr/bin/env python3
"""Preflight check: verify the orchestrator's environment before trusting the routing.

Responsible for: turning README.md's "Settings that will break this" table
into a script a consumer runs once, instead of checking six things by hand.
Exits 0 only if every check that can be verified from a shell passes; a WARN
is something this script cannot verify (an admin-controlled policy, or a
version it could not parse) and needs a human to confirm.

Deliberately does not: install the bundle, spawn a worker, or check the
routing table's correctness. That needs test/harness/score_routing.py, run
from this repository against this project, not this script.

Ships standalone in dist/, without the rest of this repository, so it does
not import tools/cells.py; MODELS is declared here for that reason, not from
missed deduplication.

Usage:
    python3 preflight.py                run from the consumer project's root
    python3 preflight.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MODELS = ("sonnet", "opus", "fable")

# The version FINDINGS.md names as the first to show effort on the /tasks
# row (this repository's docs/FINDINGS.md, checked 2026-09-05 against the
# Claude Code changelog). A lower version does not break routing; it only
# means /tasks cannot be used to verify routing took effect.
MIN_VERSION_FOR_EFFORT_ROW = (2, 1, 243)

BLOCKING_ENV = {
    "CLAUDE_CODE_EFFORT_LEVEL": (None, "Overrides frontmatter effort on every worker."),
    "CLAUDE_CODE_SUBAGENT_MODEL_FORCE": ({None, "", "0"},
        "When set, Claude Code ignores every worker's model field and flattens the whole scheme onto one model."),
    "CLAUDE_CODE_SUBAGENT_MODEL": (None,
        "A default for workers without a model. Harmless here since every worker sets one, but leave it clear to avoid confusion."),
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": (None,
        "Named subagents launch as teammates and follow the lead's effort level instead of their own definition."),
}


def check_env() -> list[dict]:
    out = []
    for name, (required, why) in BLOCKING_ENV.items():
        value = os.environ.get(name)
        ok = (value is None) if required is None else (value in required)
        out.append({"check": f"env:{name}", "status": "PASS" if ok else "FAIL",
                    "detail": f"{name} is {'unset' if value is None else f'{value!r}'}. {why}"})
    return out


def check_available_models(cwd: Path) -> dict:
    candidates = [Path.home() / ".claude" / "settings.json",
                  cwd / ".claude" / "settings.json",
                  cwd / ".claude" / "settings.local.json"]
    found: list[str] = []
    blocked: list[str] = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            blocked.append(f"{path}: unparseable ({exc})")
            continue
        allow = data.get("availableModels")
        if allow is None:
            continue
        found.append(str(path))
        allow_text = json.dumps(allow).lower()
        for model in MODELS:
            if model not in allow_text:
                blocked.append(f"{path}: availableModels does not mention {model}")
    if not found and not blocked:
        return {"check": "availableModels", "status": "PASS",
                "detail": f"no availableModels allowlist in {[str(c) for c in candidates if c.exists()] or 'any checked settings file'}. "
                          "A managed enterprise policy is not checked here; a blocked model is substituted, not failed, so a "
                          "silent substitution is still possible from that layer."}
    return {"check": "availableModels", "status": "PASS" if not blocked else "FAIL",
            "detail": f"allowlist in {found}" if not blocked else "; ".join(blocked)}


def check_version() -> dict:
    if shutil.which("claude") is None:
        return {"check": "claude --version", "status": "WARN", "detail": "`claude` not found on PATH; cannot check the version"}
    try:
        proc = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"check": "claude --version", "status": "WARN", "detail": f"could not run `claude --version`: {exc}"}
    out = proc.stdout.strip()
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    if not m:
        return {"check": "claude --version", "status": "WARN", "detail": f"could not parse a version from {out!r}"}
    version = tuple(int(g) for g in m.groups())
    ok = version >= MIN_VERSION_FOR_EFFORT_ROW
    tail = "" if ok else (f" This is below v{'.'.join(map(str, MIN_VERSION_FOR_EFFORT_ROW))}, the version FINDINGS.md "
                           "names as the first to show effort on the /tasks row; routing may still work, but you "
                           "cannot verify it from /tasks.")
    return {"check": "claude --version", "status": "PASS" if ok else "WARN", "detail": f"{out}.{tail}"}


def check_bundle(cwd: Path) -> dict:
    agents_dir = cwd / ".claude" / "agents"
    if not agents_dir.is_dir():
        return {"check": "bundle installed", "status": "FAIL",
                "detail": f"{agents_dir} missing; install dist/ first (README.md)"}
    count = len(list(agents_dir.glob("WORKER_*.md")))
    version_file = cwd / ".claude" / "ORCHESTRATOR_VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "unknown (no ORCHESTRATOR_VERSION file)"
    # B0_BRIEF.md is a manual, optional alternative since D63 (no longer read
    # by section 4's automatic trigger), so its absence is noted, not a FAIL.
    brief = cwd / ".claude" / "B0_BRIEF.md"
    brief_note = "" if brief.is_file() else f"; {brief} missing (optional; a manual single-worker alternative)"
    return {"check": "bundle installed", "status": "PASS" if count == 15 else "FAIL",
            "detail": f"{count} of 15 worker definitions found in {agents_dir}; bundle version {version}{brief_note}"}


def check_controller(cwd: Path) -> dict:
    """ORCHESTRATOR.md section 4's falsified-constraint trigger invokes
    tools/system_controller.py directly (D63); this checks whether it and
    its full dependency chain are present, partially present (which would
    fail mid-trigger, not at install time, so it is caught here instead),
    or absent (in which case the trigger falls through to worker-opus-high
    directly, per its own documented fallback)."""
    required = [cwd / "tools" / "system_controller.py", cwd / "tools" / "claudep.py",
                cwd / "tools" / "system_prompts.py", cwd / "tools" / "validate_records.py",
                cwd / "src" / "System" / "ROLES.md", cwd / "src" / "System" / "TECHNIQUES.md"]
    schemas_dir = cwd / "src" / "System" / "schemas"
    present = [p for p in required if p.is_file()]
    schema_count = len(list(schemas_dir.glob("*.schema.json"))) if schemas_dir.is_dir() else 0
    if len(present) == len(required) and schema_count >= 13:
        return {"check": "Controller installed", "status": "PASS",
                "detail": f"all {len(required)} files and {schema_count} schemas found; "
                          "section 4's trigger can invoke tools/system_controller.py"}
    if not present and schema_count == 0:
        return {"check": "Controller installed", "status": "WARN",
                "detail": "not installed; section 4's falsified-constraint trigger will fall through to "
                          "worker-opus-high directly, its documented fallback (README.md)"}
    missing = [str(p.relative_to(cwd)) for p in required if not p.is_file()]
    if schema_count < 13:
        missing.append(f"src/System/schemas/ ({schema_count} of 13 schemas)")
    return {"check": "Controller installed", "status": "FAIL",
            "detail": f"partially installed, missing: {missing}; a mid-trigger crash, not a clean fallback, "
                      "is what an incomplete install like this produces"}


def check_routing_data(cwd: Path) -> dict:
    """route.py's plan() reads both files at import time (tools/route.py);
    a missing one fails every routing decision, not just an edge case, so
    this is checked at install time rather than left to surface mid-task."""
    required = [cwd / "src" / "routing_priors.json", cwd / "src" / "cost_table.json",
                cwd / "src" / "routing_table.json"]
    missing = [str(p.relative_to(cwd)) for p in required if not p.is_file()]
    if not missing:
        return {"check": "routing data present", "status": "PASS",
                "detail": "src/routing_priors.json, src/cost_table.json and src/routing_table.json all found"}
    return {"check": "routing data present", "status": "FAIL",
            "detail": f"missing: {missing}; section 2's route.py call will fail on every task"}


def check_route_selftest(cwd: Path) -> dict:
    """Runs the installed copy's own --selftest (no claude -p calls, no
    project ledger touched) so a broken or partial install is caught here
    instead of failing silently mid-task, which is the failure mode
    section 2 says to never fall back to own judgement from."""
    route_py = cwd / "tools" / "route.py"
    if not route_py.is_file():
        return {"check": "route.py --selftest", "status": "FAIL",
                "detail": f"{route_py} missing; section 2 cannot resolve any cell"}
    try:
        proc = subprocess.run([sys.executable, str(route_py), "--selftest"],
                               capture_output=True, text=True, timeout=30, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"check": "route.py --selftest", "status": "FAIL", "detail": f"could not run: {exc}"}
    if proc.returncode == 0:
        return {"check": "route.py --selftest", "status": "PASS", "detail": proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "ok"}
    return {"check": "route.py --selftest", "status": "FAIL",
            "detail": (proc.stdout + proc.stderr).strip()[-1500:]}


def check_bash_permission(cwd: Path) -> dict:
    """Section 2 and section 4 both shell out to python3 (route.py,
    system_controller.py); a settings.json that does not permit it makes
    the orchestrator unable to route at all, silently, from inside a
    session where this script cannot run again to explain why."""
    candidates = [cwd / ".claude" / "settings.json", cwd / ".claude" / "settings.local.json"]
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {"check": "Bash(python3 *) permitted", "status": "WARN",
                    "detail": f"{path}: unparseable ({exc}); could not check"}
        allow = data.get("permissions", {}).get("allow", [])
        if any(isinstance(a, str) and a.startswith("Bash(python3") for a in allow):
            return {"check": "Bash(python3 *) permitted", "status": "PASS",
                    "detail": f"found in {path}"}
    return {"check": "Bash(python3 *) permitted", "status": "WARN",
            "detail": "no Bash(python3 *) allow rule found in .claude/settings.json or settings.local.json; "
                      "if Bash requires per-call approval, section 2's route.py call will prompt every task"}


def _settings_candidates(cwd: Path) -> list[Path]:
    return [Path.home() / ".claude" / "settings.json", cwd / ".claude" / "settings.json",
            cwd / ".claude" / "settings.local.json"]


def _load_settings(cwd: Path) -> list[tuple[Path, dict]]:
    """Every settings file that exists and parses, in precedence order
    (user, project, local). A file that does not parse is skipped, not
    raised: the checks below degrade to WARN on a settings file they
    cannot read, the same as check_available_models already does."""
    out = []
    for path in _settings_candidates(cwd):
        if not path.exists():
            continue
        try:
            out.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError:
            continue
    return out


def _resolved_autocompact_window(cwd: Path) -> tuple[int | None, str]:
    """The auto-compact window's resolution logic, in the documented
    precedence: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` first, else the first
    `autoCompactWindow` key found across `_load_settings`'s scopes (user,
    project, local, in that order). Factored out of `check_autocompact_window`
    so `check_autocompact_headroom` (section 13.5) shares the same scan
    instead of carrying a second copy of it in this same file; unlike
    `tools/context_probe.py`'s own duplicate of this logic (cited there,
    since that file cannot import this one), this is the same-file case,
    where sharing costs nothing.

    Returns `(value, source)`. `source` is always a string, never `None`:
    the settings file's path, the environment variable's name, a short
    note when the environment variable did not parse as an integer, or
    the empty string when nothing is configured anywhere, so a caller can
    tell "explicitly invalid" from "simply unset" without a second check."""
    env = os.environ.get("CLAUDE_CODE_AUTO_COMPACT_WINDOW")
    if env is not None:
        try:
            return int(env), "CLAUDE_CODE_AUTO_COMPACT_WINDOW"
        except ValueError:
            return None, f"CLAUDE_CODE_AUTO_COMPACT_WINDOW={env!r} (not a plain token count)"
    for path, data in _load_settings(cwd):
        if "autoCompactWindow" in data:
            return data["autoCompactWindow"], str(path)
    return None, ""


def check_autocompact_window(cwd: Path) -> dict:
    """docs/COMPACTION-DESIGN.md section 9: the auto-compact window should
    be set below the model's native limit, so route.py --explain's
    handoff recommendation (steering.handoff_context_percent) has a
    chance to fire before the platform's own compaction does (D68's
    economics: a handoff is a few hundred tokens, a fallback compaction
    at the model's full 1M-token limit is not)."""
    value, source = _resolved_autocompact_window(cwd)
    if value is None and source:
        return {"check": "auto-compact window", "status": "WARN", "detail": source}
    if value is None:
        return {"check": "auto-compact window", "status": "WARN",
                "detail": "unset; Claude Code compacts at the model's own limit (about 967,000 tokens on a "
                          "native 1M model). route.py --explain's handoff threshold still fires, but the "
                          "fallback compaction it is meant to pre-empt will be large and expensive when it happens"}
    if not isinstance(value, int) or not (100_000 <= value <= 1_000_000):
        return {"check": "auto-compact window", "status": "WARN",
                "detail": f"{source} sets autoCompactWindow to {value!r}, outside the documented 100,000 to "
                          "1,000,000 range (code.claude.com/docs/en/model-config)"}
    return {"check": "auto-compact window", "status": "PASS", "detail": f"{value:,} tokens, set in {source}"}


# The model's own default native ceiling, quoted verbatim from
# check_autocompact_window's own WARN text above ("about 967,000 tokens on
# a native 1M model"), used as check_autocompact_headroom's assumed window
# only when nothing is configured at all: an assumption stated as one in
# that check's own detail string, never silently treated as measured.
_ASSUMED_DEFAULT_WINDOW = 967_000

# The floor after a structured compaction (about 59,000 tokens) plus the
# platform's own reserve before it triggers the next one: docs/DECISIONS.md
# D72 point 4, bracketed from four observed compactions across two windows
# on plain-text content, version 2.1.268. Both this and the multiplier of
# three below are a bracket, not an exact constant, which is why
# check_autocompact_headroom below never returns FAIL.
_THRASH_FLOOR_RESERVE = 93_000


def check_autocompact_headroom(cwd: Path, per_turn_tokens: int) -> dict:
    """docs/COMPACTION-DESIGN.md section 13.5: a new check alongside
    `check_autocompact_window`, warning when the resolved auto-compact
    window leaves too little headroom above the platform's own
    post-compaction floor for a task to survive three ordinary turns
    before the platform aborts it outright as thrashing.

    `WARN` when `window - 93,000 < 3 * per_turn_tokens`; `PASS` otherwise.
    Never `FAIL`: 93,000 and the multiplier of three are both brackets
    from a small number of observed compactions (docs/DECISIONS.md D72
    point 4, plain-text content, version 2.1.268), not exact thresholds,
    so a value just outside them is an advisory, not a certainty. When no
    window is configured at all, this assumes the model's own default
    native ceiling (about 967,000 tokens) rather than leaving the check
    unable to run, and says in its detail string that this is an
    assumption, not an observation, per this repository's own rule
    against silent capability claims."""
    value, source = _resolved_autocompact_window(cwd)
    if value is None:
        window = _ASSUMED_DEFAULT_WINDOW
        configured_note = (f"no explicit window configured ({source}); " if source
                            else "no explicit window configured; ")
        window_note = f"{configured_note}assuming the model's own default native ceiling of about {window:,} tokens"
    else:
        window = value
        window_note = f"resolved window {window:,} tokens, from {source}"

    headroom = window - _THRASH_FLOOR_RESERVE
    threshold = 3 * per_turn_tokens
    detail = (f"{window_note}. window - {_THRASH_FLOOR_RESERVE:,} = {headroom:,}; "
              f"3 * per-turn footprint ({per_turn_tokens:,}) = {threshold:,}. "
              "Bracket per docs/DECISIONS.md D72 point 4, plain-text content, version 2.1.268.")
    if headroom < threshold:
        return {"check": "auto-compact headroom", "status": "WARN",
                "detail": f"{detail} Below the bracket: a task refilling this headroom within three turns "
                          "may be aborted outright by the platform as thrashing. Read in smaller chunks."}
    return {"check": "auto-compact headroom", "status": "PASS", "detail": detail}


def check_cache_ttl(cwd: Path, controller_installed: bool) -> dict:
    """A five-minute cache TTL on the main conversation turns a Controller
    run (about 500 seconds, src/cost_table.json) into a guaranteed cold
    cache on the orchestrator's next turn, reprocessing its whole context
    as uncached input (docs/COST.md; D68's economics). Only flagged when
    the Controller is actually installed, since that is the one thing in
    this bundle whose own wall clock reliably exceeds five minutes."""
    env = os.environ.get("CLAUDE_CODE_PROMPT_CACHE_TTL")
    value, source = (env, "CLAUDE_CODE_PROMPT_CACHE_TTL") if env else (None, None)
    if value is None:
        for path, data in _load_settings(cwd):
            if "promptCacheTtl" in data:
                value, source = data["promptCacheTtl"], str(path)
                break
    if value == "1h":
        return {"check": "prompt cache TTL", "status": "PASS", "detail": f"1h, set in {source}"}
    if controller_installed:
        return {"check": "prompt cache TTL", "status": "WARN",
                "detail": f"{'unset' if value is None else f'{value!r} in {source}'}; a Controller run is "
                          "about 500 seconds, longer than the default 5-minute TTL, so the orchestrator's next "
                          "turn after one reprocesses its whole context uncached. Set promptCacheTtl to \"1h\""}
    return {"check": "prompt cache TTL", "status": "PASS" if value else "WARN",
            "detail": f"{'unset (default 5m)' if value is None else f'{value!r} in {source}'}; "
                      "the Controller is not installed, so no run in this bundle reliably outlasts the default TTL"}


def check_compaction_hook(cwd: Path) -> dict:
    """docs/COMPACTION-DESIGN.md section 4: without this hook, the ledger
    still has every pending worker after a compaction, but nothing tells
    the orchestrator to read it."""
    for path, data in _load_settings(cwd):
        for entry in data.get("hooks", {}).get("SessionStart", []) or []:
            if entry.get("matcher") != "compact":
                continue
            for hook in entry.get("hooks", []) or []:
                if "route.py --recover" in (hook.get("command") or ""):
                    return {"check": "compaction recovery hook", "status": "PASS", "detail": f"found in {path}"}
    return {"check": "compaction recovery hook", "status": "WARN",
            "detail": "no SessionStart(compact) hook running route.py --recover found; after a compaction the "
                      "ledger still has every pending worker, but nothing prompts a read of it "
                      "(src/settings.fragment.json)"}


def check_context_probe(cwd: Path) -> dict:
    """docs/COMPACTION-DESIGN.md section 4: without both status line
    commands, route.py --explain's context line always reads unknown and
    the handoff-before-compaction mechanism never fires."""
    found = {"statusLine": None, "subagentStatusLine": None}
    for path, data in _load_settings(cwd):
        for key in found:
            if found[key] is None and "context_probe.py" in (data.get(key, {}).get("command") or ""):
                found[key] = str(path)
    missing = [k for k, v in found.items() if v is None]
    if not missing:
        return {"check": "context probe", "status": "PASS",
                "detail": f"statusLine in {found['statusLine']}, subagentStatusLine in {found['subagentStatusLine']}"}
    return {"check": "context probe", "status": "WARN",
            "detail": f"missing: {missing}; route.py --explain's context line will read unknown and never "
                      "recommend a handoff before a compaction (src/settings.fragment.json)"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--per-turn-tokens", type=int, default=8000,
                     help="assumed per-turn read size for the auto-compact headroom check "
                          "(docs/COMPACTION-DESIGN.md section 13.5); default 8,000, E30's read size")
    args = ap.parse_args(argv)

    cwd = Path.cwd()
    controller = check_controller(cwd)
    checks = check_env() + [check_available_models(cwd), check_version(), check_bundle(cwd), controller,
                            check_routing_data(cwd), check_route_selftest(cwd), check_bash_permission(cwd),
                            check_autocompact_window(cwd), check_autocompact_headroom(cwd, args.per_turn_tokens),
                            check_cache_ttl(cwd, controller["status"] == "PASS"),
                            check_compaction_hook(cwd), check_context_probe(cwd)]
    checks.append({"check": "organisation effort limits", "status": "WARN",
                    "detail": "not checkable from a shell; ask your admin whether any model has a capped effort "
                              "level, which runs silently under json output or in background agents (README.md)"})

    failed = sum(c["status"] == "FAIL" for c in checks)
    warned = sum(c["status"] == "WARN" for c in checks)

    if args.json:
        print(json.dumps({"result": "FAIL" if failed else "PASS", "checks": checks}, indent=2))
    else:
        for c in checks:
            print(f"{c['status']:4}  {c['check']}\n      {c['detail']}")
        print(f"\n{'FAIL' if failed else 'PASS'}: {failed} failing, {warned} needing manual follow-up, of {len(checks)} checks")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
