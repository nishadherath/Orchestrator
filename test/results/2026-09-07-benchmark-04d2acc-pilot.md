# Benchmark run, pilot, 2026-09-07 08:18 at c287aa4

Bundle: 2026-09-06-04d2acc. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=5, steer threshold=4 of 5 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). No confirmation phase.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T1

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 5 | 5 | 100% | yes | USD 0.1728 | 36.1 |

Candidate frontier: `worker-sonnet-low`.

### Per-run detail

| Cell | Run | Pass | Cost | Wall-clock (s) | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 1 | yes | USD 0.2333 | 36.9 |  |
| worker-sonnet-low | 2 | yes | USD 0.1754 | 36.6 |  |
| worker-sonnet-low | 3 | yes | USD 0.1986 | 37.8 |  |
| worker-sonnet-low | 4 | yes | USD 0.1175 | 27.5 |  |
| worker-sonnet-low | 5 | yes | USD 0.1390 | 41.8 |  |

## Task T5

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 5 | 5 | 100% | yes | USD 0.1120 | 27.0 |

Candidate frontier: `worker-sonnet-low`.

### Per-run detail

| Cell | Run | Pass | Cost | Wall-clock (s) | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 1 | yes | USD 0.1670 | 30.0 |  |
| worker-sonnet-low | 2 | yes | USD 0.1237 | 31.3 |  |
| worker-sonnet-low | 3 | yes | USD 0.1348 | 25.2 |  |
| worker-sonnet-low | 4 | yes | USD 0.0682 | 22.6 |  |
| worker-sonnet-low | 5 | yes | USD 0.0665 | 25.8 |  |

