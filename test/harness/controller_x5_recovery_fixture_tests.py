"""Provider-free behaviour audit for X5 recovery development actors."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CASES = {
    "R01": {"files": {"acceptance.json", "app.py", "delivery.py", "issue.md",
                       "journal.py", "public_check.py", "report.json", "trace.json"},
            "editable": {"journal.py", "delivery.py"},
            "baseline": 25, "partials": {"tenant_only": 45, "checkpoint_only": 80}},
    "R02": {"files": {"acceptance.json", "app.py", "cache.py", "decision.py",
                       "issue.md", "policy.py", "public_check.py", "report.json", "trace.json"},
            "editable": {"cache.py", "decision.py"},
            "baseline": 25, "partials": {"cache_only": 65, "precedence_only": 45}},
}


def run(actor: Path, operations: list[dict]) -> dict:
    result = subprocess.run(
        [sys.executable, "-B", "app.py"], cwd=actor,
        input=json.dumps({"operations": operations}), capture_output=True,
        text=True, timeout=10, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return json.loads(result.stdout)


def public(actor: Path) -> bool:
    result = subprocess.run(
        [sys.executable, "-B", "public_check.py"], cwd=actor,
        capture_output=True, text=True, timeout=10, check=False,
    )
    return result.returncode == 0


def score(actor: Path, task_id: str) -> tuple[int, list[str]]:
    oracle = json.loads((ROOT / "test/oracles/controller_x5_recovery" / f"{task_id}.json").read_text(encoding="utf-8"))
    if oracle["schema_version"] != 1 or oracle["task_id"] != task_id:
        raise AssertionError("invalid oracle identity")
    if sum(row["weight"] for row in oracle["cases"]) != 100:
        raise AssertionError("oracle weights do not total 100")
    earned = 0
    failed = []
    for case in oracle["cases"]:
        if run(actor, case["operations"]) == case["expected"]:
            earned += case["weight"]
        else:
            failed.append(case["name"])
    return earned, failed


class RecoveryFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="x5-recovery-")
        self.addCleanup(self.temp.cleanup)

    def actor(self, task_id: str, variant: str | None = None) -> Path:
        case = ROOT / "test/fixtures/controller_x5_recovery/development" / task_id
        target = Path(self.temp.name) / f"{task_id}-{variant or 'baseline'}"
        shutil.copytree(case / "actor", target)
        if variant:
            for source in (case / "variants" / variant).iterdir():
                self.assertIn(source.name, CASES[task_id]["editable"])
                shutil.copy2(source, target / source.name)
        self.assertEqual({path.name for path in target.iterdir()}, CASES[task_id]["files"])
        self.assertFalse((target / f"{task_id}.json").exists())
        return target

    def test_initial_actor_reproduces_public_trace_and_fails_acceptance(self) -> None:
        for task_id, config in CASES.items():
            with self.subTest(task_id=task_id):
                actor = self.actor(task_id)
                trace = json.loads((actor / "trace.json").read_text(encoding="utf-8"))
                observed = run(actor, trace["operations"])
                if task_id == "R01":
                    self.assertEqual([row["status"] for row in observed["results"]],
                                     trace["observed_statuses"])
                    self.assertEqual(observed["totals"], trace["observed_totals"])
                else:
                    self.assertEqual(observed["results"], trace["observed_results"])
                self.assertFalse(public(actor))
                earned, failed = score(actor, task_id)
                self.assertEqual(earned, config["baseline"])
                self.assertTrue(failed)

    def test_reference_passes_public_and_all_protected_cases(self) -> None:
        for task_id in CASES:
            with self.subTest(task_id=task_id):
                actor = self.actor(task_id, "reference")
                self.assertTrue(public(actor))
                self.assertEqual(score(actor, task_id), (100, []))

    def test_single_mechanism_repairs_remain_incomplete(self) -> None:
        for task_id, config in CASES.items():
            for variant, expected in config["partials"].items():
                with self.subTest(task_id=task_id, variant=variant):
                    actor = self.actor(task_id, variant)
                    self.assertFalse(public(actor))
                    self.assertEqual(score(actor, task_id)[0], expected)


if __name__ == "__main__":
    unittest.main()
