"""Freeze the H02 actor and private tests before protected calibration."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02"
ACTOR = CASE / "actor"
ORACLE = ROOT / "test/oracles/controller_x5_authored_pytest/H02"
OUT = CASE / "catalogue-h02.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = json.loads((ACTOR / "SOURCE.json").read_text(encoding="utf-8"))
    actor_files = {path.relative_to(ACTOR).as_posix(): sha(path)
                   for path in sorted(ACTOR.rglob("*")) if path.is_file()}
    if len(actor_files) != 159:
        raise ValueError(f"H02 actor inventory differs: {len(actor_files)} files")
    if any(actor_files.get(name) != digest for name, digest in source["files"].items()):
        raise ValueError("H02 source manifest differs from actor")
    oracle_files = {path.relative_to(ORACLE).as_posix(): sha(path)
                    for path in sorted(ORACLE.rglob("*.py"))}
    if len(oracle_files) != 6:
        raise ValueError(f"H02 oracle inventory differs: {len(oracle_files)} files")
    body = {"schema_version": 1, "case_id": "H02",
            "origin": "authored development adaptation",
            "editable_paths": ["pytest_asyncio/plugin.py"],
            "actor_files": actor_files, "oracle_files": oracle_files,
            "weights": {"public": 20, "forward": 25, "reverse": 25,
                        "no_hook": 10, "upstream": 20}}
    body["catalogue_sha256"] = hashlib.sha256(json.dumps(
        body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(body, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"catalogue_sha256": body["catalogue_sha256"],
                      "actor_files": len(actor_files),
                      "oracle_files": len(oracle_files)}, sort_keys=True))


if __name__ == "__main__":
    main()
