# Controller-aware routing and full model utilisation

Date: 2026-09-18. Status: proposed for operator review; no new runtime policy
has been implemented or promoted by this document. Owner: staged development
sessions using GPT-5.6 Sol, high reasoning. Start with the checked
[Stage R0 handoff](../handoffs/2026-09-18-controller-routing-stage-0.md).

This is the next programme after the completed
[improvements roadmap](IMPROVEMENTS-ACTION-PLAN-2026-09-17.md).
The detailed [evaluation protocol](CONTROLLER-ROUTING-EVALUATION.md) is part of
this plan. Neither document replaces the historical evaluation results.

## 1. Intended result and scope

Ship a router whose default is `controller=auto`: it invokes the Controller
for evidence-supported task shapes that benefit from its independent roles,
then dispatches implementation and verifies the resulting artefacts. The
operator can select `on` or `off` for a task, session or project, including
from an interactive session. Explicit selection overrides the router's
recommendation while retaining budget, identity, permission and acceptance
checks. An override that cannot execute reports a precise blocked state.

Use the entire supported Sonnet/Opus/Fable by low/medium/high/xhigh/max matrix.
Every cell must be representable, identity-checked, dispatchable, tested and
available for explicit selection. Automatic selection gives each cell a
defined opportunity and records whether it is qualified, provisional,
unavailable or dominated for the task. It does not cycle through fifteen
cells or spend money to satisfy a usage quota. Demonstrating that one cell
is unnecessary in a workload is a valid result, not a reason to hide it.

Optimise useful, verified task outcomes subject to cost and time allowances.
Report completion, partial progress, critical failures, dollars and latency
separately. A persuasive report or extra reasoning tokens are not quality.

In scope: routing, controls, quick-mode integrity, partial-result handoff,
model identity, independent acceptance, evaluation and packaging. Out of scope:
model-weight training, a new generic agent framework, full deep-mode debate,
unbounded research, automatic production exploration and cross-run Librarian
memory. Runtime changes follow review of this plan and the stage gates below.

## 2. Verified starting facts and gaps

Baseline inspected: branch `v1.0-rc1`, HEAD `1eb0fbe`. Uncommitted Controller
documentation and bundle changes already exist; preserve them. Recheck these
facts at R0 because the operator may commit or otherwise change the checkout.

| Observation | Evidence and implication |
| :--- | :--- |
| The current default is Sonnet-low, one same-cell repair, Opus-high, stop; Controller disabled. | `src/routing_priors.json: qualified_default`; `tools/route.py: plan`. Introduce a new policy ID instead of quietly relabelling B0. |
| Fifteen worker definitions exist. | `tools/cells.py`, `src/agents/`. Definition existence is not evidence of real dispatch or correct served identity. |
| The live worker adapter supports only Sonnet/Opus. | `tools/evaluation_live_worker.py: cell_identity`. `tools/evaluation_runner.py: expected_model` also maps non-Opus to Sonnet. Fix both through shared explicit registry data. |
| Controller role assignments are fixed in code. | `tools/system_controller.py: QUICK_CELLS`. Configured role cells and measured suitability are different concepts. |
| Quick mode records stability but does not branch on the classification. | `phases()` calls `classify` then proceeds to family selection. Enforce an evidence gate before claiming stronger rigour. |
| Quick mode chooses the first eligible generated candidate before the Selector call, otherwise baseline B0. | `phases()` selection/close. Verify eligibility, baseline handling and acceptance immutability in executable tests. |
| No implementation/evaluation phase runs inside quick mode. | `phases()` closes with `SolutionRecord`. Controller success cannot mean the user task passed. |
| The live evaluation executor only forwards guidance for a Controller `solution`. | `tools/evaluation_live_episode.py: PolicyExecutor`. Evidence from `gap` or a valid reframe needs an explicit, validated path. |
| The old campaign favoured fixed B0 over adaptive B1 but reached no live Controller episode. | `test/results/2026-09-18-realworld-reserved.json`, README limitations. It does not estimate the causal benefit of Controller assistance. |
| Historical Controller costs exclude failed runs. | `src/cost_table.json: controller`: six completed runs, mean USD 2.623 plus USD 0.3628 instantiation; three budget-failed runs excluded. Use only as a provisional workload estimate. |

