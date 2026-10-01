# N5 Claude Code subscription screen: spend notice

Prepared 2026-09-25 (Australia/Sydney). This notice is for the fixed,
sequential **15-cell, 60-call worker capability screen only**: one identity
call and three microtasks for each Sonnet, Opus and Fable effort cell. It does
not authorise the later development or reserved campaigns. The screen uses
Claude Code's existing Claude.ai Max subscription in isolated Kali WSL, not
an Anthropic API key. The figures below are direct Claude API-equivalent
estimates for comparison, not a prediction of an incremental subscription
invoice.

| Pinned model | Base input/output, USD per million tokens | 5-minute cache write/read, USD per million tokens |
|---|---:|---:|
| `claude-sonnet-5` | 2 / 10 | 2.50 / 0.20 |
| `claude-opus-5` | 5 / 25 | 6.25 / 0.50 |
| `claude-fable-5-1` | 10 / 50 | 12.50 / 0.25 |

Prices were checked against [Anthropic's model pricing](https://platform.claude.com/docs/en/about-claude/pricing)
on 2026-09-25. The pinned Opus 5 is a legacy model; the newer Opus 5.5 price
does not apply to this frozen screen. The screen tests the requested model and
effort and records the served identity. An unsupported or mismatched identity
stops that cell's remaining tranche; it is never silently substituted.

The manifest allocates **USD 48.75** locally: 15 identity calls at USD 0.25
and 45 microtasks at USD 1.00. This is the exact admission ceiling requested
for the screen, not a hard provider-billing guarantee. A reported overrun is
retained in the ledger and stops subsequent dispatch. There is no automatic
retry of a started call. A separately prepared, manifest-matched approval is
required before launch.

For a direct API-equivalent projection, assume 1,000 uncached input and 200
output tokens per identity call, and the same token counts for every
microtask across models and efforts. At 10,000 input / 2,000 output tokens
per microtask the total is **USD 5.27**; at 40,000 / 6,000 it is **USD
18.02**; at 50,000 / 8,000 it is **USD 23.12**. These examples exclude cache
charges, tool overhead, failed-call usage, tax and possible overrun. The
planning band is **USD 5–30**, with low confidence and USD 48.75 reserved
locally. It is not a spend target. The preceding one-call Sonnet-low access
sentinel reported USD 0.053081 API-equivalent cost, including 11,277 cache
creation, 21,880 cache-read, six other input and 247 output tokens; it is a
security probe, not a representative microtask.

Serial elapsed time is projected at **2.1–6.9 hours** if all 60 calls run:
0.5–1.5 minutes per identity call, 2–8 minutes per microtask, plus roughly
0.5 minute of WSL validation and staging per scheduled call. These are
assumptions, not measured screen latency. The configured worker timeouts alone
sum to 12.5 hours (15 × 5 minutes plus 45 × 15 minutes), before staging;
unsupported cells can shorten the schedule. The screen runner persists an
intent before each call and blocks on an ambiguous stop rather than replaying
it. The hidden grader runs only after a terminal, stopped-writer receipt.

The dated [pricing snapshot](../WORKER-N5-PRICING-SNAPSHOT-2026-09-24.md)
contains the arithmetic and model-migration caveat. The current host,
subscription and Read-denial attestations and this notice are hashed into the
screen manifest. A changed source, host, credential evidence or notice needs
a new manifest and a new exact approval before dispatch.
