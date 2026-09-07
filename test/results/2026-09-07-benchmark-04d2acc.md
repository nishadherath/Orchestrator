# Benchmark run, full, 2026-09-07 14:29 at a219d55

Bundle: 2026-09-06-04d2acc. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Forwarder model: sonnet. Permission mode: acceptEdits+allowedTools. Ladder: worker-sonnet-low -> worker-sonnet-medium -> worker-sonnet-high -> worker-sonnet-xhigh -> worker-opus-high -> worker-opus-xhigh -> worker-fable-xhigh.

R_search=3, steer threshold=2 of 3 (permissive; ceil(0.667 x n); never cited as evidence, docs/BENCHMARK-DESIGN.md). R_confirm=9, reporting threshold: 95% Wilson lower bound above 0.7, and the cell below must fail the same bar.

Cost figures assume a spawned worker's cost rolls up into the forwarder's reported `total_cost_usd`; this is unverified (docs/FINDINGS.md), and the pilot is partly how it gets checked.

## Task T1

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.1857 | 36.4 |

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
| worker-sonnet-low | 1 | yes | USD 0.2318 | 37.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":21028,"cache_read_input_tokens":99378,"output_tokens":796,"output_tokens_details":{"thinking_tokens":206},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 2 | yes | USD 0.1279 | 28.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9606,"cache_read_input_tokens":114742,"output_tokens":647,"output_tokens_details":{"thinking_tokens":97},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 3 | yes | USD 0.1973 | 43.6 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":742,"cache_read_input_tokens":45062,"output_tokens":183,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":74 |
| worker-sonnet-low | 4 | yes | USD 0.1666 | 33.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9837,"cache_read_input_tokens":114833,"output_tokens":876,"output_tokens_details":{"thinking_tokens":266},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 5 | yes | USD 0.1527 | 51.3 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9757,"cache_read_input_tokens":114749,"output_tokens":794,"output_tokens_details":{"thinking_tokens":197},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 6 | yes | USD 0.1651 | 35.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9687,"cache_read_input_tokens":114749,"output_tokens":725,"output_tokens_details":{"thinking_tokens":98},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 7 | yes | USD 0.1644 | 33.5 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":707,"cache_read_input_tokens":45040,"output_tokens":142,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":70 |
| worker-sonnet-low | 8 | yes | USD 0.1497 | 48.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9686,"cache_read_input_tokens":114737,"output_tokens":726,"output_tokens_details":{"thinking_tokens":82},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 9 | yes | USD 0.2087 | 49.8 |  | {"usage":{"input_tokens":8,"cache_creation_input_tokens":10136,"cache_read_input_tokens":154487,"output_tokens":1120,"output_tokens_details":{"thinking_tokens":191},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 10 | yes | USD 0.1842 | 40.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":17053,"cache_read_input_tokens":101040,"output_tokens":618,"output_tokens_details":{"thinking_tokens":37},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 11 | yes | USD 0.1595 | 38.3 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":687,"cache_read_input_tokens":45097,"output_tokens":126,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":68 |
| worker-sonnet-low | 12 | yes | USD 0.1063 | 31.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9634,"cache_read_input_tokens":114741,"output_tokens":673,"output_tokens_details":{"thinking_tokens":115},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |

## Task T2

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.1779 | 43.2 |

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
| worker-sonnet-low | 1 | yes | USD 0.2123 | 35.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":20876,"cache_read_input_tokens":103118,"output_tokens":823,"output_tokens_details":{"thinking_tokens":197},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 2 | yes | USD 0.1733 | 54.0 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9806,"cache_read_input_tokens":114210,"output_tokens":843,"output_tokens_details":{"thinking_tokens":88},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 3 | yes | USD 0.1481 | 39.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9918,"cache_read_input_tokens":114212,"output_tokens":959,"output_tokens_details":{"thinking_tokens":334},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 4 | yes | USD 0.1059 | 35.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":814,"cache_read_input_tokens":123160,"output_tokens":803,"output_tokens_details":{"thinking_tokens":86},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 5 | yes | USD 0.0964 | 32.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":1012,"cache_read_input_tokens":123160,"output_tokens":1037,"output_tokens_details":{"thinking_tokens":244},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 6 | yes | USD 0.1529 | 37.2 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9726,"cache_read_input_tokens":114210,"output_tokens":818,"output_tokens_details":{"thinking_tokens":81},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 7 | yes | USD 0.1257 | 43.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":959,"cache_read_input_tokens":123160,"output_tokens":984,"output_tokens_details":{"thinking_tokens":199},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 8 | yes | USD 0.5788 | 119.2 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":902,"cache_read_input_tokens":45020,"output_tokens":347,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":90 |
| worker-sonnet-low | 9 | yes | USD 0.1749 | 43.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":12193,"cache_read_input_tokens":105545,"output_tokens":794,"output_tokens_details":{"thinking_tokens":135},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 10 | yes | USD 0.2889 | 102.0 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":846,"cache_read_input_tokens":45002,"output_tokens":248,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":84 |
| worker-sonnet-low | 11 | yes | USD 0.2511 | 107.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":917,"cache_read_input_tokens":123160,"output_tokens":902,"output_tokens_details":{"thinking_tokens":188},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 12 | yes | USD 0.2039 | 63.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":12329,"cache_read_input_tokens":105545,"output_tokens":930,"output_tokens_details":{"thinking_tokens":213},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |

## Task T3

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.1426 | 35.5 |

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
| worker-sonnet-low | 1 | yes | USD 0.1569 | 29.2 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":16799,"cache_read_input_tokens":59751,"output_tokens":805,"output_tokens_details":{"thinking_tokens":29},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 2 | yes | USD 0.1549 | 36.6 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":796,"cache_read_input_tokens":45883,"output_tokens":227,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":79 |
| worker-sonnet-low | 3 | yes | USD 0.1162 | 40.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10004,"cache_read_input_tokens":116227,"output_tokens":1047,"output_tokens_details":{"thinking_tokens":203},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 4 | yes | USD 0.1582 | 40.6 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":760,"cache_read_input_tokens":46227,"output_tokens":200,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":76 |
| worker-sonnet-low | 5 | yes | USD 0.1060 | 34.2 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5091,"cache_read_input_tokens":71508,"output_tokens":848,"output_tokens_details":{"thinking_tokens":37},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 6 | yes | USD 0.1314 | 36.4 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":726,"cache_read_input_tokens":45913,"output_tokens":170,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":72 |
| worker-sonnet-low | 7 | yes | USD 0.0934 | 28.0 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5025,"cache_read_input_tokens":71508,"output_tokens":785,"output_tokens_details":{"thinking_tokens":30},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 8 | yes | USD 0.1282 | 35.7 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":748,"cache_read_input_tokens":45937,"output_tokens":181,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":74 |
| worker-sonnet-low | 9 | yes | USD 0.1325 | 44.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":11106,"cache_read_input_tokens":116216,"output_tokens":2146,"output_tokens_details":{"thinking_tokens":1127},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tok |
| worker-sonnet-low | 10 | yes | USD 0.1208 | 35.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10076,"cache_read_input_tokens":116208,"output_tokens":1120,"output_tokens_details":{"thinking_tokens":153},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 11 | yes | USD 0.1054 | 32.7 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":776,"cache_read_input_tokens":40930,"output_tokens":215,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":77 |
| worker-sonnet-low | 12 | yes | USD 0.1504 | 32.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":17936,"cache_read_input_tokens":102313,"output_tokens":1239,"output_tokens_details":{"thinking_tokens":360},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |

## Task T4

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.2097 | 48.8 |

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
| worker-sonnet-low | 1 | yes | USD 0.2261 | 43.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":22138,"cache_read_input_tokens":104533,"output_tokens":1381,"output_tokens_details":{"thinking_tokens":206},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 2 | yes | USD 0.2014 | 52.0 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":851,"cache_read_input_tokens":46286,"output_tokens":285,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":85 |
| worker-sonnet-low | 3 | yes | USD 0.2018 | 50.3 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":865,"cache_read_input_tokens":46109,"output_tokens":292,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":86 |
| worker-sonnet-low | 4 | yes | USD 0.1771 | 49.3 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10365,"cache_read_input_tokens":116333,"output_tokens":1408,"output_tokens_details":{"thinking_tokens":276},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 5 | yes | USD 0.1615 | 48.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10263,"cache_read_input_tokens":116436,"output_tokens":1299,"output_tokens_details":{"thinking_tokens":216},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 6 | yes | USD 0.1401 | 54.7 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5385,"cache_read_input_tokens":71590,"output_tokens":1148,"output_tokens_details":{"thinking_tokens":185},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 7 | yes | USD 0.2061 | 52.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10549,"cache_read_input_tokens":116381,"output_tokens":1589,"output_tokens_details":{"thinking_tokens":494},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 8 | yes | USD 0.1089 | 46.0 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":5299,"cache_read_input_tokens":71590,"output_tokens":1061,"output_tokens_details":{"thinking_tokens":49},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 9 | yes | USD 0.1320 | 40.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":1306,"cache_read_input_tokens":125281,"output_tokens":1296,"output_tokens_details":{"thinking_tokens":205},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 10 | yes | USD 0.1807 | 41.3 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10160,"cache_read_input_tokens":116329,"output_tokens":1197,"output_tokens_details":{"thinking_tokens":152},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 11 | yes | USD 0.1367 | 43.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":1331,"cache_read_input_tokens":125281,"output_tokens":1316,"output_tokens_details":{"thinking_tokens":165},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 12 | yes | USD 0.2658 | 53.1 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":18025,"cache_read_input_tokens":102246,"output_tokens":1211,"output_tokens_details":{"thinking_tokens":100},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |

## Task T5

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.1783 | 27.0 |

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
| worker-sonnet-low | 1 | yes | USD 0.1710 | 33.5 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":21308,"cache_read_input_tokens":104001,"output_tokens":820,"output_tokens_details":{"thinking_tokens":201},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 2 | yes | USD 0.2678 | 26.7 |  | {"usage":{"input_tokens":2,"cache_creation_input_tokens":738,"cache_read_input_tokens":45118,"output_tokens":179,"output_tokens_details":{"thinking_tokens":0},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":73 |
| worker-sonnet-low | 3 | yes | USD 0.0961 | 20.7 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":6702,"cache_read_input_tokens":66388,"output_tokens":449,"output_tokens_details":{"thinking_tokens":17},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 4 | yes | USD 0.1249 | 26.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9758,"cache_read_input_tokens":115535,"output_tokens":793,"output_tokens_details":{"thinking_tokens":201},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 5 | yes | USD 0.0711 | 28.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":899,"cache_read_input_tokens":124479,"output_tokens":882,"output_tokens_details":{"thinking_tokens":283},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 6 | yes | USD 0.1045 | 39.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9882,"cache_read_input_tokens":115587,"output_tokens":920,"output_tokens_details":{"thinking_tokens":278},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 7 | yes | USD 0.1016 | 35.0 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9649,"cache_read_input_tokens":115535,"output_tokens":748,"output_tokens_details":{"thinking_tokens":166},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 8 | yes | USD 0.0872 | 29.0 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":767,"cache_read_input_tokens":124479,"output_tokens":750,"output_tokens_details":{"thinking_tokens":149},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 9 | yes | USD 0.0730 | 30.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":1093,"cache_read_input_tokens":124483,"output_tokens":1082,"output_tokens_details":{"thinking_tokens":557},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 10 | yes | USD 0.1099 | 25.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":12170,"cache_read_input_tokens":106868,"output_tokens":774,"output_tokens_details":{"thinking_tokens":208},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 11 | yes | USD 0.0674 | 21.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":657,"cache_read_input_tokens":124483,"output_tokens":641,"output_tokens_details":{"thinking_tokens":87},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 12 | yes | USD 0.0694 | 23.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":842,"cache_read_input_tokens":124479,"output_tokens":868,"output_tokens_details":{"thinking_tokens":170},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |

## Task T6

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met | Mean cost | Mean wall-clock (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes | USD 0.1268 | 29.7 |

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
| worker-sonnet-low | 1 | yes | USD 0.1718 | 31.9 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":21257,"cache_read_input_tokens":103997,"output_tokens":765,"output_tokens_details":{"thinking_tokens":181},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 2 | yes | USD 0.0791 | 26.8 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":4698,"cache_read_input_tokens":71056,"output_tokens":464,"output_tokens_details":{"thinking_tokens":16},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 3 | yes | USD 0.1294 | 30.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":10101,"cache_read_input_tokens":115787,"output_tokens":1142,"output_tokens_details":{"thinking_tokens":481},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_toke |
| worker-sonnet-low | 4 | yes | USD 0.1054 | 28.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9737,"cache_read_input_tokens":115530,"output_tokens":774,"output_tokens_details":{"thinking_tokens":182},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 5 | yes | USD 0.0726 | 21.2 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":4756,"cache_read_input_tokens":71056,"output_tokens":518,"output_tokens_details":{"thinking_tokens":23},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |
| worker-sonnet-low | 6 | yes | USD 0.1077 | 29.3 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9868,"cache_read_input_tokens":115532,"output_tokens":951,"output_tokens_details":{"thinking_tokens":214},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens |
| worker-sonnet-low | 7 | yes | USD 0.1317 | 26.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":17152,"cache_read_input_tokens":101887,"output_tokens":783,"output_tokens_details":{"thinking_tokens":164},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 8 | yes | USD 0.0735 | 28.6 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":897,"cache_read_input_tokens":124476,"output_tokens":946,"output_tokens_details":{"thinking_tokens":210},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 9 | yes | USD 0.0972 | 26.7 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":767,"cache_read_input_tokens":124480,"output_tokens":750,"output_tokens_details":{"thinking_tokens":140},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 10 | yes | USD 0.0935 | 36.8 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":969,"cache_read_input_tokens":124476,"output_tokens":955,"output_tokens_details":{"thinking_tokens":221},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens" |
| worker-sonnet-low | 11 | yes | USD 0.1092 | 43.4 |  | {"usage":{"input_tokens":6,"cache_creation_input_tokens":9988,"cache_read_input_tokens":115537,"output_tokens":1026,"output_tokens_details":{"thinking_tokens":391},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_token |
| worker-sonnet-low | 12 | yes | USD 0.0704 | 19.0 |  | {"usage":{"input_tokens":4,"cache_creation_input_tokens":4649,"cache_read_input_tokens":71056,"output_tokens":404,"output_tokens_details":{"thinking_tokens":16},"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens": |

