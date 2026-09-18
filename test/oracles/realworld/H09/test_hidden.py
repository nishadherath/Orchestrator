import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from shared.schema import Result, make_result
from consumers.api import render
from consumers.export import export


class HiddenSchemaTests(unittest.TestCase):
    def test_contract_and_consumers_agree(self):
        result = make_result(9, ["late"])
        self.assertEqual((result.value, result.warnings), (9, ("late",)))
        self.assertEqual(render(result), {"value":9,"warnings":["late"]})
        self.assertEqual(export(result), "9|late")
        with self.assertRaises((AttributeError, TypeError)): result.value = 10


if __name__ == "__main__": unittest.main()
