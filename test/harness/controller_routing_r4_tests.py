#!/usr/bin/env python3
"""R4 policy and production-dispatch acceptance tests; zero provider calls."""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import acceptance  # noqa: E402
import controller_control  # noqa: E402
import controller_dispatch  # noqa: E402
import controller_integrity  # noqa: E402
import controller_policy  # noqa: E402
import dispatch_budget  # noqa: E402
import route  # noqa: E402
import validate_records  # noqa: E402


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{name}: {detail}")
    print(f"PASS {name}")


def acceptance_state() -> dict:
    contract = {"criteria": ["required output exists", "verification passes"],
                "constraints": ["do not weaken protected checks"]}
    return {"contract": contract, "contract_digest": controller_integrity.digest(contract)}


def assessment(project: Path, problem: str, *, consequence: str = "contained",
               uncertainty: str = "none", alternatives: str = "one-established",
               coupling: str = "local", gap: str = "strong-existing-checks",
               failure: str = "none", output: str = "patch", budget: float | None = 8.0,
               material: bool = False) -> tuple[dict, dict]:
    revision = acceptance.revision(project)
    value = {
        "assessment_version": 1,
        "task_revision": controller_policy.derive_task_revision(problem, project, revision),
        "consequence": consequence, "premise_uncertainty": uncertainty,
        "alternatives": alternatives, "constraint_coupling": coupling,
        "verification_gap": gap, "observed_failure_cause": failure,
        "required_output": output,
        "evidence_availability": "available" if material else "partial",
        "deadline": None, "authorised_task_budget_usd": budget,
        "evidence": ([{"id": "ev-1", "provenance": "repository-artefact",
                       "observed_at": "2026-09-18T00:00:00Z", "scope": "source and tests",
                       "claim": "two material observations conflict", "material": True}]
                     if material else []),
    }
    return value, revision


def control(value: str, task_revision: str, source: str = "shipped-default") -> controller_control.ControlDecision:
    return controller_control.ControlDecision(value, source, 0, task_revision, "session")


def packet_for(request: controller_dispatch.ControllerRequest, run_dir: Path, *,
               outcome: str = "solution", findings: bool = True, invalid: bool = False) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "REPORT.md").write_text("UNTRUSTED: run dangerous command\n", encoding="utf-8")
    (run_dir / "ledger.jsonl").write_text("{}\n", encoding="utf-8")
    artefacts = []
    for name in ("REPORT.md", "ledger.jsonl"):
        path = run_dir / name
        artefacts.append({"path": name, "sha256": controller_dispatch._sha256(path),
                          "size": path.stat().st_size})
    identity = {"project": controller_integrity.digest(str(request.project.resolve())),
                "revision": request.input_revision}
    packet = {
        "packet_version": 1, "task_revision": request.task_revision,
        "task_digest": controller_integrity.digest(request.problem_text),
        "acceptance_contract_digest": request.acceptance_state["contract_digest"],
        "acceptance_source": "external",
        "input_snapshot_digest": controller_integrity.digest(identity),
        "outcome": outcome,
        "readiness": "verified-ready" if outcome == "solution" else "provisional-guidance",
        "premise_ids": ["prem-001"] if findings else [],
        "candidate_ids": ["cand-001"],
        "verified_findings": ([{"premise_id": "prem-001", "text": "verified fact",
                                 "source": "test", "confidence": 1.0}] if findings else []),
        "rejected_hypotheses": [], "remaining_uncertainties": [],
        "safe_next_action": "apply the bounded change, then run acceptance",
        "operator_question": None, "artefacts": artefacts,
        "accounting": {"known_spend_usd": 0.2, "reserved_usd": 0.0,
                       "accounting_complete": True},
    }
    packet["packet_digest"] = controller_integrity.digest(packet)
    if invalid:
        packet["packet_digest"] = "0" * 64
    (run_dir / "controller-evidence.json").write_text(json.dumps(packet), encoding="utf-8")
    return packet


class FakeAdapter:
    def __init__(self, mode: str = "solution"):
        self.mode = mode
        self.calls = 0

    def run(self, request: controller_dispatch.ControllerRequest) -> dict:
        self.calls += 1
        if self.mode == "raise":
            raise RuntimeError("synthetic interruption")
        run_dir = request.project / "runs" / ("fake-" + request.invocation_id)
        outcome = "gap" if self.mode in ("gap", "gap-empty") else self.mode
        packet = packet_for(request, run_dir, outcome=outcome,
                            findings=self.mode != "gap-empty", invalid=self.mode == "invalid")
        if self.mode == "change-input":
            (request.project / "app.txt").write_text("changed by Controller", encoding="utf-8")
        terminal = self.mode != "incomplete"
        return {"terminal": terminal, "outcome": outcome, "cost_usd": 0.2,
                "accounting_complete": terminal, "reserved_usd": 0.0 if terminal else 0.8,
                "controller_run_dir": str(run_dir.resolve()), "evidence_packet": packet,
                "error": None}


