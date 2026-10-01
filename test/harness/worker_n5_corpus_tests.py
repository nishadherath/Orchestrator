#!/usr/bin/env python3
"""Provider-free checks for the task-sensitive development and sealed splits."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import worker_evaluation  # noqa: E402
import worker_n5_corpus  # noqa: E402
import worker_selector  # noqa: E402


class CorpusTests(unittest.TestCase):
    def test_generated_files_and_balanced_public_assessments(self):
        planned = worker_n5_corpus.planned_files()
        self.assertEqual({name: path.read_text(encoding="utf-8") for name, path in
                          ((name, worker_n5_corpus.ROOT / name) for name in planned)}, planned)
        tasks = worker_evaluation.load_catalogue(worker_n5_corpus.ROOT)["tasks"]
        self.assertEqual(24, len(tasks))
        self.assertEqual({("development", k): 4 for k in
                          ("routine", "moderate", "complex")}
                         | {("reserved", k): 4 for k in
                            ("routine", "moderate", "complex")},
                         Counter((task["split"], task["assessment"]["complexity"])
                                 for task in tasks))
        self.assertEqual({"worker-sonnet-low", "worker-sonnet-high", "worker-opus-high"},
                         {worker_selector.PRIORS[task["assessment"]["complexity"]]
                          for task in tasks if task["split"] == "development"})

    def test_reference_passes_both_splits_and_public_only_attack_fails(self):
        tasks = worker_evaluation.load_catalogue(worker_n5_corpus.ROOT)["tasks"]
        with tempfile.TemporaryDirectory(prefix="worker-n5-corpus-") as tmp:
            actor = Path(tmp) / "actor"
            for task in tasks:
                source = worker_n5_corpus.ROOT / task["actor"]
                shutil.copytree(source, actor)
                oracle = worker_n5_corpus.ROOT / task["oracle"]
                (actor / "app.py").write_text(worker_n5_corpus.REFERENCE,
                                              encoding="utf-8")
                result = worker_evaluation._grade(oracle, actor, "accepted")
                self.assertTrue(result["acceptance"], task["id"])
                self.assertEqual(100, result["quality"], task["id"])
                data = json.loads(oracle.read_text(encoding="utf-8"))
                self.assertEqual(3, len(data["cases"]))
                # A worker that merely memorises the public examples must not
                # receive credit for any hidden input.
                number = int(task["id"][1:]) - 1
                spec = worker_n5_corpus.SPECS[number]
                offset = 0 if task["split"] == "development" else 5
                public = [{"kind": spec[2], **case}
                          for case in spec[4][offset:offset + 2]]
                lookup = {json.dumps(case, sort_keys=True):
                          worker_n5_corpus.reference_solve(case) for case in public}
                (actor / "app.py").write_text(
                    "import json,sys\nLOOKUP = " + repr(lookup) + "\n"
                    "def solve(data): return LOOKUP.get(json.dumps(data, sort_keys=True))\n"
                    "if __name__ == '__main__': print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n",
                    encoding="utf-8")
                weak = worker_evaluation._grade(oracle, actor, "accepted")
                self.assertFalse(weak["acceptance"], task["id"])
                self.assertTrue(weak["false_success"], task["id"])
                shutil.rmtree(actor)


if __name__ == "__main__":
    unittest.main()
