"""Isolated, provider-free protected grading for X5 recovery development actors."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from controller_x5_recovery_protocol import PUBLIC_FILES


ROOT = Path(__file__).resolve().parents[1]
TASK_IDS = {"R01", "R02"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stage_source(source: Path, overlay: Path | None, seeds: Path,
                 task_id: str) -> Path:
    if source.is_symlink() or not source.is_dir():
        raise ValueError("actor source is not a real directory")
    contract = json.loads((source / "acceptance.json").read_text(encoding="utf-8"))
    editable = set(contract["editable_paths"])
    if overlay is not None:
        if overlay.is_symlink() or not overlay.is_dir():
            raise ValueError("overlay is not a real directory")
        entries = list(overlay.rglob("*"))
        if any(item.is_symlink() or not (item.is_file() or item.is_dir()) for item in entries):
            raise ValueError("overlay contains a symlink or special file")
        changes = [item for item in entries if item.is_file()]
        relative = {item.relative_to(overlay).as_posix() for item in changes}
        if not relative or not relative <= editable:
            raise ValueError("overlay must contain only editable regular files")
    staged = Path(tempfile.mkdtemp(prefix="x5-recovery-grade-", dir=seeds))
    try:
        for name in sorted(PUBLIC_FILES[task_id]):
            item = source / name
            if item.is_symlink() or not item.is_file():
                raise ValueError("actor public source contains a missing or redirected file")
            shutil.copy2(item, staged / name)
        if overlay is not None:
            for item in changes:
                target = staged / item.relative_to(overlay)
                target.write_bytes(item.read_bytes())
        return staged
    except Exception:
        shutil.rmtree(staged)
        raise


def grade(source: Path, oracle_path: Path, overlay: Path | None = None) -> dict:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("protected grading requires WSL root")
    if oracle_path.is_symlink() or not oracle_path.is_file():
        raise ValueError("protected oracle is not a regular file")
    oracle_bytes = oracle_path.read_bytes()
    oracle = json.loads(oracle_bytes)
    task_id = oracle.get("task_id")
    expected_oracle = ROOT / "test/oracles/controller_x5_recovery" / f"{task_id}.json"
    if task_id not in TASK_IDS or oracle_path.resolve() != expected_oracle.resolve():
        raise ValueError("oracle must identify a known development case")
    cases = oracle.get("cases")
    if (oracle.get("schema_version") != 1
            or not isinstance(cases, list) or not cases
            or sum(row.get("weight", 0) for row in cases) != 100
            or any(type(row.get("weight")) is not int or row["weight"] <= 0
                   or type(row.get("critical")) is not bool
                   or not isinstance(row.get("name"), str)
                   or not isinstance(row.get("operations"), list)
                   or not isinstance(row.get("expected"), dict) for row in cases)):
        raise ValueError("protected oracle contract is invalid")
    sys.path.insert(0, "/opt/orchestrator-worker-runtime")
    import worker_wsl_q2_verify as q2  # noqa: PLC0415

    staged = stage_source(source, overlay, q2.SEEDS, task_id)
    package = manifest_path = None
    uncertain = False
    try:
        package, manifest_path, manifest = q2.copy_package(staged, None)
        denial = q2.run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "-c",
             "from pathlib import Path;import sys;"
             "\ntry: Path(sys.argv[1]).read_bytes()"
             "\nexcept OSError: print('DENIED')"
             "\nelse: print('EXPOSED')", str(oracle_path)],
        )
        if denial.returncode or denial.stdout.strip() != "DENIED":
            raise RuntimeError("protected oracle is visible from actor")
        public = q2.run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "public_check.py"],
        )
        if public.returncode not in {0, 1}:
            raise RuntimeError("public check crashed outside an assertion")
        observations = []
        for case in cases:
            run = q2.run_isolated(
                package, manifest_path, manifest,
                ["/usr/bin/python3", "-B", "app.py"],
                json.dumps({"operations": case["operations"]}),
            )
            if run.returncode:
                raise RuntimeError("protected case did not return JSON: " + run.stderr[-400:])
            observed = json.loads(run.stdout)
            observations.append({"name": case["name"],
                                 "passed": observed == case["expected"],
                                 "weight": case["weight"],
                                 "critical": case["critical"]})
        if sha(oracle_path.read_bytes()) != sha(oracle_bytes):
            raise RuntimeError("protected oracle changed during grading")
        earned = sum(row["weight"] for row in observations if row["passed"])
        critical = any(row["critical"] and not row["passed"] for row in observations)
        return {"schema_version": 1, "task_id": task_id, "quality": earned,
                "accepted": earned == 100 and public.returncode == 0,
                "critical_violation": critical,
                "public_check_passed": public.returncode == 0,
                "oracle_read_denied": True, "oracle_sha256": sha(oracle_bytes),
                "package_sha256": sha(json.dumps(manifest, sort_keys=True).encode()),
                "observed_milestones": observations,
                "provider_calls": 0, "provider_cost_usd": 0}
    except q2.UncertainActorError:
        uncertain = True
        raise
    finally:
        if not uncertain:
            if package is not None:
                q2.dispose(package, q2.SEEDS)
            if manifest_path is not None:
                manifest_path.unlink(missing_ok=True)
            q2.dispose(staged, q2.SEEDS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, default=ROOT / "test/oracles/controller_x5_recovery/R01.json")
    parser.add_argument("--overlay", type=Path)
    args = parser.parse_args()
    print(json.dumps(grade(args.actor, args.oracle, args.overlay), sort_keys=True))


if __name__ == "__main__":
    main()
