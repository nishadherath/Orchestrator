"""Provider-free checks for the frozen B02 resource task variants."""
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

from worker_q4u_boltons import (B02Error, EVALUATOR, FIXTURES,  # noqa: E402
                                actor_files, calibrate, check)


class B02Tests(unittest.TestCase):
    def test_both_public_actors_are_sealed_without_evaluator_material(self):
        weak, strong = check("B02W"), check("B02S")
        self.assertEqual(weak["evaluator_zip_sha256"], strong["evaluator_zip_sha256"])
        self.assertNotEqual(weak["task_sha256"], strong["task_sha256"])
        for task_id in ("B02W", "B02S"):
            names = set(actor_files(FIXTURES / task_id / "actor"))
            self.assertEqual(6, len(names))
            self.assertFalse(any(name.startswith("reference/") or
                                 name.startswith("partial/") or
                                 name == "grader.py" for name in names))

    def test_weak_and_strong_checks_share_hidden_grades(self):
        weak, strong = calibrate("B02W"), calibrate("B02S")
        for value in (weak, strong):
            self.assertEqual(0, value["provider_calls"])
            self.assertEqual([30, 65, 100],
                             [value["grades"][name]["score"] for name in
                              ("baseline", "partial", "reference")])
        self.assertEqual([True, True, True],
                         [weak["grades"][name]["public_pass"] for name in
                          ("baseline", "partial", "reference")])
        self.assertEqual([False, False, True],
                         [strong["grades"][name]["public_pass"] for name in
                          ("baseline", "partial", "reference")])

    def test_plain_public_commands_run_without_external_package_path(self):
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        for task_id, expected in (("B02W", 0), ("B02S", 1)):
            actor = FIXTURES / task_id / "actor"
            result = subprocess.run([sys.executable, "-B", "-S", "public_check.py"],
                                    cwd=actor, env=env, capture_output=True,
                                    text=True, timeout=30)
            self.assertEqual(expected, 0 if result.returncode == 0 else 1)
            self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_tampering_actor_or_evaluator_fails(self):
        temp_root = ROOT / "pilot-runs/q4u-test-temp"
        temp_root.mkdir(parents=True, exist_ok=True)
        self.assertTrue(temp_root.resolve().is_relative_to(ROOT.resolve()))
        with tempfile.TemporaryDirectory(prefix="b02-test-", dir=temp_root) as temporary:
            folder = Path(temporary).resolve()
            self.assertTrue(folder.is_relative_to(temp_root.resolve()))
            shutil.copytree(FIXTURES / "B02W", folder / "B02W")
            archive = folder / "B02.zip"
            shutil.copy2(EVALUATOR, archive)
            self.assertEqual(check("B02W")["task_sha256"],
                             check("B02W", archive, folder)["task_sha256"])
            issue = folder / "B02W/actor/ISSUE.md"
            with issue.open("a", encoding="utf-8") as stream:
                stream.write("tampered\n")
            with self.assertRaisesRegex(B02Error, "actor byte changed"):
                check("B02W", archive, folder)
            shutil.copy2(FIXTURES / "B02W/actor/ISSUE.md", issue)
            with archive.open("ab") as stream:
                stream.write(b"tampered")
            with self.assertRaisesRegex(B02Error, "evaluator seal differs"):
                check("B02W", archive, folder)


if __name__ == "__main__":
    unittest.main()
