# X5 H01 authored development producer and post hoc audit

Date: 2026-09-30 Australia/Sydney. Status: **one settled B0 producer; no
eligible S/A continuation; no measured Controller uplift**. B0 remains the
shipping default and X6 remains sealed.

H01 is an authored development adaptation of pinned httpcore 1.0.9. The
[preflight](controller-x5-httpcore-authored-preflight-2026-09-30.md) records
its source, licensing, isolated actor, frozen public and protected checks,
calibration and limits. The [public issue](https://github.com/encode/httpcore/issues/1110)
and [PR](https://github.com/encode/httpcore/pull/1111) reveal the mechanism,
so H01 is not blind natural evidence.

## Frozen producer observation

The single-use [manifest](../../test/results/2026-09-30-controller-x5-h01-producer-manifest.json)
and [dated notice](../../test/results/2026-09-30-controller-x5-h01-producer-notice.json)
bound one B0 attempt to a USD 5 maximum. The projection stated before launch
was USD 0.2–1.5 API-equivalent. The
[settled result](../../test/results/2026-09-30-controller-x5-h01-producer-run/producer-result.json)
records one call, USD 0.214186 provider-reported API-equivalent spend, no
unresolved reservation and a 77.924-second producer wall time. The candidate
edited the sync and async pool sources. The evaluator-owned Q1 isolated grader
reported accepted and 100/100 on its four frozen checks: public, sync surplus,
async competing-origin and ordinary cleanup. No S/A call was eligible under
the predeclared first-pass stop rule. The frozen score and stop decision stand;
there was no Controller comparison.

## Distinct post hoc observation

Source review after settlement identified a missed path: the candidate's
surplus and replacement guards preserve assigned connections, but its expiry
cleanup can still close one after assignment and before request handling. The
[separate Q1 isolated probe](../../test/results/2026-09-30-controller-x5-httpcore-posthoc-expiry.py)
holds that state across two pool passes. Its
[saved result](../../test/results/2026-09-30-controller-x5-httpcore-posthoc-expiry.json)
reports `assigned_retained=false` for the settled candidate in both sync and
async paths; the reference and alternative repairs report `true` in both.
Ordinary unassigned expiry still works in every variant. This probe was
created after the paid call, outside H01's frozen oracle and acceptance.
It cannot retrospectively change the 100/100 result or justify an S/A run
against a revised H01 grader.

**Inference:** the frozen grader overstated completeness against the broader
state-window property. This is an evaluator coverage failure and a useful
calibration result, not evidence of Controller uplift. Retire H01 from paid
comparisons. For a distinct future authored development case, enumerate each
cleanup path against assigned and unassigned state before freeze, include
independent negative controls, and test the producer stop against the full
frozen property. Do not replay this case to manufacture an eligible S/A pair.

**Untested risks:** the post hoc schedule uses fake connections and does not
measure a real network timeout; other pool paths may also be uncovered. One
authored case has no external-validity claim. The repository's full offline
harness passed 83/83 on stable files before the paid run; the result and this
documentation make no consumer source or distribution changes.
