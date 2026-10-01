# Controller remediation: X0 integration and evaluation contract

Version: `controller-remediation-x0-v1`. Date: 2026-09-27.
Scope: X1-X8 implementation contract. This is a design freeze, not a shipped
capability or authorisation to promote a policy. The
[stage record](stage-results/controller-x0-2026-09-27.md) and
[offline probes](../test/results/2026-09-27-controller-x0-probes.json) distinguish
observed defects from this design. The [programme](CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md)
owns stage ordering and the operator's standing execution direction.

## 1. Baseline and decisions

N8 delivered the durable B0 CLI and bundle at `2026-09-27-15ecf66-dirty`.
N7 rejected Q4U default promotion; N6 stopped before reserved comparison.
Use B0 as the worker control. N3 remains a shadow selector. Its `assess()`
validates structured public facts; it does not infer them from task prose.
No new worker-only automatic policy is implied by Controller remediation.

X0 reproduced six defect classes: settled-failure campaign restart,
unbound-dependency acceptance, public-label-only full credit, label-derived
assessment/canned clarification, first-Generator-only dispatch and two
Controller admissions for one task revision. It also reproduced loss of known
cost in the pilot's blocked-result projection. None is a paid incident claim.

The 24-task X6 comparison is **exploratory only, with no promotion authority**.
This applies even if all its estimated quality/cost thresholds look favourable.
Keep the existing default unless a subsequent, separately frozen confirmation
programme supports the desired claim. Do not buy an automatic sample expansion.
X7 can still decide mechanical readiness and labelled manual availability.

## 2. Ownership and data flow

Use one durable root task and its existing N1 monetary owner. A Controller is
an allocated workflow step, never a new task scheduler or independent purse.

| Boundary | Input | Output | Owner and prohibition |
| :--- | :--- | :--- | :--- |
| Public evidence collection | Goal, frozen acceptance, permitted source spans and observed failures | Hashed public observations with references and uncertainty | Production assessment path; cannot see family/split/oracle/expected action |
| Worker assessment and selection | Validated N3 public facts, host capabilities and root balance | B0 effective cell plus labelled shadow recommendation | Existing selector; cannot admit or silently promote a candidate |
| Workflow decision | Public rigour assessment, effective operator control, qualification and budget | Worker, Controller, clarify or blocked; reasons and next checkpoint | Versioned Controller policy; cannot create authority |
| Role plan | Explicit or eligible profile, technique subset and allowance | Immutable per-invocation assignments and caps | Registry plus role planner; cannot collapse requested cells to fit budget |
| Admission and execution | Decision, task revision, authority, capability and reservations | Durable intent, receipts and evidence | N1 executor; sole root lifecycle and cancellation owner |
| Acceptance | Frozen contract plus independently observed output | Verified accepted, failed, partial, clarification or blocked evidence | Acceptance owner; Controller output is never acceptance authority |

### Public assessment bridge, owned by X3/X4

Add one production bridge that collects a bounded evidence packet and calls
`worker_selector.assess()` for the existing worker facts. Produce the separate
rigour assessment from the same public packet. Name consequence, premise
uncertainty, material alternatives, constraint coupling, verification gap,
failure cause and unavailable operator decisions explicitly. Each asserted
fact needs a source span or tool receipt; an inaccessible fact remains unknown.
Structured observations can be collected deterministically. If an LLM is
needed to interpret them, use a versioned prompt/schema and record its cell,
tokens, cost, timeout and failure. Do not add an unpriced assessor outside the
root budget. The bridge is the same callable in the interactive and campaign
paths; unit-test injections must not reach live comparison arms.

Changing family metadata while holding the entire public packet fixed must
not change assessment. Merely rejecting a `family_id` key is insufficient:
inspect tool visibility, inherited instructions, Graft scope and prompts for
labels or solution hints. Equivalent wording with equivalent facts should
preserve routing, but disagreement on genuinely different evidence is valid.

## 3. Identity, admission and recovery, owned by X1/X2

Retain N1's immutable definition and revision. Model/profile/settings changes
create decisions, not fresh task revisions or allowances. Keep the legacy
Controller hash in a versioned mapping to the N1 root/task/revision, acceptance
digest, input digest and authority reference. Validate old packets in their
original namespace before validating the mapping. Never rewrite old evidence.

