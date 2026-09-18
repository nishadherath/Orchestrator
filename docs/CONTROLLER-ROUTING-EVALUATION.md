# Controller routing evaluation protocol

Date: 2026-09-18. Status: proposed, to freeze after R0-R4 and pilot calibration.
Parent: [Controller routing plan](CONTROLLER-ROUTING-PLAN.md). Values below are
predeclared design choices for review, not measured optima or a paid-run approval.

## 1. Questions and causal comparisons

Measure separately:

1. Does the expanded model/effort router improve quality over fixed B0?
2. Does Controller-assisted work improve quality beyond the best economical
   single-worker comparator qualified on development data under the same task budget?
3. Can the router detect where that incremental benefit is worth buying?
4. Does an incomplete Controller run leave useful, correct and reusable evidence?
5. Do manual controls actually dominate automatic routing on the installed host?

Policies, with exact hashes and choices frozen for each phase:

- **B:** historical fixed B0, as implemented at its recorded source/bundle
  revision. Keep its three-worker sequence and stopping semantics intact.
- **S:** worker-only vNext router, all fifteen supported cells eligible. A
  bounded structured problem-solving brief provides a strong cheap control.
  It uses the same visible acceptance contract, permitted tools and task cap
  as the treatment. It cannot invoke Controller.
- **T:** explicit Controller treatment followed by an S-selected implementer,
  or a contract-valid clarification/no-change result. Development forces this
  path on positive and negative tasks to learn where the extra roles add no value.
- **A:** automatic vNext policy choosing S or T from observable features and
  approved rules, with the same post-report implementation/acceptance logic.

Comparing A only with Sonnet-low would confound extra roles with stronger
models and extra spend. S is the principal reserved comparator. B remains a
reference and regression target; do not overwrite earlier B0/B1/B2 evidence.

Match whole-task allowances and maximum attempts, input/tool access and output
requirements. A need not spend the allowance. Record costs of routing, review,
failed attempts and verification. High-cost quality gains may be valid, but
must be visible, reproducible and within the declared operator envelope.

## 2. Corpus and protected graders

Build 48 fresh synthetic tasks: 12 families, two development instances and
two reserved instances each. Development = 24; reserved = 24. Eight positive
families and four negative/control families give 16 potentially suitable and
eight ordinary/control tasks per split. Add 60 cheap routing vignettes for
offline rule/override tests; these are not model-quality evidence.

Use existing fixtures only for regressions and instrumentation, not as fresh
held-out evidence. Reserved instances must vary the mechanism, invariants and
repository structure, not just constants or names. Do not split near-duplicate
variants or code from one external repository across training and reserved
sets. Synthetic "realistic" tasks do not establish production generalisation.

| ID | Family and issue shape | Hidden checks/milestones and useful incomplete result |
| :--- | :--- | :--- |
| C01 | False premise: duplicated identifiers blamed on ordering; a second instance concerns the wrong cache cause | Preserve explicit compatibility constraint; demonstrate/disprove the claimed cause; minimal valid repair or exact clarification with evidence. |
| C02 | Online migration with mixed old/new readers and interrupted backfill | Data conservation, restart idempotency, mixed-version behaviour, rollback; a verified compatibility matrix and failing interleaving can be valuable before full repair. |
| C03 | Retry/idempotency with ambiguous timeouts and duplicate delivery | No duplicate side effects, durable commit ordering, bounded retry; counterexample trace and specific unhandled boundary get evidence credit. |
| C04 | Tenant/authorisation boundary across cache, job and request context | No cross-tenant disclosure, denied requests preserved, no permission widening; executable isolation reproduction is a useful intermediate result. |
| C05 | Competing architecture under latency/memory/compatibility constraints | Locally simulated workload, property checks and resource envelopes; graded decision matrix plus cheapest discriminating experiment, not preferred prose. |
| C06 | Multi-layer incident with misleading correlated logs | Correct causal mechanism on independent traces; avoid destructive symptom suppression; ranked falsified hypotheses and a reproducible discriminating probe. |
| C07 | Money/time/protocol invariant across two or more consumers | Exact units/rounding, timezone boundaries or framing compatibility; verified invariant and residual failure list even if adapter remains unfinished. |
| C08 | Prior repairs contradict each other or a feasibility constraint | Preserve attempts; demonstrate which assumption fails; a bounded new mechanism or evidence-backed infeasibility/clarification can meet the contract. |
| N01 | High-sounding but mechanical multi-file change | Exact mechanical preservation and full tests; Controller analysis should not earn credit or trigger just from rhetoric. |
| N02 | Local reproducible defect with an established repair | Complete targeted repair, no unrelated changes; compare overhead and false-positive Controller selection. |
| N03 | Missing operator fact/access, not missing reasoning | Ask the minimal decisive question, make no harmful mutation; invented default fails. Pair with a version whose needed fact is available locally. |
| N04 | Long repetitive work or known urgent containment | Decompose or execute the safe supplied procedure; time/coverage and no unnecessary fleet; match "critical/simple" wording variants. |

