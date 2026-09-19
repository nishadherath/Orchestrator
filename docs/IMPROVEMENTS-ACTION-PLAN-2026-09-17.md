# Improvements action plan

Date: 2026-09-17. Status: Stages 0-7 complete.
Owner: continued development sessions.

Successor status updated 2026-09-19: the
[Controller-aware routing programme](CONTROLLER-ROUTING-PLAN.md) has R0-R4
records and paused R5 scaffolding. The next planned work is
[worker remediation](WORKER-ROUTING-ACTION-PLAN-2026-09-19.md), followed later
by separately requested [Controller remediation](CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md).
Neither new programme has started. This completed roadmap remains the record
of the earlier programme.

This is the execution roadmap for the six recommendations in the
[audit summary](AUDIT-SUMMARY-2026-09-17.md). The operator has directed that
real-world evaluation be performed last. This plan supersedes the earlier
ordering, not the historical audit findings or results.

Start a fresh session with the
[Stage 1 handoff](../handoffs/2026-09-17-improvements-stage-1.md).
The Stage 1 session used GPT-5.6 Sol at high reasoning, as requested by the
operator. It made no paid `claude -p` calls.

## Order and dependencies

The original recommendation order becomes **1, 2, 3, 5, 6, 4**. Recommendation
1 is split into storage/accounting and learning corrections. Diagnostics needed
to validate those stages can be added early; the complete consumer experience
belongs after the record and verification contracts settle.

| Stage | Original recommendation | Result | Depends on | Engineering estimate |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Preparation | Reproducible baseline and protected existing work | None | 1-2 hours |
| 1 | 1: accounting | Versioned attempt records and safe concurrent updates | 0 | 1-2 days |
| 2 | 1: learning | Correct outcome eligibility, model partitions and projections | 1 | 0.5-1 day |
| 3 | 2: spending limits | Reserved budgets and complete failure accounting | 1-2 | 1-2 days |
| 4 | 3: acceptance verification | Evidence-backed completion and pending-work recovery | 1-3 | 0.75-1.5 days |
| 5 | 5: recurring context | Smaller stable instructions with measured load and retrieval | 1-4 | 0.5-1 day, plus optional probes |
| 6 | 6: installation and diagnostics | Reversible installation, clear diagnostics and reproducible bundle | 1-5 | 1-2 days |
| 7 | 4: real-world evaluation | Qualified defaults from complete-task evidence | All earlier stages | Re-estimate remaining evaluation work at entry |

Allow approximately **5-10 engineer-days before Stage 7**, with uncertainty
around migration, process interruption and Windows compatibility. These are
planning estimates, not elapsed model runtime or commitments. The first new
session should complete Stage 0 and a coherent part of Stage 1 in 4-8 hours.
Do not force a model/session change merely because a stage ended.

## Current state and rules that remain in force

- The audit is [ASSESSMENT-2026-09-17.md](ASSESSMENT-2026-09-17.md), findings
  R1-R9. Four defects have offline reproductions; other risks are labelled
  as inspection findings. Do not describe every risk as a reproduced incident.
- The last reviewed HEAD is `4fb4682`, branch `v1.0-beta`. There are substantial
  pre-existing uncommitted changes, including generated bundle files and local
  configuration. Inspect the current state; do not reset, clean, overwrite or
  commit unrelated work. Existing audit documents remain historical evidence.
- Graft MCP is mandatory in every session, resumed session and delegated task.
  Start with freshness, use scoped queries and pass the active checkout root
  through handoffs. See [GRAFT.md](GRAFT.md). Its savings estimates are not bills.
- Follow root `AGENTS.md` and `CLAUDE.md`. Consumer changes belong in `src/`
  and runtime tools, then reach `dist/` through the existing build process.
  Generated workers and bundled copies are not edited by hand.
- Use deterministic tests and fake runners first. No broad model sweep, routing
  threshold optimisation or real-world corpus construction before Stage 7.
- A new model, effort, session or subagent needs a checked concise handoff and
  operator notice with model, effort, cost and time. No delegation is required
  by this plan. Use the host's actual controls rather than Claude worker names
  as if they were Codex model settings.

## Stage 0. Establish the baseline

**Purpose:** make each later claim attributable to the change that caused it.

- [x] **0.1** Read the handoff and instructions, check Graft access/freshness,
  record branch/HEAD and inspect the dirty worktree. Save the relevant diff
  inventory; preserve existing local configuration and user changes.
- [x] **0.2** Run the existing offline harness and retain a dated result. Treat
  launcher/permissions failures separately from test failures. Do not run paid
  `claude -p` commands as a substitute for fixing the local test environment.
- [x] **0.3** Turn audit reproductions R1, R2, R3 and R5 into desired-behaviour
  regression cases. Do not copy assertions that deliberately confirm the bugs
  and then call their success a fix.
