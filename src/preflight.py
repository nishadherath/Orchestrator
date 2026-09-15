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
    required = [cwd / "src" / "routing_priors.json", cwd / "src" / "cost_table.json"]
    missing = [str(p.relative_to(cwd)) for p in required if not p.is_file()]
    if not missing:
        return {"check": "routing data present", "status": "PASS",
                "detail": "src/routing_priors.json and src/cost_table.json both found"}
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


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    cwd = Path.cwd()
    checks = check_env() + [check_available_models(cwd), check_version(), check_bundle(cwd), check_controller(cwd),
                            check_routing_data(cwd), check_route_selftest(cwd), check_bash_permission(cwd)]
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
