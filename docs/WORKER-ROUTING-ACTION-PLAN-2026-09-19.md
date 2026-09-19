# Worker routing and delegation: staged action plan

Date: 2026-09-19. Status: **planned, not started; operator chooses the start**.

This is the next programme requested after the twelve-gap review. It repairs
ordinary worker routing, execution and delegation. Experimental Controller
changes belong to the separate [deferred plan](CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md).
Both use the [execution protocol and cost basis](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
Start only when directed, using the [N0 handoff](../handoffs/2026-09-19-worker-routing-n0.md).

## 1. Scope and ownership of all twelve gaps

| Review gap | Next programme ownership | Deferred Controller ownership |
| :--- | :--- | :--- |
| 1. Stopped R5 campaign resumes | Give new worker campaigns terminal stop semantics in N4; no R5 repair here | X1 repairs the existing matrix and pilot |
| 2. Incomplete R5 manifest | Complete worker execution inventory in N4 | X1 binds the R5/Controller dependency set |
| 3. R5 public-label grading | Genuine worker fixtures and independent graders in N4 | X3 replaces Controller quality fixtures; preserves old scaffolding |
| 4. Pilot family-label/canned-answer bias | Assess public inputs without evaluator labels in N3/N4 | X3 repairs the Controller pilot comparison |
| 5. First Generator cell only | Excluded | X2 |
| 6. Missing cell selector | Worker-only selector in N3/N5 | X4 integrates it with workflow/profile selection |
| 7. Execution stops at handoff | General worker executor in N1 | X4 inserts Controller evidence before worker execution |
| 8. Controls not in default path | Excluded; keep existing controls unchanged | X4 and X8 |
| 9. Controller count partly caller supplied | Excluded; N1 offers a task identity contract only | X2 implements Controller-specific admission |
| 10. Prompt-driven child delegation | N2 and N8 | Reuse completed contracts, no separate scheduler |
| 11. Missing qualification evidence | Worker identity, effort, selection and delegation in N5-N7 | Controller uplift and role profiles in X5-X7 |
| 12. Documentation/test overclaims | Worker scope throughout, release in N8 | Controller scope throughout, release in X8 |

This split does not call a deferred defect fixed merely because a safer
worker-only component exists. Shared contracts are built once and reused
later. Do not modify `controller_policy.py`, `controller_dispatch.py`,
`controller_control.py`, `controller_corpus.py`, `controller_evaluation.py`,
`controller_matrix_runtime.py`, `controller_pilot_runtime.py` or Controller
role assignments during this programme. Shared modules may receive necessary
backward-compatible worker changes with existing Controller regressions run.
Do not refresh the frozen R5 manifests or execute them.

Deliverable: a consumer-installable worker execution path with explainable
cell selection, durable task accounting, independent acceptance and bounded
delegation. B0 remains the shipping default until a new worker-only candidate
passes N7 and the operator directs promotion. Controller stays disabled in
all N-series execution and evaluation paths, including failure fallbacks.

## 2. Stage schedule and operator checkpoints

| Stage | Deliverable | Dependencies | Model / effort | Engineering time | API unit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| N0 | Baseline, boundaries, versioned contracts and exit criteria | Operator start | GPT-5.6 Sol / High | 2-3 h | B |
| N1 | Durable worker task executor and host adapter | N0 | GPT-5.6 Sol / High | 5-9 h | I |
| N2 | Bounded delegation, dependencies and shared budgets | N1 | GPT-5.6 Sol / High | 4-8 h | I |
| N3 | Public-evidence assessment and explicit cell selector | N0-N2 | GPT-5.6 Sol / High | 4-8 h | I |
| N4 | Executable worker corpus and trusted campaign runner | N1-N3 | GPT-5.6 Sol / High | 6-12 h | I |
| N5 | Live cell screen and economical development tuning | N4; spend check | GPT-5.6 Sol / High | 2-4 h plus 1-5 h live | B |
| N6 | Frozen candidate and unseen paired evaluation | N5; spend check | GPT-5.6 Sol / High | 2-4 h plus 4-10 h live | B |
| N7 | Independent evaluation and promotion adjudication | N6 | GPT-6 Astra / High | 2-4 h | R |
| N8 | Consumer wiring, packaging, installation and handover | N7 decision | GPT-5.6 Sol / High | 3-5 h | I |

Stop after every stage and report its gate. Keep Sol High across N0-N6 when
the same session remains suitable; a stage boundary is not a reason to discard
useful context. Before N7 and N8, write and validate a fresh transition handoff
and wait for the operator to set the model. N7 is an adversarial review of
the candidate and evidence, not a request to reimplement the programme.

## 3. Implementation work packages

### N0: baseline and contract freeze

Read `tools/route.py`, `tools/acceptance.py`, `tools/dispatch_budget.py`,
`tools/model_registry.py`, `tools/evaluation_live_worker.py`,
`src/ORCHESTRATOR_CORE.md`, `src/ROUTING.md` and `src/LIFECYCLE.md` using Graft
first. Save branch/HEAD, dirty paths, bundle stamp and the full offline result.
Preserve B0's exact three-attempt sequence and historical campaign evidence.

Specify TaskSpec, TaskRevision, WorkerDecision, AttemptResult, DelegationPlan
and a host capability contract. Prefer existing schemas over duplicate ones.
Task identity includes goal, frozen acceptance and admitted input revision;
restarting a session or changing a cell is not a new task revision. The caller
may propose an assessment but may not invent permission or acceptance changes.
Specify exactly which operations the current Claude host can enforce and which
remain interactive instructions. No claim that Codex can run Claude worker
definitions. Give proposed new files names only after inspecting existing APIs.

Check prospective statistical feasibility using offline simulations before
freezing the proposed N6 sample and margins. Twelve independent tasks may be
too few to establish a five-percentage-point non-inferiority margin. If so,
label the capped campaign exploratory, or propose a larger affordable sample
before any reserved outcomes are viewed. Do not spend on a known underpowered
campaign while describing it as capable of qualifying a new default.

Exit: contracts name fields, owners, transitions, error states, migration and
rollback; every scoped gap has an owning stage; B0 baseline reproduces; future
tests have explicit expected outcomes. No runtime policy change or paid call.

### N1: production worker execution

Implement a small reusable executor, proposed `tools/task_executor.py`, around
existing budget, acceptance, registry and record helpers. Start with B0 and a
fake host adapter. States must distinguish prepared, admitted, running,
verification, accepted, failed, partial, blocked, cancelled and uncertain.
Persist intent before dispatch; acquire task ownership atomically. A terminal
stop never continues simply because the launcher was restarted.

The executor owns the complete attempt sequence, task budget, verification and
bounded repair. Commands and required outputs are verified independently;
rubric decisions remain review-required. Preserve the first output and exact
failure evidence for a repair. Identity mismatch or incomplete accounting stops
new admissions. Keep known charges and unknown held reservations separate.

Implement a host adapter for supported execution, with explicit cell/effort
and telemetry. Interactive Agent-tool launches need an admission token and a
receipt reconciled by the executor; programmatic launches use the same record
contract. Do not describe an interactive-only path as automatic execution.
Default host permissions stay within operator scope; never enable a broad
bypass to make tests run. Retain CLI compatibility for existing consumers.

Exit: fake and subprocess-fixture tests cover all transitions, three-attempt
B0 ceiling, two simultaneous admissions, interruption before/after launch,
uncertain charges, identical/conflicting receipts, protected-path changes and
independent acceptance. No duplicate launch or double counting after recovery.

### N2: delegation with dependencies and ownership

Implement a bounded plan consumed by the executor. Each work item records its
parent, dependencies, acceptance, cell selection request, read/write ownership,
cost allowance, deadline and return contract. The model proposes decomposition;
deterministic validation rejects cycles, overlapping writers, unsafe paths and
children outside scope. Default to a single worker; serialise dependencies.
Parallelise only admitted independent work with a stated latency or isolation
benefit. No paid planning call is mandatory for a trivial task.

Children consume the parent's remaining allowance through one accounting
owner. Sibling work cannot oversubscribe the parent. Cancellation stops new
children and preserves in-flight charges. Bound depth and concurrency by
tested host capability and an operator-configurable lower limit, not old
documentation's assumed host maxima. Merge child outputs through verified
acceptance; the parent cannot claim success while a required child is partial.
Unmanaged child launches are either disabled by the adapter or reported as an
unenforced boundary. Do not pretend prompts intercept arbitrary host actions.

Exit: conflicting writers, DAG cycles, parent cancellation, races for budget,
recursive spawning, failed dependencies and aggregation all have executable
tests. The no-delegation path is cheap and remains fully functional.

### N3: assessment and model/effort selection

Add a versioned worker-only policy, separate from historical `plan()` and
`rigour-auto-v1`. Extract task features in the existing assessment turn where
possible. Preserve evidence provenance, uncertainty, required artefacts,
verification strength, context demand, task deadline and failure cause. Hidden
grader results, corpus family IDs and reserved task IDs cannot enter selection.
One bounded evidence lookup is allowed when explicitly priced into the task.

Resolve all 15 cells from the shared registry. Return selected cell, eligible
alternatives, rejection reasons, evidence cohort, qualification status and cost
uncertainty. Initially use conservative labelled priors; N5 supplies measured
choices. Explicit model/effort requests are visible overrides within budget
and host capability; reject unsupported requests without silent substitution.

Compare raising effort with changing model, rather than assuming monotonic
quality or cost. Local implementation failure may earn one bounded repair;
context overflow suggests decomposition; missing facts suggest clarification;
infrastructure failure does not imply a stronger model. Preserve an explicit
unresolved-frame stop for tasks that would need the deferred Controller.
Account for input and cache costs when switching; unknown cache reuse is not
a saving. Avoid a learned classifier or bandit at this small evidence volume.

Exit: all cells can be explicitly selected or precisely rejected; fake commands
preserve requested identity/effort; paired wording changes leave decisions
stable for identical structured facts; no branch can invoke Controller. Record
a shadow decision alongside B0 until qualification permits dispatch changes.

### N4: independent worker evaluation and launch integrity

Create a new worker campaign; do not reuse the unqualified R5 grader as a
quality oracle. Use 24 executable tasks: 12 development and 12 newly reserved,
across six families with two distinct mechanisms per family per split. Cover
local repairs, mechanical multi-file edits, cross-module integration, resource
constraints, misleading diagnosis and missing operator decisions. Synthetic
repositories are acceptable when they execute genuine behaviour. Reused older
fixtures are development data, not new held-out evidence.

Each task has public requirements, inspectable inputs, externally frozen
acceptance and protected behavioural graders. Keep graders inaccessible to
actors using the project's proven isolation mechanism, not just a request to
avoid parent paths. Test read/search/shell and Graft access so hidden oracles
cannot leak through the repository index. Capture artefact hashes and actual
changes for safety checks. Genuine alternative solutions must pass.

Retain milestone/evidence/diagnosis/continuation/reporting dimensions but derive
them from reproducible checks. Add variants that copy public labels, falsely
claim success, omit admitting a prohibited edit and make useful partial
progress. Reference/alternative variants must pass; label-only claims must
not earn implementation credit. Assess public evidence identically across
arms, charge assessment overhead and never insert evaluator-written answers.

Build a reusable campaign driver, proposed `tools/worker_evaluation.py`, using
N1. Freeze the complete dependency inventory, prompts, policy, corpus, graders,
host version, caps, stop rules, cache protocol and launch order. Cover budget
sum validation, terminal-failure restart, concurrent campaign starts, altered
dependencies and incomplete receipts before a provider-enabled path exists.
This reusable work may be adopted by X1/X3 later; old R5 launchers remain paused.

Exit: adversarial graders, isolation and a full fake campaign pass; a public
label copier cannot solve the tasks; authorisation binds the complete scope;
ordinary restart after terminal failure admits zero calls. Full offline gate
passes without changing historical evidence hashes to disguise new behaviour.

### N5: qualification screen and development selection

After a concrete spend notice and authorisation check, run a worker-only screen
of 15 identity calls and three fixed microtasks per cell, 60 calls total.
Capture served model, requested effort, CLI/host version, usage, cache counters,
latency, accounting completeness and objective microtask scores. Unsupported
or mismatched identities stop that tranche; reconcile and explicitly revise
the remaining schedule rather than substituting or silently retrying.

Use the 12 development tasks for up to three worker-only arms: B0, the candidate
selector, and one predeclared alternative cell-selection strategy. This is a
36-episode upper bound, not a requirement to spend on a dominated option.
Compare effort and model independently; eliminate only on recorded evidence.
Tune a small versioned rule table and preserve rejected alternatives. All
arms have the same task-level cap and acceptance; all their overhead counts.

Exit: a dated availability/identity snapshot, full spend reconciliation,
uncertainty-aware capability/cost table, selected policy and rejected options.
Insufficient evidence leaves a cell provisional. It does not require assigning
every cell a production workload. Freeze the candidate before N6.

### N6: reserved comparison

Before viewing reserved results, freeze the candidate, task set, two-arm
schedule, attempt caps, scoring and analysis. Run 12 reserved tasks x B0 and
candidate x two repetitions: 48 episodes, treating task as the paired unit,
not repetitions as independent tasks. Balance order and record cache effects.
No tuning, substituted tasks or undeclared retries after inspecting results.

Predeclare N0's proposed promotion gates, finalised before N5 spend: no observed
new critical violation; no increase in false-success count; lower 95 percent
paired bounds above -5 percentage points for acceptance and -5/100 for quality;
plus either at least 10 percent lower observed total cost at those quality
floors, or a lower 95 percent paired quality-uplift bound above +5/100 within
1.25x baseline total cost. Report family outcomes and budget censoring. These
are policy thresholds, not established economic facts. Document the exact
interval method and multiplicity handling before results exist.

Small samples may be inconclusive. Then retain B0 and state what further
independent sample, cost and runtime would be required; no automatic expansion
or threshold relaxation. A fair negative result is a completed evaluation.

Exit: immutable paired results, analysis script, uncertainty intervals,
critical-error/false-success tables, all-attempt costs and a proposed decision.

### N7: independent adjudication

The operator switches to Astra High using the checked N6 handoff. Review the
executor and selector against actual evidence, leakage boundaries, cost
attribution and the frozen gates. Challenge task usefulness and inspect real
outputs, not just test counts. Reproduce any blocking finding without paid
calls where possible. Decide qualified, rejected or inconclusive; separate a
mechanically ready package from a justified default change.

Exit: a signed-by-session review record, each finding disposition and an exact
release recommendation. A defect returns to its owning N stage, with new
evidence when semantics change. An operator controls any promotion decision.

### N8: consumer integration and release preparation

Switch back to Sol High via a checked handoff. Update `src/ORCHESTRATOR_CORE.md`,
`src/ROUTING.md`, `src/LIFECYCLE.md`, `src/SELF-LEARNING.md`, `src/README.md`,
preflight and required commands around N1-N3. Distinguish supported launch
mechanisms from prompt-only obligations. Update the capability matrix and root
README. Promote only the policy qualified in N7 and directed by the operator;
otherwise ship its explicit experimental entry while keeping B0 default.

Generate `dist/` through the builder. Test clean consumer install, upgrade,
rollback, interactive task admission, explicit cell choice, cancellation,
resume and nested-budget limits. Use fake adapters first and at most six
predeclared paid smoke tasks if needed. Freeze an exact B0 rollback path.
The Controller remains outside this release change. Refresh Graft for changed
source under standing approval, record freshness and full harness evidence.

Exit: source/bundle parity, install/rollback evidence, actual interactive
behaviour, honest limitations and a handoff for the deferred programme. Stop;
do not commit, merge, tag or publish without the applicable operator direction.

## 4. Budget and time

Development: three B units, five I units and one R unit from the common
protocol: approximately **USD 23-137 API-equivalent**, spanning Standard/Fast
and token uncertainty. Engineering time totals **30-57 hours**, plus **5-15
hours** serial live evaluation and operator waits. Refresh estimates at each
handoff; these are planning ranges, not a subscription bill.

| Proposed worker experiment | Calls/episodes | Local admission allocation |
| :--- | :--- | ---: |
| Identity and microtasks | 15 x .25 + 45 x 1 USD | USD 48.75 |
| Development | At most 36 episodes x 3 USD total per episode | USD 108 |
| Reserved | 48 episodes x 3 USD total per episode | USD 144 |
| Consumer smoke | At most 6 episodes x 3 USD | USD 18 |
| Total scheduled upper bound | No automatic retries | USD 318.75 |

Provisional expected Claude spend: **USD 40-160**, low confidence until N5.
USD 3 covers all attempts and assessment/check overhead per episode, not each
worker call. Failed/censored expensive cells may require a separately scoped
experiment; do not increase caps after seeing reserved grades. Provider prices
are not inferred from OpenAI rates. No spend is approved by this table.

## 5. Completion register

- [ ] N0 baseline/contracts accepted.
- [ ] N1 worker executor qualified offline.
- [ ] N2 delegation qualified offline.
- [ ] N3 selector and assessment qualified offline.
- [ ] N4 worker corpus, isolation and campaign integrity qualified.
- [ ] N5 live screen and development evidence reconciled.
- [ ] N6 reserved comparison complete, including inconclusive if appropriate.
- [ ] N7 independent adjudication recorded.
- [ ] N8 consumer release preparation complete.

Exact initial action: when the operator chooses to begin, set **GPT-5.6 Sol,
High**, read the N0 handoff and execute N0 only. First-stage projection:
**USD 1.25-6.50 API-equivalent; 2-3 hours; no Claude experiment spend**.
