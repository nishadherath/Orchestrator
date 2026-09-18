#!/usr/bin/env python3
"""Prepare, validate and execute an authorised real-world evaluation stage.

Preparation and qualification make no model calls. Execution is unavailable
without an exact operator authorisation file bound to the current candidate
and manifest. Fixed profiles preserve the completed pilot stages and define
the 32-episode W07 development comparison without changing historical runs.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import platform
import sys
import tempfile
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import evaluation_freeze  # noqa: E402
import evaluation_live_episode  # noqa: E402
import evaluation_runner  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402

DEFAULT_MANIFEST = ROOT / "docs" / "REAL-WORLD-PILOT-6-EPISODE-2026-09-18.json"
DEFAULT_REPORT = ROOT / "docs" / "REAL-WORLD-PILOT-6-EPISODE-2026-09-18.md"
DEFAULT_AUTHORISATION = ROOT / "docs" / "REAL-WORLD-PILOT-AUTHORISATION.json"
AUTHORISATION_TEMPLATE = ROOT / "docs" / "REAL-WORLD-PILOT-AUTHORISATION-TEMPLATE.json"
DEFAULT_CAMPAIGN_ROOT = ROOT / "pilot-runs" / "realworld-v1-six-episode"
CONTINUATION_MANIFEST = ROOT / "docs" / "REAL-WORLD-PILOT-18-EPISODE-2026-09-18.json"
CONTINUATION_REPORT = ROOT / "docs" / "REAL-WORLD-PILOT-18-EPISODE-2026-09-18.md"
CONTINUATION_AUTHORISATION = ROOT / "docs" / "REAL-WORLD-PILOT-CONTINUATION-AUTHORISATION.json"
CONTINUATION_CAMPAIGN_ROOT = ROOT / "pilot-runs" / "realworld-v1-remaining-eighteen"
DEVELOPMENT_MANIFEST = ROOT / "docs" / "REAL-WORLD-DEVELOPMENT-32-EPISODE-2026-09-18.json"
DEVELOPMENT_REPORT = ROOT / "docs" / "REAL-WORLD-DEVELOPMENT-32-EPISODE-2026-09-18.md"
DEVELOPMENT_AUTHORISATION = ROOT / "docs" / "REAL-WORLD-DEVELOPMENT-AUTHORISATION.json"
DEVELOPMENT_CAMPAIGN_ROOT = ROOT / "pilot-runs" / "realworld-v1-development-thirty-two"
RESERVED_MANIFEST = ROOT / "docs" / "REAL-WORLD-RESERVED-48-EPISODE-2026-09-18.json"
RESERVED_REPORT = ROOT / "docs" / "REAL-WORLD-RESERVED-48-EPISODE-2026-09-18.md"
RESERVED_AUTHORISATION = ROOT / "docs" / "REAL-WORLD-RESERVED-AUTHORISATION.json"
RESERVED_CAMPAIGN_ROOT = ROOT / "pilot-runs" / "realworld-v1-reserved-forty-eight"
DEFAULT_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-pilot-preflight.json"
DEFAULT_EVIDENCE_REPORT = ROOT / "test" / "results" / "2026-09-18-pilot-preflight.md"
PILOT_CHECKPOINT_RESULT = ROOT / "test" / "results" / "2026-09-18-realworld-pilot-checkpoint.json"
PILOT_CONTINUATION_RESULT = ROOT / "test" / "results" / "2026-09-18-realworld-pilot-continuation.json"
DEVELOPMENT_RESULT = ROOT / "test" / "results" / "2026-09-18-realworld-development.json"
EPISODE_BUDGET_USD = 4.0


@dataclasses.dataclass(frozen=True)
class PilotProfile:
    key: str
    campaign: str
    title: str
    tasks: tuple[str, ...]
    sequence_start: int
    calibration_headroom_usd: float
    description: str
    policies: tuple[str, ...] = ("B0", "B1", "B2")
    repeat_tasks: tuple[str, ...] = ()
    alternate_policy_order: bool = False

    @property
    def episodes(self) -> tuple[tuple[int, str, str, str, int], ...]:
        rows: list[tuple[str, str, int]] = []
        occurrences: dict[str, int] = {}
        for pair_index, task in enumerate((*self.tasks, *self.repeat_tasks)):
            occurrences[task] = occurrences.get(task, 0) + 1
            policies = self.policies
            if self.alternate_policy_order and pair_index % 2:
                policies = tuple(reversed(policies))
            rows.extend((task, policy, occurrences[task]) for policy in policies)
        return tuple(
            (
                sequence,
                f"evaluation-{sequence:03d}-{task.lower()}-{policy.lower()}-r{repetition}",
                task,
                policy,
                repetition,
            )
            for sequence, (task, policy, repetition) in enumerate(rows, self.sequence_start)
        )

    @property
    def episode_total_usd(self) -> float:
        return len(self.episodes) * EPISODE_BUDGET_USD

    @property
    def total_ceiling_usd(self) -> float:
        return self.episode_total_usd + self.calibration_headroom_usd


CHECKPOINT_PROFILE = PilotProfile(
    key="checkpoint-six",
    campaign="realworld-v1-six-episode-checkpoint",
    title="Six-episode paid pilot approval package",
    tasks=("D01", "D11"),
    sequence_start=1,
    calibration_headroom_usd=2.0,
    description="D01 and D11 once under each policy B0, B1 and B2",
)
CONTINUATION_PROFILE = PilotProfile(
    key="continuation-eighteen",
    campaign="realworld-v1-remaining-eighteen",
    title="Remaining eighteen-episode paid pilot approval package",
    tasks=("D03", "D05", "D07", "D08", "D09", "D10"),
    sequence_start=7,
    calibration_headroom_usd=2.0,
    description="D03, D05 and D07-D10 once under each policy B0, B1 and B2",
)
DEVELOPMENT_PROFILE = PilotProfile(
    key="development-thirty-two",
    campaign="realworld-v1-development-thirty-two",
    title="W07 32-episode development comparison approval package",
    tasks=tuple(f"D{number:02d}" for number in range(1, 13)),
    repeat_tasks=("D03", "D05", "D07", "D11"),
    policies=("B0", "B1"),
    alternate_policy_order=True,
    sequence_start=25,
    calibration_headroom_usd=12.0,
    description=("D01-D12 once under B0 and B1, then the predeclared D03, D05, "
                 "D07 and D11 repeats under both policies"),
)
RESERVED_PROFILE = PilotProfile(
    key="reserved-forty-eight",
    campaign="realworld-v1-reserved-forty-eight",
    title="W08 48-episode reserved comparison approval package",
    tasks=tuple(f"H{number:02d}" for number in range(1, 13)),
    repeat_tasks=tuple(f"H{number:02d}" for number in range(1, 13)),
    policies=("B0", "B1"),
    alternate_policy_order=True,
    sequence_start=57,
    calibration_headroom_usd=8.0,
    description="H01-H12 twice under the frozen B0 baseline and B1 adaptive candidate",
)
PROFILES = {
    profile.key: profile
    for profile in (CHECKPOINT_PROFILE, CONTINUATION_PROFILE,
                    DEVELOPMENT_PROFILE, RESERVED_PROFILE)
}
PROFILE_PATHS = {
    CHECKPOINT_PROFILE.key: (DEFAULT_MANIFEST, DEFAULT_REPORT, DEFAULT_AUTHORISATION,
                             DEFAULT_CAMPAIGN_ROOT),
    CONTINUATION_PROFILE.key: (CONTINUATION_MANIFEST, CONTINUATION_REPORT,
                               CONTINUATION_AUTHORISATION, CONTINUATION_CAMPAIGN_ROOT),
    DEVELOPMENT_PROFILE.key: (DEVELOPMENT_MANIFEST, DEVELOPMENT_REPORT,
                              DEVELOPMENT_AUTHORISATION, DEVELOPMENT_CAMPAIGN_ROOT),
    RESERVED_PROFILE.key: (RESERVED_MANIFEST, RESERVED_REPORT,
                           RESERVED_AUTHORISATION, RESERVED_CAMPAIGN_ROOT),
}
AUTHORISATION_BLOCKERS = {
    "paid pilot has not been authorised",
    "paid W07 development comparison has not been authorised",
    "paid W08 reserved comparison has not been authorised",
}


class PilotError(RuntimeError):
    """The pilot is not authorised or cannot safely continue."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def development_cost_projection() -> dict:
    """Project W07 from measured pilot arm costs without hiding the hard cap."""
    paths = (PILOT_CHECKPOINT_RESULT, PILOT_CONTINUATION_RESULT)
    evidence = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    episodes = [row for result in evidence for row in result["episodes"]]
    by_policy = {
        policy: [row["cost_usd"] for row in episodes if row["policy_id"] == policy]
        for policy in DEVELOPMENT_PROFILE.policies
    }
    counts = {
        policy: sum(1 for row in DEVELOPMENT_PROFILE.episodes if row[3] == policy)
        for policy in DEVELOPMENT_PROFILE.policies
    }
    means = {policy: sum(costs) / len(costs) for policy, costs in by_policy.items()}
    maximum = max(row["cost_usd"] for row in episodes)
    return {
        "method": "pilot policy mean multiplied by the fixed W07 episode count",
        "source_evidence": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": file_sha256(path)}
            for path in paths
        ],
        "policy_episode_counts": counts,
        "pilot_policy_mean_usd": {key: round(value, 12) for key, value in means.items()},
        "point_estimate_usd": round(sum(means[key] * counts[key] for key in counts), 9),
        "maximum_observed_pilot_episode_usd": round(maximum, 9),
        "observed_max_extrapolation_usd": round(maximum * len(DEVELOPMENT_PROFILE.episodes), 9),
        "limitation": "The pilot is small; neither extrapolation is a billing limit.",
    }


