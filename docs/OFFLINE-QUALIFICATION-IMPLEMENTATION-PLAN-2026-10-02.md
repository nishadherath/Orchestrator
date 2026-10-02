# Offline qualification package: staged implementation plan

Date: 2026-10-02, Australia/Sydney. Status: planned; implementation has not
started. The operator accepted the next offline qualification deliverable and
requested this plan with manual model/effort handovers. This document schedules
that bounded work. It does not start a paid campaign or authorise agent launches.

## 1. Goal and scope

Produce a newly versioned research package that can interpret evaluator results,
admit eligible continuations from public evidence, give both arms the same
feedback, and consume appropriately scoped account identity evidence. Its
acceptance suite must prove that invalid states stop before provider dispatch.
This implements Q1 and the necessary engineering portion of Q0 in the
[post-RC analysis](POST-RC-QUALIFICATION-ANALYSIS-2026-10-02.md).

The package succeeds when a fresh campaign can be prepared, replayed with fake
providers, interrupted, resumed and audited without ambiguous scoring, hidden
feedback leakage, duplicate dispatch or unreconciled accounting. It qualifies
the measurement mechanism. Controller uplift remains an unfinished empirical
goal. B0 remains default; Controller remains experimental.

Preserve the frozen RC and all historical manifests, receipts, grades and closed
roots. V7 is complete, H03b is closed with its private score unavailable, and the
older W programme ended without promoting B1. None is a resumable new experiment.
Do not add shell access, enable live managed children, redesign production
accounting, refresh provider mappings or claim broader host confinement as a
side effect of this work.

The simplest implementation is a small successor research package using existing
execution, ledger and registry mechanisms. A second general executor or a new
policy framework is outside scope. If the existing mechanisms cannot enforce a
required boundary, record the exact gap and resolve that design issue before
continuing dependent implementation.

## 2. Priority and stage sequence

P0 means a prerequisite for interpreting results or preventing invalid dispatch.
P1 means integration and qualification required before any new paid producer.
Every stage below is an operator handover checkpoint, including adjacent stages
with the same setting. In the manual route, finish the stage, save and validate
the next handoff, report its target and estimates, then wait for the operator's
continuation. A stage boundary does not inherently require a fresh chat, but
the operator can select one using its handoff.

Model and effort assignments are owned only by
[development model calibration](DEVELOPMENT-MODEL-CALIBRATION.md), currently
revision DMC-1. Read its stage row before each handover. This plan owns scope,
sequence and acceptance; it does not maintain another model-selection table.

| Stage | Priority and dependency | Deliverable | Calibration row | Planning elapsed time |
| :--- | :--- | :--- | :--- | :--- |
| O0 | P0; first | Frozen contracts, threat boundary, acceptance matrix and ownership | O0 | 45-90 minutes |
| O1 | P0; O0 passes | Bounded evaluator and negative-control qualification | O1 | 2-4 hours |
| O2 | P0; O0 passes | Canonical admission and identical public feedback | O2 | 1.5-3 hours |
| O3 | P0; O0 passes | Campaign-local identity evidence and preflight | O3 | 1.5-3 hours |
| O4 | P1; O1-O3 pass | Integrated fake campaign, seals and offline regression | O4 | 1.5-3 hours |
| O5 | P1; O4 passes | Independent adversarial review and finding closure | O5 | 1-2 hours |
| O6 | P1; O5 passes | Assemble reviewed dossier and readiness disposition | O6 | 30-60 minutes |

The calibration records the accepted Luna-first and Sol-first decisions,
Astra escalation triggers, evidence limits and update procedure. The
[dated allocation review](MODEL-ALLOCATION-REVIEW-2026-10-02.md) is supporting
rationale. No comparative model run or launch has been performed. All stage
acceptance gates below remain mandatory regardless of the assigned model.

Manual order: O0, O1, O2, O3, O4, O5, O6. Optional authorised parallel order:
O0, then O1/O2/O3 together, then O4, O5, O6. Detailed controls are in
[development session capabilities](DEVELOPMENT-SESSION-CONTROLS-2026-10-02.md).

## 3. O0: freeze the engineering contract

Start with the validated [O0 handoff](../handoffs/2026-10-02-offline-qualification-o0.md).
Check Graft freshness and read the current root instructions. Establish the
branch, source revision and pre-existing changes before edits. The known
release source is `f9f141c` on `v1.0-rc2`; subsequent documentation and generated
artefacts are present. Verify the current state rather than assuming a clean
tree. Permission-limited listings are not evidence that campaign files were
deleted.

