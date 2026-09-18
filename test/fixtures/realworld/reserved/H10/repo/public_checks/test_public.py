import unittest
from exports.retention import NeedClarification, cleanup


class RetentionTests(unittest.TestCase):
    def test_missing_decision_requests_clarification(self):
        with self.assertRaises(NeedClarification): cleanup([], 100)


if __name__ == "__main__": unittest.main()