- [x] **0.4** Inventory ledger readers/writers and billing ownership through
  Graft call tracing. Identify task, attempt, parent and Controller boundaries.
  Write a short data-contract decision before migrating any consumer state.

**Files:** `tools/route.py`, `tools/system_controller.py`, `tools/claudep.py`,
`tools/handoff.py`, `src/System/schemas/RoutingLedgerEntry.schema.json`, relevant
existing selftests and `test/harness/check.py`.

**Gate:** a reproducible baseline, named defect tests and explicit migration
boundaries exist. A green legacy suite alone does not close an audit finding.

## Stage 1. Correct accounting and make ledger updates safe

Addresses R1, R4 and R6; supplies the record contract for R2, R3 and R7.

- [x] **1.1 Define a versioned attempt record.** Include stable task/attempt
  IDs, parent invocation ID, ordered attempt number, direct versus escalated
  start, requested cell, actual served model, effort evidence, bundle/policy
  version, timestamps, termination status and result. Keep provider usage and
  acceptance evidence as separate fields.
- [x] **1.2 Separate state from judgement.** Distinguish pending, running,
  completed, failed, cancelled and interrupted execution from claimed outcome
  and independently checked outcome. Missing usage, duration or identity is
  unknown, not zero. A zero-cost fake runner is a different case from missing
  production usage.
- [x] **1.3 Record costs at the invocation boundary.** Capture ordinary input,
  cache write/read, output including billed reasoning where reported, actual
  charge or price-derived estimate, currency, price snapshot and provenance.
  Preserve usage even when output parsing or schema validation fails.
- [x] **1.4 Define roll-up ownership.** Link parent, worker and Controller
  invocations. Record whether provider totals include descendants. Compute task
  totals once; do not add a parent aggregate to its already-included children.
  Preserve ambiguous totals as unresolved instead of allocating them equally.
- [x] **1.5 Make state updates transactional.** Prefer a small standard-library
  SQLite store for active attempts, events and later reservations, with JSONL
  import/export for compatibility and inspection. Confirm this choice against
  the existing interfaces before implementation. If retaining JSONL instead,
  enforce cross-process single-writer ownership around the entire read/modify/
  write and ID-allocation sequence; atomic rename alone is insufficient.
- [x] **1.6 Implement a reversible migration.** Provide a dry-run summary,
  byte-preserving backup, schema-version check and idempotent import. Preserve
  historical task totals and source rows. Import old per-attempt allocations
  as unknown when evidence cannot recover them. A migration must not fabricate
  model identities, validation results or timestamps.
- [x] **1.7 Preserve readers and recovery.** Adapt routing, handoffs, diagnostics
  and exports to one shared read layer. Retain old fixture/ledger support via
  explicit adapters; reject unsupported future versions with a useful message.
  Do not repeatedly rewrite historical records during ordinary routing.

**Mandatory regression cases:** five pending rows do not set cost/time means
to zero; USD 0.10 and USD 1.90 attempts remain distinct; missing cost differs
from measured zero; duplicate completion is idempotent; malformed output keeps
spending; two processes cannot lose updates or reuse IDs; interrupted migration
does not corrupt the original ledger; backup restores the exact original bytes.

**Likely files:** `tools/route.py`, `tools/claudep.py`,
`tools/system_controller.py`, schema files, `tools/handoff.py`, existing replay
and backtest harnesses. Add a small shared ledger module/schema only where it
removes duplicated ownership. Keep external runtime dependencies unchanged.

**Gate:** exact task/attempt ownership, reversible compatibility and concurrency
tests pass. Unknown historical costs remain visible. No consumer ledger is
silently upgraded while merely asking for a routing explanation.

**Completion evidence, 2026-09-17:** `docs/ATTEMPT-LEDGER-DESIGN.md` records
the contract and D84 records the storage decision. The project retained JSONL
because its readable artefact contract is useful here; operating-system locks
cover the complete transaction. `route.py --selftest` covers 19 scenarios and
`claudep.py --selftest` covers four subprocess outcomes. Before Stage 2, the
executable audit regressions reported R1 as passing and R2, R3 and R5 as
explicit expected failures. The complete offline harness passed 35
checks after the redistributable rebuild. No consumer ledger was migrated.

## Stage 2. Correct learning and economic projections

Addresses R2 and R5 plus the freshness part of R7.

- [x] **2.1 Define evidence eligibility once.** Success-rate updates use
  qualified outcomes; operational costs retain failures and aborted spending.
  Pending attempts never count as successes, failures or zero-cost completions.
  Infrastructure failures are labelled rather than silently treated as model
  incapability or removed from spending.
- [x] **2.2 Learn from every eligible starting cell.** A direct Opus failure
  must affect its direct-start estimate. Keep escalation performance conditional
  on the preceding failure population; do not blend it with direct-start data.
  Describe the remaining selection bias and sparsity in explanations.
