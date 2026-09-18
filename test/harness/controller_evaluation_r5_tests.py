#!/usr/bin/env python3
"""R5 offline evaluation-foundation checks; zero provider calls."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_evaluation as subject  # noqa: E402
import controller_corpus  # noqa: E402
import controller_matrix_runtime  # noqa: E402
import controller_pilot_runtime  # noqa: E402
import acceptance  # noqa: E402
import controller_control  # noqa: E402
import controller_dispatch  # noqa: E402
import controller_integrity  # noqa: E402
import controller_policy  # noqa: E402
import system_controller  # noqa: E402
import dispatch_budget  # noqa: E402


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS {name}")


def main() -> int:
    contract = subject.load_contract()
    blueprints = subject.task_blueprints(contract)
    check("48-blueprints", len(blueprints) == 48)
    check("24-per-split", {split: sum(row["split"] == split for row in blueprints)
                           for split in ("development", "reserved")}
          == {"development": 24, "reserved": 24})
    check("16-suitable-per-split", all(sum(row["split"] == split and row["suitable"]
                                             for row in blueprints) == 16
                                         for split in ("development", "reserved")))
    check("reserved-mechanisms-differ", all(len({row["mechanism"] for row in blueprints
                                                   if row["family_id"] == family["id"]}) == 4
                                             for family in contract["families"]))

    vignettes = subject.routing_vignettes(contract)
    recorded = [json.loads(line) for line in subject.VIGNETTES_PATH.read_text(encoding="utf-8").splitlines()]
    check("60-vignettes", len(vignettes) == 60 and recorded == vignettes)
    check("five-per-family", all(sum(row["family_id"] == family["id"] for row in vignettes) == 5
                                 for family in contract["families"]))

    matrix = json.loads(subject.MATRIX_MANIFEST.read_text(encoding="utf-8"))
    check("15-cells-four-calls", all(sum(row["cell"] == cell for row in matrix["episodes"]) == 4
                                      for cell in {row["cell"] for row in matrix["episodes"]}))
    check("all-effortful-shapes", all({row["shape"] for row in matrix["episodes"]
                                        if row["cell"] == cell and row["kind"] == "microtask"}
                                       == set(contract["calibration"]["microtask_shapes"])
                                       for cell in {row["cell"] for row in matrix["episodes"]}))
    pilot = json.loads(subject.PILOT_MANIFEST.read_text(encoding="utf-8"))
    check("pilot-six-by-three", len(pilot["episodes"]) == 18
          and len({row["task_id"] for row in pilot["episodes"]}) == 6)
    check("four-auto-controller-entries", sum(row["automatic_controller_expected"]
                                               for row in pilot["episodes"]) == 4)

    approved = {"schema_version": 1, "decision": "approved",
                "manifest_sha256": matrix["manifest_sha256"],
                "maximum_authorised_usd": 48.75,
                "approved_at": "fixture-clock", "approved_by": "offline-test"}
    check("exact-authorisation", subject.validate_authorisation(approved, matrix))
    check("tampered-authorisation-rejected",
          not subject.validate_authorisation(dict(approved, maximum_authorised_usd=121.0), matrix))

    partial = subject.score_quality({"semantic_outcome": "useful-partial",
                                     "components": {"M": .25, "E": .8, "D": .8, "N": .8, "H": 1.0},
                                     "critical_violation": False, "completion_claim": "partial"})
    critical = subject.score_quality({"semantic_outcome": "critical-violation",
                                      "components": {name: 1.0 for name in subject.COMPONENTS},
                                      "critical_violation": True, "completion_claim": "complete"})
    check("partial-progress-retained", partial["quality"] == 60.0 and not partial["false_success"])
    check("critical-gate-dominates", critical["quality"] == 0.0 and critical["raw_quality"] == 100.0)

    corpus = controller_corpus.load_corpus()
    check("48-generated-task-packages", len(corpus["tasks"]) == 48)
    corpus_qualification = controller_corpus.qualify()
    check("all-288-labelled-variants", corpus_qualification["result"] == "PASS"
          and not corpus_qualification["variant_failures"])
    with tempfile.TemporaryDirectory(prefix="r5-actor-") as raw:
        actor = Path(raw) / "actor"
        task = corpus["tasks"][0]
        controller_corpus.materialise(task, actor)
        check("actor-package-is-public-only", {path.name for path in actor.iterdir()}
              == {"issue.md", "task.json", "observations.json", "public_check.py"}
              and "accepted_actions" not in "".join(path.read_text(encoding="utf-8")
                                                      for path in actor.iterdir()))
        wrong = task["variants"]["confident-wrong"]
        (actor / "result.json").write_text(json.dumps(wrong), encoding="utf-8")
        public = subprocess.run([sys.executable, "public_check.py"], cwd=actor,
                                capture_output=True, text=True, timeout=30)
        hidden = controller_corpus.grade_task(task, wrong)
        check("public-pass-does-not-imply-hidden-pass", public.returncode == 0
              and not hidden["accepted"] and hidden["false_success"])
        check("oracle-never-materialised", not any("oracle" in path.name for path in actor.iterdir()))

    with tempfile.TemporaryDirectory(prefix="r5-tamper-") as raw:
        tampered_path = Path(raw) / "corpus.json"
        tampered = json.loads(controller_corpus.CORPUS_PATH.read_text(encoding="utf-8"))
        tampered["tasks"][0]["oracle"]["accepted_actions"] = ["unsafe"]
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        try:
            controller_corpus.load_corpus(tampered_path)
            rejected = False
        except controller_corpus.CorpusError:
            rejected = True
        check("corpus-tampering-rejected", rejected)

    def fake_stream(model: str, cost: float = 0.01) -> str:
        rows = [
            {"type": "assistant", "parent_tool_use_id": None,
             "message": {"model": model, "content": []}},
            {"type": "result", "subtype": "success", "result": "fixture-result",
             "total_cost_usd": cost,
             "usage": {"input_tokens": 10, "output_tokens": 5},
             "modelUsage": {model: {"costUSD": cost}}},
        ]
        return "\n".join(json.dumps(row) for row in rows) + "\n"

    observed_commands = []
    def fake_transport(command, cwd, env, timeout):
        observed_commands.append(command)
        model = command[command.index("--model") + 1]
        return subprocess.CompletedProcess(command, 0, fake_stream(model), "")

    with tempfile.TemporaryDirectory(prefix="r5-matrix-") as raw:
        root = Path(raw)
        auth = dict(approved, maximum_authorised_usd=48.75)
        auth_path = root / "authorisation.json"
        auth_path.write_text(json.dumps(auth), encoding="utf-8")
        state = controller_matrix_runtime.execute(
            subject.MATRIX_MANIFEST, auth_path, root / "run",
            controller_matrix_runtime.MatrixAdapter(fake_transport))
        check("matrix-fake-run-completes-once", state["status"] == "completed"
              and len(state["episodes"]) == 60 and state["known_spend_usd"] == 0.6)
        check("matrix-exercises-all-cell-flags", len({
            (command[command.index("--model") + 1], command[command.index("--effort") + 1])
            for command in observed_commands}) == 15)
        before = len(observed_commands)
        resumed = controller_matrix_runtime.execute(
            subject.MATRIX_MANIFEST, auth_path, root / "run",
            controller_matrix_runtime.MatrixAdapter(fake_transport))
        check("matrix-replay-is-free", resumed["status"] == "completed"
              and len(observed_commands) == before)

    class RaisingAdapter:
        def __init__(self): self.calls = 0
        def run(self, episode, cwd):
            self.calls += 1
            raise RuntimeError("fixture interruption")

    with tempfile.TemporaryDirectory(prefix="r5-matrix-crash-") as raw:
        root = Path(raw)
        auth_path = root / "authorisation.json"
        auth_path.write_text(json.dumps(dict(approved, maximum_authorised_usd=48.75)),
                             encoding="utf-8")
        raising = RaisingAdapter()
        first = controller_matrix_runtime.execute(subject.MATRIX_MANIFEST, auth_path,
                                                   root / "run", raising)
        second = controller_matrix_runtime.execute(subject.MATRIX_MANIFEST, auth_path,
                                                    root / "run", raising)
        check("matrix-interruption-never-replays", first["status"] == second["status"] == "stopped"
              and raising.calls == 1 and "without replay" in second["stop_reason"])

    runner = system_controller.LiveRoleRunner(
        ROOT, lambda: 4.0, role_profile="frontier-candidate")
    check("frontier-profile-reaches-live-role-runner",
          runner.cells["framer"] == ("fable", "xhigh")
          and runner.cells["critic"] == ("fable", "max")
          and runner.cells["selector"] == ("opus", "medium"))

    class CaptureController:
        def __init__(self): self.request = None
        def run(self, request):
            self.request = request
            return {"terminal": False, "outcome": "error", "cost_usd": 0.0,
                    "accounting_complete": False, "reserved_usd": request.allowance_usd,
                    "controller_run_dir": None, "evidence_packet": None,
                    "error": "offline boundary fixture"}

    with tempfile.TemporaryDirectory(prefix="r5-frontier-") as raw:
        project = Path(raw)
        (project / "input.txt").write_text("stable", encoding="utf-8")
        problem = "Inspect a consequential premise conflict."
        revision = acceptance.revision(project)
        task_revision = controller_policy.derive_task_revision(problem, project, revision)
        assessment = {
            "assessment_version": 1, "task_revision": task_revision,
            "consequence": "consequential", "premise_uncertainty": "contradictory",
            "alternatives": "several-material", "constraint_coupling": "cross-module",
            "verification_gap": "incomplete-checks", "observed_failure_cause": "premise-conflict",
            "required_output": "investigation", "evidence_availability": "available",
            "deadline": None, "authorised_task_budget_usd": 8.0,
            "evidence": [{"id": "e1", "provenance": "repository-artefact",
                          "observed_at": "fixture", "scope": "input",
                          "claim": "material premises conflict", "material": True}],
        }
        control = controller_control.ControlDecision("auto", "shipped-default", 0,
                                                     task_revision, "r5-frontier")
        decision = controller_policy.decide(
            assessment, control, controller_profile="frontier-candidate")
        contract = {"criteria": ["evidence recorded"], "constraints": ["no unsafe edits"]}
        acceptance_state = {"contract": contract,
                            "contract_digest": controller_integrity.digest(contract)}
        capture = CaptureController()
        controller_dispatch.TaskDispatcher(project, capture).dispatch(
            decision, problem_text=problem, acceptance_state=acceptance_state,
            input_revision=revision)
        check("frontier-profile-crosses-dispatch-boundary",
              capture.request is not None
              and capture.request.controller_profile == "frontier-candidate")

    corpus_by_id = {row["task_id"]: row for row in controller_corpus.load_corpus()["tasks"]}
    class FakePilotWorker:
        def __init__(self): self.calls = 0
        def run(self, request):
            self.calls += 1
            task_id = json.loads((request.actor_root / "task.json").read_text(encoding="utf-8"))["task_id"]
            reference = corpus_by_id[task_id]["variants"]["reference"]
            (request.actor_root / "result.json").write_text(json.dumps(reference), encoding="utf-8")
            resolved = __import__("model_registry").resolve_cell(request.requested_cell)
            return {"status": "completed", "terminal": True, "timed_out": False,
                    "result": "fixture", "returncode": 0,
                    "requested_cell": request.requested_cell,
                    "expected_model": resolved["expected_provider_model"],
                    "actual_model": resolved["expected_provider_model"], "identity_valid": True,
                    "effort_evidence": f"cli-argument:{resolved['effort']}",
                    "usage": {}, "cost_usd": 0.01, "root_models": [], "child_models": [],
                    "billed_models": [], "auxiliary_billed_models": [], "stream": {},
                    "started_at": "fixture", "finished_at": "fixture", "wall_clock_s": 0.0,
                    "stderr_tail": "", "command_contract": {}}

    class FakePilotController:
        def __init__(self): self.calls = 0; self.profiles = []
        def run(self, request):
            self.calls += 1
            self.profiles.append(request.controller_profile)
            run_dir = request.project / "runs" / ("dispatch-" + request.invocation_id.replace("controller-", ""))
            run_dir.mkdir(parents=True)
            (run_dir / "REPORT.md").write_text("fixture report\n", encoding="utf-8")
            (run_dir / "ledger.jsonl").write_text("{}\n", encoding="utf-8")
            artefacts = [{"path": name,
                          "sha256": controller_dispatch._sha256(run_dir / name),
                          "size": (run_dir / name).stat().st_size}
                         for name in ("REPORT.md", "ledger.jsonl")]
            identity = {"project": controller_integrity.digest(str(request.project.resolve())),
                        "revision": request.input_revision}
            packet = {
                "packet_version": 1, "task_revision": request.task_revision,
                "task_digest": controller_integrity.digest(request.problem_text),
                "acceptance_contract_digest": request.acceptance_state["contract_digest"],
                "acceptance_source": "external",
                "input_snapshot_digest": controller_integrity.digest(identity),
                "outcome": "solution", "readiness": "verified-ready",
                "premise_ids": ["prem-001"], "candidate_ids": ["cand-001"],
                "verified_findings": [{"premise_id": "prem-001", "text": "fixture fact",
                                       "source": "observations.json", "confidence": 1.0}],
                "rejected_hypotheses": [], "remaining_uncertainties": [],
                "safe_next_action": "write result.json and run public_check.py",
                "operator_question": None, "artefacts": artefacts,
                "accounting": {"known_spend_usd": 0.01, "reserved_usd": 0.0,
                               "accounting_complete": True},
            }
            packet["packet_digest"] = controller_integrity.digest(packet)
            (run_dir / "controller-evidence.json").write_text(json.dumps(packet), encoding="utf-8")
            inner = dispatch_budget.DispatchBudget(run_dir / "dispatch-budget.json", request.allowance_usd)
            inner.reserve("role-1", 0.01, 0.0, {})
            inner.start("role-1")
            inner.settle("role-1", 0.01, final=True, telemetry={}, evidence="fixture")
            return {"terminal": True, "outcome": "solution", "cost_usd": 0.01,
                    "accounting_complete": True, "reserved_usd": 0.0,
                    "controller_run_dir": str(run_dir.resolve()),
                    "evidence_packet": packet, "error": None}

    with tempfile.TemporaryDirectory(prefix="r5-pilot-") as raw:
        root = Path(raw)
        pilot_manifest = json.loads(subject.PILOT_MANIFEST.read_text(encoding="utf-8"))
        pilot_manifest.update(execution_enabled=True, launch_readiness="authorisation-required",
                              blockers=["operator authorisation is absent"])
        unsigned = {key: value for key, value in pilot_manifest.items() if key != "manifest_sha256"}
        pilot_manifest["manifest_sha256"] = subject.digest(unsigned)
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(pilot_manifest), encoding="utf-8")
        pilot_auth = {"schema_version": 1, "decision": "approved",
                      "manifest_sha256": pilot_manifest["manifest_sha256"],
                      "maximum_authorised_usd": 144.0,
                      "approved_at": "fixture", "approved_by": "offline-test"}
        auth_path = root / "authorisation.json"
        auth_path.write_text(json.dumps(pilot_auth), encoding="utf-8")
        fake_worker, fake_controller = FakePilotWorker(), FakePilotController()
        executor = controller_pilot_runtime.PilotEpisodeExecutor(fake_worker, fake_controller)
        pilot_state = controller_pilot_runtime.execute(manifest_path, auth_path,
                                                       root / "run", executor)
        check("pilot-fake-run-completes-once", pilot_state["status"] == "completed"
              and len(pilot_state["episodes"]) == 18)
        check("pilot-four-automatic-controller-entries", fake_controller.calls == 4)
        check("pilot-frontier-and-standard-profiles", set(fake_controller.profiles)
              == {"standard", "frontier-candidate"})
        handoff_count = sum(row["controller_handoff_used"]
                            for row in pilot_state["episodes"].values())
        check("pilot-controller-handoffs-reach-workers", handoff_count == 4)
        calls_before = (fake_worker.calls, fake_controller.calls)
        replay = controller_pilot_runtime.execute(manifest_path, auth_path, root / "run", executor)
        check("pilot-replay-is-free", replay["status"] == "completed"
              and calls_before == (fake_worker.calls, fake_controller.calls))

        class RaisingEpisode:
            def __init__(self): self.calls = 0
            def run(self, task, episode, episode_root):
                self.calls += 1
                raise RuntimeError("fixture interruption")
        raising_episode = RaisingEpisode()
        try:
            controller_pilot_runtime.execute(manifest_path, auth_path,
                                             root / "crash-run", raising_episode)
        except RuntimeError:
            pass
        recovered = controller_pilot_runtime.execute(manifest_path, auth_path,
                                                      root / "crash-run", raising_episode)
        check("pilot-interruption-never-replays", recovered["status"] == "stopped"
              and raising_episode.calls == 1 and "without replay" in recovered["stop_reason"])

    qualification = subject.qualify()
    check("offline-qualification", qualification["result"] == "PASS"
          and qualification["model_calls"] == 0 and all(qualification["checks"].values()))
    print("controller evaluation R5 foundation: 33/33 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
