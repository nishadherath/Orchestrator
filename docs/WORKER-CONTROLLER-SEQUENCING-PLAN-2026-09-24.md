# Worker-first remediation: dependency corrections and execution plan

Date: 2026-09-24. Status: **N0A through N2 complete for offline review; N3 pending**.
See [N0A evidence](stage-results/worker-n0a.md),
[contract v2](WORKER-EXECUTION-CONTRACT-v2.md) and the
[N1 result](stage-results/worker-n1.md) and
[N2 result](stage-results/worker-n2.md).
Planning baseline: HEAD `a70e311`; tracked worktree clean before this planning
change. N0 produced a contract and stage record; N1 has now implemented its
offline executor while all X stages remain unstarted. The preceding dependency
review passed the offline harness and
confirmed current Graft semantic and wiring indexes. These checks establish
the current baseline, not correctness of the proposed implementation.

## 1. Decision, scope and document precedence

Complete worker remediation before experimental Controller remediation. Add
one bounded contract-amendment stage, **N0A**, before N1. No Controller feature
implementation is needed to unblock worker work. A worker candidate need not
beat B0 for the mechanically complete worker platform to ship or for X0 to begin.

This document governs sequencing and the specific amendments below. The
[worker plan](WORKER-ROUTING-ACTION-PLAN-2026-09-19.md) and
[Controller plan](CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md) retain their
detailed requirements and stage numbers. The
[execution protocol](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md) governs
review, handoffs and spending. Where older start instructions conflict, start
with N0A. This is a plan, not approval to execute later stages or promote policy.

The original N0 record and execution contract remain historical design
evidence. N0A must version its amendment and describe changed assumptions;
do not retrospectively claim that the N0 contract already satisfied them.
Keep historical paid artefacts, manifests, authorisations and result hashes.

Consumer behaviour is unchanged by this planning update. No source or bundle
change is required until implementation modifies a shipped component. Do not
rebuild the redistributable solely to include development planning documents.

## 2. Model selection and stage protocol

Use **GPT-5.6 Sol / High** for bounded implementation and campaign operation.
Use **GPT-6 Astra / High** for N0A architecture, N7 worker adjudication, X0
revalidation and X7 Controller adjudication. These are engineering choices,
not measured claims that one model outperforms another on this repository.
Both named models expose High in the current host tool metadata; check the
receiving session's actual setting. No model has been switched by this plan.

High is sufficient as the planned effort level. Do not use every effort
level merely to fill a development matrix. Qualification of the product's
fifteen Claude worker cells is a separate experiment. Do not substitute a
Claude cell for the development session's OpenAI model.

Every stage follows these steps:

1. Read its checked handoff and preceding stage result. Verify branch, HEAD
   and local changes. Read project instructions. Check Graft freshness in
   this session, then use scoped retrieval before repository discovery.
2. Record the stage's inputs, decisions, proposed files and exit checklist.
   Reproduce observed implementation defects before fixing them. For design
   requirements, write behavioural acceptance cases before implementation.
3. Complete only this stage. Use deterministic checks and fake transports
   until the stage explicitly requires a paid experiment. No subagents are
   scheduled. Record unsupported host capabilities instead of claiming them.
4. Run focused checks and the existing offline harness. For shipped changes,
   build via `tools/build_dist.py` using its required gates, then verify the
   installed consumer path. Do not hand-edit `dist/` or duplicate full runs
   without a changed input or unresolved failure.
5. Write `docs/stage-results/worker-<stage>.md` or
   `docs/stage-results/controller-<stage>.md`. Record completed and unmet
   criteria, commands/results, requested and observed model/effort, changed
   files, costs, limitations, rollback and exact next action.
6. **Stop for operator review.** Before a model/effort switch, fresh session
   or any agent launch, create a ten-section handoff using
   `tools/handoff.py new`, complete it and run `tools/handoff.py check`.
   Report its path, target settings, cost and elapsed-time range. Do not
   create every future handoff now; it must contain actual preceding results.

Keep the same model/session across suitable consecutive stages after operator
direction; a stage boundary alone does not require a context reset. If Sol
encounters an unresolved ownership contract or repeated failure of the same
invariant, provide a minimal reproduction and a bounded Astra High review
handoff. No silent effort escalation or speculative multi-agent work.