- [x] **2.3 Partition and retire evidence deliberately.** Include actual model,
  policy/bundle compatibility and acceptance-contract version. Mark historical
  unknown identities explicitly. Add configurable evidence-age policy and an
  override visible in diagnostics; do not invent a decay constant as a measured
  optimum. Exact-identity evidence is the default for automatic learning.
- [x] **2.4 Price the policy that will execute.** Start projections at the
  selected cell; include routing, verification, likely retries and failed
  Controller runs where measured. Report intervals or unknown terms when data
  is insufficient. Avoid presenting successful-only averages as total economics.
- [x] **2.5 Keep fallbacks conservative.** Sparse or incompatible evidence
  falls back to documented priors/policy. Do not retune thresholds, add new
  routing rows or optimise the fifteen-cell fleet in this stage.
- [x] **2.6 Update provenance and documentation.** Keep measured, inherited and
  policy-selected values distinct. Document which historical records remain
  usable and why. Update `src/SELF-LEARNING.md` to match the implemented fields,
  including `prior_failure` and any retained unused field.

**Mandatory cases:** twenty direct elevated-cell failures lower its applicable
estimate; escalation failures change only the conditional population; pending
and unverified outcomes are excluded appropriately; alias/version changes do
not silently pool data; selected-start projections follow the chosen ladder;
missing Controller failure costs are exposed; empty-ledger routing still works.

**Files:** `tools/route.py` (`posterior`, `ledger_cell_means`, `plan`),
`tools/generate_priors.py`, `tools/handoff.py`, `src/routing_priors.json`,
`src/cost_table.json`, `src/SELF-LEARNING.md`, replay/backtest/selftests.

**Gate:** correct populations, attributable costs and honest uncertainty in
both machine output and explanations. Regenerate data only from its source;
do not manufacture new empirical priors before the deferred evaluation.

**Completion evidence, 2026-09-17:** D85 records the population and projection
contract. `route.py --selftest` now covers 23 scenarios, including all Stage 2
mandatory cases without model calls. R2 and R5 pass in the executable audit
regressions; R3 remains the sole expected failure for Stage 3. No threshold,
prior or routing row changed. Version-2 capability learning stays conservative
until Stage 4 produces acceptance-qualified records; measured terminal costs
remain usable meanwhile.

## Stage 3. Enforce spending limits across concurrent work

Addresses R3 using Stage 1's shared accounting boundary.

- [x] **3.1 Define the invariant.** Authoritative spent plus outstanding
  reservations must remain within the configured dispatch budget, including
  retries, Controller roles and continuations. Specify run versus project
  budget scope. A known budget breach stops new work; it does not erase history.
- [x] **3.2 Reserve before dispatch.** Atomically claim a unique reservation;
  concurrent generators must not read and spend the same remaining balance.
  Bound each invocation by its own reservation and any smaller provider limit.
- [x] **3.3 Account every exit path.** Reconcile success, exception, timeout,
  malformed response, cancellation and partial output. Release only known
  unspent funds. Keep ambiguous in-flight/unknown usage reserved until resolved.
- [x] **3.4 Make resume idempotent.** A restarted controller reads durable
  reservations, reconciles existing invocation IDs and cannot refund or charge
  an attempt twice. Stale work produces a diagnostic/recovery action.
- [x] **3.5 Define affordable stopping.** Preserve a useful partial result and
  remaining-work record when another invocation cannot be funded. Include
  token ceilings, elapsed-time limits and a cancellation path. Do not assume
  killing the local process instantly ends provider billing.
- [x] **3.6 Expose limits honestly.** Distinguish local dispatch enforcement
  from a verified provider billing ceiling. Document overshoot assumptions and
  discrepancies; avoid claiming a hard invoice limit from an untested flag.

**Mandatory cases:** USD 0.60 remaining never permits a USD 2 role allowance;
parallel reservations cannot oversubscribe; zero/negative remainder blocks
dispatch; failed calls retain costs; a lost reply does not refund unknown spend;
resume cannot repeat a side effect or reservation reconciliation.

**Files:** `tools/system_controller.py` (`Budget`, `LiveRoleRunner`, generation
dispatch and exception paths), `tools/claudep.py`, shared ledger/reservation
module, Controller schema/tests and consumer lifecycle documentation.

**Gate:** deterministic race, interruption and failure tests pass. Live billing
guarantees remain unverified until a separately projected compatibility probe;
offline proof is sufficient to proceed with the next implementation stage.

**Completion evidence, 2026-09-17:** D86 and
`docs/DISPATCH-BUDGET-DESIGN.md` define the per-run scope and durable allowance
contract. The `DISPATCH-BUDGET` harness gate covers 28 deterministic tests,
including process races, actual process death, partial costs, cancellation,
deadline expiry during admission, duplicate settlement and preserved parallel
output. R3 now passes alongside R1/R2/R5. The complete harness has 36 checks.
Recovery reopens accounting and regenerates reports without replaying calls;
automatic continuation of pipeline phases is intentionally not provided.
Provider invoice enforcement and live token-setting behaviour remain unverified.
No paid Claude tests, routing threshold changes or consumer migrations occurred.
The redistributable contains the reservation module and recovery commands.

