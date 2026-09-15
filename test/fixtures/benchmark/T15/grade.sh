#!/usr/bin/env bash
# Grader for T15: not part of the automated decomposition or preservation
# measurements, only benchmark.load_task's own contract (task.md, repo/,
# grade.sh). docs/PLAN-5.md Stage D.1: this fixture exists to run long
# enough, in an interactive session, for tokenSamples to be observed; it
# carries no constraint to preserve, so this grader checks only that the
# total was written correctly.
set -u

TASK_STATUS="not-done"
if [ -f summary.txt ]; then
    COUNT=$(tr -d '[:space:]' < summary.txt)
    if [ "$COUNT" = "4200" ]; then
        TASK_STATUS="done"
    fi
fi

echo "TASK: ${TASK_STATUS}"

if [ "$TASK_STATUS" = "done" ]; then
    echo "PASS"
    exit 0
fi
echo "FAIL: task ${TASK_STATUS}"
exit 1
