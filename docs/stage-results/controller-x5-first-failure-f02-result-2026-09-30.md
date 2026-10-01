# X5 F02 first-failure development result

Date: 2026-09-30 Australia/Sydney. The F02
[manifest](../../test/results/2026-09-30-controller-x5-first-failure-f02-manifest.json)
and [dated notice](controller-x5-first-failure-f02-notice-2026-09-30.md)
bound one new producer and conditional matched S/A continuations. The final
full offline harness passed **83/83**. WSL credential, Controller Graft and
actor preparation completed at zero provider spend before dispatch.

Observed: F02's authored Click baseline failed two of three public checks
and passed 3/7 protected cases. A one-module repair still failed public and
passed 6/7; the upstream reference and a separate repair passed public and
7/7. The new producer made exactly one Sonnet-low call. Its served receipt
identified `claude-sonnet-5`, was terminal, writer-stopped and identity-valid,
and settled **USD 0.0695534** reported API-equivalent with no unresolved
charge or budget breach. The public check passed on that first attempt;
protected grading scored **100/100**, with zero critical errors. The
[result](../../test/results/2026-09-30-controller-x5-first-failure-f02-run/producer-result.json)
records `accepted`, `qualified: true`, `eligible: false` and 22.883 seconds
for the producer phase. No S or A successor started. Do not replay F02.

Inference: F02 independently repeats the lack of headroom found on F01.
The case was a stronger provider-free baseline than a single trivial fault,
but the worker repaired it within one ordinary attempt. The first-failure
route has produced zero eligible matched comparisons across R3, R4, P02,
F01 and F02. Their producer receipts total **USD 0.597339801** reported
API-equivalent. Continuing to author similar self-contained regressions is
unlikely to efficiently estimate Controller uplift.

Unknown: whether genuinely ambiguous real issues with competing public
causes would create a first-failure checkpoint, and whether a Controller
would outperform a direct second worker once that checkpoint exists. A
public-only risk review after apparent success is a separate possible
hypothesis; it must be predeclared and tested on new cases, without using a
hidden score as a trigger. The exact failed-report S/A path remains
provider-free qualified but has not run live. B0 remains the shipping default
and X6 remains sealed.