## Stage 4. Require acceptance evidence and recover incomplete records

Addresses R7 and the operational part of R8.

- [x] **4.1 Define the acceptance contract before dispatch.** Record required
  outputs, constraints, verification command or rubric and scope. Separate
  worker-reported success, verified success, failure and incomplete/blocked.
- [x] **4.2 Attach evidence to the exact artefact.** Store verification command,
  exit status, result digest/path, relevant revision/diff identity and timestamp.
  Successful old tests cannot validate a later edited patch. Validate evidence
  references and provenance rather than trusting a supplied `verified=true`.
- [x] **4.3 Make completion reconciliation unavoidable in owned code paths.**
  Controller and harness exits write terminal or interrupted records. Recovery
  lists pending attempts and asks for resolution without silently converting
  them to failure or success. State clearly which external Claude lifecycle
  events remain observable only through hooks/instructions.
- [x] **4.4 Restrict automatic learning.** Only acceptance-qualified outcomes
  enter success learning. All measured spending still enters cost reporting.
  Prose-only work without an executable oracle uses a visible rubric and, when
  needed, an explicit human review state; it is not automatically a verified pass.
- [x] **4.5 Preserve permission boundaries.** A false technical rationale does
  not revoke an explicit user constraint. Keep this rule in verifier acceptance
  and escalation guidance; do not reward unauthorised fixes in historical or
  future fixtures.
- [x] **4.6 Show actionable recovery.** A concise status summary names missing
  results, evidence mismatch, unresolved cost and the next useful command.
  Prepare the read interface needed by Stage 6 diagnostics.

**Mandatory cases:** claimed pass with a failing check; absent/stale evidence;
changed artefact after verification; duplicate terminal event; crash before
completion write; intentionally blocked work; missing hook output; a synthetic
attempt to weaken a protected acceptance test.

**Files:** routing completion/recovery code, Controller boundaries,
`src/LIFECYCLE.md`, `src/ROUTING.md`, acceptance schema and offline tests.

**Gate:** false success cannot automatically train the router, and every owned
exit path leaves a diagnosable state. Document evidence limits; test evidence
is not a guarantee of semantic correctness on arbitrary work.

**Completion evidence, 2026-09-17:** D87 and
`docs/ACCEPTANCE-EVIDENCE-DESIGN.md` record the contract and limits.
`test/harness/acceptance_tests.py` passes 10 offline cases covering every
mandatory case above. Route selftest passes 23 scenarios, Controller dispatch
passes 29 tests, and the complete harness passes 37 checks after rebuilding the
redistributable. No model or provider call was made.

## Stage 5. Reduce recurring context without weakening the contract

Implements original recommendation 5 after costs and outcomes are trustworthy.

- [x] **5.1 Inventory what is loaded.** Identify always-loaded charter text,
  repeated worker/persona instructions, Controller role material, tool schemas
  and task-specific evidence. Measure bytes and estimate tokens with a labelled
  method; use real usage where available. Keep repository-development and
  installed-consumer contexts separate.
- [x] **5.2 Create a requirements map.** Preserve Graft use, permissions,
  acceptance, budgets, recovery and handoff requirements. Map each mandatory
  behaviour to its retained instruction, load trigger and regression case.
- [x] **5.3 Shorten the stable core.** Remove duplicated explanations; keep
  operating rules concise and move reference material behind explicit retrieval
  instructions. Preserve stable prefix ordering. Avoid adding an extra model
  call simply to decide which short document to load.
- [x] **5.4 Make retrieval reliable.** State when to load each specialist brief;
  verify those files exist in a clean `dist/` install. Ensure a child and resumed
  session can find the relevant contract independently of parent memory.
- [x] **5.5 Measure before/after.** Record initial load, repeated-turn input,
  cache creation/read, billed output and verification outcomes. Static text
  reduction is not proof of monetary savings or unchanged model behaviour.
- [x] **5.6 Retain a rollback.** Keep baseline prompt hashes and compare existing
  small fixtures before publishing changed behavioural instructions. Any paid
  compatibility probes use the fixed existing corpus, a predeclared call count
  and projected budget; they are not the deferred real-world campaign.

**Files:** `src/CLAUDE.template.md`, `src/WORKER_PERSONA.md`,
`src/System/ROLES.md`, `src/LIFECYCLE.md`, prompt assembly/generation tools,
context/cost probes, consumer README and generated bundle.

**Gate:** a smaller measured static load, no missing mandatory contract and
clean offline checks. Mark live savings/behaviour unverified if probes have
not run. Do not change TTLs, model selection and context structure together.
Unverified prompt changes can remain a candidate until Stage 7.

