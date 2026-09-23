import os
import sys
import unittest
from pathlib import Path

ACTOR_ROOT = Path(os.environ["REALWORLD_ACTOR_ROOT"])
sys.path.insert(0, str(ACTOR_ROOT))

from service.reports import ReportService


class HiddenTenantCacheTests(unittest.TestCase):
    def make_service(self):
        calls = []

        def load(tenant, record, options):
            calls.append((tenant, record, dict(options)))
            return {"tenant": tenant, "record": record, "options": dict(options)}

        return ReportService(load, {}), calls

    def test_interleaved_tenants_never_cross(self):
        service, calls = self.make_service()
        north = service.get("north", 17, {"format": "brief"})
        south = service.get("south", 17, {"format": "brief"})
        self.assertEqual(north["tenant"], "north")
        self.assertEqual(south["tenant"], "south")
        self.assertEqual(len(calls), 2)

    def test_options_are_part_of_the_key(self):
        service, calls = self.make_service()
        brief = service.get("north", 17, {"format": "brief", "currency": "AUD"})
        full = service.get("north", 17, {"format": "full", "currency": "AUD"})
        self.assertEqual(brief["options"]["format"], "brief")
        self.assertEqual(full["options"]["format"], "full")
        self.assertEqual(len(calls), 2)

    def test_option_order_does_not_destroy_a_valid_hit(self):
        service, calls = self.make_service()
        first = service.get("north", 17, {"format": "brief", "currency": "AUD"})
        second = service.get("north", 17, {"currency": "AUD", "format": "brief"})
        self.assertIs(first, second)
        self.assertEqual(len(calls), 1)

    def test_repeated_identical_request_is_a_cache_hit(self):
        service, calls = self.make_service()
        first = service.get("tenant-with-long-name", 991, {})
        second = service.get("tenant-with-long-name", 991, {})
        self.assertIs(first, second)
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
