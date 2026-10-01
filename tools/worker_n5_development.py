#!/usr/bin/env python3
"""Freeze diverse N5 development arms and require exact paid approval.

The reserved R-series tasks are frozen for N6 but never enter this schedule or
an N5 worker's filesystem. A task-sensitive result remains exploratory until
the separately held-out, repeated N6 comparison is complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
import zipfile
from pathlib import Path

import dispatch_budget
import model_registry
import route
import worker_evaluation
import worker_selector
import worker_wsl_attestation as host_attestation
import worker_wsl_subscription_attestation as subscription_host
import worker_wsl_subscription_sentinel as subscription_sentinel
from task_executor import TaskExecutor, EXPERIMENTAL_POLICY
from worker_adapter import digest
from worker_wsl_transport import (WslWorkerAdapter, grade_isolated,
                                  screen_observed_cells, wsl_public_command_runner)

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "test" / "fixtures" / "worker_n5_realworld"
SCREEN_RUN = ROOT / "test" / "results" / "2026-09-25-worker-n5-screen-run"
ARMS = ("B0", "candidate", "alternative")
ALTERNATIVE_BY_COMPLEXITY = {"routine": "worker-sonnet-medium",
                             "moderate": "worker-sonnet-xhigh",
                             "complex": "worker-fable-high"}
FALLBACK_CELL = "worker-opus-high"
EPISODE_CEILING_USD = 3.0
CAMPAIGN_CEILING_USD = 36 * EPISODE_CEILING_USD
CAMPAIGN_PROMPT = "One bounded worker attempt. Do not delegate."
HEX = re.compile(r"[0-9a-f]{64}\Z")
SOURCE = ("tools/worker_n5_development.py", "tools/worker_n5_live_development.py",
          "tools/worker_n5_corpus.py",
          "tools/worker_wsl_auth.py",
          "tools/worker_wsl_subscription_attestation.py",
          "tools/worker_wsl_subscription_sentinel.py")
PUBLIC = ("app.py", "public_check.py", "ISSUE.md", "acceptance.json")


class DevelopmentError(RuntimeError):
    """A development campaign cannot safely admit another episode."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screen_evidence(screen_run: Path = SCREEN_RUN) -> dict:
    """Check the historical screen as evidence without re-freezing old source."""
    paths = {name: screen_run / name for name in
             ("campaign.json", "budget.json", "actors.zip")}
    try:
        campaign = json.loads(paths["campaign.json"].read_text(encoding="utf-8"))
        budget = json.loads(paths["budget.json"].read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DevelopmentError("complete screen checkpoint and budget are required") from exc
    body = {key: value for key, value in campaign.items() if key != "state_sha256"}
    rows = campaign.get("rows")
    invocations = budget.get("invocations")
    if (campaign.get("state_sha256") != digest(body)
            or campaign.get("status") != "complete"
            or campaign.get("next_sequence") != 61
            or campaign.get("inflight") is not None
            or campaign.get("stopped_cells") != []
            or not isinstance(rows, list) or len(rows) != 60
            or not isinstance(invocations, dict) or len(invocations) != 60
            or any(value.get("state") != "settled" for value in invocations.values())):
        raise DevelopmentError("screen is incomplete or has unsettled calls")
    expected = [f"worker-{model}-{effort}"
                for model in model_registry.load()["model_order"]
                for effort in model_registry.load()["effort_order"]]
    for index, row in enumerate(rows):
        receipt = row.get("receipt") or {}
        if (row.get("sequence") != index + 1
                or row.get("cell") != expected[index // 4]
                or row.get("status") != "graded"
                or row.get("observed_identity_valid") is not True
                or receipt.get("terminal") is not True
                or receipt.get("writer_stopped") is not True
                or type(receipt.get("cost_usd")) not in (int, float)
                or receipt["cost_usd"] < 0
                or (index % 4 != 0 and not isinstance(row.get("grade"), dict))):
            raise DevelopmentError(f"screen row {index + 1} lacks settled identity or grade")
    by_sequence = {value.get("metadata", {}).get("sequence"): value
                   for value in invocations.values()}
    if (set(by_sequence) != set(range(1, 61))
            or any(by_sequence[index]["metadata"].get("cell") != row["cell"]
                   or not math.isclose(by_sequence[index].get("cost_usd", -1),
                                       row["receipt"]["cost_usd"], abs_tol=1e-8)
                   for index, row in enumerate(rows, 1))
            or budget.get("cancelled") is True):
        raise DevelopmentError("screen receipts and durable budget do not reconcile")
    if not paths["actors.zip"].is_file():
        raise DevelopmentError("public actor archive is missing")
    try:
        with zipfile.ZipFile(paths["actors.zip"]) as archive:
            if archive.testzip() is not None or len(archive.namelist()) != 240:
                raise DevelopmentError("screen actor archive is incomplete")
    except (OSError, zipfile.BadZipFile) as exc:
        raise DevelopmentError("screen actor archive is unreadable") from exc
    return {name + "_sha256": sha(path) for name, path in paths.items()}


def supported_cells(registry: dict) -> list[str]:
    """Use only observed direct-worker cells for automatic N5 dispatch."""
    screen_cells, _ = screen_observed_cells()
    names = []
    for name in registry["cells"]:
        cell = model_registry.resolve_cell(name, registry)
        if (cell["direct_worker"] and
                (cell["availability"]["status"] == "observed" or name in screen_cells)):
            names.append(name)
    return sorted(names)


def build_manifest(*, host_attestation_sha256: str,
                   subscription_attestation_sha256: str,
                   subscription_sentinel_sha256: str,
                   spend_notice_sha256: str,
                   corpus: Path = CORPUS, screen_run: Path = SCREEN_RUN) -> dict:
    """Freeze 12 public tasks by three arms with balanced within-task order."""
    for name, value in (("host", host_attestation_sha256),
                        ("subscription", subscription_attestation_sha256),
                        ("sentinel", subscription_sentinel_sha256),
                        ("notice", spend_notice_sha256)):
        if not isinstance(value, str) or not HEX.fullmatch(value):
            raise DevelopmentError(f"{name} SHA-256 is required")
    catalogue = worker_evaluation.load_catalogue(corpus)["tasks"]
    development = [task for task in catalogue if task["split"] == "development"]
    if len(development) != 12:
        raise DevelopmentError("expected twelve frozen development tasks")
    registry = model_registry.load()
    supported = supported_cells(registry)
    if not ({"worker-sonnet-low", "worker-sonnet-high", FALLBACK_CELL}
            | set(ALTERNATIVE_BY_COMPLEXITY.values())) <= set(supported):
        raise DevelopmentError("a required development cell is not observed")
    rows = []
    for task_index, task in enumerate(development):
        assessment = worker_selector.assess(task["assessment"])
        selection = worker_selector.select(
            assessment, supported_cells=set(supported),
            remaining_usd=EPISODE_CEILING_USD, budget_enforced=True)
        if selection["stop"] is not None or selection["selected_cell"] is None:
            raise DevelopmentError(f"candidate cannot select {task['id']}: {selection['stop']}")
        operational = {row["cell"] for row in selection["cells"]
                       if row["operationally_eligible"]}
        alternative = ALTERNATIVE_BY_COMPLEXITY[task["assessment"]["complexity"]]
        alternative_selection = worker_selector.select(
            assessment, supported_cells=set(supported),
            remaining_usd=EPISODE_CEILING_USD, budget_enforced=True,
            override={"cell": alternative, "actor": "n5-development",
                      "authority_id": "a" * 64,
                      "reason": "predeclared bounded comparison arm",
                      "max_cost_usd": EPISODE_CEILING_USD})
        if (alternative_selection["stop"] is not None
                or alternative_selection["selected_cell"] != alternative
                or FALLBACK_CELL not in operational):
            raise DevelopmentError("predeclared alternative is not eligible")
        ladders = {
            "B0": route.plan("structured", "medium", "contained")["execution_ladder"],
            "candidate": [selection["selected_cell"], selection["selected_cell"],
                          FALLBACK_CELL],
            "alternative": [alternative, alternative, FALLBACK_CELL],
        }
        for arm in (*ARMS[task_index % 3:], *ARMS[:task_index % 3]):
            rows.append({"sequence": len(rows) + 1, "task_id": task["id"],
                         "arm": arm, "assessment_digest": assessment["assessment_digest"],
                         "selected_cell": ladders[arm][0], "ladder": ladders[arm],
                         "maximum_usd": EPISODE_CEILING_USD})
    if len(rows) != 36 or sum(row["maximum_usd"] for row in rows) != CAMPAIGN_CEILING_USD:
        raise DevelopmentError("development schedule or allocation changed")
    value = {"schema_version": 1, "profile": "worker-n5-development",
             "credential_method": "subscription",
             "host_attestation_sha256": host_attestation_sha256,
             "subscription_attestation_sha256": subscription_attestation_sha256,
             "subscription_sentinel_sha256": subscription_sentinel_sha256,
             "spend_notice_sha256": spend_notice_sha256,
             "screen_evidence": screen_evidence(screen_run),
             "execution_manifest_sha256": worker_evaluation.freeze(corpus)["manifest_sha256"],
             "corpus_files": worker_evaluation._files(corpus),
             "assessments": {task["id"]: worker_selector.assess(task["assessment"])
                             for task in development},
             "extra_source_sha256": {name: sha(ROOT / name) for name in SOURCE},
             "registry_id": registry["registry_id"],
             "supported_cells": supported,
             "policy": {"candidate": worker_selector.POLICY,
                        "alternative_by_complexity": ALTERNATIVE_BY_COMPLEXITY,
                        "fallback": FALLBACK_CELL,
                        "experimental_dispatch": EXPERIMENTAL_POLICY,
                        "campaign_prompt": CAMPAIGN_PROMPT},
             "rows": rows,
             "cost": {"currency": "USD", "episodes": len(rows),
                      "maximum_usd": CAMPAIGN_CEILING_USD,
                      "episode_maximum_usd": EPISODE_CEILING_USD,
                      "basis": "36 x USD 3 local admission allocations"},
             "retry_policy": "no-automatic-provider-replay",
             "reserved_tasks_allowed": False,
             "authorisation": "separate-exact-approval-required"}
    return {**value, "manifest_sha256": digest(value)}


def validate_manifest(manifest: dict, *, corpus: Path = CORPUS,
                      screen_run: Path = SCREEN_RUN, check_host: bool = False) -> None:
    if not isinstance(manifest, dict):
        raise DevelopmentError("development manifest must be an object")
    expected = build_manifest(
        host_attestation_sha256=manifest.get("host_attestation_sha256", ""),
        subscription_attestation_sha256=manifest.get("subscription_attestation_sha256", ""),
        subscription_sentinel_sha256=manifest.get("subscription_sentinel_sha256", ""),
        spend_notice_sha256=manifest.get("spend_notice_sha256", ""),
        corpus=corpus, screen_run=screen_run)
    if manifest != expected:
        raise DevelopmentError("development manifest or frozen inputs changed")
    if check_host:
        host = json.loads(host_attestation.OUTPUT.read_text(encoding="utf-8"))
        auth = json.loads(subscription_host.OUTPUT.read_text(encoding="utf-8"))
        sentinel = json.loads(subscription_sentinel.OUTPUT.read_text(encoding="utf-8"))
        if (not host_attestation.validate(host, check_host=True)
                or host["evidence_sha256"] != manifest["host_attestation_sha256"]
                or not subscription_host.validate(auth, check_host=True)
                or auth["evidence_sha256"] != manifest["subscription_attestation_sha256"]
                or not subscription_sentinel.validate(sentinel, check_host=False)
                or sentinel["evidence_sha256"] != manifest["subscription_sentinel_sha256"]
                or sentinel["host_attestation_sha256"] != host["evidence_sha256"]
                or sentinel["subscription_attestation_sha256"] != auth["evidence_sha256"]):
            raise DevelopmentError("WSL subscription host or sentinel is stale")


def validate_authorisation(manifest: dict, approval: dict, *,
                           corpus: Path = CORPUS, screen_run: Path = SCREEN_RUN,
                           check_host: bool = True) -> None:
    validate_manifest(manifest, corpus=corpus, screen_run=screen_run,
                      check_host=check_host)
    if (not isinstance(approval, dict) or set(approval) != {
            "schema_version", "decision", "manifest_sha256", "maximum_authorised_usd",
            "credential_method", "spend_notice_sha256", "approved_by", "approved_at"}
            or approval["schema_version"] != 1 or approval["decision"] != "approved"
            or approval["manifest_sha256"] != manifest["manifest_sha256"]
            or approval["maximum_authorised_usd"] != CAMPAIGN_CEILING_USD
            or approval["credential_method"] != "subscription"
            or approval["spend_notice_sha256"] != manifest["spend_notice_sha256"]
            or not isinstance(approval["approved_by"], str)
            or not approval["approved_by"].strip()
            or not isinstance(approval["approved_at"], str)
            or not approval["approved_at"].strip()):
        raise DevelopmentError("approval must exactly match development manifest and cap")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spend-notice", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        host = json.loads(host_attestation.OUTPUT.read_text(encoding="utf-8"))
        auth = json.loads(subscription_host.OUTPUT.read_text(encoding="utf-8"))
        sentinel = json.loads(subscription_sentinel.OUTPUT.read_text(encoding="utf-8"))
        manifest = build_manifest(
            host_attestation_sha256=host["evidence_sha256"],
            subscription_attestation_sha256=auth["evidence_sha256"],
            subscription_sentinel_sha256=sentinel["evidence_sha256"],
            spend_notice_sha256=sha(args.spend_notice))
        validate_manifest(manifest, check_host=True)
    except (OSError, ValueError, KeyError, DevelopmentError) as exc:
        print(f"N5 development planning blocked: {exc}", file=sys.stderr)
        return 2
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8", newline="\n")
    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(f"N5 development: {len(manifest['rows'])} episodes, "
              f"USD {CAMPAIGN_CEILING_USD:.2f} local allocation; "
              f"manifest {manifest['manifest_sha256'][:12]}; paid launch disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
