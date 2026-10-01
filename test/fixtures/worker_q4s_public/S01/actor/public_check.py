"""Public smoke test for generator assignment hooks."""
import unittest

import attrs


class HooksTest(unittest.TestCase):
    def test_generator_runs_on_both_sides_of_assignment(self):
        seen = []

        def hook(instance, attribute, value):
            seen.append(("before", instance.x, value))
            yield value * 2
            seen.append(("after", instance.x, value))

        @attrs.define(on_setattr=hook)
        class Item:
            x: int

        item = Item(2)
        item.x = 3
        self.assertEqual(item.x, 6)
        self.assertEqual(seen, [("before", 2, 3), ("after", 6, 3)])


if __name__ == "__main__":
    unittest.main()
