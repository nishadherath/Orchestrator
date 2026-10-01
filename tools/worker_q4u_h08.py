#!/usr/bin/env python3
"""Verify and calibrate sealed H08 single-module reconciliation tasks."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "test/fixtures/worker_q4u_public"
EVALUATOR = ROOT / "test/oracles/worker_q4u_public/H08.zip"
IDS = {"H08W": ("partial", "weak"), "H08S": ("direct", "strong")}
EDITABLE = ["reconcile.py"]
FILES = {"ISSUE.md", "LICENSE", "acceptance.json", "public_check.py",
         "reconcile.py"}
ZIP_FILES = {"grader.py", "oracle.json", "LICENSE",
             "partial/reconcile.py", "reference/reconcile.py"}
WEIGHTS = {"newer_put": 30, "stale_update": 35,
           "tombstone_blocks_resurrection": 35}


class H08Error(ValueError):
    """H08 actor, evaluator or calibration differs from the frozen task."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def check(task_id: str, *, fixtures: Path = FIXTURES,
          evaluator: Path = EVALUATOR) -> dict:
    if task_id not in IDS:
        raise H08Error(f"unknown H08 task: {task_id}")
    folder = fixtures / task_id
    task_path, actor = folder / "task.json", folder / "actor"
    if task_path.is_symlink() or actor.is_symlink() or evaluator.is_symlink():
        raise H08Error("H08 paths must not be symlinks")
    task = json.loads(task_path.read_text(encoding="utf-8"))
    actual = {}
    for path in actor.rglob("*"):
        if path.is_symlink():
            raise H08Error("H08 actor contains a symlink")
        if path.is_file():
            actual[path.relative_to(actor).as_posix()] = sha(path.read_bytes())
    if (set(actual) != FILES or task.get("actor_files") != actual
            or task.get("schema_version") != 1 or task.get("id") != task_id
            or task.get("origin") != "authored-synthetic-regression"
            or task.get("split") != "development"
            or task.get("mechanism") != "monotonic-event-tombstones"
            or task.get("task_kind") != "implementation"
            or task.get("change_required") is not True
            or task.get("editable_paths") != EDITABLE
            or task.get("public_coverage") != IDS[task_id][0]
            or task.get("public_check_variant") != IDS[task_id][1]
            or task.get("licence") != "Apache-2.0"
            or task.get("licence_sha256") != actual["LICENSE"]
            or task.get("task_sha256") != digest({
                key: value for key, value in task.items() if key != "task_sha256"})):
        raise H08Error("H08 actor or task differs")
    metadata = json.loads((actor / "acceptance.json").read_text(encoding="utf-8"))
    if metadata != {"schema_version": 1,
                    "public_command": ["python3", "-B", "public_check.py"],
                    "editable_paths": EDITABLE, "require_changed_output": True}:
        raise H08Error("H08 acceptance metadata differs")
    if sha(evaluator.read_bytes()) != task["evaluator_zip_sha256"]:
        raise H08Error("H08 evaluator seal differs")
    with zipfile.ZipFile(evaluator) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (len(names) != len(set(names)) or set(names) != ZIP_FILES
                or any(entry.is_dir() or entry.file_size > 30_000
                       or stat.S_ISLNK(entry.external_attr >> 16)
                       or entry.filename.startswith("/")
                       or ".." in Path(entry.filename).parts for entry in entries)):
            raise H08Error("H08 evaluator inventory is unsafe")
        oracle = json.loads(archive.read("oracle.json"))
        if oracle != {"schema_version": 1, "mechanism": "monotonic-event-tombstones",
                      "weights": WEIGHTS,
                      "partial_variant": "stale-filter-without-tombstone"}:
            raise H08Error("H08 evaluator metadata differs")
        if archive.read("LICENSE") != (actor / "LICENSE").read_bytes():
            raise H08Error("H08 evaluator licence differs")
    return {"task_id": task_id, "task_sha256": task["task_sha256"],
            "evaluator_zip_sha256": task["evaluator_zip_sha256"],
            "actor_file_count": len(actual)}


def calibrate(task_id: str, *, fixtures: Path = FIXTURES,
              evaluator: Path = EVALUATOR) -> dict:
    binding = check(task_id, fixtures=fixtures, evaluator=evaluator)
    with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
        temporary = Path(directory)
        grader = temporary / "grader.py"
        with zipfile.ZipFile(evaluator) as archive:
            grader.write_bytes(archive.read("grader.py"))
            overlays = {name: archive.read(name) for name in ZIP_FILES
                        if name.startswith(("partial/", "reference/"))}
        grades = {}
        for variant in ("baseline", "partial", "reference"):
            actor = temporary / variant
            shutil.copytree(fixtures / task_id / "actor", actor)
            for name, data in overlays.items():
                if name.startswith(variant + "/"):
                    (actor / name.split("/", 1)[1]).write_bytes(data)
            public = subprocess.run([sys.executable, "-B", "-S", "public_check.py"],
                                    cwd=actor, capture_output=True, text=True,
                                    timeout=15)
            graded = subprocess.run([sys.executable, "-B", "-S", str(grader),
                                     str(actor)], cwd=temporary, capture_output=True,
                                    text=True, timeout=15)
            if graded.returncode:
                raise H08Error(f"{task_id} {variant} grader failed: {graded.stderr}")
            result = json.loads(graded.stdout)
            expected = {"baseline": 30, "partial": 65, "reference": 100}[variant]
            public_expected = task_id.endswith("W") or variant == "reference"
            if (result.get("schema_version") != 1
                    or result.get("score") != expected
                    or result.get("weights") != WEIGHTS
                    or (public.returncode == 0) != public_expected):
                raise H08Error(f"{task_id} {variant} calibration differs: "
                               f"{public.stderr} {result}")
            grades[variant] = {**result, "public_pass": public.returncode == 0}
    return {"schema_version": 1, **binding, "grades": grades,
            "provider_calls": 0, "python_version": sys.version.split()[0]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(IDS), required=True)
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = calibrate(args.task) if args.calibrate else check(args.task)
        if args.output:
            if args.output.exists():
                raise H08Error(f"refusing to overwrite: {args.output}")
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8", newline="\n")
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired,
            zipfile.BadZipFile) as error:
        print(f"BLOCKED: H08: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
