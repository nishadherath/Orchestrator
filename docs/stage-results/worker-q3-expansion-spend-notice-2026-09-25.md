# Q3 six-family public B0 expansion: dated spend notice

Date: 2026-09-25 UTC. This notice applies only to public P03-P08, one B0
episode per independent project family, after the two-task P01/P02 canary. The
fixed ladder is Sonnet-low, one Sonnet-low local repair, then Opus-high. The
runner may start at most **18 Claude Code subscription provider calls** and
reserves **USD 6 per task, USD 36 combined** in local allocations. It cannot
interrupt an in-flight provider call at the allocation; any uncertain or
excess charge stops later dispatch without replay. It excludes Controller,
candidate routing, Q4 reserved tasks and all Q5 work.

The projected *additional* direct API-equivalent usage is **USD 0.5-16** and
elapsed time **1-8 hours** after preflight. These are estimates, not a
subscription invoice or a promise that no provider overrun can occur. The
earlier sentinel and two-task canary reported USD 0.493561202 API-equivalent
usage in total; that amount is already spent and is separate from this notice.

Pricing checked 2026-09-25 against
[Anthropic's Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing):
the frozen Sonnet 5 cell costs USD 2 per million ordinary input, 2.50 per
million five-minute cache writes, 0.20 per million cache reads and 10 per
million output tokens. The frozen Opus 5 cell costs USD 5, 6.25, 0.50 and 25
for those categories. A high-use scenario of 12 Sonnet and six Opus calls,
each with 20,000 ordinary input, 30,000 cache-write, 150,000 cache-read and
15,000 output tokens, prices near USD 8; roughly twofold contingency gives
the USD 16 projection ceiling. A low path needs one Sonnet call per task.
Cache categories are mutually exclusive and cross-model reuse is not assumed.
Actual tool loops, tokenisation, changed model prices and unexpected output
can exceed the range. The Claude Code subscription's actual billing impact is
not observable from these API-equivalent receipts.

The exact manifest must bind this notice's SHA-256, all six frozen tasks and
oracles, reference calibration, attack evidence, live adapter/runtime hashes,
current WSL host, authentication and Read-denial sentinel evidence, fixed
model identities and stop rules. The operator's standing instruction on
2026-09-25 approved work through Q4, including this bounded paid Q3 run;
the manifest-specific approval record will quote that instruction and the
USD 36 / 18-call ceiling. No episode starts if that record or fresh preflight
does not match. This notice does not authorise Q5.