## 3. Dependency map and ownership

| Producer | Consumer | Required contract or evidence |
| :--- | :--- | :--- |
| N0A | N1 and later X2/X4 | Lifecycle, task lineage, one owner per mutable record, extension boundary |
| N1 | N2-N4; X2/X4 | Durable executor, host adapter, admission, receipts and accounting |
| N2 | N3/N4; X4 | Managed delegation, dependencies, limits and cancellation |
| N3 | N4; X3/X4 | Public-input assessor, explicit selector, override provenance |
| N4 | N5/N6; X1/X3 | Campaign lifecycle, complete dependency inventory, independent grading |
| N5 | N6; X5 | Capability evidence reusable only for compatible model/host/settings |
| N7/N8 | X0 onward | Actual qualified default and installed execution baseline, possibly B0 |
| X3 | X4 | Qualified corpus/grader and fake boundary checks, not completed Controller integration |
| X4 | X5/X6 | Integrated production path for live Controller comparisons |

Only the worker executor owns overall task progression. The selector advises;
the host adapter performs one admitted action; the budget module owns its
accounting records; the acceptance module owns verification. X4 adds a
Controller step that returns evidence within an allocated allowance. It must
not add a second overall scheduler, final acceptor or independent root budget.

Worker stages do not repair Controller algorithms, role mappings, invocation
counts, automatic invocation or interactive Controller controls. Those stay
with X1-X4. Necessary shared-module changes must preserve existing callers.
N1 may adjust offline test fixtures to distinguish historical evidence from
current-code tests, without editing frozen manifests or Controller runtime.
No old R5 campaign is relaunched during the worker programme.

## 4. Stage schedule

Each row is a separate operator checkpoint. Costs use the units in section 8.
Time estimates are planning ranges, not execution guarantees.

| Stage | Main deliverable | Prerequisite | Model / effort | Engineering hours | Cost unit |
| :--- | :--- | :--- | :--- | ---: | :--- |
| N0A | Correct and version shared contracts | Operator start; N0 review | Astra / High | 2-4 | R |
| N1 | Durable executor and installable adapter | Accepted N0A | Sol / High | 5-9 | I |
| N2 | Managed delegation | N1 | Sol / High | 4-8 | I |
| N3 | Assessor and worker selector | N1-N2 | Sol / High | 4-8 | I |
| N4 | Real corpus and protected campaign runner | N1-N3 | Sol / High | 6-12 | I |
| N5 | Cell screen and development tuning | N4; spend notice | Sol / High | 2-4 | B |
| N6 | Frozen unseen worker comparison | N5; spend notice | Sol / High | 2-4 | B |
| N7 | Independent worker adjudication | N6 result, including inconclusive | Astra / High | 2-4 | R |
| N8 | Worker consumer release preparation | N7 decision | Sol / High | 3-5 | I |
| X0 | Revalidate Controller defects/contracts | N8; explicit deferred start | Astra / High | 2-4 | R |
| X1 | Controller campaign integrity | X0; N4 | Sol / High | 3-6 | I |
| X2 | Generator assignments and task-wide admission | X1; N1/N0A contracts | Sol / High | 4-8 | I |
| X3 | Controller corpus and unbiased grading | X2; N3/N4 | Sol / High | 6-12 | I |
| X4 | Integrated Controller workflow and controls | X2/X3; N1-N3 | Sol / High | 5-10 | I |
| X5 | Controller pilot and development evidence | X4; reusable N5 evidence; spend notice | Sol / High | 3-6 | B |
| X6 | Frozen unseen Controller comparison | X5; spend notice | Sol / High | 2-4 | B |
| X7 | Independent Controller adjudication | X6 result | Astra / High | 2-4 | R |
| X8 | Controller consumer release preparation | X7 decision | Sol / High | 3-5 | I |

## 5. N0A: bounded amendment before implementation

Inputs: the [N0 contract](WORKER-EXECUTION-CONTRACT.md),
[N0 result](stage-results/worker-n0.md), both programme plans and the source
anchors in section 9. Output: a versioned contract amendment, an ownership
table, corrected acceptance cases, `docs/stage-results/worker-n0a.md` and a
fresh N1 handoff. Preserve the prior N0 result and explain the amendment there
with an additive pointer. Do not implement N1 or change Controller runtime.

