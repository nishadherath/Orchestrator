# Real-world episode runner offline qualification

Result: **PASS**. Mode: `offline-fake-worker-v1`. Model calls: **0**.

The runner replayed every scenario from a separate campaign root. Hidden grading ran only
after episode termination. Unknown terminal usage retained its reservation and did not
qualify as learning evidence.

| Scenario | Policy | Task | Grade | Accounting | Learning | Dispatches |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: |
| success | B0 | D01 | pass | settled | yes | 1 |
| worker_failure | B1 | D03 | fail | settled | yes | 1 |
| timeout | B2 | D05 | fail | uncertain | no | 1 |
| cancellation | B0 | D07 | fail | settled | no | 1 |
| interruption_resume | B1 | D11 | pass | settled | yes | 1 |
| identity_mismatch | B2 | D09 | pass | settled | no | 1 |
| missing_usage | B0 | D08 | pass | uncertain | no | 1 |
| grader_failure | B1 | D10 | blocked | settled | no | 1 |
| wrong_solution | B2 | D03 | fail | settled | yes | 1 |

## Reconciliation

- Known fake spend: USD 1.40.
- Retained unresolved allowance: USD 8.00.
- Episodes with unknown cost: 2.
- Double-counted cost: USD 0.00.

## Replay

- Deterministic state: true.
- Valid event chains: true.
- One dispatch per episode: true.

## Limits

- Fake workers prove control flow and accounting, not Claude behaviour.
- The recorded WSL2 access-control mechanism is required but a live model episode has not exercised it.
- Unknown terminal usage retains its full unused allowance and is ineligible for learning.
