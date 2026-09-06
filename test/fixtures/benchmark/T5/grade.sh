#!/usr/bin/env bash
# Grader for T5 (open, short). benchmark.py invokes this with cwd already set
# to the task's working copy inside the consumer project, after writing
# BENCHMARK_REPORT.txt there with the worker's relayed final report.
#
# Pass condition: the report names both the file and the function that hold
# the planted defect. This is a string match, not a correctness check on any
# fix the worker may also have made (grading a diagnosis, not a patch, is the
# point of this task shape; docs/BENCHMARK-DESIGN.md).
set -u

if [ ! -f BENCHMARK_REPORT.txt ]; then
    echo "FAIL: no BENCHMARK_REPORT.txt to grade"
    exit 1
fi

if ! grep -qi "pricing\.py" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name pricing.py"
    exit 1
fi
if ! grep -qi "apply_discount" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name apply_discount"
    exit 1
fi

echo "PASS"
exit 0