At a reactive checkpoint, capture the stopped worker's current artefacts as a
separate evidence snapshot. The Controller's legacy input hash describes that
read view; the mapping binds it to the unchanged N1 definition and revision.
Do not overwrite the admitted input or acceptance baseline with failed worker
output. Source-revision checks exclude only enumerated executor-owned runtime
paths; they must still detect changes to user inputs during read-only analysis.

Add a durable Controller admission record under the existing task journal:
version, root/task/revision, decision digest/generation, intervention ordinal,
authority reference, legacy mapping digest, profile/assignment digest,
capability digest, budget allocation ids and cancellation generation.
The exact serialised schema must be frozen with X2 tests before migration.
Unknown versions/fields fail closed. Do not leave the record in a caller's
counter, session memory or decision-specific directory alone.

The task lock checks the complete admission predicate and commits the record
and its dispatch intent before any adapter call. One automatic Controller
intervention is allowed per revision. Competing decisions, changed overrides,
restarts and profile changes cannot reset that allowance. An explicit further
intervention needs recorded operator authority and settled predecessor writers
and charges under the same root balance. Root intent recovery must reconcile
partially committed budget/journal operations, never grant a second allowance.

Keep N1's lifecycle states. A workflow substate records assessment, Controller
admission, Controller execution, evidence validation and worker readiness;
it cannot bypass cancellation or verification guards. Do not mark a task
accepted because its Controller produced a solution or useful gap. Keep the
worker attempt slots separate from Controller invocation counts.

For campaigns, use a campaign lock and per-invocation intent. Completed,
stopped, cancelled and accounting-uncertain campaigns cannot dispatch again
through ordinary `execute`. Recovery only projects evidence and settles known
charges. An authorised continuation is a new immutable schedule linked to the
old campaign and its outstanding/consumed root allowance. It never edits the
old manifest, resets spend, retries a failed row invisibly or promotes a new
input revision to evade an invocation cap.

Cancellation records operator intent immediately, signals every owned active
process tree and prevents later admission. Late receipts may settle costs and
retain useful evidence but cannot turn a cancelled task into worker-ready or
accepted. A missing termination proof retains the writer barrier even when a
charge is known. Tests must cancel during a Controller call and its return,
not only before dispatch. The general host's unproved process isolation remains
an explicit capability limitation until separately exercised.

## 4. Complete execution binding, owned by X1/X3

Create newly versioned manifests from current source; preserve historical
R/Q/N manifests and receipts. Bind the actual runnable package, not only a
curated list of top-level Python modules. The manifest identifies:

- First-party execution source, import closure and explicit dynamic imports.
- Controller and worker prompts, role/technique instructions, schemas,
  registry, policy, cost assumptions and acceptance/grading definitions.
- Public corpus package, protected oracle package, reference and attack variants.
- Interpreter, dependencies, Claude Code version and relevant non-secret
  settings; host isolation/runtime attestation and Graft visibility.
- Ordered schedule, unique row ids, per-call/per-task/campaign allowances,
  timeout/continuation limits, analysis version and applicable authority.

Materialise an immutable runtime package whose exact file inventory and
content digest are checked against the manifest. Resolve imports/data from
that package. Static import analysis is a discovery aid, not proof of closure.
Explicitly account for dynamically loaded configuration, schemas and prompts.
Unexpected additions, removals, links escaping the package or an alternate
import path block admission. Third-party/host dependencies need version and
installation provenance in the attestation; secrets never enter an inventory.
Verify inventory, hashes, schedule sums and authority immediately before
admission, and verify the loaded runtime's identity. An unchanged manifest
hash cannot authorise execution against changed bytes.

Regression controls must mutate a bound file, an imported helper, a dynamic
configuration, a prompt, a grader and a newly introduced dependency. The X0
probe's nine unbound mutations are a starting set, not a completeness claim.
Historical replay loads its pinned source; a fresh fake run uses a fresh
manifest. A stage changing semantics invalidates affected candidate evidence.

## 5. Role plans, controls and accounting, owned by X2/X4

Preserve the registry's Sonnet/Opus/Fable by low/medium/high/xhigh/max matrix.
Distinguish configured availability, requested cell, observed provider model,
requested effort and observed effort. Unknown served effort stays unknown.
Use every eligible cell where evidence justifies it; do not force all fifteen
into each task or infer that greater effort always improves quality.