Inspection findings above are not reproduced defects until R0/R1 tests confirm
them. Existing `SYSTEM.md` and role briefs contain design intentions beyond
the executable subset. Update the maintained Controller guide to distinguish
enforced behaviour, role instructions and future design; do not claim formal
convergence or a real measurement merely because a record is schema-valid.

## 3. Tasks likely to benefit: hypotheses to validate

Controller value comes from testing the frame, obtaining independent candidate
mechanisms and adversarially examining shared assumptions. Model difficulty
alone calls for a stronger worker or greater effort. Length alone calls for
decomposition. The hypotheses below predict incremental benefit over a
competent single-worker alternative, not merely over the cheapest worker.

| Task family | Observable reason to consider Controller | Intended improvement and limit |
| :--- | :--- | :--- |
| False diagnosis or contradictory constraints | A stated explanation conflicts with source, logs or a reproducible check. | Correct the diagnosis or request a specific decision before implementing the wrong repair. Operator requirements remain binding even if their stated rationale is false. |
| Irreversible migration or compatibility boundary | Several migration/rollback paths; data, old clients or mixed versions must remain valid. | Identify invariants, fault points, rollback and a smaller safe first increment. A routine migration with an established tested recipe can stay with a worker. |
| Distributed state and concurrency | Credible competing explanations involving retries, ordering, idempotency, failover or partial commit. | Compare mechanisms and construct discriminating tests; extra prose without tests earns no credit. |
| Security and trust boundaries | Cross-tenant effects, privilege transitions or competing threat assumptions with available code/evidence. | Find bypasses and least-privilege constraints. Importance alone does not justify extra roles for a known local fix. |
| Architecture with conflicting objectives | Explicit latency, availability, memory, compatibility or cost requirements admit multiple viable designs. | Compare measurable trade-offs against a simple baseline and preserve acceptance criteria. |
| Ambiguous multi-layer incident | Several plausible causes fit the available traces and repeated local changes fail. | Eliminate hypotheses and name the next discriminating observation; containment may happen first under a known runbook. |
| Numerical, protocol or shared-schema correctness | Silent failures appear only under boundaries, version combinations or unit/representation changes. | Expose assumptions and verify invariants across consumers. A fully specified isolated algorithm often needs a strong worker instead. |
| Research/optimisation feasibility decision | A bounded design question has inspectable data and a cheap way to falsify alternatives. | Stop an unproductive direction or derive an experiment/implementation brief. No automatic claims about unavailable external evidence. |
| Recovery after contradictory attempts | Distinct attempts or measurements disagree about the frame, not simply repeated syntax/test failures. | Reframe using preserved evidence, preventing another identical repair. Infrastructure failures are not capability signals. |

Use negative controls: routine CRUD, formatting, deterministic refactors,
well-isolated defects, pure missing permission/credential cases, urgent known
containment, and long mechanical work. Include task pairs with identical
technical content but different words such as "critical" or "simple" to
detect routing based on rhetoric. High-quality clarification and justified
no-change decisions can be correct outcomes if their contracts allow them.

### 3.1 Evidence fields, not model names in the classifier

Keep the existing five assessment axes for compatibility. Add a versioned
`RigourAssessment` with categorical fields and bounded supporting references:

- consequence/reversibility: contained, recoverable, consequential, irreversible;
- premise uncertainty: none, specific-checkable, contradictory, unavailable;
- alternatives: one-established, several-material, unknown;
- constraint coupling: local, cross-module, cross-system;
- verification gap: strong-existing-checks, incomplete-checks, rubric-only;
- observed failure cause: none, implementation, premise-conflict, no-new-evidence,
  infrastructure, context-overflow;
- required output: patch, decision, investigation, clarification;
- evidence availability, deadline and authorised task budget;
- provenance: operator fact, repository artefact or model inference, with
  evidence IDs, time and scope. Unknown is never false or high confidence.

Extract this in the existing assessment turn where practical. Keep routing
destinations and performance tables out of that classifier's input. Do not
add a paid classification call to every mechanical task. Validate the shape
in code, and use at most one bounded read-only evidence check on ambiguous
consequential work. Count that check and its context cost in evaluation.