### A. Separate task and attempt lifecycles

- Define attempt completion independently from task completion. After a
  verified unsuccessful attempt, permit a next-attempt state while the
  authorised policy still allows repair/fallback. Freeze the exact transition
  table and the owner/lock held across each transition.
- Preserve B0: Sonnet Low, one Sonnet Low repair after observable failure,
  then Opus High. Stop on verified acceptance. Infrastructure, permission,
  identity and accounting failures do not consume a speculative quality retry.
- Define waiting-for-review, blocked and uncertain states precisely. A
  required review must have a documented resolution path without pretending
  that a reviewer change is a new task input.
- Keep accepted and deliberately terminal stopped records immutable. An
  append-only accounting reconciliation does not grant execution permission.
  A lost receipt never causes automatic replay of the same invocation.
- Prevent a new revision or restart from escaping an unresolved in-flight
  writer, reservation, task lock or cancellation decision.

Exit evidence: walk through success on attempts 1/2/3, exhaustion, operator
stop, pending review and crashes before/after dispatch. Every event must have
one legal transition and owner; no repair requires a fabricated revision.

### B. Freeze identity, override and budget semantics

- Distinguish stable task identity, immutable input/acceptance revision,
  per-attempt decision, invocation id and authorised budget amendment.
- Resolve `policy_request` digest ambiguity: retain immutable original intent
  if useful, but record later model/effort overrides separately. A model switch
  must not alter task identity, reset limits or masquerade as changed inputs.
- Define parent/root linkage for revisions, continuations and delegated tasks.
  Carry known spend and unresolved reservations forward. Additional budget
  needs explicit authority and a ledger entry, not a fresh identifier.
- Specify an explicit compatibility mapping for legacy Controller revision
  ids. X2/X4 implement that mapping; N1 provides the stable worker contract.
- Define how richer attempt records project to existing strict ledger schemas.
  Use a versioned serializer or sidecar; do not assume extra fields or new
  enum values are accepted by the old schema.

Exit evidence: examples show a cell override, legitimate input revision,
authorised continuation and child task with stable lineage and no reset of
spend. Old ledgers remain readable. X2's Controller count ownership is explicit.

### C. Define the production adapter and optional Controller boundary

- Specify a minimal admitted request/receipt API. The adapter cannot select
  another worker, retry, grant permission or accept its own output.
- Plan extraction from `evaluation_live_worker.py` so the production module
  imports neither test fixtures nor evaluation-only modules. Retain compatible
  evaluation wrappers and put new shipped modules in the distribution inventory.
- Declare supported host tools and scoped Graft access. Prove isolation in N4,
  including Graft retrieval; if unavailable, record an unsupported capability
  instead of silently disabling the project requirement.
- Interactive launches require admission and completion receipts. State which
  boundaries the host can enforce and which remain operator-observed. Do not
  claim control over arbitrary unmanaged UI launches.
- Define a future Controller step using an executor-granted allowance and
  returned evidence. Inner role accounting reconciles once against that
  allowance. N1 implements no Controller scheduling or invocation policy.
- Inspect existing import directions before adding the executor. Extract a
  small persistence helper only if needed to avoid a real import cycle;
  preserve legacy imports rather than designing a second framework.

Exit evidence: one ownership table covers admission, locks, budget, cancellation,
verification and final state; a consumer import inventory has no test dependency.

### D. Resolve historical manifests and evaluation semantics

- Classify frozen campaign integrity checks separately from current-code
  behaviour tests. Historical checks use the recorded baseline or immutable
  artefact evidence. Current-code tests construct separate temporary manifests
  and test authorisations; they never overwrite a historical campaign file.
- Keep an explicit negative test that altered dependencies invalidate a
  historical manifest. No bypass of integrity validation is acceptable.
- Authorise only the test-fixture compatibility edits needed in N1/N3. Keep
  Controller algorithms and old live campaigns out of worker scope.
- Separate operational acceptance checks, available to the worker, from
  protected post-episode grading. Hidden oracle feedback must not choose
  retries, models or Controller invocation in either experimental arm.
