# Real-world pilot: six-episode instrumentation checkpoint

Date: 2026-09-18. Result: **PASS**.

The exact candidate-bound checkpoint completed all six authorised episodes.
Every task passed visible and hidden checks on its first Sonnet-low attempt.
Model identity, provider-reported cost, event chains, actor boundaries and
protected oracles reconciled in every episode. The machine-readable record is
[`2026-09-18-realworld-pilot-checkpoint.json`](2026-09-18-realworld-pilot-checkpoint.json).

## Bound execution

| Field | Value |
| :--- | :--- |
| Candidate | `4fd79c1577ef97ccae9430d9b5f666edf72172d0973135baa3808642e6d08dcd` |
| Manifest | `86e5fe1aec9a0d4db03ac5cf84f26e38e8ab9ce57a9e5173c583c1e324e793b7` |
| Authorisation | `161e07cd92b0b048cc5a8840df3b6a10ad23ff3418f162c4e976bedbb56428a3` |
| Launch revision | `1da7078` |
| Bundle | `2026-09-18-de8cefc` |
| Episode reservation ceiling | USD 24.00 |
| Calibration headroom | USD 2.00; unused |
| Combined authorised ceiling | USD 26.00 |
| Reconciled spend | **USD 0.139236601** |
| Unused ceiling | USD 25.860763399 |

The run used 0.54 percent of the authorised ceiling. Its mean episode cost was
USD 0.0232061. The earlier USD 1-2 illustrative episode estimate was 43-86
times the observed mean for these two easy, first-attempt tasks. That estimate
must not be replaced campaign-wide yet because this checkpoint exercised no
fallback, escalation or Controller path.

## Episode results

| Episode | Policy | Path | Hidden grade | Cost (USD) | Wall time |
| :--- | :---: | :--- | :---: | ---: | ---: |
| D01-B0 | B0 | `worker-sonnet-low` | pass | 0.029786600 | 10.547 s |
| D01-B1 | B1 | `worker-sonnet-low` | pass | 0.015129000 | 8.140 s |
| D01-B2 | B2 | `worker-sonnet-low` | pass | 0.015738601 | 7.547 s |
| D11-B0 | B0 | `worker-sonnet-low` | pass | 0.023159800 | 11.953 s |
| D11-B1 | B1 | `worker-sonnet-low` | pass | 0.024156000 | 11.578 s |
| D11-B2 | B2 | `worker-sonnet-low` | pass | 0.031266600 | 21.016 s |

All six task messages reported `claude-sonnet-5` with low effort. Aggregate
billing also named `claude-haiku-4-5-20251001` as auxiliary CLI overhead in
every episode; its cost remains included in the provider-reported total rather
than being discarded or treated as task-model substitution.

Aggregate recorded usage was 42 ordinary input tokens, 17,099 cache-creation
input tokens, 100,678 cache-read input tokens and 4,347 output tokens. Model
wall time totalled 70.781 seconds. These categories come from the provider
terminal envelopes and remain separate.

## Interpretation and decision

The checkpoint validates the live execution boundary. It proves this candidate
can run the policy loop end to end with exact model attribution, complete cost
settlement, external grading and protected-oracle checks under the durable
budget and journal contracts.

It does not rank B0, B1 and B2. Both selected tasks were solved by the common
floor worker, so all policies followed the same path and produced only two
observations per arm. There is no escalation, Opus or Controller evidence and
no sound basis for promoting a policy or changing defaults from this result.

The predeclared infrastructure continuation condition is satisfied. The next
W05 action is to prepare the remaining 18 pilot episodes across D03, D05 and
D07-D10 under B0, B1 and B2. Keep the USD 4 per-episode cap. The unspent portion
of this authorisation does not authorise those calls; bind a new manifest and
operator approval before execution. Stop the expanded pilot if it still yields
no policy-path differentiation or if any existing integrity condition fails.
