from datetime import datetime, timedelta, timezone
import os, sys, unittest
sys.path.insert(0, os.environ["REALWORLD_ACTOR_ROOT"])
from reporting.window import select


class HiddenWindowTests(unittest.TestCase):
    def test_offset_transition_and_half_open_end(self):
        start = datetime(2026,4,5,0,tzinfo=timezone(timedelta(hours=11)))
        end = datetime(2026,4,6,0,tzinfo=timezone(timedelta(hours=10)))
        rows = [
            {"id":"before","at":start.astimezone(timezone.utc)-timedelta(seconds=1)},
            {"id":"start","at":start.astimezone(timezone.utc)},
            {"id":"last","at":end.astimezone(timezone.utc)-timedelta(seconds=1)},
            {"id":"end","at":end.astimezone(timezone.utc)},
        ]
        self.assertEqual([r["id"] for r in select(rows, start, end)], ["start", "last"])
        self.assertEqual(select(rows, start, end), select(rows, start, end))


if __name__ == "__main__": unittest.main()
