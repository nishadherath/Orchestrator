#!/usr/bin/env python3
"""Freeze and verify independent X5 first-failure development fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "test/fixtures/controller_x5_first_failure"
CATALOGUE = BASE / "catalogue-f03.json"
ORACLES = ROOT / "test/oracles/controller_x5_first_failure"
CASES = {
    "F01": {
        "upstream": "https://github.com/python-attrs/attrs",
        "upstream_commit": "8f767776326faaed11e6c2974798787f6e19b343",
        "upstream_source": "src/attr",
        "issue_origin": "authored regression on pinned upstream source; not an upstream issue",
        "licence": "MIT",
        "editable_paths": ["attr/_make.py", "attr/validators.py"],
        "public_command": ["python3", "-B", "public_check.py"],
        "expected_public": {"baseline": False, "partial": False,
                            "reference": True, "alternative": True},
        "expected_hidden_passed": {"baseline": 2, "partial": 4,
                                   "reference": 6, "alternative": 6},
        "hidden_total": 6,
    },
    "F02": {
        "upstream": "https://github.com/pallets/click",
        "upstream_commit": "06b2a678741131fd577ce170e23e5ca0aeba0309",
        "upstream_source": "src/click",
        "issue_origin": "authored regression on pinned upstream source; not an upstream issue",
        "licence": "BSD-3-Clause",
        "editable_paths": ["click/formatting.py", "click/_textwrap.py"],
        "public_command": ["python3", "-B", "public_check.py"],
        "expected_public": {"baseline": False, "partial": False,
                            "reference": True, "alternative": True},
        "expected_hidden_passed": {"baseline": 3, "partial": 6,
                                   "reference": 7, "alternative": 7},
        "hidden_total": 7,
    },
    "F03": {
        "upstream": "https://github.com/jd/tenacity",
        "upstream_commit": "3e58094d3bc414975aad9eadf343a32bdb3b89b3",
        "upstream_source": "tenacity",
        "issue_origin": "adapted from upstream cancellation report #529 with an authored async-default regression",
        "licence": "Apache-2.0",
        "editable_paths": ["tenacity/retry.py", "tenacity/asyncio/__init__.py"],
        "public_command": ["python3", "-B", "public_check.py"],
        "expected_public": {"baseline": False, "partial": False,
                            "reference": True, "alternative": True},
        "expected_hidden_passed": {"baseline": 4, "partial": 7,
                                   "reference": 9, "alternative": 9},
        "hidden_total": 9,
    },
}


class CorpusStop(ValueError):
    """A development case no longer matches its frozen package."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(directory: Path) -> dict[str, str]:
    if directory.is_symlink() or not directory.is_dir():
        raise CorpusStop(f"missing or redirected fixture tree: {directory}")
    files = {}
    for path in directory.rglob("*"):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            raise CorpusStop(f"redirected fixture path: {relative}")
        if path.is_dir():
            if path.name == "__pycache__":
                raise CorpusStop("fixture contains interpreter cache")
            continue
        if not path.is_file() or path.suffix == ".pyc":
            raise CorpusStop(f"unsupported fixture path: {relative}")
        files[relative] = sha(path.read_bytes())
    if not files:
        raise CorpusStop("fixture tree is empty")
    return dict(sorted(files.items()))


def case_record(case_id: str, metadata: dict) -> dict:
    root = BASE / "development" / case_id
    actor = inventory(root / "actor")
    editable = set(metadata["editable_paths"])
    if (not editable.issubset(actor)
            or not {"ISSUE.md", "LICENSE.txt", "acceptance.json", "public_check.py"}.issubset(actor)):
        raise CorpusStop("actor package lacks its public contract")
    acceptance = json.loads((root / "actor/acceptance.json").read_text(encoding="utf-8"))
    if (acceptance.get("editable_paths") != metadata["editable_paths"]
            or acceptance.get("public_command") != metadata["public_command"]):
        raise CorpusStop("actor acceptance differs from catalogue")
    variants = {}
    for variant in ("partial", "reference", "alternative"):
        files = inventory(root / "variants" / variant)
        if set(files) != editable:
            raise CorpusStop(f"{variant} overlay differs from editable paths")
        variants[variant] = files
    oracle = ORACLES / f"{case_id}_hidden.py"
    if oracle.is_symlink() or not oracle.is_file() or oracle.name in actor:
        raise CorpusStop("hidden oracle is missing or actor-visible")
    return {"id": case_id, **metadata, "actor_files": actor,
            "variants": variants, "oracle_sha256": sha(oracle.read_bytes()),
            "actor_total_bytes": sum((root / "actor" / name).stat().st_size for name in actor)}


def freeze() -> dict:
    body = {"schema_version": 1, "split": "development",
            "cases": [case_record(case_id, metadata)
                      for case_id, metadata in sorted(CASES.items())]}
    body["catalogue_sha256"] = sha(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode())
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = freeze()
    if args.freeze:
        with CATALOGUE.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(expected, sort_keys=True, indent=2) + "\n")
    else:
        if CATALOGUE.is_symlink() or not CATALOGUE.is_file():
            raise CorpusStop("frozen catalogue is missing")
        if json.loads(CATALOGUE.read_text(encoding="utf-8")) != expected:
            raise CorpusStop("frozen catalogue differs from fixture bytes")
    print(json.dumps({"catalogue_sha256": expected["catalogue_sha256"],
                      "cases": [row["id"] for row in expected["cases"]]}))


if __name__ == "__main__":
    main()
