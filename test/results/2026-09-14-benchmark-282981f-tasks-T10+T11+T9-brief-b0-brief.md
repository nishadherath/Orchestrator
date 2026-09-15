# Benchmark run, full, 2026-09-14 11:16 at c7200b0

Bundle: 2026-09-14-282981f. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools[Bash(python3 *),Bash(python *)]. Brief: B0_BRIEF.md (sha256 3ae46b0895fd7890) prepended to every handover. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=3, steer threshold=2 of 3 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). R_confirm=9, reporting threshold: 95% Wilson lower bound above 0.7, and the cell below must fail the same bar.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T9

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.4204 | 212.3 |

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
| worker-sonnet-low | 1 | yes | USD 0.4871 | 240.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":22213,"cache_read_input_tokens":111244,"output_tokens":3890,"output_tokens_details":{"thinking_tokens":768},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 2 | yes | USD 0.3819 | 203.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":22256,"cache_read_input_tokens":111205,"output_tokens":3915,"output_tokens_details":{"thinking_tokens":887},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 3 | yes | USD 0.3921 | 192.8 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":2041,"cache_read_input_tokens":97913,"output_tokens":752,"output_tokens_details":{"thinking_tokens":53},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 4 | yes | USD 0.3309 | 179.9 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":2360,"cache_read_input_tokens":98551,"output_tokens":950,"output_tokens_details":{"thinking_tokens":222},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 5 | yes | USD 0.3117 | 155.6 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":2347,"cache_read_input_tokens":98808,"output_tokens":974,"output_tokens_details":{"thinking_tokens":144},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 6 | yes | USD 0.3129 | 152.8 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":2014,"cache_read_input_tokens":98942,"output_tokens":1255,"output_tokens_details":{"thinking_tokens":291},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 7 | yes | USD 0.3471 | 166.2 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":2550,"cache_read_input_tokens":98406,"output_tokens":964,"output_tokens_details":{"thinking_tokens":157},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 8 | yes | USD 0.4173 | 197.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9804,"cache_read_input_tokens":123902,"output_tokens":3889,"output_tokens_details":{"thinking_tokens":735},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 9 | yes | USD 0.3254 | 153.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9191,"cache_read_input_tokens":123667,"output_tokens":3192,"output_tokens_details":{"thinking_tokens":319},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 10 | yes | USD 0.3633 | 200.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9458,"cache_read_input_tokens":123828,"output_tokens":3433,"output_tokens_details":{"thinking_tokens":610},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 11 | yes | USD 0.3463 | 150.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1511,"cache_read_input_tokens":48355,"output_tokens":946,"output_tokens_details":{"thinking_tokens":138},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 12 | yes | USD 0.3182 | 175.3 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10377,"cache_read_input_tokens":124015,"output_tokens":4294,"output_tokens_details":{"thinking_tokens":645},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |

