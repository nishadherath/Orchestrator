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
LIVE_CONTROLLER = ROOT / "tools" / "evaluation_live_controller.py"
LIVE_CONTROLLER_TESTS = ROOT / "test" / "harness" / "evaluation_live_controller_tests.py"
LIVE_CONTROLLER_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-live-controller-adapter.json"
LIVE_CONTROLLER_REPORT = ROOT / "test" / "results" / "2026-09-18-live-controller-adapter.md"
LIVE_EPISODE = ROOT / "tools" / "evaluation_live_episode.py"
LIVE_EPISODE_TESTS = ROOT / "test" / "harness" / "evaluation_live_episode_tests.py"
LIVE_EPISODE_EVIDENCE = ROOT / "test" / "results" / "2026-09-17-live-episode-integration.json"
LIVE_EPISODE_REPORT = ROOT / "test" / "results" / "2026-09-17-live-episode-integration.md"
PILOT_RUNNER = ROOT / "tools" / "evaluation_pilot.py"
PILOT_TESTS = ROOT / "test" / "harness" / "evaluation_pilot_tests.py"
PILOT_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-pilot-preflight.json"
PILOT_REPORT = ROOT / "test" / "results" / "2026-09-18-pilot-preflight.md"
PILOT_AUTHORISATION_TEMPLATE = ROOT / "docs" / "REAL-WORLD-PILOT-AUTHORISATION-TEMPLATE.json"
CORPUS_HARNESS = ROOT / "test" / "harness" / "realworld.py"
CORPUS_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-realworld-corpus.json"
CORPUS_REPORT = ROOT / "test" / "results" / "2026-09-18-realworld-corpus.md"
DEVELOPMENT_RESULT_TOOL = ROOT / "tools" / "evaluation_development_result.py"
DEVELOPMENT_RESULT_TESTS = ROOT / "test" / "harness" / "evaluation_development_result_tests.py"
DEVELOPMENT_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-realworld-development.json"
DEVELOPMENT_REPORT = ROOT / "test" / "results" / "2026-09-18-realworld-development.md"
RESERVED_RESULT_TOOL = ROOT / "tools" / "evaluation_reserved_result.py"
RESERVED_RESULT_TESTS = ROOT / "test" / "harness" / "evaluation_reserved_result_tests.py"
RESERVED_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-realworld-reserved.json"
RESERVED_REPORT = ROOT / "test" / "results" / "2026-09-18-realworld-reserved.md"
ROUTER = ROOT / "tools" / "route.py"
ROUTING_PRIORS = ROOT / "src" / "routing_priors.json"
QUALIFIED_DEFAULT_TESTS = ROOT / "test" / "harness" / "qualified_default_tests.py"
INSTALL_TESTS = ROOT / "test" / "harness" / "install_tests.py"


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
        ROOT / "LICENSE",
        ROOT / "dist" / "bundle-manifest.json",
        CATALOGUE,
        PRICE,
        ROOT / "src" / "acceptance-contract.example.json",
        ROOT / "src" / "model_registry.json",
        ROOT / "src" / "System" / "schemas" / "RoutingLedgerEntry.schema.json",
        ROOT / "src" / "System" / "schemas" / "BudgetEntry.schema.json",
        ROOT / "tools" / "acceptance.py",
        ROOT / "tools" / "claudep.py",
        ROOT / "tools" / "dispatch_budget.py",
        ROOT / "tools" / "evaluation_freeze.py",
        ROOT / "tools" / "model_registry.py",
        ROOT / "tools" / "realworld_isolation.py",
        ROOT / "tools" / "system_controller.py",
        ROUTER,
        ROUTING_PRIORS,
        QUALIFIED_DEFAULT_TESTS,
        INSTALL_TESTS,
        ROOT / "test" / "harness" / "realworld.py",
        ROOT / "test" / "harness" / "realworld_tests.py",
        ROOT / "test" / "harness" / "model_registry_tests.py",
        ISOLATION,
    ]
    fixture_files = [path for path in (ROOT / "test" / "fixtures" / "realworld").rglob("*") if path.is_file()]
    oracle_files = [path for path in (ROOT / "test" / "oracles" / "realworld").rglob("*") if path.is_file()]
    runner_files = [path for path in (RUNNER, RUNNER_EVIDENCE, RUNNER_REPORT) if path.is_file()]
    calibration_files = [path for path in (
        CALIBRATION, CALIBRATION_TESTS, CALIBRATION_EVIDENCE,
        ADJUDICATION, ADJUDICATION_TESTS, ADJUDICATION_EVIDENCE,
        LIVE_ADAPTER, LIVE_ADAPTER_TESTS, LIVE_ADAPTER_EVIDENCE, LIVE_ADAPTER_REPORT,
        LIVE_CONTROLLER, LIVE_CONTROLLER_TESTS, LIVE_CONTROLLER_EVIDENCE,
        LIVE_CONTROLLER_REPORT,
        LIVE_EPISODE, LIVE_EPISODE_TESTS, LIVE_EPISODE_EVIDENCE, LIVE_EPISODE_REPORT,
        PILOT_RUNNER, PILOT_TESTS, PILOT_EVIDENCE, PILOT_REPORT,
        PILOT_AUTHORISATION_TEMPLATE,
        CORPUS_EVIDENCE, CORPUS_REPORT,
        DEVELOPMENT_RESULT_TOOL, DEVELOPMENT_RESULT_TESTS,
        DEVELOPMENT_EVIDENCE, DEVELOPMENT_REPORT,
        RESERVED_RESULT_TOOL, RESERVED_RESULT_TESTS, RESERVED_EVIDENCE, RESERVED_REPORT,
    ) if path.is_file()]
    return sorted(set(fixed + fixture_files + oracle_files + runner_files + calibration_files))


