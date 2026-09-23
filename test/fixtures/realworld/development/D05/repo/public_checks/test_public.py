import unittest

from service.reports import ReportService


class ReportTests(unittest.TestCase):
    def test_tenants_do_not_share_a_record_entry(self):
        calls = []

        def load(tenant, record, options):
            calls.append((tenant, record, options))
            return f"{tenant}:{record}"

        service = ReportService(load, {})
        self.assertEqual(service.get("north", 7), "north:7")
        self.assertEqual(service.get("south", 7), "south:7")
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
