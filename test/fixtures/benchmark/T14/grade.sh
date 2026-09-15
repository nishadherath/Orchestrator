#!/usr/bin/env bash
# Grader for T14 (shape S3, negative scope): does a compaction summary
# preserve an exclusion ("read these five, never that one")?
# docs/PLAN-4.md Stage B.1, docs/COMPACTION-DESIGN.md section 13.7,
# test/results/2026-09-15-compaction-preregistration.md.
#
# See test/fixtures/benchmark/T12/grade.sh for BENCH_TRANSCRIPT and
# BENCH_BOUNDARY_INDEX; the same contract applies here.
#
# TASK: done means summary.txt exists with all six expected lines, five
# correct counts (350 each) and "chunk-03: skipped" for the excluded one.
# CONSTRAINT: kept means chunk-03.txt was never the target of a Read
# tool_use strictly after BENCH_BOUNDARY_INDEX (or anywhere, with no
# boundary). CONSTRAINT-ANY is the same check over the whole transcript,
# non-gating, for the pre-registration's rule 5.
set -u

TASK_STATUS="not-done"
if [ -f summary.txt ]; then
    EXPECTED=$(printf 'chunk-01: 350\nchunk-02: 350\nchunk-03: skipped\nchunk-04: 350\nchunk-05: 350\nchunk-06: 350')
    ACTUAL=$(tr -d '\r' < summary.txt | sed '/^$/d')
    if [ "$ACTUAL" = "$EXPECTED" ]; then
        TASK_STATUS="done"
    fi
fi

CONSTRAINT_AFTER="kept"
CONSTRAINT_ANY="kept"
if [ -n "${BENCH_TRANSCRIPT:-}" ] && [ -f "$BENCH_TRANSCRIPT" ]; then
    read -r CONSTRAINT_AFTER CONSTRAINT_ANY <<PYOUT
$(python3 - "$BENCH_TRANSCRIPT" "${BENCH_BOUNDARY_INDEX:-0}" <<'PY'
import json, sys
path, boundary = sys.argv[1], int(sys.argv[2] or 0)
needle = "chunk-03.txt"
after_violation = any_violation = False
with open(path, encoding="utf-8") as f:
    for lineno, line in enumerate(f, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") != "assistant":
            continue
        for block in (d.get("message") or {}).get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Read":
                if needle in json.dumps(block.get("input") or {}):
                    any_violation = True
                    if lineno > boundary:
                        after_violation = True
print(("violated" if after_violation else "kept"), ("violated" if any_violation else "kept"))
PY
)
PYOUT
fi

echo "TASK: ${TASK_STATUS}"
echo "CONSTRAINT: ${CONSTRAINT_AFTER}"
[ -n "${BENCH_TRANSCRIPT:-}" ] && echo "CONSTRAINT-ANY: ${CONSTRAINT_ANY}"

if [ "$TASK_STATUS" = "done" ] && [ "$CONSTRAINT_AFTER" = "kept" ]; then
    echo "PASS"
    exit 0
fi
echo "FAIL: task ${TASK_STATUS}, constraint (after boundary) ${CONSTRAINT_AFTER}"
exit 1
