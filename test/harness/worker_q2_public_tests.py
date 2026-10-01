#!/usr/bin/env python3
"""Reject Q2 evidence that is internally inconsistent after digest renewal."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_q2_public as q2  # noqa: E402


class Q2EvidenceTests(unittest.TestCase):
    def test_saved_evidence_is_current(self) -> None:
        self.assertEqual(len(q2.check_evidence()["outcomes"]), 6)

    def reject_modified(self, field: str, value: object) -> None:
        record = copy.deepcopy(json.loads(q2.RESULT.read_text(encoding="utf-8")))
        record["outcomes"][0][field] = value
        record["evidence_sha256"] = q2.digest({key: item for key, item in record.items()
                                                if key != "evidence_sha256"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            with patch.object(q2, "RESULT", path), self.assertRaises(ValueError):
                q2.check_evidence()

    def test_rejects_rewritten_score(self) -> None:
        self.reject_modified("quality", 100)

    def test_rejects_rewritten_false_success(self) -> None:
        self.reject_modified("false_success", True)

    def test_rejects_rewritten_hidden_acceptance(self) -> None:
        self.reject_modified("hidden_acceptance", True)


if __name__ == "__main__":
    unittest.main()
