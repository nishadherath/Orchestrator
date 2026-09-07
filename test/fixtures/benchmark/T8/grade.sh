#!/usr/bin/env bash
# Grader for T8 (open, short, a fair-scale proxy for F09's row). benchmark.py
# invokes this with cwd already set to the task's working copy inside the
# consumer project, after writing BENCHMARK_REPORT.txt there with the
# worker's relayed final report.
#
# Pass condition: the report names api_client.py, names create_order
# specifically (not get_order, list_orders, or cancel_order, all of which
# are genuinely safe to retry), and names the duplicate-side-effect risk in
# some form. This is a string match, not a correctness check on any fix the
# worker may also have proposed (grading a diagnosis, not a patch, is the
# point of this task shape; docs/BENCHMARK-DESIGN.md).
set -u

if [ ! -f BENCHMARK_REPORT.txt ]; then
    echo "FAIL: no BENCHMARK_REPORT.txt to grade"
    exit 1
fi

if ! grep -qi "api_client\.py" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name api_client.py"
    exit 1
fi
if ! grep -qi "create_order" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name create_order"
    exit 1
fi
if ! grep -Eqi "idempoten|duplicat|double.charg|double.creat|two orders|second order|creat\w*.{0,30}twice|twice.{0,30}creat\w*|order.{0,20}twice|twice.{0,20}order" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name the duplicate-side-effect risk"
    exit 1
fi

echo "PASS"
exit 0
