"""Read the already settled N1 root; never starts or replays a provider call."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from test.harness.controller_x3_pair_tests import FakeWorker
from tools.task_executor import TaskExecutor

home = Path(__file__).resolve().parent
actor = home / "actor"
state = TaskExecutor(actor, FakeWorker(
    ROOT / "test/fixtures/controller_x3/development/C03-D1/variants/reference"
)).status("offline-pair-root")
assessment = state["public_assessment"]
result = assessment["result"]
rigour = result["rigour"]
worker = result["worker"]
observation = {
    "source": "persisted N1 root; no provider call",
    "public_assessment_status": assessment["status"],
    "root_state": state["state"],
    "spent_usd": state["budget"]["spent_usd"],
    "unresolved": state["budget"]["unresolved"],
    "rigour": {key: rigour[key] for key in (
        "consequence", "premise_uncertainty", "alternatives",
        "constraint_coupling", "verification_gap", "observed_failure_cause",
        "required_output", "evidence_availability")},
    "worker": worker["facts"],
}
(home / "settled-observation.json").write_text(
    json.dumps(observation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(observation, sort_keys=True))