def reserved_cost_projection() -> dict:
    """Project W08 from the complete, independently graded W07 evidence."""
    evidence = json.loads(DEVELOPMENT_RESULT.read_text(encoding="utf-8"))
    summaries = {row["policy_id"]: row for row in evidence["policy_summary"]}
    counts = {
        policy: sum(1 for row in RESERVED_PROFILE.episodes if row[3] == policy)
        for policy in RESERVED_PROFILE.policies
    }
    means = {
        policy: summaries[policy]["spend_usd"] / summaries[policy]["episodes"]
        for policy in RESERVED_PROFILE.policies
    }
    maximum = max(row["cost_usd"] for row in evidence["episodes"])
    return {
        "method": "W07 policy mean multiplied by the fixed W08 episode count",
        "source_evidence": {
            "path": DEVELOPMENT_RESULT.relative_to(ROOT).as_posix(),
            "sha256": file_sha256(DEVELOPMENT_RESULT),
        },
        "policy_episode_counts": counts,
        "development_policy_mean_usd": {key: round(value, 12) for key, value in means.items()},
        "point_estimate_usd": round(sum(means[key] * counts[key] for key in counts), 9),
        "maximum_observed_development_episode_usd": round(maximum, 9),
        "observed_max_extrapolation_usd": round(maximum * len(RESERVED_PROFILE.episodes), 9),
        "limitation": "Reserved tasks differ from development tasks; neither extrapolation is a billing limit.",
    }


