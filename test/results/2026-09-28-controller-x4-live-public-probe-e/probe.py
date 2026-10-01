"""Single fresh-root C03-D1 assessor probe after enum-definition revision."""
from __future__ import annotations

import json
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))

from test.harness.controller_x3_pair_tests import prepare
from test.harness.controller_x4_assessment_tests import AssessmentTests
from tools.controller_wsl_interpreter import PROMPT, WslPublicInterpreter


QUOTES = [
    ("issue.md", "# Ambiguous payment retry"),
    ("issue.md", "The client can lose the response after a payment commits"),
    ("issue.md", "same idempotency key. Repair"),
    ("issue.md", "original result without charging again"),
    ("issue.md", "must be rejected, and keys belong to tenants"),
    ("issue.md", "must remain retryable"),
    ("payment.py", "Faulty baseline: every committed retry charges again"),
    ("payment.py", 'if attempt["phase"] == "commit":'),
    ("payment.py", 'balance += attempt["amount"]'),
    ("public_check.py", "does not cover retries or tenant separation"),
    ("public_check.py", "assert completed.returncode == 0"),
]


def main() -> int:
    home = Path(__file__).resolve().parent
    actor = home / "actor"
    if actor.exists():
        raise RuntimeError("root exists; inspect its ledger and never replay")
    executor, root_id, _ = prepare(actor, "C03-D1")
    options = AssessmentTests().inputs(executor, root_id)
    options["quote_requests"] = [
        {"source": source, "quote": quote} for source, quote in QUOTES]

    def observing_runner(command, **kwargs):
        proc = subprocess.run(command, **kwargs)
        if command[-3:] != ["auth", "status", "--json"]:
            (home / "transport-diagnostic.json").write_text(
                json.dumps({"returncode": proc.returncode,
                            "stderr": (proc.stderr or "")[:1600],
                            "stdout_tail": (proc.stdout or "")[-2400:]},
                           indent=2) + "\n", encoding="utf-8")
        return proc

    interpreter = WslPublicInterpreter(
        distro="kali-linux", linux_user="wsl",
        claude_path="/opt/orchestrator-worker-runtime/bin/claude",
        allowance_usd=options["maximum_usd"], timeout_s=180,
        runner=observing_runner)
    receipt = {"schema_version": 1, "fixture": "C03-D1",
               "started_at": datetime.now(timezone.utc).isoformat(),
               "allowance_usd": options["maximum_usd"], "root_id": root_id,
               "citation_count": len(QUOTES),
               "prompt_sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest()}
    try:
        result = executor.assess_public(root_id, interpreter=interpreter, **options)
        receipt["outcome"] = "assessed"
        receipt["telemetry"] = result["telemetry"]
        receipt["classifications"] = {
            key: result["rigour"][key] for key in (
                "consequence", "premise_uncertainty", "alternatives",
                "constraint_coupling", "verification_gap",
                "observed_failure_cause", "required_output",
                "evidence_availability")}
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
    print(json.dumps({key: receipt.get(key) for key in (
        "outcome", "error_type", "error", "root_state",
        "public_assessment_status", "telemetry", "classifications")}))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
