"""Run the unchanged offline suite with per-test wall timing."""
import time
import unittest
import argparse
import sys
from pathlib import Path


class TimedResult(unittest.TextTestResult):
    def startTest(self, test):
        self.started = time.monotonic()
        super().startTest(test)

    def stopTest(self, test):
        self.stream.writeln(f"  elapsed_seconds={time.monotonic() - self.started:.6f}")
        super().stopTest(test)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.repeat <= 10 or (args.case and not args.case.startswith("test_helpers.Helpers.test_")):
        parser.error("Select a helper test case and 1..10 repeats")
    sys.path.insert(0, str(Path(__file__).parent))
    suite = unittest.TestSuite()
    for _ in range(args.repeat):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName(args.case) if args.case else unittest.defaultTestLoader.discover(str(Path(__file__).parent)))
    result = unittest.TextTestRunner(verbosity=2, resultclass=TimedResult).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
