#!/usr/bin/env python3
"""Prospective X5 v4 public-assessment screen; run inside kali-linux as root.

Each task has a single-use N1 root. Re-running a settled task reads its
receipt; an interrupted assessment is never called again automatically.
No worker or Controller call is made by this screen.
"""
from __future__ import annotations

import argparse
import copy
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
import controller_x5_worker_adapter
import task_executor
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import isolated_public_runner


ROOT = Path(__file__).resolve().parents[1]
TASKS = ("X5-PAY", "X5-FEAT", "X5-LEASE", "X5-MONEY", "N01-D1", "C08-D2")
CASE_DIRS = {"X5-PAY": "payment_replay", "X5-FEAT": "tenant_feature",
             "X5-LEASE": "lease_lag", "X5-MONEY": "monetary_discrepancy"}
ALLOWANCE_USD = 0.5
ROOT_BUDGET_USD = 8.0
CLAUDE = "/opt/orchestrator-worker-runtime/bin/claude"
RUNUSER = "/usr/sbin/runuser"
EXPECTED_ACTIONS = {**{case: "controller" for case in CASE_DIRS},
                    "N01-D1": "worker", "C08-D2": "clarify"}


class ScreenError(RuntimeError):
    """The frozen X5 screen cannot safely advance."""


def gate_results(task: str, previous: list[dict]) -> None:
    """Enforce the prospective order before a new assessment may start."""
    if task not in TASKS or len(previous) != TASKS.index(task):
        raise ScreenError("screen assessment order is invalid")
    for expected_task, result in zip(TASKS, previous):
        if (result.get("task_id") != expected_task
                or result.get("assessment_status") != "settled"
                or result.get("effective_action") != EXPECTED_ACTIONS[expected_task]
                or result.get("budget_unresolved")):
            raise ScreenError(
                f"prospective gate stopped after {expected_task}; "
                f"refusing assessment for {task}")


def _digest(value: object) -> str:
    return controller_evaluation.digest(value)


def _load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ScreenError(f"missing or redirected file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _rows() -> dict[str, dict]:
    inventory = controller_x3_corpus.inventory()
    if inventory["ready_tasks"] != 48 or inventory["pending_tasks"]:
        raise ScreenError("X3 control corpus is not ready")
    rows = {row["task_id"]: row for row in inventory["tasks"]}
    controls = ("N01-D1", "C08-D2")
    if any(rows[task]["split"] != "development" for task in controls):
        raise ScreenError("X5 screen includes a reserved control")
    return {task: rows[task] for task in controls}


def _packages(rows: dict[str, dict]) -> dict[str, dict]:
    """Bind four X5-only public actors and two unchanged X3 controls."""
    packages = {task: copy.deepcopy(row["package"]) for task, row in rows.items()}
    for task, directory in CASE_DIRS.items():
        actor = ROOT / "test/fixtures/controller_x5_v4" / directory / "actor"
        oracle = ROOT / "test/oracles/controller_x5_v4" / directory
        files = {}
        for path in actor.iterdir():
            if path.is_symlink() or not path.is_file():
                raise ScreenError(f"X5 public actor has redirected entry: {task}")
            files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if set(files) != {"app.py", "issue.md", "trace.json", "public_check.py",
                          "acceptance.json", "report.json",
                          {"X5-PAY": "payments.py", "X5-FEAT": "features.py",
                           "X5-LEASE": "leases.py", "X5-MONEY": "amounts.py"}[task]}:
            raise ScreenError(f"X5 actor file boundary changed: {task}")
        protected = {}
        for path in oracle.iterdir():
            if path.is_symlink() or not path.is_file():
                raise ScreenError(f"X5 protected package has redirected entry: {task}")
            protected[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        packages[task] = {"actor_files": files, "protected_files": protected}
    return packages


def freeze() -> dict:
    rows = _rows()
    body = {
        "schema_version": 4, "stage": "controller-x5-public-screen-v4",
        "tasks": list(TASKS), "assessment_allowance_usd": ALLOWANCE_USD,
        "root_budget_usd": ROOT_BUDGET_USD,
        "packages": _packages(rows),
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
            or manifest.get("schema_version") != 4
            or manifest.get("stage") != "controller-x5-public-screen-v4"
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
    if manifest["packages"] != _packages(_rows()):
        raise ScreenError("screen actor or oracle inventory changed")


def _project(manifest: dict, task: str) -> Path:
    name = f"x5-v4-screen-{manifest['manifest_sha256'][:12]}-{task.lower()}"
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
        project, controller_x5_worker_adapter.X5WslAdapter(task),
        command_runner=isolated_public_runner(task))


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
        source = ((ROOT / "test/fixtures/controller_x5_v4" /
                   CASE_DIRS[task] / "actor") if task in CASE_DIRS else
                  (ROOT / "test/fixtures/controller_x3/development" /
                   task / "actor"))
        project.mkdir(mode=0o700)
        for relative, expected in package["actor_files"].items():
            origin = source / relative
            data = origin.read_bytes()
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
    sources = list(dict.fromkeys(
        ["issue.md", "app.py", "public_check.py", source]))
    quotes = [{"source": "issue.md", "quote": heading},
              {"source": "public_check.py", "quote": assertion}]
    trace = project / "trace.json"
    if trace.is_file():
        lines = trace.read_text(encoding="utf-8").splitlines()
        quote = next(line for line in lines if line.strip()
                     and line.strip() not in {"{", "}", "[", "]"}
                     and lines.count(line) == 1)
        sources.append("trace.json")
        quotes.append({"source": "trace.json", "quote": quote})
    return {
        "issue": "issue.md",
        "source_paths": sources, "quote_requests": quotes,
        "operational": {"context_tokens": 1000, "deadline_seconds": None,
                        "prior_local_repairs": 0, "required_artefacts": editable,
                        "deadline": None,
                        "authorised_task_budget_usd": ROOT_BUDGET_USD,
                        "observed_at": "2026-09-29T00:00:00Z"},
        "maximum_usd": ALLOWANCE_USD,
    }


def screen(manifest: dict, notice: dict, task: str,
           *, _replay: bool = False) -> dict:
    validate(manifest)
    if (task not in TASKS or notice.get("manifest_sha256") !=
            manifest["manifest_sha256"] or notice.get("approved") is not True
            or notice.get("maximum_screen_usd") != len(TASKS) * ALLOWANCE_USD):
        raise ScreenError("dated spend notice does not authorise this screen")
    if not _replay:
        prior = [screen(manifest, notice, previous, _replay=True)
                 for previous in TASKS[:TASKS.index(task)]]
        gate_results(task, prior)
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
    if _replay and (assessment is None or assessment.get("status") != "settled"):
        raise ScreenError(f"prior assessment is not settled: {task}")
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
        try:
            record = executor.freeze_public_selection(root)
        except task_executor.ExecutorError as exc:
            record = executor.status(root)
            return {"task_id": task, "root_id": root, "project": str(project),
                    "assessment_invocation_id": assessment["invocation_id"]
                    if assessment else record["public_assessment"]["invocation_id"],
                    "assessment_cost_usd": record["budget"]["spent_usd"],
                    "assessment_status": record["public_assessment"]["status"],
                    "screen_stop": str(exc),
                    "budget_unresolved": record["budget"]["unresolved"]}
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
