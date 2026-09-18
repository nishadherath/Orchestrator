from datetime import datetime, timezone
import unittest
from reporting.window import select


class WindowTests(unittest.TestCase):
    def test_simple_window(self):
        rows = [{"id":1,"at":datetime(2026,1,1,1,tzinfo=timezone.utc)}]
        self.assertEqual(select(rows, datetime(2026,1,1,tzinfo=timezone.utc), datetime(2026,1,2,tzinfo=timezone.utc)), rows)


if __name__ == "__main__": unittest.main()
