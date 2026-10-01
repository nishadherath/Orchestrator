"""Close the K01 A worker hold after a proved pre-provider Graft failure."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "tools"))

import controller_x5_public_risk_live as live


manifest = live.load(root / "test/results/2026-09-30-controller-x5-public-risk-k01-recovery-v2-manifest.json")
executor = live.entry(manifest, "A")
rid = live.root_id(manifest, "A")
state = executor.status(rid)
attempt = state["attempts"][-1]
assert state["state"] == "uncertain"
assert attempt["process_state"] == "uncertain" and attempt["receipt"] is None
assert state["budget"]["unresolved"] == [attempt["invocation_id"]]
assert state["journal"][-1]["kind"] == "transition"
assert "isolated Graft build failed: umount: /mnt/c: target is busy" in state["journal"][-1]["data"]["reason"]
actor = Path("/var/lib/orchestrator-worker-n4/actors") / ("q1-" + attempt["invocation_id"])
assert actor.is_dir()
evidence = ("K01 A journal transition 16 records isolated Graft build failure "
            "(umount /mnt/c target busy); worker_wsl_q3_adapter._run_process "
            "builds actor graph before _invoke, so no worker provider call began. "
            "The staged actor has no worker receipt, no matching process "
            "was present at audit, and the Controller session reconciled separately.")
closed = executor.reconcile_uncertain(
    rid, actor="x5-k01-host-audit", reason="pre-provider isolated Graft build failure",
    cost_usd=0.0, evidence=evidence, writers_stopped=True)
print({"state": closed["state"], "unresolved": closed["budget"]["unresolved"],
       "spent_usd": closed["budget"]["spent_usd"], "worker_cost_usd": 0.0})
