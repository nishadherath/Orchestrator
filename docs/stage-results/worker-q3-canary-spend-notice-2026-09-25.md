# Q3 two-task B0 canary spend notice

Date: 2026-09-25 UTC. Status: **approval not yet requested; no Q3 canary
episode has been dispatched**.

The canary runs the frozen public P01 cachetools and P02 ItsDangerous tasks in
that order, once per family, through the default B0 ladder. A task stops as
soon as B0 stops. The maximum is three serial attempts per task: Sonnet 5 low,
one Sonnet 5 low repair, then Opus 5 high. There are at most six Claude Code
subscription calls in WSL, four Sonnet and two Opus. No Controller, candidate
route, reference overlay, partial overlay or sealed N6 task is included.

Each episode has a **USD 6 local admission allocation**, **USD 12 combined**.
The direct API-equivalent usage projection is **USD 0.1-6 total** with
**0.5-2 hours** elapsed after preflight. This is neither a subscription invoice
nor a provider-enforced charge cap. A running call may exceed its local
allocation; a reported overrun or unknown charge stops further dispatch and
requires manual reconciliation. A started invocation is never replayed.
The separately gated Q3 Read-denial sentinel has its own notice and allowance;
its reported API equivalent will be listed separately in the result.

Pricing checked on 2026-09-25 from [Anthropic's Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing):
Sonnet 5 input, five-minute cache write, cache read and output cost USD 2,
2.50, 0.20 and 10 per million tokens. The pinned Opus 5 costs USD 5, 6.25,
0.50 and 25 respectively. The projection allows 0-20,000 ordinary input,
3,000-30,000 cache-write, 20,000-150,000 cache-read and 1,000-15,000 output
tokens per call. At those per-call upper values, four Sonnet and two Opus
calls price at about USD 2.66. A roughly twofold contingency rounds the high
projection to USD 6. Cache categories are mutually exclusive; cross-model
cache reuse is not assumed. Extra tool loops, longer output or changed
provider behaviour can exceed that range. The existing N5 synthetic B0
average is not treated as a forecast for these larger packages.

The exact approval manifest must bind the two actor file inventories and
hidden oracle digests, B0 order/ladder, current Q1/Q3 host and credential
evidence, current paid Read sentinel, relevant runtime/source hashes, this
notice digest, the provider-free timeout/no-replay result, USD 6/12
allocations, six-call ceiling, stop rules and no-replay
condition. Root-owned hidden grading follows each stopped writer. The canary
is diagnostic only and cannot qualify a routing change or be counted as an
eight-family Q0 admission result.
