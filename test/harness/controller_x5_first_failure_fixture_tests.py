"""Provider-free calibration for prospective first-failure development cases."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_first_failure_corpus as corpus  # noqa: E402


class FirstFailureFixtureTests(unittest.TestCase):
    def test_catalogue_and_independent_variants(self) -> None:
        frozen = json.loads(corpus.CATALOGUE.read_text(encoding="utf-8"))
        self.assertEqual(frozen, corpus.freeze())
        for row in frozen["cases"]:
            with self.subTest(case=row["id"]):
                case = corpus.BASE / "development" / row["id"]
                oracle = corpus.ORACLES / f"{row['id']}_hidden.py"
                self.assertEqual(row["oracle_sha256"], corpus.sha(oracle.read_bytes()))
                for variant in ("baseline", "partial", "reference", "alternative"):
                    with self.subTest(variant=variant):
                        with tempfile.TemporaryDirectory(prefix=f"x5-{row['id']}-{variant}-") as raw:
                            actor = Path(raw) / "actor"
                            shutil.copytree(case / "actor", actor)
                            if variant != "baseline":
                                for name in row["editable_paths"]:
                                    shutil.copy2(case / "variants" / variant / name,
                                                 actor / name)
                            before = corpus.inventory(actor)
                            public = subprocess.run(
                                [sys.executable, "-B", "public_check.py"], cwd=actor,
                                capture_output=True, text=True, timeout=20, check=False)
                            environment = dict(os.environ)
                            environment[f"X5_{row['id']}_ACTOR_ROOT"] = str(actor)
                            hidden = subprocess.run(
                                [sys.executable, "-B", str(oracle)], cwd=actor,
                                env=environment, capture_output=True, text=True,
                                timeout=20, check=False)
                            result = json.loads(hidden.stdout)
                            cases = result["cases"]
                            self.assertEqual(row["hidden_total"], len(cases))
                            self.assertEqual(len(cases), len({item["name"] for item in cases}))
                            self.assertTrue(all(type(item["passed"]) is bool
                                                and type(item["critical"]) is bool
                                                and item["weight"] > 0 for item in cases))
                            self.assertEqual(row["expected_hidden_passed"][variant],
                                             sum(item["passed"] for item in cases))
                            self.assertEqual(row["expected_public"][variant],
                                             public.returncode == 0,
                                             public.stderr[-500:])
                            self.assertEqual(0 if all(item["passed"] for item in cases) else 1,
                                             hidden.returncode, hidden.stderr[-500:])
                            self.assertEqual(before, corpus.inventory(actor))

    def test_unlisted_source_change_invalidates_catalogue(self) -> None:
        original = corpus.freeze()
        with tempfile.TemporaryDirectory(prefix="x5-fixture-tamper-") as raw:
            clone = Path(raw) / "fixtures"
            shutil.copytree(corpus.BASE, clone)
            check = clone / "development/F01/actor/public_check.py"
            check.write_text(check.read_text(encoding="utf-8") + "\n# tamper\n",
                             encoding="utf-8")
            old = corpus.BASE
            try:
                corpus.BASE = clone
                self.assertNotEqual(original, corpus.freeze())
            finally:
                corpus.BASE = old
        self.assertEqual(original, corpus.freeze())


if __name__ == "__main__":
    unittest.main()
