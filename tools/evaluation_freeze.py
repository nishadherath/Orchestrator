#!/usr/bin/env python3
"""Create or verify a content-addressed real-world evaluation candidate."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "docs" / "REAL-WORLD-EVALUATION-FREEZE-2026-09-17.json"
CATALOGUE = ROOT / "test" / "fixtures" / "realworld" / "catalogue.json"
PRICE = ROOT / "test" / "fixtures" / "realworld" / "price-snapshot-2026-09-17.json"
POLICIES = ROOT / "test" / "fixtures" / "realworld" / "policies"
ISOLATION = ROOT / "test" / "results" / "2026-09-17-realworld-isolation.json"
RUNNER = ROOT / "tools" / "evaluation_runner.py"
RUNNER_EVIDENCE = ROOT / "test" / "results" / "2026-09-17-realworld-runner.json"
RUNNER_REPORT = ROOT / "test" / "results" / "2026-09-17-realworld-runner.md"
CALIBRATION = ROOT / "tools" / "live_calibration.py"
CALIBRATION_TESTS = ROOT / "test" / "harness" / "live_calibration_tests.py"
CALIBRATION_EVIDENCE = ROOT / "test" / "results" / "2026-09-17-live-calibration.json"
ADJUDICATION = ROOT / "tools" / "live_calibration_adjudication.py"
ADJUDICATION_TESTS = ROOT / "test" / "harness" / "live_calibration_adjudication_tests.py"
ADJUDICATION_EVIDENCE = (
    ROOT / "test" / "results" / "2026-09-17-live-calibration-adjudication.json"
)
LIVE_ADAPTER = ROOT / "tools" / "evaluation_live_worker.py"
LIVE_ADAPTER_TESTS = ROOT / "test" / "harness" / "evaluation_live_worker_tests.py"
LIVE_ADAPTER_EVIDENCE = ROOT / "test" / "results" / "2026-09-17-live-worker-adapter.json"
LIVE_ADAPTER_REPORT = ROOT / "test" / "results" / "2026-09-17-live-worker-adapter.md"
LIVE_EPISODE = ROOT / "tools" / "evaluation_live_episode.py"
LIVE_EPISODE_TESTS = ROOT / "test" / "harness" / "evaluation_live_episode_tests.py"
LIVE_EPISODE_EVIDENCE = ROOT / "test" / "results" / "2026-09-17-live-episode-integration.json"
LIVE_EPISODE_REPORT = ROOT / "test" / "results" / "2026-09-17-live-episode-integration.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def bound_files() -> list[Path]:
    fixed = [
        ROOT / "dist" / "bundle-manifest.json",
        CATALOGUE,
        PRICE,
        ROOT / "src" / "acceptance-contract.example.json",
        ROOT / "src" / "System" / "schemas" / "RoutingLedgerEntry.schema.json",
        ROOT / "src" / "System" / "schemas" / "BudgetEntry.schema.json",
        ROOT / "tools" / "acceptance.py",
        ROOT / "tools" / "dispatch_budget.py",
        ROOT / "tools" / "evaluation_freeze.py",
        ROOT / "tools" / "realworld_isolation.py",
        ROOT / "test" / "harness" / "realworld.py",
        ROOT / "test" / "harness" / "realworld_tests.py",
        ISOLATION,
    ]
    fixture_files = [path for path in (ROOT / "test" / "fixtures" / "realworld").rglob("*") if path.is_file()]
    oracle_files = [path for path in (ROOT / "test" / "oracles" / "realworld").rglob("*") if path.is_file()]
    runner_files = [path for path in (RUNNER, RUNNER_EVIDENCE, RUNNER_REPORT) if path.is_file()]
    calibration_files = [path for path in (
        CALIBRATION, CALIBRATION_TESTS, CALIBRATION_EVIDENCE,
        ADJUDICATION, ADJUDICATION_TESTS, ADJUDICATION_EVIDENCE,
        LIVE_ADAPTER, LIVE_ADAPTER_TESTS, LIVE_ADAPTER_EVIDENCE, LIVE_ADAPTER_REPORT,
        LIVE_EPISODE, LIVE_EPISODE_TESTS, LIVE_EPISODE_EVIDENCE, LIVE_EPISODE_REPORT,
    ) if path.is_file()]
    return sorted(set(fixed + fixture_files + oracle_files + runner_files + calibration_files))


def valid_evidence(path: Path) -> tuple[bool, str | None, dict]:
    if not path.is_file():
        return False, None, {}
    value = json.loads(path.read_text(encoding="utf-8"))
    digest = value.pop("evidence_sha256", None)
    valid = digest == hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest() and value.get("result") == "PASS"
    return valid, digest, value


def valid_runner_evidence(path: Path) -> tuple[bool, str | None, dict]:
    valid, evidence_digest, value = valid_evidence(path)
    replay = value.get("replay") or {}
    report = value.get("report") or {}
    valid = bool(
        valid and RUNNER.is_file()
        and value.get("mode") == "offline-fake-worker-v1"
        and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(RUNNER)
        and value.get("policies") == ["B0", "B1", "B2"]
        and value.get("scenario_count") == 9
        and replay.get("deterministic") is True
        and replay.get("event_chains_valid") is True
        and replay.get("one_dispatch_per_episode") is True
        and RUNNER_REPORT.is_file()
        and report.get("path") == RUNNER_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(RUNNER_REPORT)
    )
    return valid, evidence_digest, value


def valid_calibration_evidence() -> tuple[bool, str | None, dict]:
    """Validate the PASS adjudication and its bound first-run evidence."""
    valid, evidence_digest, value = valid_evidence(ADJUDICATION_EVIDENCE)
    checks = value.get("checks") or {}
    attribution = value.get("attribution") or {}
    original = value.get("original") or {}
    expected_checks = (
        "original_evidence_valid", "terminal_result", "one_worker_completed",
        "root_model_attributed", "worker_model_attributed",
        "billing_telemetry_present", "stream_well_formed",
    )
    valid = bool(
        valid and ADJUDICATION.is_file() and CALIBRATION_EVIDENCE.is_file()
        and value.get("implementation_sha256") == sha256(ADJUDICATION)
        and original.get("file_sha256") == sha256(CALIBRATION_EVIDENCE)
        and attribution.get("root_models") == ["claude-sonnet-5"]
        and attribution.get("worker_models") == ["claude-sonnet-5"]
        and all(checks.get(name) is True for name in expected_checks)
    )
    return valid, evidence_digest, value


def valid_live_adapter_evidence() -> tuple[bool, str | None, dict]:
    valid, evidence_digest, value = valid_evidence(LIVE_ADAPTER_EVIDENCE)
    checks = value.get("checks") or {}
    calibration = value.get("calibration") or {}
    report = value.get("report") or {}
    valid = bool(
        valid and LIVE_ADAPTER.is_file() and LIVE_ADAPTER_REPORT.is_file()
        and value.get("mode") == "offline-fake-transport-v1"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(LIVE_ADAPTER)
        and calibration.get("file_sha256") == sha256(ADJUDICATION_EVIDENCE)
        and calibration.get("original_file_sha256") == sha256(CALIBRATION_EVIDENCE)
        and report.get("path") == LIVE_ADAPTER_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(LIVE_ADAPTER_REPORT)
        and len(checks) == 7 and all(checks.values())
    )
    return valid, evidence_digest, value


def valid_live_episode_evidence() -> tuple[bool, str | None, dict]:
    valid, evidence_digest, value = valid_evidence(LIVE_EPISODE_EVIDENCE)
    checks = value.get("checks") or {}
    report = value.get("report") or {}
    cases = value.get("cases") or {}
    valid = bool(
        valid and LIVE_EPISODE.is_file() and LIVE_EPISODE_REPORT.is_file()
        and value.get("mode") == "offline-scripted-adapters-v1"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(LIVE_EPISODE)
        and report.get("path") == LIVE_EPISODE_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(LIVE_EPISODE_REPORT)
        and len(checks) == 8 and all(checks.values())
        and set(cases) == {"b0-repair", "b1-ladder", "b2-controller",
                           "crash_recovery", "missing_cost"}
    )
    return valid, evidence_digest, value


def candidate() -> dict:
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    ready = sorted(task["id"] for task in catalogue["tasks"] if task.get("readiness") == "ready")
    remaining = sorted(set(catalogue["pilot_ids"]) - set(ready))
    files = {path.relative_to(ROOT).as_posix(): sha256(path) for path in bound_files()}
    candidate_digest = hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    manifest = json.loads((ROOT / "dist" / "bundle-manifest.json").read_text(encoding="utf-8"))
    dirty = git("status", "--porcelain") not in ("", "unknown")
    isolation_valid, isolation_digest, isolation = valid_evidence(ISOLATION)
    runner_valid, runner_digest, runner = valid_runner_evidence(RUNNER_EVIDENCE)
    calibration_valid, calibration_digest, calibration = valid_calibration_evidence()
    adapter_valid, adapter_digest, adapter = valid_live_adapter_evidence()
    episode_valid, episode_digest, episode = valid_live_episode_evidence()
    blockers = []
    if remaining:
        blockers.append(f"pilot fixtures not ready: {', '.join(remaining)}")
    if dirty:
        blockers.append("candidate source tree is dirty")
    if manifest.get("licence", {}).get("status") != "present":
        blockers.append("project licence remains an operator decision")
    if not isolation_valid:
        blockers.append("actor/evaluator access-control evidence is missing or invalid")
    if not runner_valid:
        blockers.append("offline episode runner and replay evidence are missing or invalid")
    if not calibration_valid:
        blockers.append("live Claude CLI calibration has not confirmed served model IDs and billing roll-up")
    if not adapter_valid:
        blockers.append("live episode worker adapter and offline qualification evidence are missing")
    if not episode_valid:
        blockers.append("live policy executor and restart-safe episode integration are missing or invalid")
    blockers.append("live Controller escalation adapter is missing")
    blockers.append("paid pilot has not been authorised")
    return {
        "schema_version": 1,
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "campaign": catalogue["campaign"],
        "candidate_sha256": candidate_digest,
        "source_revision": git("rev-parse", "HEAD"),
        "source_dirty": dirty,
        "bundle": {
            "version": manifest.get("bundle_version"),
            "manifest_sha256": files["dist/bundle-manifest.json"],
            "payload_files": len(manifest.get("files", {})),
        },
        "models": {
            "requested_cells": ["worker-sonnet-low", "worker-opus-high"],
            "required_actual_ids": ["claude-sonnet-5", "claude-opus-5"],
            "frontier_not_in_pilot": "claude-fable-5-1",
            "identity_rule": "price and compare the actual served model; an alias alone is insufficient",
        },
        "contracts": {
            "acceptance": "acceptance-v2",
            "routing_ledger_schema": 2,
            "budget_ledger_schema": 1,
            "episode_budget_usd": 4.0,
            "active_model_timeout_seconds": 900,
            "external_grader_timeout_seconds": 120,
        },
        "isolation": {
            "boundary": isolation.get("boundary"),
            "evidence_sha256": isolation_digest,
            "valid": isolation_valid,
        },
        "episode_runner": {
            "implementation": RUNNER.relative_to(ROOT).as_posix(),
            "evidence": RUNNER_EVIDENCE.relative_to(ROOT).as_posix(),
            "evidence_sha256": runner_digest,
            "valid": runner_valid,
            "mode": runner.get("mode"),
        },
        "live_calibration": {
            "evidence": ADJUDICATION_EVIDENCE.relative_to(ROOT).as_posix(),
            "evidence_sha256": calibration_digest,
            "valid": calibration_valid,
            "root_models": (calibration.get("attribution") or {}).get("root_models"),
            "worker_models": (calibration.get("attribution") or {}).get("worker_models"),
            "billed_models": (calibration.get("attribution") or {}).get("billed_models"),
            "api_equivalent_cost_usd": (calibration.get("call") or {}).get("cost_usd"),
        },
        "live_episode_execution": {
            "adapter_implemented": LIVE_ADAPTER.is_file(),
            "adapter_qualified": adapter_valid,
            "adapter_evidence": LIVE_ADAPTER_EVIDENCE.relative_to(ROOT).as_posix(),
            "adapter_evidence_sha256": adapter_digest,
            "adapter_mode": adapter.get("mode"),
            "policy_executor_implemented": LIVE_EPISODE.is_file(),
            "restart_safe_integration_qualified": episode_valid,
            "integration_evidence": LIVE_EPISODE_EVIDENCE.relative_to(ROOT).as_posix(),
            "integration_evidence_sha256": episode_digest,
            "integration_mode": episode.get("mode"),
            "controller_adapter_implemented": False,
            "note": "Worker sequencing and at-most-once recovery qualify offline; live Controller execution remains open.",
        },
        "policies": {path.stem: files[path.relative_to(ROOT).as_posix()] for path in sorted(POLICIES.glob("*.json"))},
        "prices": json.loads(PRICE.read_text(encoding="utf-8")),
        "pilot": {
            "planned_tasks": catalogue["pilot_ids"],
            "ready_tasks": ready,
            "remaining_tasks": remaining,
            "planned_episodes": 24,
            "allocation_usd": 100.0,
        },
        "bound_files": files,
        "paid_launch_ready": not blockers,
        "blockers": blockers,
    }


def stable(value: dict) -> dict:
    return {key: item for key, item in value.items() if key != "created_at"}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    value = candidate()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        if not output.is_file():
            print(f"FAIL: freeze missing: {output}")
            return 1
        recorded = json.loads(output.read_text(encoding="utf-8"))
        ok = stable(recorded) == stable(value)
        print(("PASS" if ok else "FAIL") + f": evaluation freeze {value['candidate_sha256']}")
        return 0 if ok else 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if args.json:
        print(json.dumps(value, indent=2))
    else:
        print(f"wrote {output.relative_to(ROOT)}")
        print(f"candidate {value['candidate_sha256']}; paid_launch_ready={value['paid_launch_ready']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
