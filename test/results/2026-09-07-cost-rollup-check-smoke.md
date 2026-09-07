# Cost roll-up check (smoke), 2026-09-07 16:40

Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Model: sonnet. Reps per condition: 1. Per-call timeout: 90s.

| Condition | Rep | total_cost_usd | num_turns | elapsed_s | Error |
| :--- | :--- | :--- | :--- | :--- | :--- |
| SPAWN | 1 | 0.17074479999999997 | 3 | 78.9 |  |
| DIRECT | 1 | 0.0386076 | 1 | 10.1 |  |

SPAWN mean: 0.17074479999999997. DIRECT mean: 0.0386076.

Raw usage objects:

```json
[
  {
    "condition": "SPAWN",
    "rep": 1,
    "usage": {
      "input_tokens": 6,
      "cache_creation_input_tokens": 16948,
      "cache_read_input_tokens": 108069,
      "output_tokens": 794,
      "output_tokens_details": {
        "thinking_tokens": 98
      },
      "server_tool_use": {
        "web_search_requests": 0,
        "web_fetch_requests": 0
      },
      "service_tier": "standard",
      "cache_creation": {
        "ephemeral_1h_input_tokens": 16948,
        "ephemeral_5m_input_tokens": 0
      },
      "inference_geo": "not_available",
      "iterations": [
        {
          "input_tokens": 2,
          "output_tokens": 368,
          "cache_read_input_tokens": 44408,
          "cache_creation_input_tokens": 748,
          "cache_creation": {
            "ephemeral_5m_input_tokens": 0,
            "ephemeral_1h_input_tokens": 748
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
      "cache_creation_input_tokens": 7096,
      "cache_read_input_tokens": 28208,
      "output_tokens": 358,
      "output_tokens_details": {
        "thinking_tokens": 0
      },
      "server_tool_use": {
        "web_search_requests": 0,
        "web_fetch_requests": 0
      },
      "service_tier": "standard",
      "cache_creation": {
        "ephemeral_1h_input_tokens": 7096,
        "ephemeral_5m_input_tokens": 0
      },
      "inference_geo": "not_available",
      "iterations": [
        {
          "input_tokens": 2,
          "output_tokens": 358,
          "cache_read_input_tokens": 28208,
          "cache_creation_input_tokens": 7096,
          "cache_creation": {
            "ephemeral_5m_input_tokens": 0,
            "ephemeral_1h_input_tokens": 7096
          },
          "type": "message"
        }
      ],
      "speed": "standard"
    }
  }
]
```