Use Graft call graphs before changing shared symbols. Inspect these starting
points and their actual dependencies:

- `tools/controller_x5_h03_pilot.py`: historical admission and paired runner.
- `tools/controller_x5_h03_risk.py`, `tools/controller_x5_h03_fixture.py` and
  `tools/controller_x5_h03_freeze.py`: public branch, evaluator inputs and seal.
- `tools/evaluation_freeze.py` and `tools/evaluation_pilot.py`: candidate
  blockers, account evidence and clean-source launch boundary.
- `tools/task_executor.py`, `tools/controller_dispatch.py` and their ledger
  dependencies: reuse established execution/accounting contracts.
- `src/model_registry.json` and `tools/model_registry.py`: current model-class
  resolution. Recorded historical identities remain evidence.
- `test/harness/check.py` and relevant existing campaign/isolation suites:
  integrate new tests into the existing offline gate.

Write the qualification contract and machine-readable acceptance matrix. Assign
stable requirement IDs from section 10, exact input/output shapes, error codes,
ownership, permitted paths, evidence retention and falsification tests. Define
schema versioning before modules diverge. Proposed new files live under a common
`tools/controller_qualification_` prefix with matching harness tests; O0 chooses
the exact minimal files after inspecting reuse opportunities. These are proposed
names, not claims that modules already exist.

Specify evaluator outcomes separately from public verification and admission:
valid scored result, specified actor functional failure, evaluator error,
infrastructure error, timeout and cancellation. Decide which deadlines belong
to the actor scenario versus the evaluator host. Score availability must be
explicit; missing is never silently zero or pass. Freeze how partial criteria
aggregate, including critical violations, before observing new model outcomes.

Make O2/O3 briefs executable by their calibrated implementation model: name the canonical money helper, complete
decision tables, exact schemas, allowed shared APIs and independent expected
outcomes. An unfinished design contract does not pass O0 merely because the
next implementation model could try to infer it.

Freeze two public branches and their shared feedback schema. Define S as an
ordinary continuation and A as Controller followed by the same worker
opportunity. Pin original acceptance, tool access, worker attempt allowance,
public verification and failed-handoff disposition. Hidden evaluation cannot
select a branch, choose a case or supply the repair diagnosis.

Define the identity evidence issuer and trust boundary. A hash proves content
consistency, not that an arbitrary operator-authored JSON document came from a
provider. Require traceable raw receipts produced by the trusted host path,
validate their interpretation, and state which local actors are trusted.
Choose explicit evidence freshness/revocation rules and an offline clock input
for testing. Do not invent a universal validity period from one successful probe.

**Exit:** all required states have predetermined outcomes and tests; no unresolved
P0 interface decision; file owners and dependencies are frozen; original records
are identified for preservation. Save `docs/OFFLINE-QUALIFICATION-CONTRACT.md`,
a requirements matrix under `test/fixtures/`, and a stage-result record. The
contract is reviewed against the failures in the prior analysis. Downstream
stages receive only the contract version that passed this gate.

## 4. O1: evaluator and isolation

Implement the successor evaluator without altering a closed oracle or its
historical reported score. Use bounded subprocess execution and explicit result
parsing where untrusted actor code is evaluated. Keep protected oracle logic
outside the actor's interpreter and readable scope. Separate processes alone
are insufficient if the actor can inspect evaluator files or processes.

Exercise the original defect, at least two materially different correct repairs,
plausible partial repairs, changed-acceptance repairs, malformed outputs,
exceptions, hangs, excessive output and the stopped H03b patch as a labelled
development negative control. Reuse or reference immutable bytes with hashes;
new diagnostic scores belong only to the new evaluator's development report.

Test actor attempts to introspect protected inputs, modify oracle artefacts,
write forged results and leave child processes or files that influence a later
case. Qualification must match the actual intended host boundary. If a required
isolation property is unavailable, the package remains blocked for that host;
an in-process fake does not substitute for an OS boundary test.

Calibrate timeout and resource limits against reference controls. Test evaluator
exceptions independently from actor exceptions. Preserve exit code, bounded
diagnostics, score availability, rule version and evidence hashes. Invalid
scoring stays visible in operational outcomes and cost totals.

