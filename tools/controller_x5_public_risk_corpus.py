#!/usr/bin/env python3
"""Freeze the prospective K01 public-risk review case and negative controls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import controller_evaluation
import controller_x5_public_risk_review as review


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "test/fixtures/controller_x5_public_risk"
CASE = BASE / "development/K01"
CATALOGUE = BASE / "catalogue-k01.json"
CASE_K02 = BASE / "development/K02"
CATALOGUE_K02 = BASE / "catalogue-k02.json"


class CorpusStop(ValueError):
    """The case or rubric differs from its frozen public package."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(directory: Path) -> dict[str, str]:
    if directory.is_symlink() or not directory.is_dir():
        raise CorpusStop("missing or redirected fixture tree")
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
        files[relative] = digest(path.read_bytes())
    if not files:
        raise CorpusStop("fixture tree is empty")
    return dict(sorted(files.items()))


def freeze() -> dict:
    actor = inventory(CASE / "actor")
    editable = ["auth_gateway.py", "tenant_keys.py"]
    acceptance = json.loads((CASE / "actor/acceptance.json").read_text(encoding="utf-8"))
    if (acceptance != {"editable_paths": editable,
                       "public_command": ["python3", "-B", "public_check.py"]}
            or not set(editable).issubset(actor)
            or "ISSUE.md" not in actor or "public_check.py" not in actor):
        raise CorpusStop("actor public contract differs")
    risk = json.loads((CASE / "risk.json").read_text(encoding="utf-8"))
    risk_digest = controller_evaluation.digest(risk)
    try:
        review.qualify_risk({name: (CASE / "actor" / name).read_bytes()
                             for name in actor}, risk, risk_digest)
    except review.ReviewStop as exc:
        raise CorpusStop(str(exc)) from exc
    overlays = {}
    for variant in ("partial", "reference", "alternative"):
        files = inventory(CASE / "variants" / variant)
        if not set(files).issubset(editable):
            raise CorpusStop("variant edits outside allowed paths")
        overlays[variant] = files
    oracle = ROOT / "test/oracles/controller_x5_public_risk/K01_hidden.py"
    if oracle.is_symlink() or not oracle.is_file() or oracle.name in actor:
        raise CorpusStop("protected oracle is not isolated")
    controls = json.loads((BASE / "controls.json").read_text(encoding="utf-8"))
    if (not isinstance(controls, list) or len(controls) != 2
            or {item.get("id") for item in controls} != {"C01", "M01"}
            or any(item.get("eligible") is not False for item in controls)):
        raise CorpusStop("negative controls differ")
    body = {"schema_version": 1, "split": "development",
            "case": {"id": "K01", "upstream": "https://github.com/jpadilla/pyjwt",
                     "upstream_commit": "1d41a6478e1562e68ff667fcd703356acf085f68",
                     "issue_origin": "authored gateway regression using pinned PyJWT source",
                     "licence": "MIT", "editable_paths": editable,
                     "public_command": ["python3", "-B", "public_check.py"],
                     "actor_files": actor, "overlays": overlays,
                     "oracle_sha256": digest(oracle.read_bytes()),
                     "risk": risk, "risk_digest": risk_digest},
            "negative_controls": controls,
            "controls_sha256": digest((BASE / "controls.json").read_bytes())}
    body["catalogue_sha256"] = controller_evaluation.digest(body)
    return body


def freeze_k02() -> dict:
    actor = inventory(CASE_K02 / "actor")
    editable = ["payment_service.py", "retry_policy.py"]
    acceptance = json.loads((CASE_K02 / "actor/acceptance.json").read_text(encoding="utf-8"))
    if (acceptance != {"editable_paths": editable,
                       "public_command": ["python3", "-B", "public_check.py"]}
            or not set(editable).issubset(actor)
            or "ISSUE.md" not in actor or "public_check.py" not in actor):
        raise CorpusStop("K02 public contract differs")
    risk = json.loads((CASE_K02 / "risk.json").read_text(encoding="utf-8"))
    risk_digest = controller_evaluation.digest(risk)
    try:
        review.qualify_risk({name: (CASE_K02 / "actor" / name).read_bytes()
                             for name in actor}, risk, risk_digest)
    except review.ReviewStop as exc:
        raise CorpusStop(str(exc)) from exc
    overlays = {}
    for variant in ("partial", "reference", "alternative"):
        files = inventory(CASE_K02 / "variants" / variant)
        if not set(files).issubset(editable):
            raise CorpusStop("K02 variant edits outside allowed paths")
        overlays[variant] = files
    oracle = ROOT / "test/oracles/controller_x5_public_risk/K02_hidden.py"
    if oracle.is_symlink() or not oracle.is_file() or oracle.name in actor:
        raise CorpusStop("K02 protected oracle is not isolated")
    controls_path = BASE / "controls-k02.json"
    controls = json.loads(controls_path.read_text(encoding="utf-8"))
    if (not isinstance(controls, list) or len(controls) != 2
            or {item.get("id") for item in controls} != {"C02", "M02"}
            or any(item.get("eligible") is not False for item in controls)):
        raise CorpusStop("K02 negative controls differ")
    body = {"schema_version": 1, "split": "development",
            "case": {"id": "K02", "upstream": "https://github.com/jd/tenacity",
                     "upstream_commit": "3e58094d3bc414975aad9eadf343a32bdb3b89b3",
                     "issue_origin": "authored payment regression on pinned Tenacity source",
                     "licence": "Apache-2.0", "editable_paths": editable,
                     "public_command": ["python3", "-B", "public_check.py"],
                     "actor_files": actor, "overlays": overlays,
                     "oracle_sha256": digest(oracle.read_bytes()),
                     "risk": risk, "risk_digest": risk_digest},
            "negative_controls": controls,
            "controls_sha256": digest(controls_path.read_bytes())}
    body["catalogue_sha256"] = controller_evaluation.digest(body)
    return body


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--case", choices=("K01", "K02"), default="K01")
    args = parser.parse_args()
    expected = freeze() if args.case == "K01" else freeze_k02()
    catalogue = CATALOGUE if args.case == "K01" else CATALOGUE_K02
    if args.freeze:
        with catalogue.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(expected, sort_keys=True, indent=2) + "\n")
    elif (catalogue.is_symlink() or not catalogue.is_file()
          or json.loads(catalogue.read_text(encoding="utf-8")) != expected):
        raise CorpusStop("frozen catalogue differs from public case and oracle")
    print(json.dumps({"catalogue_sha256": expected["catalogue_sha256"],
                      "case": expected["case"]["id"]}))


if __name__ == "__main__":
    main()
