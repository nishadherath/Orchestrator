# Post-RC qualification: outstanding work, sequence and risk

Date: 2026-10-02, Australia/Sydney.

Status: evidence review and proposed next programme. This document records the
analysis requested after RC preparation. It does not launch an experiment,
reopen a stopped campaign, approve spending, or promote a policy. The operator
deferred Controller qualification and a separate policy pilot from the RC.

## 1. What we want to achieve

We want reliable completion of user tasks at a defensible total cost, with
truthful verification and safe recovery. Controller is one possible means of
achieving that outcome. Its value would be to resolve competing explanations,
find a missing constraint, or produce a useful investigation result that lets
the subsequent worker succeed where an ordinary continuation does not.

The qualification goal is to determine **whether, where and under what limits
Controller improves outcomes**. A successful research programme can conclude
that it should remain an explicitly selected experimental option. We cannot
promise a positive uplift result, and should not manufacture one by weakening
the baseline, selecting favourable failures or changing a grader after a run.

There are three distinct claims to establish:

1. **Mechanism:** at the same initial task state, does adding Controller improve
   the next worker's verified result, with equal public evidence and an intact
   acceptance contract?
2. **Practical value:** is that improvement worth its extra calls, delay and
   operator burden compared with another worker attempt or a stronger worker?
3. **Policy value:** across the intended mix of complete user tasks, can a
   deployable rule choose those interventions often enough, and avoid unnecessary
   interventions well enough, to improve the whole service?

Passing the first claim does not establish the other two. The separate policy
pilot answers the third question and includes all ordinary tasks, screening
costs, failed interventions and recovery. Controller-specific studies focus on
the first two questions. Both depend on sound measurement and host evidence.

The current RC can be published within its stated B0 and experimental-Controller
scope without a positive Controller result. The [bounded RC contract](RELEASE-CANDIDATE-2026-10-01.md)
explicitly separates packaging readiness from this unfinished qualification.

## 2. Reconciled status: what is complete and what remains open

Some earlier plans retain obsolete status paragraphs above later completion
records. Their titles and unchecked historical prerequisites must not be read
as instructions to repeat completed work.

| Work | Recorded position | Consequence for the next programme |
| :--- | :--- | :--- |
| Current RC | Source commit `f9f141cb38e48e15b96e5eef69b81e33be00d3b6`; clean bundle stamp `2026-10-02-f9f141c`; recorded full harness 83/83 PASS; 85-file archive and install lifecycle PASS | Preserve that release baseline. Publication is a separate operator action. These results establish the recorded mechanical scope. |
| Current account identity | Dated Sonnet-low and Opus-high probes returned the registered provider IDs on the recorded account and CLI | Reuse only for matching account, host, adapter and freshness requirements. This does not verify every effort, frontier profile, WSL transport or quality claim. |
| X5 v7 continuation | All 12 previously unrun positions completed; combined v6/v7 evidence gave no Controller gain on the four suitable cases | V7 is closed negative development evidence. There are no remaining v7 episodes to run. |
| Later recovery and public-risk studies | Several stopped before a usable pair. H02 produced equal protected scores with an unqualified A handoff. H03b stopped at public failure and had no private score | These are development observations and regression inputs. Their stopped roots and frozen grades stay closed. |
| Controller uplift | Not established | Requires a new prospectively defined candidate, sound measurement, fair comparisons and confirmation. |
| Controller X6-X8 | Not entered for the rejected v7 candidate | A new development gate must be passed before a new reserved comparison. A recorded disposition is not a completed experiment. |
| Earlier real-world W programme | Pilot, development, reserved comparison and W09 packaging completed; B1 rejected and B0 retained | The old six-, eighteen-, thirty-two- and forty-eight-episode schedules are historical. A separate current policy pilot needs a new plan and fresh evidence. |
| Broader runtime claims | General filesystem confinement, descendant termination, served effort and general frontier suitability remain unqualified; the general adapter rejects live managed children | Qualify only the capabilities needed by the proposed experiment or supported product expansion. |

