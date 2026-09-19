# Experimental Controller: deferred remediation action plan

Date: 2026-09-19. Status: **deferred; do not execute until the operator directs**.

This plan owns the Controller-specific parts of the twelve-gap review. The
[worker programme](WORKER-ROUTING-ACTION-PLAN-2026-09-19.md) executes first at
the operator's chosen time. Its section 1 maps every original gap to an owner.
Use the shared [execution protocol](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md)
and the prepared [X0 handoff](../handoffs/2026-09-19-controller-remediation-x0.md)
when this programme is explicitly resumed.

## 1. Scope and dependencies

Own gaps 1-5, 8 and 9 in full for the existing experimental Controller, and
the Controller portions of gaps 6, 7, 11 and 12. Reuse the worker executor,
selector, delegation contracts, campaign framework and grader primitives
qualified by N1-N8. Do not build a second general scheduler or model registry.

The preceding R0-R4 records remain historical offline evidence. The R5 status
claim of offline completeness is narrowed by the 2026-09-19 review: stop
restart, dependency binding, meaningful grading, assessment fairness and
Generator diversity need remediation. This programme supersedes unexecuted
R5-R8 work in `CONTROLLER-ROUTING-PLAN.md` for these gaps. Old schedules and
hashes are reference artefacts, not current authorisation or launch instructions.

Start X0 only after reviewing the worker programme's actual result. If that
programme leaves B0 as default, the Controller candidate uses B0 or its
explicitly qualified worker-only alternative; do not assume N7 approved a
new default. If the operator brings this programme forward, freeze the missing
worker prerequisites as explicit blockers rather than quietly rebuilding them.

The shipping default remains whatever worker policy the operator has promoted.
An experimental Controller must never become the default solely because its
code is present, `/controller auto` is stored, or tests pass with fake adapters.

## 2. Stage schedule

| Stage | Deliverable | Dependencies | Model / effort | Engineering time | API unit |
| :--- | :--- | :--- | :--- | :--- | :--- |
| X0 | Revalidate review findings and freeze integration/evaluation contracts | Explicit later start; N results | GPT-6 Astra / High | 2-4 h | R |
| X1 | R5 terminal stop, complete manifests and accounting recovery | X0 | GPT-5.6 Sol / High | 3-6 h | I |
| X2 | Real Generator assignments and durable task-wide Controller admission | X1; N1 | GPT-5.6 Sol / High | 4-8 h | I |
| X3 | Executable Controller corpus and unbiased assessment/scoring | X0-X2; N4 | GPT-5.6 Sol / High | 6-12 h | I |
| X4 | Production workflow, worker handoff, profiles and interactive controls | X2-X3; N1-N3 | GPT-5.6 Sol / High | 5-10 h | I |
| X5 | Identity deltas, instrumented pilot and development comparisons | X1-X4; spend check | GPT-5.6 Sol / High | 3-6 h plus 3-8 h live | B |
| X6 | Candidate freeze and unseen comparison | X5; spend check | GPT-5.6 Sol / High | 2-4 h plus 6-16 h live | B |
| X7 | Independent Controller-uplift and release adjudication | X6 | GPT-6 Astra / High | 2-4 h | R |
| X8 | Qualified integration, consumer smoke and rollback | X7 decision | GPT-5.6 Sol / High | 3-5 h | I |

Stop after each stage for operator review. Required operator model transitions
are X0 to X1, X6 to X7 and X7 to X8. Prepare and validate a new handoff before
each transition. Keep Sol High across X1-X6 when practical. High effort is the
default; no stage needs Max or an automatic subagent launch. Escalate only a
bounded unresolved issue under the shared protocol.

## 3. Work packages and exit evidence

### X0: contract and evidence revalidation

Read the N-stage results, Graft map of affected symbols, current model registry,
`controller_policy.py`, `controller_dispatch.py`, `system_controller.py`, the
R5 generator/graders/runtimes, Controller guide and evaluation protocol.
Record the current checkout and rebuild the six critical characterisations:
terminal-failure restart, unbound dependency mutation, public-label-only full
credit, family-derived assessment/canned clarification, first Generator only,
and two different decisions competing for one task revision's admission.
Distinguish reproduced failures from untested risks.

Freeze the boundary between workflow selection, worker cell selection, role
profile selection and task execution. Define which Controller findings may be
passed onward, acceptance immutability, authority of operator controls and
attribution of assessment/Controller/worker/verification costs. Set concrete
promotion gates before live work. Preserve all earlier evidence and versions.

