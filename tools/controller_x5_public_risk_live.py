#!/usr/bin/env python3
"""Single-use public-success review comparisons with bounded paid calls."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

import controller_campaign_manifest
import controller_dispatch
import controller_evaluation
import controller_workflow
import controller_x5_public_risk_corpus as corpus
import controller_x5_public_risk_review as review
import controller_x5_v6_screen as screen
import controller_x5_v7_pilot as v7
import model_registry
import dispatch_budget
import task_executor
from controller_wsl_interpreter import WslPublicInterpreter
from controller_x5_recovery_isolation import hidden_evaluation_tree
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import GRAFT, MCP, NODE, Q3WslAdapter, isolated_public_runner


ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "K01"
SOURCE = corpus.CASE / "actor"
RUN_DIR = ROOT / "test/results/2026-09-30-controller-x5-public-risk-k01-run"
SCOPE = "K01 development public-success review: one producer and conditional matched S/A calls"
RECOVERY_SCOPE = "K01 accepted-producer recovery: no producer replay, one matched S/A review each"
ORIGINAL_MANIFEST = ROOT / "test/results/2026-09-30-controller-x5-public-risk-k01-manifest.json"
FIRST_RECOVERY_MANIFEST = ROOT / "test/results/2026-09-30-controller-x5-public-risk-k01-recovery-manifest.json"
PER_ROOT_USD = 5.0
MAXIMUM_USD = 20.0
ASSESSMENT_USD = 0.5


def configure_case(case_id: str) -> None:
    """Select one frozen case before constructing any manifest or root."""
    global CASE_ID, SOURCE, RUN_DIR, SCOPE
    if case_id not in {"K01", "K02"}:
        raise PilotStop("unknown public-risk case")
    CASE_ID = case_id
    if case_id == "K02":
        SOURCE = corpus.CASE_K02 / "actor"
        RUN_DIR = ROOT / "test/results/2026-09-30-controller-x5-public-risk-k02-run"
        SCOPE = "K02 development public-success review: one producer and conditional matched S/A calls"


class PilotStop(RuntimeError):
    """A frozen, single-use, or accounting boundary cannot be proved."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise PilotStop(f"missing or redirected record: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def task() -> dict:
    catalogue_path = corpus.CATALOGUE if CASE_ID == "K01" else corpus.CATALOGUE_K02
    expected = corpus.freeze() if CASE_ID == "K01" else corpus.freeze_k02()
    catalogue = load(catalogue_path)
    if catalogue != expected:
        raise PilotStop("frozen public-risk catalogue differs from source or oracle")
    return catalogue["case"]


