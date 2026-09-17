import copy, os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from exports.retention import NeedClarification, cleanup


class HiddenRetentionTests(unittest.TestCase):
    def test_clarification_precedes_mutation(self):
        rows=[{"id":1,"day":1,"category":"ordinary"}]; before=copy.deepcopy(rows)
        with self.assertRaises(NeedClarification): cleanup(rows,100)
        self.assertEqual(rows,before)

    def test_answer_controls_retention_and_protection(self):
        rows=[{"id":1,"day":60,"category":"ordinary"},{"id":2,"day":1,"category":"legal"},{"id":3,"day":80,"category":"ordinary"}]
        removed=cleanup(rows,100,{"retention_days":30,"protected_categories":["legal"]})
        self.assertEqual(removed,[1]); self.assertEqual([r["id"] for r in rows],[2,3])


if __name__ == "__main__": unittest.main()
