# X5 F01 first-failure development result

Date: 2026-09-30 Australia/Sydney. The single-use [manifest](../../test/results/2026-09-30-controller-x5-first-failure-f01-manifest.json)
and [dated notice](controller-x5-first-failure-f01-notice-2026-09-30.md)
bound one new producer and conditional S/A continuations. The final full
offline harness passed **83/83**. WSL credential, Controller Graft and actor
preparation completed with zero provider calls before dispatch.

Observed: F01's baseline had three failing public checks and passed 2/6
protected cases. One authored partial repair still failed public and passed
4/6 protected cases; both the upstream reference and an independent repair
passed public and 6/6 protected cases. The new producer made exactly one
Sonnet-low call. Its served receipt identified `claude-sonnet-5`, was terminal,
writer-stopped and identity-valid, and settled **USD 0.1270084** reported
API-equivalent with no unresolved charge or budget breach. The public check
passed on that first attempt; protected grading scored **100/100**, with zero
critical errors. The [result](../../test/results/2026-09-30-controller-x5-first-failure-f01-run/producer-result.json)
records `accepted`, `qualified: true`, `eligible: false` and 37.472 seconds
for the producer phase. No S or A successor started. Do not replay F01.

Inference: even a fresh two-regression case with a failing baseline and
independent partial and complete repairs did not create a first public
failure with this worker and contract. F01 demonstrates that the actor and
protected grading work live; it supplies **no Controller uplift comparison**.
R3, R4, P02 and F01 producers together reported **USD 0.527786401**
API-equivalent and produced zero matched Controller pairs.

Unknown: the first public-failure rate on a broader independently frozen
development set, the quality of a live Controller handoff after a genuine
first failure, and its effect against a direct second worker call. The F01
Controller packet would use an exact failed public report if such a failure
occurred, but this path has not run live. B0 remains the shipping default and
X6 remains sealed.
