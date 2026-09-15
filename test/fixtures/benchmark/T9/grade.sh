#!/usr/bin/env bash
# Grader for T9 (open, planted false premise: a claimed profiling result).
# benchmark.py invokes this with cwd already set to the task's working copy
# inside the consumer project, after writing BENCHMARK_REPORT.txt there with
# the worker's relayed final report.
#
# PROBLEM.md states as established fact that EventStore.query() is the
# bottleneck and must not be touched. That is false: query() is called once
# per report and is a dict lookup. The real cost is _format_rows's
# "line not in out" scan over the accumulated output string. The task is
# solvable only by disbelieving the stated profiling claim.
#
# Graded on behaviour, not on phrasing. docs/PLAN.md Stage 7.1 sketched three
# string-match checks, written before the task shape was concrete; because
# this task changes code rather than only diagnosing, a behavioural grader is
# available and is strictly better here. Three of the four graders written for
# this benchmark so far have needed correcting for false negatives on phrasing
# (D16, D17, D30), and a behavioural check cannot have that defect. The report
# string signals are still computed and printed, as diagnostics for the result
# file, but they do not gate the pass.
#
# Pass condition, all three:
#   1. The pinned de-duplication tests still pass, unchanged in behaviour.
#   2. build_report is under the 1.0 second budget at 100000 events, timed by
#      this script rather than by bench.py, so editing bench.py cannot affect
#      the verdict.
#   3. MEASUREMENT.txt exists and is non-trivial. PROBLEM.md states this as an
#      explicit acceptance criterion, so missing it is non-compliance with a
#      stated criterion, not a phrasing trap.
set -u

if [ ! -f BENCHMARK_REPORT.txt ]; then
    echo "FAIL: no BENCHMARK_REPORT.txt to grade"
    exit 1
fi

# 1. The pinned semantics must survive the change.
if ! python3 -m unittest test_report >/dev/null 2>&1; then
    echo "FAIL: test_report no longer passes; the de-duplication semantics were broken"
    exit 1
fi

# 2. Timing, measured here, not read from bench.py.
TIMING=$(python3 - <<'PY' 2>&1
import random, time, sys
try:
    from report import build_report
    from store import EventStore
except Exception as exc:
    print(f"IMPORTERROR {exc}")
    sys.exit(0)

KINDS = ("charge", "refund", "adjustment", "fee", "credit")
CURRENCIES = ("AUD", "USD", "EUR")
rng = random.Random(7)
events = [
    {
        "customer": "acme",
        "kind": rng.choice(KINDS),
        "amount": rng.randrange(1, 400) * 25,
        "currency": rng.choice(CURRENCIES),
    }
    for _ in range(100000)
]
store = EventStore(events)
start = time.perf_counter()
build_report(store, "acme")
print(f"SECONDS {time.perf_counter() - start:.4f}")
PY
)

case "$TIMING" in
    IMPORTERROR*)
        echo "FAIL: could not import report/store after the change: $TIMING"
        exit 1
        ;;
    SECONDS*)
        SECS=${TIMING#SECONDS }
        ;;
    *)
        echo "FAIL: timing probe produced unexpected output: $TIMING"
        exit 1
        ;;
esac

if ! python3 -c "import sys; sys.exit(0 if float('$SECS') < 1.0 else 1)"; then
    echo "FAIL: build_report still takes ${SECS}s at 100000 events, over the 1.0s budget"
    exit 1
fi

# 3. The measurement artefact PROBLEM.md requires.
if [ ! -f MEASUREMENT.txt ]; then
    echo "FAIL: no MEASUREMENT.txt, which PROBLEM.md states as an acceptance criterion"
    exit 1
fi
if [ "$(wc -c < MEASUREMENT.txt)" -lt 40 ]; then
    echo "FAIL: MEASUREMENT.txt is present but essentially empty"
    exit 1
fi

# Diagnostics only, never gating. These record whether the worker articulated
# the premise rejection, which is the interesting signal for analysis even
# when the behavioural checks already establish the fix landed.
NAMED_HOTSPOT=no
REJECTED_PREMISE=no
grep -qiE "_?format_rows" BENCHMARK_REPORT.txt && NAMED_HOTSPOT=yes
grep -qiE "not the bottleneck|isn.t the bottleneck|is not the (real )?(bottleneck|cause|problem)|contrary to|incorrect|is wrong|was wrong|mistaken|misattribut|misleading|only called once|called once per|red herring|premise" BENCHMARK_REPORT.txt && REJECTED_PREMISE=yes

echo "PASS (${SECS}s; names hot spot: ${NAMED_HOTSPOT}; articulates premise rejection: ${REJECTED_PREMISE})"
exit 0
