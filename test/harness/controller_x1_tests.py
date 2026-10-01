#!/usr/bin/env python3
"""Provider-free regression tests for Controller campaign integrity X1."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_x0_probe as probe  # noqa: E402
import controller_matrix_runtime as matrix  # noqa: E402
import controller_pilot_runtime as pilot  # noqa: E402
import controller_corpus as corpus  # noqa: E402
import controller_campaign_manifest as package  # noqa: E402
import controller_campaign_state as campaign_state  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402
import route  # noqa: E402


class CampaignIntegrityTests(unittest.TestCase):
    def test_cancellation_between_budget_start_and_adapter_is_not_launched(self) -> None:
        with tempfile.TemporaryDirectory(prefix="controller-x1-start-race-") as raw:
            root = Path(raw)
            manifest_value = probe.fresh_manifest("matrix-calibration")
            manifest, auth = probe.manifest_files(root, manifest_value)
            run_root = root / "run"
            original_start = DispatchBudget.start

            def cancel_after_start(budget, invocation_id):
                original_start(budget, invocation_id)
                matrix.cancel(run_root)

            class MustNotRun:
                def run(self, *args):
                    raise AssertionError("cancelled matrix adapter launched")

            with patch.object(DispatchBudget, "start", cancel_after_start):
                result = matrix.execute(manifest, auth, run_root, MustNotRun())
            self.assertEqual("cancelled", result["status"])
            self.assertIsNone(result["current"])
            first_row = manifest_value["episodes"][0]
            episode_id = (f"matrix-{first_row['sequence']:03d}-"
                          f"{first_row['cell']}-{first_row['kind']}")
            snapshot = DispatchBudget(run_root / episode_id / "budget.json").snapshot()
            self.assertEqual(0.0, snapshot["spent_usd"])
            self.assertEqual([], snapshot["unresolved"])

        with tempfile.TemporaryDirectory(prefix="controller-x1-worker-race-") as raw:
            task = corpus.load_corpus()["tasks"][0]
            calls = []

            class MustNotRunWorker:
                def run(self, request):
                    calls.append(request)
                    raise AssertionError("cancelled worker adapter launched")

            executor = pilot.PilotEpisodeExecutor(MustNotRunWorker(), probe.NoCalls())
            probes = iter((False, True))
            executor.cancelled_probe = lambda: next(probes, True)
            episode = {"arm": "B", "selected_cell": "worker-sonnet-low",
                       "controller_profile": "standard", "maximum_usd": 8.0}
            result = executor.run(task, episode, Path(raw))
            snapshot = DispatchBudget(Path(raw) / "task-budget.json",
                                      scope="task_dispatch").snapshot()
            self.assertEqual([], calls)
            self.assertEqual(0.0, result["cost_usd"])
            self.assertEqual([], snapshot["unresolved"])
            self.assertTrue(snapshot["cancelled"])

    def test_materialised_package_blocks_unqualified_live_launch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="controller-x1-live-gate-") as raw:
            root = Path(raw)
            runtime_root = root / "package"
            package.materialise(ROOT, runtime_root)
            manifest = probe.fresh_manifest("matrix-calibration")
            manifest_path, auth_path = probe.manifest_files(root, manifest)
            run_root = root / "run"
            process = subprocess.run([
                sys.executable, "-B", str(runtime_root / "tools/controller_matrix_runtime.py"),
                "--manifest", str(manifest_path), "--authorisation", str(auth_path),
                "--run-root", str(run_root)], capture_output=True, text=True, timeout=30)
            self.assertNotEqual(0, process.returncode)
            self.assertIn("live dispatch is closed", process.stderr)
            self.assertFalse((run_root / "state.json").exists())
            self.assertFalse(list(run_root.rglob("budget.json")))

    def test_missing_budget_is_unresolved_even_with_reported_cost(self) -> None:
        with tempfile.TemporaryDirectory(prefix="controller-x1-missing-ledger-") as raw:
            root = Path(raw)
            manifest = probe.fresh_manifest("instrumented-pilot")
            path, auth = probe.manifest_files(root, manifest)

            class Failed:
                def run(self, task, episode, episode_root):
                    return {"status": "failed", "cost_usd": .25,
                            "accounting_complete": True}

            run_root = root / "run"
            self.assertEqual("stopped", pilot.execute(path, auth, run_root, Failed())["status"])
            result = pilot.reconcile(run_root, manifest["manifest_sha256"])
            self.assertEqual(.25, result["known_spend_usd"])
            self.assertEqual(1, len(result["accounting"]["unresolved"]))
            self.assertIn("cost-ledger-disagrees", result["accounting"]["unresolved"][0])

    def test_archived_manifest_and_tampered_checkpoint_cannot_dispatch(self) -> None:
        legacy = json.loads((ROOT / "docs/CONTROLLER-ROUTING-R5-MATRIX-MANIFEST.json")
                            .read_text(encoding="utf-8"))
        with self.assertRaisesRegex(matrix.MatrixRuntimeError, "archived R5"):
            matrix.validate_manifest(legacy)
        with tempfile.TemporaryDirectory(prefix="controller-x1-state-seal-") as raw:
            root = Path(raw)
            manifest, auth = probe.manifest_files(root,
                                                   probe.fresh_manifest("matrix-calibration"))

            class Failed:
                calls = 0

                def run(self, episode, cwd):
                    self.calls += 1
                    return {"status": "failed", "terminal": True,
                            "cost_usd": .01, "identity_valid": True}

            adapter = Failed()
            run_root = root / "run"
            matrix.execute(manifest, auth, run_root, adapter)
            path = run_root / "state.json"
            state = json.loads(path.read_text())
            state.update(status="running", current=None)
            path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaises(campaign_state.CampaignStateError):
                matrix.execute(manifest, auth, run_root, adapter)
            self.assertEqual(1, adapter.calls)

    def test_explicit_continuation_links_allowance_without_replay(self) -> None:
        for name, runtime, kind in (("matrix", matrix, "matrix-calibration"),
                                    ("pilot", pilot, "instrumented-pilot")):
            with self.subTest(campaign=name), tempfile.TemporaryDirectory(
                    prefix="controller-x1-next-") as raw:
                root = Path(raw)
                original = probe.fresh_manifest(kind)
                manifest, auth = probe.manifest_files(root, original)

                class Failed:
                    calls = []

                    def run(self, *args):
                        row = args[0] if name == "matrix" else args[1]
                        self.calls.append(row["sequence"])
                        return {"status": "failed", "terminal": True,
                                "cost_usd": .01, "identity_valid": True,
                                "accounting_complete": True}

                adapter = Failed()
                predecessor = root / "prior-run"
                self.assertEqual("stopped", runtime.execute(
                    manifest, auth, predecessor, adapter)["status"])
                if name == "pilot":
                    # The injected episode stub bypasses the real executor's
                    # durable task budget, so supply its matching fake ledger.
                    episode_id = next(iter(json.loads((predecessor / "state.json").read_text())
                                           ["episodes"]))
                    budget = DispatchBudget(predecessor / episode_id / "task-budget.json",
                                            8.0, scope="task_dispatch")
                    budget.reserve("fixture-1", 1.0, .001, {"offline": True})
                    budget.start("fixture-1")
                    budget.settle("fixture-1", .01, final=True,
                                  telemetry={"terminal": True}, evidence="offline-receipt")
                rows = original["episodes"][1:]
                maximum = round(sum(row["maximum_usd"] for row in rows), 9)
                approval = {"decision": "approved", "authority_id": "offline-grant-1",
                            "approved_by": "offline-test", "approved_at": "fixture-clock",
                            "schedule_sha256": probe.evaluation.digest({
                                "episodes": rows, "maximum_authorised_usd": maximum}),
                            "maximum_authorised_usd": maximum}
                successor = root / "successor"
                next_manifest, next_auth = package.prepare_continuation(
                    manifest, predecessor, successor, rows, maximum, approval, kind=name)
                # Recovery after a crash between the grant and the second
                # successor file must reuse, not duplicate, the allowance.
                next_auth.unlink()
                recovered_manifest, recovered_auth = package.prepare_continuation(
                    manifest, predecessor, successor, rows, maximum, approval, kind=name)
                self.assertEqual((next_manifest, next_auth),
                                 (recovered_manifest, recovered_auth))
                altered = json.loads(next_manifest.read_text())
                altered["maximum_authorised_usd"] += 1
                next_manifest.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaisesRegex(package.CampaignManifestError,
                                            "existing successor file differs"):
                    package.prepare_continuation(
                        manifest, predecessor, successor, rows, maximum, approval,
                        kind=name)
                package_module = json.loads(recovered_manifest.read_text())
                package_module["maximum_authorised_usd"] -= 1
                next_manifest.write_text(json.dumps(package_module), encoding="utf-8")
                next_value = json.loads(next_manifest.read_text())
                self.assertEqual(original["manifest_sha256"], next_value[
                    "continuation"]["predecessor_manifest_sha256"])
                self.assertEqual(.01, next_value["continuation"]["inherited_spend_usd"])
                self.assertEqual("stopped", runtime.execute(
                    next_manifest, next_auth, successor / "run", adapter)["status"])
                self.assertEqual([1, 2], adapter.calls)
                self.assertEqual("stopped", runtime.execute(
                    manifest, auth, predecessor, adapter)["status"])
                self.assertEqual([1, 2], adapter.calls)
                with self.assertRaises(package.CampaignManifestError):
                    package.prepare_continuation(
                        manifest, predecessor, root / "another", rows, maximum,
                        dict(approval, authority_id="offline-grant-2"), kind=name)

    def test_reconciliation_recovers_settled_charge_without_dispatch(self) -> None:
        for name, runtime, kind in (("matrix", matrix, "matrix-calibration"),
                                    ("pilot", pilot, "instrumented-pilot")):
            with self.subTest(campaign=name), tempfile.TemporaryDirectory(
                    prefix="controller-x1-reconcile-") as raw:
                root = Path(raw)
                manifest = probe.fresh_manifest(kind)
                manifest_path, auth = probe.manifest_files(root, manifest)
                run_root = root / "run"

                class Interrupted:
                    calls = 0

                    def run(self, *args):
                        self.calls += 1
                        raise RuntimeError("provider return lost after billing")

                adapter = Interrupted()
                if name == "matrix":
                    first = runtime.execute(manifest_path, auth, run_root, adapter)
                    self.assertEqual("stopped", first["status"])
                else:
                    with self.assertRaisesRegex(RuntimeError, "return lost"):
                        runtime.execute(manifest_path, auth, run_root, adapter)
                state = json.loads((run_root / "state.json").read_text())
                episode = run_root / state["current"]["episode_id"]
                if name == "matrix":
                    budget = DispatchBudget(episode / "budget.json")
                    invocation = state["current"]["invocation_id"]
                else:
                    budget = DispatchBudget(episode / "task-budget.json", 8.0,
                                            scope="task_dispatch")
                    invocation = "controller-001"
                    budget.reserve(invocation, 1.0, .001, {"offline": True})
                    budget.start(invocation)
                budget.settle(invocation, .25, final=True,
                              telemetry={"terminal": True},
                              evidence="post-crash-provider-receipt")
                reconciled = runtime.reconcile(run_root, manifest["manifest_sha256"])
                self.assertEqual("stopped", reconciled["status"])
                self.assertEqual(.25, reconciled["known_spend_usd"])
                self.assertEqual(
                    [f"{state['current']['episode_id']}/writer-status-unproved"],
                    reconciled["accounting"]["unresolved"])
                self.assertEqual(0.0, reconciled["accounting"]["reserved_usd"])
                self.assertEqual(1, adapter.calls)
                replay = runtime.execute(manifest_path, auth, run_root, adapter)
                self.assertEqual("stopped", replay["status"])
                self.assertEqual(1, adapter.calls)

    def test_complete_runtime_inventory_rejects_mutation_and_addition(self) -> None:
        archived = (ROOT / "docs/CONTROLLER-ROUTING-R5-MATRIX-MANIFEST.json").read_bytes()
        with tempfile.TemporaryDirectory(prefix="controller-x1-package-") as raw:
            destination = Path(raw) / "package"
            record = package.materialise(ROOT, destination)
            self.assertGreater(len(record["files"]), 300)
            self.assertIn("test/fixtures/controller_x3/reserved/N04-R2/actor/generate.py",
                          record["files"])
            self.assertIn("test/oracles/controller_x3/N04-R2.json",
                          record["files"])
            for relative in ("tools/dispatch_budget.py", "tools/controller_corpus.py",
                             "tools/controller_evaluation.py", "test/harness/realworld.py",
                             "src/System/ROLES.md", "src/model_registry.json",
                             "src/controller_evaluation_contract.json",
                             "src/System/schemas/ControllerEvidencePacket.schema.json",
                             "test/fixtures/controller_x3/reserved/N04-R2/actor/generate.py",
                             "test/oracles/controller_x3/N04-R2.json"):
                with self.subTest(file=relative):
                    path = destination / relative
                    original = path.read_bytes()
                    path.write_bytes(original + b"\nchanged\n")
                    with self.assertRaises(package.CampaignManifestError):
                        package.verify_package(destination, record,
                                               require_materialised=True)
                    path.write_bytes(original)
            extra = destination / "tools/new_dependency.py"
            extra.write_text("pass\n", encoding="utf-8")
            with self.assertRaises(package.CampaignManifestError):
                package.verify_package(destination, record, require_materialised=True)
            extra.unlink()
            package.verify_package(destination, record, require_materialised=True)
        self.assertEqual(archived, (ROOT / "docs/CONTROLLER-ROUTING-R5-MATRIX-MANIFEST.json").read_bytes())

    def test_new_v2_manifest_binds_all_runtime_files(self) -> None:
        for kind, runtime in (("matrix-calibration", matrix),
                              ("instrumented-pilot", pilot)):
            with self.subTest(kind=kind):
                value = probe.fresh_manifest(kind)
                self.assertEqual(2, value["schema_version"])
                self.assertEqual(value["runtime_package"]["files"], value["bound_files"])
                runtime.validate_manifest(value)
                broken = dict(value)
                broken["episodes"] = [dict(row) for row in value["episodes"]]
                broken["episodes"][0]["maximum_usd"] = value["maximum_authorised_usd"]
                broken["manifest_sha256"] = probe.evaluation.digest(
                    {k: v for k, v in broken.items() if k != "manifest_sha256"})
                with self.assertRaises((matrix.MatrixRuntimeError, pilot.PilotRuntimeError)):
                    runtime.validate_manifest(broken)

    def test_pilot_cancellation_prevents_next_worker_attempt(self) -> None:
        task = corpus.load_corpus()["tasks"][0]
        with tempfile.TemporaryDirectory(prefix="controller-x1-worker-stop-") as raw:
            class Worker:
                calls = 0

                def run(self, request):
                    self.calls += 1
                    return {"status": "failed", "terminal": True,
                            "cost_usd": 0.01, "identity_valid": True}

            worker = Worker()
            executor = pilot.PilotEpisodeExecutor(worker, probe.NoCalls())
            executor.cancelled_probe = lambda: worker.calls > 0
            episode = {"arm": "B", "selected_cell": "worker-sonnet-low",
                       "controller_profile": "standard", "maximum_usd": 8.0}
            result = executor.run(task, episode, Path(raw))
            budget = DispatchBudget(Path(raw) / "task-budget.json",
                                    scope="task_dispatch").snapshot()
        self.assertEqual(1, worker.calls)
        self.assertEqual(1, len(result["worker_attempts"]))
        self.assertEqual(0.01, result["cost_usd"])
        self.assertTrue(budget["cancelled"])

    def test_competing_drivers_and_cancellation_keep_late_charge(self) -> None:
        for name, runtime, kind in (("matrix", matrix, "matrix-calibration"),
                                    ("pilot", pilot, "instrumented-pilot")):
            with self.subTest(campaign=name), tempfile.TemporaryDirectory(
                    prefix="controller-x1-race-") as raw:
                root = Path(raw)
                manifest, auth = probe.manifest_files(root, probe.fresh_manifest(kind))
                run_root = root / "run"
                entered, release = threading.Event(), threading.Event()
                calls = []

                class HeldAdapter:
                    def run(self, *args):
                        episode = args[0] if name == "matrix" else args[1]
                        calls.append(episode["sequence"])
                        entered.set()
                        if not release.wait(30):
                            raise RuntimeError("test adapter release timed out")
                        return {"status": "failed", "terminal": True,
                                "cost_usd": 0.25, "identity_valid": True,
                                "accounting_complete": True}

                adapter = HeldAdapter()
                with ThreadPoolExecutor(max_workers=2) as pool:
                    first = pool.submit(runtime.execute, manifest, auth, run_root, adapter)
                    if not entered.wait(30):
                        # Expose an early campaign failure instead of reporting
                        # an opaque race timeout from this helper thread.
                        first.result(timeout=1)
                        self.fail("campaign did not enter the held adapter")
                    with self.assertRaises(route.LedgerLockTimeout):
                        runtime.execute(manifest, auth, run_root, adapter,
                                        driver_lock_timeout_s=0.05)
                    cancelled = runtime.cancel(run_root)
                    self.assertEqual("cancelled", cancelled["status"])
                    release.set()
                    final = first.result(timeout=30)
                self.assertEqual([1], calls)
                self.assertEqual("cancelled", final["status"])
                self.assertEqual(0.25, final["known_spend_usd"])
                replay = runtime.execute(manifest, auth, run_root, adapter)
                self.assertEqual("cancelled", replay["status"])
                self.assertEqual([1], calls)

    def test_settled_failure_cannot_resume_either_campaign(self) -> None:
        with tempfile.TemporaryDirectory(prefix="controller-x1-stop-") as raw:
            for name, result in probe.terminal_restart(Path(raw)).items():
                with self.subTest(campaign=name):
                    self.assertEqual("stopped", result["first_status"])
                    self.assertEqual("stopped", result["second_status"])
                    self.assertEqual([1], result["sequences"])
                    self.assertEqual(0, result["additional_calls"])
                    self.assertEqual(0.01, result["known_spend_usd"])

    def test_blocked_pilot_reports_settled_controller_cost(self) -> None:
        with tempfile.TemporaryDirectory(prefix="controller-x1-cost-") as raw:
            result = probe.failed_cost_projection(Path(raw))
        self.assertEqual(0.25, result["durable_known_spend_usd"])
        self.assertEqual([], result["durable_unresolved"])
        self.assertEqual(0.25, result["episode_cost_usd"])
        self.assertTrue(result["episode_accounting_complete"])


if __name__ == "__main__":
    unittest.main()
