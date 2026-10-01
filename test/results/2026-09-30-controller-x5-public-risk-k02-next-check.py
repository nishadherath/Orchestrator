"""Run K02's predeclared public next check on accepted producer bytes."""

from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "tools"))

import controller_x5_public_risk_live as live


live.configure_case("K02")
manifest = live.load(root / "test/results/2026-09-30-controller-x5-public-risk-k02-manifest.json")
actor = live.actor_path(manifest, "B0")
state = live.entry(manifest, "B0").status(live.root_id(manifest, "B0"))
assert state["state"] == "accepted"
assert len(state["attempts"]) == 1 and not state["budget"]["unresolved"]
sys.path.insert(0, str(actor))

from gateway import Gateway
from payment_service import submit_payment


gateway = Gateway("after")
first = submit_payment(gateway, "public-follow-up-1", 800)
assert len(gateway.calls) == 2 and len(gateway.debits) == 1
same = submit_payment(gateway, "public-follow-up-1", 800)
assert same == first and len(gateway.debits) == 1
different = submit_payment(gateway, "public-follow-up-2", 800)
assert different["payment_id"] == "public-follow-up-2"
assert len(gateway.debits) == 2
print({"after_debit_retry_one_debit": True,
       "same_id_stable_receipt": True,
       "distinct_ids_independent": True,
       "provider_calls": 0})
