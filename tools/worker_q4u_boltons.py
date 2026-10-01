#!/usr/bin/env python3
"""Verify and calibrate the frozen boltons B02 resource task without a provider."""
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
FIXTURES = ROOT / "test/fixtures/worker_q4u_public"
EVALUATOR = ROOT / "test/oracles/worker_q4u_public/B02.zip"
IDS = {"B02W": ("partial", "weak"), "B02S": ("direct", "strong")}
PARENT = "435774ef8b10c1355bf77483a837945034011754"
FIX = "f1034b07ddf71f4d9285134a47a4ade16fe40789"
EDITABLE = "boltons/jsonutils.py"
ACTOR_FILES = {"boltons/__init__.py", EDITABLE, "LICENSE", "ISSUE.md",
               "public_check.py", "acceptance.json"}
ZIP_FILES = {"grader.py", "oracle.json", "LICENSE",
             f"reference/{EDITABLE}", f"partial/{EDITABLE}"}
WEIGHTS = {"mid_final_line_terminates": 35,
           "negative_seek_matches_positive": 35,
           "positive_seek_keeps_tail": 15, "full_forward": 15}


class B02Error(ValueError):
    """A B02 actor, evaluator, provenance or calibration check failed."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def actor_files(root: Path) -> dict[str, Path]:
    if not root.is_dir() or root.is_symlink():
        raise B02Error(f"B02 actor directory is missing or linked: {root}")
    result: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise B02Error(f"B02 actor contains a symlink: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path
    return result


def check(task_id: str, archive_path: Path = EVALUATOR,
          fixture_root: Path = FIXTURES) -> dict:
    """Recompute task hashes and verify that evaluator material is sealed."""
    if task_id not in IDS:
        raise B02Error(f"unknown B02 task: {task_id}")
    folder = fixture_root / task_id
    task_path, actor = folder / "task.json", folder / "actor"
    if task_path.is_symlink() or archive_path.is_symlink():
        raise B02Error("B02 task or evaluator is a symlink")
    task = json.loads(task_path.read_text(encoding="utf-8"))
    if (not isinstance(task, dict) or task.get("schema_version") != 1
            or task.get("id") != task_id
            or task.get("origin") != "pinned-upstream-regression"
            or task.get("source_url") != "https://github.com/mahmoud/boltons"
            or task.get("source_commit") != PARENT or task.get("fix_commit") != FIX
            or task.get("licence") != "BSD-3-Clause"
            or task.get("editable_paths") != [EDITABLE]
            or task.get("public_coverage") != IDS[task_id][0]
            or task.get("public_check_variant") != IDS[task_id][1]
            or task.get("task_sha256") != digest({
                key: value for key, value in task.items() if key != "task_sha256"})):
        raise B02Error("B02 task provenance or digest differs")
    files = actor_files(actor)
    if set(files) != ACTOR_FILES or set(task.get("actor_files", {})) != ACTOR_FILES:
        raise B02Error("B02 actor inventory differs")
    for name, path in files.items():
        if sha(path.read_bytes()) != task["actor_files"][name]:
            raise B02Error(f"B02 actor byte changed: {name}")
    if sha(files["LICENSE"].read_bytes()) != task["licence_sha256"]:
        raise B02Error("B02 licence differs")
    contract = json.loads(files["acceptance.json"].read_text(encoding="utf-8"))
    if contract != {"schema_version": 1,
                    "public_command": ["python3", "-B", "public_check.py"],
                    "editable_paths": [EDITABLE], "require_changed_output": True}:
        raise B02Error("B02 acceptance metadata differs")
    if sha(archive_path.read_bytes()) != task["evaluator_zip_sha256"]:
        raise B02Error("B02 evaluator seal differs")
    with zipfile.ZipFile(archive_path) as archive:
        items = archive.infolist()
        names = [item.filename for item in items]
        if (len(names) != len(set(names)) or set(names) != ZIP_FILES
                or any(item.is_dir() or item.file_size > 100_000
                       or stat.S_ISLNK(item.external_attr >> 16)
                       or item.filename.startswith("/")
                       or ".." in Path(item.filename).parts for item in items)):
            raise B02Error("B02 evaluator archive inventory is unsafe")
        if archive.read("LICENSE") != files["LICENSE"].read_bytes():
            raise B02Error("B02 evaluator licence differs")
        oracle = json.loads(archive.read("oracle.json"))
        if (oracle.get("schema_version") != 1
                or oracle.get("reference_commit") != FIX
                or oracle.get("partial_mechanism") != "EOF-guard-only"
                or oracle.get("case_weights") != WEIGHTS):
            raise B02Error("B02 oracle metadata differs")
    return {"task_id": task_id, "task_sha256": task["task_sha256"],
            "evaluator_zip_sha256": task["evaluator_zip_sha256"],
            "actor_file_count": len(files)}


def check_upstream(repo: Path, task_id: str) -> dict:
    """Optional exact Git-object verification, independent of fixture hashes."""
    check(task_id)
    actor = FIXTURES / task_id / "actor"

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", "-c", "safe.directory=*", "-C",
                                        str(repo), *args], timeout=30)

    if git("rev-parse", f"{FIX}^").decode().strip() != PARENT:
        raise B02Error("B02 upstream fix parent differs")
    for name in ("boltons/__init__.py", EDITABLE, "LICENSE"):
        if (actor / name).read_bytes() != git("show", f"{PARENT}:{name}"):
            raise B02Error(f"B02 actor differs from upstream: {name}")
    fixed = git("show", f"{FIX}:{EDITABLE}")
    anchor = b"rel_seek = 1.0 + rel_seek"
    if fixed.count(anchor) != 1:
        raise B02Error("B02 partial anchor differs")
    partial = fixed.replace(anchor, b"rel_seek = 1.0 - rel_seek", 1)
    with zipfile.ZipFile(EVALUATOR) as archive:
        if (archive.read(f"reference/{EDITABLE}") != fixed
                or archive.read(f"partial/{EDITABLE}") != partial):
            raise B02Error("B02 overlays differ from upstream-derived bytes")
    return {"source_commit": PARENT, "fix_commit": FIX,
            "upstream_verified": True}


def _process(root: Path, argument: str, *, code: bool) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONPATH": str(root), "PYTHONNOUSERSITE": "1"}
    command = [sys.executable, "-B", "-S"] + (["-c", argument] if code else [argument])
    return subprocess.run(command, cwd=root, env=env, text=True,
                          capture_output=True, timeout=30)


def calibrate(task_id: str) -> dict:
    """Run one public check and the same bounded hidden grader on three variants."""
    binding = check(task_id)
    temp_root = ROOT / "pilot-runs/q4u-calibration-temp"
    temp_root.mkdir(parents=True, exist_ok=True)
    if not temp_root.resolve().is_relative_to(ROOT.resolve()):
        raise B02Error("B02 temporary root escaped workspace")
    with zipfile.ZipFile(EVALUATOR) as archive:
        grader = archive.read("grader.py").decode("utf-8")
        with tempfile.TemporaryDirectory(prefix="b02-", dir=temp_root) as temporary:
            work = Path(temporary).resolve()
            if not work.is_relative_to(temp_root.resolve()):
                raise B02Error("B02 temporary workspace escaped root")
            grades = {}
            for variant in ("baseline", "partial", "reference"):
                actor = work / variant
                shutil.copytree(FIXTURES / task_id / "actor", actor)
                if variant != "baseline":
                    (actor / EDITABLE).write_bytes(archive.read(f"{variant}/{EDITABLE}"))
                before = {name: sha(path.read_bytes())
                          for name, path in actor_files(actor).items()}
                imported = _process(actor, "import boltons.jsonutils as m; print(m.__file__)",
                                    code=True)
                if (imported.returncode or Path(imported.stdout.strip()).resolve()
                        != (actor / EDITABLE).resolve()):
                    raise B02Error("B02 calibration imported a non-actor module")
                public = _process(actor, "public_check.py", code=False)
                if public.returncode and "AssertionError" not in public.stderr:
                    raise B02Error(f"B02 public check could not run: {public.stderr[-1000:]}")
                hidden = _process(actor, grader, code=True)
                if hidden.returncode:
                    raise B02Error(f"B02 hidden grader failed: {hidden.stderr[-1000:]}")
                outcome = json.loads(hidden.stdout)
                if (outcome.get("schema_version") != 1
                        or outcome.get("weights") != WEIGHTS
                        or set(outcome.get("cases", {})) != set(WEIGHTS)
                        or any(type(value) is not bool for value in outcome["cases"].values())
                        or outcome.get("score") != sum(
                            WEIGHTS[name] for name, passed in outcome["cases"].items() if passed)
                        or before != {name: sha(path.read_bytes())
                                      for name, path in actor_files(actor).items()}):
                    raise B02Error(f"B02 {variant} grade or source integrity differs")
                grades[variant] = {"public_pass": public.returncode == 0, **outcome}
    if ([grades[name]["score"] for name in ("baseline", "partial", "reference")]
            != [30, 65, 100]
            or [grades[name]["public_pass"] for name in
                ("baseline", "partial", "reference")]
                != ([True, True, True] if task_id == "B02W" else [False, False, True])):
        raise B02Error("B02 calibration separation differs")
    return {"schema_version": 1, **binding, "provider_calls": 0,
            "python_version": sys.version.split()[0], "grades": grades}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--calibrate", action="store_true")
    mode.add_argument("--upstream-repo", type=Path)
    parser.add_argument("--task", choices=sorted(IDS), required=True)
    args = parser.parse_args()
    try:
        result = (check(args.task) if args.check else
                  calibrate(args.task) if args.calibrate else
                  check_upstream(args.upstream_repo, args.task))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError,
            zipfile.BadZipFile) as error:
        print(f"BLOCKED: Q4U B02: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