### 3.2 Initial deterministic policy, before calibration

The following are proposed rules, not empirically learned thresholds:

1. `on` requests Controller even for a cheap task; `off` excludes it even if
   recommended. Both keep the router's hypothetical recommendation visible.
2. In `auto`, missing operator decisions/access route to targeted clarification
   or blocked status. Do not invent permissions, requirements or observations.
3. Proactively request Controller for checkable contradictory premises with a
   material effect on the result, or consequential/irreversible work with both
   unresolved assumptions and materially competing mechanisms/coupled constraints.
4. Use a normal selected worker for a clear frame. Choose its model and effort
   through section 4, and validate visible acceptance afterwards.
5. Reconsider once at an observable failure or before accepting consequential
   weakly verified work. A new premise conflict can trigger Controller. A
   local implementation failure can trigger a different cell/effort or repair.
6. Empty evidence, mere self-confidence, file count, token count and the words
   "complex" or "critical" do not independently trigger Controller.
7. At most one Controller invocation per task revision in the initial release;
   no Controller/worker loop. After a report, execute or clarify, verify, then
   stop within the frozen attempt/budget envelope. A second run needs a new
   explicit operator request and remaining/new allowance.

Proactive checking must run before a worker-visible test pass is accepted for
a task tagged with unresolved consequential assumptions. The previous
executor's immediate public-pass stop must not make those tasks unreachable.
Hidden evaluator results are never available as runtime triggers.

If recommended rigour cannot fit the budget, show `controller_recommended`
and `budget_blocked` separately. Do not silently downgrade to a normal worker
and describe it as equivalent assurance. Read-only work already inside scope
can continue where useful; any later recommendation carries its limits.

## 4. Model and effort selection

There are two independent choices: `workflow` (worker or Controller) and
`cell` (model plus effort, per worker or Controller role). Record both. Fable
must have an explicit direct-worker route and Controller-role routes; it must
not be reachable only after every cheaper option has failed.

### 4.1 A shared capability registry

Extend `tools/cells.py` and introduce data in `src/model_registry.json` for the
fifteen logical cells. Include exact requested/provider identifiers, supported
efforts, observed served identity, availability evidence, price snapshot/date,
role eligibility, model context/output limits and qualification status. Keep
deployment-local availability outside the shipped universal defaults.

All worker/controller adapters, diagnostics, cost projections and evaluators
use this resolver. Remove implicit "not Opus means Sonnet" mappings. Aliases,
availability substitution and environment overrides must be detected, billed
and labelled mismatches, not accepted as successful Fable/effort tests. Missing
identity evidence is unknown. Do not assume Fable's exact provider model ID.
Calibrate it from the installed host and a paid identity probe before use.

### 4.2 Starting allocation hypotheses

| Effort | Sonnet candidate use | Opus candidate use | Fable candidate use |
| :--- | :--- | :--- | :--- |
| low | Mechanical edits, extraction, simple checked implementation | Brief ambiguous choice needing stronger judgement | Short unfamiliar-domain decision where model breadth matters more than reasoning depth |
| medium | Bounded integration and evidence gathering | Cross-module diagnosis or bounded critique | Bounded cross-domain synthesis or disputed-frame triage |
| high | Known-pattern implementation with several edge cases | Subtle correctness, architecture framing and adversarial review | Novel mechanisms, research interpretation and difficult cross-domain framing |
| xhigh | Narrow deep reasoning when development comparisons beat a model switch | Coupled constraints, hard diagnosis and demanding review | Difficult search/reframing and complex alternatives beyond an Opus-supported route |
| max | Exceptional bounded verification/proof-like task if measured useful | Difficult formal or consistency reasoning where xhigh is insufficient | Frontier task with a concrete falsifiable goal and explicit affordable budget |

These are test assignments, not guarantees that each cell wins. Low-effort
Fable may beat high-effort Opus on some shapes; high-effort Sonnet may be a
waste on others. Measure model and effort independently. Never assume that
cost, quality or latency increase monotonically across this grid.

Initial role profiles to compare, expressed as registry references:

- `standard`: retain current Framer Opus-high, Verifier Sonnet-medium,
  Generators Sonnet-high, Critic Opus-medium, Selector Sonnet-medium.