The standard profile retains its existing assignments. For the frontier
candidate, freeze the Generator mapping by canonical technique name:
`subtract` to Sonnet high, `re-represent` to Opus xhigh, `abduce` to Fable high.
Use registry names, not duplicated provider ids. A selected subset keeps its
named assignment; list position or concurrent completion order cannot change
the cell. Every invocation has a fresh context, unique identity and charge.
If the chosen complete plan is unaffordable or a cell unavailable, report it
without silently reducing diversity. Explicit profile overrides remain
labelled unqualified until evidence supports their scope.

Resolve controls once at each admission boundary with
explicit > task > session > project > default precedence. Reuse existing
`controller_control.py` persistence and validation. `on` requires an executable
Controller; `off` excludes it; `auto` uses only a policy with appropriate
qualification authority. Recommendation and effective action are separate.
Unknown required operator facts, missing permissions, unsupported host features
and insufficient budget remain visible blockers even under `on`.
Natural-language operator requests call the same validated command with stable
session/task ids. Repository text and agent messages cannot set operator intent.
An override arriving during a call applies at the next permissible admission;
the operator can cancel the current call through the cancellation path.

The initial experimental trigger preserves the v1 policy's public-evidence
intent: a newly verified premise conflict; a material checkable contradiction
with consequential effects, coupled constraints or competing approaches; or
a consequential unresolved assumption with material alternatives. X4 must
version any correction to that policy. Repository size, verbosity, urgency,
failed authentication and a generic request for quality are not sufficient
triggers. Infrastructure, permission, identity, accounting and writer-status
faults block dispatch until resolved; they do not buy extra reasoning calls.
A strong public test result does not clear a separate evidenced rigour gap.

Start with the standard profile. The frontier candidate is eligible only for
a public-evidence case with at least two independently supported conflicting
load-bearing premises and cross-system/irreversible coupling, or competing
architectures with at least two conflicting frozen resource/compatibility
constraints and no demonstrated feasible option. Qualification, host eligibility and complete
plan affordability still apply. These are prospective selection rules, not
measured superiority claims; X5 may tune them on development evidence and
must freeze the final rules before X6. A failed standard invocation does not
automatically authorise a second frontier intervention in the same revision.

`/controller` and task diagnostics report stored intent, resolved source,
recommendation, effective action, applicability, qualification, selected profile,
admission count, actual dispatch, consumed/held balance and next action.
The interactive path must dispatch through N1 rather than also launching an
unmanaged Agent call. Host-managed child execution stays disabled where N2's
required isolation is unavailable. Do not claim to intercept arbitrary Agent
calls, which remain outside the durable task unless explicitly integrated.

Before Controller admission, reserve the required worker/verification allowance
under the same root. A profile cannot spend it speculatively. Root accounting
includes assessment, Controller classification and roles, workers, independent
verification and any paid grading. Nested budgets allocate from that root and
are reported once; their charges are not added to the parent's charge again.
Known settled cost remains numeric on failed, blocked, gap and clarification
paths; outstanding holds are separate. Unknown cost is null, never zero.
In-flight provider overruns stop further admission and remain recorded.

Controller packets carry validated evidence with provenance, rejected hypotheses,
uncertainty and a bounded next action. Hash validation proves identity, not
truth. Worker and acceptance checks must verify decisive findings. A dissolved
problem requires independent acceptance confirmation; a useful partial report
can guide continuation but cannot certify completion. Preserve the original
acceptance and prohibited changes throughout.

## 6. Corpus and grading contract, owned by X3

Retain R5 as a plumbing fixture. Create a new version with 24 development and
24 untouched reserved tasks across the existing 12 families, two per family
per split, with independent mechanisms. Development cases already used in N/Q
selection or review cannot become reserved cases. Use real code/data/traces
and executable or independently reviewable outcomes. Preserve licences and
pin GitHub source commits when importing a project. A new filename or wording
of the same mechanism is not an independent task.

The protected evaluator derives outcomes from artefacts and behavioural checks
in an evaluator-owned process. Never import actor code into the trusted process
that calculates scores or serialises the final grade. Execute actor code under
an isolated child principal and treat its stdout, exit status and JSON as
untrusted observations. The parent owns expected results, comparison and score
serialisation. N7's `json.dumps` monkeypatch attack and equivalent forged
stdout, module shadowing, descendant writes and altered public checks must fail.
No actor tools, Graft instance, inherited instructions or search path may expose
protected oracles, reference solutions, family labels or the runtime package.

Keep quality weights M/E/D/N/H = 40/25/15/10/10, but replace evidence-id credit:

