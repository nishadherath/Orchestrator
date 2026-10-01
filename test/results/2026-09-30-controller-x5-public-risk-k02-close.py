"""Close K02 when its predeclared public risk is resolved by the producer."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "tools"))

import controller_x5_public_risk_live as live


live.configure_case("K02")
manifest = live.load(root / "test/results/2026-09-30-controller-x5-public-risk-k02-manifest.json")
result = live.load(live.RUN_DIR / "producer-result.json")
assert result["manifest_sha256"] == manifest["manifest_sha256"]
assert result["eligible"] is True and result["qualified"] is True
for arm in ("S", "A"):
    state = live.entry(manifest, arm).status(live.root_id(manifest, arm))
    assert state["state"] == "ready" and not state["attempts"]
    assert state["budget"]["spent_usd"] == 0
record = {
    "schema_version": 1,
    "manifest_sha256": manifest["manifest_sha256"],
    "producer_root_id": result["root_id"],
    "producer_reported_api_equivalent_usd": result["budget"]["spent_usd"],
    "risk_digest": manifest["risk_digest"],
    "public_next_check": {
        "after_debit_retry_one_debit": True,
        "same_id_stable_receipt": True,
        "distinct_ids_independent": True,
        "evidence_script": "test/results/2026-09-30-controller-x5-public-risk-k02-next-check.py",
    },
    "S_and_A_provider_calls": 0,
    "reason": "accepted public source and predeclared public next check close the duplicate-debit premise",
    "protected_oracle_executed": False,
    "replay_allowed": False,
}
live.exclusive(live.RUN_DIR / "stopped.json", record)
print({"closed": True, "producer_usd": record["producer_reported_api_equivalent_usd"],
       "review_calls": 0})