- `frontier`: candidate Framer Fable-high/xhigh, two independent Generators
  from Opus-high/xhigh and Fable-high, Critic Fable-high/xhigh, cheap evidence
  collection and selection where qualified. Select one concrete version in
  development, rather than tuning all combinations in paid reserved runs.
- `operator-custom`: explicit role/cell overrides recorded as unqualified
  unless matching a calibrated profile. Preserve critic-class strength rules
  until evidence justifies changing them. Model-class rank is a policy prior,
  not proof of independence or correctness.

All five efforts must work end to end for supported worker cells. The current
Generator xhigh cap can remain a documented role constraint while max is used
for appropriate direct-worker/Framer/Critic work. Any extension of Generator
max requires its own measured ablation, not removal just for symmetry.

### 4.3 Cost-aware selection and escalation

Choose the lowest expected-cost qualified action meeting the task's quality
floor, time bound and risk constraints. For sparse evidence, use labelled
conservative rule priors and report uncertainty; do not invent probabilities.
Quality-sensitive work may choose Fable or Controller first. Routine work
normally remains Sonnet-low. Use a maximum of three worker attempts and one
Controller per task revision initially, with explicit skip paths.

Failure-specific transitions: unchanged evidence -> stop/clarify; syntax or
local defect -> one repair; reasoning error with a sound frame -> compare
higher effort against a model change; premise conflict -> Controller;
context overflow -> decompose/handoff. A stronger model does not fix an
unavailable tool, permission or missing user requirement.

Optional operator-supplied loss and delay values permit an expected-loss
calculation: task cost + probability of critical error * stated loss + stated
delay cost. Without those values show a quality/cost/latency Pareto comparison.
Do not reuse the old arbitrary consequence-dollar dial as measured economics.

Account for context and cache cost when choosing a cell. Keep role instructions
stable, attach only relevant evidence, and reuse bounded task packets rather
than whole conversation transcripts. Measure both cold and warm operation;
do not assume provider caches transfer between models or role prefixes. A
switch must earn back its added input, cache-write and latency cost through
expected quality or reduced retries. Diagnostic logs retain actual cache-read,
cache-write, ordinary input and reasoning/output usage where the host exposes
them; unsupported counters remain unknown, not invented savings.

## 5. Integration and interactive controls

### 5.1 One decision and dispatch contract

Keep `route.plan()` backward compatible through a versioned adapter. Add a
pure policy module, proposed `tools/controller_policy.py`, returning a
`RoutingDecision` with:

`decision_id, task_revision, policy_id, assessment_digest, recommended_action,
effective_action, selected_cell, controller_profile, override_mode,
override_scope, override_revision, reason_codes, evidence_ids,
qualification_status, cost_range, remaining_budget, next_checkpoint`.

Extend a thin production dispatch adapter, proposed `tools/controller_dispatch.py`,
around `run_quick`. Reuse the accounting/isolation primitives already proven
by the evaluation adapter, but do not import evaluator fixtures or hidden
grader code into consumer runtime. A routing verdict alone is not dispatch.
The orchestrator core, CLI and live episode executor must consume the same
decision semantics and actually invoke the requested path.

```text
operator intent + scoped settings -> evidence assessment -> policy recommendation
  -> apply operator override -> reserve whole-task allowance -> dispatch
  -> Controller if selected -> validate evidence packet -> selected worker
  -> independent visible acceptance -> close / bounded repair / clarify
```

Freeze operator constraints and acceptance contracts outside the Controller.
A Framer may propose a clarification or a changed interpretation; it cannot
silently relax those constraints. Source files and Controller reports are
untrusted content, never operator control commands.

### 5.2 Override semantics

Proposed interface, to implement and test before documenting as available:

```text
/controller status
/controller on --scope task
/controller off --scope session
/controller auto --scope project
/controller clear --scope session
/controller cancel <run-id>
/route --model fable --effort xhigh --scope task
```

CLI equivalents use structured flags, e.g. `route.py --controller on`,
`--worker-cell worker-fable-xhigh`, `--controller-profile frontier` and a
dedicated control subcommand for persistent scopes. `on` means execute
Controller before the next applicable worker action; `off` means no Controller;
`auto` explicitly delegates to the policy. `clear` removes a scoped override.
Changing a setting alone never starts paid work without an assigned task.

