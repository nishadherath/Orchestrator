from decimal import Decimal
import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from billing.pricing import total
from labels.normalise import normalise


class HiddenBatchTests(unittest.TestCase):
    def test_independent_contracts(self):
        self.assertEqual(total([Decimal("1.005"), Decimal("0")]), Decimal("1.01"))
        self.assertIsInstance(total([Decimal("2.10")]), Decimal)
        self.assertEqual(normalise("  Alpha\t Beta\nGamma  "), "Alpha Beta Gamma")
        self.assertEqual(normalise("MiXeD"), "MiXeD")


if __name__ == "__main__": unittest.main()
