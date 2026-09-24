#!/usr/bin/env python3
"""Provider-free checks for the frozen N5 cell screen and approval gate."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_evaluation  # noqa: E402
import worker_n5_screen as screen  # noqa: E402


class ScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = screen.build_manifest(host_attestation_sha256="a" * 64)

    def test_inventory_and_cost_are_fixed_without_reserved_content(self):
        rows = self.manifest["rows"]
        self.assertEqual(60, len(rows))
        self.assertEqual(15, sum(row["kind"] == "identity" for row in rows))
        self.assertEqual(45, sum(row["kind"] == "microtask" for row in rows))
        self.assertEqual(48.75, sum(row["maximum_usd"] for row in rows))
        self.assertEqual(list(range(1, 61)), [row["sequence"] for row in rows])
        for index in range(0, 60, 4):
            tranche = rows[index:index + 4]
            self.assertEqual(1, len({row["cell"] for row in tranche}))
            self.assertEqual(["I00", "S01", "S02", "S03"],
                             [row["task"] for row in tranche])
        self.assertEqual(4, len([name for name in self.manifest["screen_files"]
                                 if name.startswith("I00/")]))
        self.assertFalse(any("reserved" in name.lower() for name in
                             self.manifest["screen_files"]))
        screen.validate_manifest(self.manifest)

    def test_manifest_and_fixture_drift_fail_closed(self):
        altered = copy.deepcopy(self.manifest)
        altered["rows"][0]["maximum_usd"] = 1.0
        with self.assertRaises(screen.ScreenError):
            screen.validate_manifest(altered)
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "screen"
            shutil.copytree(screen.SCREEN, fixture)
            (fixture / "S01" / "ISSUE.md").write_text("changed\n", encoding="utf-8")
            with self.assertRaises(screen.ScreenError):
                screen.validate_manifest(self.manifest, screen=fixture)
            shutil.copytree(screen.SCREEN, fixture, dirs_exist_ok=True)
            oracle = fixture / "oracles" / "S03.json"
            oracle.write_text(oracle.read_text(encoding="utf-8").replace(
                '"no_edit_baseline_sha256": "', '"no_edit_baseline_sha256": "0'),
                encoding="utf-8")
            with self.assertRaises(screen.ScreenError):
                screen.validate_fixtures(fixture)

    def test_approval_requires_frozen_method_notice_manifest_and_ceiling(self):
        approval = {"schema_version": 1, "decision": "approved",
                    "manifest_sha256": self.manifest["manifest_sha256"],
                    "maximum_authorised_usd": 48.75,
                    "credential_method": "unconfigured",
                    "spend_notice_sha256": None,
                    "approved_by": "operator", "approved_at": "2026-09-24T00:00:00Z"}
        with self.assertRaises(screen.ScreenError):
            screen.validate_authorisation(self.manifest, approval, check_host=False)

        bound = screen.build_manifest(credential_method="api_key",
                                      host_attestation_sha256="a" * 64,
                                      spend_notice_sha256="b" * 64)
        approval.update(manifest_sha256=bound["manifest_sha256"],
                        credential_method="api_key", spend_notice_sha256="b" * 64)
        screen.validate_authorisation(bound, approval, check_host=False)
        for key, replacement in (("manifest_sha256", "0" * 64),
                                 ("maximum_authorised_usd", 49.0),
                                 ("credential_method", "subscription"),
                                 ("spend_notice_sha256", "0" * 64)):
            changed = dict(approval, **{key: replacement})
            with self.subTest(key=key), self.assertRaises(screen.ScreenError):
                screen.validate_authorisation(bound, changed, check_host=False)

    def test_no_edit_microtask_starts_correct_and_is_penalised_for_edit(self):
        actor = screen.SCREEN / "S03"
        oracle = screen.SCREEN / "oracles" / "S03.json"
        grade = worker_evaluation._grade(oracle, actor, "accepted")
        self.assertTrue(grade["acceptance"])
        self.assertEqual(100, grade["quality"])
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "actor"
            shutil.copytree(actor, copied)
            (copied / "app.py").write_text("# unnecessary change\n" +
                                           (copied / "app.py").read_text(encoding="utf-8"),
                                           encoding="utf-8")
            changed = worker_evaluation._grade(oracle, copied, "accepted")
            self.assertFalse(changed["acceptance"])
            self.assertTrue(changed["critical_error"])
            self.assertEqual(0, changed["quality"])

    def test_microtask_oracles_have_independent_reference_solutions(self):
        def port(data):
            raw = data.get("port")
            if type(raw) is int:
                number = raw
            elif isinstance(raw, str) and raw.strip().isdigit():
                number = int(raw.strip())
            else:
                number = None
            return ({"port": number, "error": None} if number is not None
                    and 1 <= number <= 65535 else
                    {"port": None, "error": "invalid_port"})

        def stock(data):
            original = data["stock"]
            updated = dict(original)
            seen = set()
            for change in data["changes"]:
                if change["id"] in seen:
                    return {"stock": original, "error": "duplicate_id"}
                seen.add(change["id"])
                delta = change["delta"]
                if type(delta) is not int:
                    return {"stock": original, "error": "invalid_delta"}
                sku = change["sku"]
                updated[sku] = updated.get(sku, 0) + delta
                if updated[sku] < 0:
                    return {"stock": original, "error": "negative_stock"}
            return {"stock": updated, "error": None}

        for ident, reference in (("S01", port), ("S02", stock)):
            oracle = json.loads((screen.SCREEN / "oracles" / f"{ident}.json").read_text(
                encoding="utf-8"))
            self.assertGreaterEqual(len(oracle["cases"]), 4)
            for case in oracle["cases"]:
                with self.subTest(task=ident, milestone=case["milestone"]):
                    self.assertEqual(case["expected"], reference(case["input"]))
            baseline = worker_evaluation._grade(
                screen.SCREEN / "oracles" / f"{ident}.json",
                screen.SCREEN / ident, "accepted")
            self.assertFalse(baseline["acceptance"])


if __name__ == "__main__":
    unittest.main()
