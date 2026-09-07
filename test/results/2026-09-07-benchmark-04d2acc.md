# Benchmark run, full, 2026-09-07 15:14 at bde72dd

Bundle: 2026-09-06-04d2acc. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=3, steer threshold=2 of 3 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). R_confirm=9, reporting threshold: 95% Wilson lower bound above 0.7, and the cell below must fail the same bar.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T7

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.2194 | 67.3 |

Candidate frontier: `worker-sonnet-low`.

### Confirmation (reporting threshold)

| Cell | Passes | Runs | Rate | 95% Wilson interval | Clears 0.7 lower bound |
| :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 8 | 9 | 89% | [56.5%, 98.0%] | no |

`worker-sonnet-low` is the cheapest cell on the ladder; there is no cell below to confirm exclusivity against.

Frontier confirmed: no.

### Per-run detail

| Cell | Run | Pass | Cost | Wall-clock (s) | Notes | Extras (raw) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 1 | yes | USD 0.3121 | 81.9 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":17610,"cache_read_input_tokens":59537,"output_tokens":1826,"output_tokens_details":{"thinking_tokens":46},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 2 | yes | USD 0.1080 | 54.2 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5624,"cache_read_input_tokens":71080,"output_tokens":1380,"output_tokens_details":{"thinking_tokens":16},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 3 | yes | USD 0.2381 | 65.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10585,"cache_read_input_tokens":115617,"output_tokens":1627,"output_tokens_details":{"thinking_tokens":152},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 4 | yes | USD 0.2771 | 89.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":2030,"cache_read_input_tokens":45655,"output_tokens":1446,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 5 | yes | USD 0.1329 | 49.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10459,"cache_read_input_tokens":115571,"output_tokens":1496,"output_tokens_details":{"thinking_tokens":205},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 6 | yes | USD 0.1900 | 74.0 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5863,"cache_read_input_tokens":71080,"output_tokens":1623,"output_tokens_details":{"thinking_tokens":16},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 7 | no | USD 0.5804 | 118.9 | grader: FAIL: report does not name shared/serialize.py || worker: The `worker-opus-high` task (the misrouted worker from before) has finished and returned a full diagnosis. However, I still haven't received your decision on how to handle the subagent_type mismatch I | {"usage":{"input_tokens":2,"cache_creation_input_tokens":3205,"cache_read_input_tokens":45818,"output_tokens":392,"output_tokens_details":{"thinking_tokens":205},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 8 | yes | USD 0.1726 | 71.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":1838,"cache_read_input_tokens":124516,"output_tokens":1762,"output_tokens_details":{"thinking_tokens":159},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 9 | yes | USD 0.1423 | 42.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10541,"cache_read_input_tokens":115608,"output_tokens":1557,"output_tokens_details":{"thinking_tokens":239},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 10 | yes | USD 0.1476 | 47.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9391,"cache_read_input_tokens":114228,"output_tokens":1861,"output_tokens_details":{"thinking_tokens":270},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 11 | yes | USD 0.1564 | 66.1 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5654,"cache_read_input_tokens":71080,"output_tokens":1421,"output_tokens_details":{"thinking_tokens":16},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 12 | yes | USD 0.2080 | 89.2 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5859,"cache_read_input_tokens":71080,"output_tokens":1648,"output_tokens_details":{"thinking_tokens":41},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |

