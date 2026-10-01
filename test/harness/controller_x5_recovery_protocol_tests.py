"""Provider-free gates for recovery eligibility and paired snapshots."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_recovery_protocol as protocol  # noqa: E402


def settled() -> dict:
    return {"root_id": "producer-r01", "state": "partial",
            "budget": {"spent_usd": 0.4, "limit_usd": 1.0,
                       "unresolved": [], "breached": False},
            "attempts": [{"process_state": "terminal", "receipt_digest": "abc",
                          "late_receipts": [], "receipt": {
                              "terminal": True, "writer_stopped": True,
                              "identity_valid": True, "actual_model": "fixture-model",
                              "cost_usd": 0.4}}]}


class RecoveryProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="x5-recovery-protocol-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.actor = self.base / "actor"
        source = ROOT / "test/fixtures/controller_x5_recovery/development/R01/actor"
        shutil.copytree(source, self.actor)

    def test_failed_public_check_qualifies_and_twins_match(self) -> None:
        dest = self.base / "pair"
        record = protocol.twins("R01", self.actor, settled(), dest)
        self.assertEqual(record["public_check_exit_code"], 1)
        for name, expected in record["actor_sha256"].items():
            self.assertEqual(protocol.digest((dest / "S" / name).read_bytes()), expected)
            self.assertEqual((dest / "S" / name).read_bytes(),
                             (dest / "A" / name).read_bytes())
        self.assertEqual(json.loads((dest / "snapshot.json").read_text()), record)
        with self.assertRaisesRegex(protocol.RecoveryStop, "already used"):
            protocol.twins("R01", self.actor, settled(), dest)

    def test_unsettled_or_active_writer_stops(self) -> None:
        for mutation in (
            lambda s: s["budget"].update(unresolved=["pending-invocation"]),
            lambda s: s["budget"].update(unresolved=False),
            lambda s: s["attempts"][0]["receipt"].update(writer_stopped=False),
            lambda s: s["attempts"][0].update(process_state="uncertain"),
            lambda s: s["attempts"][0].update(late_receipts=[{"conflict": True}]),
            lambda s: s["attempts"][0]["receipt"].update(cost_usd=0.3),
        ):
            with self.subTest(mutation=mutation):
                state = settled()
                mutation(state)
                with self.assertRaises(protocol.RecoveryStop):
                    protocol.qualify("R01", self.actor, state)

    def test_public_success_without_concrete_unresolved_test_does_not_qualify(self) -> None:
        reference = ROOT / "test/fixtures/controller_x5_recovery/development/R01/variants/reference"
        for source in reference.iterdir():
            shutil.copy2(source, self.actor / source.name)
        with self.assertRaisesRegex(protocol.RecoveryStop, "no publicly observable"):
            protocol.qualify("R01", self.actor, settled())

    def test_actor_tamper_and_oracle_copy_stop(self) -> None:
        (self.actor / "journal.py").unlink()
        (self.actor / "journal.py").symlink_to(self.actor / "delivery.py")
        with self.assertRaises(protocol.RecoveryStop):
            protocol.qualify("R01", self.actor, settled())
        (self.actor / "journal.py").unlink()
        source = ROOT / "test/fixtures/controller_x5_recovery/development/R01/actor/journal.py"
        shutil.copy2(source, self.actor / "journal.py")
        (self.actor / "R01.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(protocol.RecoveryStop, "unexpected actor"):
            protocol.qualify("R01", self.actor, settled())


if __name__ == "__main__":
    unittest.main()
