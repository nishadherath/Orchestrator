# Cost roll-up check (full), 2026-09-07 17:36

Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Model: sonnet. Reps per condition: 2. Per-call timeout: 600s.

| Condition | Rep | total_cost_usd | num_turns | elapsed_s | Error |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SPAWN | 1 | 0.2975875 | 3 | 520.3 |  |
| SPAWN | 2 | 0.2881648 | 3 | 540.5 |  |
| DIRECT | 1 |  |  | 600.0 | timed out after 600s |
| DIRECT | 2 | 0.057827199999999995 | 1 | 70.3 |  |

SPAWN mean: 0.29287615. DIRECT mean: 0.057827199999999995.

Raw usage objects:

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
    "usage": null
  },
  {
    "condition": "DIRECT",
    "rep": 2,
    "usage": {
      "input_tokens": 2,
      "cache_creation_input_tokens": 0,
      "cache_read_input_tokens": 35346,
      "output_tokens": 4973,
      "output_tokens_details": {
        "thinking_tokens": 127
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
          "output_tokens": 4973,
          "cache_read_input_tokens": 35346,
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
