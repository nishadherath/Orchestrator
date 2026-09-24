# Routing remediation: execution protocol and estimates

Date: 2026-09-19. Status updated 2026-09-24: worker N0A and N1 are complete
for offline review; N2 and Controller execution remain deferred.

2026-09-24 sequencing amendment: follow the
[worker-first plan](WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md).
N0A and N1 are complete for review. The current design is
[contract v2](WORKER-EXECUTION-CONTRACT-v2.md), with the
[N1 result](stage-results/worker-n1.md). The sequencing plan supplies corrected
dependencies and dated estimates without changing this protocol's review gates.

Applies to the [worker plan](WORKER-ROUTING-ACTION-PLAN-2026-09-19.md) and
[deferred Controller plan](CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md).
The operator directed worker N0, N0A and N1. Further stages and the Controller
programme still require the operator's direction. This document and its
handoffs do not independently authorise a model switch, agent launch,
experiment or promotion.

## Stage contract

1. Start only the named stage after the operator directs execution. Check the
   current branch, HEAD, worktree and preceding stage evidence; preserve local
   work. Read `AGENTS.md`, `CLAUDE.md` and the named handoff. Use Graft MCP
   freshness and scoped retrieval in every session, resume and child agent.
2. Implement only that stage's scope. Write reproductions for observed defects
   before their fixes. Keep an explicit distinction between observed behaviour,
   source-inspection findings and proposed design. Never repair a frozen
   historical result by replacing its hashes with current ones.
3. Run focused checks after the change. Run the existing full offline harness
   before stage delivery. For shipped source changes, use `tools/build_dist.py`
   and verify source/bundle parity; follow the builder's existing gate instead
   of adding redundant complete runs. Never hand-edit generated `dist/` files.
4. Record the stage in `docs/stage-results/<programme>-<stage>.md`, with a
   machine-readable result under `test/results/` where useful. Include files,
   acceptance evidence, commands, actual versus requested model/effort,
   measured spend or unknowns, limitations and the exact next action. Paths
   below are proposed artefacts until created by their owning stage.
5. Report complete, incomplete or blocked against each exit criterion. A
   green existing harness is not evidence for an untested requirement. Stop
   for operator review at the stage boundary; do not continue automatically.
6. Before a model/effort change, fresh session or any agent launch, use
   `tools/handoff.py new`, fill its ten sections, retain computed subtotal
   lines and pass `tools/handoff.py check`. Notify the operator of the target
   model/effort, path, API-equivalent cost range and elapsed-time range.
   Same-model continuation needs no artificial switch. Stage records still
   state the next action. No subagents are scheduled by these plans.

Use GPT-5.6 Sol High for bounded implementation. Reserve GPT-6 Astra High for
the specified architecture/evaluation adjudications. These are engineering
recommendations, not measured head-to-head rankings. If Sol encounters an
unresolved contract or repeated failure on the same invariant, stop with a
minimal reproduction and propose a bounded Astra High review. Do not quietly
raise effort, launch a helper or repeat the entire implementation context.

For required switches the operator selects the named model and effort in the
host, then continues with the checked handoff. The application must expose
those settings; a Claude worker name is not a substitute for a Codex model.

## Planning evidence and limits

Planning baseline: branch `v1.0-rc1`, HEAD `1983834`, clean tracked worktree
before these documents. Graft semantic and wiring checks passed on 2026-09-19.
The preceding review ran the full offline harness, 57/57 passed, including
69-file source/bundle parity. These counts predate future implementation.

The twelve gaps refer to the 2026-09-19 review in this conversation. Its local
fake probes found: a public-label-only C01-D1 result scored accepted/100 with
no implementation; restarting a terminally failed matrix admitted sequence 2
after sequence 1 had failed; and the manifest omitted relevant runtime
dependencies. The first two are reproduced behaviours, not paid incidents.
The first-entry Generator mapping is source-confirmed. Task-wide Controller
admission needs a concurrency reproduction before claiming a double dispatch.
Preserve these distinctions in stage results.

