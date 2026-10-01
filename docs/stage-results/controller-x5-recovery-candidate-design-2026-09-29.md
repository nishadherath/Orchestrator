# X5 recovery candidate: development design

Date: 2026-09-29 Australia/Sydney. Status at 2026-09-30: **R3 stopped after
one paid producer; no recovery case qualified**. This is a new candidate hypothesis,
separate from the closed X5 v7 preflight Controller candidate. B0 remains the
shipping default. X6 reserved cases remain sealed.

## Why change the mechanism

The completed X5 comparison had four suitable tasks with full protected
acceptance in B, S and A. A's Controller frame added cost and latency but no
measured benefit. Its payment packet did contain source-linked diagnoses of
two independent faults, yet the worker-only arms solved the same task. The
packet also had a `gap` outcome and a generic safe next action, so a route or
role call is not itself useful progress. Worker N5 development accepted 11 of
12 tasks under B0. Its one miss, D03, was detected by protected grading after
a public success; using that hidden result as a Controller trigger would leak
the oracle. D03 may inform debugging, but cannot supply a prospective trigger.

The new hypothesis is that a Controller adds value when it receives a
settled, publicly observable failed or partial worker attempt. It can inspect
the failed code and public check, separate competing causes, and pass a
source-grounded next test to a second worker. Easy tasks finish on the normal
worker path and incur no Controller cost. This mechanism must be measured,
not assumed from the quality of a generated frame.

The prior v7 B0 suitable arms all passed their public checks on their first
worker attempt. R3's R01 producer did too, despite a protected critical miss.
That miss cannot be used as a prospective Controller trigger. R02 was not run
because an eligibility contract error stopped the frozen R3 runner. No
post-result replacement case can be used to obtain two eligible R3 pairs.

## Entry and paired continuation

Author new development cases with at least three interacting source files,
two plausible independent causes and a public issue that describes symptoms
without naming a repair. Each case needs an independent protected oracle, a
reference repair, at least two plausible wrong or partial repairs and an
isolated public check. Validate the baseline, reference and wrong variants
provider-free before any paid worker. Keep case authorship, oracle and grader
outside the actor root and Controller context.

Run one bounded B0 producer attempt per case. Eligibility is decided only
from the frozen public issue, the settled producer receipt, the producer's
report and public check output. A case enters the matched continuation only
if the producer has a settled charge and either the public check fails or
the report explicitly claims `partial` or `blocked` with a concrete unresolved
test. Hidden quality, protected checks and later A outcomes cannot determine
eligibility. If the producer is accepted by the public contract, uncertain
only because its host lacked an execution tool, it is not automatically
eligible. An unresolved provider charge, active writer or missing receipt
stops the case before cloning.

Freeze one source and report snapshot with content hashes. Materialise two
isolated successors from those identical bytes. S receives a direct second
worker attempt. A receives one Controller invocation and then the same B0
worker ladder, effort request, tool surface, acceptance contract and USD 5
task ceiling as S. Controller and public assessment spend consume A's task
ceiling. The only additional worker input in A is the validated Controller
handoff appended as explicitly untrusted evidence. Controller may read the
public failure and actor source, but must not edit the actor or see the
protected oracle. Both successors are single use. No retry may replay a paid
invocation after a crash or uncertain receipt.

The first feasibility run should use the existing standard Controller profile
and packet contract, without simultaneous role or prompt tuning. Inspect
whether it produces specific verified findings and useful discriminating
tests on the partial state. If it repeatedly returns a gap or generic action,
stop that candidate and redesign the evidence contract before paying for a
larger comparison. A later packet revision must require machine-checkable
source references rather than relying on a model's `verified` label alone.

## Measurement and stop rules

