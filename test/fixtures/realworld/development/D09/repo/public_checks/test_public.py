import unittest

from orders.cli import render_order
from orders.parser import parse_order
from orders.types import ParseResult


class PublicResultMigrationTests(unittest.TestCase):
    def test_parser_returns_named_non_tuple_result(self):
        parsed = parse_order("A17,12.50")
        self.assertIsInstance(parsed, ParseResult)
        self.assertNotIsInstance(parsed, tuple)
        self.assertEqual(parsed.order.order_id, "A17")
        self.assertEqual(parsed.warnings, ("note missing",))

    def test_cli_uses_named_result(self):
        self.assertEqual(render_order("A17,12.50,priority"), "A17: 12.50")


if __name__ == "__main__":
    unittest.main()
