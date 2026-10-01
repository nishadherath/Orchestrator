#!/usr/bin/env python3
"""Validate and freeze the independent Q4S public corpus without model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from worker_adapter import digest
from worker_q3_public_catalogue import SUPPORTED_LICENCES, paths
from worker_q4s_public_source import FIXTURES, SOURCES


ROOT = Path(__file__).resolve().parent.parent
ORACLES = ROOT / "test/oracles/worker_q4s_public"
HEX = re.compile(r"[0-9a-f]{40}\Z")


class CorpusError(RuntimeError):
    """A Q4S corpus record does not match its frozen inputs."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(task_id: str) -> dict:
    if task_id not in SOURCES:
        raise CorpusError(f"unknown Q4S family: {task_id}")
    root = FIXTURES / task_id
    provenance_path = root / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if (provenance.get("schema_version") != 1 or provenance.get("id") != task_id
            or provenance.get("issue_origin") != "authored-regression"
            or not provenance.get("authored_rationale")
            or provenance.get("licence") not in SUPPORTED_LICENCES
            or any(not isinstance(provenance.get(key), str)
                   or not HEX.fullmatch(provenance[key])
                   for key in ("source_commit", "fix_commit"))
            or provenance.get("upstream_change_url")
            != provenance.get("source_url", "") + "/commit/" + provenance.get("fix_commit", "")):
        raise CorpusError(f"{task_id}: incomplete or inconsistent provenance")
    actor = paths(root / "actor")
    package = provenance["package_path"]
    editable = provenance["editable_paths"]
    if (not isinstance(package, str) or not package.isidentifier()
            or not isinstance(editable, list)
            or not 2 <= len(editable) <= 8 or len(set(editable)) != len(editable)
            or any(name not in actor or not name.endswith(".py") for name in editable)):
        raise CorpusError(f"{task_id}: invalid editable scope")
    source_files = {name: path for name, path in actor.items()
                    if name.startswith(package + "/")}
    source_lines = sum(len(path.read_text(encoding="utf-8").splitlines())
                       for name, path in source_files.items() if name.endswith(".py"))
    actor_bytes = sum(path.stat().st_size for path in actor.values())
    if (not 1000 <= source_lines <= 20000 or len(actor) > 200
            or actor_bytes > 5_000_000
            or provenance["licence_file"] not in actor
            or sha(actor[provenance["licence_file"]]) != provenance["licence_sha256"]):
        raise CorpusError(f"{task_id}: source size or licence ineligible")
    acceptance = json.loads(actor["acceptance.json"].read_text(encoding="utf-8"))
    if (acceptance != {"schema_version": 1,
                       "public_command": ["python3", "-B", "public_check.py"],
                       "editable_paths": editable}
            or "ISSUE.md" not in actor or "public_check.py" not in actor):
        raise CorpusError(f"{task_id}: public contract incomplete")
    reference = paths(root / "reference")
    partial = paths(root / "partial")
    if set(reference) != set(editable) or set(partial) != set(editable):
        raise CorpusError(f"{task_id}: overlay scope differs from editable scope")
    oracle_path = ORACLES / provenance["oracle_file"]
    case_path = ORACLES / provenance["case_file"]
    if (oracle_path.is_symlink() or case_path.is_symlink()
            or not oracle_path.is_file() or not case_path.is_file()
            or oracle_path.is_relative_to(root / "actor")
            or case_path.is_relative_to(root / "actor")):
        raise CorpusError(f"{task_id}: protected oracle missing or exposed")
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    cases = oracle.get("cases", [])
    if (oracle.get("schema_version") != 1 or not isinstance(cases, list)
            or len(cases) < 3 or sum(row["weight"] for row in cases) != 100
            or len({row["input"]["case"] for row in cases}) != len(cases)
            or any(row.get("expected") != {"ok": True} for row in cases)):
        raise CorpusError(f"{task_id}: invalid protected oracle")
    value = {**provenance,
             "provenance_sha256": sha(provenance_path),
             "actor_files": {name: sha(path) for name, path in actor.items()},
             "reference_files": {name: sha(path) for name, path in reference.items()},
             "partial_files": {name: sha(path) for name, path in partial.items()},
             "source_python_lines": source_lines, "actor_file_count": len(actor),
             "actor_bytes": actor_bytes, "oracle_sha256": sha(oracle_path),
             "case_source_sha256": sha(case_path)}
    return {**value, "task_sha256": digest(value)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.prepare == args.check:
        parser.error("choose exactly one of --prepare or --check")
    try:
        for task_id in SOURCES:
            value = build(task_id)
            path = FIXTURES / task_id / "task.json"
            if args.prepare:
                if path.exists():
                    raise CorpusError(f"{task_id}: refusing to overwrite frozen task digest")
                path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
            elif json.loads(path.read_text(encoding="utf-8")) != value:
                raise CorpusError(f"{task_id}: task digest or inventory changed")
            print(f"PASS: {task_id} {value['task_sha256']} "
                  f"{value['source_python_lines']} source lines")
        return 0
    except (OSError, ValueError, KeyError, TypeError, CorpusError) as error:
        print(f"BLOCKED: Q4S corpus: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
