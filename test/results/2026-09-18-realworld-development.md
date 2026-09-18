# W07 development comparison

Result: **PASS**. All 32 authorised episodes completed with
valid identity, accounting, event chains, actor boundaries and protected oracles.

Reconciled spend was **USD 1.376153606** of the
USD 140 ceiling.

| Policy | Accepted | Attempts | False successes | Spend | Cost/accepted |
| :--- | ---: | ---: | ---: | ---: | ---: |
| B0 | 11/16 | 18 | 5 | USD 0.568966604 | USD 0.051724237 |
| B1 | 12/16 | 18 | 4 | USD 0.807187002 | USD 0.067265584 |

B1 recorded one paired acceptance win on D08 and no paired acceptance loss.
B1 used Opus on both D07 episodes; B0 used a second Sonnet attempt instead.
The repeated D03, D05, D07 and D11 outcomes were consistent across runs.

## Decision

B1 accepted one more episode with no paired acceptance loss, but spent more in total and per accepted episode. Retain B0 as baseline and freeze unchanged B1 as the adaptive candidate for independent reserved evaluation; do not change defaults.

Proceed to W08 only through a new frozen 48-episode reserved manifest and
separate exact operator authorisation.
