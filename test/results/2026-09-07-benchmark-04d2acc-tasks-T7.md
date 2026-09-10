# Benchmark run, full, 2026-09-07 15:47 at 59babc4

Bundle: 2026-09-06-04d2acc. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=3, steer threshold=2 of 3 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). R_confirm=9, reporting threshold: 95% Wilson lower bound above 0.7, and the cell below must fail the same bar.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T7

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.2640 | 74.6 |

Candidate frontier: `worker-sonnet-low`.

### Confirmation (reporting threshold)

| Cell | Passes | Runs | Rate | 95% Wilson interval | Clears 0.7 lower bound |
| :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 9 | 9 | 100% | [70.1%, 100.0%] | yes |

`worker-sonnet-low` is the cheapest cell on the ladder; there is no cell below to confirm exclusivity against.

Frontier confirmed: yes.

### Per-run detail

| Cell | Run | Pass | Cost | Wall-clock (s) | Notes | Extras (raw) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 1 | yes | USD 0.3192 | 86.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":22627,"cache_read_input_tokens":104023,"output_tokens":2128,"output_tokens_details":{"thinking_tokens":150},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 2 | yes | USD 0.2252 | 53.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1919,"cache_read_input_tokens":45444,"output_tokens":1338,"output_tokens_details":{"thinking_tokens":34},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 3 | yes | USD 0.2477 | 84.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":18432,"cache_read_input_tokens":101902,"output_tokens":2062,"output_tokens_details":{"thinking_tokens":235},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 4 | yes | USD 0.6585 | 127.8 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":2386,"cache_read_input_tokens":48696,"output_tokens":2558,"output_tokens_details":{"thinking_tokens":723},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 5 | yes | USD 0.4857 | 124.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":2387,"cache_read_input_tokens":40180,"output_tokens":2446,"output_tokens_details":{"thinking_tokens":670},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 6 | yes | USD 0.2174 | 68.8 |  | {"usage":{"input_tokens":8,"cache_creation_input_tokens":10913,"cache_read_input_tokens":155678,"output_tokens":1820,"output_tokens_details":{"thinking_tokens":150},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 7 | yes | USD 0.2277 | 65.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":11222,"cache_read_input_tokens":115599,"output_tokens":2262,"output_tokens_details":{"thinking_tokens":308},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 8 | yes | USD 0.1562 | 62.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":2227,"cache_read_input_tokens":124513,"output_tokens":2150,"output_tokens_details":{"thinking_tokens":374},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 9 | yes | USD 0.1681 | 75.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":1982,"cache_read_input_tokens":124513,"output_tokens":1968,"output_tokens_details":{"thinking_tokens":170},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 10 | yes | USD 0.2328 | 79.0 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":11099,"cache_read_input_tokens":115565,"output_tokens":2094,"output_tokens_details":{"thinking_tokens":208},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 11 | yes | USD 0.2458 | 91.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":11740,"cache_read_input_tokens":105657,"output_tokens":1724,"output_tokens_details":{"thinking_tokens":195},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 12 | yes | USD 0.1824 | 78.1 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":6242,"cache_read_input_tokens":71078,"output_tokens":2003,"output_tokens_details":{"thinking_tokens":452},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |

