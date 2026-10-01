#!/usr/bin/env python3
"""Exact-approval, at-most-once gate for Q3's paid Read-denial sentinel."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import route
import worker_wsl_q3_attestation as q3
import worker_wsl_subscription_attestation as auth
import worker_wsl_subscription_sentinel as sentinel
from worker_adapter import digest

ROOT = Path(__file__).resolve().parent.parent
NOTICE = ROOT / "docs/stage-results/worker-q3-sentinel-spend-notice-2026-09-25.md"
MANIFEST = ROOT / "test/results/2026-09-25-worker-q3-sentinel-manifest.json"
REQUEST = ROOT / "test/results/2026-09-25-worker-q3-sentinel-approval-request.json"
APPROVAL = ROOT / "test/results/2026-09-25-worker-q3-sentinel-approval.json"
INTENT = ROOT / "test/results/2026-09-25-worker-q3-sentinel-intent.json"
OUTPUT = ROOT / "test/results/2026-09-25-worker-q3-subscription-sentinel.json"


class SentinelGateError(RuntimeError):
    """The sentinel cannot be dispatched under a current exact approval."""


def sha(path: Path) -> str:
    return q3.sha(path)


def current() -> dict:
    host = json.loads(q3.OUTPUT.read_text(encoding="utf-8"))
    subscription = json.loads(auth.OUTPUT.read_text(encoding="utf-8"))
    if not q3.validate(host, check_host=True, require_auth=True):
        raise SentinelGateError("Q3 isolated WSL host/auth evidence is stale")
    if not auth.validate(subscription, check_host=True):
        raise SentinelGateError("N5 subscription evidence is stale")
    return {"q3_host": host["evidence_sha256"],
            "n4_host": host["predecessor_evidence_sha256"]["n4"],
            "subscription": subscription["evidence_sha256"]}


def build(evidence: dict, date_utc: str) -> dict:
    if evidence != current():
        raise SentinelGateError("host evidence changed during freeze")
    if date_utc != dt.datetime.now(dt.timezone.utc).date().isoformat():
        raise SentinelGateError("dated notice must be approved today in UTC")
    value = {"schema_version": 1, "profile": "worker-q3-read-denial-sentinel",
             "date_utc": date_utc,
             "evidence_sha256": evidence,
             "notice_sha256": sha(NOTICE),
             "source_sha256": {
                 "tools/worker_q3_sentinel_gate.py": sha(Path(__file__)),
                 "tools/worker_wsl_subscription_sentinel.py": sha(
                     ROOT / "tools/worker_wsl_subscription_sentinel.py"),
                 "tools/worker_wsl_transport.py": sha(
                     ROOT / "tools/worker_wsl_transport.py"),
                 "src/model_registry.json": sha(ROOT / "src/model_registry.json")},
             "requested_cell": "worker-sonnet-low", "requested_effort": "low",
             "target": sentinel.TARGET, "credential_method": "claude-code-wsl-subscription",
             "maximum_provider_calls": 1, "local_allocation_usd": 0.10,
             "api_equivalent_projection_usd": [0.03, 0.15],
             "retry_policy": "no-automatic-provider-replay",
             "authorisation": "separate-exact-approval-required"}
    return {**value, "manifest_sha256": digest(value)}


def approved(manifest: dict) -> None:
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    if (set(approval) != {"schema_version", "decision", "manifest_sha256",
                          "maximum_authorised_usd", "credential_method",
                          "notice_sha256", "approved_by", "approved_at"}
            or approval["schema_version"] != 1
            or approval["decision"] != "approved"
            or approval["manifest_sha256"] != manifest["manifest_sha256"]
            or approval["maximum_authorised_usd"] != 0.10
            or approval["credential_method"] != manifest["credential_method"]
            or approval["notice_sha256"] != manifest["notice_sha256"]
            or not isinstance(approval["approved_by"], str)
            or not approval["approved_by"].strip()
            or not isinstance(approval["approved_at"], str)
            or not approval["approved_at"].strip()):
        raise SentinelGateError("sentinel approval does not match exact manifest")


def prepare() -> dict:
    value = build(current(), dt.datetime.now(dt.timezone.utc).date().isoformat())
    MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    request = {"schema_version": 1, "decision": "approval-requested",
               "manifest_sha256": value["manifest_sha256"],
               "notice_sha256": value["notice_sha256"],
               "maximum_authorised_usd": 0.10,
               "maximum_provider_calls": 1,
               "credential_method": value["credential_method"]}
    REQUEST.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8", newline="\n")
    return value


def check(*, require_approval: bool) -> dict:
    value = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if value != build(value["evidence_sha256"], value["date_utc"]):
        raise SentinelGateError("sentinel manifest differs from current host or source")
    if require_approval:
        approved(value)
    return value


def run() -> dict:
    manifest = check(require_approval=True)
    with route.ledger_lock(INTENT):
        if INTENT.exists() or OUTPUT.exists():
            raise SentinelGateError("prior sentinel intent or output exists; no replay")
        intent = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
                  "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                  "state": "provider-call-may-have-started"}
        route._atomic_write_bytes(INTENT, (json.dumps(intent, sort_keys=True) + "\n").encode())
    result = sentinel.run()
    # The underlying N5 sentinel seals its own body. Preserve it exactly and
    # bind the Q3 manifest in a separate wrapper record instead.
    route._atomic_write_bytes(OUTPUT, (json.dumps(result, indent=2, sort_keys=True)
                                       + "\n").encode())
    if not sentinel.validate(result, check_host=True):
        raise SentinelGateError("sentinel result failed; intent retained, no replay")
    receipt = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
               "sentinel_evidence_sha256": result["evidence_sha256"],
               "reported_api_equivalent_cost_usd": result[
                   "reported_api_equivalent_cost_usd"], "result": "PASS"}
    route._atomic_write_bytes(OUTPUT.with_suffix(".receipt.json"),
                              (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--run", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare:
            value = prepare()
            print(f"PASS: exact sentinel approval requested for {value['manifest_sha256']}")
        elif args.check:
            check(require_approval=False)
            print("PASS: sentinel manifest and host preflight current")
        else:
            receipt = run()
            print(f"PASS: sentinel API-equivalent USD "
                  f"{receipt['reported_api_equivalent_cost_usd']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(f"BLOCKED: Q3 sentinel gate: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