| Dimension | Credit must come from |
| :--- | :--- |
| M: milestone progress | Frozen task-specific behavioural assertions or independently checked artefacts |
| E: evidence | Reproducible observations supported by trusted receipts, not cited id membership |
| D: diagnosis | A discriminating test or observation ruling in the mechanism and challenging alternatives |
| N: next step | A feasible safe continuation satisfying current constraints; test it in matched continuation probes where possible |
| H: reporting | Accurate completion/uncertainty claims compared with evaluator observations |

Critical violations dominate and force quality zero. Determine prohibited edits
from controlled filesystem/diff and execution evidence, not a `mutations` list.
Report full acceptance, accepted clarification/no-change, useful partial,
no useful progress, wrong and critical violation separately. Report false
success independently. A schema-valid report, cited milestone, public-test pass
or persuasive explanation earns no unverified behavioural credit.

Every task has baseline/no-progress, reference, equivalent solution, useful
partial, confident wrong, label-copy and concealed-harm controls. Validate that
partial improvement outranks no progress without becoming accepted. Reference
and equivalent solutions must satisfy the same protected acceptance definition.
For subjective work, freeze a blinded rubric and calibrate it against known
controls before live runs; graders must not infer treatment/model from reports.
Clarification is produced by the common production path, never `_clarification_result`.

## 7. Comparison and analysis freeze, owned by X3/X5/X6

X5 first proves identity, accounting and actual integration on development
tasks. Reuse only host-compatible model evidence; price any missing refresh.
Keep served-effort limitations visible. Run no live Controller evaluation until
X1-X4 gates pass, including a complete fake production path.

The baseline S is B0 plus the common assessment/execution envelope. A uses
the same envelope and B0 worker policy plus the experimental rigour decision.
All assessment/verification costs are included in both. B0 escalation rules,
acceptance and attempt ceilings are equal. Controller instructions are the
intended intervention; unrelated differences in worker prompts, tools, context
or clarification handling are confounders and must be removed.

Since B and S use the same qualified worker policy now, the B/S labels may
share one execution **only if their complete treatment fingerprints match**:
assessment, prompts, runtime, tools, policy, caps and verification. Record the
alias before scheduling and attribute the charge once. If they differ, run both
and explain the intended difference. No duplicate observation counts as an
independent replication. This can reduce the six-task pilot from 18 to 12
episodes and the additional 12-task comparison from 36 to 24; they are maxima,
not a reason to fill unused budget. Preserve four automatic Controller
admissions, one frontier exercise, verified end-to-end completion, a real
clarification result and reconciled gap/failed paths in the pilot.

X6 remains capped at 24 new tasks, 16 suitable and 8 controls, two repetitions
per arm S/A, 96 episodes. Freeze package, policy, role assignments, costs,
rubric, task grouping, random seed and order before reserved outcomes are
available. Counterbalance order within task/repetition; record cache and host
conditions. Do not tune on held-out results or replace failed tasks post hoc.

Compute each task's mean A-minus-S acceptance and quality across repetitions.
Tasks, not episodes, are the replication unit. Give equal weight to the frozen
family composition. Report per-family and suitable/control outcomes plus raw
per-attempt records. The exploratory quality interval uses paired hierarchical
bootstrap: sample families, then task deltas within family, preserving the
two arms and both repetitions. Use seed 27092026, 10,000 resamples and the
2.5/97.5 percentiles. Report family-only and task-only sensitivity and degenerate
intervals; none overrides the exploratory-only decision.

Report candidate-only acceptance harm and critical/false-success events per
task, counting any affected repetition. Give exact binomial bounds only under
their stated independence assumption; clustered families can invalidate that
assumption. Do not use a bootstrap [0,0] from no observed failures to certify
non-inferiority. The proposed -5 percentage-point acceptance and +5/100 suitable
quality margins remain diagnostic thresholds. Also report overall quality
against -5/100, no unexpected automatic Controller use on ordinary controls,
cost ratio <=1.5 and p95 latency ratio <=2. Tail estimates from this sample
are descriptive. A zero denominator, missing receipt or unmatched pair makes
the affected comparison unavailable, never favourable by default.

Every attempted episode counts. Budget/time stops score the artefact actually
obtained at the frozen deadline; verified partial work is retained. Missing
grades remain missing with worst/best bounded sensitivity, not silently
dropped. Infrastructure failure is separate from task-quality failure but
does not erase spend. Publish full cost and quality jointly so a cheap censored
attempt cannot look efficient merely because it did little work.

