"""Q4U ladders are frozen from cited public bytes and actually dispatched."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import model_registry  # noqa: E402
import acceptance as acceptance_module  # noqa: E402
from task_executor import ExecutorError  # noqa: E402
from worker_q4u_executor import Q4UTaskExecutor  # noqa: E402
from worker_q4u_contract import build as contract  # noqa: E402


class FakeAdapter:
    offline_fake = True

    def __init__(self):
        self.calls = []

    def capability(self, root):
        return {"actor_root": str(root.resolve()), "enforcement_proven": False,
                "budget_enforced": True,
                "supported_cells": ["worker-opus-high", "worker-sonnet-low",
                                    "worker-sonnet-medium"]}

    def run(self, request):
        self.calls.append(request.requested_cell)
        model = model_registry.resolve_cell(request.requested_cell)
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": model["expected_provider_model"],
                "identity_valid": True, "child_models": [],
                "status": "completed", "terminal": True,
                "writer_stopped": True, "cost_usd": 0.1,
                "usage": {"cost_usd": 0.1},
                "effort_evidence": f"cli-argument:{model['effort']}",
                "started_at": "2026-09-26T00:00:00Z",
                "finished_at": "2026-09-26T00:00:01Z", "wall_clock_s": 1.0}


class Q4UDispatchTests(unittest.TestCase):
    def test_initial_and_conditional_repair_ladders(self):
        for task_id, arm, expected in (
                ("D01W", "cross_component_medium",
                 ["worker-sonnet-medium", "worker-sonnet-low", "worker-opus-high"]),
                ("B02W", "coverage_repair",
                 ["worker-sonnet-low", "worker-sonnet-medium", "worker-opus-high"]),
                ("B02S", "coverage_repair",
                 ["worker-sonnet-low", "worker-sonnet-low", "worker-opus-high"]),
                ("C03", "coverage_repair", ["worker-sonnet-low"])):
            with self.subTest(task=task_id, arm=arm):
                folder = ROOT / "test/fixtures/worker_q4u_public" / task_id
                with tempfile.TemporaryDirectory(prefix="q4u-dispatch-") as raw:
                    project = Path(raw) / "actor"
                    shutil.copytree(folder / "actor", project)
                    acceptance = project / ".claude/acceptance.json"
                    acceptance.parent.mkdir()
                    acceptance.write_text(json.dumps(contract(task_id)), encoding="utf-8")
                    public = json.loads((folder / "public_assessment.json").read_text(
                        encoding="utf-8"))
                    adapter = FakeAdapter()
                    contract_value = contract(task_id)
                    def checked_public_runner(argv, *, cwd, capture_output,
                                              timeout, shell):
                        proof = {
                            "artefacts_digest": acceptance_module.snapshot(
                                cwd, contract_value["required_outputs"])["digest"],
                            "protected_digest": acceptance_module.snapshot(
                                cwd, contract_value["protected_paths"])["digest"],
                        }
                        proof["sha256"] = acceptance_module.digest(proof)
                        process = subprocess.CompletedProcess(argv, 0, b"", b"")
                        process.isolation_evidence = proof
                        return process
                    executor = Q4UTaskExecutor(
                        project, adapter, command_runner=checked_public_runner)
                    spec = {"schema_version": 3, "arm": arm,
                            "manifest_sha256": "c" * 64,
                            "public_assessment": public,
                            "cost_ceiling_usd": 4.0}
                    root = executor.admit(
                        goal="Complete the public issue", scope=contract(task_id)["required_outputs"],
                        permissions=["read", "edit"], acceptance_path=acceptance,
                        budget_usd=4.0, authority_id="q4u-probe", actor="operator",
                        experimental_dispatch=spec)
                    executor.run(root)
                    self.assertEqual(expected, adapter.calls)
                    self.assertEqual("Q4U-verification-v3",
                                     executor.status(root)["admission"]["policy"])

    def test_public_bytes_are_bound_at_admission(self):
        folder = ROOT / "test/fixtures/worker_q4u_public/B02W"
        with tempfile.TemporaryDirectory(prefix="q4u-drift-") as raw:
            project = Path(raw) / "actor"
            shutil.copytree(folder / "actor", project)
            acceptance = project / ".claude/acceptance.json"
            acceptance.parent.mkdir()
            acceptance.write_text(json.dumps(contract("B02W")), encoding="utf-8")
            (project / "ISSUE.md").write_text("drift", encoding="utf-8")
            public = json.loads((folder / "public_assessment.json").read_text(
                encoding="utf-8"))
            with self.assertRaises(ExecutorError):
                Q4UTaskExecutor(project, FakeAdapter()).admit(
                    goal="Complete the public issue", scope=["boltons/jsonutils.py"],
                    permissions=["read", "edit"], acceptance_path=acceptance,
                    budget_usd=4.0, authority_id="q4u-probe", actor="operator",
                    experimental_dispatch={"schema_version": 3,
                                           "arm": "coverage_repair",
                                           "manifest_sha256": "c" * 64,
                                           "public_assessment": public,
                                           "cost_ceiling_usd": 4.0})


if __name__ == "__main__":
    unittest.main()