def freeze() -> dict:
    row = task()
    catalogue_path = corpus.CATALOGUE if CASE_ID == "K01" else corpus.CATALOGUE_K02
    body = {"schema_version": 1, "stage": f"x5-public-risk-{CASE_ID.lower()}-development",
            "case": CASE_ID, "effect_unit": True,
            "catalogue_sha256": load(catalogue_path)["catalogue_sha256"],
            "actor_files": row["actor_files"], "editable_paths": row["editable_paths"],
            "oracle_sha256": row["oracle_sha256"],
            "risk_digest": row["risk_digest"],
            "negative_controls": (["C01", "M01"] if CASE_ID == "K01"
                                  else ["C02", "M02"]),
            "schedule": ["B0", "S-if-accepted", "A-if-S-qualified", "grade-after-both"],
            "worker_policy": "one Sonnet-low producer and one Sonnet-low review call per arm",
            "per_root_maximum_usd": PER_ROOT_USD,
            "maximum_authorised_usd": MAXIMUM_USD,
            "assessment_allowance_usd": ASSESSMENT_USD,
            "controller_profile": "standard", "controller_invocations_per_A": 1,
            "eligibility": "one settled, writer-stopped, public-passed B0 attempt and frozen risk",
            "stop_rule": "stop on uncertainty, source drift, replay or invalid identity",
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "host": controller_campaign_manifest.host_record(),
            "credential_method": "claude-code-wsl-subscription"}
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def freeze_recovery() -> dict:
    """Bind a new runtime to the already settled producer; never rerun it."""
    if CASE_ID != "K01":
        raise PilotStop("recovery belongs only to the stopped K01 producer")
    prior = load(ORIGINAL_MANIFEST)
    old_digest = prior.get("manifest_sha256")
    if (not isinstance(old_digest, str)
            or controller_evaluation.digest({key: value for key, value in prior.items()
                                             if key != "manifest_sha256"}) != old_digest):
        raise PilotStop("original manifest is not self-consistent")
    row = task()
    if (prior.get("catalogue_sha256") != load(corpus.CATALOGUE)["catalogue_sha256"]
            or prior.get("actor_files") != row["actor_files"]
            or prior.get("oracle_sha256") != row["oracle_sha256"]
            or prior.get("risk_digest") != row["risk_digest"]):
        raise PilotStop("original producer source differs from frozen case")
    state = entry(prior, "B0").status(root_id(prior, "B0"))
    checked = review.qualify(actor_path(prior, "B0"), set(row["actor_files"]),
                             state, row["risk"], row["risk_digest"],
                             isolated_public_runner(row))
    snapshot = load(RUN_DIR / "pair/snapshot.json")
    stable = ("actor_sha256", "producer_root_id", "producer_cost_usd",
              "producer_receipt_digest", "risk_digest", "next_worker_cell")
    if any(snapshot.get(key) != checked.get(key) for key in stable):
        raise PilotStop("saved twins do not belong to the settled producer")
    for arm in ("S", "A"):
        for name, expected in snapshot["actor_sha256"].items():
            path = RUN_DIR / "pair" / arm / name
            if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
                raise PilotStop("saved twin bytes changed")
    summary = load(RUN_DIR / "edit-summary.json")
    if (summary.get("manifest_sha256") != old_digest
            or sha(summary.get("summary", "").encode()) != summary.get("sha256")):
        raise PilotStop("producer edit summary changed")
    concise_edit_summary()
    base = freeze()
    body = {key: value for key, value in base.items() if key != "manifest_sha256"}
    body.update(stage="x5-public-risk-k01-accepted-recovery",
                source_manifest_sha256=old_digest,
                source_snapshot_digest=controller_evaluation.digest(snapshot),
                producer_receipt_digest=checked["producer_receipt_digest"],
                producer_cost_usd=checked["producer_cost_usd"],
                schedule=["recover-accepted-root", "S", "A", "grade-after-both"],
                eligibility="the original accepted root and exact twins are requalified without a producer call")
    if (RUN_DIR / "producer-result.json").is_file():
        predecessor = load(FIRST_RECOVERY_MANIFEST)
        predecessor_digest = predecessor.get("manifest_sha256")
        prior_result = load(RUN_DIR / "producer-result.json")
        if (not isinstance(predecessor_digest, str)
                or controller_evaluation.digest({key: value for key, value in predecessor.items()
                                                 if key != "manifest_sha256"}) != predecessor_digest
                or predecessor.get("source_manifest_sha256") != old_digest
                or prior_result.get("manifest_sha256") != predecessor_digest
                or prior_result.get("snapshot") != snapshot
                or prior_result.get("qualified") is not True):
            raise PilotStop("first recovery record is not bound to the accepted root")
        body["source_recovery_manifest_sha256"] = predecessor_digest
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def gate(manifest: dict, notice: dict) -> None:
    recovery = manifest.get("stage") == "x5-public-risk-k01-accepted-recovery"
    if manifest != (freeze_recovery() if recovery else freeze()):
        raise PilotStop("manifest or host/source package changed")
    if (notice.get("approved") is not True
            or notice.get("manifest_sha256") != manifest["manifest_sha256"]
            or notice.get("maximum_usd") != MAXIMUM_USD
            or notice.get("scope") != (RECOVERY_SCOPE if recovery else SCOPE)
            or notice.get("date") != dt.datetime.now(dt.timezone.utc).date().isoformat()
            or notice.get("approval_source") != "user approved all planned tests on 2026-09-30"):
        raise PilotStop("dated cost notice does not authorise this manifest")


def actor_path(manifest: dict, arm: str) -> Path:
    if arm not in {"B0", "S", "A"}:
        raise PilotStop("unknown arm")
    source = manifest.get("source_manifest_sha256", manifest["manifest_sha256"])
    return SEEDS / f"x5-public-risk-{source[:12]}-{CASE_ID.lower()}-{arm.lower()}"


def root_id(manifest: dict, arm: str) -> str:
    source = manifest.get("source_manifest_sha256", manifest["manifest_sha256"])
    return controller_evaluation.digest(
        {"manifest": source, "case": CASE_ID, "arm": arm})[:24]


