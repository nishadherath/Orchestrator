#!/usr/bin/env python3
"""Grade the authored H01 case with evaluator-owned expectations in WSL."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import sys

import worker_wsl_q2_verify as q2


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01"
CATALOGUE = CASE / "catalogue-h01.json"
PROBE = ROOT / "test/oracles/controller_x5_authored_httpcore/H01_probe.py"
EXPECTED = {
    "sync_surplus": {"initial_assignment": True, "assigned_retained": True,
                     "surplus_selected": True, "pool_count": 1},
    "async_competing": {"initial_assignment": True, "assigned_retained": True,
                        "second_queued": True, "pool_count": 1},
    "ordinary_cleanup": {"expired_selected": True, "expired_removed": True,
                         "pool_count": 0},
}
WEIGHTS = {"public": 25, "sync_surplus": 25,
           "async_competing": 25, "ordinary_cleanup": 25}
UNSAFE_NAMES = {"__import__", "eval", "exec", "globals", "locals", "vars",
                "unittest", "json", "builtins", "importlib"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(actor: Path) -> dict[str, str]:
    if actor.is_symlink() or not actor.is_dir():
        raise ValueError("H01 actor root is missing or redirected")
    found = {}
    for path in actor.rglob("*"):
        relative = path.relative_to(actor).as_posix()
        if path.is_symlink() or (path.is_dir() and path.name == "__pycache__"):
            raise ValueError(f"H01 actor has a redirected or cached path: {relative}")
        if path.is_file():
            found[relative] = sha(path)
    return found


def scoped_method_tree(path: Path) -> tuple[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    target = None
    for item in tree.body:
        if isinstance(item, ast.ClassDef) and item.name in {"ConnectionPool", "AsyncConnectionPool"}:
            for member in item.body:
                if isinstance(member, ast.FunctionDef) and member.name == "_assign_requests_to_connections":
                    target = member
                    break
    if target is None:
        raise ValueError("H01 editable pool method missing")
    original_body = target.body
    target.body = [ast.Pass()]
    outside = ast.dump(tree, include_attributes=False)
    target.body = original_body
    return outside, target


def edit_scope_violations(actor: Path, editable: set[str]) -> list[str]:
    violations = []
    for name in sorted(editable):
        baseline, _ = scoped_method_tree(CASE / "actor" / name)
        candidate, method = scoped_method_tree(actor / name)
        if baseline != candidate:
            violations.append(f"{name}: outside assignment method")
        if any(isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal))
               or isinstance(node, ast.Name) and node.id in UNSAFE_NAMES
               or isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
               and node.value.id == "sys"
               for node in ast.walk(method)):
            violations.append(f"{name}: evaluator-facing operation")
    return violations


def grade(actor: Path) -> dict:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("H01 protected grading requires WSL root")
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    body = {key: value for key, value in catalogue.items() if key != "catalogue_sha256"}
    if hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest() != catalogue.get("catalogue_sha256"):
        raise RuntimeError("H01 catalogue digest differs")
    frozen = catalogue["actor_files"]
    editable = set(catalogue["editable_paths"])
    before = inventory(actor)
    if set(before) != set(frozen):
        raise ValueError("H01 actor file inventory differs from frozen package")
    protected_edits = sorted(name for name in frozen if name not in editable
                             and before[name] != frozen[name])
    if protected_edits:
        return {"case": "H01", "quality": 0, "accepted": False,
                "critical": True, "protected_edits": protected_edits}
    scope = edit_scope_violations(actor, editable)
    if scope:
        return {"case": "H01", "quality": 0, "accepted": False,
                "critical": True, "scope_violations": scope}
    if sha(PROBE) != catalogue["probe_sha256"]:
        raise RuntimeError("H01 evaluator probe changed")
    package, manifest_path, manifest = q2.copy_package(actor, None)
    uncertain = False
    try:
        public = q2.run_isolated(package, manifest_path, manifest,
                                 ["/usr/bin/python3", "-B", "public_check.py"])
        hidden = q2.run_isolated(package, manifest_path, manifest,
                                 ["/usr/bin/python3", "-B", "-c",
                                  PROBE.read_text(encoding="utf-8")])
    except q2.UncertainActorError:
        uncertain = True
        raise
    finally:
        if not uncertain:
            q2.dispose(package, q2.SEEDS)
            manifest_path.unlink(missing_ok=True)
    if inventory(actor) != before or sha(PROBE) != catalogue["probe_sha256"]:
        raise RuntimeError("H01 candidate or probe changed during grading")
    if public.returncode not in {0, 1}:
        raise RuntimeError("H01 public check crashed outside assertion outcome")
    if hidden.returncode != 0 or len(hidden.stdout) > 4096:
        raise RuntimeError("H01 hidden probe failed or exceeded output cap")
    try:
        observed = json.loads(hidden.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("H01 hidden probe returned invalid JSON") from exc
    if not isinstance(observed, dict) or set(observed) != set(EXPECTED):
        raise RuntimeError("H01 hidden probe returned an invalid case set")
    checks = {"public": public.returncode == 0}
    for name, expected in EXPECTED.items():
        actual = observed[name]
        checks[name] = (isinstance(actual, dict) and set(actual) == set(expected)
                        and all(type(actual[key]) is type(value) and actual[key] == value
                                for key, value in expected.items()))
    quality = sum(WEIGHTS[name] for name, passed in checks.items() if passed)
    return {"case": "H01", "quality": quality, "accepted": quality == 100,
            "critical": False, "checks": checks,
            "candidate_edit_sha256": {name: before[name] for name in sorted(editable)},
            "oracle_sha256": catalogue["probe_sha256"],
            "boundary": "Q1 isolated actor uid 65534; evaluator-owned comparison"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(grade(args.actor.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
