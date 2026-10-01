"""Read the settled H02c attempt and public verification without dispatch."""

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02c_producer as h02  # noqa: E402


def main() -> None:
    row = h02.manifest()
    state = h02.entry(row).status(h02.root_id(row))
    attempt = state["attempts"][-1]
    receipt = attempt.get("receipt") or {}
    actor = h02.actor_path(row)
    plugin = actor / "pytest_asyncio/plugin.py"
    print(json.dumps({
        "state": state["state"], "attempt_count": len(state["attempts"]),
        "attempt_process_state": attempt.get("process_state"),
        "attempt_verification": attempt.get("verification"),
        "receipt_status": receipt.get("status"),
        "receipt_terminal": receipt.get("terminal"),
        "receipt_identity_valid": receipt.get("identity_valid"),
        "receipt_actual_model": receipt.get("actual_model"),
        "receipt_requested_effort": receipt.get("requested_effort"),
        "receipt_cost_usd": receipt.get("cost_usd"),
        "receipt_usage": receipt.get("usage"),
        "actor_path": str(actor),
        "candidate_plugin_sha256": hashlib.sha256(plugin.read_bytes()).hexdigest(),
        "baseline_plugin_sha256": row["actor_files"]["pytest_asyncio/plugin.py"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
