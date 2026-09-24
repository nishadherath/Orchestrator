#!/usr/bin/env python3
"""Exercise N4 materialize/namespace/collect without provider credentials."""
from __future__ import annotations

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
from worker_wsl_collect import collect  # noqa: E402
from worker_wsl_materialize import ACTORS, BASE, MANIFESTS, stage  # noqa: E402

SEEDS = BASE / "seed"


def seed() -> Path:
    source = Path(tempfile.mkdtemp(prefix="transport-", dir=SEEDS))
    (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    (source / "public_check.py").write_text("assert True\n", encoding="utf-8")
    (source / "ISSUE.md").write_text("Set VALUE to 2.\n", encoding="utf-8")
    (source / "acceptance.json").write_text('{"schema_version":1}\n', encoding="utf-8")
    return source


def safe_remove(path: Path, parent: Path) -> None:
    if path.is_symlink() or not path.resolve().is_relative_to(parent.resolve()):
        raise RuntimeError("probe cleanup escaped its root")
    shutil.rmtree(path)


def run() -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("transport probe needs WSL root")
    source = seed()
    name = "inv-" + uuid.uuid4().hex
    actor = Path(stage(source, name)["actor_root"])
    command = [str(RUNTIME / "bin/worker-wsl-namespace"), str(actor), "--",
               "/usr/bin/python3", "-c",
               "from pathlib import Path; "
               "Path('app.py').write_text('VALUE = 2\\n'); "
               "print('ACTOR_EDIT_OK')"]
    try:
        process = subprocess.run(command, cwd="/", capture_output=True, text=True,
                                 timeout=30)
        checks = {
            "namespace_process_stopped": process.returncode == 0,
            "actor_edit_observed": "ACTOR_EDIT_OK" in process.stdout,
        }
        if all(checks.values()):
            receipt = collect(name, source)
            checks.update({
                "allowed_edit_collected": receipt["changed"]
                and (source / "app.py").read_text(encoding="utf-8") == "VALUE = 2\n",
                "protected_source_untouched": (source / "acceptance.json").read_text(
                    encoding="utf-8") == '{"schema_version":1}\n',
            })
        else:
            checks.update(allowed_edit_collected=False, protected_source_untouched=False)
    except subprocess.TimeoutExpired:
        # A timed-out writer is uncertain; do not inspect or copy its output.
        return {"checks": {"namespace_process_stopped": False,
                            "timeout_never_collected": True}, "result": "FAIL"}
    finally:
        if "process" in locals() and process.returncode is not None:
            safe_remove(actor, ACTORS)
            (MANIFESTS / f"{name}.json").unlink()
            safe_remove(source, SEEDS)

    source = seed()
    name = "inv-" + uuid.uuid4().hex
    actor = Path(stage(source, name)["actor_root"])
    try:
        (actor / "acceptance.json").write_text("corrupted\n", encoding="utf-8")
        try:
            collect(name, source)
        except ValueError:
            checks["protected_actor_change_rejected"] = True
        else:
            checks["protected_actor_change_rejected"] = False
        checks["rejected_collection_did_not_write"] = (
            (source / "app.py").read_text(encoding="utf-8") == "VALUE = 1\n")
    finally:
        safe_remove(actor, ACTORS)
        (MANIFESTS / f"{name}.json").unlink()
        safe_remove(source, SEEDS)

    source = seed()
    name = "inv-" + uuid.uuid4().hex
    actor = Path(stage(source, name)["actor_root"])
    try:
        (source / "app.py").write_text("VALUE = 99\n", encoding="utf-8")
        try:
            collect(name, source)
        except ValueError:
            checks["concurrent_source_change_rejected"] = True
        else:
            checks["concurrent_source_change_rejected"] = False
        checks["source_change_preserved"] = (source / "app.py").read_text(
            encoding="utf-8") == "VALUE = 99\n"
    finally:
        safe_remove(actor, ACTORS)
        (MANIFESTS / f"{name}.json").unlink()
        safe_remove(source, SEEDS)
    return {"checks": checks, "result": "PASS" if all(checks.values()) else "FAIL"}


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:200]}))
        raise SystemExit(1)