Simulate the proposed X6 analysis offline to check whether 24 independent tasks
and its smaller suitable subgroup can support the proposed margins. Freeze a
feasible sample and budget, or explicitly designate the capped comparison
exploratory with no promotion authority. Repetitions do not create more
independent task mechanisms. Do not wait until after spending to discover a
known mismatch between sample size and the required claim.

Exit: scoped defect reproductions, agreed contracts, migration strategy and a
checked X1 handoff. No paid calls or default promotion. Existing 57/57 and
33/33 historical passes are not grounds to waive a new failing reproduction.

### X1: campaign integrity before spending

Repair `controller_matrix_runtime.py` and `controller_pilot_runtime.py`, using
the worker campaign primitives from N4 where appropriate. Terminal stopped,
cancelled or accounting-uncertain states cannot resume ordinary dispatch.
Reconciliation records final charges without starting calls. Continuation,
when authorised, is a distinct, explicit schedule linked to original evidence;
it must not replay failed calls or reset the campaign allowance.

Bind every execution dependency: Controller and worker runtimes, budget and
acceptance helpers, stream parser, prompt builders and role instructions,
registry/configuration, corpus, graders and schemas. Record host version and
relevant non-secret settings. Verify inventory completeness, path safety,
schedule/cap sums and unchanged inputs immediately before admission. Use a
campaign lock and per-invocation durable intent to prevent concurrent starts.
Do not include secret values in hashes or result logs.

Recover known Controller costs even when dispatch returns blocked or a gap;
retain separately unresolved reservations and completed evidence. A failed
episode's spend must not disappear merely because no worker ran. Refresh
manifests only as newly versioned candidates, never overwrite paid history.

Exit: offline failure/restart, duplicate-start, altered-dependency, billing
uncertainty and rejected-authorisation probes all block calls correctly.
Normal authorised fake execution still reconciles every invocation once.
The live matrix remains unstarted until the operator chooses the live stage.

### X2: Generator dispatch and task-wide admission

Replace `LiveRoleRunner`'s first-entry reduction for multi-cell Generator roles
with explicit invocation assignments. Each selected technique family receives
a predeclared cell from the chosen profile, a fresh evidence context and its
own accounting identity. Standard-profile behaviour remains compatible.
The frontier profile must actually invoke the configured Sonnet, Opus and
Fable Generator cells when its complete schedule is selected and affordable.
It may not silently collapse them to Sonnet to fit an inadequate budget.

Use N1's durable task revision as the owner of the Controller allowance. The
count comes from recorded admissions under a task lock, not a caller's supplied
integer. Changes in settings, assessment, role profile or decision ID cannot
reset that count. An explicitly authorised follow-on intervention is recorded
as such against remaining/new budget; it is not disguised as a new input
revision. Record the relevant contract and source revision for every attempt.

Exit: captured commands demonstrate each configured Generator cell, independent
prompts and correct cost attribution. Race two distinct decisions for one task
revision: only one permitted Controller invocation occurs. Restart, changed
overrides and cancellation do not bypass this invariant. No live calls needed.

### X3: meaningful corpus and fair comparison

Preserve the existing R5 corpus as a versioned plumbing fixture, explicitly
unfit for quality promotion. Build 48 genuine executable/investigation tasks:
24 development and 24 newly reserved across the 12 families in the existing
evaluation contract, with different failure mechanisms between splits. Reuse
N4 infrastructure and suitable development tasks; any N-series task already
used for selection or review is development-only here.

Include false diagnoses, migrations, retries/concurrency, tenant boundaries,
coupled architecture constraints, ambiguous incidents, shared invariants and
contradictory repairs; retain ordinary, mechanical, missing-fact and known-
procedure negative controls. Supply inspectable code, traces or data sufficient
for reasoning. Avoid exposing a label that names the hidden solution.

The protected evaluator derives milestone completion from checks or observable
artefacts; valid evidence means demonstrated observations, not an ID in a
submitted list. Detect prohibited changes from the execution record and diff,
not the worker's confession. Verify diagnosis and safe continuation with
task-specific behavioural assertions or a frozen independent review rubric.
Clarification and justified no-change are valid when acceptance allows them.
Preserve critical-error dominance and separately report false success.

