# Q3 subscription Read-denial sentinel spend notice

Date: 2026-09-25 UTC. Status: **approval requested, no Q3 paid call made**.

This is one Claude Code in WSL subscription call on the pinned
`worker-sonnet-low` cell. It asks Claude Code's restricted `Read` tool to open
one nonexistent path below `/run/claude-auth` and verifies a permission denial,
served Sonnet 5 identity, terminal receipt and unchanged actor. No credential
value or account identifier is requested or stored. The existing N5 sentinel
passed previously, but its binding to the N4 host changed when that host was
reattested, so it cannot serve as current Q3 evidence.

The local admission allowance is **USD 0.10 API-equivalent for one call**.
The projected API-equivalent usage is **USD 0.03-0.15**, with **5-20 minutes**
elapsed including preflight and reconciliation. The earlier N5 sentinel
reported USD 0.053023. This is a bounded local allocation, not a subscription
invoice or a hard provider charge cap; a provider overrun or uncertain receipt
stops the Q3 canary without replay. The Q3 canary's separate USD 12 allocation
and USD 0.1-6 API-equivalent projection are not included in this notice.

Pricing checked on 2026-09-25 from [Anthropic's Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing):
Sonnet 5 costs USD 2 per million ordinary input tokens, USD 2.50 per million
five-minute cache-write tokens, USD 0.20 per million cache-read tokens and
USD 10 per million output tokens. This projection assumes one call with
2,000-10,000 ordinary input tokens, 2,000-20,000 cache-write tokens,
0-100,000 cache-read tokens and 1,000-5,000 output tokens, allowing for tool
loop variance. Those upper category assumptions price at about USD 0.14,
above the USD 0.10 local allowance; the historical sentinel result is the
more relevant central estimate. The model call may exceed its allocation,
and subscription billing impact cannot be inferred from the reported API
equivalent.

The gate must freeze the current Q3, N4 and subscription evidence digests,
sentinel source and runtime hashes, this notice digest, one-call ceiling,
model/effort, target path and no-replay rule into an exact manifest. A separate
approval record must bind that manifest before dispatch.