**Completion evidence, 2026-09-17:** D88,
`docs/CONTEXT-REDUCTION-DESIGN.md`, the immutable baseline and dated measurement
record the method, hashes, requirements and limits. The installed standing
orchestrator estimate fell 69.5 per cent, repository-development instructions
71.7 per cent, a selected worker 30.1 per cent on average, and each Controller
role brief by 378 estimated tokens. CONTEXT passes six offline cases; standalone
bundle preflight passes; the complete harness passes 38 checks. No model or
provider call ran, so billed savings and behavioural equivalence remain
unverified.

## Stage 6. Make installation reversible and diagnostics useful

Implements original recommendation 6 and documentation finding R9.

- [x] **6.1 Specify ownership.** List files and configuration keys owned by the
  bundle. Preserve unrelated user settings, permissions, MCP servers and hooks.
  Treat same-name conflicting entries as conflicts rather than overwriting them.
- [x] **6.2 Add a dry-run install/update path.** Show the target, changed keys,
  conflicts and backup location before application. Validate configuration
  before replacement; refuse malformed input without touching it.
- [x] **6.3 Add backup and rollback.** Record bundle/version and pre-install
  hashes. Restore owned changes safely. Refuse a blind rollback if the operator
  has subsequently edited those values; present the conflict and recovery path.
- [x] **6.4 Make repeat installation idempotent.** Reapplying the same bundle
  must not duplicate hooks, permissions or MCP entries. Test upgrades from an
  older fixture and uninstall/rollback with preserved unrelated configuration.
- [x] **6.5 Expose concise status and detailed explanation.** Prefer extending
  existing status/preflight commands over adding a dashboard. Show actual versus
  requested model, unresolved attempts, acceptance evidence, spent/reserved/
  unknown amounts, stale priors and Graft availability. Provide stable JSON
  output for automation and deeper detail behind an explain option.
- [x] **6.6 Verify a clean consumer.** Install from immutable `dist/` into an
  empty disposable project, then exercise routing, fake work, verification,
  recording, recovery and rollback. Test paths with spaces on Windows. Include
  Linux only when actually exercised; do not infer portability from one host.
- [x] **6.7 Establish release checks.** Run the offline suite in CI on available
  supported platforms, regenerate workers/bundle, verify source equivalence
  and record a clean build stamp for a release candidate. Check licence/notice
  coverage and exclude personal ledgers, logs, credentials and machine paths.
  Do not publish a release or choose an unresolved project licence implicitly.
- [x] **6.8 Correct current documentation.** Update stale check counts, handoff
  counts and learning-field descriptions from a canonical generated or dated
  status source. Leave historical results intact. Explain remaining live-model
  and compatibility uncertainty in the release notes.

**Files:** `src/README.md`, `src/CLAUDE.template.md`,
`src/settings.fragment.json`, `src/preflight.py`, `src/commands/workers.md`,
`tools/build_dist.py`, an installer helper if needed, CI workflow and tests.

**Gate:** clean install, repeat install, upgrade conflict, rollback conflict,
malformed settings and unrelated-settings preservation tests pass. Diagnostics
read authoritative data without altering it. Source and bundle match. Any
publication/licence decision remains an explicit operator action.

**Completion evidence, 2026-09-17:** D89 and
`docs/INSTALLATION-AND-DIAGNOSTICS-DESIGN.md` define ownership and semantic
rollback. `tools/install.py` and the generated manifest implement
plan/apply/status/uninstall/rollback. Seven install cases and four diagnostics
cases pass, including a disposable Windows path containing spaces and an
installed routing, fake-work, acceptance, recording and recovery path. The
offline workflow defines Windows and Ubuntu jobs; Ubuntu was not run in this
session. `tools/release_check.py` leaves licence, clean release stamp and
publication as explicit operator actions.

## Stage 7. Real-world evaluation, deliberately last

- [x] **7.1** Review Stages 0-6 evidence and carry completed prerequisites into
  [REAL-WORLD-EVALUATION-PLAN.md](REAL-WORLD-EVALUATION-PLAN.md). Map completed
  work to W01 and relevant W02/W04/W09 parts; do not repeat or charge for it twice.
- [x] **7.2** Re-estimate the remaining corpus/harness work and current API prices.
  Freeze bundle, model identities, policies, acceptance and accounting first.
- [x] **7.3** Follow that plan's offline qualification, eight-task pilot,
  development comparison and reserved evaluation, with its stop conditions.
- [x] **7.4** Promote only supported policy changes and aggregates; preserve a
  simple fallback when the evidence is weak. Rebuild and requalify the bundle
  after any evaluation-driven change.

The earlier campaign proposal is 104 episodes, a USD 110-220 conditional
working estimate and USD 440 allocation, including a USD 100 pilot allocation.
These are not fresh quotes or spending authorisation. The project's paid-run
rule requires approval before a projected campaign above USD 100; dividing it
into stages does not bypass that rule. No part of this stage starts merely
because another stage has finished during the current planning request.