The current RC evidence is [the recorded harness status](../test/results/2026-10-02-harness-status.json)
and [archive verification](../test/results/2026-10-01-rc/verification.json).
The bundle SHA-256 is
`783861afe26a8b65fa93194d9d3fbcaeedac9bc72278d5c2c1fe4fb3051d63ed`.
The verification file is generated output; the archive hash identifies the
specific bytes described here. This documentation change does not rebuild or
revalidate a different product bundle.

The shipping B0 policy starts with Sonnet low, allows one same-cell repair after
observable failure, then one Opus-high fallback if needed and affordable. It
does not automatically promote Controller or change dispatch from learned
priors. The baseline must retain those real recovery opportunities in a policy
comparison.

### What the previous results tell us

The [v7 result](stage-results/controller-x5-v7-result-2026-09-29.md) records
4/4 suitable tasks passing protected functionality in each of B, S and A.
A cost 2.67 times S and took 1.84 times its mean elapsed time, with zero measured
acceptance or quality gain. The 12 v7 episodes settled USD 3.020660704; the
combined v6/v7 spend was USD 7.15007251. The first six episodes were regraded
post hoc for diagnosis, so the combined set is hybrid development evidence.
It is neither independent replication nor evidence that Controller can never
help. The baseline reached the maximum score on the measured suitable cases,
leaving no measured improvement available.

The [candidate closure](stage-results/controller-x5-candidate-closure-2026-09-29.md)
therefore correctly stopped that candidate before X6. Exercising automatic
routing, a frontier role or a complete Controller-to-worker path demonstrated
execution, not benefit.

The later [H02 pair](stage-results/controller-x5-h02-sa-result-2026-09-30.md)
scored 30/100 in both S and A. A cost USD 0.6434197 more, and its handoff failed
the actionable-repair condition. Controller had expanded frozen acceptance
criteria and stopped before a complete investigation. Production checks at all
three Framer entry paths were subsequently repaired and qualified offline.
The paid outcome remains unchanged; it did not test a fully successful
investigation under the repaired mechanism.

The [H03b result](stage-results/controller-x5-h03b-result-2026-10-01.md)
records one producer at USD 0.184233601, public failure, zero S/A calls, and a
private grader exception. Its patch committed an altered acceptance criterion
before correction. That public violation is observed; the private score is
unavailable. The failed patch belongs to an isolated authored case. It is not
evidence that the repaired installed Controller currently has that same defect.

The [earlier real-world programme](REAL-WORLD-EVALUATION-PLAN.md) also reached a
decision. In its reserved comparison B0 accepted 12/24 episodes and B1 10/24,
with two paired wins for B0, none for B1, and 22 ties. B1 failed the fixed
promotion gates. Those counts describe that fixture set and historical runtime;
they are not production acceptance rates or proof of current-model performance.
Its already observed reserved cases cannot become an unseen holdout again.

All monetary figures above are historical reported API-equivalent observations
from the linked records, not new estimates or invoice claims.

## 3. The outstanding engineering work before another experiment

### A. Repair measurement and admission in a new research revision

The next evaluator must return bounded, interpretable outcomes for correct,
incorrect, partial, malformed, exceptional and timed-out candidates. Distinguish
a candidate failing a specified behavioural scenario from evaluator or host
infrastructure breaking before it can score. A candidate runtime error can be
a functional failure under a predeclared rubric. An evaluator failure leaves
the relevant score unavailable and stays visible in operational failure and
cost totals.

Calibrate against the original defect, materially different correct repairs,
plausible partial repairs, criterion-changing repairs and the stopped H03b
patch as a labelled development negative control. An updated grader can help
future cases; it must not replace H03b's historical score. Oracle isolation and
resistance to actor introspection also need qualification for the next threat
model. Running untrusted actor code after its writer stops does not, by itself,
protect a grader from introspection.