## Task T10

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.3901 | 199.5 |

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
| worker-sonnet-low | 1 | yes | USD 0.3955 | 190.3 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1887,"cache_read_input_tokens":48382,"output_tokens":1164,"output_tokens_details":{"thinking_tokens":180},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 2 | yes | USD 0.3846 | 204.2 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1808,"cache_read_input_tokens":48136,"output_tokens":1178,"output_tokens_details":{"thinking_tokens":177},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 3 | yes | USD 0.3901 | 203.9 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":2074,"cache_read_input_tokens":48645,"output_tokens":1747,"output_tokens_details":{"thinking_tokens":361},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 4 | yes | USD 0.3200 | 153.6 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1660,"cache_read_input_tokens":48402,"output_tokens":994,"output_tokens_details":{"thinking_tokens":124},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 5 | yes | USD 0.3727 | 198.5 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1753,"cache_read_input_tokens":48642,"output_tokens":1438,"output_tokens_details":{"thinking_tokens":337},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 6 | yes | USD 0.3882 | 188.0 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9635,"cache_read_input_tokens":123595,"output_tokens":3469,"output_tokens_details":{"thinking_tokens":327},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 7 | yes | USD 0.3261 | 150.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10036,"cache_read_input_tokens":123480,"output_tokens":3912,"output_tokens_details":{"thinking_tokens":544},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 8 | no | USD 0.3781 | 193.2 | grader: FAIL: normalise('  alice@example.com ') returned '  alice@example.com ', wanted 'alice@example.com'; normalise('\tAlice@Example.COM\n') returned '\talice@example.com\n', wanted 'alice@example.com' || worker: # Report  ## Answer  Changed `accounts.py` only. It now patches `legacy_ids.normalise` at import time (`legacy_ids.normalise = wrapper`) so the function also folds surrounding whitespace, for every ca | {"usage":{"input_tokens":8,"cache_creation_input_tokens":11199,"cache_read_input_tokens":172669,"output_tokens":4022,"output_tokens_details":{"thinking_tokens":647},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 9 | yes | USD 0.4150 | 166.7 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1866,"cache_read_input_tokens":48244,"output_tokens":1276,"output_tokens_details":{"thinking_tokens":96},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 10 | yes | USD 0.3429 | 152.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9789,"cache_read_input_tokens":123507,"output_tokens":3508,"output_tokens_details":{"thinking_tokens":357},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 11 | yes | USD 0.3324 | 178.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10282,"cache_read_input_tokens":123623,"output_tokens":4239,"output_tokens_details":{"thinking_tokens":1069},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tok |
| worker-sonnet-low | 12 | yes | USD 0.3339 | 194.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10860,"cache_read_input_tokens":123557,"output_tokens":4851,"output_tokens_details":{"thinking_tokens":1288},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tok |

## Task T11

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.3926 | 175.7 |

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
| worker-sonnet-low | 1 | yes | USD 0.3856 | 168.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":22920,"cache_read_input_tokens":111070,"output_tokens":4219,"output_tokens_details":{"thinking_tokens":437},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 2 | yes | USD 0.3972 | 155.8 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":1824,"cache_read_input_tokens":48061,"output_tokens":1209,"output_tokens_details":{"thinking_tokens":156},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 3 | yes | USD 0.3949 | 203.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10573,"cache_read_input_tokens":123633,"output_tokens":4583,"output_tokens_details":{"thinking_tokens":431},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 4 | yes | USD 0.3281 | 194.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9723,"cache_read_input_tokens":123684,"output_tokens":3529,"output_tokens_details":{"thinking_tokens":465},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 5 | yes | USD 0.3387 | 184.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":11598,"cache_read_input_tokens":124547,"output_tokens":5439,"output_tokens_details":{"thinking_tokens":1463},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tok |
| worker-sonnet-low | 6 | yes | USD 0.3305 | 194.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10039,"cache_read_input_tokens":123536,"output_tokens":3878,"output_tokens_details":{"thinking_tokens":460},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 7 | yes | USD 0.3348 | 180.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10694,"cache_read_input_tokens":123555,"output_tokens":4535,"output_tokens_details":{"thinking_tokens":616},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 8 | yes | USD 0.2779 | 158.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10198,"cache_read_input_tokens":123579,"output_tokens":4166,"output_tokens_details":{"thinking_tokens":598},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 9 | yes | USD 0.3072 | 147.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10371,"cache_read_input_tokens":123542,"output_tokens":4635,"output_tokens_details":{"thinking_tokens":926},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 10 | yes | USD 0.3516 | 222.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9760,"cache_read_input_tokens":123562,"output_tokens":3564,"output_tokens_details":{"thinking_tokens":364},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 11 | yes | USD 0.4288 | 213.0 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":2064,"cache_read_input_tokens":48652,"output_tokens":1383,"output_tokens_details":{"thinking_tokens":84},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 12 | yes | USD 0.3429 | 186.0 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10707,"cache_read_input_tokens":123859,"output_tokens":4848,"output_tokens_details":{"thinking_tokens":1199},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tok |