**Exit:** expected outcomes for every control, independently checked correct
solutions, demonstrated rejection of criterion changes and forgery, bounded
termination, protected evidence inaccessible on the declared host, and no
historical mutation. Report Windows and WSL results separately when both are
claimed. Deliver evaluator module/tests plus requirement-linked evidence.

## 5. O2: canonical admission and shared public feedback

Reproduce the recorded receipt-versus-rounded-ledger false rejection in a new
regression. Trace and reuse the ledger's actual canonical monetary conversion;
do not assume a precision or add a permissive epsilon. Reject non-finite,
negative, malformed, missing and genuinely inconsistent costs. Preserve
terminal-writer evidence, one-attempt policy, exact identity binding, budget
capacity and unresolved-charge checks.

Implement these decisions as explicit, inspectable results:

| Public state | Admission outcome |
| :--- | :--- |
| Settled producer with valid public verification failure | Eligible public-failure continuation |
| Public pass with predeclared still-open public risk concerning an original requirement | Eligible residual-risk investigation |
| Public pass and follow-up closes the risk | Complete without S/A calls |
| Public pass with no eligible risk | Complete without S/A calls |
| Missing decision that requires the user | Clarification outcome; no invented acceptance or forced worker |
| Invalid receipt, identity, source, writer, budget or verifier evidence | Blocked; no provider intent or call |
| Protected failure without a public trigger | Ineligible; protected result is not actor feedback |

A source concern invites investigation; it does not assert a defect. A justified
no-change result can succeed. The shared packet includes original requirements,
producer snapshot, public check identity and relevant complete output, public
risk evidence, available tools and host-verification instructions. Both arms
receive identical public content and digests. Private scores, hidden paths,
repair hints and evaluator exception internals cannot enter the packet.

If logs exceed a declared packet limit, retain the full public artefact and a
common documented access path. Never silently remove the failing assertion or
give one arm more feedback. Tests must compare evidence bytes, not merely keys.
Controller output is an additional A artefact; it cannot rewrite the shared
acceptance contract. A failed or unhelpful handoff remains an A outcome.

**Exit:** both branches and all rejection paths pass; true monetary disagreement
is still rejected; packet parity and hidden-data exclusion pass; invalid input
cannot reserve or dispatch; repeated admission cannot create another attempt.
Deliver pure admission/packet components and focused tests. O4 owns final runner
wiring so O2 does not concurrently rewrite shared launch code.

## 6. O3: campaign-local identity and source preflight

Implement an explicit evidence input to the new campaign path. Bind account
scope without credentials, host/environment, transport, CLI and adapter revision,
observation time, expiry policy, registry snapshot, requested class/effort,
observed provider identity, raw receipt digest and evidence schema version.

Separate three claims: registry mapping is known, account served the observed
identity in this environment, and the command requested the selected effort.
Served effort stays unknown unless supplied by trustworthy telemetry. Missing
telemetry is not a fabricated verification or necessarily a failure of a scope
that only requires requested effort; the contract must say which is required.

Current provider IDs resolve exclusively from the registry into a frozen
campaign snapshot. Match observed receipts against that snapshot. Do not copy
current IDs into scripts or replace the registry's portable account status with
a machine-specific claim. Reuse existing evidence only when every required
binding and freshness rule matches. The existing Windows observation must not
silently qualify WSL. Drift requires a new cohort or explicit closure, not
mid-comparison substitution.

Test missing, stale, future-dated, revoked, tampered and wrong-account evidence;
different host/transport/cell/effort/adapter/registry; forged provenance; and
valid exact reuse. Test against a fixture registry with deliberately different
IDs so hard-coded current IDs cannot accidentally pass. Keep frozen historical
receipts intact.

**Exit:** local evidence clears only its scoped blocker; all other launch
conditions remain enforced; portable installations remain unverified without
their own evidence; the new preflight reports why it blocks and what evidence
would resolve it. Use fake or archived inputs only. A live freshness canary is
a later paid prerequisite, never hidden inside this offline stage.

## 7. O4: integrated campaign and recovery

Connect O1-O3 through a new versioned runner or narrowly versioned integration
path. Reuse the established executor rather than invoking providers directly
from a new helper. Keep historical launch entry points closed. The offline
mode must have an explicit fake transport and a guard that prevents accidental
network/provider fallback.

