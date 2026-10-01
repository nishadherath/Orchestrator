#!/usr/bin/env python3
"""Root-owned, provider-free WSL qualification of the Q1 multi-file boundary."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

RUNTIME = Path("/opt/orchestrator-worker-runtime")
sys.path.insert(0, str(RUNTIME))
from worker_wsl_q1 import ACTORS, BASE, MANIFESTS, OUTPUTS, SEEDS, collect, stage  # noqa: E402

FILES = {
    "src/main.py": "def answer():\n    return 'Q1_ACTOR_VISIBLE_MAIN'\n",
    "src/helper.py": "def helper():\n    return 'Q1_ACTOR_VISIBLE_HELPER'\n",
    "tests/public_check.py": "assert True\n",
    "ISSUE.md": "Edit both modules without changing tests.\n",
    "acceptance.json": '{"schema_version":1}\n',
}
EDITABLE = {"src/main.py", "src/helper.py"}


def package() -> tuple[Path, Path]:
    source = Path(tempfile.mkdtemp(prefix="qualification-", dir=SEEDS))
    for relative, content in FILES.items():
        path = source / relative
        path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    spec = {"schema_version": 1, "files": [
        {"path": relative, "sha256": hashlib.sha256(content.encode()).hexdigest(),
         "editable": relative in EDITABLE}
        for relative, content in sorted(FILES.items())]}
    fd, raw_path = tempfile.mkstemp(prefix="qualification-spec-", suffix=".json", dir=SEEDS)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(spec, stream, sort_keys=True)
    return source, Path(raw_path)


def dispose(path: Path, parent: Path) -> None:
    if path.is_symlink() or path.resolve().parent != parent.resolve():
        raise RuntimeError("cleanup target escaped the Q1 root")
    if path.exists():
        shutil.rmtree(path)


def run_actor(actor: Path, *command: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(RUNTIME / "bin/worker-wsl-namespace-q1"),
                           str(actor), "--", *command], cwd="/",
                          capture_output=True, text=True, timeout=180)


def run() -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("Q1 probe needs WSL root")
    checks: dict[str, bool] = {}
    sources: list[Path] = []
    specs: list[Path] = []
    names: list[str] = []
    try:
        source, spec = package()
        sources.append(source)
        specs.append(spec)
        name = "q1-" + uuid.uuid4().hex
        names.append(name)
        actor = Path(stage(source, spec, name)["actor_root"])
        sibling_source, sibling_spec = package()
        sources.append(sibling_source)
        specs.append(sibling_spec)
        sibling = "q1-" + uuid.uuid4().hex
        names.append(sibling)
        stage(sibling_source, sibling_spec, sibling)
        try:
            collect(name, source)
        except (OSError, ValueError):
            checks["collection_before_stop_rejected"] = True
        else:
            checks["collection_before_stop_rejected"] = False
        process = run_actor(actor, "/usr/bin/python3",
                            str(RUNTIME / "worker_wsl_q1_actor_probe.py"), sibling)
        try:
            result = json.loads(process.stdout.strip().splitlines()[-1])
        except (IndexError, ValueError):
            result = {"result": "ERROR", "checks": {}}
        checks["namespace_stopped"] = process.returncode == 0
        checks.update(result.get("checks", {}))
        checks["actor_probe_passed"] = result.get("result") == "PASS"
        if not checks["namespace_stopped"]:
            raise RuntimeError("Q1 actor probe failed: " + (process.stderr + process.stdout)[-700:])
        receipt = collect(name, source)
        output = Path(receipt["output_root"])
        checks["two_allowed_edits_collected"] = receipt["changed_paths"] == sorted(EDITABLE)
        checks["collected_content_matches_actor"] = all(
            (output / relative).read_bytes() == (actor / relative).read_bytes()
            for relative in FILES)
        checks["source_unchanged"] = all((source / relative).read_text(encoding="utf-8") == content
                                         for relative, content in FILES.items())
        checks["protected_output_unchanged"] = all(
            (output / relative).read_text(encoding="utf-8") == FILES[relative]
            for relative in set(FILES) - EDITABLE)
        checks["receipt_bound_to_manifest"] = (
            receipt["spec_sha256"] == stage_record(name)["spec_sha256"]
            and receipt["writer_exit_status"] == 0)
        try:
            collect(name, source)
        except ValueError:
            checks["duplicate_collection_rejected"] = True
        else:
            checks["duplicate_collection_rejected"] = False

        # A stopped actor with a source race or protected-file drift cannot be collected.
        race_source, race_spec = package()
        sources.append(race_source)
        specs.append(race_spec)
        race_name = "q1-" + uuid.uuid4().hex
        names.append(race_name)
        race_actor = Path(stage(race_source, race_spec, race_name)["actor_root"])
        checks["race_actor_stopped"] = run_actor(race_actor, "/usr/bin/true").returncode == 0
        (race_source / "src/main.py").write_text("changed after staging\n", encoding="utf-8")
        try:
            collect(race_name, race_source)
        except ValueError:
            checks["concurrent_source_change_rejected"] = True
        else:
            checks["concurrent_source_change_rejected"] = False
        checks["race_no_output"] = not (OUTPUTS / race_name).exists()

        drift_source, drift_spec = package()
        sources.append(drift_source)
        specs.append(drift_spec)
        drift_name = "q1-" + uuid.uuid4().hex
        names.append(drift_name)
        drift_actor = Path(stage(drift_source, drift_spec, drift_name)["actor_root"])
        checks["drift_actor_stopped"] = run_actor(drift_actor, "/usr/bin/true").returncode == 0
        (drift_actor / "ISSUE.md").write_text("root tampered\n", encoding="utf-8")
        try:
            collect(drift_name, drift_source)
        except ValueError:
            checks["protected_actor_change_rejected"] = True
        else:
            checks["protected_actor_change_rejected"] = False
        checks["drift_no_output"] = not (OUTPUTS / drift_name).exists()

        invalid_source, invalid_spec = package()
        sources.append(invalid_source)
        specs.append(invalid_spec)
        original = json.loads(invalid_spec.read_text(encoding="utf-8"))
        for label, replacement in (("traversal", "../escape.py"),
                                   ("absolute", "/tmp/escape.py"),
                                   ("backslash", "src\\escape.py")):
            bad = json.loads(json.dumps(original))
            bad["files"][0]["path"] = replacement
            invalid_spec.write_text(json.dumps(bad), encoding="utf-8")
            rejected_name = "q1-" + uuid.uuid4().hex
            try:
                stage(invalid_source, invalid_spec, rejected_name)
            except ValueError:
                checks[f"{label}_path_rejected"] = True
            else:
                checks[f"{label}_path_rejected"] = False
                names.append(rejected_name)
        invalid_spec.write_text(json.dumps(original), encoding="utf-8")
        (invalid_source / "extra.py").write_text("EXTRA = True\n", encoding="utf-8")
        try:
            stage(invalid_source, invalid_spec, "q1-" + uuid.uuid4().hex)
        except ValueError:
            checks["undeclared_source_file_rejected"] = True
        else:
            checks["undeclared_source_file_rejected"] = False
        (invalid_source / "extra.py").unlink()
        (invalid_source / "src" / "escape.py").symlink_to(BASE / "evaluator" / "oracle.py")
        try:
            stage(invalid_source, invalid_spec, "q1-" + uuid.uuid4().hex)
        except ValueError:
            checks["source_symlink_rejected"] = True
        else:
            checks["source_symlink_rejected"] = False
        return {"result": "PASS" if checks and all(checks.values()) else "FAIL",
                "checks": checks, "check_count": len(checks),
                "provider_calls": 0, "provider_cost_usd": 0}
    finally:
        for name in names:
            dispose(ACTORS / name, ACTORS)
            dispose(OUTPUTS / name, OUTPUTS)
            for suffix in (".json", ".start.json", ".stop.json"):
                (MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)
        for source in sources:
            dispose(source, SEEDS)
        for spec in specs:
            spec.unlink(missing_ok=True)


def stage_record(name: str) -> dict:
    return json.loads((MANIFESTS / f"{name}.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:500]}))
        raise SystemExit(1)
