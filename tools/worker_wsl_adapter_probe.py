#!/usr/bin/env python3
"""Probe the real WSL WorkerAdapter path without provider credentials."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from worker_adapter import WorkerRequest
from worker_wsl_attestation import OUTPUT, temporary_actor
from worker_wsl_transport import WslWorkerAdapter


def run() -> dict:
    with temporary_actor("worker-n5-adapter-") as actor:
        (actor / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (actor / "public_check.py").write_text("assert True\n", encoding="utf-8")
        (actor / "ISSUE.md").write_text("Probe startup.\n", encoding="utf-8")
        (actor / "acceptance.json").write_text('{"schema_version":1}\n',
                                                encoding="utf-8")
        adapter = WslWorkerAdapter(OUTPUT)
        capability = adapter.capability(actor)
        request = WorkerRequest(actor, "Probe startup", ("app.py",),
                                "worker-sonnet-low", 0.01, "No paid call",
                                timeout_s=30, admission_token="probe",
                                invocation_id=uuid.uuid4().hex, revision_id="probe",
                                decision_digest="probe", intent_digest="probe")
        receipt = adapter.run(request)
        checks = {
            "attested_capability": capability["enforcement_proven"],
            "receipt_identity": receipt["invocation_id"] == request.invocation_id,
            "terminal_auth_failure": receipt["terminal"] and receipt["status"] == "failed",
            "writer_stopped": receipt["writer_stopped"],
            "zero_provider_charge": receipt["cost_usd"] == 0,
            "attestation_in_receipt": receipt["command_contract"].get(
                "host_attestation_sha256") == capability["host_attestation_sha256"],
            "source_unchanged": (actor / "app.py").read_text(encoding="utf-8")
            == "VALUE = 1\n",
        }
        return {"result": "PASS" if all(checks.values()) else "FAIL", "checks": checks}


if __name__ == "__main__":
    value = run()
    print(json.dumps(value, sort_keys=True))
    raise SystemExit(0 if value["result"] == "PASS" else 1)
