#!/usr/bin/env bash
# Grader for T4 (structured, long horizon). benchmark.py invokes this with
# cwd already set to the task's working copy inside the consumer project.
#
# Pass condition: both supplied test files pass (test_callers.py, already
# green in the starting state and required to stay green; test_new_interface.py,
# failing in the starting state until Store exists), and KVStore is gone
# from every .py file, not left behind alongside Store. That last check
# goes beyond docs/BENCHMARK-DESIGN.md's baseline "supplied tests pass" for
# structured tasks, but "ported to a new interface" means the old one is
# retired, not duplicated, and that is not otherwise exercised by either
# test file.
set -u

python3 -m unittest discover -s . -p "test_*.py"
suite_status=$?
if [ "$suite_status" -ne 0 ]; then
    echo "FAIL: test suite did not pass"
    exit 1
fi

old_count=$(grep -rn "KVStore" --include="*.py" . | wc -l | tr -d ' ')
if [ "$old_count" -ne 0 ]; then
    echo "FAIL: KVStore still appears $old_count time(s), the port is incomplete"
    exit 1
fi

echo "PASS"
exit 0
