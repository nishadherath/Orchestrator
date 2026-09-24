#!/usr/bin/env python3
"""Generate the 24 original, standard-library N4 worker tasks.

Only actor starter code, issue text and shallow public checks are copied to
the actor. Evaluator-only reference semantics and data oracles stay outside.
This generator is deterministic; `--check` reports drift without writing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import worker_oracles

ROOT = Path(__file__).resolve().parent.parent
DESTINATION = ROOT / "test" / "fixtures" / "worker_n4"


def _task(ident: str, family: str, issue: str, public: dict,
          hidden: list[dict]) -> dict:
    return {"id": ident, "family": family,
            "split": "development" if ident.startswith("D") else "reserved",
            "issue_text": issue, "public": public, "hidden": hidden}


TASKS = [
    _task("D01", "configuration", "Return the first non-null value in CLI, environment, file, default order, with its source. Empty strings are values.",
          {"cli": "blue", "environment": "green", "file": "red", "default": "black"},
          [{"cli": None, "environment": "green", "file": "red", "default": "black"},
           {"cli": "", "environment": "green", "file": "red", "default": "black"},
           {"cli": None, "environment": None, "file": None, "default": "black"}]),
    _task("D02", "configuration", "Validate a service port in 1..65535. Accept a decimal integer or decimal string; reject booleans, other text and out-of-range values without silently choosing a default.",
          {"port": 8080}, [{"port": 0}, {"port": "65535"}, {"port": "abc"}, {"port": True}]),
    _task("R01", "configuration", "Replay read and reload events for a rotating secret. Each read sees the latest completed reload; return all read values and the current secret.",
          {"initial": "a", "events": [{"kind": "read"}]},
          [{"initial": "a", "events": [{"kind": "reload", "secret": "b"}, {"kind": "read"}]},
           {"initial": "x", "events": [{"kind": "read"}, {"kind": "reload", "secret": "y"}, {"kind": "read"}]},
           {"initial": "old", "events": [{"kind": "reload", "secret": "new"}]}]),
    _task("R02", "configuration", "Resolve a POSIX-style relative request under root. Reject absolute paths and any parent component before normalization; return the normalized path or outside-root error.",
          {"root": "/srv/data", "requested": "a/file.txt"},
          [{"root": "/srv/data", "requested": "../secret"},
           {"root": "/srv/data", "requested": "/etc/passwd"},
           {"root": "/srv/data", "requested": "a/./b"}]),
    _task("D03", "resilience", "Model a bounded HTTP call. Retry only status 503 for GET, PUT or DELETE, never POST; stop on another status or max_attempts. Return statuses actually attempted and final status.",
          {"method": "GET", "statuses": [200], "max_attempts": 3},
          [{"method": "GET", "statuses": [503, 503, 200], "max_attempts": 3},
           {"method": "POST", "statuses": [503, 200], "max_attempts": 3},
           {"method": "GET", "statuses": [503, 200], "max_attempts": 1}]),
    _task("D04", "resilience", "Apply one end-to-end millisecond budget across sequential hops. A hop completes only if its cumulative finish is within the budget. Return completed count, elapsed completed time and timeout flag.",
          {"budget_ms": 100, "hops_ms": [10]},
          [{"budget_ms": 100, "hops_ms": [60, 60]},
           {"budget_ms": 100, "hops_ms": [40, 60]},
           {"budget_ms": 5, "hops_ms": [10]}]),
    _task("R03", "resilience", "Implement a deterministic circuit breaker. Consecutive failures open it at threshold; open calls are denied. Each tick advances reset time; after reset_ticks, admit one half-open probe. A successful probe closes it; a failed probe reopens it.",
          {"threshold": 2, "reset_ticks": 2, "events": ["ok"]},
          [{"threshold": 2, "reset_ticks": 2, "events": ["fail", "fail", "ok"]},
           {"threshold": 2, "reset_ticks": 2, "events": ["fail", "fail", "tick", "tick", "ok"]},
           {"threshold": 1, "reset_ticks": 1, "events": ["fail", "tick", "fail", "ok"]}]),
    _task("R04", "resilience", "Track a bounded permit pool. Acquire fills active slots then FIFO waiters. Release or cancel removes that ID and promotes waiting work; cancelled IDs are reported.",
          {"capacity": 1, "events": [{"kind": "acquire", "id": "a"}]},
          [{"capacity": 1, "events": [{"kind": "acquire", "id": "a"}, {"kind": "acquire", "id": "b"}, {"kind": "release", "id": "a"}]},
           {"capacity": 1, "events": [{"kind": "acquire", "id": "a"}, {"kind": "acquire", "id": "b"}, {"kind": "cancel", "id": "b"}]},
           {"capacity": 2, "events": [{"kind": "acquire", "id": "a"}, {"kind": "acquire", "id": "b"}, {"kind": "acquire", "id": "c"}, {"kind": "cancel", "id": "a"}]}]),
    _task("D05", "integrity", "Import a batch atomically. Duplicate IDs or negative amounts reject the entire batch; otherwise return committed IDs in input order and null error.",
          {"rows": [{"id": "a", "amount": 1}]},
          [{"rows": [{"id": "a", "amount": 1}, {"id": "a", "amount": 2}]},
           {"rows": [{"id": "a", "amount": -1}, {"id": "b", "amount": 2}]},
           {"rows": [{"id": "b", "amount": 0}, {"id": "a", "amount": 2}]}]),
    _task("D06", "integrity", "Plan a resumable ordered migration. Return required steps not already applied, preserving required order, and whether migration is already complete.",
          {"required": ["v1"], "applied": []},
          [{"required": ["v1", "v2", "v3"], "applied": ["v1"]},
           {"required": ["v1", "v2"], "applied": ["v1", "v2"]},
           {"required": ["a", "b", "c"], "applied": ["b"]}]),
    _task("R05", "integrity", "Recover a JSONL stream after a numeric checkpoint. Ignore old records and duplicate sequence numbers, emit remaining values in sequence order, and advance the checkpoint only to the highest emitted sequence.",
          {"checkpoint": 0, "records": [{"seq": 1, "value": "a"}]},
          [{"checkpoint": 2, "records": [{"seq": 1, "value": "a"}, {"seq": 3, "value": "c"}]},
           {"checkpoint": 0, "records": [{"seq": 3, "value": "c"}, {"seq": 1, "value": "a"}, {"seq": 3, "value": "wrong"}]},
           {"checkpoint": 5, "records": [{"seq": 4, "value": "old"}]}]),
    _task("R06", "integrity", "Sum decimal ledger entries exactly, round half-even to cents once at the end, and reject a negative final balance as overdraft. Return a two-decimal string.",
          {"start": "1.00", "entries": ["0.50"]},
          [{"start": "0.00", "entries": ["0.005"]},
           {"start": "1.00", "entries": ["-2.00"]},
           {"start": "0.10", "entries": ["0.20", "0.30"]}]),
    _task("D07", "concurrency", "Replay cache put/get operations. Keys are scoped by both tenant and key; a miss returns null. Return get results in order.",
          {"operations": [{"kind": "put", "tenant": "a", "key": "k", "value": 1}, {"kind": "get", "tenant": "a", "key": "k"}]},
          [{"operations": [{"kind": "put", "tenant": "a", "key": "k", "value": 1}, {"kind": "get", "tenant": "b", "key": "k"}]},
           {"operations": [{"kind": "put", "tenant": "a", "key": "k", "value": 1}, {"kind": "put", "tenant": "b", "key": "k", "value": 2}, {"kind": "get", "tenant": "a", "key": "k"}, {"kind": "get", "tenant": "b", "key": "k"}]},
           {"operations": [{"kind": "get", "tenant": "x", "key": "none"}]}]),
    _task("D08", "concurrency", "Coalesce concurrent requests by key within one batch. Execute the first outcome for each distinct key once; fan that outcome, including errors, to all duplicate requesters in original order.",
          {"requests": [{"key": "a", "outcome": "ok"}]},
          [{"requests": [{"key": "a", "outcome": "error"}, {"key": "a", "outcome": "ok"}]},
           {"requests": [{"key": "a", "outcome": "ok"}, {"key": "b", "outcome": "error"}, {"key": "a", "outcome": "error"}]},
           {"requests": []}]),
    _task("R07", "concurrency", "Apply asynchronously completed cache refreshes. For each key, retain the highest version even if an older refresh finishes later; return version and value per key.",
          {"completions": [{"key": "a", "version": 1, "value": "new"}]},
          [{"completions": [{"key": "a", "version": 2, "value": "new"}, {"key": "a", "version": 1, "value": "stale"}]},
           {"completions": [{"key": "a", "version": 1, "value": "a"}, {"key": "b", "version": 3, "value": "b"}]},
           {"completions": []}]),
    _task("R08", "concurrency", "Simulate FIFO tasks on capacity fixed workers. A task starts on the earliest-free worker; shutdown rejects work that would start at or after shutdown_at. Report accepted work finished by drain_deadline and rejected IDs.",
          {"capacity": 1, "shutdown_at": 10, "drain_deadline": 10, "tasks": [{"id": "a", "duration": 2}]},
          [{"capacity": 1, "shutdown_at": 3, "drain_deadline": 5, "tasks": [{"id": "a", "duration": 3}, {"id": "b", "duration": 2}]},
           {"capacity": 2, "shutdown_at": 2, "drain_deadline": 5, "tasks": [{"id": "a", "duration": 4}, {"id": "b", "duration": 1}, {"id": "c", "duration": 2}]},
           {"capacity": 1, "shutdown_at": 1, "drain_deadline": 2, "tasks": [{"id": "a", "duration": 5}, {"id": "b", "duration": 1}]}]),
    _task("D09", "protocol", "Return status 304 with no body when If-None-Match exactly matches the resource ETag; otherwise return status 200 with body. Preserve the ETag in both responses.",
          {"etag": "v1", "if_none_match": None, "body": "hello"},
          [{"etag": "v1", "if_none_match": "v1", "body": "hello"},
           {"etag": "v2", "if_none_match": "v1", "body": "new"},
           {"etag": "abc", "if_none_match": "ABC", "body": "case"}]),
    _task("D10", "protocol", "Validate the supplied lowercase hexadecimal HMAC-SHA256 signature over the exact UTF-8 body bytes with the provided key. Return only a boolean valid field; never normalize the body.",
          {"key": "k", "body": "hello", "signature": "406e4b43f87095aa86ca6299d25e875921fefa180f02043bb29bec5681c0c2d0"},
          [{"key": "k", "body": "hello ", "signature": "406e4b43f87095aa86ca6299d25e875921fefa180f02043bb29bec5681c0c2d0"},
           {"key": "k", "body": "hello", "signature": "0" * 64},
           {"key": "secret", "body": "x", "signature": "117eca332f7e13ccb8e4574e4f33daa212a9231353670c2b8b4797df0bb77afa"}]),
    _task("R09", "protocol", "Page records in ascending stable ID order. Return IDs strictly after an optional cursor up to limit; emit a next_cursor only when more records remain.",
          {"records": [{"id": "a"}, {"id": "b"}], "cursor": None, "limit": 1},
          [{"records": [{"id": "c"}, {"id": "a"}, {"id": "b"}], "cursor": "a", "limit": 1},
           {"records": [{"id": "b"}, {"id": "a"}], "cursor": None, "limit": 2},
           {"records": [{"id": "a"}], "cursor": "z", "limit": 2}]),
    _task("R10", "protocol", "Decode two-byte big-endian length-prefixed UTF-8 frames from hex chunks. Emit complete frames, preserve an incomplete suffix as lowercase hex, and reject malformed UTF-8 with invalid-utf8 error.",
          {"chunks_hex": ["000161"]},
          [{"chunks_hex": ["0001", "61", "000162"]},
           {"chunks_hex": ["0003", "6162"]},
           {"chunks_hex": ["0000", "0001ff"]}]),
    _task("D11", "diagnosis", "Measure total stage cost as count times milliseconds each. Name the largest total as bottleneck and state whether it contradicts the named hotspot; do not optimise the named hotspot by assumption.",
          {"named_hotspot": "parse", "measurements": [{"stage": "parse", "count": 10, "ms_each": 2}, {"stage": "write", "count": 1, "ms_each": 5}]},
          [{"named_hotspot": "parse", "measurements": [{"stage": "parse", "count": 1, "ms_each": 20}, {"stage": "write", "count": 100, "ms_each": 2}]},
           {"named_hotspot": "network", "measurements": [{"stage": "network", "count": 2, "ms_each": 5}, {"stage": "db", "count": 4, "ms_each": 3}]},
           {"named_hotspot": "db", "measurements": [{"stage": "db", "count": 3, "ms_each": 4}, {"stage": "parse", "count": 2, "ms_each": 2}]}]),
    _task("D12", "diagnosis", "A missing retention_days is an operator decision: request clarification and delete nothing. When supplied, return IDs whose age_days is strictly greater than the limit.",
          {"retention_days": None, "records": [{"id": "a", "age_days": 99}]},
          [{"retention_days": 30, "records": [{"id": "a", "age_days": 31}, {"id": "b", "age_days": 30}]},
           {"retention_days": 0, "records": [{"id": "a", "age_days": 0}, {"id": "b", "age_days": 1}]},
           {"retention_days": None, "records": []}]),
    _task("R11", "diagnosis", "Compare observed and expected upstream configuration before editing code. On a mismatch, report no-code-change, upstream-config and the observed value; otherwise mark code investigation as unresolved.",
          {"actual_upstream": "east", "expected_upstream": "west"},
          [{"actual_upstream": "west", "expected_upstream": "west"},
           {"actual_upstream": "disabled", "expected_upstream": "enabled"},
           {"actual_upstream": "a", "expected_upstream": "b"}]),
    _task("R12", "diagnosis", "Complete verifiable local checks first. If external_key is absent, report a safe partial with local pass count and external_key blocker. With a key, complete only when all local checks pass.",
          {"external_key": None, "local_checks": [True, False, True]},
          [{"external_key": "key", "local_checks": [True, True]},
           {"external_key": "key", "local_checks": [True, False]},
           {"external_key": None, "local_checks": []}]),
]


def planned_files() -> dict[str, str]:
    out = {}
    catalogue = {"schema_version": 1, "tasks": []}
    starter = ("import json, sys\n\n"
               "def solve(data):\n    return None\n\n"
               "if __name__ == '__main__':\n"
               "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n")
    for task in TASKS:
        ident = task["id"]
        public = task["public"]
        public_expected = worker_oracles.expected(ident, public)
        prefix = f"{task['split']}/{ident}"
        actor_source = starter
        if ident == "R11":
            actor_source = (
                "import json, sys\n\n"
                "def solve(data):\n"
                "    actual = data['actual_upstream']\n"
                "    if actual != data['expected_upstream']:\n"
                "        return {'action': 'no-code-change', 'cause': 'upstream-config', 'observed': actual}\n"
                "    return {'action': 'investigate-code', 'cause': 'undetermined', 'observed': actual}\n\n"
                "if __name__ == '__main__':\n"
                "    print(json.dumps(solve(json.loads(sys.stdin.readline()))))\n")
        out[f"{prefix}/actor/app.py"] = actor_source
        out[f"{prefix}/actor/public_check.py"] = (
            "from app import solve\n"
            f"assert solve({public!r}) == {public_expected!r}\n")
        lead = ("Investigate this incident; preserve `app.py` when the code is correct. "
                if ident == "R11" else
                "Implement `solve(data)` in `app.py` for this service behaviour. ")
        out[f"{prefix}/issue.md"] = lead + task["issue_text"] + " Keep the JSON-line CLI working.\n"
        out[f"{prefix}/acceptance.json"] = json.dumps({
            "version": 1, "kind": "command", "criteria": ["public check passes"],
            "constraints": ["Do not edit the public check or task definition"],
            "required_outputs": ["app.py"],
            "protected_paths": ["public_check.py", "ISSUE.md", "acceptance.json"],
            "command": ["python3", "public_check.py"], "timeout_s": 10},
            indent=2) + "\n"
        oracle = {"schema_version": 1,
                  "cases": [{"input": item, "expected": worker_oracles.expected(ident, item),
                             "weight": 1, "milestone": f"case-{n}",
                             "critical": n == 1 and task["split"] == "reserved"}
                            for n, item in enumerate(task["hidden"], 1)]}
        if ident == "R11":
            oracle["no_edit_baseline_sha256"] = hashlib.sha256(
                actor_source.encode("utf-8")).hexdigest()
        out[f"oracles/{ident}.json"] = json.dumps(oracle, indent=2, sort_keys=True) + "\n"
        assessment = {"task_kind": ("investigation" if task["family"] == "diagnosis"
                                    else "implementation"),
                      "complexity": "moderate", "verification": "executable",
                      "context_tokens": 5000, "deadline_seconds": None,
                      "failure_cause": "none", "prior_local_repairs": 0,
                      "frame_confidence": "clear", "required_artefacts": ["app.py"],
                      "evidence": [{"source": "operator", "reference": "issue.md",
                                    "claim": "implement stated behaviour"}]}
        catalogue["tasks"].append({"id": ident, "family": task["family"],
                                    "split": task["split"], "actor": f"{prefix}/actor",
                                    "issue": f"{prefix}/issue.md",
                                    "acceptance": f"{prefix}/acceptance.json",
                                    "oracle": f"oracles/{ident}.json",
                                    "allowed_edits": ["app.py"], "assessment": assessment})
    out["catalogue.json"] = json.dumps(catalogue, indent=2, sort_keys=True) + "\n"
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    planned = planned_files()
    drift = []
    for name, content in planned.items():
        path = DESTINATION / name
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                drift.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    if drift:
        print(f"N4 corpus drift: {len(drift)} files; first: {drift[:5]}")
        return 1
    print(f"N4 corpus {'checked' if args.check else 'wrote'}: {len(TASKS)} tasks, {len(planned)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
