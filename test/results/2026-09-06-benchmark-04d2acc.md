# Benchmark run, full, 2026-09-06 21:19 at dd65886

Bundle: 2026-09-06-04d2acc. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=1, steer threshold=1 of 1 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). No confirmation phase.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T1

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 0 | 1 | 0% | no | not reported | n/a |
| worker-sonnet-medium | 0 | 1 | 0% | no | not reported | n/a |
| worker-sonnet-high | 0 | 1 | 0% | no | not reported | n/a |
| worker-sonnet-xhigh | 0 | 1 | 0% | no | not reported | n/a |
| worker-opus-high | 0 | 1 | 0% | no | not reported | n/a |
| worker-opus-xhigh | 0 | 1 | 0% | no | not reported | n/a |
| worker-fable-xhigh | 0 | 1 | 0% | no | not reported | n/a |

No cell cleared the steering threshold; ladder exhausted.

### Per-run detail

| Cell | Run | Pass | Cost | Wall-clock (s) | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 1 | no | not reported |  | claude exited 1:  |
| worker-sonnet-medium | 1 | no | not reported |  | claude exited 1:  |
| worker-sonnet-high | 1 | no | not reported |  | claude exited 1:  |
| worker-sonnet-xhigh | 1 | no | not reported |  | claude exited 1:  |
| worker-opus-high | 1 | no | not reported |  | claude exited 1:  |
| worker-opus-xhigh | 1 | no | not reported |  | claude exited 1:  |
| worker-fable-xhigh | 1 | no | not reported |  | claude exited 1:  |