Each task package contains: issue, actor snapshot, allowed edits, operator
constraints, public checks, frozen acceptance contract, objective milestones,
hidden invariants, feasible/infeasible decisions, risk markers and deterministic
failure injection points. Decision tasks require a structured recommendation
with cited artefacts and an executable discriminating check where possible.
Public checks intentionally miss at least one relevant behaviour, without
requiring an impossible or undocumented contract.

For every family provide a reference, at least one alternative valid solution,
a partial-but-useful result, a confident wrong result, a superficial test-pass
mutation and a dishonest completion claim. Validate that the graders reject
the bad variants and distinguish partial from full success. This is more
important than increasing the number of live episodes.

Keep hidden oracles, labels and reference repairs outside actor access under
the existing isolation mechanism. A classifier sees only the issue, allowed
public artefacts and runtime observations. Task ID, family labels and hidden
grade cannot enter its decision API. Freeze Graft roots so retrieval cannot
read a neighbouring oracle or another episode's work.

Optional later external validity: six pinned, licence-reviewed open-source
issue snapshots with hashes, original issue/commit provenance and independent
graders. Add them only after the synthetic gates. Use a fresh repository split
and report possible pretraining contamination. No repository is assumed safe
to redistribute or included merely because it is public on GitHub.

## 3. Quality when completion is partial

Keep semantic task outcome, execution status and quality separate. Semantic
outcomes: accepted-full, accepted-clarification, accepted-no-change,
useful-partial, incomplete-no-useful-progress, wrong, critical-violation.
An accepted clarification/no-change counts as task success only when the
frozen contract explicitly defines it as the correct result. Timeout and
budget exhaustion remain execution statuses, not quality judgements.

### 3.1 Independent quality vector and a predeclared summary

Record five normalised [0,1] dimensions. The weighted 0-100 score is a compact
summary for paired analysis; publish every component alongside it.

| Component | Weight | Objective interpretation |
| :--- | ---: | :--- |
| M: contract milestones | 40 | Fraction of preweighted user-relevant subgoals met by external checks. Group tests by requirement so adding redundant tests cannot inflate quality. |
| E: reliable evidence | 25 | Coverage and correctness of required observations; artefacts are independently rerun or validated against fixtures. A path/hash alone is insufficient. |
| D: diagnosis/decision | 15 | Agreement with the task's causal/property oracle, including valid alternative diagnoses and acknowledged unknowns. |
| N: useful continuation | 10 | Correctly identified remaining blocker and executable safe next test/step, judged against the frozen rubric. Real continuation experiments validate this proxy. |
| H: calibrated reporting | 10 | Completion claims agree with actual acceptance, uncertainty and residual risks. Unsupported confidence is a failure, not a style preference. |

`Q = 40*M + 25*E + 15*D + 10*N + 10*H`.

Freeze applicability and weights per family before execution. Do not normalise
away a failed applicable dimension after seeing results. Zero-output/no-op
results get zero primary quality unless a validated clarification/no-change
is specifically appropriate; honest admission alone is not valuable progress.
Deduct invalid evidence from E and affected milestone credit, and grade its
consequences. A critical invariant violation sets primary Q to zero and fails
the safety gate regardless of positive components; still publish raw components.
Avoided harm means evidence of an actual defective action prevented, not
credit for listing generic risks.

Example, both unfinished: one result changes three files and wrongly claims
success; another reproduces the cause, proves two important invariants and
leaves a reproducible unresolved case. Both fail full acceptance, but only the
second can earn independently checked E/D/N credit. Conversely, a long accurate
essay cannot outscore completed requirements merely by repeating the issue.

Record full acceptance, false-success count, critical error count and Q for
ALL scheduled episodes, including zero-progress timeouts and failed calls.
No survivor-only quality averages. Unknown accounting disqualifies economic
claims and pauses admission, but does not erase work already performed.

### 3.2 Grading and uncertainty