def valid_qualified_default() -> tuple[bool, dict]:
    """Prove that source and bundle expose the W08-selected B0 policy."""
    dist_router = ROOT / "dist" / "tools" / "route.py"
    dist_priors = ROOT / "dist" / "src" / "routing_priors.json"
    required = (ROUTER, ROUTING_PRIORS, QUALIFIED_DEFAULT_TESTS, INSTALL_TESTS,
                dist_router, dist_priors)
    if not all(path.is_file() for path in required):
        return False, {"policy_id": "B0", "reason": "required source or bundle file is missing"}

    source = json.loads(ROUTING_PRIORS.read_text(encoding="utf-8"))
    bundled = json.loads(dist_priors.read_text(encoding="utf-8"))
    policy = source.get("qualified_default") or {}
    expected = {
        "policy_id": "B0",
        "first_cell": "worker-sonnet-low",
        "repair_cell": "worker-sonnet-low",
        "fallback_cell": "worker-opus-high",
        "maximum_worker_attempts": 3,
        "controller_allowed": False,
        "adaptive_routing_enabled": False,
        "evidence": "test/results/2026-09-18-realworld-reserved.json",
        "evidence_sha256": "79624e2bf2c846531a4d2ebc746449a7c70c3e4310d0271cb9d0342ee5e47382",
        "decision": "docs/DECISIONS.md D107",
    }
    checks = {
        "configuration_exact": all(policy.get(key) == value for key, value in expected.items()),
        "source_bundle_priors_equal": source == bundled,
        "source_bundle_router_equal": ROUTER.read_bytes() == dist_router.read_bytes(),
        "rollback_documented": bool(policy.get("rollback")),
        "behavioural_regression_present": QUALIFIED_DEFAULT_TESTS.is_file(),
        "install_rollback_regression_present": INSTALL_TESTS.is_file(),
    }
    return all(checks.values()), {
        "policy_id": "B0",
        "sequence": ["worker-sonnet-low", "worker-sonnet-low", "worker-opus-high"],
        "maximum_worker_attempts": 3,
        "controller_allowed": False,
        "adaptive_routing_enabled": False,
        "evidence": policy.get("evidence"),
        "evidence_sha256": policy.get("evidence_sha256"),
        "decision": policy.get("decision"),
        "rollback": policy.get("rollback"),
        "checks": checks,
    }


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
        and len(checks) == 9 and all(checks.values())
        and set(cases) == {"b0-repair", "b1-ladder", "b2-controller",
                           "crash_recovery", "missing_cost"}
    )
    return valid, evidence_digest, value


def valid_live_controller_evidence() -> tuple[bool, str | None, dict]:
    valid, evidence_digest, value = valid_evidence(LIVE_CONTROLLER_EVIDENCE)
    checks = value.get("checks") or {}
    report = value.get("report") or {}
    valid = bool(
        valid and LIVE_CONTROLLER.is_file() and LIVE_CONTROLLER_REPORT.is_file()
        and value.get("mode") == "offline-injected-controller-v1"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(LIVE_CONTROLLER)
        and report.get("path") == LIVE_CONTROLLER_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(LIVE_CONTROLLER_REPORT)
        and len(checks) == 9 and all(checks.values())
    )
    return valid, evidence_digest, value