- Freeze the statistical estimand and decision procedure before paid work.
  Net paired acceptance difference is not the same as the rate of B0-only
  successes. A zero-event bound on that latter rate is conservative evidence,
  not a universal minimum sample size for net non-inferiority. N4/N5 must
  evaluate power using independent tasks and account for repeated runs.
- Correct X1's N4 and X3's N3 dependencies. X3's fake tests validate available
  interfaces; full Controller integration is an X4 gate, before X5 paid runs.

Exit gate: contract amendment and acceptance matrix have no unresolved ownership
or transition contradiction; full offline harness passes; operator reviews N0A.
No paid Claude experiment, new default or Controller implementation is part of
N0A. Graft refreshes remain governed by their separate standing authorisation.

## 6. Worker implementation and qualification

### N1: executor, adapter and compatibility

Implement the accepted N0A contract using existing budget, acceptance and
registry primitives. Add fake-transport tests for concurrent admission, exact
B0 ordering, early success, exhaustion, immutable acceptance, identity mismatch,
timeout, missing receipt, retained reservation, cancellation and restart.
Prove one admitted action per invocation and no new revision to obtain a repair.
Test legacy record serialization and task-lineage budget carry-forward.

Extract the production adapter, update the distribution inventory and exercise
a fake task from an isolated installed consumer directory. Implement the offline
manifest-test split before changes to bound shared modules break the harness.
Preserve old Controller callers and historical rejection checks. Do not broaden
the existing model-identity rule to permit untracked children.

Exit: behavioural tests and full harness pass; installed execution has no test
imports; no Controller call occurs on any success, failure or fallback path.
Record `worker-n1.md`, including unsupported interactive enforcement limits.

### N2: managed delegation

Implement validated task graphs: dependencies, read/write ownership, depth,
concurrency, deadlines, child permissions and root budget allocations. Model
proposals are untrusted input to deterministic validation. Admit children
through N1; require each child's model/effort request and receipt. Prevent
cycles, overlapping unauthorised writers, root-cap escape and orphan execution.
Propagate cancellation and reconcile every child before root finalisation.

Exit: fake graphs demonstrate independent work, dependency failure, conflicting
writes, cancellation and recovery. Aggregate charges are counted once. Hosts
without enforceable child controls reject managed delegation or expose the
documented unsupported boundary. Record `worker-n2.md`.

### N3: assessor and selector

Implement public-evidence assessment and a worker policy separate from the
qualified B0 default. Resolve or explicitly reject all fifteen model/effort
cells. Distinguish task difficulty from transport, permission, identity and
accounting failures. Record override provenance; apply it to future admitted
work without relabelling an in-flight call or resetting task limits.

Keep candidate selection in shadow/experimental mode. If resolving an uncertain
task frame requires deferred Controller capability, return a clear unresolved
outcome; do not invoke Controller from a fallback. Test equivalent task
descriptions, missing evidence, invalid assessments, unsupported cells and
unchanged B0 behaviour. Record `worker-n3.md` with explanations and traces.

### N4: production-path evaluation infrastructure

Build the existing plan's 24-task corpus with 12 development and 12 reserved
tasks. Use executable implementation/investigation tasks, independent graders
and protected oracles; include useful partial work, justified clarification
and no-change outcomes. Keep reserved content unavailable to development actors.

Use N1/N3 directly in campaigns. Freeze runtime, prompts, model registry,
tools, package revision, graders and dependencies in manifests. Test terminal
stop, restart, concurrent admission, missing receipts and actual charge
reconciliation using fake transports. Prove hidden data cannot reach actor
reads, shell, search, inherited instructions or Graft. Check graders reject
label copying and confident false completion while crediting demonstrated work.

Simulate the proposed statistical gate before deciding whether its sample can
support promotion. Repeated attempts on one task do not become new independent
tasks. Preserve an honest inconclusive outcome; do not enlarge the paid design
automatically. Exit with a frozen protocol and provider-free miniature campaign.
Record `worker-n4.md` and the exact authorised run inventory for N5.

### N5: screen capabilities, then tune on development only

Run the planned screen of at most 15 identity calls and 45 microtasks, with
the pre-run cost notice. Confirm provider identity and distinguish requested
effort from independently observed effort. Unsupported/censored cells remain
explicit; no silent substitution. Run at most 36 development episodes under
the original allocation, measuring full assessment, attempt and check costs.

