#!/usr/bin/env bash
# Grader for T3 (structured, short horizon). benchmark.py invokes this with
# cwd already set to the task's working copy inside the consumer project.
#
# Pass condition: the supplied test suite passes. Verified against three
# states when this fixture was built: the shipped stub (fails all 12,
# NotImplementedError), a correct reference implementation (passes all 12),
# and a plausible loose implementation that ignores order and repetition
# (fails exactly the two tests that check for that).
set -u

python3 -m unittest discover -s . -p "test_*.py"
suite_status=$?
if [ "$suite_status" -ne 0 ]; then
    echo "FAIL: test suite did not pass"
    exit 1
fi

echo "PASS"
exit 0