def valid_pilot_preflight_evidence() -> tuple[bool, str | None, dict]:
    valid, evidence_digest, value = valid_evidence(PILOT_EVIDENCE)
    checks = value.get("checks") or {}
    report = value.get("report") or {}
    valid = bool(
        valid and PILOT_RUNNER.is_file() and PILOT_REPORT.is_file()
        and value.get("mode") == "offline-paid-evaluation-preflight-v2"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(PILOT_RUNNER)
        and report.get("path") == PILOT_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(PILOT_REPORT)
        and len(checks) == 13 and all(checks.values())
    )
    return valid, evidence_digest, value


def valid_corpus_evidence() -> tuple[bool, str | None, dict]:
    valid, evidence_digest, value = valid_evidence(CORPUS_EVIDENCE)
    report = value.get("report") or {}
    expected_development = [f"D{number:02d}" for number in range(1, 13)]
    expected_reserved = [f"H{number:02d}" for number in range(1, 13)]
    task_results = value.get("tasks") or []
    valid = bool(
        valid and CORPUS_HARNESS.is_file() and CORPUS_REPORT.is_file()
        and value.get("mode") == "offline-corpus-qualification-v1"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(CORPUS_HARNESS)
        and value.get("catalogue_sha256") == sha256(CATALOGUE)
        and value.get("development_tasks") == expected_development
        and value.get("reserved_tasks") == expected_reserved
        and value.get("task_count") == 24
        and value.get("variant_states") == 144
        and value.get("attack_checks") == 72
        and len(task_results) == 24
        and all(
            task.get("passed") is True
            and task.get("oracle_unchanged") is True
            and task.get("variants_as_expected") is True
            and task.get("attacks_rejected") is True
            for task in task_results
        )
        and (value.get("reserved_authoring") or {}).get("arm_label_blinding")
            == "not-provable-same-session"
        and report.get("path") == CORPUS_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(CORPUS_REPORT)
    )
    return valid, evidence_digest, value


def valid_development_evidence() -> tuple[bool, str | None, dict]:
    """Validate the completed W07 result before it can inform W08."""
    valid, evidence_digest, value = valid_evidence(DEVELOPMENT_EVIDENCE)
    checks = value.get("checks") or {}
    report = value.get("report") or {}
    policies = {row.get("policy_id"): row for row in value.get("policy_summary") or []}
    decision = value.get("decision") or {}
    valid = bool(
        valid and DEVELOPMENT_RESULT_TOOL.is_file() and DEVELOPMENT_REPORT.is_file()
        and value.get("offline_aggregation") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(DEVELOPMENT_RESULT_TOOL)
        and value.get("candidate_sha256")
            == "6f89533045ac2a6abe29e989f5a8ba69666a8f50bab6e58b334ab467a6638f28"
        and value.get("manifest_sha256")
            == "b5e78aab46c13eba30fb8dd0a6a0bda71b68cada30c10269e5247b287ede15a8"
        and (value.get("budget") or {}).get("known_spend_usd") == 1.376153606
        and policies.get("B0", {}).get("accepted") == 11
        and policies.get("B1", {}).get("accepted") == 12
        and decision.get("baseline_retained") == "B0"
        and decision.get("adaptive_candidate") == "B1"
        and decision.get("proceed_to_w08") is True
        and decision.get("default_changed") is False
        and len(checks) == 11 and all(checks.values())
        and report.get("path") == DEVELOPMENT_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(DEVELOPMENT_REPORT)
    )
    return valid, evidence_digest, value