Precedence: explicit request/CLI > task setting > session setting > project
setting > shipped `auto`. An explicit `auto` at a narrower scope overrides
`on/off` at a wider scope; absence inherits. Reject contradictory flags in
one request. Omitted interactive scope defaults to the current task; when no
task exists, require an explicit scope rather than guessing. Plain language
such as "use the Controller for this task" writes that same task control and
echoes its scope. "Stop this Controller" cancels the named active run as well
as recording any requested future policy change.

Store project defaults in a local operator-owned config and task/session
overrides in an atomically updated control store keyed by canonical project,
session ID and task revision. Do not use a global last-session pointer or file
modification times to select an override. Separate concurrent sessions must
not leak state; compaction retains the same session; a fresh session inherits
only project settings. A task override survives its worker handoffs and ends
when that task closes. Delegated workers inherit effective task controls;
a model-generated child request cannot override an operator's setting. A
different child setting requires explicit operator intent at that scope.

Record the source operator message or CLI action with each control update.
Separate control mutation from normal dispatch arguments so a router or role
cannot manufacture a higher-precedence override. On hosts without verifiable
message provenance, report that limitation and require an operator-invoked
control command. This is an orchestration boundary, not a security guarantee
against an arbitrary same-user process editing local files.

Policy setting changes apply at the next safe dispatch boundary. Each role
admission rechecks the control revision before reserving money. `off` during a
Controller run stops new role admissions and preserves completed evidence;
running calls may still bill. `on` during worker execution queues Controller
for the next checkpoint, not a racing second worker. An explicit `cancel`
also signals supported process cancellation, retains uncertain billing and
never promises reversal of already applied edits.

Provide a short confirmation with requested/effective mode, scope, source,
pending work, estimated allowance and reason. Example:
`Controller ON (task override). Router suggested worker-only. Waiting for
current worker checkpoint; USD 4 Controller allowance within USD 8 task cap.`