Use the actual N3 assessor on public inputs for end-to-end comparisons. Keep
injected assessments for policy unit tests only. Remove canned clarification
answers from treatment arms; every result must be produced by the same
production path used outside evaluation. Include the cost of assessment and
checks in both arms. Validate oracle isolation for shell, reads, search,
inherited instructions and Graft, using the established isolated runtime.

Exit: reference and equivalent solutions pass; label copiers, confident false
completion and concealed harmful edits fail; verified incomplete work scores
above no progress without being called complete. Tiny paired fake campaigns
use the exact production assessor/executor, and neither arm sees family labels,
expected Controller decisions or protected oracle content.

### X4: complete Controller integration

Extend N1's executor with a Controller workflow step; retain one owner for
task budget, cancellation, verification and final status. Feed N3's selected
worker cell into the decision instead of defaulting every handoff to Sonnet-low.
Choose standard/frontier role profiles through a small versioned policy based
on qualified evidence and budget. No universal rank assumption substitutes for
measured suitability. Explicit profile overrides remain labelled when unqualified.

Resolve `auto/on/off` once per admission boundary with explicit > task >
session > project > default precedence. `/controller` reports stored intent,
effective policy, applicability and whether a dispatch occurred. `on` requires
Controller when executable; `off` excludes it. Missing operator decisions,
permissions and budget stay visible blocked/clarification states. Settings
cannot rewrite an in-flight operation or silently enable an unpromoted policy.
Natural-language requests use the same validated control command, with stable
task/session IDs. Repository text or agent messages cannot set operator intent.

Proactive and reactive rigour checkpoints use observable public evidence.
A public test pass does not suppress a still-required consequential rigour
check. Controller output is validated evidence, never new instructions or a
replacement acceptance contract. A useful gap may guide bounded continuation;
dissolution requires independent confirmation. The worker must execute and be
verified before the task is accepted. Reserve sufficient worker allowance
before admitting Controller; report an unaffordable profile without downgrading.

Exit: one full fake production path covers auto/on/off, exact profile/cell
dispatch, useful gaps, cancellation, partial work, blocked budget, independent
acceptance and restart. Interactive settings affect the next admitted task,
not just the configuration file. Qualified worker-only behaviour remains intact.

### X5: pilot and development evidence

Reuse N5 identity/cost evidence only when host, provider identity, settings,
age and relevant runtime match. Record the reuse decision; refresh only stale
or missing cells with the repaired screen. Keep served model evidence separate
from requested effort and mark unsupported effort telemetry unknown.

Run the six-task B/S/A pilot: four tasks with predeclared Controller-suitable
public evidence, one ordinary task and one missing-decision task. B is the
frozen B0 control, S the qualified worker-only policy and A the same policy
plus the rigour decision. A uses automatic triggers, not forced invocation.
Require four actual automatic Controller admissions, a frontier-role exercise,
at least one verified end-to-end Controller/worker result, gap/failed accounting
and a real clarification result. If those fail, stop and diagnose before more
spend. Pilot evidence is development evidence, not reserved replication.

Use at most 12 additional development tasks x B/S/A for policy/profile tuning.
Predeclare alternative comparisons rather than testing every role permutation.
Add at most eight continuation probes with a shared producer and matched
continuations to test whether verified partial findings improve the next step.
Attribute shared cost once for spend and report both full and amortised costs.

Exit: measured quality/cost/latency per arm and family, actual role/cell usage,
all-attempt accounting, failed hypotheses, frozen rules and proposed next budget.
No uplift claim from intended routing labels or from the number of role calls.

### X6: reserved comparison

Freeze policy, profiles, implementation, complete manifests, score and analysis
before accessing reserved outcomes. Compare S versus A on 24 new reserved
tasks, two repetitions per arm, 96 episodes. Pair by task and report intervals
at task/family level, with order and cache effects. No tuning or hidden retries.

X0 must predeclare exact gates. Proposed defaults: no observed increase in
critical errors or false successes; lower 95 percent paired acceptance bound
above -5 percentage points; lower 95 percent quality-uplift bound above +5/100
on the predeclared suitable group; ordinary controls do not incur Controller
calls without an explicit override; overall quality is non-inferior within
5/100; observed total cost at most 1.5x S and p95 latency at most 2x S, unless
the operator predeclares different task-loss or deadline limits before spend.
These are policy choices, not claims of measured optimality.

