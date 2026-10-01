# Live episode integration offline qualification

Result: **PASS**. Mode: `offline-scripted-adapters-v1`. Model calls: **0**.

| Check | Result |
| :--- | :--- |
| b0 repairs once at floor | pass |
| b1 uses frozen ladder | pass |
| b2 requires two distinct failures | pass |
| dispatch recovery never redispatches | pass |
| missing cost retains allowance | pass |
| event chains valid | pass |
| hidden grade after policy stop | pass |
| controller metadata reaches routing ledger | pass |
| policy boundary excludes forbidden inputs | pass |

## Limits

- Scripted adapters qualify policy ordering, external grading and recovery without model calls.
- The live worker adapter is separately calibrated and qualified.
- The live Controller adapter is qualified separately with injected provider-free accounting.