Claude Code integration can use its documented project command/skill mechanism
and session-ID substitution. The command wrapper must call the structured
control API, not interpolate arbitrary `$ARGUMENTS` into shell text. Make
operator control user-invoked, not autonomously triggered by a role. In a
Codex session, support the same intent through CLI/tools and natural language;
do not claim that a Claude slash command automatically exists in Codex.
Platform support reference: [Claude Code skills](https://code.claude.com/docs/en/skills),
checked 2026-09-18. Validate actual installed-host behaviour in R3/R8.

### 5.3 Budget, persistence and useful incomplete output

Reserve one whole-task envelope with allocations for assessment, Controller,
implementation and acceptance. The Controller cannot consume the implementer's
entire allowance. Reconcile children once into the parent, including failed,
cancelled and auxiliary provider usage. Unknown charges remain reserved.

Initial experimental envelope: USD 8 per episode, at most USD 4 Controller,
USD 3 total workers and USD 1 routing/verification. This is an experiment dial,
not a universal suitable budget. R5 must reprice Fable and max before approving
it; if this envelope is inadequate, issue a new predeclared manifest before
running affected episodes. Never widen a cap after inspecting hidden grades.

Write a compact `ControllerEvidencePacket` with task/contract/input digests,
premise and candidate IDs, verified findings with relative artefact paths and
hashes, rejected hypotheses with evidence, remaining uncertainties, safe next
action and any proposed operator question. Exclude private scratch and raw
transcripts. Artefacts must be within the admitted snapshot and revalidated
if the repository changes. Reports from `gap` may supply verified facts but
must not be promoted into a completed solution. `dissolved` is independently
checked against the task contract. Invalid evidence is not forwarded.

The next worker reuses useful findings and runs its own required checks.
Persist the packet before stopping where possible. Process recovery restores
accounting and evidence, not an automatic replay of paid calls. Local quality
records are diagnostic until a versioned, held-out-qualified policy promotes
them; observational histories and operator overrides are selection-biased.

## 6. Staged delivery for GPT-5.6 Sol High

Each stage uses the current repo instructions and Graft MCP. Start with the
named files and reuse results; no full-repository reread or fresh agent merely
because a stage changes. One coherent change per work unit, tests matched to
its risk, and the full offline harness before bundle delivery. Retain failed
gate evidence, update this plan's checklist, and record exact next action in
a checked handoff if a real session/model transition is needed.

R0 must map the existing candidate-bound hash checks before code changes.
Preserve the old frozen artefacts for replay; never refresh historical hashes
to make a changed implementation appear previously qualified. Maintain source
and generated-bundle parity as required by each stage's checks, behind an
experimental policy selection. R8 promotes the default only after validation.

| Stage | Work and primary files | Required exit evidence | Effort estimate |
| :--- | :--- | :--- | :--- |
| R0 | Re-establish baseline, protect current docs, write decisions and desired-behaviour tests for the inspected gaps. Trace `route.py`, worker/Controller adapters and selection code. | Saved baseline; reproducible tests that distinguish observed gaps from hypotheses; agreed schema/override/risk contracts. No paid calls. | 2-4 h |
| R1 | **Complete.** Controller integrity: externally frozen acceptance, explicit stability handling, evidence-backed candidate eligibility, complete critique coverage and valid baseline fallback; add `ControllerEvidencePacket`. `system_controller.py`, record schemas, acceptance helpers. | Ten adversarial tests cover false stability, unsupported premise, stale baseline/selection, changed criteria, ignored exclusion, valid fallback, tampering, verified readiness and gap-with-valid-evidence. Existing quick-mode history remains replayable as `legacy-quick-v0`. See [R1 record](CONTROLLER-ROUTING-R1.md). | 6-12 h |
| R2 | **Complete.** Full cell registry and resolver; update `cells.py`, live worker/runner identity helpers, role profiles, projections and diagnostics. | Eight registry tests build exact fake commands for all 15 cells; unsupported cells and silent substitution fail visibly; exact Fable mapping and all five efforts are reachable; null prices remain unknown. See [R2 record](CONTROLLER-ROUTING-R2.md). No paid calls. | 4-8 h |
| R3 | **Complete.** Durable `auto/on/off` scopes, natural-language/interactive wrapper, CLI parity, override precedence, cancellation and concurrent-session handling. | Fourteen control tests and full bundle gate passed. See [R3 record](CONTROLLER-ROUTING-R3.md). | 5-10 h |
| R4 | **Complete.** Versioned assessment and policy, production dispatcher, worker handoff, task budget and evidence reuse. | Twenty-eight policy/dispatch tests reach the real adapter under mocks, preserve the high-risk public-pass check and prevent replay/double charging. See [R4 record](CONTROLLER-ROUTING-R4.md). | 6-12 h |
| R5 | **Offline implementation complete; live work pending.** New corpus, protected milestone graders, scoring/reporting, crash-safe identity and 15-cell calibration runtime, then six-task three-arm live pilot. Evaluation protocol sections 2-5. | Offline mutants/isolation pass; actual Fable and efforts proven; four automatic live Controller entries including a frontier-role profile, with at least one successful end-to-end handoff; failed/gap accounting exercised. See [R5 record](CONTROLLER-ROUTING-R5.md). | 6-12 h engineering plus paid runtime |
| R6 | Development policy/role-profile comparisons, economical single-worker control, cost/effort screening and paired rescue/continuation probes. | Frozen feature rules and cell choices, paired quality/cost results, documented rejected options and calibrated future spend range. | 4-8 h analysis plus paid runtime |
| R7 | Freeze candidate and run reserved S-versus-A comparison under the predeclared gates. No tuning from reserved observations. | Promotion, rejection or inconclusive report with paired intervals, critical-error table, partial progress and spend reconciliation. | 3-6 h plus paid runtime |
| R8 | Package validated auto default, controls, profile registry and docs; clean install/update/rollback; interactive host smoke and cold-start consumer checks. | Source/bundle parity, manifest hashes, full harness, verified interactive commands, fresh-install auto behaviour and exact B0 rollback. | 4-8 h plus smoke runtime |

Estimated engineering/analysis total: 40-80 hours, approximately 5-10 working
days, plus paid evaluation runtime and review. This is a planning range, not a
model-runtime guarantee. R0 is the first implementation work unit after plan
review; no paid evaluation is triggered by this plan.

### 6.1 R1 choices the implementation session must not guess

- Distinguish `verified_ready`, `provisional_guidance` and `blocked`, separately
  from execution status. A budget gap can carry reusable facts.
- Initial vNext automatic path: unstable material premises yield provisional
  guidance/clarification, never a claimed verified solution. Do not require
  proving every harmless premise to complete routine work.
- Apply deterministic eligibility (current ledger, required critiques,
  contract preservation, artefact provenance, known exclusions) before the
  Selector's ranking can choose among survivors. Check baseline B0 by the
  same material constraints. If none qualifies, return a gap.
- Preserve current first-survivor behaviour only behind the explicitly named
  historical quick-mode policy for comparison/replay. Do not silently change
  the meaning of the earlier benchmark.
- The revised ranking is still model judgement, not external verification.
  Final implementation acceptance and measured decision rubrics remain separate.
- Critic claims trigger re-verification or a qualified uncertainty record;
  a critic's assertion alone must not become a verified negative premise.

### 6.2 Mandatory cross-cutting regression cases

Test all modes and precedence pairs, explicit auto versus inherited off,
malformed controls, accidental prompt-injected overrides, conflicting session
IDs, control revision races, replayed decision IDs, cancellation after dispatch,
crash before/after settlement, uncertain invoices, identity substitution,
effort override, Fable availability failure, missing prices, task budget
exhaustion, no useful evidence, invalid report hashes, actor changes, unsafe
paths/symlinks, partial reports, duplicated work and untrusted report commands.

Add reachability fixtures for every cell and workflow, including direct Fable
and max. Verify platform frontmatter/CLI settings and served identity
separately. A mocked effort flag proves wiring only. Preserve legacy B0/B1/B2
fixtures and decisions; new policy IDs and schemas need explicit adapters.

## 7. Validation and promotion

The companion protocol defines matched task families, external scoring,
partial progress, blinded grading, continuation probes, a 15-cell screen,
cost caps and statistical gates. Do not run another broad benchmark in which
the Controller never fires and describe it as Controller validation.

The rollout target is a new `rigour-auto-v1` default for qualifying tasks,
with manual `on/off` always accessible. The old B0 remains a named rollback.
If the candidate fails reserved gates, retain operator controls and publish
the failed hypotheses; do not silently declare success or retune against the
same reserved tasks. A new candidate needs new reserved evidence.

## 8. Cost and model handoff

Recommended executor: **GPT-5.6 Sol, high reasoning** for all bounded R0-R8
implementation work. This is an execution choice, not a claim that Sol is
equivalent to any Claude cell. Do not switch models solely because a stage
ended. Stop for an unresolved architecture/metric contract instead of inventing
a local policy; report it with the failed gate and a minimal reproduction.

Official [Sol model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [API pricing](https://developers.openai.com/api/docs/pricing), checked
2026-09-18: standard short-context USD 4/M input, 0.40/M cached input, 5/M
cache writes where separately billed, 20/M output including billed reasoning.
Use mutually exclusive usage categories and the actual endpoint's usage.
No assumed cache hit may be counted as a realised saving. Fast/priority is
approximately twice these standard rates; confirm the chosen session tier.
Requests above 272k input tokens have separate higher pricing.

R0 estimate: 0.10-0.25M ordinary input, 0.02-0.05M cache writes,
0.20-0.60M cache reads, 0.02-0.05M output. Arithmetic USD 0.98-2.49 standard,
or USD 1.96-4.98 fast, before 30% contingency. Budget **USD 2-7
API-equivalent** and **2-4 hours** for the first handoff. These are token
assumptions, not a Codex subscription bill. No Claude calls in R0.

Whole development envelope: 1-3M input, 0.2-0.6M writes, 3-10M reads,
0.2-0.6M output -> USD 10.20-31 standard, USD 20.40-62 fast; with 30%
contingency, round to **USD 15-85 API-equivalent**. Reprice if the work exceeds
these assumptions. Paid Claude experiments are separate: provisional core
campaign **USD 300-700 expected**, **USD 1,800 proposed dispatch ceiling**,
released in gated tranches, not charged or approved now. Fable/max costs and
completion under those caps are unmeasured; R5 must replace these estimates.

## 9. Completion record

- [x] Repository-grounded proposal and review summary prepared.
- [x] Separate evaluation protocol and Sol High R0 handoff written.
- [x] Operator review accepted; execution directed on 2026-09-18.
- [x] R0 baseline and decisions complete: [R0 record](CONTROLLER-ROUTING-R0.md),
  machine-readable baseline and v1 contracts; no runtime policy change.
- [x] R1 Controller integrity complete: [R1 record](CONTROLLER-ROUTING-R1.md).
- [x] R2 full registry and identity support complete: [R2 record](CONTROLLER-ROUTING-R2.md).
- [x] R3 operator controls complete: [R3 record](CONTROLLER-ROUTING-R3.md).
- [x] R4 policy and dispatch complete: [R4 record](CONTROLLER-ROUTING-R4.md).
- [ ] R5 corpus, identity screen and pilot complete. The provider-free
  [R5 evaluation implementation](CONTROLLER-ROUTING-R5.md) is complete: all 48
  tasks, 288 variants, protected graders and crash-safe launch runtimes pass
  offline checks. The paid matrix and subsequent pilot evidence remain.
- [ ] R6 development policy frozen.
- [ ] R7 reserved gates adjudicated.
- [ ] R8 qualified bundle and interactive installation verified.

Update this checklist only with paths to evidence, observed costs, actual
model/effort and unresolved limits. Runtime functionality is unchanged by
this planning task; existing working-tree changes remain uncommitted.

Planning validation on 2026-09-18: Graft graph/wiring freshness passed; the
generated handoff, local document links, budget arithmetic and `git diff --check`
passed. The complete offline harness passed **51/51 checks** with required
child-process access. Its sandboxed run had passed 49/51; the two failures
cleared on the full rerun without code changes. No paid provider calls were made.

R0 completion validation on 2026-09-18: the focused contract/characterisation
suite passed 6/6 and the expanded offline harness passed **52/52 checks**. The
runtime default and redistributable remain B0; no provider calls were made.

R1 completion validation on 2026-09-18: integrity-v1 became the Controller's
default direct-run policy while the qualified router remained B0. The focused
integrity suite passed 10/10, the historical suite passed 6/6 and Controller
self-test passed 12/12. The rebuilt 61-file distribution matched source and the
full offline harness passed **53/53 checks**. The Graft deep index closed with
zero stale or pending semantics. No provider calls were made.

R2 completion validation on 2026-09-18: the 15-cell registry suite passed 8/8,
the rebuilt 63-file distribution matched source and the full offline harness
passed **54/54 checks**. Fake dispatch covered every model/effort cell and
rejected silent substitution. Fable live identity, prices and quality remain
explicitly unqualified for R5. No provider calls were made.

R3 completion validation on 2026-09-18: the focused provider-free control
suite passed 14/14, the rebuilt 65-file distribution matched source and the
full offline harness passed **55/55 checks**. The approved deep Graft refresh
closed at 2,155 nodes, 4,366 edges and 423 cards, with zero stale or pending
meanings. No Claude worker, Controller, grading, or other paid task dispatch
occurred; Graft used its separately configured DeepSeek semantic service.

R4 completion validation on 2026-09-18: the pure `rigour-auto-v1` policy and
crash-safe dispatcher passed 28/28 focused cases. The rebuilt 69-file
distribution matched source and the complete offline harness passed **56/56
checks**. B0 remains the automatic shipping default; the R4 path is available
for explicit use and evaluation only. No Claude worker, Controller, grading,
or other paid task dispatch occurred; Graft used its separately configured
DeepSeek semantic service. The deep refresh closed at 2,209 nodes, 4,531 edges
and 426 cards, with zero stale or pending meanings; semantic and wiring
freshness checks passed.

R5 offline validation on 2026-09-18: the 48-task declarative corpus, 288
labelled variants, protected grader, 60-call matrix runtime and 18-episode
pilot runtime passed **33/33 focused checks** using fake transports. The matrix
manifest is content-addressed, has a USD 48.75 hard ceiling and remains
unauthorised. The pilot is execution-disabled pending matrix evidence and a
later authorisation. No Claude calls were made.

The final R5 offline deep Graft refresh closed at 2,284 nodes, 4,736 edges and
431 cards with zero stale or pending meanings. Semantic and wiring freshness
checks passed.