def pilot_manifest(candidate_fn: Callable[[], dict] = evaluation_freeze.candidate,
                   profile: PilotProfile = CHECKPOINT_PROFILE) -> dict:
    freeze = candidate_fn()
    cost = {
        "currency": "USD", "episode_count": len(profile.episodes),
        "per_episode_cap_usd": EPISODE_BUDGET_USD,
        "episode_total_cap_usd": profile.episode_total_usd,
        "calibration_headroom_usd": profile.calibration_headroom_usd,
        "combined_authorisation_ceiling_usd": profile.total_ceiling_usd,
        "basis": f"{len(profile.episodes)} fixed episode reservations plus separate calibration headroom",
    }
    if profile is DEVELOPMENT_PROFILE:
        cost["measured_projection"] = development_cost_projection()
    elif profile is RESERVED_PROFILE:
        cost["measured_projection"] = reserved_cost_projection()
    value = {
        "schema_version": 1,
        "profile": profile.key,
        "campaign": profile.campaign,
        "candidate_sha256": freeze["candidate_sha256"],
        "source_revision": freeze["source_revision"],
        "bundle_version": freeze["bundle"]["version"],
        "isolation_evidence_sha256": freeze["isolation"]["evidence_sha256"],
        "cost": cost,
        "episodes": [
            {"sequence": sequence, "episode_id": episode_id, "task_id": task_id,
             "policy_id": policy_id, "repetition": repetition,
             "budget_usd": EPISODE_BUDGET_USD}
            for sequence, episode_id, task_id, policy_id, repetition in profile.episodes
        ],
        "stop_conditions": [
            "candidate, bundle, isolation or authorisation does not validate",
            "an episode stops with unresolved provider accounting",
            "a served task model does not match the exact required model",
            "the event chain, external grade or protected-oracle check is invalid",
            f"the fixed USD {profile.episode_total_usd:.0f} episode envelope or USD "
            f"{profile.total_ceiling_usd:.0f} combined ceiling would be exceeded",
        ],
        "review_after": (f"all {len(profile.episodes)} episodes complete, or immediately after "
                         "the first stop condition"),
    }
    value["manifest_sha256"] = digest(value)
    return value


