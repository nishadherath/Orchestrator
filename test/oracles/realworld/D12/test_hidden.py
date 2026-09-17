import os
import sys
import unittest

sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from operations.diagnose import resolve


class HiddenDiagnosisTests(unittest.TestCase):
    def test_each_layer_has_one_action(self):
        self.assertEqual(resolve(False, False, False), "patch-source")
        self.assertEqual(resolve(True, False, True), "regenerate")
        self.assertEqual(resolve(True, True, False), "correct-invocation")
        self.assertEqual(resolve(True, True, True), "no-change")

    def test_operational_fault_does_not_become_source_patch(self):
        self.assertNotEqual(resolve(True, False, False), "patch-source")


if __name__ == "__main__":
    unittest.main()
