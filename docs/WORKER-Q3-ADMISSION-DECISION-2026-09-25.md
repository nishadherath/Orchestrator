# Q3 admission decision: two public B0 tasks

Date: 2026-09-25. Status: **Q3 implementation authorised and underway;
the exact paid sentinel and canary remain separately gated**. This is the
concrete next-stage proposal after
[Q2](stage-results/worker-q2.md), under the
[execution protocol](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md). It does not
authorise a provider call or change the shipped B0 default.

## Recommended decision

Direct a bounded Q3 stage that first builds and attests a paid Claude Code
adapter for the Q1 multi-file actor boundary, then prepares a frozen
**two-task B0-only canary** using public P01 cachetools and P02 ItsDangerous.
Review the exact manifest and dated spend notice before dispatch. Do not
build a reserved corpus or run candidate routes in this stage.

The two-task canary should answer whether B0 sees these larger packages as
nontrivial, what the actual per-task cost and time are, whether the graders are
stable, and whether a six-family expansion is worth curating. It cannot invoke
the original Q0 eight-task ceiling/floor thresholds or qualify a routing
change. Repeating either task does not create an independent task unit.

## Frozen intended scope and gates

| Gate | Required Q3 evidence before the next gate |
| :--- | :--- |
| Paid multi-file adapter | An authenticated WSL Claude Code worker may read the public package and edit only the two declared existing source files. Root-owned issue/acceptance evidence, oracle, credential and Windows mounts stay protected. The adapter binds requested cell, served model identity, requested effort and terminal receipt to the Q1 stop/collect record. Unknown effort remains unknown; no model substitution is accepted. |
| Provider-free adversarial checks | Run at-most-once dispatch, cancellation/uncertain receipt, protected-file drift, actor self-modification, oracle read denial, source parity, accounting and replay rejection without a paid call. The legacy single-file N5 transport must still pass. Run the full offline harness. |
| Exact paid preflight | Freeze P01 and P02 catalogue/oracle hashes, actor files, order, B0's three-step ladder, current Q1/credential/sentinel evidence, adapter/runtime hashes, root allocations, stop rules, no-replay rule and dated notice into one manifest. Its approval record must match that manifest and allowance before dispatch. Stale authentication or host evidence blocks launch. |
| Canary dispatch | Run each public family once under B0, stopping an episode as soon as its policy stops. Record all attempts, actual Claude Code API-equivalent receipts, cache categories, wall time, served model identity, requested effort, public result, hidden quality, critical errors, false success and any uncertain charge. Grade only after writer stop. |
| Adjudication | Examine actual patches and diagnosis, not only test booleans. Report both tasks independently, timer-sensitive P01 grade stability, per-attempt costs and the decision to curate six more families or stop. Keep B0 unchanged. |

B0's fixed ladder is Sonnet-low, a Sonnet-low local repair, then Opus-high
fallback. These map to frozen `claude-sonnet-5` and `claude-opus-5` identities in
[`src/model_registry.json`](../src/model_registry.json). There are at most six
serial worker calls across the two tasks, four Sonnet and two Opus. The
reference and partial overlays are calibration evidence and must not enter the
worker actor. No candidate cell, Controller, Fable or sealed N6 R task is in
this canary.

## Cost and time for the decision

The proposed **local admission allocation is USD 6 per episode, USD 12
combined**. Reservation limits which episode may start; it cannot stop an
already running provider call at that amount. An uncertain or excess charge
halts further dispatch without replay. The allocation is not a subscription
invoice or a forecast of actual provider usage.

The preliminary **direct API-equivalent usage projection is USD 0.1-6 for the
two-task run**, with **0.5-2 hours** elapsed after paid preflight. Separately,
building and validating the multi-file paid adapter is estimated at **4-8
engineering hours** and makes no planned Claude provider call. The current
development host does not expose this session's API-token accounting, so its
own API-equivalent cost is unknown rather than zero. The exact spend notice
must be updated from fresh attestation and any revised token estimate before
dispatch.

Pricing checked 2026-09-25 from [Anthropic's Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing):
Sonnet 5 ordinary input, five-minute cache write, cache read and output cost
USD 2, 2.50, 0.20 and 10 per million tokens; Opus 5 costs USD 5, 6.25, 0.50
and 25. The projection assumes up to six calls, each with 0-20,000 ordinary
input, 3,000-30,000 five-minute cache-write, 20,000-150,000 cache-read and
1,000-15,000 output tokens. At those upper token values four Sonnet and two
Opus calls price at about USD 2.66; a roughly twofold contingency rounds to
USD 6. A lower path has one Sonnet call per task. Cache categories are
mutually exclusive and no cross-model cache reuse is assumed. The much
smaller N5 synthetic B0 tasks averaged about USD 0.081 per episode across
12 tasks; that observation is context, not an extrapolation that these
multi-file tasks will cost the same. Extra tool loops, long output, changed
model prices or provider behaviour can exceed the projected range and local
allocation. Subscription billing impact is not inferred from API-equivalent
receipts.

## Why a decision is needed now

The operator-review boundary is explicit in the
[Q0 protocol](WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md) and
[execution protocol](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md). Q2 has
passed; the Q3 paid adapter is an unstarted stage, and the two-task canary
amends Q0's original eight-task admission sequence. The decision requested
here was **whether to start this bounded Q3 stage**; the operator authorised
that start. This did not authorise dispatch of a still-unbuilt manifest. The
later exact approval gate uses a completed, hash-bound manifest and current
host evidence, as Q2 requires.
