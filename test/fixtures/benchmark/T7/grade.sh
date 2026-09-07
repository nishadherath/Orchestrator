#!/usr/bin/env bash
# Grader for T7 (open, long horizon). benchmark.py invokes this with cwd
# already set to the task's working copy inside the consumer project, after
# writing BENCHMARK_REPORT.txt there with the worker's relayed final report.
#
# Same shape as T5's and T6's graders (docs/BENCHMARK-DESIGN.md: "same
# grader"): a string match on the relayed report, not a correctness check
# on any fix the worker may also have made. The defect is the list-based
# cache in shared/serialize.py's _encode_string, reached via the public
# to_wire; either name is accepted for the function, since to_wire is the
# entry point most reports would name and _encode_string is the exact
# locus, and both correctly identify the file.
set -u

if [ ! -f BENCHMARK_REPORT.txt ]; then
    echo "FAIL: no BENCHMARK_REPORT.txt to grade"
    exit 1
fi

if ! grep -qi "serialize\.py" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name shared/serialize.py"
    exit 1
fi
if ! grep -qiE "_encode_string|to_wire" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name to_wire or _encode_string"
    exit 1
fi

echo "PASS"
exit 0
