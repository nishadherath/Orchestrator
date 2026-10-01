#!/usr/bin/env python3
"""One bounded Sonnet High identity canary on the X5 isolated worker host."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import controller_evaluation
import controller_x5_screen as screen
import controller_x5_worker_adapter
import dispatch_budget
import model_registry
import worker_adapter
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import MANIFESTS, SEEDS
from worker_wsl_q3_adapter import isolated_public_runner


TASK = "C03-D1"
CELL = "worker-sonnet-high"
LIMIT_USD = 1.0


class CanaryError(RuntimeError):
    """The X5 host canary cannot safely launch or verify one worker call."""


def _source(relative: str) -> Path:
    if relative in {"issue.md", "trace.json"}:
        return screen.ROOT / "test/fixtures/controller_x5" / TASK / relative
    return (screen.ROOT / "test/fixtures/controller_x3/development" /
            TASK / "actor" / relative)


def run(manifest: dict, notice: dict, output: Path) -> dict:
    screen.validate(manifest)
    if (notice.get("manifest_sha256") != manifest["manifest_sha256"]
            or notice.get("approved") is not True
            or notice.get("task_id") != TASK
            or notice.get("requested_cell") != CELL
            or notice.get("maximum_canary_usd") != LIMIT_USD):
        raise CanaryError("canary spend notice differs from the frozen manifest")
    if output.exists() or output.is_symlink():
        raise CanaryError("canary receipt already exists; no replay")
    CredentialStore().inspect()
    actor = SEEDS / f"x5-high-canary-{manifest['manifest_sha256'][:12]}"
    if actor.exists() or actor.is_symlink():
        raise CanaryError("canary actor already exists; no replay")
    package = manifest["packages"][TASK]
    actor.mkdir(mode=0o700)
    for relative, expected in package["actor_files"].items():
        data = _source(relative).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise CanaryError(f"canary public file changed: {relative}")
        target = actor / relative
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(data)
    editable = json.loads((actor / "acceptance.json").read_text(
        encoding="utf-8"))["editable_paths"]
    task = {"actor_files": package["actor_files"], "editable_paths": editable}
    adapter = controller_x5_worker_adapter.X5WslAdapter(task)
    capability = adapter.capability(actor)
    if (CELL not in capability["supported_cells"]
            or capability["enforcement_proven"] is not True
            or capability["budget_enforced"] is not True):
        raise CanaryError("Sonnet High isolated host capability is unavailable")
    seed = controller_evaluation.digest({
        "manifest": manifest["manifest_sha256"], "task": TASK, "cell": CELL})
    invocation_id = seed[:32]
    request = worker_adapter.WorkerRequest(
        actor_root=actor, issue=(actor / "issue.md").read_text(encoding="utf-8"),
        allowed_edits=tuple(editable), requested_cell=CELL,
        allowance_usd=LIMIT_USD, policy="x5-host-identity-canary",
        timeout_s=900.0, admission_token=seed[32:],
        invocation_id=invocation_id, revision_id=seed,
        decision_digest=seed, intent_digest=seed)
    # Generate and validate the exact command before the ledger starts.
    adapter.command(request)
    ledger_path = actor / ".claude/x5-high-budget.json"
    ledger_path.parent.mkdir(mode=0o700, exist_ok=True)
    ledger = dispatch_budget.DispatchBudget(
        ledger_path, LIMIT_USD, scope="task_dispatch")
    ledger.reserve(invocation_id, LIMIT_USD, .000001,
                   {"manifest_sha256": manifest["manifest_sha256"],
                    "task_id": TASK, "requested_cell": CELL})
    ledger.start(invocation_id)
    try:
        receipt = adapter.run(request)
    except Exception as exc:
        ledger.settle(invocation_id, None, final=False,
                      telemetry={"exception_type": type(exc).__name__},
                      evidence="x5-canary-no-terminal-receipt")
        output.write_text(json.dumps({
            "manifest_sha256": manifest["manifest_sha256"],
            "task_id": TASK, "invocation_id": invocation_id,
            "status": "uncertain", "exception_type": type(exc).__name__,
            "q1_launch_started": (MANIFESTS / f"q1-{invocation_id}.start.json").is_file(),
            "q1_launch_stopped": (MANIFESTS / f"q1-{invocation_id}.stop.json").is_file(),
            "budget": ledger.snapshot(),
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise CanaryError("canary attempt needs manual cost reconciliation") from exc
    cost = receipt.get("cost_usd")
    terminal = receipt.get("terminal") is True and receipt.get("writer_stopped") is True
    valid_cost = type(cost) in (int, float) and math.isfinite(cost) and cost >= 0
    if not valid_cost or not terminal:
        ledger.settle(invocation_id, cost if valid_cost else None,
                      final=False, telemetry={"terminal": terminal},
                      evidence="x5-canary-incomplete-receipt")
        output.write_text(json.dumps({
            "manifest_sha256": manifest["manifest_sha256"],
            "task_id": TASK, "invocation_id": invocation_id,
            "status": "uncertain", "terminal": terminal,
            "writer_stopped": receipt.get("writer_stopped"),
            "returncode": receipt.get("returncode"),
            "timed_out": receipt.get("timed_out"),
            "cost_usd": cost if valid_cost else None,
            "actual_model": receipt.get("actual_model"),
            "stream": receipt.get("stream"),
            "q1_launch_started": (MANIFESTS / f"q1-{invocation_id}.start.json").is_file(),
            "q1_launch_stopped": (MANIFESTS / f"q1-{invocation_id}.stop.json").is_file(),
            "budget": ledger.snapshot(),
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise CanaryError("canary receipt is incomplete; cost hold retained")
    ledger.settle(invocation_id, cost, final=True,
                  telemetry=receipt.get("usage") or {},
                  evidence="x5-canary-terminal-worker-receipt")
    identity = model_registry.identity_matches(
        CELL, receipt.get("actual_model"), receipt.get("child_models"))
    try:
        public = isolated_public_runner(task)(
            ["python3", "-B", "public_check.py"], cwd=actor,
            capture_output=True, timeout=30, shell=False)
        public_status = "pass" if public.returncode == 0 else "fail"
        isolation = getattr(public, "isolation_evidence", None)
    except Exception as exc:
        public_status = "verification-error:" + type(exc).__name__
        isolation = None
    result = {
        "schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
        "task_id": TASK, "actor": str(actor), "requested_cell": CELL,
        "actual_model": receipt.get("actual_model"),
        "child_models": receipt.get("child_models"),
        "served_identity_valid": identity, "terminal": terminal,
        "worker_status": receipt.get("status"),
        "cost_usd": cost, "budget": ledger.snapshot(),
        "public_check_status": public_status,
        "public_check_passed": public_status == "pass",
        "isolation_evidence": isolation,
        "provider_calls": 1,
    }
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--notice", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if os.name != "posix" or os.geteuid() != 0:
        raise CanaryError("X5 host canary requires the WSL root host")
    result = run(screen._load(args.manifest), screen._load(args.notice), args.out)
    print(json.dumps({key: result[key] for key in
                      ("requested_cell", "actual_model", "served_identity_valid",
                       "terminal", "cost_usd", "public_check_passed")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