Freeze the source and transitive runtime dependencies, public/protected inputs,
registry snapshot, identity evidence and configuration. Qualify both omitted
dependencies and changed bytes as invalid. Put mutable outputs in the launcher's
permitted ignored location, outside sealed inputs. Show that the clean-source
requirement checks the campaign's real checkout, not merely the release stamp.

Run end-to-end fake cases for both entry branches, ordinary completion,
clarification, no-change success, unhelpful Controller output, failed worker,
grader failure, identity mismatch and insufficient budget. Check the complete
life cycle: producer, settlement, public decision, twins, S/A continuation,
protected scoring and aggregate report. Actual shared-producer spend is counted
once; hypothetical per-arm full-path costs are labelled separately.

Inject interruption before intent, after intent, after call start, after receipt
and before settlement/reporting. Repeat resume and settlement. Assert no second
dispatch where the first call's outcome is uncertain; retain unresolved holds
until writer and charge evidence justify reconciliation. Late receipts and
partially written records must not create false completion. Cancellation tests
may claim only the process/host scope they exercise.

Register the qualification suites in `test/harness/check.py`. Run focused suites
during development, then the full offline harness on the integrated revision.
Where shared consumer runtime or bundled tools change, run the checked
`tools/build_dist.py` path and relevant installed regressions. Never hand-edit
`dist/`. Research-only additions must still preserve the existing build gate;
the archived RC remains identified by its original hash.

**Exit:** all mandatory requirements are represented in executable tests; full
offline gate and applicable checked build pass; zero experimental provider
calls; reports identify exact source and fixture hashes. Keep command, exit code,
counts and skipped scope. A required host check cannot be waived by labelling it
SKIP. Save the integrated candidate for O5 without a concurrent writer.

## 8. O5: independent review and corrections

Use calibration row O5 in a fresh review context. Derive the critical failure
conditions from original requirements before reading the implementer's
conclusions. Use the canonical calibration's escalation rules if a critical
question remains unresolved.

Use a fresh review context with the frozen contract, candidate revision, tests
and raw evidence. Avoid carrying implementation deliberation into the review.
A model change alone is not independence, and a separate chat still shares
filesystem visibility unless explicitly isolated. The reviewer must derive
counterexamples from the contract and inspect the implementation, not simply
endorse the implementer's summary.

Attempt to falsify score availability, public/private separation, packet parity,
monetary reconciliation, identity scope, source sealing, interruption safety and
the no-provider guard. Trace admission to actual dispatch to find alternative
entry paths. Check assertions against meaningful negative controls and inspect
the generated result artefacts. Review whether the ordinary worker receives a
fair chance under the same tools and feedback.

Record findings with severity, requirement, evidence, reproduction, owner and
closure test. A launch, privacy, evidence-integrity or accounting defect blocks
completion. Return fixes to their implementation owner; rerun affected tests
and integration gates for the changed revision. The reviewer rechecks closures.
Do not call a report independent if the same context authored and approved its
own fix without another challenge.

**Exit:** no unresolved blocking findings; every mandatory requirement has
reproducible evidence; no unsupported broadened claim; explicit qualify or do
not qualify decision. A failed review is a useful result and returns to the
relevant stage rather than weakening the gate.

## 9. O6: package the result and stop at the paid boundary

The O6 assignee assembles decisions already made in O0 and reviewed in O5. The schedule,
cost notice and readiness disposition below must have reviewed inputs. New
statistical, trust-boundary or authorisation judgements return to the relevant
design/review owner; unresolved inputs remain explicit blockers.

Produce a concise operator runbook, schema descriptions, evidence index,
requirements-to-test map, supported-host statement, known limitations and a
signed-off readiness disposition in `docs/stage-results/`. Here sign-off means
named review responsibility and recorded result, not cryptographic identity.

Prepare a new prospective development schedule and exposure ledger. Reused
historical patches are development controls, never unseen reserved cases. The
next feasibility block is proposed at no more than four fresh producers, with a
stop if no public eligible state appears. Separate its calibration slice from
any subsequent paired development slice. Define primary outcome, no replacement
of inconvenient results, stop rules and the fields needed for later costing.

Prepare an exact payload inventory, destination, registry-class selections,
role/worker limits, pricing assumptions, source seal, total ceiling and launch
notice. If intended task population or acceptable quality/cost tradeoff remains
unsettled, record the decision and its effect; do not invent a promotion margin.
Check existing authorisation against this scope before requesting any genuinely
missing approval. RC validation approval and closed campaign budgets do not
automatically reopen deferred research.

