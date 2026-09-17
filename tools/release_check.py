#!/usr/bin/env python3
"""Assess an offline release candidate without publishing it."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"


def load_build_dist():
    spec = importlib.util.spec_from_file_location("build_dist_release", ROOT / "tools" / "build_dist.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def check_source_equivalence() -> dict:
    version_file = DIST / ".claude" / "ORCHESTRATOR_VERSION"
    if not version_file.is_file():
        return {"status": "FAIL", "detail": "dist/.claude/ORCHESTRATOR_VERSION is missing"}
    version = version_file.read_text(encoding="utf-8").strip()
    planned = load_build_dist().planned_files(version, DIST)
    expected = {path.relative_to(DIST).as_posix(): content.encode("utf-8") for path, content in planned.items()}
    actual = {path.relative_to(DIST).as_posix(): path.read_bytes() for path in DIST.rglob("*") if path.is_file()}
    changed = sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    ok = not (changed or missing or extra)
    detail = f"{len(actual)} files match source" if ok else f"changed={changed}, missing={missing}, extra={extra}"
    return {"status": "PASS" if ok else "FAIL", "detail": detail}


def check_workers() -> dict:
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "generate_workers.py"), "--check", "--json"],
                          cwd=ROOT, capture_output=True, text=True)
    try:
        value = json.loads(proc.stdout)
        drift = [row["file"] for row in value["files"] if row["status"] != "unchanged"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return {"status": "FAIL", "detail": f"worker generator failed: {(proc.stdout + proc.stderr)[-500:]}"}
    return {"status": "PASS" if not drift else "FAIL",
            "detail": "15 generated definitions match" if not drift else f"drifted={drift}"}


def check_sensitive_material() -> dict:
    forbidden_paths = ("routing-ledger", "orchestrator-install/backups", "graft/", ".mcp.json", ".codex/", "handoffs/")
    path_hits, content_hits = [], []
    secret = re.compile(r"(?i)(?:sk-[a-z0-9_-]{16,}|api[_-]?key\s*[=:]\s*['\"][^'\"]{8,})")
    machine = re.compile(r"(?i)(?:[a-z]:[/\\]users[/\\][^/\\\s]+|/home/[^/\s]+|/users/[^/\s]+)")
    for path in sorted(p for p in DIST.rglob("*") if p.is_file()):
        relative = path.relative_to(DIST).as_posix()
        lowered = relative.lower()
        if any(item in lowered for item in forbidden_paths):
            path_hits.append(relative)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if secret.search(text):
            content_hits.append(f"{relative}:credential-like text")
        if machine.search(text):
            content_hits.append(f"{relative}:machine-specific home path")
    problems = path_hits + content_hits
    return {"status": "PASS" if not problems else "FAIL",
            "detail": "no personal ledgers, caches, credentials or machine home paths" if not problems else str(problems)}


def check_licence() -> dict:
    candidates = [path for name in ("LICENSE", "LICENSE.md", "LICENSE.txt", "NOTICE", "NOTICE.md")
                  if (path := ROOT / name).is_file()]
    if not candidates:
        return {"status": "ACTION_REQUIRED",
                "detail": "no project licence or notice is present; the operator must choose one before publication"}
    return {"status": "PASS", "detail": f"found {', '.join(path.name for path in candidates)}"}


def check_stamp() -> dict:
    path = DIST / ".claude" / "ORCHESTRATOR_VERSION"
    version = path.read_text(encoding="utf-8").strip() if path.is_file() else ""
    return {"status": "PASS" if version and not version.endswith("-dirty") else "ACTION_REQUIRED",
            "detail": version or "version stamp missing"}


def report() -> dict:
    checks = {
        "source_equivalence": check_source_equivalence(),
        "generated_workers": check_workers(),
        "sensitive_material": check_sensitive_material(),
        "licence_notice": check_licence(),
        "clean_build_stamp": check_stamp(),
        "publication": {"status": "ACTION_REQUIRED",
                        "detail": "publishing remains an explicit operator action"},
    }
    mechanical_failures = [name for name, value in checks.items() if value["status"] == "FAIL"]
    actions = [name for name, value in checks.items() if value["status"] == "ACTION_REQUIRED"]
    return {"schema_version": 1, "result": "FAIL" if mechanical_failures else "PASS",
            "release_ready": not mechanical_failures and not actions,
            "mechanical_failures": mechanical_failures, "operator_actions": actions, "checks": checks}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="also fail when licence, clean-stamp or publication action remains")
    args = parser.parse_args(argv)
    value = report()
    if args.json:
        print(json.dumps(value, indent=2))
    else:
        for name, row in value["checks"].items():
            print(f"{row['status']:15} {name}: {row['detail']}")
        print(f"\n{value['result']}: release_ready={value['release_ready']}")
    return 1 if value["mechanical_failures"] or (args.strict and value["operator_actions"]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