def verify_actor(manifest: dict, arm: str) -> None:
    expected = (manifest["actor_files"] if arm == "B0"
                else load(RUN_DIR / "pair/snapshot.json")["actor_sha256"])
    actor = actor_path(manifest, arm)
    for name, digest in expected.items():
        path = actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != digest:
            raise PilotStop(f"public actor differs before dispatch: {arm}/{name}")
    if CASE_ID == "K02" and arm in {"S", "A"}:
        review_record = load(RUN_DIR / "review-goal.json")
        goal = actor / "REVIEW.md"
        if (goal.is_symlink() or not goal.is_file()
                or sha(goal.read_bytes()) != review_record["review_goal_sha256"]):
            raise PilotStop("review goal differs before dispatch")


def copy_actor(manifest: dict, arm: str, files: dict[str, bytes]) -> None:
    actor = actor_path(manifest, arm)
    if actor.exists() or actor.is_symlink():
        raise PilotStop("single-use actor path already exists")
    actor.mkdir(mode=0o700)
    for name, data in files.items():
        path = actor / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def build_controller_graph(actor: Path) -> None:
    config = actor / ".mcp.json"
    config.write_bytes(MCP.read_bytes())
    config.chmod(0o600)
    graph = subprocess.run([str(NODE), str(GRAFT), "build", str(actor)], cwd=actor,
                           capture_output=True, text=True, timeout=120, check=False)
    if graph.returncode or not (actor / "graft").is_dir():
        raise PilotStop("Controller Graft preflight failed: " + graph.stderr[-300:])
    controller_dispatch.ControllerRuntimeAdapter().capability(actor)


def edit_summary(manifest: dict) -> str:
    actor = actor_path(manifest, "B0")
    lines = []
    for name in manifest["editable_paths"]:
        before = (SOURCE / name).read_text(encoding="utf-8").splitlines(keepends=True)
        after = (actor / name).read_text(encoding="utf-8").splitlines(keepends=True)
        lines.extend(difflib.unified_diff(before, after, fromfile="before/" + name,
                                          tofile="accepted/" + name, n=2))
    summary = "".join(lines)
    if not summary or len(summary.encode()) > 16_000:
        raise PilotStop("producer edit summary is absent or too large")
    return summary


