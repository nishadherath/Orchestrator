#!/usr/bin/env python3
"""Run one fake B0 task from a copied distribution with no source-tree imports."""
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
from worker_adapter import WorkerAdapter
class Fake:
    def __init__(self): self.calls = 0
    def capability(self, root):
        return {"configured": True, "actor_root": str(root.resolve()), "enforcement_proven": False}
    def run(self, request):
        self.calls += 1
        (project / "output.txt").write_text("done", encoding="utf-8")
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
audit = [sys.executable, str(bundle / "tools" / "task_executor.py"),
         "--audit", "--project", str(project)]
assert subprocess.run(audit, capture_output=True).returncode == 2
result = executor.run(root)
assert result["state"] == "accepted", result["state"]
assert result["budget"]["spent_usd"] == 0.02
assert result["budget"]["unresolved"] == []
assert fake.calls == 1
assert subprocess.run(audit, capture_output=True).returncode == 0
assert WorkerAdapter.__module__ == "worker_adapter"
print("PASS: isolated bundle import and fake B0 execution")
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