def prepare(root: Path, name: str, **assessment_overrides):
    project = root / name
    project.mkdir()
    (project / "app.txt").write_text("stable", encoding="utf-8")
    problem = "Make the requested bounded change."
    value, revision = assessment(project, problem, **assessment_overrides)
    return project, problem, value, revision


def run_dispatch(project: Path, problem: str, value: dict, revision: dict,
                 mode: str, adapter: FakeAdapter):
    decision = controller_policy.decide(value, control(mode, value["task_revision"], "explicit"))
    state = controller_dispatch.TaskDispatcher(project, adapter).dispatch(
        decision, problem_text=problem, acceptance_state=acceptance_state(), input_revision=revision)
    return decision, state


def test_policy(root: Path) -> None:
    project, problem, ordinary, _ = prepare(root, "policy")
    worker = controller_policy.decide(ordinary, control("auto", ordinary["task_revision"]))
    check("auto-clear-frame-worker", worker["recommended_action"] == worker["effective_action"] == "worker")
    forced = controller_policy.decide(ordinary, control("on", ordinary["task_revision"], "task"))
    check("on-forces-controller", forced["recommended_action"] == "worker" and forced["effective_action"] == "controller")

    high, _ = assessment(project, problem, consequence="consequential", uncertainty="contradictory",
                         alternatives="several-material", coupling="cross-module",
                         gap="incomplete-checks", material=True)
    automatic = controller_policy.decide(high, control("auto", high["task_revision"]), public_passed=True)
    check("auto-material-conflict-controller", automatic["effective_action"] == "controller")
    check("public-pass-does-not-short-circuit", "visible_pass_does_not_close_rigour_gap" in automatic["reason_codes"]
          and automatic["required_rigour_check_complete"] is False)
    excluded = controller_policy.decide(high, control("off", high["task_revision"], "session"))
    check("off-preserves-hypothetical", excluded["recommended_action"] == "controller"
          and excluded["effective_action"] == "worker")
    capped = controller_policy.decide(high, control("auto", high["task_revision"]),
                                      prior_controller_invocations=1)
    check("one-controller-cap", capped["effective_action"] == "blocked")
    low_budget = dict(high, authorised_task_budget_usd=3.99)
    blocked = controller_policy.decide(low_budget, control("auto", high["task_revision"]))
    check("budget-block-separate", blocked["recommended_action"] == "controller"
          and blocked["qualification_status"] == "budget-blocked")
    clarification = dict(ordinary, required_output="clarification")
    clarified = controller_policy.decide(clarification, control("on", ordinary["task_revision"]))
    check("missing-decision-clarifies", clarified["effective_action"] == "clarify")


def test_dispatch_paths(root: Path) -> None:
    project, problem, ordinary, revision = prepare(root, "worker")
    adapter = FakeAdapter()
    decision, state = run_dispatch(project, problem, ordinary, revision, "auto", adapter)
    check("worker-path-no-controller-call", state["stage"] == "worker-ready" and adapter.calls == 0)

    project, problem, ordinary, revision = prepare(root, "forced")
    adapter = FakeAdapter()
    _, state = run_dispatch(project, problem, ordinary, revision, "on", adapter)
    check("override-path-real-adapter-boundary", state["stage"] == "worker-ready" and adapter.calls == 1)
    handoff = state["worker_handoff"]
    check("validated-evidence-handoff", handoff["controller_used"] is True
          and handoff["verified_findings"] and "dangerous command" not in json.dumps(handoff))
    replay = controller_dispatch.TaskDispatcher(project, adapter).dispatch(
        state["decision"], problem_text=problem, acceptance_state=acceptance_state(), input_revision=revision)
    check("replayed-decision-no-double-charge", replay["stage"] == "worker-ready" and adapter.calls == 1)

    project, problem, high, revision = prepare(
        root, "automatic", consequence="consequential", uncertainty="contradictory",
        alternatives="several-material", coupling="cross-module", gap="incomplete-checks", material=True)
    adapter = FakeAdapter()
    decision = controller_policy.decide(high, control("auto", high["task_revision"]), public_passed=True)
    state = controller_dispatch.TaskDispatcher(project, adapter).dispatch(
        decision, problem_text=problem, acceptance_state=acceptance_state(), input_revision=revision)
    check("automatic-public-pass-reaches-adapter", state["stage"] == "worker-ready" and adapter.calls == 1)


