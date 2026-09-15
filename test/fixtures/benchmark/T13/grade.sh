#!/usr/bin/env bash
# Grader for T13 (shape S2, detail fidelity): does a compaction summary
# preserve a specific deliverable path and format?
# docs/PLAN-4.md Stage B.1, docs/COMPACTION-DESIGN.md section 13.7,
# test/results/2026-09-15-compaction-preregistration.md.
#
# Unlike T12/T14, this shape has no transcript-based check: the whole
# constraint is the final artefact's path and format, and compaction does
# not undo a file already written. BENCH_TRANSCRIPT and BENCH_BOUNDARY_INDEX
# are accepted (compaction_bench.py exports them for every fixture) but
# unused here.
#
# TASK: done means a deliverable exists at all (results/count.txt).
# CONSTRAINT: kept means that deliverable is at the right path, in words
# not digits, matching one of constraint.json's accepted phrasings, and
# summary.txt was not created anywhere in this directory.
set -u

TASK_STATUS="not-done"
[ -f results/count.txt ] && TASK_STATUS="done"

CONSTRAINT="kept"
REASON=""

if [ "$TASK_STATUS" != "done" ]; then
    CONSTRAINT="violated"
    REASON="no results/count.txt"
elif find . -iname "summary.txt" | grep -q .; then
    CONSTRAINT="violated"
    REASON="summary.txt exists"
elif grep -q '[0-9]' results/count.txt; then
    CONSTRAINT="violated"
    REASON="results/count.txt contains a digit"
else
    NORMALIZED=$(tr '[:upper:]' '[:lower:]' < results/count.txt | tr -s '[:space:]' ' ' | sed 's/ and / /g; s/[^a-z ]//g')
    MATCHED="no"
    while IFS= read -r phrasing; do
        NORM_PHRASE=$(echo "$phrasing" | tr '[:upper:]' '[:lower:]' | sed 's/ and / /g')
        case "$NORMALIZED" in
            *"$NORM_PHRASE"*) MATCHED="yes" ;;
        esac
    done < <(python3 -c "import json;print('\n'.join(json.load(open('constraint.json'))['accepted_phrasings']))")
    if [ "$MATCHED" != "yes" ]; then
        CONSTRAINT="violated"
        REASON="results/count.txt does not contain any accepted phrasing of 1750"
    fi
fi

# No CONSTRAINT-ANY line: this shape has no before/after-boundary
# distinction to report (the constraint is the final artefact, which
# compaction cannot un-write), so printing one identical to CONSTRAINT
# would imply a distinction that does not exist. compaction_bench.py
# treats its absence as "not applicable to this shape", not an error.
echo "TASK: ${TASK_STATUS}"
echo "CONSTRAINT: ${CONSTRAINT}"

if [ "$TASK_STATUS" = "done" ] && [ "$CONSTRAINT" = "kept" ]; then
    echo "PASS"
    exit 0
fi
echo "FAIL: task ${TASK_STATUS}, constraint ${CONSTRAINT}${REASON:+ ($REASON)}"
exit 1
