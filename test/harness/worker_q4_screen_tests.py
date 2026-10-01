#!/usr/bin/env python3
"""Provider-free checks for the exact Q4 M3 screen and decision rule."""
from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_q4_screen as screen  # noqa: E402
import worker_q4_screen_live as live  # noqa: E402
import worker_q4_screen_continue as continuation  # noqa: E402
from worker_q3_public_catalogue import sha  # noqa: E402


class Q4ScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # These are historical screen-shape and analysis tests. The saved Q4
        # evidence still validates against its source, but its installed WSL
        # launcher is no longer the current one. Keep the live gate strict.
        host_validate = screen.q4_host.validate
        with patch.object(screen.q4_host, "validate",
                          side_effect=lambda value, check_host: host_validate(
                              value, check_host=False)):
            cls.manifest = screen.build_manifest(
                dt.datetime.now(dt.timezone.utc).date().isoformat(),
                sha(screen.NOTICE))

    def test_stale_host_cannot_launch_a_new_q4_screen(self):
        host = json.loads(screen.HOST.read_text(encoding="utf-8"))
        self.assertTrue(screen.q4_host.validate(host, check_host=False))
        with patch.object(screen.q4_host, "runtime_hash", return_value="0" * 64):
            self.assertFalse(screen.q4_host.validate(host, check_host=True))
            with self.assertRaisesRegex(screen.ScreenError, "host evidence is stale"):
                screen.build_manifest(dt.datetime.now(dt.timezone.utc).date().isoformat(),
                                      sha(screen.NOTICE))

    def test_manifest_freezes_latin_order_common_tail_and_cost(self):
        rows = self.manifest["rows"]
        self.assertEqual(16, len(rows))
        self.assertEqual(list(range(1, 17)), [row["sequence"] for row in rows])
        self.assertEqual(99.0, self.manifest["cost"]["combined_allocation_usd"])
        self.assertEqual(51, self.manifest["cost"]["maximum_provider_calls"])
        self.assertEqual(96.0, sum(row["episode_maximum_usd"] for row in rows))
        for task_id in screen.TASKS:
            family = [row for row in rows if row["task_id"] == task_id]
            self.assertEqual(set(screen.LABELS), {row["episode_label"] for row in family})
            self.assertEqual([1, 2, 3, 4], [row["latin_position"] for row in family])
            self.assertTrue(all(row["repair_cells"] == screen.REPAIR_TAIL
                                and row["ladder"] == [row["first_cell"],
                                                      *screen.REPAIR_TAIL]
                                for row in family))

    def test_manifest_is_source_bound_and_approval_is_exact(self):
        self.assertEqual({name: sha(ROOT / name) for name in screen.SOURCES},
                         self.manifest["source_sha256"])
        approval = {"schema_version": 1, "decision": "approved",
                    "manifest_sha256": self.manifest["manifest_sha256"],
                    "maximum_authorised_usd": 99.0,
                    "maximum_provider_calls": 51,
                    "spend_notice_sha256": self.manifest["spend_notice_sha256"],
                    "credential_method": "claude-code-wsl-subscription",
                    "approved_by": "operator-standing-through-Q4-2026-09-25",
                    "approved_at": "2026-09-26T00:00:00+00:00"}
        screen.validate_approval(self.manifest, approval)
        with self.assertRaises(screen.ScreenError):
            screen.validate_approval(self.manifest,
                                     {**approval, "maximum_provider_calls": 52})

    @staticmethod
    def episode(task_id: str, label: str, quality: int, accepted: bool,
                cost: float) -> dict:
        return {"task_id": task_id, "episode_label": label,
                "quality_v2": {"quality": quality, "hidden_accepted": accepted,
                               "critical_error": False,
                               "unsupported_completion": False,
                               "report_observability": "present"},
                "budget": {"spent_usd": cost}, "attempts": [{}]}

    def test_analysis_applies_quality_cost_and_repetition_rules(self):
        rows = []
        for label in screen.LABELS:
            for index, task_id in enumerate(screen.TASKS):
                if label in {"b0-a", "b0-b"}:
                    episode = self.episode(task_id, label, 70, index == 0, 1.0)
                elif label == "sonnet-xhigh":
                    episode = self.episode(task_id, label, 82, index < 2, 1.25)
                else:
                    episode = self.episode(task_id, label, 85, index < 2, 2.0)
                rows.append({"state": "graded", "episode": episode})
        decision = live.analyse({"rows": rows}, self.manifest)
        self.assertEqual("provisional-candidate", decision["policy_decision"])
        self.assertEqual("sonnet-xhigh", decision["selected_candidate"])
        self.assertEqual(1, decision["reserved_repetitions_if_q4_freezes"])
        opus = next(row for row in decision["candidates"]
                    if row["episode_label"] == "opus-high")
        self.assertFalse(opus["qualifies"])

    def test_continuation_preserves_failure_and_original_envelope(self):
        # The predecessor is sealed historical evidence, not current launch
        # authority. Current code must reject its source drift. Only this
        # read-only continuation-arithmetic test substitutes the frozen
        # predecessor for the source re-derivation; production validation is
        # unchanged and a new paid dispatch remains closed.
        predecessor = json.loads(screen.MANIFEST.read_text(encoding="utf-8"))
        frozen_date = dt.date.fromisoformat(predecessor["date_utc"])

        class FrozenClock:
            @staticmethod
            def now(timezone):
                return dt.datetime.combine(frozen_date, dt.time.min,
                                           tzinfo=timezone)

        historical_dt = SimpleNamespace(date=dt.date, datetime=FrozenClock,
                                        timezone=dt.timezone)
        host_validate = screen.q4_host.validate
        with (patch.object(screen, "dt", historical_dt),
              patch.object(screen.q4_host, "validate",
                           side_effect=lambda value, check_host: host_validate(
                               value, check_host=False))):
            with self.assertRaisesRegex(screen.ScreenError,
                                        "M3 manifest differs from current inputs"):
                screen.validate(predecessor)
            with patch.object(screen, "build_manifest", return_value=predecessor):
                value = continuation.build_manifest(
                    dt.datetime.now(dt.timezone.utc).date().isoformat(),
                    sha(continuation.NOTICE))
        if frozen_date != dt.datetime.now(dt.timezone.utc).date():
            with self.assertRaisesRegex(screen.ScreenError, "today's UTC date"):
                screen.validate(predecessor)
        self.assertEqual(list(range(4, 17)), value["remaining_sequences"])
        self.assertEqual([1, 2, 3], value["inherited_sequences"])
        self.assertEqual(13, len(value["rows"]))
        self.assertLessEqual(value["cost"]["combined_maximum_usd"], 99)
        self.assertLessEqual(value["cost"]["combined_maximum_provider_calls"], 51)
        self.assertEqual(2.323065001, value["cost"]["prior_spent_usd"])
        self.assertEqual(3, value["cost"]["prior_provider_calls"])
        self.assertEqual({name: sha(ROOT / name) for name in continuation.SOURCES},
                         value["source_sha256"])


if __name__ == "__main__":
    unittest.main()
