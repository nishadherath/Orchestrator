import unittest
from runner.recovery import run


class RecoveryTests(unittest.TestCase):
    def test_success_cost_is_recorded(self):
        self.assertEqual(run({}, [{"status":"success","cost_usd":0.2}], 1)["spent_usd"], 0.2)


if __name__ == "__main__": unittest.main()