def valid_reserved_evidence() -> tuple[bool, str | None, dict]:
    """Validate the completed W08 result and its release-gate decision."""
    valid, evidence_digest, value = valid_evidence(RESERVED_EVIDENCE)
    checks = value.get("checks") or {}
    report = value.get("report") or {}
    policies = {row.get("policy_id"): row for row in value.get("policy_summary") or []}
    gates = value.get("promotion_gates") or {}
    decision = value.get("decision") or {}
    valid = bool(
        valid and RESERVED_RESULT_TOOL.is_file() and RESERVED_REPORT.is_file()
        and value.get("offline_aggregation") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == sha256(RESERVED_RESULT_TOOL)
        and value.get("candidate_sha256")
            == "99f6e7447b81054101c7ad57c4cd1bfd14b8d860aeec6f54f6f5a8d812e04fa4"
        and value.get("manifest_sha256")
            == "a064865e0712bca2d8b9d32887a78dc383292884dfe35af27266c564f8e9dd86"
        and (value.get("budget") or {}).get("known_spend_usd") == 1.053580005
        and policies.get("B0", {}).get("accepted") == 12
        and policies.get("B1", {}).get("accepted") == 10
        and gates.get("promotion_gate_passed") is False
        and decision.get("qualified_default") == "B0"
        and decision.get("candidate_not_promoted") == "B1"
        and decision.get("package_policy") == "B0"
        and decision.get("proceed_to_w09") is True
        and len(checks) == 11 and all(checks.values())
        and report.get("path") == RESERVED_REPORT.relative_to(ROOT).as_posix()
        and report.get("sha256") == sha256(RESERVED_REPORT)
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
    controller_valid, controller_digest, controller = valid_live_controller_evidence()
    episode_valid, episode_digest, episode = valid_live_episode_evidence()
    pilot_valid, pilot_digest, pilot = valid_pilot_preflight_evidence()
    corpus_valid, corpus_digest, corpus = valid_corpus_evidence()
    development_valid, development_digest, development = valid_development_evidence()
    reserved_valid, reserved_digest, reserved = valid_reserved_evidence()
    qualified_default_valid, qualified_default = valid_qualified_default()
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
    if not controller_valid:
        blockers.append("live Controller escalation adapter and offline qualification evidence are missing or invalid")
    if not pilot_valid:
        blockers.append("pilot profile preflight and authorisation boundary are missing or invalid")
    if not corpus_valid:
        blockers.append("complete development and reserved corpus evidence is missing or invalid")
    if not development_valid:
        blockers.append("W07 development comparison evidence is missing or invalid")
    if not reserved_valid:
        blockers.append("W08 reserved comparison evidence is missing or invalid")
    if not qualified_default_valid:
        blockers.append("W09 qualified-default source or bundle is missing or invalid")
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
            "controller_adapter_implemented": LIVE_CONTROLLER.is_file(),
            "controller_adapter_qualified": controller_valid,
            "controller_adapter_evidence": LIVE_CONTROLLER_EVIDENCE.relative_to(ROOT).as_posix(),
            "controller_adapter_evidence_sha256": controller_digest,
            "controller_adapter_mode": controller.get("mode"),
            "pilot_preflight_qualified": pilot_valid,
            "pilot_preflight_evidence": PILOT_EVIDENCE.relative_to(ROOT).as_posix(),
            "pilot_preflight_evidence_sha256": pilot_digest,
            "pilot_preflight_mode": pilot.get("mode"),
            "note": "Worker and Controller execution, nested accounting, sequencing and at-most-once recovery qualify offline.",
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
        "corpus": {
            "qualified": corpus_valid,
            "evidence": CORPUS_EVIDENCE.relative_to(ROOT).as_posix(),
            "evidence_sha256": corpus_digest,
            "task_count": corpus.get("task_count"),
            "development_tasks": corpus.get("development_tasks"),
            "reserved_tasks": corpus.get("reserved_tasks"),
            "reserved_authoring": corpus.get("reserved_authoring"),
        },
        "development": {
            "qualified": development_valid,
            "evidence": DEVELOPMENT_EVIDENCE.relative_to(ROOT).as_posix(),
            "evidence_sha256": development_digest,
            "known_spend_usd": (development.get("budget") or {}).get("known_spend_usd"),
            "policy_summary": development.get("policy_summary"),
            "decision": development.get("decision"),
        },
        "reserved": {
            "qualified": reserved_valid,
            "evidence": RESERVED_EVIDENCE.relative_to(ROOT).as_posix(),
            "evidence_sha256": reserved_digest,
            "known_spend_usd": (reserved.get("budget") or {}).get("known_spend_usd"),
            "policy_summary": reserved.get("policy_summary"),
            "promotion_gates": reserved.get("promotion_gates"),
            "decision": reserved.get("decision"),
        },
        "qualified_default": {
            **qualified_default,
            "qualified": qualified_default_valid,
        },
        "bound_files": files,
        "paid_launch_ready": not blockers,
        "blockers": blockers,
    }


def stable(value: dict) -> dict:
    # The freeze commit necessarily follows the source revision it records.
    # Candidate content is bound by candidate_sha256; ignore the informational
    # revision and timestamp when checking a committed freeze.
    return {key: item for key, item in value.items()
            if key not in {"created_at", "source_revision"}}


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