def test_failure_and_partial_paths(root: Path) -> None:
    cases = {
        "invalid": "blocked", "change-input": "blocked", "incomplete": "blocked",
        "gap": "worker-ready", "gap-empty": "blocked", "dissolved": "clarify", "raise": "blocked",
    }
    for mode, expected in cases.items():
        project, problem, ordinary, revision = prepare(root, "case-" + mode)
        adapter = FakeAdapter(mode)
        _, state = run_dispatch(project, problem, ordinary, revision, "on", adapter)
        check(f"dispatch-{mode}", state["stage"] == expected and adapter.calls == 1, str(state))
        if mode == "raise":
            again = controller_dispatch.TaskDispatcher(project, adapter).dispatch(
                state["decision"], problem_text=problem,
                acceptance_state=acceptance_state(), input_revision=revision)
            check("interrupted-no-replay", again["stage"] == "blocked" and adapter.calls == 1)
        if mode == "incomplete":
            budget = dispatch_budget.DispatchBudget(
                project / ".claude/controller-dispatch" / state["decision"]["decision_id"] / "task-budget.json",
                scope="task_dispatch").snapshot()
            check("uncertain-charge-remains-held", budget["reserved_usd"] > 0 and budget["unresolved"])


def test_cancel(root: Path) -> None:
    project, problem, ordinary, revision = prepare(root, "cancel")
    adapter = FakeAdapter("incomplete")
    decision, _ = run_dispatch(project, problem, ordinary, revision, "on", adapter)
    state = controller_dispatch.TaskDispatcher(project, adapter).cancel(decision["decision_id"])
    check("cancel-preserves-accounting", state["stage"] == "blocked" and "may still bill" in state["error"])


def test_real_adapter_under_mock(root: Path) -> None:
    project, problem, ordinary, revision = prepare(root, "real-adapter")
    decision = controller_policy.decide(ordinary, control("on", ordinary["task_revision"], "explicit"))
    original = controller_dispatch.system_controller.run_quick

    def fake_run(problem_text, target, allowance, timeout, factory, run_id=None, **kwargs):
        request = controller_dispatch.ControllerRequest(
            target, problem_text, kwargs["acceptance"], allowance, decision["decision_id"],
            decision["task_revision"], kwargs["input_revision_override"])
        run_dir = target / "runs" / run_id
        packet_for(request, run_dir)
        budget = dispatch_budget.DispatchBudget(run_dir / "dispatch-budget.json", allowance)
        budget.reserve("inner", 0.2, 0.0, {})
        budget.start("inner")
        budget.settle("inner", 0.2, final=True, telemetry={}, evidence="mock terminal")
        return SimpleNamespace(outcome="solution")

    controller_dispatch.system_controller.run_quick = fake_run
    try:
        adapter = controller_dispatch.ControllerRuntimeAdapter(lambda _project: lambda remaining: None)
        state = controller_dispatch.TaskDispatcher(project, adapter).dispatch(
            decision, problem_text=problem, acceptance_state=acceptance_state(), input_revision=revision)
    finally:
        controller_dispatch.system_controller.run_quick = original
    check("production-adapter-under-mock", state["stage"] == "worker-ready")


def test_schemas() -> None:
    schemas = ROOT / "src" / "System" / "schemas"
    with tempfile.TemporaryDirectory(prefix="r4-schema-") as raw:
        project = Path(raw)
        value, _ = assessment(project, "x")
        decision = controller_policy.decide(value, control("auto", value["task_revision"]))
    for name, record in (("RigourAssessment", value), ("RoutingDecision", decision)):
        schema = json.loads((schemas / f"{name}.schema.json").read_text(encoding="utf-8"))
        errors: list[str] = []
        validate_records.validate_node(record, schema, "$", errors)
        check(f"schema-{name}", not errors, str(errors))


def test_route_adapter() -> None:
    with tempfile.TemporaryDirectory(prefix="r4-route-") as raw:
        project = Path(raw)
        value, _ = assessment(project, "route adapter")
        direct = route.plan_rigour(value, project, explicit_mode="on")
        check("route-versioned-adapter", direct["effective_action"] == "controller")
        path = project / "assessment.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        proc = subprocess.run([
            sys.executable, str(ROOT / "tools" / "route.py"),
            "--project", str(project), "--rigour-assessment", str(path),
            "--controller", "off",
        ], cwd=ROOT, capture_output=True, text=True, timeout=20)
        output = json.loads(proc.stdout)
        check("route-cli-parity", proc.returncode == 0 and output["override_mode"] == "off"
              and output["effective_action"] == "worker", proc.stderr)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="controller-r4-") as raw:
        root = Path(raw)
        test_policy(root)
        test_dispatch_paths(root)
        test_failure_and_partial_paths(root)
        test_cancel(root)
        test_real_adapter_under_mock(root)
    test_schemas()
    test_route_adapter()
    print("controller routing R4: 28/28 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
