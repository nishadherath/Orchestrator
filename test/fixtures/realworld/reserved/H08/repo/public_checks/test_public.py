from decimal import Decimal
import unittest
from billing.pricing import total
from labels.normalise import normalise


class BatchTests(unittest.TestCase):
    def test_integration(self):
        self.assertEqual(total([Decimal("1.00"), Decimal("2.00")]), Decimal("3.00"))
        self.assertEqual(normalise("  one  "), "one")


if __name__ == "__main__": unittest.main()
