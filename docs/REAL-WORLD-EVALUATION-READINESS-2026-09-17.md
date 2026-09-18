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

The offline episode runner, live worker adapter, live Controller adapter,
policy executor, restart-safe integration and calibration are complete. The
complete remaining programme is approximately 1-2 engineer-days plus 2-4
hours of result review. Calibration
cost USD 0.0476572 API equivalent across terminal calls; the first run also
retains a separate USD 0.05 uncertain timeout allowance. These are Claude Code
list-price telemetry under the signed-in Max subscription, not an API invoice.

## Launch blockers and exact next action

The paid launch remains closed because the candidate tree is dirty, the project
licence is undecided and no pilot spending has been authorised. The offline runner blocker is closed by
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

`tools/evaluation_live_controller.py` now runs the quick Controller in an
evaluator-owned copy of the actor with read-only tools. Streamed per-role
messages prove the served task model while aggregate billing retains auxiliary
models and all token categories. The Controller's inner durable budget is the
source of the episode's known subtotal. The outer reservation settles only
when every inner call is final. Identity mismatch preserves measured cost and
blocks learning; incomplete accounting retains the outer allowance. The
Controller report, run directory and winning technique flow into observable
history and the routing ledger. Offline evidence is
`test/results/2026-09-18-live-controller-adapter.json`; no model call was made.

Next, review the refreshed candidate freeze, settle the licence and source-state
decisions, and present the concrete W05 six-episode cost projection for operator
authorisation. Regenerate host isolation and the freeze immediately before any
pilot execution.

The paid-pilot launch boundary is now qualified offline. It fixes the checkpoint
to D01 and D11 under B0, B1 and B2, caps the six episode reservations at USD 24,
and keeps USD 2 separate calibration headroom. Execution requires an exact
candidate-bound USD 26 authorisation file. Durable campaign state skips complete
episodes after restart and stops the sequence after the first accounting,
identity, event-chain, oracle-integrity or preflight failure. The qualification
evidence is `test/results/2026-09-18-pilot-preflight.json`; no model call was
made. The active authorisation file has deliberately not been created.

Release-candidate sealing on 2026-09-18 produced clean bundle stamp
`2026-09-18-98315bb`, refreshed the WSL2 isolation proof, and froze candidate
`0bca4b209ab553e6962b3a830ed2b14e831da5f5a63310f1c7f95b1c0934f7de`.
The concrete matrix and stop conditions are in
`docs/REAL-WORLD-PILOT-6-EPISODE-2026-09-18.md`. The remaining candidate
blockers are the project licence decision and exact paid-pilot authorisation.

The operator selected Apache-2.0 and approved the fixed USD 26 pilot envelope on
2026-09-18. The licence is shipped in the distribution without replacing a
consumer project's licence. Candidate and manifest hashes must be regenerated
after this authorised packaging change before the first paid call.

## Executed checkpoint, 2026-09-18

This readiness snapshot is superseded for the six-episode checkpoint. The
post-licence candidate was frozen as
`4fd79c1577ef97ccae9430d9b5f666edf72172d0973135baa3808642e6d08dcd`,
the exact approval validated, and the complete 48-check harness passed at
launch revision `1da7078`.

All six D01/D11 episodes under B0, B1 and B2 completed on their first
Sonnet-low attempt. Hidden grading, model identity, accounting, event chains,
actor boundaries and oracle protection passed in every case. Reconciled spend
was USD 0.139236601 of the USD 26 ceiling; no calibration headroom was used.
See `test/results/2026-09-18-realworld-pilot-checkpoint.md` and its neighbouring
JSON record.

The checkpoint did not distinguish the policies because no task reached a
fallback or Controller. The next launch boundary is a new manifest and approval
for the remaining 18 W05 episodes. The completed USD 26 authorisation does not
apply to them.

## Executed continuation and W05 decision, 2026-09-18

The continuation was frozen as candidate
`ce6cf4467b0ec462202f5cf419c5845aac471d30a9956fe3382b620b60660bec`
and separately authorised to a USD 74 ceiling. All 18 D03, D05 and D07-D10
episodes completed for USD 1.281458307. Identity, accounting, event chains,
actor boundaries and oracle protection passed in every episode; 7 hidden grades
passed and 11 failed. One B0 episode exercised an Opus fallback. No Controller
role ran.