Freeze the candidate, model configuration, thresholds and evaluation analysis.
Reassess N6 power using development evidence only. Report whether the proposed
sample can qualify promotion or will be exploratory. Do not open reserved
grades to choose a policy or sample expansion. Record `worker-n5.md`.

### N6: unseen worker comparison

Run the predeclared 12 reserved tasks, two policies, two repetitions, at most
48 episodes unless a separately reviewed design changes this before unblinding.
Use identical operational acceptance information and independent post-episode
grading. Analyse paired acceptance, partial quality, critical errors, false
success, total cost, latency and uncertainty. Preserve incomplete episodes and
all charges. No tuning on reserved results. Record `worker-n6.md`.

### N7: independent adjudication

Use Astra High with a compact evidence handoff. Audit leakage, sample units,
missing/censored data, identity, full cost and reproducibility. Apply the frozen
gates. Separate mechanical readiness from demonstrated policy improvement.
Possible outcomes: qualified candidate, retain B0, or inconclusive evidence.
Do not redesign the statistical gate after viewing results. Record
`worker-n7.md`; promotion still requires the operator's direction.

### N8: worker release preparation

Wire the qualified behaviour into consumer commands and `src/` documentation.
Update README, self-learning and Controller reference documents only where
worker changes affect their claims; mark Controller capabilities deferred.
Build `dist/`, check parity and smoke install/upgrade/rollback in a consumer
project. Use fake smoke checks first; any live smoke remains within the
original six-episode allocation. Retain B0 when N7 did not qualify a replacement.

Exit with `worker-n8.md`, a reproducible bundle inventory and a summary of
contracts/evidence for X0. Mechanical release does not imply commit, merge,
tag, push or publication. Stop; Controller work starts only on later direction.

## 7. Deferred Controller programme

### X0: revalidate against the completed worker platform

Use Astra High. Read N0A and N1-N8 results, identify the actual qualified
default and reproduce or reclassify the six recorded Controller findings.
Freeze the legacy-identity mapping, Generator assignment contract, task-wide
admission policy, corpus design and integration tests. Confirm N4 components
are reused, not forked. Reprice the remaining work. Record `controller-x0.md`
and a checked X1 handoff. No paid calls or implementation in X0.

### X1: repair Controller campaign integrity

Reuse N4 campaign mechanisms for terminal stop, complete dependency binding,
recovery and reservations. Reproduce the existing stop/restart defect, then
test it with fakes. Keep historical runs immutable and prepare new versioned
campaign artefacts where appropriate. Uncertain accounting blocks redispatch.
Exit with `controller-x1.md` and offline matrix/pilot integrity evidence.

### X2: Generator assignments and task-wide admission

Execute every admitted Generator assignment using its intended cell and
receipt. Enforce Controller allowance/count ownership on durable task state,
including races and competing decisions. Overrides, restarts and identity
adapters must not create a fresh allowance. An authorised further intervention
is recorded explicitly against remaining or added budget. Test legacy mapping,
different decisions for one revision and independent tasks. Record
`controller-x2.md`; do not claim concurrency safety from inspection alone.

### X3: realistic corpus and unbiased scoring

Build the original plan's 48 executable tasks, split 24 development and 24
reserved. Previously exposed worker tasks can be development material only.
Use N3 assessment on public inputs and N4 campaign/grader infrastructure.
Keep policy injections only in unit tests; eliminate treatment-specific canned
answers. Score demonstrated partial progress, diagnosis and safe continuation
without calling incomplete work complete. Verify oracle isolation and
critical-error dominance. Exit with grader/adaptor fake tests against available
production interfaces; full integrated Controller execution belongs to X4.
Record `controller-x3.md`.

### X4: integrate Controller as an executor-owned step

Implement the N0A extension boundary in N1's executor, reuse N3 selection
and N2 delegation, and reconcile Controller role costs once. Test proactive
and reactive invocation before final acceptance, worker reserve preservation,
evidence handoff and cancellation. Wire `auto/on/off` with explicit precedence
for project/session/task intent and interactive overrides. An override changes
intent, not permissions, available capability or the identity of an active call.

