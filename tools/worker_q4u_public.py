#!/usr/bin/env python3
"""Verify and calibrate the frozen Q4U D01W public actor without a provider.

The actor contains only upstream pre-fix source and public instructions.
Reference overlays and the evaluator live in a sealed, non-indexed ZIP that
is never copied into an actor workspace. This module has no dispatch path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "test/fixtures/worker_q4u_public/D01W/task.json"
ACTOR = TASK.parent / "actor"
EVALUATOR = ROOT / "test/oracles/worker_q4u_public/D01W.zip"
TASK_IDS = {"D01W": ("partial", "weak"), "D01S": ("direct", "strong")}
SOURCE_FILES = {
    "src/dotenv/__init__.py", "src/dotenv/__main__.py",
    "src/dotenv/cli.py", "src/dotenv/ipython.py", "src/dotenv/main.py",
    "src/dotenv/parser.py", "src/dotenv/py.typed",
    "src/dotenv/variables.py", "src/dotenv/version.py",
}
EDITABLE = ("src/dotenv/main.py", "src/dotenv/parser.py")
ACTOR_FILES = SOURCE_FILES | {"LICENSE", "ISSUE.md", "public_check.py",
                              "acceptance.json"}
ZIP_FILES = {"grader.py", "oracle.json", "LICENSE"} | {
    f"{variant}/{name}" for variant in ("reference", "partial")
    for name in EDITABLE}
EXPECTED_CASES = {"round_trip_double_slash", "round_trip_quote_and_slash",
                  "single_quote_boundary", "double_quote_boundary",
                  "plain_and_single_slash_controls"}


class Q4UCorpusError(ValueError):
    """The frozen actor, evaluator or calibration result cannot be trusted."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def paths(root: Path) -> dict[str, Path]:
    if not root.is_dir() or root.is_symlink():
        raise Q4UCorpusError(f"actor directory is missing or linked: {root}")
    files: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise Q4UCorpusError(f"actor contains a symlink: {path}")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = path
    return files


def check(task_path: Path = TASK, evaluator_path: Path = EVALUATOR) -> dict:
    """Recompute the complete public inventory and sealed evaluator binding."""
    actor = task_path.parent / "actor"
    task_id = task_path.parent.name
    if task_path.is_symlink() or evaluator_path.is_symlink():
        raise Q4UCorpusError("task or evaluator is a symlink")
    task = json.loads(task_path.read_text(encoding="utf-8"))
    if (not isinstance(task, dict) or task_id not in TASK_IDS
            or task.get("schema_version") != 1 or task.get("id") != task_id
            or task.get("origin") != "pinned-upstream-regression"
            or task.get("source_url") != "https://github.com/theskumar/python-dotenv"
            or task.get("source_commit") != "751f8c148222e58aa173c83c4e5e6cfccb2cc124"
            or task.get("fix_commit") != "f7b18d9c72d1abcc2ad4023424b84f5bee30d266"
            or task.get("licence") != "BSD-3-Clause"
            or task.get("editable_paths") != list(EDITABLE)
            or task.get("public_coverage") != TASK_IDS[task_id][0]
            or task.get("public_check_variant") != TASK_IDS[task_id][1]
            or task.get("task_sha256") != digest({
                key: value for key, value in task.items() if key != "task_sha256"})):
        raise Q4UCorpusError("D01W provenance, scope or task digest differs")
    found = paths(actor)
    if set(found) != ACTOR_FILES or set(task.get("actor_files", {})) != ACTOR_FILES:
        raise Q4UCorpusError("D01W actor file inventory differs")
    for name, path in found.items():
        if sha(path.read_bytes()) != task["actor_files"][name]:
            raise Q4UCorpusError(f"D01W actor byte changed: {name}")
    if sha(found["LICENSE"].read_bytes()) != task["licence_sha256"]:
        raise Q4UCorpusError("D01W licence bytes differ")
    contract = json.loads(found["acceptance.json"].read_text(encoding="utf-8"))
    if contract != {"schema_version": 1,
                    "public_command": ["python3", "-B", "public_check.py"],
                    "editable_paths": list(EDITABLE),
                    "require_changed_output": True}:
        raise Q4UCorpusError("D01W public acceptance metadata differs")
    raw = evaluator_path.read_bytes()
    if sha(raw) != task.get("evaluator_zip_sha256"):
        raise Q4UCorpusError("D01W evaluator seal differs")
    with zipfile.ZipFile(evaluator_path) as archive:
        members = archive.infolist()
        names = [item.filename for item in members]
        if (len(names) != len(set(names)) or set(names) != ZIP_FILES
                or any(item.is_dir() or item.file_size > 100_000
                       or stat.S_ISLNK(item.external_attr >> 16)
                       or item.filename.startswith("/")
                       or ".." in Path(item.filename).parts
                       for item in members)):
            raise Q4UCorpusError("D01W evaluator archive inventory is unsafe")
        if archive.read("LICENSE") != found["LICENSE"].read_bytes():
            raise Q4UCorpusError("D01W evaluator licence differs")
        oracle = json.loads(archive.read("oracle.json"))
        weights = oracle.get("case_weights")
        if (oracle.get("schema_version") != 1 or not isinstance(weights, dict)
                or set(weights) != EXPECTED_CASES
                or any(type(value) is not int or value <= 0 for value in weights.values())
                or sum(weights.values()) != 100
                or oracle.get("reference_commit") != task["fix_commit"]
                or oracle.get("partial_mechanism") != "writer-only"):
            raise Q4UCorpusError("D01W evaluator oracle differs")
    return {"task_id": task_id, "task_sha256": task["task_sha256"],
            "evaluator_zip_sha256": task["evaluator_zip_sha256"],
            "actor_file_count": len(found), "editable_paths": list(EDITABLE)}


