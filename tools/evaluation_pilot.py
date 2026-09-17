#!/usr/bin/env python3
"""Prepare, validate and execute the authorised six-episode live pilot.

Preparation and qualification make no model calls. Execution is unavailable
without an exact operator authorisation file bound to the current candidate
and manifest. The fixed six episode caps sum to USD 24; USD 2 of calibration
headroom is outside this launcher, giving a combined approval ceiling of USD 26.
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
DEFAULT_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-pilot-preflight.json"
DEFAULT_EVIDENCE_REPORT = ROOT / "test" / "results" / "2026-09-18-pilot-preflight.md"
EPISODE_BUDGET_USD = 4.0
EPISODE_TOTAL_USD = 24.0
CALIBRATION_HEADROOM_USD = 2.0
TOTAL_CEILING_USD = 26.0
EPISODES = tuple(
    (f"pilot-{index:02d}-{task.lower()}-{policy.lower()}", task, policy)
    for index, (task, policy) in enumerate(
        ((task, policy) for task in ("D01", "D11") for policy in ("B0", "B1", "B2")), 1
    )
)


class PilotError(RuntimeError):
    """The pilot is not authorised or cannot safely continue."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pilot_manifest(candidate_fn: Callable[[], dict] = evaluation_freeze.candidate) -> dict:
    freeze = candidate_fn()
    value = {
        "schema_version": 1,
        "campaign": "realworld-v1-six-episode-checkpoint",
        "candidate_sha256": freeze["candidate_sha256"],
        "source_revision": freeze["source_revision"],
        "bundle_version": freeze["bundle"]["version"],
        "isolation_evidence_sha256": freeze["isolation"]["evidence_sha256"],
        "cost": {
            "currency": "USD", "episode_count": len(EPISODES),
            "per_episode_cap_usd": EPISODE_BUDGET_USD,
            "episode_total_cap_usd": EPISODE_TOTAL_USD,
            "calibration_headroom_usd": CALIBRATION_HEADROOM_USD,
            "combined_authorisation_ceiling_usd": TOTAL_CEILING_USD,
            "basis": "six fixed episode reservations plus separate calibration headroom",
        },
        "episodes": [
            {"sequence": index, "episode_id": episode_id, "task_id": task_id,
             "policy_id": policy_id, "budget_usd": EPISODE_BUDGET_USD}
            for index, (episode_id, task_id, policy_id) in enumerate(EPISODES, 1)
        ],
        "stop_conditions": [
            "candidate, bundle, isolation or authorisation does not validate",
            "an episode stops with unresolved provider accounting",
            "a served task model does not match the exact required model",
            "the event chain, external grade or protected-oracle check is invalid",
            "the fixed USD 24 episode envelope or USD 26 combined ceiling would be exceeded",
        ],
        "review_after": "all six episodes complete, or immediately after the first stop condition",
    }
    value["manifest_sha256"] = digest(value)
    return value


