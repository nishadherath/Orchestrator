# Cost roll-up check (full), 2026-09-07

Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Model: sonnet. Reps per condition: 2. Per-call timeout: 600s.

SPAWN and DIRECT were run as two separate invocations: SPAWN at 17:36, DIRECT's first attempt at 17:36 (using the not-yet-fixed prompt), DIRECT's second attempt at 17:47 (using the fixed prompt, `--condition direct`). Combined here as the final record.

| Condition | Rep | Prompt | total_cost_usd | num_turns | elapsed_s | Error |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| SPAWN | 1 | as designed | 0.2975875 | 3 | 520.3 |  |
| SPAWN | 2 | as designed | 0.2881648 | 3 | 540.5 |  |
| DIRECT | 1 (first attempt) | missing do-not-spawn preamble | | | 600.0 | timed out after 600s |
| DIRECT | 2 (first attempt) | missing do-not-spawn preamble | 0.057827199999999995 | 1 | 70.3 |  |
| DIRECT | 1 (re-run, fixed) | with DIRECT_PREAMBLE | 0.08540060000000001 | 1 | 104.3 |  |
| DIRECT | 2 (re-run, fixed) | with DIRECT_PREAMBLE | 0.056202 | 1 | 119.6 |  |

SPAWN mean: 0.29287615. DIRECT mean (fixed prompt, the two reps that stand as the final comparison): 0.07080130000000001. Ratio SPAWN/DIRECT: 4.137.

DIRECT's first attempt (before `DIRECT_PREAMBLE` existed) is kept in the table rather than deleted: one clean run at 70.3s and one that never returned inside 600s, on the identical prompt and task, is itself the finding that motivated the fix. Its costs are excluded from the reported DIRECT mean because rep 1 produced none and a mean of one run would not be comparable to SPAWN's two.

Raw usage objects, SPAWN and the fixed DIRECT re-run:

```json
[
  {
    "condition": "SPAWN",
    "rep": 1,
    "usage": {
      "input_tokens": 6,
      "cache_creation_input_tokens": 22239,
      "cache_read_input_tokens": 100219,
      "output_tokens": 5965,
      "output_tokens_details": {
        "thinking_tokens": 582
      },
      "server_tool_use": {
        "web_search_requests": 0,
        "web_fetch_requests": 0
      },
      "service_tier": "standard",
      "cache_creation": {
        "ephemeral_1h_input_tokens": 22239,
        "ephemeral_5m_input_tokens": 0
      },
      "inference_geo": "not_available",
      "iterations": [
        {
          "input_tokens": 2,
          "output_tokens": 5066,
          "cache_read_input_tokens": 38496,
          "cache_creation_input_tokens": 11951,
          "cache_creation": {
            "ephemeral_5m_input_tokens": 0,
            "ephemeral_1h_input_tokens": 11951
          },
          "type": "message"
        }
      ],
      "speed": "standard"
    }
  },
  {
    "condition": "SPAWN",
    "rep": 2,
    "usage": {
      "input_tokens": 8,
      "cache_creation_input_tokens": 22306,
      "cache_read_input_tokens": 153225,
      "output_tokens": 6061,
      "output_tokens_details": {
        "thinking_tokens": 458
      },
      "server_tool_use": {
        "web_search_requests": 0,
        "web_fetch_requests": 0
      },
      "service_tier": "standard",
      "cache_creation": {
        "ephemeral_1h_input_tokens": 22306,
        "ephemeral_5m_input_tokens": 0
      },
      "inference_geo": "not_available",
      "iterations": [
        {
          "input_tokens": 2,
          "output_tokens": 5239,
          "cache_read_input_tokens": 44761,
          "cache_creation_input_tokens": 5753,
          "cache_creation": {
            "ephemeral_5m_input_tokens": 0,
            "ephemeral_1h_input_tokens": 5753
          },
          "type": "message"
        }
      ],
      "speed": "standard"
    }
  },
  {
    "condition": "DIRECT",
    "rep": 1,
    "usage": {
      "input_tokens": 2,
      "cache_creation_input_tokens": 7197,
      "cache_read_input_tokens": 28208,
      "output_tokens": 4990,
      "output_tokens_details": {
        "thinking_tokens": 108
      },
      "server_tool_use": {
        "web_search_requests": 0,
        "web_fetch_requests": 0
      },
      "service_tier": "standard",
      "cache_creation": {
        "ephemeral_1h_input_tokens": 7197,
        "ephemeral_5m_input_tokens": 0
      },
      "inference_geo": "not_available",
      "iterations": [
        {
          "input_tokens": 2,
          "output_tokens": 4990,
          "cache_read_input_tokens": 28208,
          "cache_creation_input_tokens": 7197,
          "cache_creation": {
            "ephemeral_5m_input_tokens": 0,
            "ephemeral_1h_input_tokens": 7197
          },
          "type": "message"
        }
      ],
      "speed": "standard"
    }
  },
  {
    "condition": "DIRECT",
    "rep": 2,
    "usage": {
      "input_tokens": 2,
      "cache_creation_input_tokens": 0,
      "cache_read_input_tokens": 35405,
      "output_tokens": 4805,
      "output_tokens_details": {
        "thinking_tokens": 125
      },
      "server_tool_use": {
        "web_search_requests": 0,
        "web_fetch_requests": 0
      },
      "service_tier": "standard",
      "cache_creation": {
        "ephemeral_1h_input_tokens": 0,
        "ephemeral_5m_input_tokens": 0
      },
      "inference_geo": "not_available",
      "iterations": [
        {
          "input_tokens": 2,
          "output_tokens": 4805,
          "cache_read_input_tokens": 35405,
          "cache_creation_input_tokens": 0,
          "cache_creation": {
            "ephemeral_5m_input_tokens": 0,
            "ephemeral_1h_input_tokens": 0
          },
          "type": "message"
        }
      ],
      "speed": "standard"
    }
  }
]
```