def check_upstream(repo: Path, task_path: Path = TASK) -> dict:
    """Optional proof that actor and overlays match the pinned Git objects."""
    task = json.loads(task_path.read_text(encoding="utf-8"))
    actor = task_path.parent / "actor"
    check(task_path)

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", "-c", "safe.directory=*", "-C",
                                        str(repo), *args], timeout=30)

    if git("rev-parse", f"{task['fix_commit']}^").decode().strip() != task["source_commit"]:
        raise Q4UCorpusError("upstream fix has a different parent")
    for name in SOURCE_FILES | {"LICENSE"}:
        if (actor / name).read_bytes() != git("show", f"{task['source_commit']}:{name}"):
            raise Q4UCorpusError(f"D01W actor differs from upstream: {name}")
    with zipfile.ZipFile(EVALUATOR) as archive:
        for name in EDITABLE:
            if archive.read(f"reference/{name}") != git("show", f"{task['fix_commit']}:{name}"):
                raise Q4UCorpusError(f"D01W reference differs from upstream: {name}")
            partial_commit = task["fix_commit"] if name.endswith("main.py") else task["source_commit"]
            if archive.read(f"partial/{name}") != git("show", f"{partial_commit}:{name}"):
                raise Q4UCorpusError(f"D01W partial differs from upstream: {name}")
    return {"source_commit": task["source_commit"],
            "fix_commit": task["fix_commit"], "upstream_verified": True}


def _process(code_or_file: str, root: Path, *, code: bool) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(root / "src"),
           "PYTHONNOUSERSITE": "1"}
    command = [sys.executable, "-B", "-S"] + (["-c", code_or_file] if code else [code_or_file])
    return subprocess.run(command, cwd=root, env=env, text=True,
                          capture_output=True, timeout=30)


def _run(code_or_file: str, root: Path, *, code: bool) -> str:
    result = _process(code_or_file, root, code=code)
    if result.returncode:
        raise Q4UCorpusError(f"D01W {'oracle' if code else 'public check'} failed: "
                            f"{result.stderr[-1000:]}")
    return result.stdout