Primary paired outcome is protected functional acceptance of the successor.
Secondary outcomes are protected partial score, critical violation, false
success, honesty of the completion claim, useful source-grounded diagnosis,
total cost and elapsed time. Report the producer cost once in aggregate and
both full and amortised per-continuation costs. Keep host-run checks distinct
from worker-run probes. Record actual served model; unsupported served effort
is unknown. Include an ordinary-worker control and a missing-decision control
in the development set to test that Controller remains selective.

Use two fresh eligible cases for an initial feasibility screen. Do not expand
if either arm has unresolved accounting, the paired source snapshots differ,
the Controller or worker identity is invalid, a critical error appears in A,
or A's handoff has no actionable grounded finding. If A shows no protected
improvement over S on either case, stop and diagnose rather than buying more
episodes. A positive feasibility signal only authorises considering up to
eight predeclared development continuations; it is not an uplift claim.
Before a larger run, freeze the cases, arm order, baseline calibration,
profiles, exact score, analysis, budget and cost notice. The current X0 power
analysis forbids treating a small favourable development set as promotion
authority. Any X6 proposal still needs a separate sample and power contract
and an independent X7 review.

No new paid scope is authorised by this design. An explicit approval for the
exact new manifest and ceiling is required before a provider call, as the
v7 approval review established for a distinct campaign.

## Provider-free evidence at 2026-09-29

R01 and R02 are fresh development cases with distinct public symptoms and
protected oracles. The provider-free fixture tests passed 3/3. Isolated WSL
grading denied oracle reads from the actor and reported R01 baseline 25/100,
reference 100/100, single-mechanism repairs 45/100 and 80/100. R02 reported
baseline 25/100, reference 100/100, and single-mechanism repairs 65/100 and
45/100. All reference public checks passed; all baseline and partial public
checks failed. These calibrations show that the cases can detect complete and
partial repairs. They do not show that a live Controller improves a worker.

The public-only protocol tests passed 4/4. They cover a settled failed public
check, equal successor bytes, root replay rejection, unsettled charge, active
writer, changed receipt cost, a public success without a concrete unresolved
test, and redirected or unexpected actor files. The live runner uses the
isolated public-check host rather than evaluating worker-edited source in the
root process. The two-case feasibility runner has a USD 30 maximum, comprising
two USD 5 producer roots and at most four USD 5 successor roots. Its paid modes
require a dated, manifest-bound notice. It has not yet made a provider call.

R3 adds a private Controller mount view because a provider-free check found
that the unprivileged Controller account could otherwise read the repository
oracle. The private view hides `test/`, `docs/`, `handoffs/` and `.git/` during
Controller assessment and role execution, while keeping the actor, installed
Graft runtime and system prompts visible. A provider-free namespace smoke
proved the oracle hidden to root and the Controller account and restored
afterward. R1 and R2 prepared roots had zero provider calls and are superseded.
The final prelaunch R3 offline harness passed 83/83. R3 was subsequently
approved. It made one settled paid call, USD 0.16955, and stopped. The frozen
eligibility helper expected Boolean `false` for `budget.unresolved`, but
TaskExecutor emits an empty list for settled roots. After the helper and
fixture were repaired, provider-free reconciliation of the original R01 state
gave `no publicly observable unresolved work`. See
`controller-x5-recovery-r3-stop-2026-09-30.md` for the measured result. The
post-repair elevated offline harness passed 83/83.

## R4 continuation and next decision

R3 cannot resume after the runtime repair. R4 used a new frozen, approved
single-case manifest for the pre-authored, unrun R02 case. Its full offline
gate passed 83/83; its one B0 producer settled USD 0.1179006 and achieved
public and protected acceptance on the first attempt. R4 therefore created
no S/A pair. See `controller-x5-recovery-r4-result-2026-09-30.md`.

The two development producers together had no prospective recovery entry.
Do not select replacement cases after seeing this result or use R01's hidden
miss as a trigger. Further Controller work needs a prospectively calibrated
public failure or concrete partial distribution and a matched direct-worker
control. Do not access X6 reserve data for this development redesign.
