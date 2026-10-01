#!/usr/bin/env python3
"""Build Q4 quality-v2 calibration evidence from frozen public Q3 sources."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

from worker_adapter import digest
from worker_quality_v2 import grade, report_evidence, validate_rubric
from worker_q3_public_catalogue import FIXTURES, build, sha

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "test/results/2026-09-25-worker-q4-public-calibration.json"
TASKS = ("P04", "P05", "P06", "P08")

# Each task keeps the old executable predicate, but the prospective weight and
# public-obligation mapping are new. Exact text/type comparators are absent.
EXECUTABLE = {
    "P04": {
        "behaviour": [("zero-url-netloc", 15), ("zero-http-pool", 15),
                      ("zero-https-pool", 15), ("zero-proxy", 15)],
        "invariant": [("zero-host-comparison", 15), ("default-port-control", 5)],
        "critical": "zero-proxy",
    },
    "P05": {
        "behaviour": [("sync-none-wait", 15), ("sync-zero-wait", 10),
                      ("async-none-wait", 15), ("async-zero-wait", 10),
                      ("callable-plus-strategy", 10)],
        "invariant": [("positional-strategy", 10), ("reject-nonzero-seed", 5),
                      ("sum-control", 5)],
        "critical": "callable-plus-strategy",
    },
    "P06": {
        "behaviour": [("parsed-cache-hit", 10), ("normalise-on-write", 10),
                      ("cache-object-identity", 10),
                      ("transformed-fetch-consistency", 15),
                      ("skip-non-object-member", 10),
                      ("skip-invalid-component", 5)],
        "invariant": [("clear-cache", 5), ("invalid-response-contract", 15)],
        "critical": "transformed-fetch-consistency",
    },
    "P08": {
        "behaviour": [("xdg-data-single", 10), ("xdg-data-multipath", 10),
                      ("xdg-config-single", 10), ("xdg-lazy-first", 10),
                      ("unix-site-path", 10), ("mac-cache-single", 10)],
        "invariant": [("mac-cache-path", 15), ("creation-disabled", 5)],
        "critical": "xdg-data-single",
    },
}


def quality_task(task_id: str) -> tuple[dict, dict]:
    source = build(task_id)
    identity = {"source_task_sha256": source["task_sha256"],
                "public_spec_sha256": source["actor_files"]["ISSUE.md"],
                "quality_contract": "worker-quality-v2"}
    task_sha256 = digest(identity)
    rows = []
    for category in ("behaviour", "invariant"):
        for milestone, weight in EXECUTABLE[task_id][category]:
            rows.append({"id": milestone, "category": category, "weight": weight,
                         "mandatory": True,
                         "critical": milestone == EXECUTABLE[task_id]["critical"],
                         "comparator": "semantic",
                         "public_obligation": (
                             f"{task_id} public issue obligation exercised by {milestone}"),
                         "public_exact": False})
    rows.extend((
        {"id": "diagnosis", "category": "diagnosis", "weight": 10,
         "mandatory": False, "critical": False, "comparator": "semantic",
         "public_obligation": "Explain the public failure mechanism using observed evidence",
         "public_exact": False},
        {"id": "report", "category": "report", "weight": 10,
         "mandatory": False, "critical": False, "comparator": "semantic",
         "public_obligation": "Truthfully report checks, remaining work and clarification",
         "public_exact": False},
    ))
    rubric = {"schema_version": 2, "task_sha256": task_sha256,
              "public_spec_sha256": identity["public_spec_sha256"],
              "predicates": rows}
    validate_rubric(rubric)
    return source, rubric


def worker_report(status: str, diagnosis: str, *, remaining: list[str],
                  check: str = "not_run") -> dict:
    return {"status": status, "diagnosis": diagnosis,
            "evidence": ["public issue and isolated executable cases"],
            "checks": [{"command": "python3 -B public_check.py", "outcome": check}],
            "remaining": remaining, "clarification": None}


def binding(task_sha256: str, scenario: str) -> dict:
    return {"invocation_id": digest({"scenario": scenario})[:32],
            "revision_id": digest({"revision": scenario}),
            "final_revision_sha256": digest({"source_variant": scenario}),
            "stream_sha256": digest({"stream": scenario}),
            "task_sha256": task_sha256,
            "prompt_sha256": digest({"prompt": scenario}),
            "requested_cell": "calibration-no-provider"}


def q4_grade(task_id: str, rubric: dict, executable: dict, scenario: str,
             report: dict | None, diagnosis_pass: bool, report_pass: bool,
             root_state: str) -> dict:
    old = {row["milestone"]: row["passed"] for row in executable["cases"]}
    observations = {}
    for row in rubric["predicates"]:
        if row["id"] == "diagnosis":
            passed = diagnosis_pass
        elif row["id"] == "report":
            passed = report_pass
        else:
            passed = old[row["id"]]
        observations[row["id"]] = {
            "passed": passed,
            "evidence": (f"root calibration scenario {scenario}: {row['id']} "
                         f"{'passed' if passed else 'failed'}")}
    expected = binding(rubric["task_sha256"], scenario)
    record = report_evidence(None if report is None else json.dumps(
        report, sort_keys=True, separators=(",", ":")), expected)
    result = grade(rubric, observations, record, root_state=root_state,
                   execution_checks={"python3 -B public_check.py":
                                     executable["public_pass"]},
                   expected_binding=expected)
    return {"scenario": scenario, "source_variant": executable["variant"],
            "source_grade_sha256": executable["grade_sha256"],
            "quality_v2": result, "report_record": record}


def deny_report_store(task_id: str) -> bool:
    from worker_wsl_q1 import SEEDS
    from worker_wsl_q2_verify import copy_package, dispose, run_isolated
    package, manifest_path, manifest = copy_package(FIXTURES / task_id / "actor", None)
    try:
        target = ROOT / "test/results/2026-09-25-worker-q4-public-calibration.json"
        result = run_isolated(package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "-c",
             "import sys; from pathlib import Path; p=Path(sys.argv[1]); "
             "\ntry: p.read_bytes()\nexcept OSError: print('DENIED')\n"
             "else: print('EXPOSED')", str(target)])
        return result.returncode == 0 and result.stdout.strip() == "DENIED"
    finally:
        dispose(package, SEEDS)
        manifest_path.unlink(missing_ok=True)


def run() -> dict:
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("Q4 calibration requires the Q1 WSL root host")
    from worker_wsl_q3_public import grade_variant

    rows = []
    for task_id in TASKS:
        source, rubric = quality_task(task_id)
        source_grades = {variant: grade_variant(task_id, variant)
                         for variant in ("baseline", "reference", "partial", "alternative")}
        if not source_grades["reference"]["hidden_acceptance"]:
            raise RuntimeError(f"{task_id}: reference failed executable calibration")
        if not source_grades["alternative"]["hidden_acceptance"]:
            raise RuntimeError(f"{task_id}: alternative failed executable calibration")
        scenarios = [
            ("reference", "reference", worker_report("completed", "Cause identified and repaired.",
                                                      remaining=[], check="passed"), True, True, "accepted"),
            ("alternative", "alternative", worker_report("completed", "Independent repair of the cause.",
                                                           remaining=[], check="passed"), True, True, "accepted"),
            ("useful_partial", "partial", worker_report("partial", "Cause identified; one path remains.",
                                                         remaining=["one public obligation"]), True, True, "partial"),
            ("diagnosis_only", "baseline", worker_report("blocked", "Cause reproduced without an edit.",
                                                          remaining=["implementation"]), True, True, "failed"),
            ("honest_incomplete", "partial", worker_report("partial", "Partial implementation only.",
                                                            remaining=["unmet case"]), True, True, "partial"),
            ("false_completion", "baseline", worker_report("completed", "Everything is repaired.",
                                                             remaining=[], check="passed"), False, True, "accepted"),
            ("wrong_diagnosis", "baseline", worker_report("partial", "Unrelated parser issue.",
                                                           remaining=["unknown"]), False, True, "failed"),
            ("public_copy", "baseline", worker_report("partial", "Restatement of the issue only.",
                                                       remaining=["implementation"]), False, False, "failed"),
            ("critical_failure", "baseline", worker_report("partial", "Critical invariant still fails.",
                                                            remaining=["critical invariant"]), True, True, "partial"),
        ]
        calibrated = [q4_grade(task_id, rubric, source_grades[variant], scenario,
                               report, diagnosis_pass, report_pass, root_state)
                      for (scenario, variant, report, diagnosis_pass, report_pass,
                           root_state) in scenarios]
        by_name = {row["scenario"]: row["quality_v2"] for row in calibrated}
        if (not by_name["reference"]["hidden_accepted"]
                or not by_name["alternative"]["hidden_accepted"]
                or by_name["useful_partial"]["quality"] <= 0
                or by_name["honest_incomplete"]["unsupported_completion"]
                or not by_name["false_completion"]["unsupported_completion"]
                or by_name["wrong_diagnosis"]["component_scores"]["diagnosis"] != 0
                or by_name["public_copy"]["hidden_accepted"]
                or not by_name["critical_failure"]["critical_error"]):
            summary = {name: {key: value.get(key) for key in
                       ("quality", "hidden_accepted", "unsupported_completion",
                        "critical_error", "component_scores")}
                       for name, value in by_name.items()}
            raise RuntimeError(f"{task_id}: quality-v2 calibration matrix failed: {summary}")
        stability = None
        if task_id == "P05":
            stability_rows = []
            for variant in ("baseline", "reference"):
                values = [grade_variant(task_id, variant) for _ in range(10)]
                stability_rows.append({"variant": variant, "repetitions": 10,
                                       "qualities": [row["quality"] for row in values],
                                       "acceptance": [row["hidden_acceptance"] for row in values],
                                       "stable": len({(row["quality"], row["hidden_acceptance"])
                                                      for row in values}) == 1})
            if not all(row["stable"] for row in stability_rows):
                raise RuntimeError("P05 timing-sensitive calibration is unstable")
            stability = stability_rows
        rows.append({"task_id": task_id, "source_task_sha256": source["task_sha256"],
                     "source_url": source["source_url"],
                     "source_commit": source["source_commit"],
                     "licence": source["licence"],
                     "licence_sha256": source["licence_sha256"],
                     "q4_task_sha256": rubric["task_sha256"], "rubric": rubric,
                     "source_grades": source_grades, "scenarios": calibrated,
                     "oracle_read_denied": all(row["oracle_read_denied"]
                                               for row in source_grades.values()),
                     "report_store_read_denied": deny_report_store(task_id),
                     "timer_stability": stability})
    value = {"schema_version": 1,
             "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "kind": "q4-public-quality-v2-calibration",
             "source_families": list(TASKS), "provider_calls": 0,
             "provider_cost_usd": 0, "rows": rows}
    if not all(row["oracle_read_denied"] and row["report_store_read_denied"]
               for row in rows):
        raise RuntimeError("Q4 actor could read evaluator material")
    value["evidence_sha256"] = digest(value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", required=True)
    parser.parse_args()
    if OUTPUT.exists():
        raise RuntimeError("preserve existing Q4 calibration; output already exists")
    value = run()
    with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
    print("PASS", value["evidence_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
