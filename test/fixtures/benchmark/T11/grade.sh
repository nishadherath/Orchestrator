#!/usr/bin/env bash
# Grader for T11 (open, long horizon, T7's lineage at a larger scale).
# benchmark.py invokes this with cwd already set to the task's working copy
# inside the consumer project, after writing BENCHMARK_REPORT.txt there with
# the worker's relayed final report.
#
# Same shape as T5 to T8: a string match on the relayed report, not a
# correctness check on a fix, because the task is diagnose-only.
#
# The defect is shared/registry.py's resolve(), which rebuilds the whole key
# index on every call. Catalogue, checkout and search each call it once per
# record, so all three are quadratic in tenant size; that is why only the
# large tenants regressed. Nothing about resolve() looks wrong when read on
# its own, and three decoys look worse on inspection than it does:
#
#   - checkout's per-line stretch() is the largest single cost at small n and
#     stays the largest absolute number at every size measured, but it is
#     linear, and catalogue and search do not use it at all;
#   - serialize.py's _encode_string scans a list, which is precisely T7's
#     defect, but the list is capped at CACHE_LIMIT so the scan is constant;
#   - inventory is last month's largest diff by a wide margin and is correct.
#
# So the diagnosis is reachable by running bench.py at more than one size and
# reading the curve, and is not reachable by reading the diff or by timing one
# size. That is the property the task is built to test.
#
# Three gating checks, all on the report:
#   1. It names shared/registry.py.
#   2. It names resolve.
#   3. It states the mechanism: the index is rebuilt on every call, or the
#      cost is quadratic in the record count. The alternation is deliberately
#      wide, because three of the four graders written for this benchmark
#      before Stage 7 needed correcting for false negatives on phrasing (D16,
#      D17, D30). Check 3 exists because a report that lists all seven
#      services and both shared modules as candidates would otherwise pass on
#      checks 1 and 2 alone without having diagnosed anything; naming the
#      mechanism is what separates a diagnosis from a shotgun.
set -u

if [ ! -f BENCHMARK_REPORT.txt ]; then
    echo "FAIL: no BENCHMARK_REPORT.txt to grade"
    exit 1
fi

if ! grep -qiE "registry(\.py)?" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name shared/registry.py"
    exit 1
fi
if ! grep -qiE "resolve" BENCHMARK_REPORT.txt; then
    echo "FAIL: report does not name resolve"
    exit 1
fi
if ! grep -qiE "quadratic|o\(n\^?2\)|n\^2|n\*n|n squared|square of|rebuil|re-?built|re-?construct|re-?creat|from scratch|(on|for|per) (every|each) (call|lookup|key|item|record|row|invocation)|(every|each) (call|lookup|key|item|record|row|invocation)" BENCHMARK_REPORT.txt; then
    echo "FAIL: report names registry.resolve but not the mechanism (index rebuilt per call, cost quadratic in record count)"
    exit 1
fi

# Diagnostics only, never gating: which decoys the report also raised, and
# whether it shows evidence of having run bench.py at more than one size.
BLAMES_HASHING=no
BLAMES_SERIALIZE=no
BLAMES_INVENTORY=no
grep -qiE "hashing\.py|ROUNDS|stretch" BENCHMARK_REPORT.txt && BLAMES_HASHING=yes
grep -qiE "serialize\.py|_encode_string|CACHE_LIMIT" BENCHMARK_REPORT.txt && BLAMES_SERIALIZE=yes
grep -qiE "inventory" BENCHMARK_REPORT.txt && BLAMES_INVENTORY=yes

echo "PASS (also mentions hashing: ${BLAMES_HASHING}; serialize: ${BLAMES_SERIALIZE}; inventory: ${BLAMES_INVENTORY})"
exit 0