def validate_manifest(path: Path, candidate_fn: Callable[[], dict] = evaluation_freeze.candidate,
                      *, require_clean: bool = True) -> tuple[bool, str, dict]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read pilot manifest: {exc}", {}
    recorded = value.pop("manifest_sha256", None)
    expected = pilot_manifest(candidate_fn)
    expected.pop("manifest_sha256", None)
    comparable_value = {key: item for key, item in value.items() if key != "source_revision"}
    comparable_expected = {key: item for key, item in expected.items() if key != "source_revision"}
    current = candidate_fn()
    valid = bool(
        recorded == digest(value) and comparable_value == comparable_expected
        and (not require_clean or current.get("source_dirty") is False)
        and len(value.get("episodes") or []) == 6
        and sum(row.get("budget_usd", 0) for row in value["episodes"]) == EPISODE_TOTAL_USD
        and (value.get("cost") or {}).get("combined_authorisation_ceiling_usd") == TOTAL_CEILING_USD
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
    valid = bool(
        value.get("schema_version") == 1 and value.get("decision") == "approved"
        and value.get("candidate_sha256") == manifest.get("candidate_sha256")
        and value.get("manifest_sha256") == manifest.get("manifest_sha256")
        and value.get("maximum_authorised_usd") == TOTAL_CEILING_USD
        and isinstance(value.get("approved_at"), str) and value["approved_at"].strip()
        and isinstance(value.get("approved_by"), str) and value["approved_by"].strip()
    )
    return valid, ("exact approval present" if valid else "approval does not match candidate, manifest and USD 26 ceiling"), value


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
            *, candidate_fn: Callable[[], dict] = evaluation_freeze.candidate,
            runner_factory: Callable[[Path], object] = evaluation_live_episode.LiveEpisodeRunner) -> dict:
    valid, detail, manifest = validate_manifest(manifest_path, candidate_fn)
    if not valid:
        raise PilotError(f"pilot manifest invalid: {detail}")
    authorised, auth_detail, _ = validate_authorisation(authorisation_path, manifest)
    if not authorised:
        raise PilotError(f"pilot is not authorised: {auth_detail}")
    freeze = candidate_fn()
    blockers = [item for item in freeze.get("blockers", [])
                if item != "paid pilot has not been authorised"]
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
    manifest = pilot_manifest(candidate_fn)
    manifest_path = work / "manifest.json"
    evaluation_runner.atomic_json(manifest_path, manifest)
    authorisation = {
        "schema_version": 1, "decision": "approved",
        "candidate_sha256": manifest["candidate_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "maximum_authorised_usd": TOTAL_CEILING_USD,
        "approved_at": "qualification-clock", "approved_by": "offline-fixture",
    }
    authorisation_path = work / "authorisation.json"
    evaluation_runner.atomic_json(authorisation_path, authorisation)
    campaign = work / "campaign"
    result = execute(manifest_path, authorisation_path, campaign,
                     candidate_fn=candidate_fn, runner_factory=_FakePilotRunner)
    tampered = dict(authorisation, maximum_authorised_usd=TOTAL_CEILING_USD + 1)
    tampered_path = work / "tampered.json"
    evaluation_runner.atomic_json(tampered_path, tampered)
    checks = {
        "fixed_six_episode_matrix": [(row["task_id"], row["policy_id"])
                                     for row in manifest["episodes"]] == [
            (task, policy) for task in ("D01", "D11") for policy in ("B0", "B1", "B2")],
        "fixed_cost_ceiling": manifest["cost"]["episode_total_cap_usd"] == 24.0
        and manifest["cost"]["combined_authorisation_ceiling_usd"] == 26.0,
        "exact_authorisation_required": validate_authorisation(authorisation_path, manifest)[0]
        and not validate_authorisation(tampered_path, manifest)[0],
        "offline_campaign_completes_once": result["status"] == "completed"
        and len(result["episodes"]) == 6 and result["known_episode_spend_usd"] == 0.06,
        "resume_does_not_repeat_completed_episodes": execute(
            manifest_path, authorisation_path, campaign,
            candidate_fn=candidate_fn, runner_factory=_FakePilotRunner,
        )["known_episode_spend_usd"] == 0.06,
    }
    return {
        "schema_version": 1, "mode": "offline-pilot-preflight-v1",
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
                      candidate_fn: Callable[[], dict] = evaluation_freeze.candidate) -> dict:
    value = pilot_manifest(candidate_fn)
    evaluation_runner.atomic_json(manifest_path, value)
    lines = [
        "# Six-episode paid pilot approval package", "",
        f"Candidate: `{value['candidate_sha256']}`.", "",
        "The fixed checkpoint runs D01 and D11 once under each policy B0, B1 and B2.",
        "Six episode reservations cap model spend at **USD 24**. Separate calibration",
        "headroom is **USD 2**, so the requested combined ceiling is **USD 26**.", "",
        "No paid call starts without an approval file matching this manifest and candidate.", "",
        "| # | Task | Policy | Episode cap |", "| -: | :--- | :--- | ---: |",
    ]
    lines.extend(f"| {row['sequence']} | {row['task_id']} | {row['policy_id']} | USD {row['budget_usd']:.2f} |"
                 for row in value["episodes"])
    lines.extend(["", "## Stop conditions", ""])
    lines.extend(f"- {item}." for item in value["stop_conditions"])
    lines.extend(["", "## Required operator decision", "",
                  "Choose the project licence, then approve or reject this exact USD 26 package.", ""])
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
              and len(checks) == 5 and all(checks.values()))
    return ok, f"mode={value.get('mode')}; digest={'valid' if recorded == digest(value) else 'invalid'}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--qualify", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--authorisation", type=Path, default=DEFAULT_AUTHORISATION)
    parser.add_argument("--campaign-root", type=Path, default=DEFAULT_CAMPAIGN_ROOT)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--evidence-report", type=Path, default=DEFAULT_EVIDENCE_REPORT)
    args = parser.parse_args(argv)
    if args.prepare:
        value = write_preparation(args.manifest, args.report)
        print(f"prepared {len(value['episodes'])} episodes; maximum authorised USD {TOTAL_CEILING_USD:.2f}")
        return 0
    if args.qualify:
        with tempfile.TemporaryDirectory(prefix="pilot-preflight-") as folder:
            value = run_qualification(Path(folder))
        value.update({"recorded_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                      "host": platform.node(), "implementation_sha256": file_sha256(Path(__file__))})
        args.evidence_report.write_text(render_report(value, "Paid pilot preflight qualification"),
                                        encoding="utf-8", newline="\n")
        value["report"] = {"path": args.evidence_report.relative_to(ROOT).as_posix(),
                           "sha256": file_sha256(args.evidence_report)}
        value["evidence_sha256"] = digest(value)
        evaluation_runner.atomic_json(args.evidence, value)
        print(f"{value['result']}: pilot preflight, 0 model calls")
        return 0 if value["result"] == "PASS" else 1
    if args.check:
        ok, detail = validate_evidence(args.evidence)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    result = execute(args.manifest, args.authorisation, args.campaign_root)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