Exit: fake end-to-end tasks prove Controller-on, Controller-off and auto paths,
including useful incomplete evidence, no duplicate admission, unchanged task
acceptance and complete accounting. Neither arm sees hidden evaluator state.
Record `controller-x4.md`; live comparisons must wait for this gate.

### X5: economical live qualification

Reuse N5 identity evidence only when model, host, tools and settings remain
compatible. Run missing/stale checks, the six-task B/S/A pilot, bounded
development comparisons and the partial-result continuation probes from the
original plan. Freeze S as the qualified worker policy, including B0 if retained;
A uses that same worker policy plus Controller. If B and S are identical in
execution as well as policy, predeclare elimination of duplicate development
runs rather than paying twice. Do not merge arms after looking at outcomes.

Charge assessment, Controller, workers, grading and continuations to the
appropriate total. Evaluate whether useful partial evidence improves a later
worker's outcome at equal total budget. Stop for nonviable costs or unresolved
identity. Record `controller-x5.md` and freeze X6 before reserved unblinding.

### X6-X8: unseen comparison, adjudication and packaging

**X6, Sol High:** execute the frozen S/A comparison, 24 reserved tasks with two
repetitions per arm, at most 96 episodes. Report paired acceptance and partial
quality, critical errors, false success, cost and latency with uncertainty.
No tuning or silent exclusions. Record `controller-x6.md`.

**X7, Astra High:** independently audit the evidence and apply frozen gates.
Worker qualification does not imply Controller uplift. Record an explicit
qualified, inconclusive or rejected decision in `controller-x7.md`.

**X8, Sol High:** wire only the behaviour supported by the X7 decision and
operator promotion instruction. Update source README, Controller roles/use
cases, self-learning guide, override instructions and diagnostics. Build and
verify `dist/`; test consumer install, rollback and overrides. Keep experimental
features labelled and reversible if unqualified. Record `controller-x8.md`.

## 8. Cost and elapsed-time assumptions

