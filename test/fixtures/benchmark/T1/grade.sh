#!/usr/bin/env bash
# Grader for T1 (mechanical, short). benchmark.py invokes this with cwd
# already set to the task's working copy inside the consumer project.
#
# Pass condition: the test suite is green, `compute_total` appears nowhere in
# the repository, and `compute_sum` appears exactly 6 times (1 definition,
# 2 imports, 3 call sites), fixed by a simulated rename recorded in the T1
# pilot pre-registration.
set -u

python3 -m unittest discover -s . -p "test_*.py"
suite_status=$?
if [ "$suite_status" -ne 0 ]; then
    echo "FAIL: test suite did not pass"
    exit 1
fi

old_count=$(grep -rn "compute_total" --include="*.py" . | wc -l | tr -d ' ')
new_count=$(grep -rn "compute_sum" --include="*.py" . | wc -l | tr -d ' ')

if [ "$old_count" -ne 0 ]; then
    echo "FAIL: compute_total still appears $old_count time(s)"
    exit 1
fi
if [ "$new_count" -ne 6 ]; then
    echo "FAIL: compute_sum appears $new_count time(s), expected 6"
    exit 1
fi

echo "PASS"
exit 0