Continuation probes use a shared producer artefact and matched continuations
with/without the validated findings. Charge the producer once in spend totals;
show both full and amortised cost per comparison. No continuation may mutate
the producer evidence or regrade a completed reserved task as a fresh task.

## 8. Feasibility decision and release authority

The [offline feasibility result](../test/results/2026-09-27-controller-x0-power.json)
uses hypothetical distributions, not measured Controller outcomes. Zero
candidate-only harms in 24 independent tasks gives a one-sided 95% upper bound
of 11.735%; 16 gives 17.075%. Even the favourable zero-event case needs 59
independent tasks to put that bound below 5%. This is a harm-rate bound, not
a paired difference interval or proof that 59 suffices for every release gate.
The exact-binomial treatment follows [NIST's confidence-interval reference](https://itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

For 16 suitable tasks, a hypothetical mean quality gain of 6/100 cleared the
strict lower-bound >5 gate in only 2.3-4.7% of 600 simulations. A 13/100 gain
cleared it in 47.2-53.5%. Simulated interval coverage fell to 89.2% for one
family-correlated scenario. The Monte Carlo standard errors and seeds are in
the result. These simulations assess one gate, not joint promotion power.
Paired resampling preserves paired observations; see the
[SciPy bootstrap reference](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
Our implementation also samples families and uses the standard library.

X6 therefore informs whether an extension is economically justified, with
no automatic-promotion authority. X7 records rejected, inconclusive or promising
exploratory evidence separately from mechanical safety. Before any extension,
freeze a new sample, practical effect, correlated-outcome sensitivity, error
control and all-gate power analysis using only development assumptions. The
operator decides material scope/budget tradeoffs that evidence cannot settle.
No threshold relaxation after seeing reserved outcomes is permitted.

X8 can ship safe, explicitly experimental manual controls while B0 stays
default. Automatic Controller adoption requires independent confirmation and
an explicit scoped release decision. Rollback retains task/control/charge
records and rejects relaunch while any predecessor writer or hold is unresolved.
Historical Controller state is imported read-only for audit; migrations never
auto-resume it. New state needs explicit legacy-to-v2 mapping and reconciliation.

## 9. Stage acceptance matrix and migration sequence

| Owner | Required falsification/regression checks | Exit artefacts |
| :--- | :--- | :--- |
| X1 | Matrix and pilot settled-failure restart dispatch zero new calls; cancelled/uncertain terminal states stay closed; duplicate drivers admit once; dynamic/added dependency mutation blocks; settled failed cost reaches summary; recovery performs no calls | Versioned campaign format, complete runtime inventory, reconciliation and continuation evidence |
| X2 | Two decisions for one revision admit once; changed settings/profile/restart do not reset count; Generator captured dispatch matches technique mapping; independent prompts and root accounting hold; cancellation wins over late success | Revision mapping, admission schema and role plan with current-source tests |
| X3 | Label-copy and N7 monkeypatch/forged-output attacks fail; references/equivalents pass; useful partial survives; family labels cannot affect identical public assessments; clarification has no canned answer | New corpus/isolated grader version, calibration and paired analysis code |
| X4 | Full N1 path covers auto/on/off, interactive and natural-language commands, exact roles/cells, useful gap, immutable acceptance, unaffordable profile, cancellation/restart, compaction and rollback audit | Production integration and updated host capability contract |
| X5 | Instrumented pilot satisfies actual dispatch/clarification/accounting conditions; all paid attempts reconciled; controls/costs comparable | Development results and frozen candidate; stop if mechanics fail |
| X6 | Frozen exploratory comparison, no hidden retries or tuning, all-attempt accounting and bounded missingness analysis | Immutable results, intervals, limitations and explicit no-promotion flag |
| X7 | Independent challenge of causal fairness, scoring, diversity, cancellation, ownership and partial utility | Mechanical/research disposition; extension decision if justified |
| X8 | Built consumer clean install/upgrade/rollback and interactive proof on supported hosts; safe persisted-state migration | Maintained documentation, generated dist, release evidence and unresolved limits |

Before touching a shared runtime, record which historical campaigns import it
and preserve their pinned replay source. X1 changes campaign tools first; X2
introduces task-wide admission and role planning; X3 establishes grading and
assessment; X4 integrates the N1 executor extension. Reuse existing budget,
registry, control and acceptance modules. Do not run later-stage paid work to
compensate for an earlier failed mechanical gate.
