"""Run the H02 symptom test against the actor's vendored pytest runtime."""

import os
import sys
from pathlib import Path

ACTOR = Path(__file__).resolve().parent
sys.path.insert(0, str(ACTOR / "deps"))
sys.path.insert(0, str(ACTOR / "deps/pygments-runtime.zip"))
sys.path.insert(0, str(ACTOR))
os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

import pytest  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(
        pytest.main(
            ["-q", "-p", "pytest_asyncio.plugin", "-p", "no:cacheprovider",
             str(ACTOR / "case/test_mre.py")]
        )
    )
