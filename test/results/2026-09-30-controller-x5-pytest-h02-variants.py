"""Preserve E01's pinned proposal and narrow control as H02 calibration overlays."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02"
EXPECTED = {
    "proposal": "558f5ab0e7c357d253f26ccb34df3779a04f39db778a94188f843e316c8e6fd2",
    "narrow_control": "121696c4633991eeccc1284919031f732f8a285cf1bc6c0265637f9d30952513",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: variants.py <proposal-checkout> <narrow-control-checkout>")
    result: dict[str, str] = {}
    for name, raw in zip(EXPECTED, sys.argv[1:], strict=True):
        source = Path(raw).resolve() / "pytest_asyncio/plugin.py"
        observed = sha(source)
        if observed != EXPECTED[name]:
            raise ValueError(f"{name} source hash differs: {observed}")
        target = CASE / "variants" / name / "pytest_asyncio"
        if target.exists():
            raise ValueError(f"variant already exists: {target}")
        target.mkdir(parents=True)
        shutil.copyfile(source, target / "plugin.py")
        shutil.copyfile(CASE / "actor/pytest_asyncio/__init__.py", target / "__init__.py")
        result[name] = observed
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