Use two distinct final statuses: **offline qualified** and **live launch ready**.
Offline success is possible while a missing current identity canary, exact
payload, cost envelope or authorisation still blocks live launch. A future
paid identity probe can precede a producer once separately justified, but no
new producer may precede successful offline qualification.

**Exit:** the package has a traceable disposition and an accurate next handoff.
No paid producer is run in O0-O6. Do not publish a release or promote Controller
as part of this completion. Consumer changes, if any, need a separately identified
future artefact; the existing RC evidence is not rewritten.

## 10. Mandatory acceptance matrix

| ID | Priority | Owner | Required evidence |
| :--- | :--- | :--- | :--- |
| E01 | P0 | O1 | Correct, incorrect and partial controls produce the predetermined result |
| E02 | P0 | O1 | Actor failure and evaluator/infrastructure failure remain distinct; unavailable score stays unavailable |
| E03 | P0 | O1 | Timeout, malformed output and excessive output finish within declared bounds |
| E04 | P0 | O1 | Criterion change, protected-data introspection and forged output cannot earn acceptance |
| A01 | P0 | O2 | Canonical rounding equivalence accepted; true cost mismatch and invalid numbers rejected |
| A02 | P0 | O2 | Writer, identity, attempts, unresolved charge and budget gates remain enforced |
| A03 | P0 | O2 | Both public entry branches and every ineligible outcome have executable controls |
| F01 | P0 | O2 | S/A shared public bytes and acceptance are identical; private data cannot affect admission or packet |
| F02 | P0 | O2 | Host verification is explicit; justified no-change and clarification are legitimate outcomes |
| I01 | P0 | O3 | Exact scoped identity evidence accepted; missing, stale, forged or mismatched evidence blocks |
| I02 | P0 | O3 | Registry is sole current mapping; drift stops; served effort is not inferred |
| R01 | P0 | O4 | Repeated resume/settlement never duplicates an uncertain or completed call |
| R02 | P0 | O4 | Interrupted and cancelled attempts preserve accounting and declared writer boundary |
| S01 | P0 | O4 | Input/dependency mutation invalidates seal; clean checkout and output boundary checked |
| H01 | P0 | O4 | Historical campaigns, hashes and missing-score records remain unchanged |
| Z01 | P0 | O4 | Fake runs cannot fall through to a live provider; zero provider intent/calls proved |
| G01 | P1 | O4 | Full offline gate and applicable checked build pass for the final candidate |
| V01 | P1 | O5 | Independent review findings have reproductions and closure evidence |
| D01 | P1 | O6 | Qualification dossier separates observed facts, inferences and untested scope |
| D02 | P1 | O6 | Live prerequisites are explicit; offline PASS is not a paid-launch authorisation |

O0 may split these into more tests, but removing or weakening a requirement needs
a documented scope decision. A test that merely mirrors the implementation is
insufficient evidence. Use independent expected outcomes and malformed or
adversarial variants that would fail if the guard were removed.

## 11. Handover procedure and escalation

For each transition, use `tools/handoff.py new`, fill all ten headings and run
`tools/handoff.py check <file>`. Include the source revision, dirty-file ownership,
completed requirements, exact commands/results, remaining failures, next action,
target model/effort and development versus experiment cost/time estimates.
Generate later handoffs at stage completion; do not pre-fill unobserved success.

The receiving session reads the named handoff as its first project document and
starts retrieval with its own Graft freshness check. Carry the absolute root,
Graft requirement and relevant spans. Check its connection and checkout binding;
do not assume another session's MCP connection or configuration was inherited.
Initial freshness for this planning task reported a stale committed index.
Current source spans require verification; paid semantic refresh is not a
prerequisite for every stage and is not silently included here.

Pause dependent work for unresolved contract design, unavailable required host
isolation, two failed diagnostic hypotheses, or a material scope/cost increase.
Resolve ordinary implementation choices within the frozen contract. Handoff
fields must say whether model/effort is requested, host-accepted or observed;
never infer the current session's setting from the persona file.

## 12. Cost, elapsed time and tradeoffs

