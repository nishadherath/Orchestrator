#!/usr/bin/env python3
"""Sealed X3 paired campaign regressions, with no provider calls."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_evaluation  # noqa: E402
import controller_x3_manifest  # noqa: E402
from test.harness import controller_x3_fake_campaign as campaign  # noqa: E402


class X3FakeCampaignTests(unittest.TestCase):
    def test_schedule_and_runtime_seal(self):
        manifest = controller_x3_manifest.build()
        controller_x3_manifest.validate(manifest)
        self.assertEqual(
            [(row["task_id"], row["arm"]) for row in manifest["episodes"]],
            [("N04-D1", "S"), ("N04-D1", "A"),
             ("C03-D1", "A"), ("C03-D1", "S")],
        )
        changed = copy.deepcopy(manifest)
        changed["runtime_package"]["files"]["tools/controller_workflow.py"] = "0" * 64
        changed["runtime_package"]["inventory_sha256"] = controller_evaluation.digest(
            changed["runtime_package"]["files"])
        changed["manifest_sha256"] = controller_evaluation.digest(
            {key: value for key, value in changed.items() if key != "manifest_sha256"})
        with self.assertRaisesRegex(ValueError, "inventory or content changed"):
            controller_x3_manifest.validate(changed)
        with self.assertRaisesRegex(ValueError, "development"):
            controller_x3_manifest.build(("C03-R1",))

    def test_frozen_pairs_use_common_workflow_and_do_not_replay(self):
        manifest = controller_x3_manifest.build()
        with tempfile.TemporaryDirectory(prefix="x3-fake-campaign-",
                                         dir=ROOT / "test" / "results") as raw:
            parent = Path(raw)
            manifest_path = parent / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            output = parent / "run"
            state = campaign.execute(manifest_path, output)
            self.assertEqual(state["status"], "completed")
            self.assertEqual(len(state["episodes"]), 4)
            self.assertEqual(state["actual_provider_calls"], 0)
            self.assertTrue(all(row["same_public_evidence"] for row in state["pairs"]))
            self.assertEqual({row["a_action"] for row in state["pairs"]},
                             {"worker", "controller"})
            self.assertTrue(all(row["task_state"] == "accepted"
                                and row["accounting_complete"]
                                for row in state["episodes"]))
            self.assertEqual(json.loads((output / "state.json").read_text())["status"],
                             "completed")
            with self.assertRaisesRegex(campaign.X3CampaignError, "fresh"):
                campaign.execute(manifest_path, output)


if __name__ == "__main__":
    unittest.main()
