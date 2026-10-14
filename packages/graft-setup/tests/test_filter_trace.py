"""Actual xperf field semantics, PID correlation and safe output."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("filter_review", Path(__file__).resolve().parents[1] / "graft-setup/scripts/filter_trace.py")
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class FilterTrace(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "trace.csv"
            with path.open("w", newline="", encoding="utf-8") as stream:
                csv.writer(stream).writerows(rows)
            return review.analyse(path, 42)

    def event(self, phase, stamp, process):
        row = [phase, str(stamp), process, "99", "2", "irp", "READ",
               "WdFilter.sys", "file-object", "private-path", "context"]
        if phase.endswith("Comp"):
            row.append("3247239387861")  # completion Initial Time uses QPC
        return row + ["callback"]

    def test_unknown_completion_is_correlated_to_own_init_without_qpc_subtraction(self):
        result = self.run_rows([self.event("MiniFilterPreOpInit", 1000, "node.exe ( 42)"),
                                self.event("MiniFilterPreOpComp", 31000, '"Unknown" ( -1)')])
        self.assertEqual(result["modules"]["WdFilter.sys"]["max_callback_elapsed_us"], 30000)
        self.assertEqual(result["matched_callback_count"], 1)
        self.assertNotIn("private-path", str(result))
        self.assertNotIn("callback'", str(result))
        self.assertFalse(result["unique_timeout_cause_proven"])

    def test_reused_pointer_from_other_pid_does_not_inherit_target_identity(self):
        result = self.run_rows([self.event("MiniFilterPreOpInit", 1000, "node.exe (42)"),
                                self.event("MiniFilterPreOpInit", 2000, "node.exe (142)"),
                                self.event("MiniFilterPreOpComp", 31000, '"Unknown" (-1)')])
        self.assertEqual(result["matched_callback_count"], 0)


if __name__ == "__main__":
    unittest.main()
