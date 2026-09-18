import json
import unittest
from pathlib import Path

from case_a.service.cleanup import expired


ROOT = Path(__file__).resolve().parents[1]


class PublicConstraintTests(unittest.TestCase):
    def test_case_a_repairs_day_conversion(self):
        now = 1_000_000
        records = [
            {"id": "old", "created_at": now - 3 * 86_400},
            {"id": "recent", "created_at": now - 86_400},
        ]
        self.assertEqual(expired(records, now, 2), ["old"])

    def test_both_resolutions_are_recorded(self):
        case_a = json.loads((ROOT / "case_a" / "resolution.json").read_text())
        case_b = json.loads((ROOT / "case_b" / "resolution.json").read_text())
        self.assertIn(case_a.get("action"), {"repair", "clarify"})
        self.assertIn(case_b.get("action"), {"repair", "clarify"})


if __name__ == "__main__":
    unittest.main()