The current research function `accepted_producer` in
[the H03 pilot runner](../tools/controller_x5_h03_pilot.py) still compares raw
receipt cost with rounded ledger spend using exact float equality. The recorded
counterfactual reproduced a false rejection at the rounding boundary. The next
runner should use the ledger's existing canonical monetary representation and
retain terminal-writer, identity, one-attempt, unresolved-charge and budget
checks. A broad epsilon that hides genuine disagreements would weaken the gate.
The [RC review](RELEASE-CANDIDATE-2026-10-01.md) found a different comparison in
the production handoff; this research defect does not justify an untested
production accounting rewrite.

Preserve historical manifests, oracles and receipts. Make a new version of the
research runner and acceptance schema; do not turn the closed H03b entry point
into an apparent resumable pilot. Exit evidence is an offline matrix in which
both eligible branches, ineligible outcomes, exceptions, cancellations, restarts
and rounded costs have the intended result and cannot cause duplicate dispatch.

### B. Give both arms complete, realistic public feedback

Predeclare two entry branches before the next producer runs:

| Entry branch | Public admission evidence | Shared S/A continuation goal |
| :--- | :--- | :--- |
| Public failure | Settled producer, frozen public verification failure and its relevant output | Repair the original task under the unchanged acceptance contract. |
| Public success with residual risk | Public pass plus a predeclared source- or behaviour-based risk signal about an original requirement | Investigate and resolve that specific remaining risk, preserving the accepted behaviour. |

A protected grader failure must never choose a branch or supply the worker's
diagnosis. A source-based concern is a reason to investigate, not an assertion
that a defect exists. A justified no-change outcome may be correct. If the
public follow-up already closes the risk, the case ends without S/A spending.
An ordinary public pass with no qualifying residual risk also ends there.

The Q4U worker surface used in H03b had retrieval and editing tools but no
execution tool. Both arms should receive the same complete host-verifier
feedback, and their briefs should explain which verification is host-provided.
Do not expect a worker to produce execution evidence it cannot obtain. Giving
ordinary repair a proper feedback loop may remove the apparent need for
Controller; that is a useful result.

Adding shell access would be a separate tool and isolation change requiring
its own tests. The first mechanism study can use the existing host verifier.
A later consumer policy study must match the intended consumer tool surface,
so an artificial lack of test access is not mistaken for a general Controller
advantage.

### C. Bind identity evidence to the actual campaign host

The [dated account observations](../test/results/2026-10-02-current-account-model-identity.json)
verify two exact served identities in their recorded environment. They do not
turn every installation into an account-verified installation. The shared
[model registry](../src/model_registry.json) remains the authority for current
model-class mappings; current IDs should not be duplicated in experimental
scripts or this roadmap.

There is a specific integration issue to resolve before using the old policy
launcher for a new campaign: [the evaluation freeze](../tools/evaluation_freeze.py)
currently reads account verification from the portable registry's
`account_identity.status`, and [the pilot launcher](../tools/evaluation_pilot.py)
refuses remaining candidate blockers. The dated local proof is not automatically
consumed by that path. Consequently RC identity verification and policy-pilot
admission are separate facts.

A clean RC stamp also does not satisfy the launcher's whole-tree cleanliness
check. Prepare a clean checkout of the intended experiment source and bind its
actual runtime dependencies. Keep campaign outputs in the permitted ignored
location. Generated release files and later research records must not be
mistaken for an already sealed paid candidate, and an old freeze must not be
relabelled to make a new launch pass.

The proposed solution is a campaign-local identity evidence input, bound to
the account scope, host, CLI/adapter version, date and registry snapshot, with
freshness and exact served-ID checks. Keep portable vendor mapping and local
account qualification separate. Reuse matching evidence; perform a new canary
only for a stale, missing or different transport/cell. A Windows CLI observation
must not silently qualify a distinct WSL execution boundary. Missing served
effort telemetry stays unknown. Requested effort and command construction can
be checked without claiming the provider exposed its internal effort setting.

