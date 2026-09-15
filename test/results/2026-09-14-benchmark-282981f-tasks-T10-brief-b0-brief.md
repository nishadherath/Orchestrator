# Benchmark run, full, 2026-09-14 12:08 at f172c52

Bundle: 2026-09-14-282981f. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools[Bash(python3 *),Bash(python *)]. Brief: B0_BRIEF.md (sha256 3ae46b0895fd7890) prepended to every handover. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=3, steer threshold=2 of 3 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). R_confirm=9, reporting threshold: 95% Wilson lower bound above 0.7, and the cell below must fail the same bar.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T10

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.3632 | 165.8 |

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
| worker-sonnet-low | 1 | yes | USD 0.3493 | 159.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9998,"cache_read_input_tokens":123513,"output_tokens":4866,"output_tokens_details":{"thinking_tokens":1528},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 2 | yes | USD 0.3606 | 159.3 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":2006,"cache_read_input_tokens":48346,"output_tokens":1672,"output_tokens_details":{"thinking_tokens":316},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 3 | yes | USD 0.3796 | 178.2 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1578,"cache_read_input_tokens":48187,"output_tokens":731,"output_tokens_details":{"thinking_tokens":96},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 4 | yes | USD 0.3573 | 189.2 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1757,"cache_read_input_tokens":48217,"output_tokens":1236,"output_tokens_details":{"thinking_tokens":182},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 5 | yes | USD 0.4523 | 161.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10375,"cache_read_input_tokens":123491,"output_tokens":3921,"output_tokens_details":{"thinking_tokens":431},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 6 | yes | USD 0.3476 | 157.0 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10260,"cache_read_input_tokens":123562,"output_tokens":3954,"output_tokens_details":{"thinking_tokens":714},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 7 | no | USD 0.4084 | 214.3 | grader: FAIL: normalise('  alice@example.com ') returned '  alice@example.com ', wanted 'alice@example.com'; normalise('\tAlice@Example.COM\n') returned '\talice@example.com\n', wanted 'alice@example.com' || worker: Task complete. Summary:  **File changed:** `bench-T10/accounts.py` only. `legacy_ids.py` was not modified (verified: 0 bytes changed).  **Why:** `test_accounts.py`'s `test_normalise_folds_surrounding_ | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9862,"cache_read_input_tokens":123648,"output_tokens":3863,"output_tokens_details":{"thinking_tokens":442},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 8 | yes | USD 0.3911 | 160.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1925,"cache_read_input_tokens":48424,"output_tokens":1395,"output_tokens_details":{"thinking_tokens":172},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 9 | yes | USD 0.4022 | 192.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1440,"cache_read_input_tokens":48749,"output_tokens":1028,"output_tokens_details":{"thinking_tokens":259},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 10 | yes | USD 0.3599 | 157.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9536,"cache_read_input_tokens":123512,"output_tokens":3616,"output_tokens_details":{"thinking_tokens":520},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 11 | yes | USD 0.3982 | 196.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10371,"cache_read_input_tokens":123546,"output_tokens":4621,"output_tokens_details":{"thinking_tokens":979},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 12 | yes | USD 0.4122 | 172.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10171,"cache_read_input_tokens":123399,"output_tokens":4270,"output_tokens_details":{"thinking_tokens":874},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |

