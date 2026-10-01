"""Provider-free calibration for the fresh public-risk review case."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import controller_x5_public_risk_corpus as corpus


CASE = ROOT / "test/fixtures/controller_x5_public_risk/development/K01"
ACTOR = CASE / "actor"
PROTECTED = ROOT / "test/oracles/controller_x5_public_risk/K01_hidden.py"
CASE_K02 = ROOT / "test/fixtures/controller_x5_public_risk/development/K02"
PROTECTED_K02 = ROOT / "test/oracles/controller_x5_public_risk/K02_hidden.py"


def check(variant: str, script: Path | str,
          case: Path = CASE) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="x5-risk-k01-") as temporary:
        destination = Path(temporary) / "actor"
        shutil.copytree(case / "actor", destination)
        if variant != "baseline":
            for source in (case / "variants" / variant).rglob("*.py"):
                relative = source.relative_to(case / "variants" / variant)
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(destination)
        return subprocess.run(
            [sys.executable, "-B", str(script)], cwd=destination,
            env=environment, capture_output=True, text=True, timeout=30,
            check=False,
        )


class PublicRiskFixtureTests(unittest.TestCase):
    def test_frozen_public_risk_and_controls(self) -> None:
        frozen = corpus.freeze()
        recorded = corpus.json.loads(corpus.CATALOGUE.read_text(encoding="utf-8"))
        self.assertEqual(recorded, frozen)
        self.assertEqual("K01", frozen["case"]["id"])
        self.assertTrue(frozen["case"]["risk"]["eligible"])
        self.assertEqual({"C01", "M01"},
                         {item["id"] for item in frozen["negative_controls"]})
        self.assertTrue(all(item["eligible"] is False
                            for item in frozen["negative_controls"]))

    def test_variant_matrix(self) -> None:
        expected = {
            "baseline": (False, False),
            "partial": (True, False),
            "reference": (True, True),
            "alternative": (True, True),
        }
        for variant, (public_pass, protected_pass) in expected.items():
            with self.subTest(variant=variant):
                public = check(variant, "public_check.py")
                protected = check(variant, PROTECTED)
                self.assertEqual(public_pass, public.returncode == 0,
                                 public.stdout + public.stderr)
                self.assertEqual(protected_pass, protected.returncode == 0,
                                 protected.stdout + protected.stderr)

    def test_k02_frozen_case_and_variant_matrix(self) -> None:
        frozen = corpus.freeze_k02()
        recorded = corpus.json.loads(corpus.CATALOGUE_K02.read_text(encoding="utf-8"))
        self.assertEqual(recorded, frozen)
        self.assertEqual("K02", frozen["case"]["id"])
        self.assertEqual({"C02", "M02"},
                         {item["id"] for item in frozen["negative_controls"]})
        expected = {"baseline": (False, False), "partial": (True, False),
                    "reference": (True, True), "alternative": (True, True)}
        for variant, (public_pass, protected_pass) in expected.items():
            with self.subTest(variant=variant):
                public = check(variant, "public_check.py", CASE_K02)
                protected = check(variant, PROTECTED_K02, CASE_K02)
                self.assertEqual(public_pass, public.returncode == 0,
                                 public.stdout + public.stderr)
                self.assertEqual(protected_pass, protected.returncode == 0,
                                 protected.stdout + protected.stderr)


if __name__ == "__main__":
    unittest.main()