Freeze the resolved mapping for each experiment. If the registry moves to a
new model during a comparison, stop and decide whether to close it or create a
new cohort. Mixing model generations would confound the policy effect. Historical
provider IDs remain in immutable receipts, with class normalisation used only
for labelled comparisons.

### D. Preserve the safe runtime and research boundaries

Recheck actor/evaluator separation, credential handling, Graft retrieval scope,
source sealing, immutable acceptance and complete attempt accounting on the
intended host. Reuse already qualified production mechanisms instead of building
a parallel executor. Test the next campaign's actual path through those
mechanisms, including partial handoffs and interruption.

The H02/H03 production acceptance repairs are completed prerequisites to
regress, not newly discovered missing features. Broader filesystem confinement,
descendant termination and live managed children remain distinct qualification
items. They become mandatory before a study or product promise relies on them.
A Controller effectiveness experiment need not enable managed children or
unrestricted execution to make progress.

## 4. Sequence of work and what each stage establishes

The identifiers below organise this proposed programme. They are not new
completion claims or an attempt to rename historical X5-X8 results.

| Stage | Action and deliverable | Exit decision |
| :--- | :--- | :--- |
| Q0: define the target | Freeze intended task families, consumer environment, primary outcome, acceptable cost/latency tradeoff and the unchanged B0 baseline. Audit historical exposure and identify fresh development and reserve pools. | A written hypothesis and claim boundary. No paid run justified merely by an available fixture. |
| Q1: qualify measurement | Complete the evaluator, canonical-cost gate, two public entry branches, shared feedback and campaign-local identity binding described above. Produce offline reproductions and results. | Every planned branch is interpretable, charges reconcile and invalid states stop before dispatch. |
| Q2: establish live feasibility | On a small, separate calibration slice, check the intended host path and whether ordinary repair leaves any publicly identifiable unmet work. | Either a feasible matched comparison or an explicit stop. No general uplift claim. |
| Q3: test the mechanism | Freeze new paired S/A development cases and run the same worker continuation with and without Controller. Include controls and a useful-handoff analysis. | Measured benefit or a closed negative/inconclusive candidate. Positive dispatch counts alone do not pass. |
| Q4: challenge the value | Compare any promising intervention with a simpler use of the extra budget, then design an adequately justified independent confirmation. | A narrow claim supported by task-level evidence, or continued experimental status. |
| Q5: evaluate the complete policy | Run the separate policy pilot under B0 and one frozen candidate using the intended installed path and representative intake; follow with a separately frozen policy confirmation if justified. | Estimate overall value, admission frequency, failures, total cost and operator burden. The pilot alone cannot authorise promotion. |
| Q6: independent decision and release | Review the qualifying evidence, close findings, and package only the approved policy/profile/host scope with rollback. | Explicit retain, reject, inconclusive or limited promotion decision. |

Representative-task intake and a B0-only current-model characterisation can be
prepared alongside Q1-Q3. A Controller-enabled policy candidate depends on a
credible mechanism signal. A separate worker-only policy can be evaluated
without waiting for Controller to succeed. Preserve distinct campaign identities
and budgets in either case.

### Q2: bound feasibility so screening does not become the project

Offline reference and wrong-repair tests show that a benchmark can distinguish
solutions. They do not show that a live baseline will fail, or that Controller
will help. The previous studies repeatedly encountered either a baseline that
already solved the problem or an entry/measurement failure.

As a proposed initial bound, allow at most four fresh calibration producers
under a frozen admission rule. Stop and review the premise if none yields a
valid public entry condition. Do not continue buying similar screens until a
desired failure appears. This count is an engineering spending checkpoint,
not a statistically sufficient sample or an approved allowance.

