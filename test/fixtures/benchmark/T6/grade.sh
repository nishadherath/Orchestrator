#!/usr/bin/env bash
# Grader for T6 (open, long). benchmark.py invokes this with cwd already set
# to the task's working copy inside the consumer project, after writing
# BENCHMARK_REPORT.txt there with the worker's relayed final report.
#
# Same shape as T5's grader (docs/BENCHMARK-DESIGN.md: "same grader"): a
# string match on the relayed report, not a correctness check on any fix the
# worker may also have made. The defect here sits three files deep from the
# reproduce command in BUG_REPORT.md (cart.py -> pricing.py -> tax.py), so
# naming tax.py and get_tax_amount means the chain was actually traced.
set -u

if [ ! -f BENCHMARK_REPORT.txt ]; then
    echo "FAIL: no BENCHMARK_REPORT.txt to grade"
    exit 1
fi

if ! grep -qi "tax\.py" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name tax.py"
    exit 1
fi
if ! grep -qi "get_tax_amount" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name get_tax_amount"
    exit 1
fi

echo "PASS"
exit 0
