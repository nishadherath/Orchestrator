#!/usr/bin/env python3
"""Run fake B0, N2 and N3 paths from a copied distribution in isolation."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = r'''
import json
import subprocess
import sys
from pathlib import Path
bundle = Path(sys.argv[1]).resolve()
project = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(bundle / "tools"))
from task_executor import TaskExecutor
from managed_delegation import ManagedDelegation
from worker_selector import assess
from worker_adapter import WorkerAdapter
class Fake:
    def __init__(self): self.calls = 0
    def capability(self, root):
        return {"configured": True, "actor_root": str(root.resolve()),
                "graft_only": True, "managed_delegation_enforced": True,
                "supported_cells": ["worker-sonnet-low", "worker-opus-high"],
                "budget_enforced": True,
                "cancellation_supported": True, "max_child_depth": 1,
                "max_child_concurrency": 1, "enforcement_proven": True}
    def run(self, request):
        self.calls += 1
        for path in request.allowed_edits:
            (project / path).write_text("done", encoding="utf-8")
        return {"admission_token": request.admission_token, "invocation_id": request.invocation_id,
                "revision_id": request.revision_id, "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest, "requested_cell": request.requested_cell,
                "actual_model": "claude-sonnet-5", "identity_valid": True, "child_models": [],
                "effort_evidence": "cli-argument:low",
                "terminal": True, "writer_stopped": True, "status": "completed", "cost_usd": 0.02,
                "usage": {"cost_usd": 0.02, "currency": "USD", "cost_source": "provider_reported"}}
contract = {"version": 1, "kind": "command", "criteria": ["output exists"],
            "required_outputs": ["output.txt"], "protected_paths": [],
            "command": [sys.executable, "-c", "from pathlib import Path; assert Path('output.txt').read_text() == 'done'"]}
(project / "acceptance.json").write_text(json.dumps(contract), encoding="utf-8")
fake = Fake()
executor = TaskExecutor(project, fake)
root = executor.admit(goal="Create output", scope=["output.txt"], permissions=["read", "edit"],
                      acceptance_path=project / "acceptance.json", budget_usd=1.0,
                      authority_id="isolated_grant", actor="operator")
assessment = assess({"task_kind": "implementation", "complexity": "routine",
    "verification": "executable", "context_tokens": 1000, "deadline_seconds": None,
    "failure_cause": "none", "prior_local_repairs": 0, "frame_confidence": "clear",
    "required_artefacts": ["output.txt"],
    "evidence": [{"source": "operator", "reference": "task", "claim": "create output"}]})
shadow = executor.shadow_select(root, assessment, override={"cell": "worker-opus-high",
    "actor": "operator", "authority_id": "consumer_override", "reason": "inspect candidate",
    "max_cost_usd": 1.0})
assert shadow["decision"]["selected_cell"] == "worker-opus-high"
assert shadow["b0_cell"] == "worker-sonnet-low"
audit = [sys.executable, str(bundle / "tools" / "task_executor.py"),
         "--audit", "--project", str(project)]
assert subprocess.run(audit, capture_output=True).returncode == 2
result = executor.run(root)
assert result["state"] == "accepted", result["state"]
assert result["budget"]["spent_usd"] == 0.02
assert result["budget"]["unresolved"] == []
assert fake.calls == 1
assert result["attempts"][0]["requested_cell"] == "worker-sonnet-low"
assert subprocess.run(audit, capture_output=True).returncode == 0
assert WorkerAdapter.__module__ == "worker_adapter"
child_contract = {**contract, "required_outputs": ["child.txt"],
                  "command": [sys.executable, "-c", "from pathlib import Path; assert Path('child.txt').read_text() == 'done'"]}
(project / "child-acceptance.json").write_text(json.dumps(child_contract), encoding="utf-8")
second = executor.admit(goal="Complete delegated output", scope=["child.txt", "output.txt"],
    permissions=["read", "edit"], acceptance_path=project / "acceptance.json",
    budget_usd=0.5, authority_id="isolated_child_grant", actor="operator")
proposal = {"version": 1, "max_depth": 1, "max_concurrency": 1,
    "parent_reserve_usd": 0.1, "parallel_reason": "", "items": [{
        "id": "child", "parent_id": None, "depends_on": [], "goal": "child output",
        "reads": [], "writes": ["child.txt"], "permissions": ["read", "edit"],
        "acceptance_path": "child-acceptance.json", "requested_cell": "worker-sonnet-low",
        "allowance_usd": 0.2, "envelope_usd": 0.2, "deadline_at": None,
        "return_contract": "verified_acceptance"}]}
managed = ManagedDelegation(executor)
managed.admit(second, proposal, actor="operator", authority_id="isolated_child_plan")
assert managed.run(second)["delegation"]["state"] == "complete"
assert executor.run(second)["state"] == "accepted"
assert executor.status(second)["budget"]["spent_usd"] == 0.04
assert fake.calls == 3
assert subprocess.run(audit, capture_output=True).returncode == 0
print("PASS: isolated bundle import, B0, managed child and shadow selector")
'''


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="worker-consumer-") as folder:
        base = Path(folder)
        shutil.copytree(ROOT / "dist", base / "bundle")
        (base / "project").mkdir()
        proc = subprocess.run([sys.executable, "-I", "-c", SCRIPT,
                               str(base / "bundle"), str(base / "project")],
                              cwd=base, capture_output=True, text=True, timeout=60)
        if proc.returncode:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
        else:
            print(proc.stdout.strip())
        return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