Stage 7.1 and 7.2 implementation note, 2026-09-17: the plan maps completed
Stage 1-6 evidence to Gates A-E and W01/W02/W04/W09. Current official prices,
three exact policy documents and the relevant bundle, acceptance and ledger
hashes are captured by `tools/evaluation_freeze.py`. D01 and D11 established
the first offline grader path; the Stage 7.3 note below records its current
state.

Stage 7.3 offline progress note, 2026-09-17: D03 and D05 join D01 and D11 as
ready fixtures. All four accept two correct implementations, reject the
original and three wrong repairs, and reject public-check deletion, weakening
and shadow-oracle attacks. A recorded WSL2 probe proves actor/evaluator file
separation on this host. D07-D10 and the episode runner remain. No paid Claude
evaluation call was made.

Stage 7.4 offline progress note, 2026-09-17: D07 and D08 are now qualified.
D07 exercises bounded Node.js queue shutdown using pinned p-limit semantics;
D08 exercises a durable SQLite backfill, legacy writes and final schema
enforcement. Six pilot fixtures now pass the complete variant and integrity
matrix. D09, D10 and the episode runner remain. No paid Claude evaluation call
was made.

Stage 7.5 offline progress note, 2026-09-17: D09 and D10 complete the eight-task
pilot corpus. D09 coordinates an immutable result-type migration across every
consumer and entry point. D10 grades a matched pair where repository evidence
disproves the same diagnosis but only one task has explicit authority to edit
the file. The freeze now names missing episode-runner replay evidence as a
launch blocker. W03 is complete and W04 is next. No paid Claude evaluation call
was made.

W04 completed 2026-09-17. `tools/evaluation_runner.py` now checkpoints each
episode through reservation, dispatch, worker commit, visible verification,
termination, external grade, reconciliation and completion. The append-only
event journal is hash-chained, a committed interruption resumes without a
second dispatch, and every terminal episode writes a schema-valid version-2
routing record. Nine fake-worker paths across B0, B1 and B2 replay identically
from two clean campaign roots. Known fake spend totals USD 1.40; the two
unknown-cost paths retain USD 8.00 and remain ineligible for learning. Evidence
is in `test/results/2026-09-17-realworld-runner.json` with a readable Markdown
report. No Claude call was made. The next work is live instrumentation
calibration and then the separately authorised W05 pilot checkpoint.

Live calibration completed 2026-09-17. The preserved first run spent USD
0.031453 API equivalent, retained a USD 0.05 uncertain timeout allowance and
passed every instrumentation check except its initial aggregate model-identity
predicate. The USD 0.0162042 adjudication used streamed root and forwarded
worker messages: both were `claude-sonnet-5`, while Haiku 4.5 appeared only as
unattributed auxiliary billing. The freeze now validates both records and no
longer lists calibration as a blocker. Graft review confirmed that W04 exposes
only the qualified fake-worker path, so the freeze now separately blocks launch
until a live attempt path and end-to-end policy evidence exist. W05 remains
unstarted and requires its own concrete cost projection and operator
authorisation.

W05 adapter progress, 2026-09-17: `tools/evaluation_live_worker.py` now owns one
restricted Claude attempt. Its no-cost qualification applies a correct D01 edit
through fake transport, runs public and external hidden checks, validates exact
Sonnet-low arguments and covers timeout, model mismatch, auxiliary billing and
missing-cost outcomes. This closes the attempt-adapter blocker only. The freeze
now separately blocks launch on policy sequencing and restart-safe live episode
integration.

W05 integration progress, 2026-09-17: `tools/evaluation_live_episode.py` now
implements deterministic B0/B1/B2 sequencing around the attempt adapter. B1
loads its route from the frozen bundle. The policy boundary receives only the
policy, route plan and observable history. Every action is reserved and journalled
before dispatch; recovery from an in-flight action retains its allowance and
never calls the provider again. Scripted no-cost cases prove B0 floor repair,
B1 ladder escalation, B2's two-distinct-failure Controller trigger, external
grading after termination, missing-cost retention and crash recovery. The
freeze now records policy execution and restart safety as qualified. At that
point live Controller execution remained a separate launch blocker. No paid
pilot episode has run.

W05 Controller adapter progress, 2026-09-18:
`tools/evaluation_live_controller.py` now runs the quick Controller in a
separate evaluator-owned copy of the actor. Role calls use streamed output,
exact served-model checks and read-only repository tools. The adapter rolls the
Controller's durable per-role budget into the episode's single outer
reservation, returns the report as worker guidance, and records its run path
and winning technique. Offline cases cover exact aggregate cost and tokens,
auxiliary billing, model mismatch, incomplete inner accounting, failure before
budget creation and actor immutability. `tools/evaluation_live_episode.py`
enables the adapter by default and blocks learning on Controller identity or
accounting failure. Evidence is
`test/results/2026-09-18-live-controller-adapter.json`; no paid call ran. The
remaining launch decisions are source cleanliness, project licence and explicit
pilot spending authorisation.