Use a different task slice for Q3, applying the frozen eligibility rule before
seeing A outcomes. Record every screened task and rejection. Authored partial
patches can test a mechanism cheaply, but must be labelled injected development
states, not naturally observed baseline failures. The operator's existing
direction to use authored cases permits this development route; a future
natural-task claim still needs natural-task evidence.

### Q3: make the matched comparison explain something

Freeze the producer's source, acceptance contract and public observations.
Create independent S/A copies with identical worker cell, tools, edit boundary,
worker attempt limit and verification access. S receives an ordinary repair or
review continuation. A receives Controller investigation followed by that same
worker opportunity. Controller contributes an evidence packet, never revised
requirements or hidden test information.

A useful packet should state the observed facts, competing explanations, the
next executable edit or check, unresolved uncertainty and preserved constraints.
A truthful but generic gap does not earn actionable-repair credit automatically.
Failure to generate a useful packet remains an A outcome with its cost. Do not
drop it from the comparison after observing the treatment result. Any fallback
after a failed Controller invocation must be declared beforehand.

A possible first development block is six task cases: two public-failure cases,
two public-success/residual-risk cases, one ordinary control and one missing-
decision control. That is at most twelve scheduled arm episodes and up to six
shared producer attempts, not eighteen provider calls: each Controller episode
may contain multiple role calls, while clarification may contain no worker call.
Admission failures remain reported outcomes; new cases do not silently replace
them. These are proposed engineering counts, not power-qualified release gates.

Record actual shared-producer spend once. For deployment-cost comparisons,
show the same producer cost on each hypothetical complete S or A path, clearly
labelled, while reconciling the actual total without double counting it. Keep
assessment, Controller roles, helpers, worker calls, failed attempts, verification,
indexing and unresolved reservations visible.

This design measures the effect of adding Controller with a fixed worker
opportunity. It does not isolate Controller's structure from spending extra
compute. If it produces a promising signal, Q4 must test a simpler alternative,
such as another bounded worker continuation or a stronger direct worker under
a comparable maximum budget. This prevents us attributing all gains from extra
resources to the Controller design.

### Q4: distinguish a promising case from a qualified claim

The development gate should require a practical improvement on the predeclared
eligible group, no unacceptable contract failures, honest completion reporting,
and an acceptable cost/latency tradeoff. Fix the primary outcome and margin
before the comparison. Secondary partial-progress scores can explain results
but cannot replace a failed primary outcome retrospectively.