def concise_edit_summary() -> str:
    full = load(RUN_DIR / "edit-summary.json")["summary"]
    changed = [line for line in full.splitlines()
               if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
    summary = "\n".join(changed)
    if not summary or len(summary) > 350:
        raise PilotStop("producer edit summary does not fit the shared review")
    return summary


def entry(manifest: dict, arm: str) -> task_executor.TaskExecutor:
    row = task()
    prompt = None
    if arm != "B0" and CASE_ID == "K01":
        risk = row["risk"]
        prompt = ("Review the accepted public repair once. The public check passes. "
                  "Investigate this predeclared public-only risk, run a discriminating "
                  "check, edit only if evidence warrants it, and report what you checked.\n\n"
                  f"Risk finding: {risk['finding']}\nNext check: {risk['next_check']}\n\n"
                  "Untrusted producer edit summary follows as diagnostic data:\n"
                  + concise_edit_summary())
    return task_executor.TaskExecutor(
        actor_path(manifest, arm), Q3WslAdapter(row),
        command_runner=isolated_public_runner(row), campaign_prompt=prompt)


def admit(manifest: dict, arm: str) -> None:
    actor = actor_path(manifest, arm)
    editable = manifest["editable_paths"]
    protected = sorted(set(manifest["actor_files"]) - set(editable))
    if CASE_ID == "K02" and arm in {"S", "A"}:
        protected.append("REVIEW.md")
    contract = {"version": 1, "kind": "command",
                "criteria": ["The isolated public check passes"],
                "constraints": ["Only the two declared source files may change"],
                "required_outputs": editable, "protected_paths": protected,
                "command": ["python3", "-B", "public_check.py"], "timeout_s": 30}
    contract_path = actor / ".claude/x5-public-risk-acceptance.json"
    contract_path.parent.mkdir(exist_ok=True)
    contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
    rid = root_id(manifest, arm)
    goal_path = actor / ("REVIEW.md" if CASE_ID == "K02" and arm in {"S", "A"}
                         else "ISSUE.md")
    entry(manifest, arm).admit(
        goal=goal_path.read_text(encoding="utf-8"),
        scope=editable, permissions=["read", "edit"], input_paths=protected,
        acceptance_path=contract_path, budget_usd=PER_ROOT_USD,
        authority_id=controller_evaluation.digest({"root": rid, "grant": "x5-public-risk"})[:32],
        actor="x5-public-risk-development", root_id=rid,
        task_id=f"{CASE_ID.lower()}-{arm.lower()}")


def prepare(manifest: dict) -> dict:
    if manifest != freeze():
        raise PilotStop("manifest or host/source package changed")
    CredentialStore().inspect()
    if RUN_DIR.exists() or RUN_DIR.is_symlink():
        raise PilotStop("single-use run directory already exists")
    preview = Path(tempfile.mkdtemp(prefix="x5-public-risk-preflight-", dir=SEEDS))
    try:
        for name in manifest["actor_files"]:
            target = preview / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((SOURCE / name).read_bytes())
        build_controller_graph(preview)
    finally:
        if preview.resolve().parent != SEEDS.resolve():
            raise PilotStop("preflight cleanup path escaped seed root")
        shutil.rmtree(preview)
    RUN_DIR.mkdir(parents=True)
    copy_actor(manifest, "B0", {name: (SOURCE / name).read_bytes()
                                for name in manifest["actor_files"]})
    admit(manifest, "B0")
    exclusive(RUN_DIR / "prepared.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "producer_root_id": root_id(manifest, "B0"), "provider_calls": 0})
    return {"producer_root_id": root_id(manifest, "B0"), "provider_calls": 0}


def recover(manifest: dict) -> dict:
    if manifest != freeze_recovery():
        raise PilotStop("recovery manifest or settled producer changed")
    if (RUN_DIR / "producer-result.json").exists() or (RUN_DIR / "S-started.json").exists():
        raise PilotStop("recovery or paid review already started")
    snapshot = load(RUN_DIR / "pair/snapshot.json")
    s_actor = actor_path(manifest, "S")
    a_actor = actor_path(manifest, "A")
    if a_actor.exists() or a_actor.is_symlink():
        raise PilotStop("A root already exists")
    for name, expected in snapshot["actor_sha256"].items():
        path = s_actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != expected:
            raise PilotStop("S actor differs from accepted twin")
    if (s_actor / ".claude/task-executor-v2/project-registry.json").exists():
        raise PilotStop("S root was already admitted")
    files = {name: (RUN_DIR / "pair/A" / name).read_bytes()
             for name in snapshot["actor_sha256"]}
    copy_actor(manifest, "A", files)
    build_controller_graph(a_actor)
    admit(manifest, "S")
    admit(manifest, "A")
    prior = load(ORIGINAL_MANIFEST)
    state = entry(prior, "B0").status(root_id(prior, "B0"))
    result = {"manifest_sha256": manifest["manifest_sha256"],
              "source_manifest_sha256": prior["manifest_sha256"],
              "root_id": root_id(manifest, "B0"), "state": state["state"],
              "budget": state["budget"], "attempt_count": len(state["attempts"]),
              "eligible": True, "qualified": True, "snapshot": snapshot,
              "error": None, "recovered_after_setup_error": True,
              "provider_calls_during_recovery": 0}
    exclusive(RUN_DIR / "producer-result.json", result)
    return {"producer_root_id": result["root_id"],
            "settled_producer_usd": state["budget"]["spent_usd"],
            "successors_admitted": ["S", "A"],
            "provider_calls_during_recovery": 0}


def require_ready(manifest: dict, arm: str) -> task_executor.TaskExecutor:
    executor = entry(manifest, arm)
    state = executor.status(root_id(manifest, arm))
    if (state["state"] != "ready" or state["attempts"]
            or state["budget"]["spent_usd"] != 0
            or state["budget"]["unresolved"]
            or state["budget"]["limit_usd"] != PER_ROOT_USD):
        raise PilotStop("single-use root is not ready")
    return executor


def prepare_successors(manifest: dict, state: dict) -> dict:
    row = task()
    record = review.twins(
        actor_path(manifest, "B0"), set(manifest["actor_files"]), state,
        row["risk"], manifest["risk_digest"], RUN_DIR / "pair",
        isolated_public_runner(row))
    summary = edit_summary(manifest)
    exclusive(RUN_DIR / "edit-summary.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "sha256": sha(summary.encode()), "summary": summary})
    if CASE_ID == "K02":
        review_record = review.write_review_goals(
            RUN_DIR / "pair", row["risk"], manifest["risk_digest"],
            concise_edit_summary())
        exclusive(RUN_DIR / "review-goal.json",
                  {"manifest_sha256": manifest["manifest_sha256"],
                   "review_goal_sha256": review_record["review_goal_sha256"],
                   "review_goal_bytes": review_record["review_goal_bytes"]})
    for arm in ("S", "A"):
        files = {name: (RUN_DIR / "pair" / arm / name).read_bytes()
                 for name in record["actor_sha256"]}
        if {name: sha(data) for name, data in files.items()} != record["actor_sha256"]:
            raise PilotStop("successor snapshot changed")
        copy_actor(manifest, arm, files)
        if CASE_ID == "K02":
            (actor_path(manifest, arm) / "REVIEW.md").write_bytes(
                (RUN_DIR / "pair" / arm / "REVIEW.md").read_bytes())
        if arm == "A":
            build_controller_graph(actor_path(manifest, arm))
        admit(manifest, arm)
    return record


def producer(manifest: dict, notice: dict) -> dict:
    gate(manifest, notice)
    if manifest.get("stage") != f"x5-public-risk-{CASE_ID.lower()}-development":
        raise PilotStop("a recovered producer must never be replayed")
    if load(RUN_DIR / "prepared.json")["manifest_sha256"] != manifest["manifest_sha256"]:
        raise PilotStop("prepared producer differs from manifest")
    executor = require_ready(manifest, "B0")
    verify_actor(manifest, "B0")
    CredentialStore().inspect()
    exclusive(RUN_DIR / "producer-started.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "root_id": root_id(manifest, "B0")})
    start = time.monotonic()
    error = None
    snapshot = None
    try:
        state = executor.run(root_id(manifest, "B0"), stop_after_attempts=1)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:400]
        state = executor.status(root_id(manifest, "B0"))
    if error is None and state["state"] == "accepted":
        try:
            snapshot = prepare_successors(manifest, state)
        except (review.ReviewStop, PilotStop) as exc:
            error = str(exc)
    eligible = snapshot is not None
    qualified = (error is None and eligible and not state["budget"]["unresolved"]
                 and not state["budget"]["breached"]
                 and state["budget"]["spent_usd"] <= PER_ROOT_USD)
    result = {"manifest_sha256": manifest["manifest_sha256"],
              "root_id": root_id(manifest, "B0"), "state": state["state"],
              "budget": state["budget"], "attempt_count": len(state["attempts"]),
              "eligible": eligible, "qualified": qualified,
              "snapshot": snapshot, "error": error,
              "elapsed_s": round(time.monotonic() - start, 3)}
    exclusive(RUN_DIR / "producer-result.json", result)
    return {"eligible": eligible, "qualified": qualified,
            "state": state["state"], "spent_usd": state["budget"]["spent_usd"],
            "error": error}


def assessment_inputs(actor: Path) -> dict:
    row = task()
    risk = row["risk"]
    issue_name = "REVIEW.md" if CASE_ID == "K02" else "ISSUE.md"
    issue = (actor / issue_name).read_text(encoding="utf-8")
    heading = next(line for line in issue.splitlines() if line.startswith("# "))
    if issue.count(heading) != 1:
        raise PilotStop("issue heading is not unique")
    sources = (["ISSUE.md", "trace.json", "key_feed.json", "public_check.py",
                "auth_gateway.py", "tenant_keys.py"] if CASE_ID == "K01" else
               ["REVIEW.md", "ISSUE.md", "trace.json", "gateway.py",
                "public_check.py", "payment_service.py", "retry_policy.py"])
    return {"issue": issue_name,
            "source_paths": sources,
            "quote_requests": [{"source": issue_name, "quote": heading},
                               {"source": risk["source"], "quote": risk["quote"]}],
            "operational": {"context_tokens": 1000, "deadline_seconds": None,
                            "prior_local_repairs": 1,
                            "required_artefacts": row["editable_paths"],
                            "deadline": None,
                            "authorised_task_budget_usd": PER_ROOT_USD,
                            "observed_at": dt.datetime.now(dt.timezone.utc).isoformat()}}


def actionable_handoff(dispatch: dict | None) -> bool:
    handoff = dispatch.get("worker_handoff") if isinstance(dispatch, dict) else None
    if not isinstance(handoff, dict) or handoff.get("controller_used") is not True:
        return False
    editable = set(task()["editable_paths"])
    findings = handoff.get("verified_findings")
    if not isinstance(findings, list) or not any(
            isinstance(item, dict) and isinstance(item.get("source"), str)
            and isinstance(item.get("text"), str) and item["text"].strip()
            and any(name in item["source"] for name in editable)
            for item in findings):
        return False
    action = handoff.get("safe_next_action")
    return (isinstance(action, str) and len(action.strip()) >= 25
            and "restore the frozen acceptance criteria" not in action.lower()
            and any(name in action for name in editable | {"public_check.py"}))


def continuation(manifest: dict, notice: dict, arm: str) -> dict:
    gate(manifest, notice)
    if arm not in {"S", "A"}:
        raise PilotStop("unknown successor arm")
    producer_result = load(RUN_DIR / "producer-result.json")
    allowed_producer_manifests = {manifest["manifest_sha256"]}
    if manifest.get("source_recovery_manifest_sha256"):
        allowed_producer_manifests.add(manifest["source_recovery_manifest_sha256"])
    if (producer_result.get("manifest_sha256") not in allowed_producer_manifests
            or producer_result.get("eligible") is not True
            or producer_result.get("qualified") is not True
            or producer_result.get("snapshot") != load(RUN_DIR / "pair/snapshot.json")):
        raise PilotStop("producer checkpoint or twin snapshot changed")
    if arm == "A" and load(RUN_DIR / "S-result.json").get("qualified") is not True:
        raise PilotStop("settled S result is required before A")
    executor = require_ready(manifest, arm)
    verify_actor(manifest, arm)
    actor = actor_path(manifest, arm)
    store = CredentialStore()
    store.inspect()
    if arm == "A":
        controller_dispatch.ControllerRuntimeAdapter().capability(actor)
    exclusive(RUN_DIR / f"{arm}-started.json",
              {"manifest_sha256": manifest["manifest_sha256"],
               "root_id": root_id(manifest, arm)})
    start = time.monotonic()
    environment = dict(os.environ)
    session_name = None
    session_open = False
    workflow = None
    error = None
    try:
        if arm == "A":
            session_name = "inv-" + uuid.uuid4().hex
            session = store.begin(session_name)
            clean = {key: value for key, value in os.environ.items()
                     if key not in {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                                    "CLAUDE_CODE_OAUTH_TOKEN", "WSLENV"}}
            clean["CLAUDE_CONFIG_DIR"] = str(session)
            clean["PATH"] = "/opt/orchestrator-worker-runtime/bin:" + clean.get("PATH", "")
            os.environ.clear()
            os.environ.update(clean)
            session_open = True
            worker = executor.adapter
            original_run = worker.run

            def run_worker(request):
                nonlocal session_open
                if session_open:
                    v7.settle_session(store, session_name)
                    session_open = False
                os.environ.pop("CLAUDE_CONFIG_DIR", None)
                try:
                    return original_run(request)
                finally:
                    os.environ["CLAUDE_CONFIG_DIR"] = str(session)

            worker.run = run_worker
        if arm == "S":
            executor.run(root_id(manifest, arm), stop_after_attempts=1)
        else:
            inputs = assessment_inputs(actor)
            interpreter = WslPublicInterpreter(
                distro="kali-linux", linux_user="wsl", claude_path=screen.CLAUDE,
                launcher_path=str(ROOT / "tools/controller_wsl_launch.py"),
                allowance_usd=ASSESSMENT_USD, runner=screen._local_runner)
            with hidden_evaluation_tree(ROOT):
                workflow = controller_workflow.execute(
                    executor, root_id(manifest, arm), interpreter=interpreter,
                    assessment_allowance_usd=ASSESSMENT_USD,
                    controller_adapter=controller_dispatch.ControllerRuntimeAdapter(),
                    explicit_mode="on", public_passed=True,
                    worker_attempt_limit=1,
                    defer_worker=CASE_ID == "K02", **inputs)
            if CASE_ID == "K02" and workflow is not None:
                decision = workflow.get("decision") or {}
                dispatch = workflow.get("dispatch")
                if (decision.get("effective_action") != "controller"
                        or not isinstance(dispatch, dict)
                        or dispatch.get("stage") != "worker-ready"
                        or not actionable_handoff(dispatch)):
                    error = "Controller handoff lacks a source-cited review action"
                elif workflow["task"]["state"] == "ready":
                    os.chdir("/")
                    workflow["task"] = executor.run(
                        root_id(manifest, arm), stop_after_attempts=1)
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:400]
    finally:
        if session_open:
            try:
                v7.settle_session(store, session_name)
                session_open = False
            except Exception as exc:
                error = (error + "; " if error else "") + "credential reconciliation: " + str(exc)[:250]
        os.environ.clear()
        os.environ.update(environment)
    state = executor.status(root_id(manifest, arm))
    decision = (state.get("routing_decision") or {}).get("decision") or {}
    dispatch = workflow.get("dispatch") if workflow else None
    actionable = actionable_handoff(dispatch) if arm == "A" else None
    role_budget = None
    if dispatch and dispatch.get("controller_result"):
        role_dir = Path(dispatch["controller_result"].get("controller_run_dir", ""))
        if role_dir.is_relative_to(actor) and (role_dir / "dispatch-budget.json").is_file():
            role_budget = dispatch_budget.DispatchBudget(
                role_dir / "dispatch-budget.json").snapshot()
    attempts = state["attempts"]
    identities_valid = all(
        (attempt.get("receipt") or {}).get("identity_valid") is True
        and model_registry.model_class_for_provider_id(
            (attempt.get("receipt") or {}).get("actual_model")) == "sonnet"
        and (attempt.get("receipt") or {}).get("writer_stopped") is True
        for attempt in attempts)
    qualified = (error is None and len(attempts) == 1 and identities_valid
                 and state["state"] == "accepted"
                 and not state["budget"]["unresolved"] and not state["budget"]["breached"]
                 and state["budget"]["spent_usd"] <= PER_ROOT_USD
                 and (arm == "S" or (
                     decision.get("effective_action") == "controller"
                     and dispatch is not None and dispatch.get("stage") == "worker-ready"
                     and dispatch.get("controller_invocations") == 1
                     and actionable is True and role_budget is not None
                     and not role_budget["unresolved"] and not role_budget["breached"])))
    result = {"manifest_sha256": manifest["manifest_sha256"], "arm": arm,
              "root_id": root_id(manifest, arm), "state": state["state"],
              "budget": state["budget"], "attempt_count": len(attempts),
              "effective_action": decision.get("effective_action"),
              "controller_stage": dispatch.get("stage") if dispatch else None,
              "controller_invocations": dispatch.get("controller_invocations") if dispatch else 0,
              "controller_handoff_actionable": actionable,
              "controller_role_cost_usd": role_budget["spent_usd"] if role_budget else None,
              "worker_identity_valid": identities_valid, "qualified": qualified,
              "error": error, "credential_reconciled": not session_open,
              "elapsed_s": round(time.monotonic() - start, 3)}
    exclusive(RUN_DIR / f"{arm}-result.json", result)
    return {"arm": arm, "state": state["state"],
            "spent_usd": state["budget"]["spent_usd"],
            "qualified": qualified, "error": error}


def protected_grade(manifest: dict, arm: str) -> dict:
    row = task()
    actor = actor_path(manifest, arm)
    protected = set(row["actor_files"]) - set(row["editable_paths"])
    for name in protected:
        path = actor / name
        if path.is_symlink() or not path.is_file() or sha(path.read_bytes()) != row["actor_files"][name]:
            raise PilotStop(f"protected actor source changed: {name}")
    before = {name: sha((actor / name).read_bytes()) for name in row["actor_files"]}
    oracle = ROOT / f"test/oracles/controller_x5_public_risk/{CASE_ID}_hidden.py"
    if sha(oracle.read_bytes()) != row["oracle_sha256"]:
        raise PilotStop("protected oracle changed")
    with tempfile.TemporaryDirectory(prefix=f"x5-{CASE_ID.lower()}-grade-", dir=SEEDS) as raw:
        copy = Path(raw) / "actor"
        copy.mkdir(mode=0o700)
        for name in row["actor_files"]:
            path = copy / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((actor / name).read_bytes())
        environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                       "PYTHONPATH": str(copy)}
        result = subprocess.run([sys.executable, "-B", str(oracle)], cwd=copy,
                                env=environment, capture_output=True, text=True,
                                timeout=30, check=False)
        if result.returncode not in {0, 1}:
            raise PilotStop("protected grader failed to execute: " + result.stderr[-250:])
        parsed = json.loads(result.stdout)
    if before != {name: sha((actor / name).read_bytes()) for name in row["actor_files"]}:
        raise PilotStop("candidate changed during protected grading")
    cases = parsed.get("cases")
    expected_cases = 8 if CASE_ID == "K01" else 5
    if (not isinstance(cases, list) or len(cases) != expected_cases
            or len({item.get("name") for item in cases if isinstance(item, dict)}) != expected_cases
            or any(not isinstance(item, dict) or type(item.get("passed")) is not bool
                   or type(item.get("critical")) is not bool
                   or type(item.get("weight")) is not int or item["weight"] <= 0
                   for item in cases)
            or (result.returncode == 0) != all(item["passed"] for item in cases)):
        raise PilotStop("protected grader returned an invalid result")
    passed = sum(item["weight"] for item in cases if item["passed"])
    total = sum(item["weight"] for item in cases)
    return {"case": CASE_ID, "arm": arm, "cases": cases,
            "quality": round(100 * passed / total, 3),
            "critical_errors": sum(item["critical"] and not item["passed"] for item in cases),
            "candidate_edit_sha256": {name: before[name] for name in row["editable_paths"]}}


def grade(manifest: dict) -> dict:
    if manifest != (freeze_recovery() if manifest.get("stage") ==
                    "x5-public-risk-k01-accepted-recovery" else freeze()):
        raise PilotStop("manifest or host/source package changed")
    for arm in ("B0", "S", "A"):
        result = load(RUN_DIR / ("producer-result.json" if arm == "B0" else f"{arm}-result.json"))
        expected_manifest = (manifest.get("source_recovery_manifest_sha256",
                                          manifest["manifest_sha256"])
                             if arm == "B0" else manifest["manifest_sha256"])
        if result.get("qualified") is not True or result.get("manifest_sha256") != expected_manifest:
            raise PilotStop("both review arms must settle before protected grading")
    if (RUN_DIR / "grade.json").exists():
        raise PilotStop("protected grade is single-use")
    grades = {arm: protected_grade(manifest, arm) for arm in ("B0", "S", "A")}
    uplift = grades["A"]["quality"] - grades["S"]["quality"]
    record = {"manifest_sha256": manifest["manifest_sha256"],
              "grades": grades, "uplift_points_A_minus_S": uplift,
              "critical_error_delta_A_minus_S": (grades["A"]["critical_errors"]
                                                - grades["S"]["critical_errors"]),
              "provisional_quality_gain": uplift > 0 and
              grades["A"]["critical_errors"] <= grades["S"]["critical_errors"]}
    exclusive(RUN_DIR / "grade.json", record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "freeze_recovery", "prepare",
                                         "recover", "producer", "continuation", "grade"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--notice", type=Path)
    parser.add_argument("--arm", choices=("S", "A"))
    parser.add_argument("--case", choices=("K01", "K02"), default="K01")
    args = parser.parse_args()
    configure_case(args.case)
    if os.name != "posix" or os.geteuid() != 0:
        raise PilotStop("development driver requires attested WSL root")
    if args.mode == "freeze":
        exclusive(args.manifest, freeze())
        result = {"manifest_sha256": load(args.manifest)["manifest_sha256"]}
    elif args.mode == "freeze_recovery":
        exclusive(args.manifest, freeze_recovery())
        result = {"manifest_sha256": load(args.manifest)["manifest_sha256"]}
    else:
        manifest = load(args.manifest)
        if args.mode == "prepare":
            result = prepare(manifest)
        elif args.mode == "recover":
            result = recover(manifest)
        elif args.mode == "grade":
            result = grade(manifest)
        else:
            if args.notice is None:
                raise PilotStop("paid mode requires an exact dated cost notice")
            notice = load(args.notice)
            if args.mode == "producer":
                result = producer(manifest, notice)
            else:
                if args.arm is None:
                    raise PilotStop("continuation needs S or A")
                result = continuation(manifest, notice, args.arm)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
