"""Provider-free guards for the Q4S corpus and prospective screen freeze."""
from __future__ import annotations

import json
import hashlib
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_adapter import digest  # noqa: E402
from worker_q4s_public_catalogue import build  # noqa: E402
from worker_q4s_public_source import FIXTURES, SOURCES  # noqa: E402
from worker_q4s_rubric import rubric  # noqa: E402
from worker_q4s_trigger import OUTPUT as TRIGGERS, build as build_triggers  # noqa: E402
from worker_quality_v2 import validate_rubric  # noqa: E402


class Q4SS2Tests(unittest.TestCase):
    def test_six_independent_pinned_families(self):
        sources = [build(task_id) for task_id in SOURCES]
        self.assertEqual(len(sources), 6)
        self.assertEqual(len({row["source_url"] for row in sources}), 6)
        self.assertEqual(len({row["source_commit"] for row in sources}), 6)
        prior = {"cachetools", "itsdangerous", "click", "urllib3", "tenacity",
                 "pyjwt", "packaging", "platformdirs"}
        for row in sources:
            self.assertNotIn(row["source_url"].split("/")[-1].lower(), prior)
            self.assertEqual(row, json.loads((FIXTURES / row["id"] / "task.json").read_text()))
            self.assertFalse(any("__pycache__" in name for name in row["actor_files"]))
            if row["id"] == "S03":
                self.assertFalse(any(name.startswith("h11/tests/")
                                     for name in row["actor_files"]))
            self.assertEqual(set(row["editable_paths"]), set(row["reference_files"]))
            self.assertEqual(set(row["editable_paths"]), set(row["partial_files"]))

    def test_trigger_is_public_source_bound(self):
        value = build_triggers()
        self.assertEqual(value, json.loads(TRIGGERS.read_text()))
        positive = {row["task_id"] for row in value["rows"] if row["triggered"]}
        self.assertEqual(positive, {"S01", "S02", "S03", "S04"})
        for row in value["rows"]:
            self.assertGreaterEqual(len(row["modules"]), 3 if row["triggered"] else 2)
            self.assertEqual(set(row["modules"]), set(row["source_sha256"]))

    def test_quality_rubric_and_calibration_separate_variants(self):
        evidence = json.loads((ROOT / "test/results/2026-09-26-worker-q4s-public-calibration.json").read_text())
        body = {key: value for key, value in evidence.items() if key != "evidence_sha256"}
        self.assertEqual(evidence["evidence_sha256"], digest(body))
        self.assertEqual(evidence["provider_calls"], 0)
        self.assertEqual({row["task_id"] for row in evidence["rows"]}, set(SOURCES))
        for row in evidence["rows"]:
            self.assertEqual(row["task_sha256"], build(row["task_id"])["task_sha256"])
            self.assertEqual([grade["variant"] for grade in row["grades"]],
                             ["baseline", "partial", "reference"])
            baseline, partial, reference = [grade["executable_score"] for grade in row["grades"]]
            self.assertLess(baseline, partial)
            self.assertLess(partial, reference)
            self.assertEqual(reference, 100)
            self.assertTrue(row["grades"][-1]["public_pass"])
            validate_rubric(rubric(row["task_id"]))

    def test_frozen_schedule_and_cost_scope(self):
        manifest = json.loads((ROOT / "test/results/2026-09-26-worker-q4s-screen-manifest.json").read_text())
        body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        self.assertEqual(manifest["manifest_sha256"], digest(body))
        self.assertEqual(len(manifest["rows"]), 18)
        self.assertEqual(manifest["cost"]["combined_allocation_usd"], 78)
        self.assertEqual(manifest["cost"]["maximum_provider_calls"], 56)
        for name, expected in manifest["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(),
                             expected, name)
        self.assertEqual(hashlib.sha256((ROOT / "docs/stage-results/worker-q4s-spend-notice-2026-09-26.md").read_bytes()).hexdigest(),
                         manifest["spend_notice_sha256"])
        self.assertEqual(hashlib.sha256(TRIGGERS.read_bytes()).hexdigest(),
                         manifest["public_trigger_sha256"])
        self.assertTrue(manifest["canary"]["excluded_from_six_family_screen"])
        self.assertFalse(manifest["reserved_tasks_allowed"])
        self.assertEqual([row["episode_label"] for row in manifest["rows"][:3]],
                         list(manifest["latin_order"]["base"]))
        for task_id in SOURCES:
            labels = {row["episode_label"] for row in manifest["rows"]
                      if row["task_id"] == task_id}
            self.assertEqual(labels, {"b0-a", "b0-b", "sonnet-medium"})


if __name__ == "__main__":
    unittest.main()
