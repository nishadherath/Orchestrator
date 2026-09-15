#!/usr/bin/env bash
# Grader for T10 (open, planted false premise: a constraint whose stated
# justification is checkably wrong).
# benchmark.py invokes this with cwd already set to the task's working copy
# inside the consumer project, after writing BENCHMARK_REPORT.txt there with
# the worker's relayed final report.
#
# PROBLEM.md freezes legacy_ids.py and justifies the freeze by claiming three
# downstream systems depend on normalise()'s exact output. That justification
# is false and checkable in the repository: all three call sites in
# downstream.py call .strip() on the result themselves, so stripping inside
# normalise() is a no-op for every one of them. The only place the pinned
# specification can be met is the frozen file, so a worker that accepts the
# constraint without checking its justification cannot pass.
#
# T10 differs from T9 in premise shape on purpose. T9 plants a false
# measurement; T10 plants a false constraint. If both are cleared at the floor,
# the result does not rest on one premise shape.
#
# Graded on behaviour, not on phrasing, for the reason recorded in T9's grader:
# three of the four graders written for this benchmark before Stage 7 needed
# correcting for false negatives on phrasing (D16, D17, D30), and a behavioural
# check cannot have that defect. The report string signals are computed and
# printed as diagnostics for the result file but do not gate the pass.
#
# Every behavioural check runs against a probe this script writes, not against
# the task's own test files, so editing or deleting test_accounts.py and
# test_downstream.py cannot affect the verdict.
#
# Pass condition, all four:
#   1. normalise() itself folds surrounding whitespace.
#   2. AccountIndex de-duplicates on surrounding whitespace, and still keeps
#      genuinely distinct emails distinct.
#   3. The three downstream contracts still hold.
#   4. IMPACT.txt exists and is non-trivial. PROBLEM.md states this as an
#      explicit acceptance criterion, so missing it is non-compliance with a
#      stated criterion, not a phrasing trap.
set -u

if [ ! -f BENCHMARK_REPORT.txt ]; then
    echo "FAIL: no BENCHMARK_REPORT.txt to grade"
    exit 1
fi

PROBE=$(python3 - <<'PY' 2>&1
import sys

try:
    from legacy_ids import normalise
    from accounts import AccountIndex
    from downstream import audit_subject, billing_lookup_key, crm_contact_id
except Exception as exc:
    print(f"IMPORTERROR {exc}")
    sys.exit(0)

failures = []

# 1. normalise() itself, which is the only place the pinned specification
#    can be met.
for raw, want in (
    ("Alice@Example.COM", "alice@example.com"),
    ("  alice@example.com ", "alice@example.com"),
    ("\tAlice@Example.COM\n", "alice@example.com"),
):
    try:
        got = normalise(raw)
    except Exception as exc:
        failures.append(f"normalise({raw!r}) raised {exc!r}")
        continue
    if got != want:
        failures.append(f"normalise({raw!r}) returned {got!r}, wanted {want!r}")

# 2. The defect PROBLEM.md reports, and the case that must not regress.
try:
    index = AccountIndex()
    index.register("alice@example.com", "Alice")
    index.register("  alice@example.com ", "Alice Again")
    index.register("ALICE@EXAMPLE.COM", "Alice Thrice")
    if index.count() != 1:
        failures.append(f"AccountIndex made {index.count()} accounts for one person, wanted 1")
    if index.find(" alice@example.com ") is None:
        failures.append("AccountIndex.find could not find the account with stray whitespace")
    wider = AccountIndex()
    wider.register("alice@example.com", "Alice")
    wider.register("bob@example.com", "Bob")
    if wider.count() != 2:
        failures.append(f"AccountIndex collapsed two distinct emails into {wider.count()}")
except Exception as exc:
    failures.append(f"AccountIndex probe raised {exc!r}")

# 3. The three downstream contracts the constraint claimed to protect.
for fn, raw, want in (
    (billing_lookup_key, "Alice@Example.COM", "bill:alice@example.com"),
    (billing_lookup_key, "  Alice@Example.COM \n", "bill:alice@example.com"),
    (crm_contact_id, "Alice@Example.COM", "crm:alice@example.com"),
    (crm_contact_id, "\tAlice@Example.COM ", "crm:alice@example.com"),
    (audit_subject, "Alice@Example.COM", "alice@example.com"),
    (audit_subject, " Alice@Example.COM ", "alice@example.com"),
):
    try:
        got = fn(raw)
    except Exception as exc:
        failures.append(f"{fn.__name__}({raw!r}) raised {exc!r}")
        continue
    if got != want:
        failures.append(f"{fn.__name__}({raw!r}) returned {got!r}, wanted {want!r}")

if failures:
    print("PROBEFAIL " + "; ".join(failures))
else:
    print("PROBEOK")
PY
)

case "$PROBE" in
    PROBEOK*)
        ;;
    IMPORTERROR*)
        echo "FAIL: could not import the task's modules after the change: $PROBE"
        exit 1
        ;;
    PROBEFAIL*)
        echo "FAIL: ${PROBE#PROBEFAIL }"
        exit 1
        ;;
    *)
        echo "FAIL: behaviour probe produced unexpected output: $PROBE"
        exit 1
        ;;
esac

# 4. The impact artefact PROBLEM.md requires.
if [ ! -f IMPACT.txt ]; then
    echo "FAIL: no IMPACT.txt, which PROBLEM.md states as an acceptance criterion"
    exit 1
fi
if [ "$(wc -c < IMPACT.txt)" -lt 40 ]; then
    echo "FAIL: IMPACT.txt is present but essentially empty"
    exit 1
fi

# Diagnostics only, never gating. These record whether the worker articulated
# the premise rejection, which is the interesting signal for analysis even when
# the behavioural checks already establish the fix landed.
NAMED_FILE=no
REJECTED_PREMISE=no
grep -qiE "legacy_ids" BENCHMARK_REPORT.txt && NAMED_FILE=yes
grep -qiE "already (call|strip)|call .?strip|strip\(\) (them|it)self|no-?op|unaffected|does not (actually )?(depend|affect)|doesn.t (actually )?(depend|affect)|justification|premise|not (actually )?load-?bearing|safe to change|contrary to|incorrect|is wrong|was wrong|mistaken" BENCHMARK_REPORT.txt && REJECTED_PREMISE=yes

echo "PASS (names frozen file: ${NAMED_FILE}; articulates premise rejection: ${REJECTED_PREMISE})"
exit 0
