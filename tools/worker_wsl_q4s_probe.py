#!/usr/bin/env python3
"""Exercise the Q4S schema boundary with three zero-provider fake workers."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


def run(repo: Path) -> dict:
    if sys.platform != "linux":
        raise RuntimeError("Q4S boundary probe runs inside WSL")
    sys.path.insert(0, str(repo / "tools"))
    import model_registry
    from worker_adapter import CapabilityError, WorkerRequest, digest
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q4s_adapter import LAUNCHER, Q4SWslAdapter, SUPPORTED_CELLS

    catalogue = json.loads((repo / "test/fixtures/worker_q2_public/catalogue.json")
                           .read_text(encoding="utf-8"))
    task = next(row for row in catalogue["tasks"] if row["id"] == "P01")
    source = repo / "test/fixtures/worker_q2_public/P01/actor"
    receipts = []
    protected_results = []

    class FakeAdapter(Q4SWslAdapter):
        def _invoke(self, command: list[str], actor: Path,
                    request: WorkerRequest) -> subprocess.CompletedProcess:
            model = model_registry.resolve_cell(request.requested_cell)[
                "expected_provider_model"]
            code = '''import json, os
from pathlib import Path
for name in ("cachetools/func.py", "cachetools/keys.py"):
    path = Path(name)
    path.write_bytes(path.read_bytes() + b"\\n# q4 probe\\n")
report = {"status":"completed", "diagnosis":"provider-free boundary probe",
          "evidence":["project=" + os.environ.get("CLAUDE_PROJECT_DIR", ""),
                      "api_key=" + str(bool(os.environ.get("ANTHROPIC_API_KEY"))),
                      "turns=" + os.environ.get("CLAUDE_CODE_MAX_TURNS", ""),
                      "retries=" + os.environ.get("MAX_STRUCTURED_OUTPUT_RETRIES", "")],
          "checks":[{"command":"python3 -B public_check.py","outcome":"not_run"}],
          "remaining":[], "clarification":None}
print(json.dumps({"type":"assistant","message":{"model":MODEL,"content":[]}}))
print(json.dumps({"type":"result","subtype":"success","result":"Report complete.",
                  "structured_output":report,
                  "total_cost_usd":0.0,
                  "usage":{"input_tokens":0,"output_tokens":0},
                  "modelUsage":{MODEL:{"costUSD":0.0}}}))
'''.replace("MODEL", repr(model))
            argv = [str(LAUNCHER), str(actor), "--", "/usr/bin/python3", "-B", "-c", code]
            return subprocess.run(argv, cwd="/", capture_output=True, timeout=30)

    for cell in sorted(SUPPORTED_CELLS):
        with tempfile.TemporaryDirectory(prefix="q4s-adapter-probe-", dir=SEEDS) as raw:
            workspace = Path(raw)
            for relative in task["actor_files"]:
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((source / relative).read_bytes())
            protected_before = {relative: (workspace / relative).read_bytes()
                                for relative in task["actor_files"]
                                if relative not in task["editable_paths"]}
            request = WorkerRequest(
                workspace, "Provider-free Q4S report and transport probe",
                tuple(task["editable_paths"]), cell, 4.0, "Q4S probe", timeout_s=60,
                admission_token=uuid.uuid4().hex, invocation_id=uuid.uuid4().hex,
                revision_id=uuid.uuid4().hex, decision_digest=uuid.uuid4().hex,
                intent_digest=uuid.uuid4().hex)
            receipt = FakeAdapter(task).run(request)
            receipts.append(receipt)
            protected_results.append(all((workspace / relative).read_bytes() == content
                                         for relative, content in protected_before.items()))

    with tempfile.TemporaryDirectory(prefix="q4s-adapter-reject-", dir=SEEDS) as raw:
        workspace = Path(raw)
        for relative in task["actor_files"]:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / relative).read_bytes())
        rejected_request = WorkerRequest(
            workspace, "Reject unsupported cell", tuple(task["editable_paths"]),
            "worker-fable-high", 4.0, "Q4S probe", timeout_s=60,
            admission_token=uuid.uuid4().hex, invocation_id=uuid.uuid4().hex,
            revision_id=uuid.uuid4().hex, decision_digest=uuid.uuid4().hex,
            intent_digest=uuid.uuid4().hex)
        try:
            FakeAdapter(task).run(rejected_request)
        except CapabilityError:
            unsupported_rejected = True
        else:
            unsupported_rejected = False

    checks = {
        "three_cells_exercised": {row["requested_cell"] for row in receipts}
                                 == SUPPORTED_CELLS,
        "exact_identity": all(row["identity_valid"] for row in receipts),
        "writers_stopped": all(row["terminal"] and row["writer_stopped"]
                               for row in receipts),
        "two_edits_collected": all(len(row["command_contract"]["q4s_boundary"][
            "changed_paths"]) == 2 for row in receipts),
        "protected_source_unchanged": all(protected_results),
        "reports_present": all(row["evaluation_report"]["observability"] == "present"
                               for row in receipts),
        "report_digests_bound": all(row["evaluation_report_digest"]
                                    == digest(row["evaluation_report"])
                                    for row in receipts),
        "collected_revision_bound": all(row["evaluation_report"]["binding"][
            "final_revision_sha256"] == digest(row["command_contract"][
                "q4s_boundary"]["after_sha256"]) for row in receipts),
        "schema_transport_bound": all(row["evaluation_transport"]["mode"]
                                      == "claude-code-json-schema-v1" and
                                      row["evaluation_transport"]["structured_output_present"]
                                      for row in receipts),
        "restricted_environment": all(
            "api_key=False" in row["evaluation_report"]["report"]["evidence"]
            and "turns=20" in row["evaluation_report"]["report"]["evidence"]
            and "retries=2" in row["evaluation_report"]["report"]["evidence"]
            and any(item.startswith("project=/var/lib/orchestrator-worker-n4/actors/q1-")
                    for item in row["evaluation_report"]["report"]["evidence"])
            for row in receipts),
        "unsupported_cell_rejected": unsupported_rejected,
        "zero_provider_cost": all(row["cost_usd"] == 0 for row in receipts),
    }
    return {"schema_version": 1, "result": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks, "supported_cells": sorted(SUPPORTED_CELLS),
            "provider_calls": 0, "provider_cost_usd": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = run(args.repo)
    except (OSError, ValueError, RuntimeError, KeyError,
            subprocess.TimeoutExpired) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:500]}))
        return 1
    print(json.dumps(value, sort_keys=True))
    return 0 if value["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
