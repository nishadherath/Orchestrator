# Q4S prospective spend notice

Prepared 2026-09-25 UTC / 2026-09-26 Australia/Sydney. Status: **frozen
design for operator stage review; no Q4S model call has been made**. The
operator's standing authorisation covers paid calls in this project, but the
staged protocol holds dispatch until the S2 review is complete. The credential
method is authenticated Claude Code in WSL, not a Claude API key.

S3 has two head-only transport-canary calls, Sonnet-low and Sonnet-medium,
each with USD 3 root allocation. Its local admission allocation is USD 6;
direct API-equivalent planning range is USD 0.5-3 and elapsed time 15-60
minutes. A failed canary stops the screen. S4 has six independent families,
each run under two B0 repetitions and one Sonnet-medium arm, 18 episodes.
Each has a USD 4 root allocation and a conditional repair tail of Sonnet-low
then Opus-high, yielding at most 54 provider calls and USD 72 of local
allocation. S4 projects USD 6-30 direct API-equivalent usage and 2-7 hours.
The combined maximum local admission allocation is **USD 78**, with at most
56 provider calls. Combined API-equivalent planning range is USD 6.5-33 and
elapsed time 2.25-8 hours. The allocation is a reservation sum, not an
invoice prediction or guarantee against an in-flight provider overrun.

The projection uses Q4's 16 calls at USD 9.849 and Q4R's three at USD 1.666
as workload anchors, then widens for the new families, medium effort, cache
mix and possible repairs. A started attempt may use roughly 10,000-100,000
cached or cache-created input tokens and 2,000-10,000 output tokens; the
actual distribution, cache charges and Claude Code subscription invoice
impact are unknown. The runner records settled reported cost, token/cache
counters and model identities for every started call. No spend is inferred
from this notice.

Anthropic's published [Sonnet 5 pricing](https://www.anthropic.com/news/claude-sonnet-5)
was USD 2 per million ordinary input tokens and USD 10 per million output
tokens; [Opus 5 pricing](https://www.anthropic.com/news/claude-opus-5) was
USD 5 and USD 25 respectively when checked on 2026-09-25 UTC. Cache pricing
and actual provider accounting may differ from ordinary-token arithmetic.

The frozen manifest binds this notice, the six corpus digests, canary,
trigger assessments, source and launcher hashes, schema, prompt, registry,
rubrics, episode order, allocation and stop rules. Dispatch must recheck WSL
authentication, current host/source attestation and exact manifest before
any campaign directory or provider-call intent. No N5/Q5 reserved task,
Controller route, historical Q4R output, or automatic replay is in scope.
