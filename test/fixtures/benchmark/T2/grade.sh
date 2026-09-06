#!/usr/bin/env bash
# Grader for T2 (mechanical, long horizon). benchmark.py invokes this with
# cwd already set to the task's working copy inside the consumer project.
#
# Pass condition: the test suite is green, `compute_hash` appears nowhere in
# the repository, and `compute_digest` appears exactly 61 times (1
# definition in utils.py, plus 1 import and 1 call site in each of the 30
# module_*.py files), verified in both directions by a simulated rename
# recorded when this fixture was built.
set -u

python3 -m unittest discover -s . -p "test_*.py"
suite_status=$?
if [ "$suite_status" -ne 0 ]; then
    echo "FAIL: test suite did not pass"
    exit 1
fi

old_count=$(grep -rn "compute_hash" --include="*.py" . | wc -l | tr -d ' ')
new_count=$(grep -rn "compute_digest" --include="*.py" . | wc -l | tr -d ' ')

if [ "$old_count" -ne 0 ]; then
    echo "FAIL: compute_hash still appears $old_count time(s)"
    exit 1
fi
if [ "$new_count" -ne 61 ]; then
    echo "FAIL: compute_digest appears $new_count time(s), expected 61"
    exit 1
fi

echo "PASS"
exit 0
