# Q4 M3 no-replay continuation spend notice

Date: 2026-09-26 UTC. This notice covers a successor execution for sequences
4–16 of the already approved M3 public screen. It inherits sequences 1 and 2
from the stopped campaign and the provider-free reconciliation of sequence 3.
No completed or started sequence is repeated.

The predecessor made three settled calls costing **USD 2.323065001
API-equivalent**. Sequence 3 is retained as a terminal Sonnet-xhigh failure:
the response exceeded the 8,192-token ceiling, no edit was collected, its cost
was settled at USD 0.9239838, and it was not replayed. The successor admits at
most 13 remaining episodes, three calls and USD 6 per episode: **USD 78 and 39
new calls**. Across predecessor and successor, the maximum becomes USD
80.323065001 based on actual prior cost plus remaining allocations and 42
calls, below the original USD 99 and 51-call limits.

Expected additional API-equivalent usage is **USD 3 to USD 50** and expected
elapsed time is **2 to 7 hours**. These are planning ranges. Claude Code uses
the existing Claude.ai Max subscription, so invoice impact remains
unobservable; provider-reported API-equivalent telemetry is recorded.

Pricing was rechecked on 2026-09-26 against Anthropic's official pages:
Claude Sonnet 5 is USD 2 per million input and USD 10 per million output
tokens; Claude Opus 5 is USD 5 per million input and USD 25 per million output
tokens. Cache telemetry remains provider-reported.

- https://www.anthropic.com/news/claude-sonnet-5
- https://www.anthropic.com/news/claude-opus-5

The continuation stops on stale predecessor, reconciliation, host,
calibration or source evidence; uncertain cost; protected drift; or a
nonterminal invocation. A settled terminal provider failure is recorded as
that episode's outcome and is not replayed. It does not authorise Q5.
