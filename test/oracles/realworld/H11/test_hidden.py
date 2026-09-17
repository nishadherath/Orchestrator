import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from runner.recovery import run


class HiddenRecoveryTests(unittest.TestCase):
    def test_retry_retains_failed_cost(self):
        state=run({},[{"status":"timeout","cost_usd":0.2},{"status":"success","cost_usd":0.3}],1)
        self.assertEqual((state["status"],state["attempts"]),("complete",2)); self.assertAlmostEqual(state["spent_usd"],0.5)

    def test_partial_is_honest_and_budget_is_conserved(self):
        partial=run({},[{"status":"partial","cost_usd":0.2}],1)
        self.assertEqual((partial["status"],partial["reason"]),("incomplete","partial_output"))
        self.assertAlmostEqual(partial["spent_usd"],0.2)
        exhausted=run({},[{"status":"success","cost_usd":0.2}],0.1)
        self.assertEqual((exhausted["status"],exhausted["attempts"],exhausted["spent_usd"]),("incomplete",0,0.0))


if __name__ == "__main__": unittest.main()