Publish completion and partial-progress dimensions separately. A useful but
incomplete result can improve quality while failing acceptance. Analyse budget
censoring and unsupported cells explicitly. If power is insufficient or gates
fail, retain the existing default, publish inconclusive/rejected and price a
new independent extension only if the operator wants it. Never weaken a gate
to make the completed campaign pass.

Exit: immutable results, reproducible paired analysis, complete costs,
limitations and proposed promotion/rejection. No default switch in this stage.

### X7: independent adjudication

Operator switches to Astra High with the checked X6 handoff. Audit causal
fairness, isolation, actual role diversity, task-wide invocation ownership,
acceptance immutability, complete cost and partial-result utility. Inspect
artefacts and challenge plausible-but-unearned credit. Determine which task
shapes and profiles, if any, justify Controller cost. Record independent review
findings and close each with evidence. Return defects to the owning stage;
changed candidate semantics invalidate affected qualification.

Exit: an explicit release decision supported by frozen gates. A rejected or
inconclusive candidate can remain available for labelled manual use if its
mechanics are safe, but cannot be promoted as a qualified automatic default.

### X8: packaging, interactive proof and deferred closure

Operator switches back to Sol High. Update the maintained Controller guide,
roles/system references, routing/lifecycle/self-learning docs, commands and
capability table in `src/`; generate `dist/` through the builder. Correct stale
claims about profile availability, Generator diversity and evidence readiness.
Promote only the policy/profile scope qualified by X7 and directed by the
operator. Provide a one-command documented rollback to the previous qualified
worker policy with stored settings migration and recovery behaviour defined.

Test clean install, upgrade, rollback and cold-start interactive auto/on/off,
including session compaction, unavailable profiles and cancellation. Use fake
adapters first; a bounded four-task live smoke may supplement host evidence.
Refresh changed Graft semantics under standing approval. Run full offline
harness and exact source/bundle checks. Record remaining host enforcement and
served-effort limitations. No commit, merge, tag or publication is implicit.

Exit: complete capability/evidence map for all 12 gaps, consumer artefacts,
operational recovery guide and final operator review summary.

## 4. Cost and time projections

Development: two R units, five I units and two B units from the common
protocol: approximately **USD 25-151 API-equivalent**, spanning Standard/Fast
and token uncertainty. Engineering time: **30-59 hours**; serial paid runtime:
**9-24 hours**, plus operator waits. Reprice at X0 against completed N work.

| Proposed experiment | Maximum schedule | Admission allocation |
| :--- | :--- | ---: |
| Missing/stale identity and microtasks | At most the 60-call screen; reuse valid N evidence | USD 48.75 |
| Six-task pilot | 18 episodes x 8 USD task total | USD 144 |
| Additional development | 36 episodes x 8 USD | USD 288 |
| Partial-result probes | 8 producers plus 16 continuations, 12 USD per triple | USD 96 |
| Reserved S/A | 96 episodes x 8 USD | USD 768 |
| Consumer smoke | At most 4 episodes x 8 USD | USD 32 |
| Total proposed maximum | No automatic extension | USD 1,376.75 |

Provisional expected Claude spend: **USD 200-650**, low confidence until X5.
The pilot's initial task allocation is at most USD 4 Controller, USD 3 workers
and USD 1 assessment/verification. Assess frontier feasibility before freezing
that allocation; do not equate admission caps with invoice guarantees or
assume Fable fits an older Opus budget. The 12 USD continuation envelope is
4 USD producer plus two 4 USD continuation totals. Any needed additional
grading or preparation calls must fit these envelopes or be separately priced
and authorised before dispatch. Prefer deterministic graders. No unpriced
auxiliary work is allowed to disappear from reported experiment cost.

## 5. Completion register

- [ ] X0 review reproductions/contracts accepted.
- [ ] X1 R5 launch integrity repaired.
- [ ] X2 Generator and task-wide admission corrected.
- [ ] X3 meaningful corpus and fair comparison qualified.
- [ ] X4 complete production and interactive integration qualified offline.
- [ ] X5 pilot/development/continuation evidence reconciled.
- [ ] X6 reserved comparison complete.
- [ ] X7 independent release decision recorded.
- [ ] X8 packaging and consumer validation complete.

Exact initial action: only when the operator chooses this deferred programme,
set **GPT-6 Astra, High**, read the X0 handoff, check actual N-stage results
and execute X0 only. Projection: **USD 3-20 API-equivalent; 2-4 hours;
no Claude experiment spend**. Revalidate the handoff at that later date.