The R5 48-task/288-variant corpus is currently a plumbing fixture. Its size and
the existing 33 passing checks do not qualify real task-quality measurement.
The old matrix and pilot stay paused. The next programme does not repair or
execute their Controller-specific code; the deferred programme owns that work.

## Cost basis

Official pages checked 2026-09-19:
[Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) and
[pricing](https://developers.openai.com/api/docs/pricing).
Both named models support High effort. Standard short-context rates in USD
per million tokens are:

| Model | Ordinary input | Cached input | Cache writes | Output |
| :--- | ---: | ---: | ---: | ---: |
| GPT-5.6 Sol | 4 | 0.40 | 5 | 20 |
| GPT-6 Astra | 10 | 1 | 12.50 | 50 |

Output includes billed reasoning. Fast rates are twice these standard rates.
Reprice long-context requests, residency charges or changed provider terms at
execution. The estimates below concern text usage; they assume no separately
billed hosted tools. Any such tools need a separate estimate.

Let I, R, W and O be millions of ordinary input, cache reads, cache writes and
output tokens. Use mutually exclusive input categories from actual accounting:
`Sol = 4I + 0.4R + 5W + 20O`; `Astra = 10I + R + 12.5W + 50O`.
Do not add cache-write tokens to ordinary input a second time. No cache hit,
cross-model cache sharing or subscription-to-API billing equivalence is assumed
to have been observed.

The following are planning units, not hourly rates or guaranteed stage costs.
All ranges include 30 percent contingency after the token calculation. The
last column spans Standard at the low assumption through Fast at the high
assumption, rounded outward. Reprice a stage that exceeds the assumed tokens.

| Unit | Model | I | R | W | O | Standard with contingency | Standard/Fast envelope |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| B: baseline/small stage | Sol High | .10-.25 | .20-.60 | .02-.05 | .02-.05 | 1.27-3.24 | USD 1.25-6.50 |
| I: implementation stage | Sol High | .25-.75 | .50-1.50 | .05-.15 | .05-.15 | 3.25-9.75 | USD 3.25-19.50 |
| R: bounded review | Astra High | .10-.30 | .20-.80 | .02-.06 | .02-.06 | 3.19-9.82 | USD 3-20 |

Time ranges in the plans cover hands-on engineering and checking, including
ordinary local test waits. They exclude operator review delays. Serial live
experiments have separate ranges. Elapsed time is uncertain and is not inferred
from tokens or from a different model's benchmark timings.

## Paid execution and standing approvals

These planning documents make no paid calls. Before a future experiment,
state its scope, expected spend, admission ceiling, run count and time range.
Check the operator's existing authorisation and `CLAUDE.md` cost rule; ask only
where those do not cover the proposed work. The project rule asks first above
USD 100. A manifest must record the applicable authorisation and frozen scope;
a changed hash alone is not a reason to demand another approval when the
existing authorisation covers the change. A scope or allowance expansion needs
its own check. Stage starts remain subject to the operator's requested pause.

Admission ceilings constrain local dispatch; they are not a guarantee that
provider billing can never overshoot an in-flight request. Stop on accounting
uncertainty, preserve reservations and reconcile actual charges. Never retry
silently or treat an interrupted call as free. No unavailable cell may be
silently substituted. Publish incomplete or inconclusive outcomes honestly.

Graft DeepSeek refreshes retain their separate standing approval. Reuse its
cache, refresh changed source as necessary, and record returned usage/cost if
available. An exact Graft cost is currently unpriced and is excluded from the
OpenAI and Claude figures, never represented as zero. Documentation-only
changes do not justify a paid semantic rebuild when freshness already passes.

## Completion protocol

A stage handoff must identify what remains and which plan owns it. Gap closure
requires its acceptance evidence, not merely the existence of a module or
schema. No automatic default promotion, commit, merge, tag, push or publication
is implied by completing a stage. Final release work preserves transactional
install/upgrade/rollback and the historical B0 evidence.
