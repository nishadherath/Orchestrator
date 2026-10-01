#!/usr/bin/env python3
"""Run Q2 public and hidden cases from fresh Q1 actors without provider calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RUNTIME = Path("/opt/orchestrator-worker-runtime")
sys.path.insert(0, str(RUNTIME))
from worker_wsl_q1 import ACTORS, MANIFESTS, OUTPUTS, SEEDS, path_parts, stage  # noqa: E402


class UncertainActorError(RuntimeError):
    """The launcher timed out; preserve actor and source for reconciliation."""


def cap_output() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (64_000, 64_000))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def copy_package(source: Path, overlay: Path | None) -> tuple[Path, Path, dict]:
    if source.is_symlink() or not source.is_dir():
        raise ValueError("public fixture is not a real directory")
    package = Path(tempfile.mkdtemp(prefix="q2-public-", dir=SEEDS))
    manifest_path: Path | None = None
    try:
        for item in sorted(source.rglob("*")):
            relative = item.relative_to(source).as_posix()
            parts = path_parts(relative)
            if item.is_symlink():
                raise ValueError("public fixture contains a symlink")
            target = package.joinpath(*parts)
            if item.is_dir():
                target.mkdir(mode=0o755, parents=True, exist_ok=True)
            elif item.is_file():
                target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                target.write_bytes(item.read_bytes())
            else:
                raise ValueError("public fixture contains a special file")
        contract = json.loads((package / "acceptance.json").read_text(encoding="utf-8"))
        editable = contract.get("editable_paths")
        if (contract.get("schema_version") != 1 or not isinstance(editable, list)
                or not 2 <= len(editable) <= 8 or len(set(editable)) != len(editable)
                or contract.get("public_command") != ["python3", "-B", "public_check.py"]):
            raise ValueError("public fixture contract is invalid")
        if overlay is not None:
            if overlay.is_symlink() or not overlay.is_dir():
                raise ValueError("overlay root is invalid")
            overlay_files = [item for item in overlay.rglob("*") if item.is_file()]
            if {item.relative_to(overlay).as_posix() for item in overlay_files} != set(editable):
                raise ValueError("overlay must replace exactly the editable paths")
            for item in overlay_files:
                relative = item.relative_to(overlay).as_posix()
                if item.is_symlink():
                    raise ValueError("overlay contains a symlink")
                (package / relative).write_bytes(item.read_bytes())
        rows = []
        for item in sorted(package.rglob("*")):
            if item.is_file():
                relative = item.relative_to(package).as_posix()
                rows.append({"path": relative, "sha256": sha(item.read_bytes()),
                             "editable": relative in editable})
        if not set(editable) <= {row["path"] for row in rows}:
            raise ValueError("editable path is missing")
        manifest = {"schema_version": 1, "files": rows}
        fd, raw_path = tempfile.mkstemp(prefix="q2-spec-", suffix=".json", dir=SEEDS)
        manifest_path = Path(raw_path)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, sort_keys=True)
        return package, manifest_path, manifest
    except Exception:
        shutil.rmtree(package)
        if manifest_path is not None:
            manifest_path.unlink(missing_ok=True)
        raise


def dispose(path: Path, parent: Path) -> None:
    if path.is_symlink() or path.resolve().parent != parent.resolve():
        raise RuntimeError("Q2 cleanup path escaped its root")
    if path.exists():
        shutil.rmtree(path)


def run_isolated(package: Path, manifest_path: Path, manifest: dict,
                 command: list[str], input_text: str = "") -> subprocess.CompletedProcess:
    name = "q1-" + uuid.uuid4().hex
    actor = ACTORS / name
    staged = False
    stopped = False
    try:
        stage(package, manifest_path, name)
        staged = True
        with tempfile.TemporaryFile(mode="w+t") as stdout, tempfile.TemporaryFile(mode="w+t") as stderr:
            try:
                process = subprocess.run(
                    [str(RUNTIME / "bin/worker-wsl-namespace-q1"), str(actor), "--", *command],
                    input=input_text, stdout=stdout, stderr=stderr, text=True,
                    cwd="/", timeout=30, preexec_fn=cap_output)
            except subprocess.TimeoutExpired as exc:
                raise UncertainActorError(f"Q2 actor {name} timed out; preserve it for reconciliation") from exc
            stopped = True
            stdout.seek(0)
            stderr.seek(0)
            result = subprocess.CompletedProcess(process.args, process.returncode,
                                                 stdout.read(), stderr.read())
        for row in manifest["files"]:
            if sha((actor / row["path"]).read_bytes()) != row["sha256"]:
                raise ValueError(f"candidate changed its grading copy: {row['path']}")
        return result
    finally:
        if staged and stopped:
            dispose(actor, ACTORS)
            dispose(OUTPUTS / name, OUTPUTS)
            for suffix in (".json", ".start.json", ".stop.json"):
                (MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)


def verify(task_id: str, source: Path, overlay: Path | None,
           oracle_path: Path, root_state: str, variant: str) -> dict:
    if os.geteuid() != 0 or task_id not in {"P01", "P02"}:
        raise ValueError("WSL root and a known public task are required")
    if root_state not in {"accepted", "partial", "failed"}:
        raise ValueError("root state is invalid")
    if variant not in {"baseline", "reference", "partial"} or (variant == "baseline") != (overlay is None):
        raise ValueError("variant and overlay disagree")
    if oracle_path.is_symlink() or not oracle_path.is_file():
        raise ValueError("hidden oracle path is invalid")
    oracle_bytes = oracle_path.read_bytes()
    oracle = json.loads(oracle_bytes)
    if (oracle.get("schema_version") != 1 or not isinstance(oracle.get("cases"), list)
            or not oracle["cases"]):
        raise ValueError("hidden oracle schema is invalid")
    package, manifest_path, manifest = copy_package(source, overlay)
    preserve_source = False
    try:
        denial = run_isolated(package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "-c",
             "import sys; from pathlib import Path; "
             "p=Path(sys.argv[1]); "
             "\ntry: p.read_bytes()\nexcept OSError: print('DENIED')\n"
             "else: print('EXPOSED')", str(oracle_path)])
        if denial.returncode or denial.stdout.strip() != "DENIED":
            raise RuntimeError("hidden oracle is visible from the actor")
        public = run_isolated(package, manifest_path, manifest,
                              ["/usr/bin/python3", "-B", "public_check.py"])
        if public.returncode not in {0, 1}:
            raise RuntimeError("isolated public check did not terminate normally: " + public.stderr[-400:])
        earned = 0
        total = 0
        critical = False
        milestones = []
        cases = []
        for case in oracle["cases"]:
            if (not isinstance(case.get("weight"), int) or case["weight"] <= 0
                    or type(case.get("critical")) is not bool
                    or not isinstance(case.get("milestone"), str)):
                raise ValueError("hidden oracle case is invalid")
            result = run_isolated(package, manifest_path, manifest,
                ["/usr/bin/python3", "-B", str(RUNTIME / "worker_wsl_q2_case.py"), task_id],
                json.dumps(case["input"]))
            if result.returncode:
                raise RuntimeError("isolated hidden case failed: " + result.stderr[-400:])
            try:
                observed = json.loads(result.stdout.strip())
            except json.JSONDecodeError as exc:
                raise RuntimeError("hidden case returned no JSON") from exc
            passed = observed == case["expected"]
            total += case["weight"]
            if passed:
                earned += case["weight"]
                milestones.append(case["milestone"])
            elif case["critical"]:
                critical = True
            cases.append({"milestone": case["milestone"], "passed": passed,
                          "weight": case["weight"]})
        if sha(oracle_path.read_bytes()) != sha(oracle_bytes):
            raise ValueError("hidden oracle changed during grading")
        accepted = earned == total and public.returncode == 0
        return {"task_id": task_id, "variant": variant,
                "public_pass": public.returncode == 0,
                "hidden_acceptance": accepted, "quality": round(100 * earned / total, 2),
                "critical_error": critical,
                "false_success": root_state == "accepted" and not accepted,
                "milestones": milestones, "cases": cases,
                "oracle_sha256": sha(oracle_bytes),
                "oracle_direct_read_denied": True,
                "package_sha256": sha(json.dumps(manifest, sort_keys=True).encode()),
                "provider_calls": 0, "provider_cost_usd": 0}
    except UncertainActorError:
        preserve_source = True
        raise
    finally:
        if not preserve_source:
            dispose(package, SEEDS)
            manifest_path.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", choices=("P01", "P02"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--variant", choices=("baseline", "reference", "partial"),
                        default="baseline")
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--root-state", choices=("accepted", "partial", "failed"),
                        default="failed")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.task_id, args.source, args.overlay,
                                args.oracle, args.root_state, args.variant), sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:500]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
