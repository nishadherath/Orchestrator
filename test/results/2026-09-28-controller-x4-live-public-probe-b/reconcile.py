"""Reconcile this one known pre-provider CLI rejection; no provider call."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT)]

from test.harness.controller_x3_pair_tests import FIXTURES, FakeWorker
from task_executor import TaskExecutor

home = Path(__file__).resolve().parent
source = home / "transport-diagnostic.json"
raw = source.read_bytes()
diagnostic = json.loads(raw)
if (diagnostic != {
        "returncode": 1,
        "stderr": "Error: --json-schema is not valid JSON: JSON Parse error: Unable to parse JSON string\n",
        "stdout_tail": ""}):
    raise RuntimeError("transport evidence differs; do not settle zero")
executor = TaskExecutor(
    home / "actor", FakeWorker(FIXTURES / "C03-D1" / "variants" / "reference"))
status = executor.reconcile_public_assessment(
    "offline-pair-root", actor="codex-x4-investigation",
    reason="CLI parser rejected JSON before provider dispatch",
    cost_usd=0.0,
    evidence="transport-diagnostic-sha256:" + hashlib.sha256(raw).hexdigest(),
    writers_stopped=True)
summary = {"state": status["state"],
           "assessment_status": status["public_assessment"]["status"],
           "spent_usd": status["budget"]["spent_usd"],
           "unresolved": status["budget"]["unresolved"]}
(home / "reconciliation.json").write_text(
    json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary))
