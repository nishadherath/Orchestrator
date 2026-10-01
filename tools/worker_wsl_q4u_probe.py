#!/usr/bin/env python3
"""Zero-provider Q4U probe for one-file edits, no edits and decision stubs."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


def run(repo: Path) -> dict:
    if sys.platform != "linux":
        raise RuntimeError("Q4U boundary probe runs inside WSL")
    sys.path.insert(0, str(repo / "tools"))
    import model_registry
    from worker_adapter import WorkerRequest, digest
    from worker_q4u_grade import grade
    from worker_wsl_q1 import SEEDS, load_spec as q1_load_spec
    from worker_wsl_q4u import load_spec as q4u_load_spec
    from worker_wsl_q4u_adapter import (LAUNCHER, Q4UWslAdapter,
                                        isolated_public_runner)
    sonnet_model = model_registry.resolve_cell("worker-sonnet-low")["cli_model"]

    results = {}
    for task_id in ("B02W", "C03", "M05"):
        folder = repo / "test/fixtures/worker_q4u_public" / task_id
        task = json.loads((folder / "task.json").read_text(encoding="utf-8"))
        source = folder / "actor"
        with tempfile.TemporaryDirectory(prefix="q4u-probe-", dir=SEEDS) as raw:
            workspace = Path(raw)
            for relative in task["actor_files"]:
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((source / relative).read_bytes())
            protected = {relative: (workspace / relative).read_bytes()
                         for relative in task["actor_files"]
                         if relative not in task["editable_paths"]}

            class FakeAdapter(Q4UWslAdapter):
                def _invoke(self, command: list[str], actor: Path,
                            request: WorkerRequest) -> subprocess.CompletedProcess:
                    action = ("from pathlib import Path\n"
                              "p=Path('boltons/jsonutils.py')\n"
                              "p.write_bytes(p.read_bytes()+b'\\n# q4u probe\\n')\n"
                              if task_id == "B02W" else
                              "from pathlib import Path\n"
                              "Path('decision.json').write_text('''{\"status\":\"needs_input\",\"missing_fields\":[\"jurisdiction\"],\"rationale\":\"Need jurisdiction.\"}''')\n"
                              if task_id == "M05" else "")
                    code = action + '''import json
report={"status":"completed","diagnosis":"provider-free boundary probe",
"evidence":["single-editable"],
"checks":[{"command":"python3 -B public_check.py","outcome":"not_run"}],
"remaining":[],"clarification":None}
print(json.dumps({"type":"assistant","message":{"model":"MODEL_ID","content":[]}}))
print(json.dumps({"type":"result","subtype":"success","result":"Complete.",
"structured_output":report,"total_cost_usd":0.0,
"usage":{"input_tokens":0,"output_tokens":0},
"modelUsage":{"MODEL_ID":{"costUSD":0.0}}}))
'''.replace("MODEL_ID", sonnet_model)
                    argv = [str(LAUNCHER), str(actor), "--", "/usr/bin/python3",
                            "-B", "-c", code]
                    return subprocess.run(argv, cwd="/", capture_output=True,
                                          timeout=45)

            request = WorkerRequest(
                workspace, "Provider-free Q4U actor boundary probe",
                tuple(task["editable_paths"]), "worker-sonnet-low", 4.0,
                "Q4U probe", timeout_s=90, admission_token=uuid.uuid4().hex,
                invocation_id=uuid.uuid4().hex, revision_id=uuid.uuid4().hex,
                decision_digest=uuid.uuid4().hex, intent_digest=uuid.uuid4().hex)
            adapter = FakeAdapter(task)
            capability = adapter.capability(workspace)
            receipt = adapter.run(request)
            public_result = isolated_public_runner(task)(
                ["python3", "-B", "public_check.py"], cwd=workspace,
                capture_output=True, timeout=30, shell=False)
            hidden_result = grade(task_id, workspace)
            boundary = receipt["command_contract"].get("q4u_boundary", {})
            expected_changed = [] if task_id == "C03" else task["editable_paths"]
            results[task_id] = {
                "capability": capability["enforcement_proven"],
                "completed": receipt["status"] == "completed",
                "structured": receipt["evaluation_report"]["observability"] == "present",
                "changed": boundary.get("changed_paths") == expected_changed,
                "protected": all((workspace / relative).read_bytes() == data
                                 for relative, data in protected.items()),
                "revision_bound": (receipt["evaluation_report"]["binding"].get(
                    "final_revision_sha256") == digest(boundary.get("after_sha256"))),
                "zero_provider_cost": receipt["cost_usd"] == 0,
                "isolated_public_pass": public_result.returncode == 0,
                "public_proof": public_result.isolation_evidence["sha256"] == digest({
                    key: value for key, value in public_result.isolation_evidence.items()
                    if key != "sha256"}),
                "hidden_score": hidden_result["score"] == {
                    "B02W": 30, "C03": 100, "M05": 100}[task_id],
            }
            if task_id == "M05":
                results[task_id]["decision_written"] = json.loads(
                    (workspace / "decision.json").read_text(encoding="utf-8"))[
                        "missing_fields"] == ["jurisdiction"]
                # Exercise the actual experimental root/acceptance path, not
                # just the transport. This second workspace is provider-free.
                from worker_q4u_contract import build as command_contract
                from worker_q4u_executor import Q4UTaskExecutor
                with tempfile.TemporaryDirectory(prefix="q4u-executor-", dir=SEEDS) as raw2:
                    project = Path(raw2)
                    for relative in task["actor_files"]:
                        target = project / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes((source / relative).read_bytes())
                    contract_path = project / ".claude/acceptance.json"
                    contract_path.parent.mkdir()
                    contract_path.write_text(json.dumps(command_contract(task_id)),
                                             encoding="utf-8")
                    public = json.loads((folder / "public_assessment.json").read_text(
                        encoding="utf-8"))
                    executor = Q4UTaskExecutor(
                        project, FakeAdapter(task),
                        command_runner=isolated_public_runner(task))
                    root_id = "q4u-probe-" + uuid.uuid4().hex
                    executor.admit(
                        goal="Complete the decision", scope=["decision.json"],
                        permissions=["read", "edit"], acceptance_path=contract_path,
                        budget_usd=4.0, authority_id=uuid.uuid4().hex,
                        actor="provider-free-probe", root_id=root_id,
                        input_paths=sorted(set(task["actor_files"]) -
                                           set(task["editable_paths"])),
                        experimental_dispatch={
                            "schema_version": 3, "arm": "coverage_repair",
                            "manifest_sha256": "0" * 64,
                            "public_assessment": public,
                            "cost_ceiling_usd": 4.0})
                    outcome = executor.run(root_id)
                    results[task_id]["executor_accepted"] = (
                        outcome["state"] == "accepted" and
                        len(outcome["attempts"]) == 1 and
                        grade(task_id, project)["score"] == 100)

    # The historical Q1 loader must remain two-editable-only.
    with tempfile.TemporaryDirectory(prefix="q4u-manifest-", dir=SEEDS) as raw:
        manifest = Path(raw) / "spec.json"
        manifest.write_text(json.dumps({"schema_version": 1, "files": [
            {"path": "ISSUE.md", "sha256": "0" * 64, "editable": False},
            {"path": "module.py", "sha256": "0" * 64, "editable": True}]}),
            encoding="utf-8")
        manifest.chmod(0o600)
        q4u_load_spec(manifest)
        try:
            q1_load_spec(manifest)
        except ValueError:
            historical_q1_rejects = True
        else:
            historical_q1_rejects = False
    checks = {task_id: all(row.values()) for task_id, row in results.items()}
    checks["historical_q1_rejects_one_editable"] = historical_q1_rejects
    return {"schema_version": 1, "result": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks, "details": results, "provider_calls": 0,
            "provider_cost_usd": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.repo)
    except (OSError, ValueError, RuntimeError, KeyError,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:500]}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
