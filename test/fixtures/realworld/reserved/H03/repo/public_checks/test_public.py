import unittest
from imports.csv_batch import import_batch


class ImportTests(unittest.TestCase):
    def test_valid_rows_import(self):
        store = {}
        import_batch("id,name\n1,Ada\n", store)
        self.assertEqual(store, {"1": "Ada"})


if __name__ == "__main__": unittest.main()