Official OpenAI sources checked 2026-09-24:
[GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
[GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) and
[API pricing](https://developers.openai.com/api/docs/pricing).
High is supported by both. Short-context Standard rates per million tokens:

| Model | Ordinary input | Cache read | Cache write | Output including reasoning |
| :--- | ---: | ---: | ---: | ---: |
| GPT-5.6 Sol | USD 4 | USD 0.40 | USD 5 | USD 20 |
| GPT-6 Astra | USD 10 | USD 1 | USD 12.50 | USD 50 |

Use mutually exclusive input categories I/R/W and output O, in millions.
Sol costs `4I + .4R + 5W + 20O`; Astra costs `10I + R + 12.5W + 50O`.
Cache hits and cross-session reuse are assumptions, not observed savings.
These retain the shared protocol's conservative Standard/Fast envelopes and
30 percent contingency. Reprice changed terms, long contexts, regional charges
and separately billed tools at each handoff. No hourly API billing is implied.

| Unit | Model / effort | I | R | W | O | API-equivalent range |
| :--- | :--- | :--- | :--- | :--- | :--- | ---: |
| B | Sol / High | .10-.25 | .20-.60 | .02-.05 | .02-.05 | USD 1.25-6.50 |
| I | Sol / High | .25-.75 | .50-1.50 | .05-.15 | .05-.15 | USD 3.25-19.50 |
| R | Astra / High | .10-.30 | .20-.80 | .02-.06 | .02-.06 | USD 3-20 |

Remaining development includes N0A but excludes completed N0:

| Scope | Units | API-equivalent estimate | Engineering time | Additional serial live time |
| :--- | :--- | ---: | ---: | ---: |
| N0A through N8 | 2R + 5I + 2B | USD 24.75-150.50 | 30-58 h | 5-15 h |
| X0 through X8 | 2R + 5I + 2B | USD 24.75-150.50 | 30-59 h | 9-24 h |
| Combined | 4R + 10I + 4B | USD 49.50-301 | 60-117 h | 14-39 h |

Ranges exclude operator delays, repeated remediation cycles and context loss
beyond the token assumptions. Re-estimate rather than promise these totals.
They are direct API-equivalent development projections, not subscription bills.

Paid Claude experiments remain separately budgeted in the original plans:
worker expected USD 40-160, allocation ceiling USD 318.75; Controller expected
USD 200-650, allocation ceiling USD 1,376.75. Combined provisional expectation
is USD 240-810 and the existing allocation sum is USD 1,695.50. Confidence is
low until N5/X5. These are inherited planning allocations, not freshly verified
provider-price quotes or permission to spend. They include the original smoke
allocations; do not add those again. Reuse valid identity evidence to reduce
actual calls. Local admission caps are not provider invoice guarantees.

Before each paid campaign state scope, counts, expected cost, cap and runtime;
check standing authorisation and the project's above-USD-100 approval rule.
Do not ask again for already covered work. Scope/allowance expansion needs a
fresh check. Graft refreshes have separate standing approval; charges are
unknown and excluded, not zero. A current documentation-only index does not
justify a paid semantic rebuild. No paid experiment runs during plan creation
or N0A. No automatic expansion to rescue inconclusive reserved evidence.

## 9. Evidence anchors and acceptance register

Source anchors checked in the dependency review; re-query Graft at execution:

- `docs/WORKER-EXECUTION-CONTRACT.md`, sections 3 and 5-6: identity, lifecycle
  and B0 sequence. The lifecycle contradiction is a design finding, not a
  failure of an implemented new executor.
- `tools/controller_policy.py`, `derive_task_revision`: legacy identity.
- `tools/controller_dispatch.py`, task dispatch: Controller-owned allowance
  and worker handoff. Duplicate ownership is a prospective integration risk.
- `tools/evaluation_live_worker.py`: harness imports and restricted host tools.
- `tools/build_dist.py`: explicit shipped-tool inventory.
- `tools/controller_evaluation.py`, `_manifest`: bound shared registry files.
- `tools/controller_matrix_runtime.py`, `validate_manifest`: changed-file
  rejection; `test/harness/controller_evaluation_r5_tests.py` executes the
  committed manifest with fake transport. This confirms test coupling; no
  shared-file mutation was needed to demonstrate the dependency in review.

| Requirement | First gate | Later confirmation |
| :--- | :--- | :--- |
| Legal B0 retry/fallback under one revision | N0A contract; N1 tests | N4 campaigns; N8 consumer |
| Overrides do not reset identity, spend or reservations | N1 | N2 children; X2 Controller counts |
| Exactly one task owner and one admitted invocation | N1 | X4 integration |
| Historical evidence immutable; current tests remain useful | N1 | N3 shared changes; X1 new campaigns |
| Installable adapter without test dependencies | N1 | N8 release; X8 release |
| Controlled child work and root budget | N2 | X4 |
| Public assessment, protected grader and Graft isolation | N3/N4 | X3/X4 |
| All fifteen cells supported or explicitly rejected | N3/N5 | X5 compatible identity evidence |
| Policy promotion separate from mechanical readiness | N7/N8 | X0 baseline; X7/X8 |
| Controller auto/on/off and useful partial outcomes | Deferred X4-X7 | X8 consumer |

Progress: N0 historical design and N0A amendment complete. N1-N3 are
qualified offline. N4 has a 24-task corpus, fake campaign and statistical
preflight; its actual worker/Graft isolation gate remains open, as recorded in
`stage-results/worker-n4.md`. N5-N8 and all Controller stages remain pending.
Update each stage result and its gate here as work is reviewed. Do not mark a
gap closed merely because a schema, module or passing legacy test exists.

Planning-delivery validation, 2026-09-24: local Markdown links, cost-unit
arithmetic, the new handoff check and `git diff --check` passed. The initial
`python test/harness/check.py --json` run encountered a sandbox child-process
permission error. Its repeat with the required process permissions exited 0.
The initial run also confirmed all 16 handoffs and 69-file bundle parity.
Graft semantic and wiring freshness passed after the planning edits. These
checks validate this documentation delivery, not completion of N0A or N1.

## 10. Exact next action

Review the [N1 result](stage-results/worker-n1.md) and its offline limits.
After operator direction, begin N2 managed delegation with the same recommended
**GPT-5.6 Sol / High** setting, then stop for review. N2's plan projection is
4-8 engineering hours. No N2 implementation or paid experiment is authorised
by this status update. Do not begin from superseded N0 or pre-amendment N1
instructions.
