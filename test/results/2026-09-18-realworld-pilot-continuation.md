# Real-world pilot: 18-episode continuation and W05 decision

Date: 2026-09-18. Execution result: **COMPLETE**. W05 decision: **proceed to
offline W06 with B0 retained and B1 as the adaptive finalist**.

All 18 authorised continuation episodes completed. Model identity, provider
accounting, event chains, actor boundaries and protected-oracle integrity were
valid in every episode, so all 18 records are learning-eligible. Seven hidden
grades passed and eleven failed. The machine-readable record is
[`2026-09-18-realworld-pilot-continuation.json`](2026-09-18-realworld-pilot-continuation.json).

## Bound execution

| Field | Value |
| :--- | :--- |
| Candidate | `ce6cf4467b0ec462202f5cf419c5845aac471d30a9956fe3382b620b60660bec` |
| Manifest | `537a21cbb46012923ac229d3a4f98a8dd7883cf60a67fc084e8a80c25d12b83c` |
| Authorisation | `13c02cecafcfcf53ad0e0a1eb3afc09919e837ceabe50521b05efdbad79b7b63` |
| Launch revision | `7ad19c8` |
| Bundle | `2026-09-18-de8cefc` |
| Episode reservation ceiling | USD 72.00 |
| Calibration headroom | USD 2.00; unused |
| Combined authorised ceiling | USD 74.00 |
| Reconciled spend | **USD 1.281458307** |
| Unused ceiling | USD 72.718541693 |

The continuation used 1.73 percent of its authorised ceiling. Its mean episode
cost was USD 0.071192128, within the pre-run USD 1-22 planning range for all 18
episodes. The run used 21 attempts: 20 Sonnet 5 low-effort attempts and one
Opus 5 high-effort fallback. Aggregate billing named Haiku 4.5 as auxiliary CLI
overhead on every attempt; that cost remains inside the reported totals.

Aggregate recorded usage was 198 ordinary input tokens, 115,841 cache-creation
input tokens, 577,949 cache-read input tokens and 52,069 output tokens. Model
wall time totalled 595.534 seconds. No Controller role ran.

## Episode results

| Task | B0 | B1 | B2 |
| :--- | :--- | :--- | :--- |
| D03 | fail; USD 0.042479200 | fail; USD 0.034024000 | fail; USD 0.032197200 |
| D05 | pass; USD 0.016269000 | pass; USD 0.021105601 | pass; USD 0.017759801 |
| D07 | pass; USD 0.051761001; two Sonnet attempts | pass; USD 0.073662000 | pass; USD 0.061884800 |
| D08 | pass; USD 0.410062700; two Sonnet attempts then Opus | fail; USD 0.095758601 | fail; USD 0.113002400 |
| D09 | fail; USD 0.053737001 | fail; USD 0.053385201 | fail; USD 0.061770200 |
| D10 | fail; USD 0.046780801 | fail; USD 0.051069000 | fail; USD 0.044749800 |

| Policy | Hidden passes | Attempts | Spend | Mean episode cost |
| :--- | ---: | ---: | ---: | ---: |
| B0 | 3/6 | 9 | USD 0.621089703 | USD 0.103514951 |
| B1 | 2/6 | 6 | USD 0.329004403 | USD 0.054834067 |
| B2 | 2/6 | 6 | USD 0.331364201 | USD 0.055227367 |

The only differentiated policy path was D08-B0. Its first Sonnet attempt left a
visible failure, its local repair also failed visibly, and the fixed Opus
fallback passed both visible and hidden checks. D08-B1 and D08-B2 happened to
pass the visible check on their first independent Sonnet samples, so both
policies correctly stopped and later failed the hidden grade. This is evidence
that fallback can recover a visible failure. With one stochastic episode, it is
not evidence that B0 has a stable one-task acceptance advantage.

D03, D09 and D10 passed visible acceptance but failed hidden grading under all
three policies. Those failures supplied no observable trigger that B1 or B2
could use. They point to worker or visible-acceptance coverage, rather than a
demonstrated routing defect.

## Complete 24-episode pilot decision

Including the six-episode checkpoint, the pilot spent **USD 1.420694908** of
the combined USD 100 ceiling and accepted 13 of 24 hidden grades. Aggregate
usage was 240 ordinary input tokens, 132,940 cache-creation tokens, 678,627
cache-read tokens and 56,416 output tokens over 27 attempts and 666.315 model
seconds.

| Policy | Hidden passes | Spend | Cost per accepted result |
| :--- | ---: | ---: | ---: |
| B0 | 5/8 | USD 0.674036103 | USD 0.134807221 |
| B1 | 4/8 | USD 0.368289403 | USD 0.092072351 |
| B2 | 4/8 | USD 0.378369402 | USD 0.094592351 |

B1 and B2 took the same observed path on every pilot task and tied on
acceptance. B1 cost USD 0.010079999 less. That small difference is not a
performance discovery, but it gives no reason to replace the incumbent with B2.
The conservative adaptive finalist is therefore **B1**, with **B0 retained** as
the required fixed-fallback baseline.

B1 spent 45 percent less than B0 and had a 32 percent lower measured cost per
accepted result, while accepting one fewer task. This is sufficient to satisfy
the predeclared credible-cost-benefit condition for continuing to W06. The
sample is too small and confounded by independent stochastic outputs to change
the redistributable's defaults. No B2 revision is justified because the failed
tasks exposed no policy-visible signal that its triggers could use.

Proceed with **offline W06 corpus completion and sealing**. Do not start W07
model calls yet. After W06, freeze a new B0-versus-B1 development manifest and
replace the old USD 110-220 campaign estimate with a stage-specific projection
from the measured task shapes. The Controller path remains live-unverified and
must not be claimed as pilot-proven.
