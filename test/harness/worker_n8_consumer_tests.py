#!/usr/bin/env python3
"""Install N8 into clean and upgraded consumers, exercise it, then roll back."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import build_dist  # noqa: E402
from worker_executor_consumer_tests import SCRIPT  # noqa: E402

CLI_SCRIPT = r'''
import contextlib
import io
from worker_tasks import main as worker_main
def command(action, request=None, root=None):
    argv = [action, "--project", str(project), "--json"]
    if request is not None:
        path = project / "operation.json"
        path.write_text(json.dumps(request), encoding="utf-8")
        argv.extend(["--request", str(path)])
    if root is not None:
        argv.extend(["--root", root])
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = worker_main(argv, adapter=fake)
    return code, json.loads(out.getvalue())
code, admitted = command("admit", {"goal": "Complete CLI task", "scope": ["output.txt"],
    "acceptance_path": "acceptance.json", "budget_usd": 1.0, "authority_id": "cli_authority",
    "actor": "operator", "root_id": "cli-root"})
assert code == 0 and admitted["state"] == "ready"
code, selected = command("shadow", {"facts": assessment["facts"], "override": {
    "cell": "worker-opus-high", "actor": "operator", "authority_id": "cli_override",
    "reason": "inspect explicit cell", "max_cost_usd": 1.0}}, "cli-root")
assert code == 0 and selected["decision"]["selected_cell"] == "worker-opus-high", selected
assert selected["b0_cell"] == "worker-sonnet-low"
assert command("audit")[0] == 2
assert command("cancel", {"actor": "operator", "reason": "replace task revision"}, "cli-root")[1]["state"] == "cancelled"
assert command("continue", {"actor": "operator", "reason": "continue under same balance",
    "authority_id": "cli_continuation"}, "cli-root")[1]["revision"]["revision_number"] == 2
code, completed = command("run", root="cli-root")
assert code == 0 and completed["state"] == "accepted"
assert completed["attempts"][0]["requested_cell"] == "worker-sonnet-low"
assert completed["budget"]["spent_usd"] == 0.02
assert command("audit")[0] == 0
sys.path.insert(0, str(project))
import preflight
diagnostics = preflight.operational_diagnostics(project)
assert diagnostics["worker_tasks"]["rollback_safe"] is True
assert len(diagnostics["worker_tasks"]["roots"]) == 3
assert subprocess.run([sys.executable, str(project / "tools/worker_tasks.py"),
    "status", "--project", str(project), "--root", "cli-root", "--json"],
    capture_output=True).returncode == 0
print("PASS: installed CLI admission, explicit shadow cell, cancellation, continuation and B0")
'''


def invoke(script: Path, *args: str) -> dict:
    proc = subprocess.run([sys.executable, str(script), *args, "--json"],
                          capture_output=True, text=True, timeout=90)
    if proc.returncode:
        raise AssertionError((proc.returncode, proc.stdout, proc.stderr))
    return json.loads(proc.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--current-baseline", action="store_true",
                      help="use the current dist byte-for-byte for the pre-build upgrade proof")
    mode.add_argument("--built-bundle", action="store_true",
                      help="exercise the generated dist instead of a source-planned candidate")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="worker-n8-consumer-") as folder:
        base = Path(folder)
        candidate = base / "candidate"
        if args.built_bundle:
            shutil.copytree(ROOT / "dist", candidate)
        else:
            for path, content in build_dist.planned_files("n8-test-candidate", candidate).items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8", newline="\n")
        baseline = base / "baseline"
        shutil.copytree(ROOT / "dist" if args.current_baseline else candidate, baseline)
        if not args.current_baseline:
            # A deterministic prior-layout fixture makes the post-build harness
            # independent of whether dist has already received the new CLI.
            manifest_path = baseline / "bundle-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for name in ("tools/worker_tasks.py", "WORKER-TASKS.md", ".claude/commands/worker-task.md"):
                (baseline / name).unlink()
                manifest["files"].pop(name)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        project = base / "consumer"
        project.mkdir()
        (project / "user.txt").write_text("preserve me", encoding="utf-8")
        invoke(baseline / "install.py", "apply", "--bundle", str(baseline), "--target", str(project))
        upgraded = invoke(candidate / "install.py", "apply", "--bundle", str(candidate), "--target", str(project))
        backup = Path(upgraded["backup_location"]).name
        proc = subprocess.run([sys.executable, "-I", "-c", SCRIPT + CLI_SCRIPT,
                               str(project), str(project)], cwd=base,
                              capture_output=True, text=True, timeout=120)
        if proc.returncode:
            raise AssertionError((proc.stdout, proc.stderr))
        task_record = project / ".claude/task-executor-v2/cli-root/root.json"
        retained = task_record.read_bytes()
        invoke(candidate / "install.py", "rollback", "--target", str(project), "--backup", backup)
        assert task_record.read_bytes() == retained
        assert (project / "user.txt").read_text(encoding="utf-8") == "preserve me"
        baseline_manifest = json.loads((baseline / "bundle-manifest.json").read_text(encoding="utf-8"))
        for name in baseline_manifest["files"]:
            assert (project / name).read_bytes() == (baseline / name).read_bytes(), name
        assert (project / "tools/worker_tasks.py").exists() == (baseline / "tools/worker_tasks.py").exists()
        assert subprocess.run([sys.executable, str(project / "tools/task_executor.py"),
                               "--audit", "--project", str(project)], capture_output=True).returncode == 0
        clean = base / "clean"
        clean.mkdir()
        invoke(candidate / "install.py", "apply", "--bundle", str(candidate), "--target", str(clean))
        proc = subprocess.run([sys.executable, "-I", "-c", SCRIPT + CLI_SCRIPT,
                               str(clean), str(clean)], cwd=base,
                              capture_output=True, text=True, timeout=120)
        if proc.returncode:
            raise AssertionError((proc.stdout, proc.stderr))
        print("PASS: clean install, upgrade, installed B0/N2/N3/CLI, rollback and retained task records")
        print("baseline=" + ("current-dist" if args.current_baseline else "synthetic-prior-layout"))
        print("candidate=" + ("built-dist" if args.built_bundle else "source-planned"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
