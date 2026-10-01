"""Host-only K02 acceptance; run with the actor directory on PYTHONPATH."""

import io
import json
import unittest

from gateway import Gateway
from payment_service import submit_payment


class ProtectedCheckoutChecks(unittest.TestCase):
    def test_pre_debit_retry(self):
        gateway = Gateway("before")
        self.assertEqual("p-1", submit_payment(gateway, "p-1", 400)["payment_id"])
        self.assertEqual(1, len(gateway.debits))

    def test_timeout_after_debit_does_not_duplicate(self):
        gateway = Gateway("after")
        receipt = submit_payment(gateway, "p-2", 500)
        self.assertEqual("p-2", receipt["payment_id"])
        self.assertEqual(2, len(gateway.calls))
        self.assertEqual(1, len(gateway.debits))

    def test_repeated_logical_payment_reuses_receipt(self):
        gateway = Gateway()
        first = submit_payment(gateway, "p-3", 600)
        second = submit_payment(gateway, "p-3", 600)
        self.assertEqual(first, second)
        self.assertEqual(1, len(gateway.debits))

    def test_independent_payment_ids_are_independent(self):
        gateway = Gateway()
        submit_payment(gateway, "p-4", 700)
        submit_payment(gateway, "p-5", 700)
        self.assertEqual(2, len(gateway.debits))

    def test_permanent_error_stops(self):
        gateway = Gateway()
        with self.assertRaises(ValueError):
            submit_payment(gateway, "p-6", 0)
        self.assertEqual(1, len(gateway.calls))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProtectedCheckoutChecks)
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    failed = {test._testMethodName for test, _ in result.failures + result.errors}
    critical = {"test_timeout_after_debit_does_not_duplicate",
                "test_repeated_logical_payment_reuses_receipt"}
    cases = [{"name": name, "passed": name not in failed,
              "critical": name in critical, "weight": 2 if name in critical else 1}
             for name in sorted(method for method in dir(ProtectedCheckoutChecks)
                                if method.startswith("test_"))]
    print(json.dumps({"cases": cases}, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