Use deterministic checks first. Bounded decision rubrics need blinded human
review or calibrated independent judges with task-specific anchors. Strip
policy/model labels and cost from grading views; randomise answer order;
require criterion-level evidence. Do not use the same producing role as the
only judge. Audit at least 20% of subjective grades and all disagreements,
critical cases and borderline promotion decisions. Log review time and paid
judging cost. Freeze rubrics before tuning. Judge agreement on golden/mutant
fixtures is a prerequisite, not proof against every possible gaming strategy.

Measure factual false claims, coverage, test reliability and reporting
calibration. Token volume, self-rated confidence, role count and apparent
novelty are diagnostics only. Do not award points simply for using Controller.

### 3.3 Continuation and rescue experiment

Prespecify eight development checkpoints with an unresolved real issue: two
budget-limited, two interrupted-after-evidence, two partially implemented and
two justified clarification/infeasibility cases. Use stage-safe fault injection
at defined boundaries, not cancellation selected after a favourable answer.
Produce these partial runs separately from the main development comparisons;
never deliberately interrupt a main T arm and mix its grade into natural
Controller outcomes. Each pair's allowance includes its live producer run.

Fork each identical checkpoint into two matched continuations with the same
worker cell, time/cost cap and public artefacts. One receives the validated
Controller evidence packet; the other receives the ordinary canonical handoff
and retains access to the same observable evidence. No full transcripts and
no hidden grader feedback. The packet arm cannot get free external facts.
This isolates the packet's continuation value conditional on a shared checkpoint;
it does not itself estimate the end-to-end benefit of paying for Controller.
The main S/T comparison answers that separate question.

Measure additional verified milestones, completion rate, repeated investigation,
unsafe actions and cost/time to acceptance. Report incremental continuation
cost AND whole-pipeline cost including the Controller that created the packet.
Synthetic/scripted packets validate plumbing only. If actual live partial
packets cannot be produced within the tranche, mark that hypothesis untested.
Keep natural incomplete episodes separate from deliberately interrupted ones.

## 4. Coverage of models, effort and routing decisions

### 4.1 Full-matrix screen without a full-matrix campaign

First 15 tiny identity calls, one per cell, under exact model/effort settings.
Then 45 microtasks: the same three distinct bounded reasoning task shapes
under each of the 15 cells. Balance ordering and record cold/warm cache state.
This screens identity, cost, latency and candidate behaviour; n=3 is not
production qualification, and tasks should not all be trivial greetings.

Give high/xhigh/max useful reasoning work and enough output allowance to avoid
confounding effort with arbitrary truncation. Freeze effort-specific limits
and report censored runs. If a model cannot honour an effort or is substituted,
label that cell unavailable and stop claims of full-matrix support until
resolved. Low/medium Fable and Sonnet max must actually be exercised, not just
listed in the registry.

Use the screen to shortlist cells for family/role hypotheses, then evaluate
those in complete development episodes. Preserve uncertainty for unsampled
cross-products. Use paired spot comparisons of neighbouring efforts versus a
model switch within the development budget; replacing planned calls requires
an amended development manifest, never an untracked sweep.

Publish a 15-row coverage table: definition, CLI/frontmatter reachability,
served identity, effort evidence, microtask quality/cost, complete-episode
evidence, automatic eligibility and reason if excluded. All supported cells
remain explicitly selectable. No claim that higher effort always improves
quality and no automatic sequential climb through all levels.

### 4.2 Router validation

Offline vignettes and metamorphic pairs test high-impact-plus-known-fix,
low-impact-plus-hard-reasoning, high-impact-plus-premise-conflict, unavailable
evidence, convincing false public success, repeated identical repair and
infrastructure failure. Validate scenario coverage, not keyword matching.

For development task i compare T and S outcomes under matched conditions.
Estimate uplift `DeltaQ_i`, critical-error difference, cost and latency.
Use that as noisy treatment-benefit evidence when tuning route features.
Never call expert "this needs Controller" labels causal ground truth.
Group validation by family; no lookup keyed by task ID or exact prompt.

Tune only a small predeclared set: proactive conjunctions, reactive trigger,
maximum cheap evidence check, standard/frontier profile and worker cell
selection. Keep thresholds in versioned data, with reasons. Avoid fitting a
learned classifier or bandit to a few dozen examples. Shadow outcomes and
operator overrides are observational, not unbiased uplift measurements.

## 5. Paid tranches, envelopes and runtime estimates

