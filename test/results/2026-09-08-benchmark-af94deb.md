# Benchmark run, full, 2026-09-08 08:12 at 9393ab9

Bundle: 2026-09-07-af94deb. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=3, steer threshold=2 of 3 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). R_confirm=9, reporting threshold: 95% Wilson lower bound above 0.7, and the cell below must fail the same bar.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T8

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 2 | 3 | 67% | yes | USD 0.1727 | 44.4 |

Candidate frontier: `worker-sonnet-low`.

### Confirmation (reporting threshold)

| Cell | Passes | Runs | Rate | 95% Wilson interval | Clears 0.7 lower bound |
| :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 7 | 9 | 78% | [45.3%, 93.7%] | no |

`worker-sonnet-low` is the cheapest cell on the ladder; there is no cell below to confirm exclusivity against.

Frontier confirmed: no.

### Per-run detail

| Cell | Run | Pass | Cost | Wall-clock (s) | Notes | Extras (raw) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 1 | yes | USD 0.2040 | 43.3 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":17135,"cache_read_input_tokens":59545,"output_tokens":1345,"output_tokens_details":{"thinking_tokens":36},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 2 | no | USD 0.1160 | 51.9 | grader: FAIL: report does not name api_client.py || worker: The key correctness risk is that `create_order` is now wrapped in the same blanket retry policy as the read-only calls, but it is not actually safe to retry.  **Not idempotent â€” risk of duplicate or | {"usage":{"input_tokens":4,"cache_creation_input_tokens":12325,"cache_read_input_tokens":61412,"output_tokens":1058,"output_tokens_details":{"thinking_tokens":35},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 3 | yes | USD 0.1980 | 38.1 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1367,"cache_read_input_tokens":45102,"output_tokens":806,"output_tokens_details":{"thinking_tokens":15},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 4 | yes | USD 0.1362 | 55.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":11217,"cache_read_input_tokens":116065,"output_tokens":2153,"output_tokens_details":{"thinking_tokens":747},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 5 | yes | USD 0.1121 | 38.3 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5427,"cache_read_input_tokens":71096,"output_tokens":1191,"output_tokens_details":{"thinking_tokens":16},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 6 | yes | USD 0.1426 | 53.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":13015,"cache_read_input_tokens":110741,"output_tokens":1937,"output_tokens_details":{"thinking_tokens":251},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 7 | yes | USD 0.1561 | 45.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":12888,"cache_read_input_tokens":110790,"output_tokens":1814,"output_tokens_details":{"thinking_tokens":423},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 8 | no | USD 0.0989 | 38.3 | grader: FAIL: report does not name api_client.py || worker: The core correctness risk: **`create_order` is retried, but POST /orders is not idempotent.**  `with_retries` retries on any exception, including a `RuntimeError` raised for a 5xx status, and also on  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5811,"cache_read_input_tokens":71096,"output_tokens":1571,"output_tokens_details":{"thinking_tokens":356},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 9 | no | USD 0.1116 | 38.9 | grader: FAIL: report does not name api_client.py || worker: The core correctness risk: **`create_order` is retried even though POST is not idempotent.**  `with_retries` retries on *any* exception, and `_retrying` wraps `create_order`'s POST call the same as th | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5492,"cache_read_input_tokens":71096,"output_tokens":1261,"output_tokens_details":{"thinking_tokens":55},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 10 | yes | USD 0.0893 | 99.9 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5252,"cache_read_input_tokens":71096,"output_tokens":1018,"output_tokens_details":{"thinking_tokens":16},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 11 | yes | USD 0.0869 | 46.1 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5482,"cache_read_input_tokens":71096,"output_tokens":1247,"output_tokens_details":{"thinking_tokens":17},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 12 | yes | USD 0.1291 | 41.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":13095,"cache_read_input_tokens":107028,"output_tokens":1600,"output_tokens_details":{"thinking_tokens":178},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |

