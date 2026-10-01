#!/usr/bin/env python3
"""Frozen X5 public-assessment screen; run inside kali-linux as root.

Each task has a single-use N1 root. Re-running a settled task reads its
receipt; an interrupted assessment is never called again automatically.
No worker or Controller call is made by this screen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import controller_campaign_manifest
import controller_control
import controller_dispatch
import controller_evaluation
import controller_policy
import controller_profile_policy
import controller_wsl_interpreter
import controller_x3_corpus
import task_executor
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import Q3WslAdapter, isolated_public_runner


ROOT = Path(__file__).resolve().parents[1]
TASKS = ("C01-D1", "C03-D2", "C06-D1", "C07-D1", "N01-D1", "C08-D2")
ALLOWANCE_USD = 0.5
ROOT_BUDGET_USD = 8.0
CLAUDE = "/opt/orchestrator-worker-runtime/bin/claude"
RUNUSER = "/usr/sbin/runuser"


class ScreenError(RuntimeError):
    """The frozen X5 screen cannot safely advance."""


def _digest(value: object) -> str:
    return controller_evaluation.digest(value)


def _load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ScreenError(f"missing or redirected file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _rows() -> dict[str, dict]:
    inventory = controller_x3_corpus.inventory()
    if inventory["ready_tasks"] != 48 or inventory["pending_tasks"]:
        raise ScreenError("X3 corpus is not ready")
    rows = {row["task_id"]: row for row in inventory["tasks"]}
    if any(rows[task]["split"] != "development" for task in TASKS):
        raise ScreenError("X5 screen includes a reserved task")
    return {task: rows[task] for task in TASKS}


def freeze() -> dict:
    rows = _rows()
    body = {
        "schema_version": 1, "stage": "controller-x5-public-screen",
        "tasks": list(TASKS), "assessment_allowance_usd": ALLOWANCE_USD,
        "root_budget_usd": ROOT_BUDGET_USD,
        "packages": {task: rows[task]["package"] for task in TASKS},
        "runtime_package": controller_campaign_manifest.package_record(ROOT),
        "host": controller_campaign_manifest.host_record(),
        "credential_method": "claude-code-wsl-subscription",
        "maximum_provider_calls": len(TASKS),
    }
    body["manifest_sha256"] = _digest(body)
    return body


def validate(manifest: dict) -> None:
    if (not isinstance(manifest, dict)
            or manifest.get("manifest_sha256") != _digest({
                key: value for key, value in manifest.items()
                if key != "manifest_sha256"})
            or manifest.get("schema_version") != 1
            or manifest.get("stage") != "controller-x5-public-screen"
            or manifest.get("tasks") != list(TASKS)
            or manifest.get("assessment_allowance_usd") != ALLOWANCE_USD
            or manifest.get("root_budget_usd") != ROOT_BUDGET_USD
            or manifest.get("maximum_provider_calls") != len(TASKS)
            or manifest.get("credential_method") !=
            "claude-code-wsl-subscription"):
        raise ScreenError("screen manifest is invalid")
    controller_campaign_manifest.verify_package(
        ROOT, manifest["runtime_package"], require_materialised=False)
    if manifest["host"] != controller_campaign_manifest.host_record():
        raise ScreenError("screen host identity or relevant settings changed")
    if manifest["packages"] != {task: row["package"]
                                for task, row in _rows().items()}:
        raise ScreenError("screen actor or oracle inventory changed")


def _project(manifest: dict, task: str) -> Path:
    name = f"x5-screen-{manifest['manifest_sha256'][:12]}-{task.lower()}"
    return SEEDS / name


def _root_id(manifest: dict, task: str) -> str:
    return _digest({"manifest": manifest["manifest_sha256"],
                    "task": task, "arm": "A"})[:24]


def _contract(project: Path, package: dict) -> Path:
    editable = json.loads((project / "acceptance.json").read_text(
        encoding="utf-8"))["editable_paths"]
    protected = sorted(set(package["actor_files"]) - set(editable))
    value = {"version": 1, "kind": "command",
             "criteria": ["The isolated public check passes"],
             "constraints": ["Only declared actor files may change"],
             "required_outputs": editable, "protected_paths": protected,
             "command": ["python3", "-B", "public_check.py"],
             "timeout_s": 30}
    path = project / ".claude/x5-acceptance.json"
    path.parent.mkdir(mode=0o700, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _executor(project: Path, package: dict) -> task_executor.TaskExecutor:
    editable = json.loads((project / "acceptance.json").read_text(
        encoding="utf-8"))["editable_paths"]
    task = {"actor_files": package["actor_files"], "editable_paths": editable}
    return task_executor.TaskExecutor(
        project, Q3WslAdapter(task), command_runner=isolated_public_runner(task))


def prepare(manifest: dict) -> list[str]:
    """Materialise all six public actors and N1 roots without a provider call."""
    validate(manifest)
    CredentialStore().inspect()
    made = []
    for task in TASKS:
        project = _project(manifest, task)
        if project.exists() or project.is_symlink():
            raise ScreenError(f"single-use actor already exists: {task}")
        package = manifest["packages"][task]
        source = (ROOT / "test/fixtures/controller_x3/development" /
                  task / "actor")
        project.mkdir(mode=0o700)
        for relative, expected in package["actor_files"].items():
            data = (source / relative).read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ScreenError(f"public actor changed: {task}/{relative}")
            target = project / relative
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            target.write_bytes(data)
        contract = _contract(project, package)
        editable = json.loads((project / "acceptance.json").read_text(
            encoding="utf-8"))["editable_paths"]
        protected = sorted(set(package["actor_files"]) - set(editable))
        root = _root_id(manifest, task)
        executor = _executor(project, package)
        executor.admit(
            goal=(project / "issue.md").read_text(encoding="utf-8"),
            scope=editable, permissions=["read", "edit"],
            input_paths=protected, acceptance_path=contract,
            budget_usd=ROOT_BUDGET_USD,
            authority_id=_digest({"root": root, "authority": "x5-screen"})[:32],
            actor="x5-pilot-auto", root_id=root, task_id=task.lower(),
            experimental_dispatch={"schema_version": 3, "arm": "candidate",
                "manifest_sha256": manifest["manifest_sha256"],
                "cost_ceiling_usd": ROOT_BUDGET_USD,
                "repair_cells": ["worker-sonnet-low", "worker-opus-high"]})
        made.append(task)
    return made


def _local_runner(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Map the Windows WSL transport to the already selected WSL account."""
    prefix = ["wsl.exe", "-d", "kali-linux", "-u", "wsl", "--",
              "/usr/bin/env", "-C", "/tmp"]
    if command[:len(prefix)] != prefix or os.geteuid() != 0:
        raise ScreenError("public interpreter requested an unexpected host")
    kwargs.pop("env", None)
    return subprocess.run(
        [RUNUSER, "-u", "wsl", "--", "/usr/bin/env", "-i",
         "HOME=/home/wsl", "USER=wsl",
         "PATH=/usr/local/bin:/usr/bin:/bin:/opt/orchestrator-worker-runtime/bin",
         "/usr/bin/env", "-C", "/tmp", *command[len(prefix):]],
        env={"PATH": "/usr/bin:/bin", "HOME": "/root"}, **kwargs)


def _inputs(project: Path, editable: list[str]) -> dict:
    source = next(path for path in editable if path != "report.json")
    issue = (project / "issue.md").read_text(encoding="utf-8")
    check = (project / "public_check.py").read_text(encoding="utf-8")
    heading = next(line for line in issue.splitlines() if line.startswith("# "))
    assertion = next(line for line in check.splitlines()
                     if line.lstrip().startswith("assert ")
                     and check.splitlines().count(line) == 1)
    return {
        "issue": "issue.md",
        "source_paths": list(dict.fromkeys(
            ["issue.md", "app.py", "public_check.py", source])),
        "quote_requests": [{"source": "issue.md", "quote": heading},
                           {"source": "public_check.py", "quote": assertion}],
        "operational": {"context_tokens": 1000, "deadline_seconds": None,
                        "prior_local_repairs": 0, "required_artefacts": editable,
                        "deadline": None,
                        "authorised_task_budget_usd": ROOT_BUDGET_USD,
                        "observed_at": "2026-09-28T00:00:00Z"},
        "maximum_usd": ALLOWANCE_USD,
    }


def screen(manifest: dict, notice: dict, task: str) -> dict:
    validate(manifest)
    if (task not in TASKS or notice.get("manifest_sha256") !=
            manifest["manifest_sha256"] or notice.get("approved") is not True
            or notice.get("maximum_screen_usd") != len(TASKS) * ALLOWANCE_USD):
        raise ScreenError("dated spend notice does not authorise this screen")
    project = _project(manifest, task)
    if not project.is_dir() or project.is_symlink():
        raise ScreenError("prepared single-use actor is missing")
    package = manifest["packages"][task]
    editable = json.loads((project / "acceptance.json").read_text(
        encoding="utf-8"))["editable_paths"]
    executor = _executor(project, package)
    root = _root_id(manifest, task)
    record = executor.status(root)
    assessment = record.get("public_assessment")
    if assessment is None:
        interpreter = controller_wsl_interpreter.WslPublicInterpreter(
            distro="kali-linux", linux_user="wsl", claude_path=CLAUDE,
            launcher_path=str(ROOT / "tools/controller_wsl_launch.py"),
            allowance_usd=ALLOWANCE_USD, runner=_local_runner)
        result = executor.assess_public(root, interpreter=interpreter,
                                        **_inputs(project, editable))
    elif assessment["status"] == "settled":
        result = assessment["result"]
    else:
        raise ScreenError("assessment is unresolved; reconcile without replay")
    record = executor.status(root)
    if record["admission"]["policy"] == task_executor.PENDING_N3_POLICY:
        record = executor.freeze_public_selection(root)
    rigour = result["rigour"]
    profile = controller_profile_policy.choose(
        remaining_usd=rigour["authorised_task_budget_usd"],
        experimental_admission=True, requested_profile=None,
        explicit_experimental=False,
        follow_on_floor_usd=controller_dispatch.FOLLOW_ON_FLOOR_USD)
    control = controller_control.resolve(
        project, task_revision=rigour["task_revision"])
    decision = controller_policy.decide(
        rigour, control, selected_cell=record["ladder"][0],
        controller_profile=profile["profile"])
    return {"task_id": task, "root_id": root, "project": str(project),
            "assessment_invocation_id": record["public_assessment"]["invocation_id"],
            "assessment_cost_usd": record["budget"]["spent_usd"],
            "assessment_status": record["public_assessment"]["status"],
            "effective_action": decision["effective_action"],
            "recommended_action": decision["recommended_action"],
            "reason_codes": decision["reason_codes"],
            "selected_cell": decision["selected_cell"],
            "profile": decision["controller_profile"],
            "decision_id": decision["decision_id"],
            "budget_unresolved": record["budget"]["unresolved"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "prepare", "screen"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--notice", type=Path)
    parser.add_argument("--task", choices=TASKS)
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() != 0:
        raise ScreenError("X5 screen requires the attested WSL root host")
    if args.mode == "freeze":
        if args.manifest.exists():
            raise ScreenError("manifest path already exists")
        value = freeze()
        args.manifest.write_text(json.dumps(value, indent=2, sort_keys=True)
                                 + "\n", encoding="utf-8")
        print(json.dumps({"manifest_sha256": value["manifest_sha256"],
                          "tasks": list(TASKS)}))
        return 0
    manifest = _load(args.manifest)
    if args.mode == "prepare":
        print(json.dumps({"prepared": prepare(manifest)}))
        return 0
    if args.task is None or args.notice is None:
        raise ScreenError("screen needs --task and --notice")
    print(json.dumps(screen(manifest, _load(args.notice), args.task),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
