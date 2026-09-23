import os
import subprocess
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ACTOR_ROOT = Path(os.environ["REALWORLD_ACTOR_ROOT"])
sys.path.insert(0, str(ACTOR_ROOT))

from orders import Order, ParseResult, parse_order
from orders.batch import summarise
from orders.storage import save_parsed


class HiddenResultMigrationTests(unittest.TestCase):
    def test_result_is_named_immutable_and_not_tuple_compatible(self):
        parsed = parse_order("B99,7.25")
        self.assertIsInstance(parsed, ParseResult)
        self.assertNotIsInstance(parsed, tuple)
        self.assertIsInstance(parsed.order, Order)
        self.assertEqual(parsed.warnings, ("note missing",))
        with self.assertRaises((AttributeError, TypeError)):
            parsed.warnings = ()

    def test_storage_and_batch_use_the_new_shape(self):
        records = []
        parsed = parse_order("B99,7.25,gift")
        self.assertEqual(save_parsed(records.append, parsed), "B99")
        self.assertEqual(records, [{
            "order_id": "B99",
            "total": "7.25",
            "note": "gift",
            "warnings": [],
        }])
        self.assertEqual(
            summarise(["B99,7.25,gift", "C10,2.75"]),
            {"count": 2, "total": Decimal("10.00"), "warnings": 1},
        )

    def test_package_entry_point_uses_the_new_contract(self):
        completed = subprocess.run(
            [sys.executable, "-m", "orders", "Z5,3.50"],
            cwd=ACTOR_ROOT,
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "Z5: 3.50 warnings=note missing")


if __name__ == "__main__":
    unittest.main()
