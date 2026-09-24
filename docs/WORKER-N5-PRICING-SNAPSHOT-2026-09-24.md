# N5 pricing snapshot, not a spend authorisation

Date checked: 2026-09-24. This is a direct Claude API-equivalent estimate for
the configured N5 cell screen. It is **not** the manifest-bound spend notice or
approval, and no provider call was made. Pricing and model availability must be
checked again immediately before a paid run.

| Configured API model | Input, USD/MTok | Output, USD/MTok | Source |
|---|---:|---:|---|
| `claude-sonnet-5` | 2 | 10 | [Sonnet 5](https://platform.claude.com/docs/en/models/sonnet-5/whats-new-sonnet-5) |
| `claude-opus-5` | 5 | 25 | [Opus 5](https://platform.claude.com/docs/en/models/opus-5/overview) |
| `claude-fable-5-1` | 10 | 50 | [Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview) |

The fixed screen has five efforts per model, each with one identity call and
three microtasks. The estimates below assume each identity call uses 1,000
uncached input and 200 output tokens. Each microtask is shown with the same
uncached token count across all 45 calls. They include no prompt-cache charge,
tool surcharge, tax, failed-call overhead or provider overrun. They are
illustrative sensitivity calculations, not measured workload usage.

| Microtask tokens per call, input/output | Direct API-equivalent screen total |
|---|---:|
| 10,000 / 2,000 | USD 5.27 |
| 40,000 / 6,000 | USD 18.02 |
| 50,000 / 8,000 | USD 23.12 |

The provisional **USD 48.75** screen budget is the sum of local per-call
admission allocations, not a guaranteed provider bill ceiling. A Fable
microtask at 50,000 input and 8,000 output tokens costs about USD 0.90 before
cache effects and fits its USD 1 allocation narrowly. If usage grows beyond
that, the CLI may stop at its per-call budget; a provider charge can also be
reported above an allowance. The driver retains such charges and blocks later
dispatch instead of hiding them. Until real token counts are observed, use a
low-confidence planning band of **USD 5-30**, with **USD 48.75** reserved
locally and possible overrun explicitly unresolved. Direct API billing and a
Claude subscription are different payment mechanisms; the API-equivalent
figure does not predict a subscription invoice.

Elapsed time is also unmeasured. At 0.5-1.5 minutes for each identity call,
2-8 minutes for each microtask, and about 0.5 minute of WSL validation and
staging per scheduled call, a complete 60-call screen would take roughly
**2.1-6.9 hours** serially. Unsupported identities shorten it by skipping
their remaining three calls. The final notice must replace these assumptions
with the latest prices and any observed host latency before dispatch.

Anthropic now lists `claude-opus-5` as legacy and
[`claude-opus-5-5`](https://platform.claude.com/docs/en/models/opus-5-5/overview)
at USD 4/20 per MTok. The current repository pins Opus 5 in the B0 fallback
and in the frozen 15-cell evaluation. Switching it to 5.5 now would change the
baseline and invalidate existing identity and quality evidence. Treat a 5.5
migration as a separately frozen, paired qualification; do not silently
substitute it into this N5 screen or B0.
