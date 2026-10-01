"""Provider-free check of the frozen A public assessment packet."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "tools"))

import controller_public_assessment
import controller_x5_public_risk_live as live


manifest = live.load(root / "test/results/2026-09-30-controller-x5-public-risk-k01-recovery-v2-manifest.json")
actor = live.actor_path(manifest, "A")
state = live.entry(manifest, "A").status(live.root_id(manifest, "A"))
inputs = live.assessment_inputs(actor)
packet = controller_public_assessment.collect(
    actor, issue=inputs["issue"], source_paths=inputs["source_paths"],
    quote_requests=inputs["quote_requests"],
    input_revision=state["definition"]["input_revision"])
issue_text = next(row["content"] for row in packet["sources"]
                  if row["path"] == packet["issue_path"])
assert issue_text == state["definition"]["goal"]
assert state["state"] == "ready" and not state["attempts"]
print({"issue_matches_goal": True,
       "source_count": len(packet["sources"]),
       "quote_count": len(inputs["quote_requests"]),
       "provider_calls": 0})