All runs use candidate-bound manifests, frozen corpora and identity/price
snapshots. State each concrete cost envelope before dispatch and check it
against the operator's standing authorisation and project cost rules. Request
additional approval only where that authorisation does not cover the proposed
spend; do not ask again merely because a stage or manifest changes. This plan
proposes budgets; no paid calls are scheduled here.

| Tranche | Fixed scope | Maximum proposed allocation |
| :--- | :--- | ---: |
| Matrix calibration | 15 identity probes at USD 0.25/call + 45 microtasks at USD 1/call | USD 48.75 |
| Instrumented pilot | Six development tasks x B/S/A, one repetition = 18 episodes | USD 144 |
| Development | 24 tasks x B/S/T, one repetition = 72 episodes | USD 576 |
| Partial rescue/continuation | Eight pairs: one live producer and two matched continuations per pair, all within USD 16/pair | USD 128 |
| Reserved comparison | 24 unseen tasks x S/A x two repetitions = 96 episodes | USD 768 |
| Independent paid grading allowance | Separate from actor envelopes; deterministic graders preferred | USD 64 |
| **Core ceiling** | 60 calibration calls + 186 main episodes + eight producer/continuation pairs | **USD 1,800** |

Allocation is an admission ceiling, not a provider invoice guarantee or an
expected bill. Per-episode initial split is USD 4 Controller + USD 3 workers +
USD 1 routing/checking within USD 8; non-Controller arms may use the same USD 8
total subject to their frozen attempt policy. Controller/worker caps may make
some Fable/max profiles infeasible; calibration must reveal this before
confirmation. Reprice a changed envelope and check its authorisation instead
of silently replacing Fable with Opus or allowing cost overshoot.

The frozen R5 matrix runtime records the requested CLI effort flag, but the
current Claude result stream does not expose an independent served-effort
field. Treat effort as a controlled request whose behavioural and cost effects
are measured, while served model identity is checked separately. The matrix's
planning range is USD 1-20 and one to three hours serially; the USD 48.75 value
above remains the hard admission ceiling.

For each continuation pair, reserve at most USD 4 for the shared Controller
producer and USD 4 for each identical-cap continuation including its checks.
The remaining USD 4 covers checkpoint creation, ordinary-handoff preparation
and experiment plumbing only if these require paid calls. Count shared costs
once in campaign spend; publish both amortised and full-prefix attribution
when analysing continuation economics. Each pair's absolute allowance is
USD 16, with no unpriced producer calls outside the tranche.

Pilot task selection: four positive families including one frontier profile,
one ordinary negative and one missing-decision negative. Require four actual
live Controller entries in A, at least one successful Controller-to-worker
handoff, actual Fable direct-worker and Controller-role evidence across the
screen/pilot, and complete model/effort/accounting evidence. If intended
automatic triggers do not fire, stop and fix the route/fixture. A forced run
can diagnose instrumentation but does not satisfy an automatic-routing test.

Preserve the six pilot tasks as development data; pilot results do not count
as held-out evidence or duplicate statistical replications. Run serially in
balanced arm order initially to simplify budget and cache attribution. A later
parallel scheduler needs its own concurrency evidence and must preserve order
randomisation, separate state and ledger ownership.

Expected core spend **USD 300-700** is a provisional engineering envelope:
historical Controller plus implementation is about USD 2.99 per completed T10
case; this campaign admits at most 86 Controller opportunities before
considering new cases or reruns, plus single-worker, calibration and grading
costs. Historical incomplete costs and Fable/max price/usage remain uncertain.
Do not extrapolate the prior cheap campaign, which never reached Controller,
as its unit price. Replace the range with R5 all-attempt measurements before
R6/R7. No retries outside the declared manifests.

Allow roughly 12-30 hours of serial live runtime for the core programme,
separate from 40-80 engineering/analysis hours. The old completed Controller
mean was 500 seconds plus 80 seconds implementation; frontier profiles may
take longer. Provider waits and human review add uncertainty. Stop early if
pilot/development cannot justify the next tranche.

Optional post-qualification checks: eight new consumer-smoke tasks x S/A,
16 episodes, USD 128 maximum, plus external-repository evaluation separately
priced. These are not included in the USD 1,800 core ceiling. No actor run,
judge call or refresh cost may be hidden outside the campaign accounting.

## 6. Freeze, measurement and promotion gates