def validate_manifest(path: Path, candidate_fn: Callable[[], dict] = evaluation_freeze.candidate,
                      *, require_clean: bool = True,
                      profile: PilotProfile = CHECKPOINT_PROFILE) -> tuple[bool, str, dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read pilot manifest: {exc}", {}
    recorded = value.pop("manifest_sha256", None)
    expected = pilot_manifest(candidate_fn, profile)
    expected.pop("manifest_sha256", None)
    comparable_value = {key: item for key, item in value.items() if key != "source_revision"}
    comparable_expected = {key: item for key, item in expected.items() if key != "source_revision"}
    current = candidate_fn()
    valid = bool(
        recorded == digest(value) and comparable_value == comparable_expected
        and (not require_clean or current.get("source_dirty") is False)
        and len(value.get("episodes") or []) == len(profile.episodes)
        and sum(row.get("budget_usd", 0) for row in value["episodes"]) == profile.episode_total_usd
        and (value.get("cost") or {}).get("combined_authorisation_ceiling_usd")
        == profile.total_ceiling_usd
    )
    value["manifest_sha256"] = recorded
    detail = (f"candidate={value.get('candidate_sha256')}; "
              f"source={'clean' if current.get('source_dirty') is False else 'dirty'}")
    return valid, detail, value


def validate_authorisation(path: Path, manifest: dict) -> tuple[bool, str, dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read pilot authorisation: {exc}", {}
    ceiling = (manifest.get("cost") or {}).get("combined_authorisation_ceiling_usd")
    valid = bool(
        value.get("schema_version") == 1 and value.get("decision") == "approved"
        and value.get("candidate_sha256") == manifest.get("candidate_sha256")
        and value.get("manifest_sha256") == manifest.get("manifest_sha256")
        and value.get("maximum_authorised_usd") == ceiling
        and isinstance(value.get("approved_at"), str) and value["approved_at"].strip()
        and isinstance(value.get("approved_by"), str) and value["approved_by"].strip()
    )
    ceiling_text = f"{ceiling:g}" if isinstance(ceiling, (int, float)) else "unknown"
    detail = ("exact approval present" if valid else
              f"approval does not match candidate, manifest and USD {ceiling_text} ceiling")
    return valid, detail, value


def _episode_integrity(campaign_root: Path, episode_id: str) -> dict:
    episode_root = campaign_root / "episodes" / episode_id
    state_path = episode_root / "state.json"
    budget_path = episode_root / "dispatch-budget.json"
    if not state_path.is_file() or not budget_path.is_file():
        raise PilotError(f"episode evidence missing for {episode_id}")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    budget = DispatchBudget(budget_path).snapshot()
    history = state.get("history") or []
    return {
        "identity_valid": all(row.get("identity_valid") is True for row in history),
        "accounting_complete": not budget["unresolved"],
        "spent_usd": budget["spent_usd"],
        "oracle_unchanged": (state.get("grade") or {}).get("oracle_unchanged") is True,
        "learning_eligible": state.get("learning_eligible") is True,
    }


def execute(manifest_path: Path, authorisation_path: Path, campaign_root: Path,
            *, profile: PilotProfile = CHECKPOINT_PROFILE,
            candidate_fn: Callable[[], dict] = evaluation_freeze.candidate,
            runner_factory: Callable[[Path], object] = evaluation_live_episode.LiveEpisodeRunner) -> dict:
    valid, detail, manifest = validate_manifest(manifest_path, candidate_fn, profile=profile)
    if not valid:
        raise PilotError(f"pilot manifest invalid: {detail}")
    authorised, auth_detail, _ = validate_authorisation(authorisation_path, manifest)
    if not authorised:
        raise PilotError(f"pilot is not authorised: {auth_detail}")
    freeze = candidate_fn()
    blockers = [item for item in freeze.get("blockers", [])
                if item not in AUTHORISATION_BLOCKERS]
    if blockers:
        raise PilotError("candidate has launch blockers: " + "; ".join(blockers))
    campaign_root = campaign_root.resolve()
    if campaign_root.is_relative_to(ROOT.resolve()) and not campaign_root.is_relative_to(
            (ROOT / "pilot-runs").resolve()):
        raise PilotError("campaign output inside the repository must stay under ignored pilot-runs/")
    campaign_root.mkdir(parents=True, exist_ok=True)
    state_path = campaign_root / "campaign-state.json"
    identity = {"manifest_sha256": manifest["manifest_sha256"],
                "authorisation_sha256": file_sha256(authorisation_path)}
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if any(state.get(key) != value for key, value in identity.items()):
            raise PilotError("existing campaign state belongs to another manifest or authorisation")
    else:
        state = {"schema_version": 1, **identity, "status": "running", "episodes": {}}
        evaluation_runner.atomic_json(state_path, state)
    runner = runner_factory(campaign_root / "episodes")
    for row in manifest["episodes"]:
        episode_id = row["episode_id"]
        prior = state["episodes"].get(episode_id)
        if prior and prior.get("complete") is True:
            continue
        state["current_episode"] = episode_id
        evaluation_runner.atomic_json(state_path, state)
        result = runner.run(evaluation_live_episode.LiveEpisodeSpec(
            episode_id=episode_id, task_id=row["task_id"], policy_id=row["policy_id"],
            budget_usd=row["budget_usd"],
        ))
        integrity = _episode_integrity(campaign_root, episode_id)
        complete = bool(
            result.get("stage") == "complete" and result.get("event_chain_valid") is True
            and integrity["identity_valid"] and integrity["accounting_complete"]
            and integrity["oracle_unchanged"]
        )
        state["episodes"][episode_id] = {"complete": complete, "summary": result,
                                          "integrity": integrity}
        state.pop("current_episode", None)
        evaluation_runner.atomic_json(state_path, state)
        if not complete:
            state["status"] = "stopped"
            state["stop_reason"] = f"episode {episode_id} failed a stop condition"
            evaluation_runner.atomic_json(state_path, state)
            return state
    state["status"] = "completed"
    state["known_episode_spend_usd"] = round(sum(
        item["integrity"]["spent_usd"] for item in state["episodes"].values()), 9)
    evaluation_runner.atomic_json(state_path, state)
    return state


class _FakePilotRunner:
    def __init__(self, root: Path):
        self.root = root
        self.calls: list[str] = []

    def run(self, spec: evaluation_live_episode.LiveEpisodeSpec) -> dict:
        self.calls.append(spec.episode_id)
        base = self.root / spec.episode_id
        base.mkdir(parents=True)
        budget = DispatchBudget(base / "dispatch-budget.json", spec.budget_usd)
        ident = f"fake-{spec.episode_id}"
        budget.reserve(ident, 0.1, 0.01, {"episode_id": spec.episode_id})
        budget.start(ident)
        budget.settle(ident, 0.01, final=True,
                      telemetry={"status": "completed"}, evidence="offline-pilot-fixture")
        state = {"history": [{"identity_valid": True}],
                 "grade": {"oracle_unchanged": True}, "learning_eligible": True}
        evaluation_runner.atomic_json(base / "state.json", state)
        return {"stage": "complete", "event_chain_valid": True,
                "grade": {"accepted": True}, "stop_reason": None}


def run_qualification(work: Path) -> dict:
    candidate = {
        "candidate_sha256": "a" * 64, "source_revision": "offline",
        "source_dirty": False, "bundle": {"version": "offline"},
        "isolation": {"evidence_sha256": "b" * 64},
        "blockers": ["paid pilot has not been authorised"],
    }
    candidate_fn = lambda: json.loads(json.dumps(candidate))
    runs = {}
    for profile in PROFILES.values():
        manifest = pilot_manifest(candidate_fn, profile)
        profile_root = work / profile.key
        profile_root.mkdir(parents=True)
        manifest_path = profile_root / "manifest.json"
        evaluation_runner.atomic_json(manifest_path, manifest)
        authorisation = {
            "schema_version": 1, "decision": "approved",
            "candidate_sha256": manifest["candidate_sha256"],
            "manifest_sha256": manifest["manifest_sha256"],
            "maximum_authorised_usd": profile.total_ceiling_usd,
            "approved_at": "qualification-clock", "approved_by": "offline-fixture",
        }
        authorisation_path = profile_root / "authorisation.json"
        evaluation_runner.atomic_json(authorisation_path, authorisation)
        campaign = profile_root / "campaign"
        result = execute(manifest_path, authorisation_path, campaign, profile=profile,
                         candidate_fn=candidate_fn, runner_factory=_FakePilotRunner)
        resumed = execute(manifest_path, authorisation_path, campaign, profile=profile,
                          candidate_fn=candidate_fn, runner_factory=_FakePilotRunner)
        runs[profile.key] = {
            "profile": profile, "manifest": manifest, "authorisation": authorisation,
            "authorisation_path": authorisation_path, "result": result, "resumed": resumed,
        }
    checkpoint = runs[CHECKPOINT_PROFILE.key]
    continuation = runs[CONTINUATION_PROFILE.key]
    development = runs[DEVELOPMENT_PROFILE.key]
    reserved = runs[RESERVED_PROFILE.key]
    tampered = dict(continuation["authorisation"],
                    maximum_authorised_usd=CONTINUATION_PROFILE.total_ceiling_usd + 1)
    tampered_path = work / "tampered.json"
    evaluation_runner.atomic_json(tampered_path, tampered)
    checks = {
        "fixed_six_episode_matrix": [(row["task_id"], row["policy_id"])
                                     for row in checkpoint["manifest"]["episodes"]] == [
            (task, policy) for task in ("D01", "D11") for policy in ("B0", "B1", "B2")],
        "fixed_eighteen_episode_matrix": [(row["task_id"], row["policy_id"])
                                          for row in continuation["manifest"]["episodes"]] == [
            (task, policy) for task in ("D03", "D05", "D07", "D08", "D09", "D10")
            for policy in ("B0", "B1", "B2")],
        "fixed_thirty_two_episode_matrix": [
            (row["task_id"], row["policy_id"], row["repetition"])
            for row in development["manifest"]["episodes"]
        ] == [
            (task, policy, 1)
            for index, task in enumerate(DEVELOPMENT_PROFILE.tasks)
            for policy in (("B0", "B1") if index % 2 == 0 else ("B1", "B0"))
        ] + [
            (task, policy, 2)
            for index, task in enumerate(DEVELOPMENT_PROFILE.repeat_tasks,
                                         start=len(DEVELOPMENT_PROFILE.tasks))
            for policy in (("B0", "B1") if index % 2 == 0 else ("B1", "B0"))
        ],
        "development_repetitions_are_predeclared": [
            row["task_id"] for row in development["manifest"]["episodes"]
            if row["repetition"] == 2 and row["policy_id"] == "B0"
        ] == ["D03", "D05", "D07", "D11"],
        "development_arm_order_alternates": [
            tuple(row["policy_id"] for row in development["manifest"]["episodes"][offset:offset + 2])
            for offset in range(0, 32, 2)
        ] == [("B0", "B1") if pair % 2 == 0 else ("B1", "B0") for pair in range(16)],
        "fixed_forty_eight_episode_matrix": [
            (row["task_id"], row["policy_id"], row["repetition"])
            for row in reserved["manifest"]["episodes"]
        ] == [
            (task, policy, repetition)
            for repetition in (1, 2)
            for index, task in enumerate(RESERVED_PROFILE.tasks)
            for policy in (("B0", "B1") if (index + (repetition - 1) * 12) % 2 == 0
                           else ("B1", "B0"))
        ],
        "reserved_tasks_repeat_exactly_twice": all(
            sum(row["task_id"] == task and row["repetition"] == repetition
                for row in reserved["manifest"]["episodes"]) == 2
            for task in RESERVED_PROFILE.tasks for repetition in (1, 2)
        ),
        "reserved_arm_order_alternates": [
            tuple(row["policy_id"] for row in reserved["manifest"]["episodes"][offset:offset + 2])
            for offset in range(0, 48, 2)
        ] == [("B0", "B1") if pair % 2 == 0 else ("B1", "B0") for pair in range(24)],
        "fixed_cost_ceilings": (
            checkpoint["manifest"]["cost"]["episode_total_cap_usd"] == 24.0
            and checkpoint["manifest"]["cost"]["combined_authorisation_ceiling_usd"] == 26.0
            and continuation["manifest"]["cost"]["episode_total_cap_usd"] == 72.0
            and continuation["manifest"]["cost"]["combined_authorisation_ceiling_usd"] == 74.0
            and development["manifest"]["cost"]["episode_total_cap_usd"] == 128.0
            and development["manifest"]["cost"]["combined_authorisation_ceiling_usd"] == 140.0
            and reserved["manifest"]["cost"]["episode_total_cap_usd"] == 192.0
            and reserved["manifest"]["cost"]["combined_authorisation_ceiling_usd"] == 200.0
        ),
        "exact_authorisation_required": validate_authorisation(
            continuation["authorisation_path"], continuation["manifest"])[0]
        and not validate_authorisation(tampered_path, continuation["manifest"])[0],
        "authorisation_cannot_cross_profiles": not validate_authorisation(
            checkpoint["authorisation_path"], continuation["manifest"])[0]
        and not validate_authorisation(checkpoint["authorisation_path"], development["manifest"])[0],
        "offline_campaigns_complete_once": all(
            run["result"]["status"] == "completed"
            and len(run["result"]["episodes"]) == len(run["profile"].episodes)
            and run["result"]["known_episode_spend_usd"]
            == round(len(run["profile"].episodes) * 0.01, 9)
            for run in runs.values()
        ),
        "resume_does_not_repeat_completed_episodes": all(
            run["resumed"]["known_episode_spend_usd"]
            == run["result"]["known_episode_spend_usd"] for run in runs.values()
        ),
    }
    return {
        "schema_version": 2, "mode": "offline-paid-evaluation-preflight-v2",
        "offline_only": True, "model_calls": 0,
        "result": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "limits": [
            "Qualification uses a fake runner and makes no provider calls.",
            "The real launcher remains disabled until exact operator authorisation exists.",
        ],
    }


def render_report(value: dict, title: str) -> str:
    lines = [f"# {title}", "", f"Result: **{value['result']}**. Model calls: **0**.", "",
             "| Check | Result |", "| :--- | :--- |"]
    lines.extend(f"| {name.replace('_', ' ')} | {'pass' if passed else 'fail'} |"
                 for name, passed in value["checks"].items())
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in value["limits"])
    return "\n".join(lines) + "\n"


def write_preparation(manifest_path: Path, report_path: Path,
                      candidate_fn: Callable[[], dict] = evaluation_freeze.candidate,
                      profile: PilotProfile = CHECKPOINT_PROFILE) -> dict:
    value = pilot_manifest(candidate_fn, profile)
    evaluation_runner.atomic_json(manifest_path, value)
    lines = [
        f"# {profile.title}", "",
        f"Candidate: `{value['candidate_sha256']}`.", "",
        f"The fixed package runs {profile.description}.",
        f"{len(profile.episodes)} episode reservations cap model spend at **USD "
        f"{profile.episode_total_usd:.0f}**. Separate calibration headroom is **USD "
        f"{profile.calibration_headroom_usd:.0f}**, so the requested combined ceiling is "
        f"**USD {profile.total_ceiling_usd:.0f}**.", "",
        "No paid call starts without an approval file matching this manifest and candidate.", "",
    ]
    if profile is CONTINUATION_PROFILE:
        lines.extend([
            "## Measured cost context", "",
            "The completed six-episode checkpoint averaged USD 0.0232061 per first-rung",
            "episode. A floor-only extrapolation for these 18 episodes is USD 0.417710.",
            "The planning range is **USD 1-22** because these harder tasks can invoke Opus",
            "fallbacks or the approximately USD 2.99 historical quick Controller path.",
            "The USD 74 ceiling remains authoritative; the range is not a billing limit.", "",
            "## Outbound data and destination", "",
            "Execution sends the synthetic D03, D05 and D07-D10 fixture issue prompts,",
            "public checks, source files read by an agent and runtime observations to",
            "Anthropic through the local Claude CLI. Task calls request Claude Sonnet 5 or",
            "Claude Opus 5. B2 can also invoke the frozen read-only Controller roles.", "",
        ])
    if profile is DEVELOPMENT_PROFILE:
        projection = value["cost"]["measured_projection"]
        lines.extend([
            "## Measured cost context", "",
            f"The policy-mean pilot extrapolation is **USD {projection['point_estimate_usd']:.9f}**.",
            f"Applying the highest single pilot episode to all 32 episodes gives **USD "
            f"{projection['observed_max_extrapolation_usd']:.9f}**. The pilot is small, so both",
            "figures are planning evidence rather than billing limits. The exact USD 140",
            "ceiling remains authoritative because every episode retains its USD 4",
            "failure-path allowance and USD 12 remains separate campaign headroom.", "",
            "## Outbound data and destination", "",
            "Execution sends the synthetic D01-D12 fixture issues, public checks, source",
            "files read by an agent and runtime observations to Anthropic through the local",
            "Claude CLI. Task calls request Claude Sonnet 5 or Claude Opus 5. B1 can invoke",
            "the frozen read-only Controller roles when its observable trigger fires.", "",
            "## Scheduling", "",
            "Episodes run serially in adjacent task pairs. The first policy alternates by",
            "pair to reduce time-order bias. D03, D05, D07 and D11 repeats are fixed before",
            "execution and cannot be selected from favourable first-run outcomes.", "",
        ])
    if profile is RESERVED_PROFILE:
        projection = value["cost"]["measured_projection"]
        lines.extend([
            "## Measured cost context", "",
            f"The W07 policy-mean extrapolation is **USD {projection['point_estimate_usd']:.9f}**.",
            f"Applying the highest W07 episode to all 48 episodes gives **USD "
            f"{projection['observed_max_extrapolation_usd']:.9f}**. Reserved tasks differ",
            "from development tasks, so both figures are planning evidence rather than",
            "billing limits. The exact USD 200 ceiling remains authoritative.", "",
            "## Outbound data and destination", "",
            "Execution sends the synthetic H01-H12 fixture issues, public checks, source",
            "files read by an agent and runtime observations to Anthropic through the local",
            "Claude CLI. B0 and B1 remain frozen; no reserved outcome may change them.", "",
            "## Scheduling", "",
            "Each reserved task runs twice under both policies. Episodes run serially in",
            "adjacent pairs and alternate which policy runs first. The full schedule is",
            "fixed before any reserved outcome is inspected.", "",
        ])
    lines.extend(["| # | Task | Policy | Repetition | Episode cap |",
                  "| -: | :--- | :--- | ---: | ---: |"])
    lines.extend(f"| {row['sequence']} | {row['task_id']} | {row['policy_id']} | "
                 f"{row['repetition']} | USD {row['budget_usd']:.2f} |"
                 for row in value["episodes"])
    lines.extend(["", "## Stop conditions", ""])
    lines.extend(f"- {item}." for item in value["stop_conditions"])
    lines.extend(["", "## Required operator decision", "",
                  f"Approve or reject this exact USD {profile.total_ceiling_usd:.0f} package.", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return value


def validate_evidence(path: Path) -> tuple[bool, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read pilot preflight evidence: {exc}"
    recorded = value.pop("evidence_sha256", None)
    checks = value.get("checks") or {}
    ok = bool(recorded == digest(value) and value.get("result") == "PASS"
              and value.get("offline_only") is True and value.get("model_calls") == 0
              and value.get("implementation_sha256") == file_sha256(Path(__file__))
              and len(checks) == 13 and all(checks.values()))
    return ok, f"mode={value.get('mode')}; digest={'valid' if recorded == digest(value) else 'invalid'}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--qualify", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--profile", choices=tuple(PROFILES), default=CHECKPOINT_PROFILE.key)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--authorisation", type=Path)
    parser.add_argument("--campaign-root", type=Path)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--evidence-report", type=Path, default=DEFAULT_EVIDENCE_REPORT)
    args = parser.parse_args(argv)
    profile = PROFILES[args.profile]
    default_manifest, default_report, default_authorisation, default_campaign = PROFILE_PATHS[profile.key]
    args.manifest = args.manifest or default_manifest
    args.report = args.report or default_report
    args.authorisation = args.authorisation or default_authorisation
    args.campaign_root = args.campaign_root or default_campaign
    if args.prepare:
        value = write_preparation(args.manifest, args.report, profile=profile)
        print(f"prepared {len(value['episodes'])} episodes; maximum authorised USD "
              f"{profile.total_ceiling_usd:.2f}")
        return 0
    if args.qualify:
        with tempfile.TemporaryDirectory(prefix="pilot-preflight-") as folder:
            value = run_qualification(Path(folder))
        value.update({"recorded_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                      "host": platform.node(), "implementation_sha256": file_sha256(Path(__file__))})
        args.evidence_report.write_text(
            render_report(value, "Paid evaluation preflight qualification"),
                                        encoding="utf-8", newline="\n")
        value["report"] = {"path": args.evidence_report.relative_to(ROOT).as_posix(),
                           "sha256": file_sha256(args.evidence_report)}
        value["evidence_sha256"] = digest(value)
        evaluation_runner.atomic_json(args.evidence, value)
        print(f"{value['result']}: paid evaluation preflight, 0 model calls")
        return 0 if value["result"] == "PASS" else 1
    if args.check:
        ok, detail = validate_evidence(args.evidence)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    result = execute(args.manifest, args.authorisation, args.campaign_root, profile=profile)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