def calibrate(task_path: Path = TASK) -> dict:
    """Run identical public/hidden checks on baseline, partial and reference."""
    binding = check(task_path)
    actor_source = task_path.parent / "actor"
    temp_parent = ROOT / "pilot-runs/q4u-calibration-temp"
    temp_parent.mkdir(parents=True, exist_ok=True)
    if not temp_parent.resolve().is_relative_to(ROOT.resolve()):
        raise Q4UCorpusError("calibration temporary root escaped workspace")
    with zipfile.ZipFile(EVALUATOR) as archive:
        grader = archive.read("grader.py").decode("utf-8")
        weights = json.loads(archive.read("oracle.json"))["case_weights"]
        with tempfile.TemporaryDirectory(prefix="d01w-", dir=temp_parent) as temporary:
            work = Path(temporary).resolve()
            if not work.is_relative_to(temp_parent.resolve()):
                raise Q4UCorpusError("calibration workspace escaped temporary root")
            grades = {}
            for variant in ("baseline", "partial", "reference"):
                actor = work / variant
                shutil.copytree(actor_source, actor)
                if variant != "baseline":
                    for name in EDITABLE:
                        (actor / name).write_bytes(archive.read(f"{variant}/{name}"))
                before = {name: sha(path.read_bytes()) for name, path in paths(actor).items()}
                module_path = _run("import dotenv; print(dotenv.__file__)", actor,
                                   code=True).strip()
                if Path(module_path).resolve() != (actor / "src/dotenv/__init__.py").resolve():
                    raise Q4UCorpusError("calibration imported a non-actor dotenv")
                public = _process("public_check.py", actor, code=False)
                if public.returncode and "AssertionError" not in public.stderr:
                    raise Q4UCorpusError(f"D01W public check could not run: {public.stderr[-1000:]}")
                outcome = json.loads(_run(grader, actor, code=True))
                if (outcome.get("schema_version") != 1
                        or outcome.get("weights") != weights
                        or set(outcome.get("cases", {})) != EXPECTED_CASES
                        or any(type(value) is not bool for value in outcome["cases"].values())
                        or outcome.get("score") != sum(
                            weights[name] for name, passed in outcome["cases"].items() if passed)
                        or before != {name: sha(path.read_bytes())
                                      for name, path in paths(actor).items()}):
                    raise Q4UCorpusError(f"D01W {variant} grade or source integrity differs")
                grades[variant] = {"public_pass": public.returncode == 0, **outcome}
    if ([grades[name]["score"] for name in ("baseline", "partial", "reference")]
            != [15, 55, 100] or not all(grades["reference"]["cases"].values())
            or grades["baseline"]["cases"]["round_trip_double_slash"]
            or grades["partial"]["cases"]["single_quote_boundary"]
            or [grades[name]["public_pass"] for name in
                ("baseline", "partial", "reference")]
                != ([True, True, True] if binding["task_id"] == "D01W"
                    else [False, False, True])):
        raise Q4UCorpusError("D01W baseline/partial/reference separation failed")
    return {"schema_version": 1, "task_id": binding["task_id"],
            "task_sha256": binding["task_sha256"],
            "evaluator_zip_sha256": binding["evaluator_zip_sha256"],
            "provider_calls": 0, "python_version": sys.version.split()[0],
            "grades": grades}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--calibrate", action="store_true")
    mode.add_argument("--upstream-repo", type=Path)
    parser.add_argument("--task", choices=sorted(TASK_IDS), default="D01W")
    args = parser.parse_args()
    task_path = ROOT / "test/fixtures/worker_q4u_public" / args.task / "task.json"
    try:
        value = (check(task_path) if args.check else
                 calibrate(task_path) if args.calibrate else
                 check_upstream(args.upstream_repo, task_path))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            zipfile.BadZipFile) as error:
        print(f"BLOCKED: Q4U D01W: {error}", file=sys.stderr)
        return 2
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
