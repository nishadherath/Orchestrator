#!/usr/bin/env python3
"""Freeze the provider-free H03 actor, risk decision and private calibration."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "test" / "fixtures" / "controller_x5_h03"
ACTOR = FIXTURE / "actor"
RESULTS = ROOT / "test" / "results"
CATALOGUE = FIXTURE / "catalogue.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def line_of(source: str, quote: str) -> int:
    lines = source.splitlines()
    hits = [number for number, line in enumerate(lines, 1) if quote in line]
    if len(hits) != 1:
        raise RuntimeError(f"expected one public citation for {quote!r}, found {len(hits)}")
    return hits[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify the frozen catalogue and every bound byte")
    args = parser.parse_args()
    if CATALOGUE.exists() and not args.check:
        raise FileExistsError("H03 catalogue already frozen; do not overwrite")
    source_path = ACTOR / "tools" / "system_controller.py"
    source = source_path.read_text(encoding="utf-8")
    public_check = (ACTOR / "public_check.py").read_text(encoding="utf-8")
    spec = importlib.util.spec_from_file_location("h03_fixture", ROOT / "tools" / "controller_x5_h03_fixture.py")
    assert spec and spec.loader
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    derived = fixture.old_source((ROOT / "tools" / "system_controller.py").read_text(encoding="utf-8"))
    if derived != source:
        raise RuntimeError("actor baseline no longer derives from the current repaired source")
    if fixture.ISSUE != (ACTOR / "ISSUE.md").read_text(encoding="utf-8"):
        raise RuntimeError("H03 issue differs from its generator")
    if fixture.PUBLIC_CHECK != public_check:
        raise RuntimeError("H03 public check differs from its generator")
    actor_files: dict[str, str] = {}
    total = 0
    for path in sorted(ACTOR.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"actor symlink: {path}")
        if path.is_file():
            if path.suffix == ".pyc" or "__pycache__" in path.parts:
                raise RuntimeError(f"actor cache artefact: {path}")
            relative = path.relative_to(ACTOR).as_posix()
            actor_files[relative] = file_sha(path)
            total += path.stat().st_size
    if len(actor_files) > 200 or total > 2_500_000:
        raise RuntimeError("H03 actor exceeds its frozen file or byte ceiling")
    probes = {}
    for host, name in (("windows", "2026-09-30-controller-x5-h03-probe.json"),
                       ("wsl", "2026-09-30-controller-x5-h03-wsl-probe.json")):
        path = RESULTS / name
        row = json.loads(path.read_text(encoding="utf-8"))
        if (row["actor_files"] != len(actor_files) or row["actor_bytes"] != total
                or row["baseline_source_sha256"] != actor_files["tools/system_controller.py"]
                or [row[variant]["oracle"]["score"] for variant in
                    ("baseline", "partial", "alternative", "reference")] != [10, 45, 100, 100]
                or row["provider_calls"] != 0):
            raise RuntimeError(f"{host} calibration no longer matches the H03 actor")
        probes[host] = {"path": path.relative_to(ROOT).as_posix(), "sha256": file_sha(path),
                        "python": row["python"], "platform": row["platform"]}
    quotes = {
        "precommit_gap": ("tools/system_controller.py", "accepted, rejected = scribe.write(records"),
        "verify_reentry": ("tools/system_controller.py", 'recs = call("frame", "framer", frame_prompt)'),
        "critique_reentry": ("tools/system_controller.py", 'recs = call("frame", "framer", build_frame_prompt(problem, [], prior_ledger, falsified))'),
        "public_coverage": ("public_check.py", 'scripted[("frame", "framer")] = [changed, canned["frame_v1"], canned["frame_v2"]]'),
    }
    citations = {}
    for key, (relative, quote) in quotes.items():
        body = source if relative.startswith("tools/") else public_check
        citations[key] = {"path": relative, "line": line_of(body, quote), "quote": quote,
                          "file_sha256": actor_files[relative]}
    private = {}
    for relative in ("oracle.py", "variants/reference/system_controller.py",
                     "variants/alternative/system_controller.py",
                     "variants/partial/system_controller.py"):
        private[relative] = file_sha(FIXTURE / relative)
    catalogue = {
        "schema_version": 1, "case_id": "H03", "status": "authored-retrospective-development",
        "provider_calls": 0, "actor_files": actor_files, "actor_file_count": len(actor_files),
        "actor_bytes": total, "editable_paths": ["tools/system_controller.py"],
        "risk": {
            "decision": "public-review-eligible-if-producer-passes",
            "unresolved_premise": "A correction that passes the initial-frame public check also guards both re-entry paths and commits no records from a rejected Framer batch.",
            "next_public_check": "Exercise a changed acceptance list on verification and critique re-entry; inspect the ledger for partial commits.",
            "citations": citations,
            "controls": [
                {"id": "C03", "decision": "do-not-review", "reason": "No external acceptance contract is frozen."},
                {"id": "M03", "decision": "clarify", "reason": "Caller asks to replace criteria without an authoritative revised contract."},
            ],
        },
        "private_sha256": private, "probes": probes,
        "limits": ["One retrospective development case is not a powered effect estimate.",
                   "The actor is reconstructed from this project's real H02 integration failure, not a blind upstream issue."],
    }
    catalogue["catalogue_sha256"] = sha(canonical(catalogue))
    if args.check:
        if json.loads(CATALOGUE.read_text(encoding="utf-8")) != catalogue:
            raise RuntimeError("H03 frozen catalogue differs from current actor or evidence")
        print(json.dumps({"catalogue": str(CATALOGUE), "sha256": catalogue["catalogue_sha256"],
                          "status": "valid"}, sort_keys=True))
        return
    with CATALOGUE.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(catalogue, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"catalogue": str(CATALOGUE), "sha256": catalogue["catalogue_sha256"],
                      "files": len(actor_files), "bytes": total}, sort_keys=True))


if __name__ == "__main__":
    main()
