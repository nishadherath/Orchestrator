#!/usr/bin/env python3
"""Freeze public-check coverage before any Q4U provider outcome."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from worker_q4u_coverage import assess
from worker_q4u_public import ROOT, TASK_IDS as D01_IDS, check as check_d01
from worker_q4u_boltons import IDS as B02_IDS, check as check_b02
from worker_q4u_controls import IDS as CONTROL_IDS, check as check_control
from worker_q4u_missing import IDS as MISSING_IDS, check as check_missing
from worker_q4u_f07 import IDS as F07_IDS, check as check_f07
from worker_q4u_h08 import IDS as H08_IDS, check as check_h08
from worker_q4u_reserve import SPECS as RESERVE_IDS, check as check_reserve


TASK_IDS = (D01_IDS.keys() | B02_IDS.keys() | CONTROL_IDS.keys() |
            MISSING_IDS.keys() | F07_IDS.keys() | H08_IDS.keys() |
            RESERVE_IDS.keys())


class PublicAssessmentError(ValueError):
    """The public-only coverage inventory is incomplete or has drifted."""


def citation(path: str, content: str, fragment: str) -> dict:
    matches = [(index, line) for index, line in enumerate(content.splitlines(), 1)
               if fragment in line]
    if len(matches) != 1:
        raise PublicAssessmentError(f"citation is absent or ambiguous: {path}: {fragment}")
    line, text = matches[0]
    return {"path": path, "line": line, "text": text,
            "file_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}


def d01_criteria(issue: str, public: str, direct: bool) -> list[dict]:
    return [
        {"id": "round_trip_consecutive_backslashes",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue, "values with consecutive backslashes"),
         "check_citations": [citation(
             "public_check.py", public,
             'value = "prefix" + slash * 2 + "suffix"' if direct else
             'for value in ("plain", "C:" + chr(92) + "Users")')],
         "gap": "Only plain and single-backslash values are checked" if not direct else ""},
        {"id": "quoted_parser_boundary",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "next binding remains separate"),
         "check_citations": ([citation("public_check.py", public,
                                       "for quote in ("),
                              citation("public_check.py", public,
                                       'raw = "key=" + quote')]
                             if direct else [citation("public_check.py", public,
                                                     "rows = list(parse_stream")]),
         "gap": "Only a quoted value without a terminal backslash is checked"
                if not direct else ""},
    ]


def b02_criteria(issue: str, public: str, direct: bool) -> list[dict]:
    return [
        {"id": "eof_terminates",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "relative seek lands in the final"),
         "check_citations": ([citation("public_check.py", public,
                                       "rel_seek=0.95"),
                              citation("public_check.py", public,
                                       "relative seek did not terminate")]
                             if direct else [citation(
                                 "public_check.py", public,
                                 "list(JSONLIterator(StringIO(text)))")]),
         "gap": "Only complete ordinary lines are checked" if not direct else ""},
        {"id": "negative_seek_tail",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "negative `rel_seek` must"),
         "check_citations": ([citation("public_check.py", public,
                                       "rel_seek=-0.25"),
                              citation("public_check.py", public,
                                       "assert tail and tail == positive")]
                             if direct else [citation(
                                 "public_check.py", public, "rel_seek=0.5")]),
         "gap": "Only positive relative seeking is checked" if not direct else ""},
    ]


def control_criteria(task_id: str, issue: str, public: str) -> list[dict]:
    if task_id == "C03":
        return [
            {"id": "stable_remainder_tie", "coverage": "direct",
             "issue_citation": citation("ISSUE.md", issue,
                                        "breaking ties"),
             "check_citations": [citation("public_check.py", public,
                                          "allocate(2, [1, 1, 1])")], "gap": ""},
            {"id": "invalid_input", "coverage": "partial",
             "issue_citation": citation("ISSUE.md", issue,
                                        "Raise `ValueError`"),
             "check_citations": [citation("public_check.py", public,
                                          "allocate(0, [1, 2])")],
             "gap": "The zero-total valid input is checked, but invalid inputs are not"},
        ]
    if task_id == "C04":
        return [
        {"id": "unicode_equivalence", "coverage": "direct",
         "issue_citation": citation("ISSUE.md", issue, "apply Unicode NFKC"),
         "check_citations": [citation("public_check.py", public,
                                      'normalise_label("Straße")'),
                             citation("public_check.py", public,
                                      'normalise_label("ＡＢＣ")')], "gap": ""},
        {"id": "non_string_type", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue, "reject non-strings"),
         "check_citations": [citation("public_check.py", public,
                                      'normalise_label("  HELLO')],
         "gap": "The public check passes only strings"},
        ]
    return [
        {"id": "touching_interval", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "overlapping or touching intervals"),
         "check_citations": [citation("public_check.py", public,
                                      "coalesce(source)")],
         "gap": "The public check covers overlap, not touching intervals"},
        {"id": "contained_interval", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "must not shorten its container"),
         "check_citations": [citation("public_check.py", public,
                                      "coalesce(source)")],
         "gap": "The public check has no contained interval"},
    ]


def missing_criteria(task_id: str, issue: str, public: str) -> list[dict]:
    if task_id == "M05":
        return [
            {"id": "jurisdiction_required", "coverage": "partial",
             "issue_citation": citation("ISSUE.md", issue,
                                        "both tier and jurisdiction"),
             "check_citations": [citation("public_check.py", public,
                                          'value["missing_fields"], list')],
             "gap": "The public check validates a list, not the needed jurisdiction"},
        ]
    if task_id == "M06":
        return [
        {"id": "source_timezone_required", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "IANA timezone identifier"),
         "check_citations": [citation("public_check.py", public,
                                      'value["missing_fields"], list')],
         "gap": "The public check does not identify the absent source timezone"},
        {"id": "dst_policy_required", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "how to handle nonexistent"),
         "check_citations": [citation("public_check.py", public,
                                      'value["status"] in')],
         "gap": "The public check permits a ready claim without a DST policy"},
        ]
    return [
        {"id": "exchange_quote_required", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "no exchange-rate quote"),
         "check_citations": [citation("public_check.py", public,
                                      'value["missing_fields"], list')],
         "gap": "The public check does not require an exchange-rate quote"},
        {"id": "quote_timestamp_required", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "timestamp at which a quote"),
         "check_citations": [citation("public_check.py", public,
                                      'value["status"] in')],
         "gap": "The public check permits ready without a quote timestamp"},
    ]


def f07_criteria(issue: str, public: str, direct: bool) -> list[dict]:
    return [
        {"id": "reserved_character_round_trip",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "inside a component must be encoded"),
         "check_citations": [citation("public_check.py", public,
                                      'decode(r"a\\|b|c\\\\d")' if direct else
                                      'decode("tenant|event|42")')],
         "gap": "Only ordinary unescaped components are checked" if not direct else ""},
        {"id": "trailing_escape_rejected",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "unpaired escape is invalid"),
         "check_citations": [citation("public_check.py", public,
                                      'raise AssertionError("trailing escape' if direct else
                                      'encode(["tenant", "event", "42"])')],
         "gap": "No malformed escape is checked" if not direct else ""},
    ]


def h08_criteria(issue: str, public: str, direct: bool) -> list[dict]:
    return [
        {"id": "stale_revision_ignored",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "not strictly newer"),
         "check_citations": [citation("public_check.py", public,
                                      'assert apply_events({"a": (5, "latest")},'
                                      if direct else 'assert apply_events(original')],
         "gap": "Only a newer put is checked" if not direct else ""},
        {"id": "tombstone_blocks_resurrection",
         "coverage": "direct" if direct else "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "retain its revision as a tombstone"),
         "check_citations": [citation("public_check.py", public,
                                      '== {"a": (5, None)}' if direct else
                                      'assert original ==')],
         "gap": "No delete or stale resurrection is checked" if not direct else ""},
    ]


def reserve_criteria(task_id: str, issue: str, public: str) -> list[dict]:
    if task_id == "R09":
        return [
            {"id": "cross_chunk_frame", "coverage": "partial",
             "issue_citation": citation("ISSUE.md", issue,
                                        "content across chunk boundaries"),
             "check_citations": [citation("public_check.py", public,
                                          'frames([b"first')],
             "gap": "Only a single complete chunk is checked"},
            {"id": "final_delimiter", "coverage": "partial",
             "issue_citation": citation("ISSUE.md", issue,
                                        "must not invent an"),
             "check_citations": [citation("public_check.py", public,
                                          'frames([b"first')],
             "gap": "The public check has no final delimiter"},
        ]
    return [
        {"id": "half_up_rounding", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "rounded half up"),
         "check_citations": [citation("public_check.py", public,
                                      "tax_cents(100, 1000)")],
         "gap": "The public check has no half-cent boundary"},
        {"id": "subtotal_once", "coverage": "partial",
         "issue_citation": citation("ISSUE.md", issue,
                                    "calculated once on the"),
         "check_citations": [citation("public_check.py", public,
                                      "invoice_total([100], 1000)")],
         "gap": "The public check has only one line"},
    ]


def build(task_id: str) -> dict:
    if task_id not in TASK_IDS:
        raise PublicAssessmentError(f"unknown public task: {task_id}")
    task_path = ROOT / "test/fixtures/worker_q4u_public" / task_id / "task.json"
    binding = (check_d01(task_path) if task_id in D01_IDS else
               check_b02(task_id) if task_id in B02_IDS else
               check_control(task_id) if task_id in CONTROL_IDS else
               check_missing(task_id) if task_id in MISSING_IDS else
               check_f07(task_id) if task_id in F07_IDS else
               check_h08(task_id) if task_id in H08_IDS else
               check_reserve(task_id))
    actor = task_path.parent / "actor"
    issue = (actor / "ISSUE.md").read_text(encoding="utf-8")
    public = (actor / "public_check.py").read_text(encoding="utf-8")
    direct = task_id.endswith("S")
    criteria = (d01_criteria(issue, public, direct) if task_id in D01_IDS else
                b02_criteria(issue, public, direct) if task_id in B02_IDS else
                control_criteria(task_id, issue, public) if task_id in CONTROL_IDS else
                missing_criteria(task_id, issue, public) if task_id in MISSING_IDS else
                f07_criteria(issue, public, direct) if task_id in F07_IDS else
                h08_criteria(issue, public, direct) if task_id in H08_IDS else
                reserve_criteria(task_id, issue, public))
    control = task_id in CONTROL_IDS or task_id in MISSING_IDS
    cross_component = (task_id in D01_IDS or task_id in F07_IDS
                       or task_id == "R10")
    facts = {"task_kind": "investigation" if control else "implementation",
             "cross_component": cross_component, "change_required": not control,
             "criteria": criteria}
    result = assess(facts, issue_files={"ISSUE.md": issue},
                    check_files={"public_check.py": public})
    expected = "partial" if control or not direct else "direct"
    if result["verification_coverage"] != expected:
        raise PublicAssessmentError(f"{task_id} public coverage label differs")
    return {"schema_version": 1, "task_id": task_id,
            "task_sha256": binding["task_sha256"], "assessment": result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        for task_id in sorted(TASK_IDS):
            value = build(task_id)
            output = ROOT / "test/fixtures/worker_q4u_public" / task_id / "public_assessment.json"
            if args.prepare:
                if output.exists():
                    if json.loads(output.read_text(encoding="utf-8")) != value:
                        raise PublicAssessmentError(f"refusing to overwrite: {output}")
                else:
                    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8", newline="\n")
            elif json.loads(output.read_text(encoding="utf-8")) != value:
                raise PublicAssessmentError(f"frozen public assessment differs: {task_id}")
            print(f"PASS: {task_id} {value['assessment']['verification_coverage']} "
                  f"{value['assessment']['assessment_sha256']}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"BLOCKED: Q4U public assessment: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
