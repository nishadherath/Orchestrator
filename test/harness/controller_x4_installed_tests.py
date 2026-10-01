#!/usr/bin/env python3
"""Exercise packaged Controller controls against a fresh consumer task.

The isolated child imports only files installed from dist. The fake assessor
and worker make this an integration and packaging check, not a quality claim.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "test/fixtures/controller_x3/development"

CHILD = r'''
import json
import shutil
import subprocess
import sys
from pathlib import Path

project, reference, mode, case = (Path(sys.argv[1]), Path(sys.argv[2]),
                                  sys.argv[3], sys.argv[4])
sys.path.insert(0, str(project / "tools"))
import controller_workflow
import model_registry
import task_executor

class Worker:
    offline_fake = True

    def __init__(self):
        self.calls = 0

    def capability(self, actor_root):
        return {"actor_root": str(actor_root.resolve()),
                "enforcement_proven": False, "budget_enforced": True,
                "supported_cells": sorted(model_registry.load()["cells"])}

    def run(self, request):
        self.calls += 1
        for source in reference.rglob("*"):
            if source.is_file():
                target = request.actor_root / source.relative_to(reference)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        cell = model_registry.resolve_cell(request.requested_cell)
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": cell["expected_provider_model"],
                "identity_valid": True, "child_models": [],
                "status": "completed", "terminal": True,
                "writer_stopped": True, "cost_usd": 0.1,
                "usage": {"cost_usd": 0.1, "cost_source": "synthetic-fixture",
                          "currency": "USD", "input_tokens": 0,
                          "output_tokens": 0, "cache_creation_input_tokens": 0,
                          "cache_read_input_tokens": 0},
                "effort_evidence": "cli-argument:" + cell["effort"],
                "started_at": "2026-09-28T00:00:00Z",
                "finished_at": "2026-09-28T00:00:01Z", "wall_clock_s": 1.0}

def interpret(packet):
    fields = {"task_kind": "implementation", "complexity": "routine",
              "verification": "executable", "failure_cause": "none",
              "frame_confidence": "clear", "consequence": "contained",
              "premise_uncertainty": "none", "alternatives": "one-established",
              "constraint_coupling": "local",
              "verification_gap": "strong-existing-checks",
              "observed_failure_cause": "none", "required_output": "patch",
              "evidence_availability": "available"}
    if case == "C03-D1":
        fields.update(consequence="consequential",
                      premise_uncertainty="specific-checkable",
                      alternatives="several-material",
                      constraint_coupling="cross-module")
    return {"interpretation": {"schema_version": 1,
                                "classifications": fields,
                                "field_evidence": {key: ["e1", "e2"] for key in fields},
                                "material_evidence": []},
            "telemetry": {"provider_calls": 0, "model": None,
                          "cost_usd": 0, "input_tokens": 0,
                          "output_tokens": 0}}

control = project / "tools/controller_control.py"
def command(*arguments):
    run = subprocess.run([sys.executable, str(control), "--project", str(project),
                          *arguments], cwd=project, capture_output=True, text=True)
    assert run.returncode == 0, (run.stdout, run.stderr)
    result = json.loads(run.stdout)
    assert result["paid_work_started"] is False
    return result

command("set", "--mode", mode, "--scope", "project")
assert command("resolve")["decision"]["mode"] == mode
editable = json.loads((project / "acceptance.json").read_text(
    encoding="utf-8"))["editable_paths"]
contract = project / "n1-acceptance.json"
contract.write_text(json.dumps({
    "version": 1, "kind": "command", "criteria": ["public check passes"],
    "constraints": [], "required_outputs": editable,
    "protected_paths": ["issue.md", "app.py", "public_check.py"],
    "command": [sys.executable, "-B", "public_check.py"], "timeout_s": 10,
}), encoding="utf-8")
worker = Worker()
executor = task_executor.TaskExecutor(project, worker)
goal = (project / "issue.md").read_text(encoding="utf-8")
root = executor.admit(goal=goal, scope=editable, permissions=["read", "edit"],
                      input_paths=["issue.md", "app.py", "public_check.py"],
                      acceptance_path=contract, budget_usd=12.0,
                      authority_id="installed-smoke-grant", actor="operator",
                      root_id="installed-smoke-root")
source = next(path for path in editable if path != "report.json")
heading = next(line for line in goal.splitlines() if line.startswith("# "))
lines = (project / "public_check.py").read_text(encoding="utf-8").splitlines()
assertion = next(line for line in lines
                 if line.lstrip().startswith("assert ") and lines.count(line) == 1)
result = controller_workflow.execute(
    executor, root, issue="issue.md",
    source_paths=list(dict.fromkeys(["issue.md", "app.py", "public_check.py", source])),
    quote_requests=[{"source": "issue.md", "quote": heading},
                    {"source": "public_check.py", "quote": assertion}],
    interpreter=interpret,
    operational={"context_tokens": 1000, "deadline_seconds": None,
                 "prior_local_repairs": 0, "required_artefacts": editable,
                 "deadline": None, "authorised_task_budget_usd": 12.0,
                 "observed_at": "2026-09-28T00:00:00Z"},
    assessment_allowance_usd=0.5)
assert result["decision"]["override_scope"] == "project", result["decision"]
assert result["task"]["budget"]["unresolved"] == []
if mode == "on" or case == "C03-D1":
    assert result["decision"]["effective_action"] == "controller"
    assert result["task"]["state"] == "blocked"
    assert worker.calls == 0
else:
    assert result["decision"]["effective_action"] == "worker"
    assert result["task"]["state"] == "accepted", result["task"]
    assert worker.calls == 1
status = command("status", "--root-id", root)["view"]
assert status["current_intent"]["mode"] == mode
assert status["effective_action"] == result["decision"]["effective_action"]
print("PASS: installed " + mode + " " + case + " controls next admission")
'''


class InstalledControllerTests(unittest.TestCase):
    def test_packaged_control_affects_next_task(self):
        with tempfile.TemporaryDirectory(prefix="controller-x4-installed-") as raw:
            base = Path(raw)
            for mode, case in (("on", "N04-D1"), ("off", "N04-D1"),
                               ("auto", "N04-D1"), ("auto", "C03-D1")):
                project = base / (mode + "-" + case)
                fixture = FIXTURES / case
                shutil.copytree(fixture / "actor", project)
                installed = subprocess.run(
                    [sys.executable, str(ROOT / "dist/install.py"), "apply",
                     "--bundle", str(ROOT / "dist"), "--target", str(project),
                     "--json"], capture_output=True, text=True, timeout=90)
                self.assertEqual(0, installed.returncode,
                                 (installed.stdout, installed.stderr))
                run = subprocess.run(
                    [sys.executable, "-I", "-c", CHILD,
                     str(project), str(fixture / "variants/reference"),
                     mode, case], cwd=base,
                    capture_output=True, text=True, timeout=120)
                self.assertEqual(0, run.returncode, (run.stdout, run.stderr))
                self.assertIn("installed " + mode + " " + case, run.stdout)


if __name__ == "__main__":
    unittest.main()
