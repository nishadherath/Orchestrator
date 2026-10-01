#!/usr/bin/env python3
"""Freeze and validate the exact two-task Q3 B0 canary admission manifest.

This module has no paid dispatch path. A blocked auth or stale sentinel keeps
the manifest in draft state; it cannot be approved by changing JSON by hand.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import model_registry
import route
import worker_q3_sentinel_gate as sentinel_gate
import worker_q2_public as q2
import worker_wsl_q3_attestation as q3
import worker_wsl_subscription_attestation as subscription
import worker_wsl_subscription_sentinel as sentinel
from worker_adapter import digest

ROOT = Path(__file__).resolve().parent.parent
CATALOGUE = ROOT / "test/fixtures/worker_q2_public/catalogue.json"
Q2_EVIDENCE = ROOT / "test/results/2026-09-25-worker-q2-public.json"
UNCERTAIN_EVIDENCE = ROOT / "test/results/2026-09-25-worker-q3-uncertain.json"
OUTPUT = ROOT / "test/results/2026-09-25-worker-q3-canary-manifest.json"
APPROVAL_REQUEST = ROOT / "test/results/2026-09-25-worker-q3-canary-approval-request.json"
LADDER = ["worker-sonnet-low", "worker-sonnet-low", "worker-opus-high"]
HEX = re.compile(r"[0-9a-f]{64}\Z")
EXTRA_SOURCES = (
    "tools/worker_q3_canary.py", "tools/worker_q3_live.py",
    "tools/worker_q3_sentinel_gate.py", "tools/worker_adapter.py",
    "tools/worker_wsl_q3_uncertain_probe.py",
    "tools/task_executor.py", "tools/acceptance.py", "tools/dispatch_budget.py",
    "tools/worker_wsl_q1.py", "tools/worker_wsl_q2_verify.py",
    "src/model_registry.json",
)


class CanaryError(RuntimeError):
    """The frozen Q3 admission contract cannot be established."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_evidence() -> dict[str, str]:
    try:
        host = json.loads(q3.OUTPUT.read_text(encoding="utf-8"))
        auth = json.loads(subscription.OUTPUT.read_text(encoding="utf-8"))
        read_sentinel = json.loads(sentinel_gate.OUTPUT.read_text(encoding="utf-8"))
        sentinel_receipt = json.loads(sentinel_gate.OUTPUT.with_suffix(
            ".receipt.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CanaryError("Q3 host, subscription or Read sentinel evidence is missing") from exc
    if not q3.validate(host, check_host=True, require_auth=True):
        raise CanaryError("Q3 WSL host or isolated login is stale")
    if not subscription.validate(auth, check_host=True):
        raise CanaryError("N5 subscription evidence is stale")
    if not sentinel.validate(read_sentinel, check_host=True):
        raise CanaryError("subscription Read-denial sentinel is stale")
    sentinel_manifest = sentinel_gate.check(require_approval=True)
    if (sentinel_receipt.get("result") != "PASS"
            or sentinel_receipt.get("manifest_sha256") != sentinel_manifest["manifest_sha256"]
            or sentinel_receipt.get("sentinel_evidence_sha256")
            != read_sentinel["evidence_sha256"]
            or sentinel_receipt.get("reported_api_equivalent_cost_usd")
            != read_sentinel["reported_api_equivalent_cost_usd"]):
        raise CanaryError("Q3 sentinel receipt does not bind current approved preflight")
    if (host["predecessor_evidence_sha256"]["n4"]
            != read_sentinel["host_attestation_sha256"]):
        raise CanaryError("Read sentinel belongs to a different N4 host")
    return {"q3_host": host["evidence_sha256"],
            "subscription": auth["evidence_sha256"],
            "read_sentinel": read_sentinel["evidence_sha256"]}


def _public() -> tuple[dict, dict]:
    q2.check_catalogue()
    q2.check_evidence()
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if [task["id"] for task in catalogue["tasks"]] != ["P01", "P02"]:
        raise CanaryError("Q2 public task order or count changed")
    rows = []
    for sequence, task in enumerate(catalogue["tasks"], 1):
        source = ROOT / "test/fixtures/worker_q2_public" / task["id"] / "actor"
        if (source.is_symlink() or not source.is_dir()
                or {p.relative_to(source).as_posix(): sha(p)
                    for p in source.rglob("*") if p.is_file()} != task["actor_files"]):
            raise CanaryError("public actor inventory differs from catalogue")
        oracle = ROOT / "test/oracles/worker_q2_public" / f"{task['id']}.json"
        if sha(oracle) != task["oracle_sha256"]:
            raise CanaryError("protected hidden oracle differs from catalogue")
        rows.append({"sequence": sequence, "task_id": task["id"],
                     "actor_files": task["actor_files"],
                     "editable_paths": task["editable_paths"],
                     "oracle_sha256": task["oracle_sha256"],
                     "ladder": LADDER, "episode_maximum_usd": 6.0})
    return catalogue, rows


def uncertain_evidence() -> str:
    value = json.loads(UNCERTAIN_EVIDENCE.read_text(encoding="utf-8"))
    body = {key: item for key, item in value.items() if key != "evidence_sha256"}
    expected = {"actor_retained_for_reconciliation", "first_attempt_uncertain",
                "no_replay_on_second_run", "no_terminal_receipt",
                "public_source_unchanged", "unknown_charge_held",
                "zero_provider_call"}
    if (value.get("schema_version") != 1 or value.get("result") != "PASS"
            or value.get("provider_calls") != 0 or value.get("provider_cost_usd") != 0
            or set(value.get("checks", {})) != expected
            or not all(value["checks"].values())
            or value.get("source_sha256") != sha(
                ROOT / "tools/worker_wsl_q3_uncertain_probe.py")
            or value.get("evidence_sha256") != hashlib.sha256(json.dumps(
                body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()):
        raise CanaryError("Q3 timeout/no-replay evidence is invalid or stale")
    return value["evidence_sha256"]


def build_manifest(*, spend_notice_sha256: str, date_utc: str,
                   evidence: dict[str, str]) -> dict:
    if not HEX.fullmatch(spend_notice_sha256):
        raise CanaryError("dated spend notice digest is required")
    if dt.date.fromisoformat(date_utc) != dt.datetime.now(dt.timezone.utc).date():
        raise CanaryError("spend notice and manifest must be frozen today in UTC")
    if evidence != current_evidence():
        raise CanaryError("host evidence changed during manifest preparation")
    catalogue, rows = _public()
    registry = model_registry.load()
    if (route.plan("structured", "medium", "contained")["execution_ladder"] != LADDER
            or [model_registry.resolve_cell(cell)["cli_model"] for cell in
                ("worker-sonnet-low", "worker-opus-high")]
            != ["claude-sonnet-5", "claude-opus-5"]):
        raise CanaryError("B0 ladder or pinned provider identities changed")
    value = {
        "schema_version": 1, "profile": "worker-q3-b0-two-task-canary",
        "date_utc": date_utc, "credential_method": "claude-code-wsl-subscription",
        "evidence_sha256": evidence, "spend_notice_sha256": spend_notice_sha256,
        "source_sha256": {name: sha(ROOT / name) for name in
                          (*q3.SOURCE_FILES, *EXTRA_SOURCES)},
        "catalogue_sha256": sha(CATALOGUE), "q2_evidence_sha256": sha(Q2_EVIDENCE),
        "q3_uncertain_evidence_sha256": uncertain_evidence(),
        "registry_id": registry["registry_id"],
        "rows": rows,
        "cost": {"currency": "USD", "episode_allocation_usd": 6.0,
                 "combined_allocation_usd": 12.0,
                 "maximum_provider_calls": 6,
                 "api_equivalent_projection_usd": [0.1, 6.0]},
        "stop_rules": ["Stop on uncertain or excess charge",
                       "Stop on stale host, auth, sentinel or source evidence",
                       "Stop on identity mismatch or protected-file drift",
                       "No automatic replay of a started invocation"],
        "reserved_tasks_allowed": False, "controller_allowed": False,
        "candidate_route_allowed": False,
        "authorisation": "separate-exact-approval-required",
        "catalogue_purpose": catalogue["purpose"],
    }
    return {**value, "manifest_sha256": digest(value)}


def validate(manifest: dict, *, notice: Path) -> None:
    if sha(notice) != manifest.get("spend_notice_sha256"):
        raise CanaryError("spend notice differs from frozen manifest")
    expected = build_manifest(spend_notice_sha256=sha(notice),
                              date_utc=manifest["date_utc"],
                              evidence=manifest["evidence_sha256"])
    if manifest != expected:
        raise CanaryError("Q3 manifest differs from current frozen inputs")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spend-notice", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            value = json.loads(OUTPUT.read_text(encoding="utf-8"))
            validate(value, notice=args.spend_notice)
            print("PASS: Q3 manifest and live preflight remain current")
            return 0
        if args.spend_notice.is_symlink() or not args.spend_notice.is_file():
            raise CanaryError("dated spend notice is missing or redirected")
        value = build_manifest(
            spend_notice_sha256=sha(args.spend_notice),
            date_utc=dt.datetime.now(dt.timezone.utc).date().isoformat(),
            evidence=current_evidence())
        OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")
        request = {"schema_version": 1, "decision": "approval-requested",
                   "manifest_sha256": value["manifest_sha256"],
                   "spend_notice_sha256": value["spend_notice_sha256"],
                   "maximum_authorised_usd": 12.0,
                   "maximum_provider_calls": 6,
                   "credential_method": value["credential_method"],
                   "approval_record_required": True}
        APPROVAL_REQUEST.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8", newline="\n")
        print(f"PASS: Q3 exact approval requested for manifest {value['manifest_sha256']}")
        return 0
    except (CanaryError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"BLOCKED: Q3 manifest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
