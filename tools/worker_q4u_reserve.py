#!/usr/bin/env python3
"""Verify and calibrate the sealed R09/R10 implementation reserve offline."""
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
SPECS = {
    "R09": {"mechanism": "chunk-boundary-frames",
            "editable": ["frame_parser.py"],
            "actor": {"ISSUE.md", "LICENSE", "acceptance.json",
                      "public_check.py", "frame_parser.py"},
            "overlays": {"partial/frame_parser.py", "reference/frame_parser.py"},
            "weights": {"ordinary": 30, "cross_chunk": 35,
                        "final_delimiter": 35},
            "partial": "buffer-with-trailing-empty"},
    "R10": {"mechanism": "invoice-subtotal-tax-rounding",
            "editable": ["billing/tax.py", "billing/invoice.py"],
            "actor": {"ISSUE.md", "LICENSE", "acceptance.json",
                      "public_check.py", "billing/__init__.py",
                      "billing/tax.py", "billing/invoice.py"},
            "overlays": {"partial/billing/tax.py",
                         "reference/billing/tax.py",
                         "reference/billing/invoice.py"},
            "weights": {"ordinary": 30, "half_up": 35, "subtotal_once": 35},
            "partial": "tax-rounding-only"},
}


class ReserveError(ValueError):
    """A reserved implementation, evaluator or calibration has drifted."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def check(task_id: str, *, fixtures: Path = FIXTURES,
          oracles: Path = ORACLES) -> dict:
    if task_id not in SPECS:
        raise ReserveError(f"unknown reserved implementation: {task_id}")
    spec = SPECS[task_id]
    folder = fixtures / task_id
    task_path, actor, archive_path = (folder / "task.json", folder / "actor",
                                      oracles / f"{task_id}.zip")
    if task_path.is_symlink() or actor.is_symlink() or archive_path.is_symlink():
        raise ReserveError("reserve paths must not be symlinks")
    task = json.loads(task_path.read_text(encoding="utf-8"))
    actual = {}
    for path in actor.rglob("*"):
        if path.is_symlink():
            raise ReserveError("reserve actor contains a symlink")
        if path.is_file():
            actual[path.relative_to(actor).as_posix()] = sha(path.read_bytes())
    if (set(actual) != spec["actor"] or task.get("actor_files") != actual
            or task.get("schema_version") != 1 or task.get("id") != task_id
            or task.get("origin") != "authored-synthetic-regression"
            or task.get("split") != "reserved"
            or task.get("mechanism") != spec["mechanism"]
            or task.get("task_kind") != "implementation"
            or task.get("change_required") is not True
            or task.get("editable_paths") != spec["editable"]
            or task.get("public_coverage") != "partial"
            or task.get("public_check_variant") != "weak"
            or task.get("licence") != "Apache-2.0"
            or task.get("licence_sha256") != actual["LICENSE"]
            or task.get("task_sha256") != digest({
                key: value for key, value in task.items() if key != "task_sha256"})):
        raise ReserveError("reserve actor or task differs")
    metadata = json.loads((actor / "acceptance.json").read_text(encoding="utf-8"))
    if metadata != {"schema_version": 1,
                    "public_command": ["python3", "-B", "public_check.py"],
                    "editable_paths": spec["editable"],
                    "require_changed_output": True}:
        raise ReserveError("reserve acceptance metadata differs")
    if sha(archive_path.read_bytes()) != task["evaluator_zip_sha256"]:
        raise ReserveError("reserve evaluator seal differs")
    with zipfile.ZipFile(archive_path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (len(names) != len(set(names))
                or set(names) != {"grader.py", "oracle.json", "LICENSE", *spec["overlays"]}
                or any(entry.is_dir() or entry.file_size > 30_000
                       or stat.S_ISLNK(entry.external_attr >> 16)
                       or entry.filename.startswith("/")
                       or ".." in Path(entry.filename).parts for entry in entries)):
            raise ReserveError("reserve evaluator inventory is unsafe")
        oracle = json.loads(archive.read("oracle.json"))
        if oracle != {"schema_version": 1,
                      "mechanism": spec["mechanism"],
                      "weights": spec["weights"],
                      "partial_variant": spec["partial"]}:
            raise ReserveError("reserve evaluator metadata differs")
        if archive.read("LICENSE") != (actor / "LICENSE").read_bytes():
            raise ReserveError("reserve evaluator licence differs")
    return {"task_id": task_id, "task_sha256": task["task_sha256"],
            "evaluator_zip_sha256": task["evaluator_zip_sha256"],
            "actor_file_count": len(actual)}


def calibrate(task_id: str, *, fixtures: Path = FIXTURES,
              oracles: Path = ORACLES) -> dict:
    binding = check(task_id, fixtures=fixtures, oracles=oracles)
    spec = SPECS[task_id]
    with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
        temporary = Path(directory)
        grader = temporary / "grader.py"
        with zipfile.ZipFile(oracles / f"{task_id}.zip") as archive:
            grader.write_bytes(archive.read("grader.py"))
            overlays = {name: archive.read(name) for name in spec["overlays"]}
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
            if public.returncode or graded.returncode:
                raise ReserveError(f"{task_id} {variant} process failed: "
                                   f"{public.stderr} {graded.stderr}")
            result = json.loads(graded.stdout)
            expected = {"baseline": 30, "partial": 65, "reference": 100}[variant]
            if (result.get("schema_version") != 1
                    or result.get("score") != expected
                    or result.get("weights") != spec["weights"]):
                raise ReserveError(f"{task_id} {variant} grade differs: {result}")
            grades[variant] = {**result, "public_pass": True}
    return {"schema_version": 1, **binding, "grades": grades,
            "provider_calls": 0, "python_version": sys.version.split()[0]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=sorted(SPECS), required=True)
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = calibrate(args.task) if args.calibrate else check(args.task)
        if args.output:
            if args.output.exists():
                raise ReserveError(f"refusing to overwrite: {args.output}")
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8", newline="\n")
        print(json.dumps(result, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired,
            zipfile.BadZipFile) as error:
        print(f"BLOCKED: Q4U reserve: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