W05 paid-pilot preflight progress, 2026-09-18: the six-episode matrix is now an
executable candidate-bound manifest rather than a manual procedure. D01 and D11
each run once under B0, B1 and B2. Episode reservations total at most USD 24;
USD 2 remains separate calibration headroom. The launcher requires an exact
USD 26 operator authorisation, checkpoints between episodes, resumes without
repeating complete episodes and stops after the first instrumentation,
accounting, identity or integrity failure. Offline qualification uses six fake
episodes and makes no model calls.

W05 paid checkpoint result, 2026-09-18: the operator selected Apache-2.0,
approved the exact synthetic payload, Anthropic destination and USD 26 ceiling,
and all six episodes completed. Each passed public and hidden checks on its
first Sonnet-low attempt. Identity, accounting, event chains, actor boundaries
and protected oracles all reconciled; all six records are learning-eligible.
Known spend was USD 0.139236601 and calibration headroom was unused. Aggregate
billing retained Haiku 4.5 auxiliary overhead. Because every policy stopped at
the common floor, this is an instrumentation pass rather than policy-comparison
evidence. The result is
`test/results/2026-09-18-realworld-pilot-checkpoint.json`. Stage 7.3 remains
open for the remaining 18 W05 episodes and later comparisons; a new exact
authorisation is required before any further paid call.

W05 continuation preparation, 2026-09-18: the launcher now exposes a separate
`continuation-eighteen` profile for D03, D05 and D07-D10 under all three
policies. Episodes 7-24 have USD 72 of reservations plus USD 2 headroom. The
offline preflight covers both profiles, rejects cross-profile approval and
resumes complete campaigns without redispatch. The continuation manifest must
be frozen against a clean candidate before requesting its exact USD 74 approval.

W05 pilot decision, 2026-09-18: the separately authorised continuation
completed all 18 episodes for USD 1.281458307. All identity, accounting,
event-chain, actor-boundary and oracle checks passed. Across the complete
24-episode pilot, B0 accepted 5/8 tasks for USD 0.674036103, B1 accepted 4/8 for
USD 0.368289403, and B2 accepted 4/8 for USD 0.378369402. B1 and B2 took the
same observed path on every task, so B1 remains the conservative adaptive
finalist and B0 remains the required baseline. The measured B1 cost per
accepted result was 32 percent below B0, satisfying the plan's cost-benefit
condition to proceed to offline W06. No default changes are supported yet,
Controller execution remains live-unverified, and no W07 call is authorised.
Evidence is `test/results/2026-09-18-realworld-pilot-continuation.json`.

W06 corpus completion, 2026-09-18: D02, D04, D06 and D12 complete the
development split; H01-H12 complete the reserved split. Each task has an issue,
actor repository, public checks, external hidden oracle, two accepted solutions
and three rejected plausible wrong implementations. The zero-call qualification
passed 24 tasks, 144 states and 72 protected-boundary attacks. Catalogue
invariants enforce the exact split, reserved application independence, the
Werkzeug source cluster and the H08/H09 coordination comparison. Strict reserved
author blinding is not claimed because the authoring session could see pilot
outcomes; the fixtures remained constrained to the frozen pre-pilot blueprints.
W07 remains unauthorised. Evidence is
`test/results/2026-09-18-realworld-corpus.json`.

W07 preparation, 2026-09-18: the launcher now defines the exact 32-episode
development schedule for B0 and B1. D01-D12 run once per arm; D03, D05, D07 and
D11 then run once more per arm. Policy-first order alternates across pairs, and
historical approvals cannot cross into this profile. Offline preflight passes
with zero model calls. The measured point projection is USD 2.084651012 and the
all-episodes-at-the-pilot-maximum extrapolation is USD 13.1220064. Execution
remains blocked until the clean candidate, manifest and exact USD 140 approval
are present.

## Verification, records and stage completion

For every implemented stage:

1. Add focused behavioural regression cases before fixing consequential defects.
   Use fake invocations for cancellation, concurrency and missing billing data.
2. Run the affected selftests and the existing offline harness. Retain results
   under `test/results/` with the tested revision and working-tree qualification.
3. Regenerate affected workers from their source, then rebuild `dist/` through
   its normal gate. Verify resolved build/delete paths remain within the project.
4. Check the resulting diff, schema compatibility, migration/rollback evidence
   and source/bundle equivalence. Do not hand-edit generated files to pass checks.
5. Update this plan's stage status with result paths and audit findings closed.
   Record architectural decisions in the existing decision log. Check only
   completed items; explicitly record partial completion and unverified claims.
   Keep the root charter's roadmap/handoff pointer current when handing over.
6. Commit coherent changes if the implementation session is authorised to do so;
   keep unrelated earlier work separate. Do not reset it to obtain a clean tree.
