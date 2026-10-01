"""Provider-free post-build K02 manifest and admitted-root check."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "tools"))

import controller_x5_public_risk_live as live


live.configure_case("K02")
manifest = live.load(root / "test/results/2026-09-30-controller-x5-public-risk-k02-manifest.json")
assert manifest == live.freeze()
state = live.entry(manifest, "B0").status(live.root_id(manifest, "B0"))
assert state["state"] == "ready" and not state["attempts"]
assert state["budget"]["spent_usd"] == 0
print({"manifest_sha256": manifest["manifest_sha256"],
       "producer_ready": True, "provider_calls": 0})
