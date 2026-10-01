#!/usr/bin/env python3
"""Freeze six independent Q3 public B0 tasks behind a dated exact manifest."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import model_registry
import route
import worker_q3_canary as canary
from worker_adapter import digest
from worker_q3_public_catalogue import FIXTURES, ROOT, build, sha
from worker_q3_public_source import verify as verify_upstream

TASKS = tuple(f"P{number:02d}" for number in range(3, 9))
NOTICE = ROOT / "docs/stage-results/worker-q3-expansion-spend-notice-2026-09-25.md"
MANIFEST = ROOT / "test/results/2026-09-25-worker-q3-expansion-manifest.json"
APPROVAL = ROOT / "test/results/2026-09-25-worker-q3-expansion-approval.json"
CANARY = ROOT / "test/results/2026-09-25-worker-q3-canary-evidence.json"
ATTACKS = ROOT / "test/results/2026-09-25-worker-q3-public-attacks.json"
TRANSPORT = ROOT / "test/results/2026-09-25-worker-q3-expansion-transport.json"
SOURCES = tuple(dict.fromkeys((*canary.q3.SOURCE_FILES, *canary.EXTRA_SOURCES,
    "tools/worker_q3_expansion.py", "tools/worker_q3_expansion_live.py",
    "tools/worker_q3_public_catalogue.py", "tools/worker_q3_public_source.py",
    "tools/worker_q3_public_calibrate.py",
    "tools/worker_wsl_q3_public.py", "tools/worker_wsl_q3_public_probe.py",
    "tools/worker_wsl_q3_expansion_probe.py",
    "test/harness/worker_q3_public_tests.py")))
HEX = re.compile(r"[0-9a-f]{64}\Z")
ALLOCATION = 6.0
MAX_CALLS = 18


class ExpansionError(RuntimeError):
    """The public campaign cannot be admitted under current evidence."""


def prior_canary() -> str:
    row = json.loads(CANARY.read_text(encoding="utf-8"))
    if (row.get("state_sha256") != digest({key: value for key, value in row.items()
                                            if key != "state_sha256"})
            or row.get("status") != "complete"
            or [(item.get("task_id"), item.get("state")) for item in row.get("rows", [])]
            != [("P01", "graded"), ("P02", "graded")]):
        raise ExpansionError("P01/P02 B0 canary evidence is invalid")
    return sha(CANARY)


def transport_evidence() -> str:
    row = json.loads(TRANSPORT.read_text(encoding="utf-8"))
    p03 = build("P03")
    expected_checks = {"fake_provider_only", "model_identity", "writer_stopped",
                       "four_edits_collected", "protected_unchanged",
                       "four_source_edits_visible", "q1_receipt_bound"}
    if (row.get("result") != "PASS"
            or set(row.get("checks", {})) != expected_checks
            or not all(row["checks"].values())
            or row.get("provider_calls") != 0 or row.get("provider_cost_usd") != 0
            or row.get("task_sha256") != p03["task_sha256"]
            or row.get("source_sha256") != {name: sha(ROOT / name) for name in (
                "tools/worker_wsl_q3_expansion_probe.py",
                "tools/worker_wsl_q3_adapter.py")}
            or row.get("evidence_sha256") != digest({key: value for key, value in row.items()
                                                     if key != "evidence_sha256"})):
        raise ExpansionError("four-file transport evidence is invalid or stale")
    return sha(TRANSPORT)


def public_rows() -> list[dict]:
    attack = json.loads(ATTACKS.read_text(encoding="utf-8"))
    expected_attacks = {"false_completion_detected", "protected_issue_edit_rejected",
                        "public_answer_edit_rejected", "editable_symlink_rejected",
                        "editable_hardlink_rejected", "public_pass_hidden_fail_detected"}
    if (attack.get("result") != "PASS"
            or set(attack.get("checks", {})) != expected_attacks
            or not all(attack["checks"].values())
            or attack.get("evidence_sha256") != digest({key: value for key, value in attack.items()
                                                        if key != "evidence_sha256"})
            or attack.get("source_sha256") != {name: sha(ROOT / name)
                for name in ("tools/worker_wsl_q3_public_probe.py",
                             "tools/worker_wsl_q3_public.py",
                             "tools/worker_q3_public_catalogue.py")}):
        raise ExpansionError("public attack evidence is stale or incomplete")
    rows = []
    seen = set()
    for sequence, task_id in enumerate(TASKS, 1):
        task = build(task_id)
        frozen = json.loads((FIXTURES / task_id / "task.json").read_text(encoding="utf-8"))
        if task != frozen or task["source_url"] in seen:
            raise ExpansionError(f"{task_id} frozen source or project independence changed")
        seen.add(task["source_url"])
        origin = verify_upstream(task_id)
        if origin["source_commit"] != task["source_commit"]:
            raise ExpansionError(f"{task_id} upstream source differs")
        calibration_files = list((ROOT / "test/results").glob(
            f"*-worker-q3-{task_id.lower()}-{task['task_sha256'][:12]}-calibration.json"))
        if len(calibration_files) != 1:
            raise ExpansionError(f"{task_id} passing calibration is missing or ambiguous")
        calibration = json.loads(calibration_files[0].read_text(encoding="utf-8"))
        if (calibration.get("result") != "PASS"
                or calibration.get("task_sha256") != task["task_sha256"]
                or not all(calibration.get("checks", {}).values())
                or calibration.get("source_sha256") != {name: sha(ROOT / name)
                    for name in ("tools/worker_q3_public_calibrate.py",
                                 "tools/worker_wsl_q3_public.py",
                                 "tools/worker_q3_public_catalogue.py",
                                 "tools/worker_wsl_q2_verify.py")}
                or calibration.get("evidence_sha256") != digest({
                    key: value for key, value in calibration.items()
                    if key != "evidence_sha256"})):
            raise ExpansionError(f"{task_id} calibration is invalid")
        rows.append({"sequence": sequence, "task_id": task_id,
                     "task_sha256": task["task_sha256"],
                     "actor_files": task["actor_files"],
                     "editable_paths": task["editable_paths"],
                     "oracle_sha256": task["oracle_sha256"],
                     "case_source_sha256": task["case_source_sha256"],
                     "calibration_sha256": sha(calibration_files[0]),
                     "ladder": canary.LADDER,
                     "episode_maximum_usd": ALLOCATION})
    return rows


def build_manifest(date_utc: str, notice_sha256: str) -> dict:
    if (dt.date.fromisoformat(date_utc) != dt.datetime.now(dt.timezone.utc).date()
            or not HEX.fullmatch(notice_sha256)):
        raise ExpansionError("manifest needs today's UTC date and dated notice digest")
    evidence = canary.current_evidence()
    if (route.plan("structured", "medium", "contained")["execution_ladder"]
            != canary.LADDER
            or [model_registry.model_class_for_provider_id(
                    model_registry.resolve_cell(cell)["cli_model"])
                for cell in ("worker-sonnet-low", "worker-opus-high")]
            != ["sonnet", "opus"]):
        raise ExpansionError("B0 ladder or pinned model identities changed")
    value = {"schema_version": 1, "profile": "worker-q3-six-family-b0-expansion",
             "date_utc": date_utc,
             "credential_method": "claude-code-wsl-subscription",
             "evidence_sha256": evidence,
             "spend_notice_sha256": notice_sha256,
             "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
             "canary_sha256": prior_canary(), "attacks_sha256": sha(ATTACKS),
             "transport_sha256": transport_evidence(),
             "registry_id": model_registry.load()["registry_id"],
             "q3_uncertain_evidence_sha256": canary.uncertain_evidence(),
             "rows": public_rows(),
             "cost": {"currency": "USD", "episode_allocation_usd": ALLOCATION,
                      "combined_allocation_usd": len(TASKS) * ALLOCATION,
                      "maximum_provider_calls": MAX_CALLS,
                      "api_equivalent_projection_usd": [0.5, 16.0]},
             "stop_rules": ["Stop on uncertain or excess charge",
                            "Stop on stale host, auth, sentinel or source evidence",
                            "Stop on identity mismatch or protected-file drift",
                            "No automatic replay of a started invocation"],
             "reserved_tasks_allowed": False, "controller_allowed": False,
             "candidate_route_allowed": False,
             "authorisation": "operator-standing-through-Q4-2026-09-25"}
    return {**value, "manifest_sha256": digest(value)}


def validate(manifest: dict) -> None:
    if NOTICE.is_symlink() or sha(NOTICE) != manifest.get("spend_notice_sha256"):
        raise ExpansionError("dated spend notice differs from frozen manifest")
    if manifest != build_manifest(manifest["date_utc"], sha(NOTICE)):
        raise ExpansionError("Q3 expansion manifest differs from current inputs")


def validate_approval(manifest: dict, approval: dict) -> None:
    expected = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": manifest["manifest_sha256"],
                "maximum_authorised_usd": len(TASKS) * ALLOCATION,
                "maximum_provider_calls": MAX_CALLS,
                "spend_notice_sha256": manifest["spend_notice_sha256"],
                "credential_method": manifest["credential_method"],
                "approved_by": "operator-standing-through-Q4-2026-09-25"}
    if (not isinstance(approval, dict)
            or {key: approval.get(key) for key in expected} != expected
            or set(approval) != set(expected) | {"approved_at"}
            or not isinstance(approval["approved_at"], str)
            or not approval["approved_at"].strip()):
        raise ExpansionError("approval is not bound to this exact Q3 campaign")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.prepare == args.check:
            parser.error("choose --prepare or --check")
        if args.prepare:
            if NOTICE.is_symlink() or not NOTICE.is_file() or MANIFEST.exists():
                raise ExpansionError("dated notice missing or manifest already exists")
            value = build_manifest(dt.datetime.now(dt.timezone.utc).date().isoformat(),
                                   sha(NOTICE))
            MANIFEST.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8", newline="\n")
        else:
            value = json.loads(MANIFEST.read_text(encoding="utf-8"))
            validate(value)
            validate_approval(value, json.loads(APPROVAL.read_text(encoding="utf-8")))
        print(f"PASS: Q3 six-family manifest {value['manifest_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ExpansionError) as exc:
        print(f"BLOCKED: Q3 expansion manifest: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