These are planning assumptions dated 2026-10-02, derived from calibration
revision DMC-1, not measured development costs or spending ceilings. They are
a dated budget snapshot, not model-selection authority. Recompute them when
the calibration changes. At [OpenAI Standard API rates](https://developers.openai.com/api/docs/pricing),
per million tokens, Astra input/cache-read/cache-write/output rates are
USD 10/1/12.5/50; Sol rates are USD 2/0.1/2.5/10.
[Luna rates](https://developers.openai.com/api/docs/models/gpt-6-luna) are USD
0.1/0.01/0.125/0.5. Fast rates are twice Standard.
The [Astra model page](https://developers.openai.com/api/docs/models/gpt-6-astra)
describes the long-context premium above 272K input tokens per request. Refresh
the relevant rates and tier before each handover. Desktop plan usage is not
an API invoice, and the current session's billable usage is unavailable here.

For budgeting, assume each stage consumes 100K-300K cache-write input tokens,
200K-1M cache-read tokens and 20K-80K output tokens including billed reasoning,
across multiple calls. Treat input categories as disjoint: no double charging
ordinary input and writes. Assume no request exceeds the short-context threshold.
At Standard rates this is USD 2.45-8.75 per Astra stage, USD 0.47-1.65 per
Sol stage and USD 0.0245-0.0875 per Luna stage. The current four-Sol/three-Luna
allocation is about USD 1.95-6.86 before retries. Allowing up to 25% extra usage
and Fast processing gives an illustrative envelope of about USD 2-18. With no
cache reuse, conservatively charging all repeated input as writes raises the
upper sensitivity case to about USD 42.02. The prior two-Astra/two-Sol/three-Luna
allocation was about USD 5.91-21.06 at Standard before retries. These comparisons
assume identical token volumes; review and escalation can reduce or erase the
savings. Additional Astra or fallback sessions must be costed in their handoffs.
These arithmetic scenarios are not measured costs or speedups.

Local shell tests and local Graft retrieval have no experimental provider call
in this plan; their output still consumes development context. External paid
tools and semantic refreshes are excluded and must be costed separately if
introduced. O0-O6 experimental Claude spend is projected at USD 0 because all
transports are offline. This does not mean the development sessions are free.

The table sums to 8.75-17.5 hours of sequential active work, excluding operator
waits and substantial redesign. Under clean independence, overlapping O1-O3
reduces the mathematical critical path to 5.75-11.5 hours; allow roughly 6-13
hours for coordination and integration. These are low-confidence scheduling
estimates. Parallel execution may consume more tokens and create merge/review
work. It does not accelerate the ordered contract, integration and review gates.
The model revisions retain these scheduling allowances until execution supplies
evidence; lower token prices do not demonstrate shorter end-to-end elapsed time.

The main design tradeoffs are deliberate:

- A new research version protects historical evidence, at the cost of an extra
  version to document. Reuse shared mechanisms to limit duplicated maintenance.
- Strict identity and source binding prevent false qualification, at the cost of
  legitimate stale-evidence stops and occasional separately costed canaries.
- Shared complete feedback makes comparison fairer; it may eliminate a previously
  apparent Controller advantage. That improves the validity of the experiment.
- Strong evaluator separation requires host-specific work. Qualify a narrow
  supported environment rather than promising portable isolation without tests.
- Manual handovers provide visible operator control. Optional parallel execution
  reduces elapsed time only when file ownership and interfaces remain stable.

## 13. What follows, conditionally

O6 does not establish uplift. The subsequent Q2-Q6 programme remains described
in the post-RC analysis. Assign its future development tasks using the current
calibration's task rows and escalation policy, after checking the actual scope.
No model choice here preauthorises a later campaign or review.

Progression is new bounded feasibility, fair paired development, comparison with
a simpler use of extra compute, independently frozen confirmation, then a
separate whole-policy pilot and confirmation if justified. Representative
intake may be prepared in parallel; a Controller-enabled policy requires credible
mechanism evidence. Each live stage needs its own fresh handoff, exact campaign
scope, cost notice and applicable authorisation. Negative or inconclusive
results can close the candidate with B0 retained.

## 14. Plan delivery status

This task created the plan, a capability record and the initial O0 handoff. It
did not implement O0-O6, launch a new session, change this session's model,
run a paid probe or rebuild the product. Documentation checks and handoff
validation passed: the existing harness's prose check reported 920 authored
files clean, all 51 local links across the four qualification documents resolved,
`tools/handoff.py check` accepted the O0 handoff, and scoped `git diff --check`
passed. This is documentation verification, not a fresh full runtime test run.
Resolve the next manual setting from calibration row O0 and verify the O0
handoff snapshot before use.
