#!/usr/bin/env python3
"""Offline rejection cases for Q3's two exact paid approval gates."""
from __future__ import annotations

import json
import datetime as dt
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_q3_live as live  # noqa: E402
import worker_q3_canary as canary  # noqa: E402
import worker_q3_sentinel_gate as sentinel  # noqa: E402


class Q3ApprovalTests(unittest.TestCase):
    def test_canary_manifest_freezes_only_two_public_b0_families(self) -> None:
        evidence = {"q3_host": "a" * 64, "subscription": "b" * 64,
                    "read_sentinel": "c" * 64}
        with (patch.object(canary, "current_evidence", return_value=evidence),
              patch.object(canary.q2, "check_catalogue"),
              patch.object(canary.q2, "check_evidence")):
            manifest = canary.build_manifest(
                spend_notice_sha256="d" * 64,
                date_utc=dt.datetime.now(dt.timezone.utc).date().isoformat(),
                evidence=evidence)
        self.assertEqual([row["task_id"] for row in manifest["rows"]],
                         ["P01", "P02"])
        self.assertTrue(all(row["ladder"] == canary.LADDER for row in
                            manifest["rows"]))
        self.assertEqual(manifest["cost"]["maximum_provider_calls"], 6)
        self.assertFalse(manifest["reserved_tasks_allowed"])
        self.assertEqual(manifest["manifest_sha256"], canary.digest({
            key: value for key, value in manifest.items()
            if key != "manifest_sha256"}))

    def test_canary_approval_is_bound_to_manifest_and_six_calls(self) -> None:
        manifest = {"manifest_sha256": "a" * 64,
                    "spend_notice_sha256": "b" * 64,
                    "credential_method": "claude-code-wsl-subscription"}
        approved = {"schema_version": 1, "decision": "approved",
                    "manifest_sha256": manifest["manifest_sha256"],
                    "maximum_authorised_usd": 12.0,
                    "maximum_provider_calls": 6,
                    "spend_notice_sha256": manifest["spend_notice_sha256"],
                    "credential_method": manifest["credential_method"],
                    "approved_by": "operator", "approved_at": "2026-09-25T00:00:00Z"}
        live.validate_approval(manifest, approved)
        for key, value in (("manifest_sha256", "c" * 64),
                           ("maximum_authorised_usd", 12.01),
                           ("maximum_provider_calls", 7),
                           ("credential_method", "api-key"),
                           ("decision", "approval-requested")):
            changed = {**approved, key: value}
            with self.subTest(key=key), self.assertRaises(live.LiveCanaryError):
                live.validate_approval(manifest, changed)

    def test_sentinel_approval_cannot_inherit_canary_authorisation(self) -> None:
        manifest = {"manifest_sha256": "d" * 64,
                    "notice_sha256": "e" * 64,
                    "credential_method": "claude-code-wsl-subscription"}
        approved = {"schema_version": 1, "decision": "approved",
                    "manifest_sha256": manifest["manifest_sha256"],
                    "maximum_authorised_usd": 0.10,
                    "notice_sha256": manifest["notice_sha256"],
                    "credential_method": manifest["credential_method"],
                    "approved_by": "operator", "approved_at": "2026-09-25T00:00:00Z"}
        with tempfile.TemporaryDirectory(prefix="q3-approval-") as raw:
            path = Path(raw) / "approval.json"
            with patch.object(sentinel, "APPROVAL", path):
                path.write_text(json.dumps(approved), encoding="utf-8")
                sentinel.approved(manifest)
                path.write_text(json.dumps({**approved,
                                            "maximum_authorised_usd": 12.0}),
                                encoding="utf-8")
                with self.assertRaises(sentinel.SentinelGateError):
                    sentinel.approved(manifest)

    def test_concurrent_sentinel_runners_can_only_start_one_call(self) -> None:
        manifest = {"manifest_sha256": "f" * 64}
        calls = []

        def fake_provider() -> dict:
            calls.append("started")
            time.sleep(0.05)
            return {"evidence_sha256": "e" * 64,
                    "reported_api_equivalent_cost_usd": 0.01}

        with tempfile.TemporaryDirectory(prefix="q3-sentinel-lock-") as raw:
            folder = Path(raw)
            with (patch.object(sentinel, "INTENT", folder / "intent.json"),
                  patch.object(sentinel, "OUTPUT", folder / "output.json"),
                  patch.object(sentinel, "check", return_value=manifest),
                  patch.object(sentinel.sentinel, "run", side_effect=fake_provider),
                  patch.object(sentinel.sentinel, "validate", return_value=True)):
                with ThreadPoolExecutor(max_workers=2) as workers:
                    futures = [workers.submit(sentinel.run) for _ in range(2)]
                    results = []
                    for future in futures:
                        try:
                            results.append(future.result())
                        except sentinel.SentinelGateError:
                            results.append("blocked")
        self.assertEqual(len(calls), 1)
        self.assertEqual(sum(isinstance(row, dict) for row in results), 1)
        self.assertEqual(results.count("blocked"), 1)


if __name__ == "__main__":
    unittest.main()
