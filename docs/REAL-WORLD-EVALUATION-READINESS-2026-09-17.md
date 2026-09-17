# Real-world evaluation readiness

Date: 2026-09-17. Scope: Stage 7 preparation and bounded live instrumentation
calibration. No pilot episode was run.

## Outcome

Stages 1-6 already supply complete attempt accounting, atomic budget admission,
eligible learning, artefact-bound acceptance, reversible installation and
operational diagnostics. Reusing those results removes most of W01 and the
shared portions of W02, W04 and W09 from the evaluation backlog.

All eight pilot vertical slices are now executable:

- D01 tests configuration precedence, including explicit zero, false and empty
  values. It represents an ordinary bounded repair.
- D11 tests interruption after durable commits, exact resume behaviour,
  idempotent completion and preservation of unknown state metadata.
- D03 tests connection and 503 retries against a fake clock, deadlines,
  idempotent methods and write retries that require a non-empty idempotency key.
- D05 tests tenant and option isolation while preserving legitimate cache hits.
- D07 tests bounded queue shutdown against p-limit semantics: pending work is
  rejected, active work drains, late submissions fail and configured
  concurrency is preserved.
- D08 tests a resumable SQLite migration with durable batches, transactional
  failure recovery, legacy-writer compatibility, preserved IDs and a final
  non-null schema.
- D09 tests migration from anonymous tuples to an immutable named result across
  parser, storage, CLI, batch consumer, package exports and module execution.
- D10 uses matched retention tickets to distinguish a disproved generated-file
  assumption from an explicit no-edit constraint that requires clarification.

Each grader is external to the disposable actor root. The original defect and
three plausible wrong repairs fail hidden behavioural checks. A reference fix
and a materially different correct fix pass. Deleting or weakening a public
check and adding an actor-controlled shadow oracle are rejected by the edit
boundary. The validation makes zero model calls and protects the external
oracle hashes across every run.

The Windows host now has a recorded WSL2 boundary proof. An actor running as
Linux `nobody` can read and write its own workspace but cannot read the
root-owned evaluator directory at mode `0700`; the evaluator can read actor
output. The evidence is integrity-bound and must be regenerated on each
campaign host. This proves filesystem separation, not model transport or a
complete episode.

The live instrumentation gate is also complete. The first three-call run
confirmed terminal direct and spawned responses, disjoint usage fields,
parent/child aggregate roll-up, retained accounting after a local timeout and
the mediated WSL boundary. Its aggregate `modelUsage` contained both Sonnet 5
and Haiku 4.5, so the run failed its deliberately strict identity predicate.
A preserved spawn-only adjudication then used streamed messages and forwarded
subagent events with both root and worker explicitly pinned. Every attributable
task message reported `claude-sonnet-5`; Haiku appeared only in the aggregate
billing map and is recorded as unattributed Claude Code auxiliary overhead.

## Frozen surfaces

`tools/evaluation_freeze.py` binds the candidate to the generated bundle
manifest, catalogue, price snapshot, policies B0/B1/B2, `acceptance-v2`, ledger
schemas and budget implementation. Its JSON output records the source revision,
dirty state, exact hashes, named model IDs, limits, ready tasks and blockers.

Requested worker aliases are not treated as identity evidence. A paid episode
must report `claude-sonnet-5` or `claude-opus-5` as actually served before its
cost or policy comparison qualifies. Fable 5.1 is frozen out of the pilot.

## Cost decision

Official prices checked on 2026-09-17 are USD 2/10 per million ordinary
input/output tokens for Sonnet 5, USD 5/25 for Opus 5, and USD 10/50 for Fable
5.1. The corresponding five-minute cache writes are USD 2.50, 6.25 and 12.50;
cache reads are USD 0.20, 0.50 and 0.25.

Keep the pilot's USD 100 hard allocation because real episode token shapes are
still unmeasured. Add a six-episode D01/D11 checkpoint across all three policy
arms with USD 24 of episode reservations and USD 2 calibration headroom. Stop
there if model identity, usage roll-up, grading or reservation records do not
reconcile. The broader 104-episode working estimate remains USD 110-220 and its
hard allocation remains USD 440 until pilot evidence supports a narrower value.

The offline episode runner, live worker adapter, policy executor, restart-safe
integration and calibration are complete. The complete remaining programme is
approximately 1-2 engineer-days plus 2-4 hours of result review. Calibration
cost USD 0.0476572 API equivalent across terminal calls; the first run also
retains a separate USD 0.05 uncertain timeout allowance. These are Claude Code
list-price telemetry under the signed-in Max subscription, not an API invoice.

## Launch blockers and exact next action

The paid launch remains closed because the live Controller escalation adapter
is not implemented, the candidate tree is dirty, the project licence is
undecided and no pilot spending has been authorised. The offline runner blocker is closed by
`test/results/2026-09-17-realworld-runner.json` and its Markdown report. The
live calibration blocker is closed by the original record and
`test/results/2026-09-17-live-calibration-adjudication.json`.

The attempt-level live worker adapter is implemented and qualified without a
model call. It pins exact model and effort arguments, uses restricted safe mode,
disables MCP, persistence, permission prompting, Bash and subagents, runs only
inside the actor root, attributes identity from streamed root messages and
retains aggregate auxiliary billing. Fake transport cases cover an externally
accepted D01 repair, timeout, model mismatch and missing cost.

`tools/evaluation_live_episode.py` now sequences B0, B1 and B2, loads B1 routing
from the frozen bundle, runs public checks outside the worker, and exposes only
observable attempt history to policy decisions. It reserves and journals each
action before dispatch. A process resumed from an in-flight dispatch never
calls an adapter again; it retains the allowance and stops for reconciliation.
Scripted qualification covers B0 repair, B1 ladder escalation, B2's two-distinct-
hypothesis Controller trigger, missing cost and crash recovery. Hidden grading
runs only after policy termination. The evidence is
`test/results/2026-09-17-live-episode-integration.json` and the neighbouring
Markdown report. No model call was made.

Next, implement the live Controller adapter against this injected boundary and
qualify its outer-budget reconciliation without a paid call. Then review the
refreshed candidate freeze, settle the licence and source-state decisions, and
present the concrete W05 six-episode cost projection for operator authorisation.
Regenerate host isolation and the freeze immediately before any pilot execution.

## Next-session handoff

Keep **GPT-5.6 Sol, High**. Start the next project session with a Graft freshness
check. If its persistent MCP process reports an older snapshot after the final
deep build, start a fresh session so it reloads the rebuilt local graph.

The next bounded goal is W05's live Controller adapter and outer-budget
reconciliation. Preserve the dirty worktree and current freeze. Relevant files
are the live episode integration and evidence, live worker adapter, Controller,
both calibration records, the budget and acceptance tools, the isolation probe,
this readiness record and the main evaluation plan.

Keep **GPT-5.6 Sol, High** for preparation. Allow **2-4 hours** and estimate
**USD 3-8 direct OpenAI API equivalent** for development and review using the
same 2026-09-17 price source and broad cache assumptions as the preceding
handoff. The completed Claude calibration reported USD 0.0476572 API equivalent
plus a retained USD 0.05 uncertain allowance. Graft semantic-summary charges
remain additional and unknown because the CLI does not report billed usage.
