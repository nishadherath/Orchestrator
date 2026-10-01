"""Provider-free proof of the first frozen Q4U development actor."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from worker_q4u_public import (ACTOR, EVALUATOR, TASK, Q4UCorpusError,  # noqa: E402
                               calibrate, check, paths)

STRONG_TASK = ROOT / "test/fixtures/worker_q4u_public/D01S/task.json"


class Q4UPublicTests(unittest.TestCase):
    def test_sealed_actor_has_no_evaluator_material(self):
        value = check()
        self.assertEqual(13, value["actor_file_count"])
        self.assertEqual(64, len(value["task_sha256"]))
        actor_names = set(paths(ACTOR))
        self.assertNotIn("grader.py", actor_names)
        self.assertFalse(any(name.startswith("reference/") or
                             name.startswith("partial/") for name in actor_names))

    def test_plain_public_command_imports_actor_source(self):
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        process = subprocess.run([sys.executable, "-B", "-S", "public_check.py"],
                                 cwd=ACTOR, env=env, capture_output=True,
                                 text=True, timeout=30)
        self.assertEqual(0, process.returncode, process.stderr)

    def test_baseline_partial_and_reference_separate(self):
        value = calibrate()
        self.assertEqual(0, value["provider_calls"])
        self.assertEqual([15, 55, 100],
                         [value["grades"][name]["score"] for name in
                          ("baseline", "partial", "reference")])
        self.assertTrue(all(value["grades"][name]["public_pass"]
                            for name in ("baseline", "partial", "reference")))
        self.assertFalse(value["grades"]["baseline"]["cases"]["round_trip_double_slash"])
        self.assertFalse(value["grades"]["partial"]["cases"]["single_quote_boundary"])
        self.assertTrue(all(value["grades"]["reference"]["cases"].values()))

    def test_strong_public_check_separates_the_same_hidden_grades(self):
        binding = check(STRONG_TASK)
        self.assertEqual("D01S", binding["task_id"])
        self.assertEqual(check()["evaluator_zip_sha256"],
                         binding["evaluator_zip_sha256"])
        value = calibrate(STRONG_TASK)
        self.assertEqual([False, False, True],
                         [value["grades"][name]["public_pass"] for name in
                          ("baseline", "partial", "reference")])
        self.assertEqual([15, 55, 100],
                         [value["grades"][name]["score"] for name in
                          ("baseline", "partial", "reference")])

    def test_actor_and_evaluator_tampering_fail_closed(self):
        temp_root = ROOT / "pilot-runs/q4u-test-temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.assertTrue(temp_root.resolve().is_relative_to(ROOT.resolve()))
        with tempfile.TemporaryDirectory(prefix="d01w-test-", dir=temp_root) as temporary:
            folder = Path(temporary).resolve()
            self.assertTrue(folder.is_relative_to(temp_root.resolve()))
            task = folder / "D01W/task.json"
            task.parent.mkdir()
            shutil.copy2(TASK, task)
            shutil.copytree(ACTOR, task.parent / "actor")
            archive = folder / "D01W.zip"
            shutil.copy2(EVALUATOR, archive)
            self.assertEqual(check()["task_sha256"], check(task, archive)["task_sha256"])
            with (task.parent / "actor/ISSUE.md").open("a", encoding="utf-8") as stream:
                stream.write("tampered\n")
            with self.assertRaisesRegex(Q4UCorpusError, "actor byte changed"):
                check(task, archive)
            shutil.copy2(ACTOR / "ISSUE.md", task.parent / "actor/ISSUE.md")
            with archive.open("ab") as stream:
                stream.write(b"tampered")
            with self.assertRaisesRegex(Q4UCorpusError, "evaluator seal differs"):
                check(task, archive)


if __name__ == "__main__":
    unittest.main()
