#!/usr/bin/env python3
"""Verify and calibrate the sealed C03/C04 no-edit controls offline."""
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
ORACLES = ROOT / "test/oracles/worker_q4u_public"
IDS = {"C03": ("allocation.py", "integer-largest-remainder-allocation"),
       "C04": ("labels.py", "unicode-label-canonicalisation"),
       "R11": ("intervals.py", "half-open-interval-coalescing")}


class ControlError(ValueError):
    """A synthetic control or its calibration has drifted."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def check(task_id: str, *, fixtures: Path = FIXTURES,
          oracles: Path = ORACLES) -> dict:
    """Recompute actor/task/archive seals; never trust task-provided paths."""
    if task_id not in IDS:
        raise ControlError(f"unknown no-edit control: {task_id}")
    module, mechanism = IDS[task_id]
    folder = fixtures / task_id
    task_path, actor, archive_path = (folder / "task.json", folder / "actor",
                                      oracles / f"{task_id}.zip")
    if task_path.is_symlink() or actor.is_symlink() or archive_path.is_symlink():
        raise ControlError("control paths must not be symlinks")
    task = json.loads(task_path.read_text(encoding="utf-8"))
    expected_files = {"ISSUE.md", "LICENSE", "acceptance.json",
                      "public_check.py", module}
    actual = {}
    for path in actor.rglob("*"):
        if path.is_symlink():
            raise ControlError("actor has a symlink")
        if path.is_file():
            actual[path.relative_to(actor).as_posix()] = sha(path.read_bytes())
    if (set(actual) != expected_files or task.get("actor_files") != actual
            or task.get("schema_version") != 1 or task.get("id") != task_id
            or task.get("origin") != "authored-synthetic-control"
            or task.get("split") != ("reserved" if task_id == "R11" else "development")
            or task.get("mechanism") != mechanism
            or task.get("task_kind") != "investigation"
            or task.get("change_required") is not False
            or task.get("editable_paths") != [module]
            or task.get("licence") != "Apache-2.0"
            or task.get("licence_sha256") != actual["LICENSE"]
            or task.get("task_sha256") != digest({
                key: value for key, value in task.items() if key != "task_sha256"})):
        raise ControlError("control actor or task differs")
    metadata = json.loads((actor / "acceptance.json").read_text(encoding="utf-8"))
    if metadata != {"schema_version": 1,
                    "public_command": ["python3", "-B", "public_check.py"],
                    "editable_paths": [module], "require_changed_output": False}:
        raise ControlError("no-edit acceptance metadata differs")
    if sha(archive_path.read_bytes()) != task["evaluator_zip_sha256"]:
        raise ControlError("control evaluator seal differs")
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (len(names) != len(set(names))
                or set(names) != {"grader.py", "oracle.json", "LICENSE",
                                      f"partial/{module}"}
                or any(entry.is_dir() or entry.file_size > 30_000
                       or stat.S_ISLNK(entry.external_attr >> 16)
                       or entry.filename.startswith("/")
                       or ".." in Path(entry.filename).parts for entry in entries)):
            raise ControlError("control evaluator inventory is unsafe")
        oracle = json.loads(archive.read("oracle.json"))
        if oracle != {"schema_version": 1, "id": task_id, "module": module,
                      "source_sha256": actual[module], "mechanism": mechanism,
                      "reference_is_baseline": True,
                      "partial_variant": "behaviour-preserving-unnecessary-edit"}:
            raise ControlError("control evaluator metadata differs")
        if (archive.read("LICENSE") != (actor / "LICENSE").read_bytes()
                or archive.read(f"partial/{module}") !=
                b"# unnecessary edit\n" + (actor / module).read_bytes()):
            raise ControlError("control evaluator overlay differs")
    return {"task_id": task_id, "task_sha256": task["task_sha256"],
            "evaluator_zip_sha256": task["evaluator_zip_sha256"],
            "actor_file_count": len(actual)}


def calibrate(task_id: str, *, fixtures: Path = FIXTURES,
              oracles: Path = ORACLES) -> dict:
    """Show correct baseline/reference and penalised unnecessary-edit partial."""
    binding = check(task_id, fixtures=fixtures, oracles=oracles)
    module = IDS[task_id][0]
    with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
        temporary = Path(directory)
        evaluator = temporary / "evaluator"
        evaluator.mkdir()
        with zipfile.ZipFile(oracles / f"{task_id}.zip") as archive:
            for name in ("grader.py", "oracle.json"):
                (evaluator / name).write_bytes(archive.read(name))
            partial_source = archive.read(f"partial/{module}")
        grades = {}
        for variant in ("baseline", "partial", "reference"):
            actor = temporary / variant
            shutil.copytree(fixtures / task_id / "actor", actor)
            if variant == "partial":
                (actor / module).write_bytes(partial_source)
            public = subprocess.run([sys.executable, "-B", "-S", "public_check.py"],
                                    cwd=actor, capture_output=True, text=True,
                                    timeout=15)
            graded = subprocess.run([sys.executable, "-B", "-S",
                                     str(evaluator / "grader.py"), str(actor)],
                                    cwd=evaluator, capture_output=True,
                                    text=True, timeout=15)
            if public.returncode or graded.returncode:
                raise ControlError(f"{task_id} {variant} calibration failed: "
                                   f"{public.stderr} {graded.stderr}")
            result = json.loads(graded.stdout)
            expected = 0 if variant == "partial" else 100
            if (result.get("schema_version") != 1
                    or result.get("task_id") != task_id
                    or result.get("score") != expected
                    or result.get("unchanged") is not (variant != "partial")
                    or not all(value is True for value in result["cases"].values())):
                raise ControlError(f"{task_id} {variant} grade differs")
            grades[variant] = {**result, "public_pass": True}
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
                raise ControlError(f"refusing to overwrite: {args.output}")
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8", newline="\n")
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired,
            zipfile.BadZipFile) as error:
        print(f"BLOCKED: Q4U no-edit control: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
