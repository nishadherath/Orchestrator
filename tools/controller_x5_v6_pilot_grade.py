#!/usr/bin/env python3
"""Grade X5 v6 pilot actors in the isolated WSL oracle boundary."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x3_grade as x3  # noqa: E402
import controller_x5_v6_grade as x5  # noqa: E402

CONTROLS = {"N01-D1", "C08-D2"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grade_control(task: str, actor_root: Path, package_record: dict) -> dict:
    if os.name != "posix" or os.geteuid() != 0 or task not in CONTROLS:
        raise RuntimeError("X5 control grading requires WSL root and a known task")
    sys.path.insert(0, "/opt/orchestrator-worker-runtime")
    import worker_wsl_q2_verify as q2  # noqa: PLC0415

    oracle_path = ROOT / "test/oracles/controller_x3" / f"{task}.json"
    oracle_before = sha(oracle_path)
    if oracle_before != package_record["oracle_sha256"]:
        raise RuntimeError(f"{task}: protected X3 oracle drift")
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    actor_files = package_record["actor_files"]
    editable = json.loads((actor_root / "acceptance.json").read_text(
        encoding="utf-8"))["editable_paths"]
    source = Path(tempfile.mkdtemp(prefix="x5-v6-control-grade-", dir=q2.SEEDS))
    package = manifest_path = None
    uncertain = False
    try:
        protected_edit = False
        for relative, expected in actor_files.items():
            origin = actor_root / relative
            if origin.is_symlink() or not origin.is_file():
                raise RuntimeError(f"{task}: actor file missing or redirected: {relative}")
            if relative not in editable and sha(origin) != expected:
                protected_edit = True
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origin, target)
        package, manifest_path, q2_manifest = q2.copy_package(source, None)
        denial = q2.run_isolated(package, manifest_path, q2_manifest,
            ["/usr/bin/python3", "-B", "-c",
             "from pathlib import Path;import sys;"
             "\ntry: Path(sys.argv[1]).read_bytes()"
             "\nexcept OSError: print('DENIED')"
             "\nelse: print('EXPOSED')", str(oracle_path)])
        if denial.returncode or denial.stdout.strip() != "DENIED":
            raise RuntimeError(f"{task}: oracle visible from actor")
        public = q2.run_isolated(package, manifest_path, q2_manifest,
                                 ["/usr/bin/python3", "-B", "public_check.py"])
        if public.returncode not in {0, 1}:
            raise RuntimeError(f"{task}: public check crashed")
        cases = []
        for row in oracle["cases"]:
            actual = x3._invoke(q2, package, manifest_path, q2_manifest,
                                x3._case_input(task, row["input"]))
            cases.append({"milestone": row["milestone"],
                          "passed": actual == row["expected"],
                          "weight": row["weight"]})
        try:
            raw = package / "report.json"
            report = (x3._report(json.loads(raw.read_text(encoding="utf-8")), task)
                      if raw.stat().st_size <= 64_000 else None)
        except (OSError, json.JSONDecodeError, ValueError):
            report = None
        probes = []
        for row in report["probes"] if report else []:
            actual = x3._invoke(q2, package, manifest_path, q2_manifest,
                                row["input"])
            probes.append({"input": row["input"], "observed": actual,
                           "verified": actual == row["observed"]})
        if sha(oracle_path) != oracle_before:
            raise RuntimeError(f"{task}: oracle changed during grading")
        score = x3.score(oracle, cases, report, probes,
                         public.returncode == 0, protected_edit)
        return {"schema_version": 1, "task_id": task,
                "oracle_sha256": oracle_before, "oracle_read_denied": True,
                "public_check_passed": public.returncode == 0,
                "provider_calls": 0, **score}
    except q2.UncertainActorError:
        uncertain = True
        raise
    finally:
        if not uncertain:
            if package is not None:
                q2.dispose(package, q2.SEEDS)
            if manifest_path is not None:
                manifest_path.unlink(missing_ok=True)
            q2.dispose(source, q2.SEEDS)


def grade(task: str, actor_root: Path, manifest: dict) -> dict:
    if task in x5.CASES:
        return x5.grade(task, actor_root, manifest)
    if task in CONTROLS:
        return grade_control(task, actor_root, manifest["packages"][task])
    raise RuntimeError(f"unknown X5 v6 pilot task: {task}")
