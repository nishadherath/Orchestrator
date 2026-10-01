"""Q4U metadata becomes change-sensitive or no-edit command contracts."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import acceptance  # noqa: E402
from worker_q4u_contract import build  # noqa: E402


class Q4UContractTests(unittest.TestCase):
    def test_frozen_tasks_apply_the_correct_change_requirement(self):
        for task_id in ("D01W", "D01S", "B02W", "B02S", "C03", "C04",
                        "M05", "M06", "F07W", "F07S", "H08W", "H08S",
                        "R09", "R10", "R11", "R12"):
            with self.subTest(task=task_id):
                contract = build(task_id)
                actor = ROOT / "test/fixtures/worker_q4u_public" / task_id / "actor"
                self.assertEqual(task_id not in {"C03", "C04", "M05", "M06",
                                                 "R11", "R12"},
                                 contract["require_changed_output"])
                self.assertTrue(set(contract["required_outputs"]).isdisjoint(
                    contract["protected_paths"]))
                with tempfile.TemporaryDirectory(dir=ROOT / "test/results") as directory:
                    workspace = Path(directory) / "actor"
                    shutil.copytree(actor, workspace)
                    path = workspace / ".claude/acceptance.json"
                    path.parent.mkdir()
                    path.write_text(json.dumps(contract), encoding="utf-8")
                    frozen = acceptance.load_contract(workspace, path)
                    self.assertEqual(contract["required_outputs"],
                                     frozen["contract"]["required_outputs"])
                    if contract["require_changed_output"]:
                        self.assertEqual([], frozen["contract"]["required_baseline"]["missing"])
                    else:
                        self.assertNotIn("required_baseline", frozen["contract"])


if __name__ == "__main__":
    unittest.main()