Across all 24 pilot episodes, B0 accepted 5/8 tasks for USD 0.674036103, B1
accepted 4/8 for USD 0.368289403, and B2 accepted 4/8 for USD 0.378369402. B1
and B2 followed identical observed paths, so B1 is the conservative adaptive
finalist and B0 remains the fixed-fallback baseline. Proceed to offline W06;
do not change defaults or begin paid W07 work from this pilot alone. See
`test/results/2026-09-18-realworld-pilot-continuation.md` and its neighbouring
JSON record.

## Completed W06 corpus seal, 2026-09-18

The complete corpus now contains D01-D12 and H01-H12. Offline qualification
passed all 24 tasks, 144 original/solution/adversarial states and 72 attempted
acceptance-boundary attacks with zero model calls. The reserved split uses a
separate application ID for every task; H01/H02 retain their pinned Werkzeug
source cluster and H08/H09 retain the planned coordination comparison. Source,
licence, fixture and grader provenance are bound into the refreshed candidate.

The reserved author was not independently blind to arm-labelled pilot results:
the same session had access to them. The fixtures were constrained to the
frozen pre-pilot blueprints and were not revised around arm-specific failures.
This is a documented validity limitation, so H01-H12 are described as reserved
evaluation rather than uncontaminated model testing.

W07 remains closed. Its 32 development episodes require a new manifest that
fixes B0 and B1, frozen triggers and schedule, a current cost projection and a
new exact operator authorisation. Evidence is
`test/results/2026-09-18-realworld-corpus.json` and the neighbouring report.

## Qualified W07 launch profile, 2026-09-18

The offline launcher qualification now covers the fixed 32-episode development
comparison. D01-D12 run under B0 and B1, followed by the predeclared D03, D05,
D07 and D11 repetitions under both arms. Serial task pairs alternate their
first policy. Resume skips every completed episode, and authorization remains
bound to the exact candidate, manifest and ceiling.

Pilot policy means produce a USD 2.084651012 point projection. Applying the
highest pilot episode to all 32 runs produces USD 13.1220064. These estimates
do not replace the USD 128 episode envelope and USD 12 separate headroom. No
provider call starts until a clean candidate and manifest exist and the
operator explicitly approves their exact USD 140 ceiling.

## Executed W07 and qualified W08 profile, 2026-09-18

W07 completed all 32 development episodes for USD 1.376153606. All launch,
identity, accounting, event-chain, isolation, oracle and learning-eligibility
checks passed. B0 accepted 11/16 episodes for USD 0.568966604. B1 accepted
12/16 for USD 0.807187002, producing one paired acceptance win and no paired
loss. B1's higher total and per-accepted cost prevents a default change. B0
remains the baseline and unchanged B1 proceeds as the reserved candidate.

W08 preparation fixes 48 episodes over H01-H12, twice per policy, as sequences
57-104. Task pairs run serially and alternate which policy runs first. The W07
mean-cost projection is USD 2.064230409 and the all-episodes-at-the-W07-maximum
projection is USD 8.3018832. The exact exposure boundary remains USD 200. No
reserved provider call may run before a clean candidate, matching manifest and
new exact authorisation exist.

## Executed W08 and release-gate decision, 2026-09-18

All 48 reserved episodes completed for USD 1.053580005 with valid identity,
accounting, event chains, actor boundaries and protected oracles. B0 accepted
12/24 and B1 accepted 10/24. B0 had two paired wins, B1 had none, and 22 pairs
tied. B1 increased false successes and cost per accepted episode, completed
only five ordinary families twice and failed H11 in both repetitions.

The campaign evidence is valid, but B1 does not pass the fixed promotion gates.
B0 is the qualified W09 packaging target. No reserved outcome will be used to
retune B1. Release readiness remains blocked until B0 source and bundle parity,
clean installation, rollback documentation and the complete harness pass.

## Completed W09 packaging, 2026-09-18

B0 is the qualified source and bundle default: one `worker-sonnet-low` attempt,
one same-cell repair after observable failure, one `worker-opus-high` fallback,
then stop. The Controller, frontier and adaptive first-cell selection remain
available only for historical replay and the documented rollback. The W08
reserved outcomes selected between the frozen policies; they did not tune a new
trigger.

Source and bundle parity, the qualified-default regression and all seven
installer lifecycle cases pass. Rollback restores the earlier adaptive source
revision, rebuilds the distribution and uses the transactional installer to
restore the prior consumer bundle. The evaluation freeze verifies the exact B0
configuration and no longer carries a W09 completion blocker. There is no
remaining paid run in this evaluation programme. The complete offline harness
passes all 51 checks.
