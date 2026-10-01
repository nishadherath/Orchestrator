"""Freeze and verify the authored H01 development case before any paid use."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01"
ORACLE = ROOT / "test/oracles/controller_x5_authored_httpcore/H01_hidden.py"
PROBE = ROOT / "test/oracles/controller_x5_authored_httpcore/H01_probe.py"
CATALOGUE = CASE / "catalogue-h01.json"
CALIBRATION = ROOT / "test/results/2026-09-30-controller-x5-httpcore-calibration.json"
ISOLATION = ROOT / "test/results/2026-09-30-controller-x5-httpcore-isolation.json"
GRADE_CALIBRATION = ROOT / "test/results/2026-09-30-controller-x5-httpcore-grade-calibration.json"
POOLS = ("httpcore/_sync/connection_pool.py", "httpcore/_async/connection_pool.py")
EXPECTED_POOL_SHA = {
    POOLS[0]: "6be4fc2d3b14c5ceebd16c356ad7c7483a163e34347c0f1497b4b7f85d0c8fbd",
    POOLS[1]: "0ce210dacd9909ff6a7f0c61ccca6b4cf2ea08bf0ec465e2285eaa447c6f5726",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(directory: Path) -> dict[str, str]:
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError("fixture tree missing or redirected")
    files = {}
    for path in directory.rglob("*"):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink() or (path.is_dir() and path.name == "__pycache__"):
            raise RuntimeError(f"fixture path redirected or cached: {relative}")
        if path.is_file():
            if path.suffix == ".pyc":
                raise RuntimeError(f"compiled fixture file: {relative}")
            files[relative] = digest(path.read_bytes())
    return dict(sorted(files.items()))


def expected() -> dict:
    actor = inventory(CASE / "actor")
    if (any(actor.get(name) != value for name, value in EXPECTED_POOL_SHA.items())
            or not ORACLE.is_file() or ORACLE.is_symlink()
            or not PROBE.is_file() or PROBE.is_symlink()):
        raise RuntimeError("baseline source or protected oracle differs")
    source = json.loads((CASE / "actor/SOURCE.json").read_text(encoding="utf-8"))
    if (source.get("httpcore_release_commit")
            != "98209758cc14e1a5f966fe1dfdc1064b94055d8c"):
        raise RuntimeError("release commit differs")
    source_hashes = source["source_sha256"]
    if any(actor.get(name) != hash_ for name, hash_ in source_hashes.items()):
        raise RuntimeError("vendored source inventory differs")
    acceptance = json.loads((CASE / "actor/acceptance.json").read_text(encoding="utf-8"))
    if acceptance != {"schema_version": 1, "editable_paths": list(POOLS),
                      "public_command": ["python3", "-B", "public_check.py"]}:
        raise RuntimeError("actor contract differs")
    overlays = {}
    for label in ("partial", "reference", "alternative"):
        files = inventory(CASE / "variants" / label)
        if set(files) != set(POOLS):
            raise RuntimeError(f"{label} changes files outside editable set")
        overlays[label] = files
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    if not calibration.get("qualified"):
        raise RuntimeError("provider-free calibration failed")
    if {row["variant"]: row["pool_sha256"] for row in calibration["results"]} != {
            "baseline": {name: actor[name] for name in POOLS}, **overlays}:
        raise RuntimeError("calibration source differs from frozen overlays")
    isolation = json.loads(ISOLATION.read_text(encoding="utf-8"))
    if (not isolation.get("qualified") or isolation.get("case") != "H01"
            or {row["variant"] for row in isolation.get("rows", [])}
            != {"baseline", "partial", "reference", "alternative"}
            or any(not row.get("oracle_read_denied") for row in isolation["rows"])):
        raise RuntimeError("WSL namespace isolation receipt differs")
    grade = json.loads(GRADE_CALIBRATION.read_text(encoding="utf-8"))
    if (not grade.get("qualified") or grade.get("case") != "H01"
            or {row["variant"]: row["grade"]["quality"] for row in grade.get("rows", [])}
            != {"baseline": 25, "partial": 50, "reference": 100,
                "alternative": 100, "protected_edit": 0, "spoof": 0}):
        raise RuntimeError("evaluator-owned grade calibration differs")
    body = {"schema_version": 1, "split": "development", "case_id": "H01",
            "origin": "authored httpcore concurrency adaptation",
            "upstream": "https://github.com/encode/httpcore",
            "upstream_release_commit": source["httpcore_release_commit"],
            "actor_files": actor, "overlays": overlays,
            "oracle_sha256": digest(ORACLE.read_bytes()),
            "probe_sha256": digest(PROBE.read_bytes()),
            "calibration_sha256": digest(CALIBRATION.read_bytes()),
            "isolation_sha256": digest(ISOLATION.read_bytes()),
            "grade_calibration_sha256": digest(GRADE_CALIBRATION.read_bytes()),
            "editable_paths": list(POOLS), "public_command": acceptance["public_command"]}
    body["catalogue_sha256"] = digest(json.dumps(body, sort_keys=True,
                                                 separators=(",", ":")).encode("utf-8"))
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    body = expected()
    if args.freeze:
        with CATALOGUE.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(body, sort_keys=True, indent=2) + "\n")
    elif json.loads(CATALOGUE.read_text(encoding="utf-8")) != body:
        raise RuntimeError("H01 frozen catalogue differs")
    print(json.dumps({"case_id": "H01", "catalogue_sha256": body["catalogue_sha256"],
                      "actor_files": len(body["actor_files"])}))


if __name__ == "__main__":
    main()