7. If a fresh session/model/agent is needed, write and validate the next handoff.
   Carry decisions and exact next action, not the full conversation.

## First-session cost and operator instruction

Recommended development model: **GPT-5.6 Sol, high reasoning**. This is a
cost-conscious engineering judgement for consequential but bounded ledger
work, not a measured claim that it is the cheapest capable model here. Keep
one session initially; avoid delegation overhead and concurrent edits to the
shared contract. No host settings were changed by this document.

[Official OpenAI model pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
checked 2026-09-17: per million tokens, ordinary input USD 4, cached input
USD 0.40, cache writes USD 5 where billed separately, output USD 20. The model
page lists high effort. The current Codex host also exposes that model/effort.
This projection assumes standard API rates and individual requests below the
documented long-input surcharge threshold; reprice the actual service tier.

For Stage 0 and the first Stage 1 work unit, assume total disjoint categories
of 100,000-400,000 ordinary input tokens, 50,000-200,000 cache-write tokens,
300,000-1,200,000 cached-input tokens and 30,000-120,000 output tokens including
billed reasoning. The calculated token subtotal is **USD 1.37-5.48**. Add
30 percent contingency and round to a **USD 2-8 direct API-equivalent estimate**.
This assumes local filesystem/Graft tools without separate model enrichment
charges; unknown service charges require repricing, not an assumption of zero.
Actual cache reuse, usage and subscription billing are not known in advance.

Elapsed first-session work: **4-8 hours**, sequential, including investigation,
implementation and tests. Paid Claude benchmark/Controller calls: **none** in
that work unit. The separate full evaluation allocation is deferred.

Paste this into a fresh session in this project after selecting the model:

```text
Read handoffs/2026-09-17-improvements-stage-1.md first, then AGENTS.md and
docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md. Use Graft MCP as required.
Implement Stage 0 and Stage 1 in order, preserving all existing uncommitted
work. Start with the audit defect regressions and the versioned attempt/storage
contract. Use offline fake-runner tests; do not start paid evaluation.
Update the action plan with evidence and a concise next-session handoff when
needed. Keep real-world evaluation last. Do not claim it has been completed.
```

## Planning-deliverable verification

The offline harness returned 33 passes, zero failures and zero skips after
these planning changes; its handoff check covered nine files. The new handoff
also passed `tools/handoff.py check` directly. Graft reported both graphs in
sync. Documentation links, cost arithmetic and referenced entry files were
checked; `git diff --check` passed. These checks validate this handoff and the
existing repository invariants, not implementation of any unchecked action.

## W07 result and W08 preparation, 2026-09-18

All 32 development episodes completed with valid instrumentation for USD
1.376153606. B0 accepted 11/16; B1 accepted 12/16, with one paired acceptance
win and no paired loss. B1 cost 42 percent more in total and more per accepted
episode, so B0 remains the baseline, unchanged B1 remains the candidate, and
defaults remain unchanged.

W08 is fixed before reserved results are inspected: H01-H12 run twice under
both policies in 48 serial episodes with alternating first-policy order. Its
W07-mean projection is USD 2.064230409, its observed-maximum extrapolation is
USD 8.3018832, and its binding authorisation ceiling is USD 200. W08 is ready
for a clean freeze and exact approval; no reserved call has run.

## W08 result and W09 decision, 2026-09-18

All 48 reserved episodes completed with valid instrumentation for USD
1.053580005. B0 accepted 12/24 and B1 accepted 10/24. B0 recorded two paired
wins and no paired loss; B1 increased false successes and cost per accepted
episode. Both policies completed five ordinary task families in both
repetitions, below the required ten, and neither passed H11 twice.

W08 execution is complete, but B1 failed the predeclared promotion gates. W09
will package B0 as the qualified default, preserve B1 as a rejected experimental
record, rebuild the distribution, verify a clean consumer installation and
document rollback. No policy tuning may use the reserved outcomes.

## W09 completion, 2026-09-18

B0 is now the source and distributable default. Every assessment starts at
`worker-sonnet-low`; an observable failure permits one same-cell repair, then
one `worker-opus-high` fallback, then stops. Project history remains diagnostic
and cannot skip the floor, activate another rung, invoke the Controller or add
an attempt. The reserved result was not used to invent or tune a trigger.

Source and bundle routing priors and router implementations match. Focused
regressions cover every assessment bucket, hostile ledger history, prior-failure
inputs and CLI resolution. The existing seven-case installer suite passed clean
install, repeated install, upgrade, uninstall and semantic rollback, including
preservation of unrelated configuration and refusal on owned drift. The former
adaptive machinery and Controller remain in the package for historical replay
and an explicit rollback; they are outside the qualified policy.

The content-addressed freeze now verifies this configuration instead of carrying
an unconditional W09 blocker, and the complete offline harness passes all 51
checks. Stage 7 is complete. Future policy work requires a separately declared
hypothesis and evaluation; it is not part of this release.
