import unittest
from shared.schema import make_result
from consumers.api import render


class SchemaTests(unittest.TestCase):
    def test_api_renders_result(self): self.assertEqual(render(make_result(3))["value"], 3)


if __name__ == "__main__": unittest.main()
