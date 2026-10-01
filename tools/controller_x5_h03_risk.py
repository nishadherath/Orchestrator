#!/usr/bin/env python3
"""Freeze/check H03's public-only post-success risk gate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import controller_evaluation
import controller_x5_public_risk_review as review


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "test" / "fixtures" / "controller_x5_h03"
RESULTS = ROOT / "test" / "results"
CATALOGUE = FIXTURE / "catalogue.json"
MANIFEST = FIXTURE / "risk-manifest.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected() -> dict:
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if catalogue["catalogue_sha256"] != "92e333e2dfa2d493e653a778ecd37a93aa0746aa322d50965cfcab24ed5700ea":
        raise RuntimeError("H03 actor catalogue changed")
    citation = catalogue["risk"]["citations"]["public_coverage"]
    risk = {
        "schema_version": 1,
        "eligible": True,
        "source": citation["path"],
        "source_sha256": citation["file_sha256"],
        "quote": citation["quote"],
        "finding": ("The visible check perturbs only initial framing. A repair can pass it "
                    "while critique re-entry still changes frozen criteria or commits a rejected batch."),
        "next_check": ("Run the separately frozen critique re-entry check on accepted public bytes; "
                       "require a completed run and unchanged committed criteria."),
    }
    digest = controller_evaluation.digest(risk)
    files = {name: (FIXTURE / "actor" / name).read_bytes() for name in catalogue["actor_files"]}
    review.qualify_risk(files, risk, digest)
    probes = {}
    for host, name in (("windows", "2026-09-30-controller-x5-h03-risk-probe.json"),
                       ("wsl", "2026-09-30-controller-x5-h03-wsl-risk-probe.json")):
        path = RESULTS / name
        row = json.loads(path.read_text(encoding="utf-8"))
        if (row["actor_files"] != catalogue["actor_file_count"]
                or row["actor_bytes"] != catalogue["actor_bytes"]
                or [row[variant]["risk"]["passed"] for variant in
                    ("baseline", "partial", "alternative", "reference")] != [False, False, True, True]
                or row["provider_calls"] != 0):
            raise RuntimeError(f"{host} public risk calibration differs")
        probes[host] = {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path),
                        "python": row["python"]}
    body = {"schema_version": 1, "case_id": "H03", "provider_calls": 0,
            "source_catalogue_sha256": catalogue["catalogue_sha256"],
            "risk": risk, "risk_digest": digest,
            "risk_check": "test/fixtures/controller_x5_h03/risk_check.py",
            "risk_check_sha256": sha(FIXTURE / "risk_check.py"),
            "probes": probes,
            "stop_if_public_risk_passes": True,
            "eligible_failure": {"public_check": "pass", "risk_check": "fail",
                                 "receipt": "terminal identity-valid writer-stopped settled"}}
    body["risk_manifest_sha256"] = controller_evaluation.digest(body)
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    body = expected()
    if args.check:
        if json.loads(MANIFEST.read_text(encoding="utf-8")) != body:
            raise RuntimeError("H03 public risk manifest differs")
        print(json.dumps({"status": "valid", "sha256": body["risk_manifest_sha256"]}, sort_keys=True))
        return
    with MANIFEST.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(body, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({"status": "frozen", "sha256": body["risk_manifest_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
