"""Bind human frame F screen decisions to the frozen selected prefix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "test/results"
FRAME = RESULTS / "2026-09-30-controller-x5-opening-frame-f.json"
BODIES = RESULTS / "2026-09-30-controller-x5-opening-frame-f-selected-bodies.json"
SCREEN = RESULTS / "2026-09-30-controller-x5-opening-frame-f-screen.json"
PRIOR = (
    "2026-09-30-controller-x5-opening-frame-e.json",
    "2026-09-30-controller-x5-external-frame-c.json",
    "2026-09-30-controller-x5-external-frame-d.json",
)

# One judgment for every row in the predeclared hash order. No row is replaced.
DECISIONS = (
    ("policy_request", "Raw Version retention and API shape are proposed, not settled."),
    ("diagnosis_disclosed", "Opening text gives parser-layer hypothesis and exact regression; frame E overlap."),
    ("deprecation_request", "Proposes an API deprecation, not a failing repair task."),
    ("diagnosis_disclosed", "Opening report maps kqueue, IOCP and epoll paths and proposes platform-specific repairs and a policy change."),
    ("diagnosis_disclosed", "Opening report identifies the case-sensitive deduplication fault; frame D overlap."),
    ("documentation_request", "Requests examples in documentation."),
    ("diagnosis_disclosed", "Opening report names TextClause parsing and the desired literal-string behaviour; frames C/D overlap."),
    ("policy_request", "Opening report weighs support versus rejection of keyword-only arguments without a settled rule."),
    ("policy_request", "Author says this 411 proposal should be closed; frame E overlap."),
    ("deprecation_request", "Proposes deprecating FileWrapper."),
    ("diagnosis_and_host_gap", "Opening report names the PostgreSQL OID join path; PostgreSQL acceptance is not qualified on this worker host."),
    ("support_question", "Asks how to strip formatting for a downstream menu search."),
    ("diagnosis_and_host_gap", "Opening report gives sync-callback cause and async-def fix; PostgreSQL acceptance is not qualified."),
    ("no_task", "Empty-body junk issue."),
    ("repair_disclosed", "Opening report states exact release-workflow permission and checkout hardening."),
    ("diagnosis_disclosed", "Opening report identifies empty input becoming an empty regex and zero-width matches."),
    ("no_task", "Contributor asks for work rather than reporting a defect."),
    ("diagnosis_disclosed", "Opening report identifies a fresh dynamic comparator class on every property access; frame D overlap."),
    ("repair_disclosed", "Opening report specifies UTC arithmetic and comparison repair; frame E overlap."),
    ("policy_request", "Requests a sequenced mutability/equality/hash migration with unresolved compatibility rules."),
    ("documentation_policy", "Requests changed guidance on MAX_CONTENT_LENGTH rather than a settled code repair."),
    ("host_oracle_gap", "Mobile visual rendering report has no deterministic local acceptance or consequential follow-up contract."),
    ("repair_disclosed", "Opening report gives IPv6 colon-splitting cause and parsing fix; frame E overlap."),
    ("maintainer_rejected_contract", "Fresh-cache Jinja 3.1.6 reproduction fails, but a maintainer closed this StrEnum request as not planned: the API expects strings."),
    ("deprecation_request", "Proposes deprecating WSGI functions."),
    ("diagnosis_and_host_gap", "Opening report names SQL Server date-offset formatting path; SQL Server acceptance host is unavailable."),
    ("no_task", "Empty-body junk issue."),
    ("repair_disclosed", "Opening report traces the connection-pool race and links an existing fix PR."),
    ("no_task", "Spam test issue."),
    ("nondeterministic_ci", "Opening report describes an intermittent Windows timeout and prior timeout/readiness repair; no deterministic entry signal."),
)


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    if SCREEN.exists():
        raise FileExistsError("frame F screen already written")
    frame = read(FRAME)
    bodies = read(BODIES)
    if len(DECISIONS) != len(bodies) or len(bodies) != frame["selected_count"]:
        raise ValueError("screen decisions do not cover the fixed prefix")
    rows = {row["url"]: row for row in frame["rows"]}
    expected = [row["url"] for row in sorted(
        frame["rows"], key=lambda row: sha(frame["hash_seed"] + row["url"]))[:30]]
    if expected != frame["selected_urls"] or expected != [row["url"] for row in bodies]:
        raise ValueError("selected issue order differs from frozen hash order")
    for body in bodies:
        row = rows[body["url"]]
        if (not (sha(body["title"]) == body["title_sha256"] == row["title_sha256"])
                or not (sha(body["body"] or "") == body["body_sha256"]
                        == row["body_sha256"])):
            raise ValueError(f"opening body binding failed: {body['url']}")
    prior = {name: set(read(RESULTS / name)["selected_urls"]) for name in PRIOR}
    decisions = [{
        "position": position, "url": body["url"],
        "decision": "reject_blind_paid", "reason_code": reason,
        "reason": note,
        "prior_frame_overlaps": [name for name, urls in prior.items()
                                 if body["url"] in urls],
    } for position, (body, (reason, note)) in enumerate(zip(bodies, DECISIONS), 1)]
    result = {
        "schema": "controller-x5-opening-event-frame-f-screen-v1",
        "frame_sha256": hashlib.sha256(FRAME.read_bytes()).hexdigest(),
        "bodies_sha256": hashlib.sha256(BODIES.read_bytes()).hexdigest(),
        "screened": len(decisions), "blind_paid_admissions": 0,
        "rows": decisions,
    }
    SCREEN.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps({"screened": len(decisions), "overlap_rows": sum(
        bool(row["prior_frame_overlaps"]) for row in decisions),
        "blind_paid_admissions": 0,
        "screen_sha256": hashlib.sha256(SCREEN.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
