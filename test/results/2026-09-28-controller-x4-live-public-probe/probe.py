"""One-shot X4 live public-assessment qualification; never replays a root."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from test.harness.controller_x3_pair_tests import prepare
from test.harness.controller_x4_assessment_tests import AssessmentTests
from tools import controller_wsl_interpreter


def main() -> int:
    home = Path(__file__).resolve().parent
    actor = home / "actor"
    if actor.exists():
        raise RuntimeError("live probe actor already exists; inspect its ledger, never replay")
    executor, root_id, _ = prepare(actor, "C03-D1")
    options = AssessmentTests().inputs(executor, root_id)
    interpreter = controller_wsl_interpreter.WslPublicInterpreter(
        distro="kali-linux", linux_user="wsl",
        claude_path="/opt/orchestrator-worker-runtime/bin/claude",
        allowance_usd=options["maximum_usd"], timeout_s=180)
    receipt = {"schema_version": 1, "fixture": "C03-D1",
               "started_at": datetime.now(timezone.utc).isoformat(),
               "allowance_usd": options["maximum_usd"], "root_id": root_id}
    try:
        result = executor.assess_public(root_id, interpreter=interpreter, **options)
        receipt["outcome"] = "assessed"
        receipt["telemetry"] = result["telemetry"]
        receipt["worker_cell"] = result["worker"].get("selected_cell")
        return_code = 0
    except Exception as exc:
        receipt["outcome"] = "failed"
        receipt["error_type"] = type(exc).__name__
        receipt["error"] = str(exc)
        return_code = 1
    finally:
        status = executor.status(root_id)
        receipt["root_state"] = status["state"]
        receipt["public_assessment_status"] = (
            status.get("public_assessment") or {}).get("status")
        receipt["budget"] = status["budget"]
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        (home / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt.get(key) for key in
                      ("outcome", "error_type", "error", "root_state",
                       "public_assessment_status", "telemetry")}))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
