#!/usr/bin/env python3
"""Freeze and validate one upstream-backed Q3 public task's exact bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

from worker_adapter import digest

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "test/fixtures/worker_q3_public"
ORACLES = ROOT / "test/oracles/worker_q3_public"
HEX = re.compile(r"[0-9a-f]{40}")
SUPPORTED_LICENCES = {"MIT", "BSD-2-Clause", "BSD-3-Clause", "Apache-2.0",
                      "Apache-2.0 OR BSD-2-Clause"}


class PublicTaskError(RuntimeError):
    """A public task violates the frozen source or grading contract."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths(root: Path) -> dict[str, Path]:
    if root.is_symlink() or not root.is_dir():
        raise PublicTaskError(f"task directory is missing or redirected: {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        parts = PurePosixPath(relative).parts
        if (path.is_symlink() or not parts or any(part in {".", ".."} for part in parts)
                or not path.is_file() and not path.is_dir()):
            raise PublicTaskError(f"task path is unsafe: {relative}")
        if path.is_file():
            result[relative] = path
    return result


def build(task_id: str) -> dict:
    if not re.fullmatch(r"P0[3-8]", task_id):
        raise PublicTaskError("public task id must be P03 through P08")
    task_root = FIXTURES / task_id
    provenance = json.loads((task_root / "provenance.json").read_text(
        encoding="utf-8"))
    if (provenance.get("schema_version") != 1 or provenance.get("id") != task_id
            or provenance.get("issue_origin") not in {
                "upstream-fix", "upstream-feature", "authored-regression"}
            or provenance.get("licence") not in SUPPORTED_LICENCES
            or not all(isinstance(provenance.get(key), str)
                       and HEX.fullmatch(provenance[key])
                       for key in ("source_commit", "fix_commit"))):
        raise PublicTaskError("task provenance is incomplete or unsupported")
    actor_root = task_root / "actor"
    actor = paths(actor_root)
    editable = provenance["editable_paths"]
    package = provenance["package_path"]
    if (not isinstance(editable, list) or not 2 <= len(editable) <= 8
            or len(set(editable)) != len(editable)
            or any(name not in actor or not name.endswith(".py") for name in editable)
            or not isinstance(package, str) or not package.isidentifier()):
        raise PublicTaskError("task edit or package scope is invalid")
    source_files = {name: path for name, path in actor.items()
                    if name.startswith(package + "/")}
    source_lines = sum(len(path.read_text(encoding="utf-8").splitlines())
                       for name, path in source_files.items() if name.endswith(".py"))
    total_bytes = sum(path.stat().st_size for path in actor.values())
    if (not 1000 <= source_lines <= 20000 or len(actor) > 200
            or total_bytes > 5_000_000 or not source_files
            or provenance["licence_file"] not in actor
            or sha(actor[provenance["licence_file"]]) != provenance["licence_sha256"]):
        raise PublicTaskError("task source, package size or licence is ineligible")
    acceptance = json.loads(actor["acceptance.json"].read_text(encoding="utf-8"))
    if (acceptance != {"schema_version": 1,
                       "public_command": ["python3", "-B", "public_check.py"],
                       "editable_paths": editable}
            or "ISSUE.md" not in actor or "public_check.py" not in actor):
        raise PublicTaskError("actor acceptance contract is incomplete")
    reference = paths(task_root / "reference")
    if set(reference) != set(editable):
        raise PublicTaskError("reference overlay must replace the editable files")
    partial = paths(task_root / "partial")
    if set(partial) != set(editable):
        raise PublicTaskError("partial overlay must replace the editable files")
    alternative_root = task_root / "alternative"
    alternative = paths(alternative_root) if alternative_root.exists() else {}
    if alternative and set(alternative) != set(editable):
        raise PublicTaskError("alternative overlay must replace the editable files")
    oracle_path = ORACLES / provenance["oracle_file"]
    case_path = ORACLES / provenance["case_file"]
    if (oracle_path.is_symlink() or case_path.is_symlink()
            or not oracle_path.is_file() or not case_path.is_file()):
        raise PublicTaskError("root-owned oracle or case source is missing")
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    if (oracle.get("schema_version") != 1 or not isinstance(oracle.get("cases"), list)
            or not oracle["cases"] or sum(row["weight"] for row in oracle["cases"]) != 100):
        raise PublicTaskError("hidden oracle weights do not total 100")
    value = {**provenance,
             "provenance_sha256": sha(task_root / "provenance.json"),
             "actor_files": {name: sha(path) for name, path in actor.items()},
             "reference_files": {name: sha(path) for name, path in reference.items()},
             "partial_files": {name: sha(path) for name, path in partial.items()},
             "alternative_files": {name: sha(path) for name, path in alternative.items()},
             "source_python_lines": source_lines,
             "actor_file_count": len(actor), "actor_bytes": total_bytes,
             "oracle_sha256": sha(oracle_path),
             "case_source_sha256": sha(case_path)}
    return {**value, "task_sha256": digest(value)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    try:
        value = build(args.task_id)
        output = FIXTURES / args.task_id / "task.json"
        if args.prepare:
            output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8", newline="\n")
        elif json.loads(output.read_text(encoding="utf-8")) != value:
            raise PublicTaskError("task catalogue differs from frozen bytes")
        print(f"PASS: {args.task_id} source, licence, reference and oracle "
              f"{value['task_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, PublicTaskError) as exc:
        print(f"BLOCKED: Q3 public task {args.task_id}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
