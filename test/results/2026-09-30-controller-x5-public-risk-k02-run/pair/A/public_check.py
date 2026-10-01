"""Public checks for the reported pre-debit response loss."""

import unittest

from gateway import Gateway
from payment_service import submit_payment


class CheckoutChecks(unittest.TestCase):
    def test_pre_debit_timeout_retries_once(self):
        gateway = Gateway("before")
        receipt = submit_payment(gateway, "order-2048", 2400)
        self.assertEqual("order-2048", receipt["payment_id"])
        self.assertEqual(2400, receipt["amount_cents"])
        self.assertEqual(2, len(gateway.calls))
        self.assertEqual(1, len(gateway.debits))

    def test_normal_payment_one_debit(self):
        gateway = Gateway()
        receipt = submit_payment(gateway, "order-2049", 500)
        self.assertEqual(1, receipt["debit_number"])
        self.assertEqual(1, len(gateway.calls))

    def test_permanent_error_is_not_retried(self):
        gateway = Gateway()
        with self.assertRaises(ValueError):
            submit_payment(gateway, "order-2050", -1)
        self.assertEqual(1, len(gateway.calls))
        self.assertEqual([], gateway.debits)


if __name__ == "__main__":
    unittest.main()
