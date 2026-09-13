# Benchmark run, full, 2026-09-13 22:41 at 1b5b20b

Bundle: 2026-09-07-af94deb. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools[Bash(python3 *),Bash(python *)]. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=3, steer threshold=2 of 3 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). R_confirm=9, reporting threshold: 95% Wilson lower bound above 0.7, and the cell below must fail the same bar.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T9

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.2162 | 73.7 |

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
| worker-sonnet-low | 1 | yes | USD 0.2940 | 89.3 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":18459,"cache_read_input_tokens":101089,"output_tokens":1091,"output_tokens_details":{"thinking_tokens":168},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 2 | yes | USD 0.1909 | 59.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":16947,"cache_read_input_tokens":106347,"output_tokens":847,"output_tokens_details":{"thinking_tokens":202},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 3 | yes | USD 0.1638 | 72.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6826,"cache_read_input_tokens":116696,"output_tokens":1047,"output_tokens_details":{"thinking_tokens":224},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 4 | yes | USD 0.1649 | 75.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6858,"cache_read_input_tokens":116670,"output_tokens":1071,"output_tokens_details":{"thinking_tokens":294},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 5 | yes | USD 0.2311 | 116.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6852,"cache_read_input_tokens":116698,"output_tokens":1063,"output_tokens_details":{"thinking_tokens":255},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 6 | yes | USD 0.1838 | 110.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6659,"cache_read_input_tokens":116695,"output_tokens":883,"output_tokens_details":{"thinking_tokens":124},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 7 | yes | USD 0.1875 | 93.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":7007,"cache_read_input_tokens":116753,"output_tokens":1221,"output_tokens_details":{"thinking_tokens":430},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 8 | yes | USD 0.1514 | 77.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6886,"cache_read_input_tokens":116735,"output_tokens":1109,"output_tokens_details":{"thinking_tokens":378},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 9 | yes | USD 0.2171 | 122.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6922,"cache_read_input_tokens":116721,"output_tokens":1146,"output_tokens_details":{"thinking_tokens":352},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 10 | yes | USD 0.2012 | 70.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6735,"cache_read_input_tokens":116656,"output_tokens":954,"output_tokens_details":{"thinking_tokens":296},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 11 | yes | USD 0.2600 | 98.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1070,"cache_read_input_tokens":43888,"output_tokens":461,"output_tokens_details":{"thinking_tokens":45},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 12 | yes | USD 0.1440 | 66.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":6896,"cache_read_input_tokens":116708,"output_tokens":1114,"output_tokens_details":{"thinking_tokens":300},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |

