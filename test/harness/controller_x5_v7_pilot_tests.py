#!/usr/bin/env python3
"""Provider-free invariants for the X5 v7 continuation and repaired rubric."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_v6_grade as x5  # noqa: E402
import controller_x5_v7_pilot as pilot  # noqa: E402
import controller_x5_v7_pilot_grade as grade  # noqa: E402


class PilotTests(unittest.TestCase):
    def test_schedule_only_unstarted_pairs_and_caps_spend(self) -> None:
        rows = pilot.schedule()
        self.assertEqual(len(rows), 12)
        self.assertEqual([row["sequence"] for row in rows], list(range(7, 19)))
        self.assertEqual(sum(row["maximum_usd"] for row in rows), 60.0)
        self.assertEqual({row["task_id"] for row in rows},
                         {"X5-PAY", "X5-FEAT", "N01-D1", "C08-D2"})
        for task in {row["task_id"] for row in rows}:
            self.assertEqual({row["arm"] for row in rows if row["task_id"] == task},
                             {"B", "S", "A"})

    def test_dated_notice_required_before_an_episode_can_start(self) -> None:
        manifest = {"manifest_sha256": "frozen", "episodes": pilot.schedule()}
        with self.assertRaisesRegex(pilot.PilotError, "cost notice"):
            pilot.gate(manifest, manifest["episodes"][0],
                       {"authorised_under_threshold": False})

    def test_started_marker_refuses_replay(self) -> None:
        with tempfile.TemporaryDirectory(prefix="x5-v7-marker-") as raw:
            path = Path(raw) / "007-started.json"
            pilot.exclusive(path, {"root_id": "first"})
            with self.assertRaises(FileExistsError):
                pilot.exclusive(path, {"root_id": "second"})

    def test_prepared_root_and_prior_overspend_stop_before_launch(self) -> None:
        manifest = {"manifest_sha256": "frozen", "episodes": pilot.schedule()}
        notice = {"authorised_under_threshold": True,
                  "manifest_sha256": "frozen", "maximum_pilot_usd": 60.0,
                  "scope": "12 paired X5 v7 development continuation episodes"}
        rows = manifest["episodes"]
        prepared = [{"sequence": row["sequence"], "task_id": row["task_id"],
                     "arm": row["arm"], "root_id": pilot.root_id(manifest, row),
                     "project": str(pilot.project(manifest, row))} for row in rows]
        with tempfile.TemporaryDirectory(prefix="x5-v7-gate-") as raw, \
                mock.patch.object(pilot, "RUN_DIR", Path(raw)):
            path = Path(raw) / "prepared.json"
            payload = {"manifest_sha256": "frozen",
                       "status": "prepared-no-provider-call", "episodes": prepared}
            correct_first = prepared[0].copy()
            payload["episodes"][0] = {**prepared[0], "root_id": "tampered"}
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(pilot.PilotError, "prepared pilot root"):
                pilot.gate(manifest, rows[0], notice)
            payload["episodes"][0] = correct_first
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = {"status": "completed", "budget_unresolved": [],
                      "manifest_sha256": "frozen",
                      "root_id": pilot.root_id(manifest, rows[0]),
                      "budget_spent_usd": 6.0, "required_admission_met": True}
            (Path(raw) / "007-result.json").write_text(json.dumps(result),
                                                          encoding="utf-8")
            state = {"budget": {"spent_usd": 6.0, "breached": False,
                                "unresolved": []}}
            with mock.patch.object(pilot, "executor") as executor:
                executor.return_value.status.return_value = state
                with self.assertRaisesRegex(pilot.PilotError, "pilot stopped"):
                    pilot.gate(manifest, rows[1], notice)

    def test_truthful_pending_reports_remain_parseable(self) -> None:
        for claim in ("unverified", "fixed, verification pending execution",
                      "not verified"):
            self.assertEqual(grade.normal_claim({"completion_claim": claim})[0],
                             "partial")
        self.assertEqual(grade.normal_claim({"status": "completed"})[0],
                         "complete")
        self.assertEqual(grade.normal_claim(None)[0], "blocked")

    def test_host_causal_checks_cover_both_mechanisms(self) -> None:
        for task in ("X5-SHIP", "X5-MIGRATE", "X5-PAY", "X5-FEAT"):
            case, _ = x5.CASES[task]
            version = ("controller_x5_v6" if task in {"X5-SHIP", "X5-MIGRATE"}
                       else "controller_x5_v4")
            path = ROOT / "test/oracles" / version / case / "acceptance.json"
            oracle = json.loads(path.read_text(encoding="utf-8"))
            base = {"oracle_sha256": x5.sha(path),
                    "observed_milestones": [
                        {"name": row["name"], "passed": True}
                        for row in oracle["checks"]]}
            evidence, kinds = grade.causal_observations(task, base)
            self.assertEqual(evidence, 1.0, task)
            self.assertEqual(set(kinds), x5.REQUIRED_KINDS[task], task)


if __name__ == "__main__":
    unittest.main()
