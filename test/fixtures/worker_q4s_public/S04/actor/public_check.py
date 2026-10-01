"""Public smoke test for constructor-based collection reduction."""
import pickle
import unittest

from sortedcontainers import SortedList


class ReductionTest(unittest.TestCase):
    def test_list_reducer_uses_values(self):
        collection = SortedList([3, 1, 2])
        reduce_function, args = collection.__reduce__()[:2]
        self.assertIs(reduce_function, SortedList)
        self.assertEqual(args, ([1, 2, 3],))
        self.assertEqual(list(pickle.loads(pickle.dumps(collection))), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