Freeze policy/profile/registry/price/schema hashes, cell support, issue and
actor hashes, external graders, rubric weights, randomisation seed, repetitions,
timeouts, caps, retry rules, confidence-interval method and gate constants
before accessing reserved outcomes. All new manifests use a new namespace;
preserve old freezes and reports. The complete task is the analysis unit.
Two repetitions are not two independent families. Pair S/A on task and
repetition, alternate execution order, and report family-clustered intervals
alongside task-level paired differences and raw counts.

Proposed gates, to accept or revise at R0 and freeze before R7:

1. **Protocol integrity:** every episode has valid identity, role/model/effort
   provenance, protected-oracle integrity and settled accounting. Violations
   stop new admissions and invalidate promotion claims; keep all costs.
2. **Critical safety:** zero new A-only critical invariant violations. Any
   systemic control/acceptance breach blocks promotion regardless of Q. Report
   events affecting both arms too; zero observed failures is not proof of zero risk.
3. **Quality on the 16 suitability-target tasks:** paired mean DeltaQ >=5/100
   and predeclared two-sided 95% lower confidence bound >0. Bootstrap families,
   retaining within-family tasks/repetitions together (fixed seed, 10,000
   resamples), and report the small eight-family sample limitation.
4. **Completion and honesty:** pooled accepted-contract rate A-S has lower
   95% paired interval >=-10 percentage points; no increase in false-success
   count. Useful partial progress cannot conceal a clear completion regression.
5. **Ordinary controls:** mean Q loss <=2/100, no new critical failures, and
   no more than one unnecessary Controller entry across 16 negative episodes.
   Median ordinary-task cost overhead <=10%; disclose absolute differences
   when denominators are near zero. Router-feature extraction costs count.
6. **Affordability:** all episodes within admitted controls; on triggered tasks
   mean incremental cost <=USD 4 and median extra latency <=12 minutes under
   the initial envelope. These are operator policy proposals, not universal
   valuations. Also report dollars per additional accepted result and per
   10 verified Q points when denominators are positive; otherwise state that
   the ratio is undefined or dominated.
7. **Reachability and coverage:** held-out triggers execute Controller, direct
   Fable and role-profile Fable are verified where selected, all five efforts
   have calibration evidence, and the 15-row support table is complete.
   Do not manufacture a held-out Fable selection merely to hit a count.
8. **Partial-result claim:** the paired continuation study improves verified
   progress without increased unsafe changes; report uncertainty. If this is
   inconclusive, salvage can ship as an operational capability with no measured
   benefit claim. It cannot rescue a failure of the main quality gate.

These sample sizes may be inconclusive, especially for non-inferiority or rare
harms. Before reserved execution, simulate power/sensitivity using development
variance and a fixed minimum useful effect, without viewing reserved results.
If insufficient, stop and propose a separately budgeted expansion of fresh
families/tasks. Do not repeatedly inspect reserved outcomes until significance
appears. Any optional extension needs a predeclared sequential error-control
method or a completely new confirmatory sample, not post-hoc threshold changes.

Tune on development; select once; confirm once. No significance claim across
fifteen cells from the microtask screen. Per-cell/family reports are exploratory
unless their own multiplicity/sample requirements were preregistered. A small
number of held-out families can justify a narrow rollout, not unrestricted
claims about all engineering domains.

## 7. Reuse and required deliverables

Reuse `dispatch_budget.py`, `acceptance.py`, actor isolation, hashed event
chains, freeze/manifest machinery and live adapters. Extend rather than copy
budget, lock or identity code. Separate new experimental policy state from
the old qualified-default freeze checks so historical evidence stays valid.

Proposed outputs by R5-R7:

- `test/fixtures/controller_routing/` development/public actor data and variants;
- protected `test/oracles/controller_routing/` with independently executed checks;
- `test/harness/controller_policy_tests.py`, `controller_control_tests.py` and
  `controller_quality_tests.py` plus meaningful extensions to existing suites;
- new registry/profile schemas, assessment/decision/evidence-packet contracts;
- campaign runner/reporting beside existing evaluation tools, with exact reuse
  chosen at R0 to avoid overlapping orchestration engines;
- dated matrix-coverage, pilot, development, continuation and reserved results;
- promotion/rollback decision with all-attempt spend, failures and uncertainty;
- updated `CONTROLLER.md`, `SELF-LEARNING.md`, root/consumer README, operating
  core, command documentation, installer ownership and rebuilt bundle at R8.

Do not ship hidden graders, private session controls, credentials, local Graft
indexes or evaluation-only snapshots. Installer rollback restores policy and
owned files while preserving operator preferences and task evidence.