The original X6 design was 24 new tasks, two repetitions per arm, or 96
episodes. [X0's contract](CONTROLLER-REMEDIATION-CONTRACT-X0.md) explicitly
classified that design as exploratory with no automatic-promotion authority.
The older +5/100 quality, -5 percentage-point acceptance, 1.5-times-cost and
2-times-tail-latency figures are historical diagnostic proposals, not newly
approved release margins or a guarantee that 96 episodes suffice.

Choose a confirmation sample from the effect size worth deploying, uncertainty
observed only in development, task-family correlation and acceptable error risk.
Analyse matched task differences and cluster uncertainty by independent task
or family as appropriate. Repetitions on the same task are not additional
independent task families. Report paired wins, losses, ties and incomplete
observations, including sensitivity to exclusions and infrastructure failures.
Sparse tail-latency observations and zero observed harms need explicit limits.

Keep development selection separate from confirmation. Verify reserve access
history without reading its solutions; use a new reserve if independence cannot
be supported. Do not relabel the old W programme's opened H tasks as unseen.
An independent review should challenge evidence and exposure, not merely run
the same rubric under a different model name. A model switch alone does not
establish independent task authoring or blindness.

If the evidence is negative, close the candidate. If it is inconclusive, retain
the current policy and price a separately frozen extension only if its expected
information is worth the cost. Finishing a fixed number of episodes is not a
reason to promote.

### Q5: what the separate real-world policy pilot must establish

This is a new end-to-end study after the earlier W programme's closure. Its
question is whether the complete routing and recovery policy improves user
outcomes on the intended work mix under the current registered models.

Use a prospective intake rule, a fixed selection window or a documented task
sample. Prefer authorised unresolved work or historical tasks reconstructed
from an original symptom and pre-fix snapshot. Record exclusions and exposure
to public fixes. Authored tasks remain useful for development and regression;
they do not become representative natural work because their code is realistic.
If no representative task supply is available, report an authored policy pilot
and keep the external-validity limitation open.

Start with B0 and one candidate. Reusing three historical arm names would not
justify reviving the rejected B1 unchanged. A proposed reconnaissance scope is
8-12 independent tasks, two policies, and one or two fixed repetitions, giving
16-48 complete episodes. Its purpose is to validate the workflow, estimate the
task distribution and price a later study. It is not a promotion-sized sample.
Task count, repetitions and spending remain to be frozen from Q0-Q4 evidence.

Use the same outer orchestrator model, input snapshot, permissions, tool access,
verification facilities, outcome-ledger initialisation and common budget rules.
Use fresh consumer ledgers for the primary cold-start comparison. Counterbalance
arm order, prevent cross-arm state leakage and distinguish cache warmth from
learned outcome history. Audit that the evaluation adapter follows the installed
RC's real dispatch and recovery path; the existence of a live research runner
does not prove consumer equivalence. Run a bounded installed-path smoke before
calling that an end-to-end consumer test.

Count the whole task, including deciding whether to invoke Controller. A matched
study on eligible failures estimates conditional benefit. It says little about
how frequent those failures are or how much screening costs on ordinary tasks.
A policy can improve rare hard cases yet worsen average cost and latency if it
invokes Controller too often. Both false admissions and missed useful admissions
therefore belong in this pilot.

Keep these outcomes separate:

| Outcome | Why it matters |
| :--- | :--- |
| Independently accepted task completion | Measures the user's required result. |
| Partial verified progress | Can be useful without being completion. |
| Correct clarification, blocked state or recovery protocol | Measures safe handling of a task that cannot yet be completed. |
| False success and critical contract violation | Prevents plausible reports or low cost from concealing harmful outcomes. |
| Total spend and cost per accepted task | Includes all failed attempts, screening and overhead; undefined if no tasks are accepted. |
| End-to-end latency and human burden | Includes verification, questions, intervention and measured review effort. |

Do not allow a composite score to compensate for a critical contract violation
with token savings. A worker-only candidate can qualify even if Controller
remains experimental. A Controller candidate should be limited to the task
classes and host conditions its evidence supports.

If the pilot supports a candidate, freeze its final policy and analyse it on
a separate, untouched representative confirmation sample sized for the intended
claim. Any pilot-driven trigger change must be included in that freeze. Q4's
conditional Controller confirmation does not automatically qualify this broader
policy claim. If suitable independent confirmation is unaffordable or unavailable,
keep the candidate experimental. Q6 cannot turn a small reconnaissance pilot
into general promotion authority.

### Q6: turn evidence into a controlled product decision

Independent adjudication follows a frozen result, and separates mechanical
safety, exploratory promise and confirmed policy value. The original X7 role
is still useful here, but its historical model/effort recommendation is not a
claim about this session's active settings or an instruction to launch agents.
Use the repository's checked handoff contract when an authorised review requires
a new session, model change or delegation.

Promote only after the agreed evidence gates and an explicit product decision.
Update consumer instructions and policy in `src/`, generate workers where
required, run the existing offline harness and checked builder, and test the
new exact bundle through install, upgrade, rollback and intended live controls.
Preserve B0 as the documented fallback. A revised Controller policy is a later
release candidate, not a silent replacement of the frozen current RC.

For that expanded scope, use a fresh installed consumer to exercise cold-start
`auto/on/off` precedence, natural-language requests reaching the validated
control command, unavailable profiles, cancellation and linked continuation.
Check that restart or session compaction preserves task ownership, budgets and
stored intent. Existing fake-workflow coverage is a prerequisite; live command
behaviour on the intended host needs its own bounded evidence. Live managed
children remain outside the claim unless separately qualified.

## 5. Cost, scheduling and stopping discipline

The dependency sequence is Q0, Q1, Q2, Q3, Q4, Q5 and Q6 for a Controller-enabled
policy. Representative intake can proceed earlier; a worker-only policy study
can proceed on its own evidence. The next implementation deliverable should be
Q1's offline qualification package, rather than another paid producer.

No credible combined price or completion date follows from the existing small
studies. The confirmation size and task supply are unresolved, and repeated
negative development results may end the candidate before later stages.
Historical small costs are not current quotes. The dated account probe record
also shows that a small planning estimate was exceeded by large CLI cache
creation, so a short user prompt is not a reliable proxy for billable context.

Before each paid block, state its payload, destination, model classes, role and
attempt limits, expected token/cache shape, dated pricing basis, experiment
ceiling and stop rules. Separate provider experiment spend, development-session
usage, local computation and unknown invoice amounts. Admission reservations
limit local launch decisions; an in-flight provider request may exceed a local
estimate, and subscription telemetry is not proof of an enforced USD billing cap.

Check existing operator authorisation against the actual proposed scope. Follow
the applicable project and manifest gates; do not ask again solely because a
hash changed within already authorised work, and do not stretch past RC-only
approval or reuse a retired campaign's allowance. The present analysis does not
rescind the operator's deferral of these experiments.

Stop on missing identity evidence, source or oracle drift, incomplete accounting,
an unsettled prior invocation, loss of isolation, or an uninterpretable grader
result. Preserve actual charges and failure records. Development effectiveness
stops should also be predeclared: no eligible cases within the calibration bound,
no practical benefit, or cost/latency outside the accepted tradeoff. A new
hypothesis is needed before another materially similar screen.

## 6. Risks of not doing the work

| Work left undone | Consequence | What we can still responsibly do |
| :--- | :--- | :--- |
| Measurement and admission repairs | Future experiments can reject valid settled attempts, lose scores to evaluator exceptions, or compare unequal feedback. More spend can produce no interpretable answer. | Continue operating the RC within its already qualified scope; keep affected research campaigns closed. |
| Controller mechanism and value studies | We do not know whether extra investigation beats ordinary repair or a simpler use of the same budget. Some difficult task opportunities may be missed. | Retain B0 and explicitly experimental/manual Controller use with the documented limitations. |
| Representative policy pilot | Conditional successes may be rare, misrouted, or outweighed by overhead on ordinary tasks. Overall cost, latency and operator burden stay unmeasured for the new policy. | Make narrow development claims and avoid claiming improved general routing. |
| Independent confirmation and review | Authored-case bias, selection effects, shared context or grader weaknesses may make a favourable development result look stronger than it is. | Treat results as exploratory and defer automatic promotion. |
| Host qualification when capabilities expand | Cancellation may leave descendants, broader execution may exceed the tested confinement, or a different transport may serve an unqualified model. | Keep unsupported capabilities disabled or explicitly limited to the recorded host contract. |
| Version and evidence discipline | Results from old model generations or local account checks may be presented as current universal guarantees; old stopped pilots may accidentally be resumed. | Keep registry snapshots, dated receipts, claim boundaries and campaign identities explicit. |
| Final publication action | The prepared RC remains local and unavailable through the intended release channel. | Review/use the frozen local artefact; this is independent of demonstrating uplift. |

The main risk of permanent deferral is foregone improvement and a narrower
evidence base. It does not, by itself, establish that the present RC is unsafe
or unusable. Risk rises when product claims or automatic behaviour expand while
the qualification remains unfinished. The historical results already justify
restraint: Controller sometimes added cost without benefit, and the earlier
adaptive policy did not beat the simpler default on its reserved comparison.

There are also risks in continuing badly. Endless authored screening can turn
the programme into an expensive search for a favourable example. More complex
roles can increase latency and introduce acceptance drift. Repeatedly inspecting
reserved outcomes destroys their value as confirmation. Measuring a highly
restricted worker can confuse tool deprivation with reasoning difficulty.
The bounded stages, meaningful baseline, independent acceptance and explicit
negative exit decisions are intended to prevent those failures.

## 7. Decisions and exact next deliverable

On 2026-10-02 the operator accepted the offline qualification recommendation.
The [staged implementation plan](OFFLINE-QUALIFICATION-IMPLEMENTATION-PLAN-2026-10-02.md)
now defines O0-O6, manual model/effort handovers and qualification gates. Its
initial handoff is ready; implementation and new paid experiments have not
started. The broader Q2-Q6 programme in this analysis remains conditional.

Engineering can proceed on the design defaults above once execution of the
deferred work is directed. The eventual product choices are the intended task
population, the practical quality gain worth paying for, tolerable extra delay,
the campaign spending envelope, and whether a limited experimental result merits
a narrower release claim. Those choices cannot be inferred from passing tests.
Until fixed, the conservative disposition is to retain B0.

The next concrete deliverable is a newly versioned offline qualification
contract and implementation for the evaluator, two public continuation branches,
canonical cost admission and scoped account evidence. It should include an
executable acceptance matrix, shared-feedback fixtures, exposure ledger,
source/dependency seal, proposed development schedule and priced launch notice.
Only after that package passes should a fresh bounded live feasibility block
be considered. H03b, v7 and the old W programme stay closed.

Completion of the overall programme means a defensible disposition with
traceable evidence: a narrowly qualified improvement, an inconclusive result
with a justified next study, or a rejected candidate with B0 retained. A positive
Controller claim is an empirical possibility, not an administrative milestone.

## 8. Evidence and verification of this analysis

This analysis uses repository records and current source inspection. It makes
no provider experiment call or current price claim. The 83-check PASS cited above is
the saved RC result, not a full harness run performed while writing this file.
Documentation verification uses the existing harness's prose check, local-link
validation and a scoped diff check. Runtime source and `dist/` are unchanged by
this task.

Graft MCP was available; its initial freshness check reported a stale committed
index. Retrieved locations were checked against the named current files. This
indexing limitation does not change the historical result records. A semantic
refresh is a separate maintenance task and is not a substitute for qualification.

Primary records:

- [RC scope and shipping review](RELEASE-CANDIDATE-2026-10-01.md),
  [account identity supplement](stage-results/release-candidate-model-identity-2026-10-02.md),
  [recorded current harness](../test/results/2026-10-02-harness-status.json), and
  [exact archive verification](../test/results/2026-10-01-rc/verification.json).
- [Controller action plan](CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md),
  [X0 contract and statistical limits](CONTROLLER-REMEDIATION-CONTRACT-X0.md),
  [v7 result](stage-results/controller-x5-v7-result-2026-09-29.md), and
  [candidate closure](stage-results/controller-x5-candidate-closure-2026-09-29.md).
- [H02 matched result and production repair](stage-results/controller-x5-h02-sa-result-2026-09-30.md),
  [H03 authored calibration](stage-results/controller-x5-h03-authored-design-2026-09-30.md),
  [H03b preflight and threat-model limit](stage-results/controller-x5-h03b-pilot-preflight-2026-10-01.md),
  and [H03b result and next requirements](stage-results/controller-x5-h03b-result-2026-10-01.md).
- [Earlier real-world plan and W09 closure](REAL-WORLD-EVALUATION-PLAN.md),
  [historical development result](../test/results/2026-09-18-realworld-development.json),
  and [historical reserved result](../test/results/2026-09-18-realworld-reserved.json).
- [Research admission implementation](../tools/controller_x5_h03_pilot.py),
  [policy candidate freeze](../tools/evaluation_freeze.py),
  [policy launcher](../tools/evaluation_pilot.py),
  [model registry](../src/model_registry.json), and
  [execution and spending protocol](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
