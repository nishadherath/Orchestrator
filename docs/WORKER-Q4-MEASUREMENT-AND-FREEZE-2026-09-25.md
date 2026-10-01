# Q3 measurement correction and Q4 implementation contract

Date: 2026-09-25. Status: **M1–M3 complete; Q4 retains B0 with no candidate**.
The operator authorised work through Q4 and requires a stop before Q5. This
document refines that work after the [contract audit](stage-results/worker-q3-contract-audit-2026-09-25.md).
It neither changes B0 nor authorises a reserved campaign. The Q0 statistical
thresholds, Q2 independent-family rule and historical manifests remain intact.
The subsequent [Q4R candidate recovery](WORKER-Q4R-CANDIDATE-RECOVERY-2026-09-26.md)
is a separate prospective public experiment after M3 selected no candidate.

## Decision and scope

Do not run another paid screen against the existing Q3 grading contract.
Repair measurement and first-cell attribution first. The frozen eight-task
result is 3/8 accepted and 87.5/100. A retrospective, contract-based sensitivity
is 5/8 and 94.375/100, not a replacement score. Perfect repairs would then add
only 5.625 mean executable points on those cases, below Q0's ten-point quality
threshold. An acceptance benefit remains possible. Neither calculation proves
how another model would perform or how representative these tasks are.

The defects are specific:

| Finding | Evidence | Required treatment |
| :--- | :--- | :--- |
| P03 penalises wording and a new API absent from the public issue | Isolated stopped-patch probes reproduce correct sorted suggestions without a colon; no `NoSuchCommand` export was requested | Preserve 55/100; use public-obligation mappings in new rubrics |
| P07 requires an unspecified exception class | The stopped patch rejects the two malformed inputs with package-specific `ValueError` subclasses | Preserve 90/100; distinguish semantic rejection from exact-class compatibility |
| Executable scores omit diagnosis and reporting | `worker_wsl_q3_public._grade` sums behavioural predicates only | Add independently checked diagnosis/reporting components prospectively |
| `false_success` conflates two different facts | It is `root_state == accepted and not hidden_acceptance` | Retain that field historically; record root acceptance gap and unsupported completion separately |
| Critical-error coverage is untested in the expansion | Every P03-P08 oracle row has `critical: false` | Mark historical coverage unavailable; calibrate actual critical failure sentinels |
| Experimental treatment changes repair effort too | `task_executor._experimental_policy` constructs `[selected, selected, fallback]` | New versioned experiment uses a common repair tail |
| Current Q3 host admits only two cells | Both `Q3WslAdapter` and its launcher whitelist Sonnet-low/Opus-high | Version adapter, launcher and attestation together; retain historical versions |

No reserved task should be selected on the basis of a model's difficulty or
score. Public pilot changes are explicitly development material. Do not change
the Q3 originals, count their variants as independent families, or use the N6
reserved set to fill a shortage.

## M1: measurement implementation, GPT-5.6 Sol High

Implement developer-only `tools/worker_quality_v2.py` and
`test/harness/worker_quality_v2_tests.py`. These filenames are planned, not
existing deliverables. Keep the old grader's meaning unchanged. Each new task
has an explicit public specification and a private rubric with a hash-bound
mapping from every scored or mandatory predicate to a public obligation.
The rubric identifies its comparator: semantic set/order, value, state,
side effect, or exact text/type. Exact formatting and exception types require
a public compatibility requirement. An implementation name or reference patch
is never an implicit requirement.

Use a common 100-point decomposition for all new task units:

| Component | Points | Evidence |
| :--- | ---: | :--- |
| Required executable behaviour | 60 | Weighted deterministic predicates linked to public obligations |
| Preserved invariants | 20 | Independent negative, boundary and regression checks |
| Diagnosis and resolution of ambiguity | 10 | Task-specific cause/evidence predicates, including explicit uncertainty where warranted |
| Reporting and remaining work | 10 | Structured claims checked against stopped artefacts and root-owned execution evidence |

Do not award points merely for fluent text, matching a hidden phrase, mentioning
a file, or saying tests passed. Each task allocates its 10 diagnosis points
before any worker outcome, to observable claims or a reproducible diagnostic
witness. It must credit a materially different valid diagnosis. For an
unambiguous task, justified diagnosis earns those points without an unnecessary
question. For a deliberately unresolved ambiguity, the public issue contains
the conflicting evidence, and the rubric credits identifying the unresolved
choice, its consequence and a safe conditional next step. Never penalise a
worker for declining to guess information the task does not supply.

Require a small JSON final report in the public worker prompt, with
`status` (`completed`, `partial`, `blocked`), `diagnosis`, `evidence`,
`checks`, `remaining` and `clarification`. Freeze field types, list/string
bounds and maximum UTF-8 bytes in a schema before dispatch. Use 16 KiB as the
report limit. Retain its original bytes or an explicit truncation/missing
marker. A malformed or missing worker report receives zero report points;
it does not erase executable progress. A transport failure that loses a report
which was actually received is an evaluator integrity fault, not a worker
failure. Do not reconstruct an unrecorded historical report from a CLI success
subtype or invent a worker claim.

Capture the final provider `result` text in a new evaluation adapter receipt,
outside the actor. The existing `WorkerAdapter.run` discards that text; use an
evaluation-specific stream hook/subclass rather than silently expanding every
consumer receipt. Bind report bytes to invocation, final collected revision,
stream digest, task, prompt and requested cell. Preserve only the needed final
response and relevant tool-result evidence. Do not retain internal reasoning,
credentials or unrelated transcript data. Candidate text is untrusted data,
never executable instructions for the root evaluator.

Keep these result fields separate:

- `behaviour_accepted`: all mandatory functional/invariant predicates pass.
- `hidden_accepted`: behaviour accepted, required report valid, no critical
  error and no contradicted completion claim. This is the new full-task
  acceptance definition and must be printed in every new manifest.
- `root_acceptance_gap`: the root accepted but full hidden acceptance failed.
- `unsupported_completion`: an explicit `completed` report with a demonstrated
  unmet public obligation, or an explicit successful-check claim contradicted
  by retained execution evidence. An unknown fact alone is not a contradiction.
- `report_observability`: present, worker-malformed, worker-missing, or
  transport-invalid. Invalid transport makes the comparison inconclusive.
- `critical_error`: a failed predeclared critical invariant, with evidence.
  Coverage is separate from value: no critical probes means unmeasured, not safe.

Retain executable and report components independently. An incomplete but honest
diagnosis can earn useful points; a report-only answer cannot earn executable
points. Public smoke-check acceptance remains distinct from hidden quality.
Partial credit never overrides an integrity, critical-error or cost stop.

For every task calibrate baseline, reference, materially different correct
variant where feasible, useful partial, diagnosis-only, honest incomplete,
false completion, wrong diagnosis, public-answer copying and critical failure.
Reference and alternative must meet all public obligations, not match source
bytes. Use multiple cosmetic report variants to reject keyword grading. The
false-completion and critical-failure variants must trip their respective
flags independently. A root pass with an honest partial report must not become
an unsupported-completion claim. Include missing/truncated reports, wrong
revision bindings and a forged test-success claim in regression tests.

Report evaluation must be deterministic where executable evidence permits it.
For an irreducibly semantic dispute, mark the task invalid for qualification
pending a blinded review of public obligations, patch and report, with cell
and cost withheld. Freeze that review procedure before dispatch. Do not add a
paid LLM judge or silently turn subjective uncertainty into pass/fail.

M1 exit: focused tests prove the distinctions above, existing Q3 evidence and
its audit still validate, no paid call is made, and the full offline harness
passes. Measurement code exists and is tested; no claim yet about live report
capture or improved routing follows.

Implementation record: M1 completed on 2026-09-26 local time. The prospective
grader, evaluation receipt extension and adversarial regression tests passed.
The provider-free details and exact evidence digests are recorded in
[the M1/M2 stage result](stage-results/worker-q4-m1-m2-2026-09-26.md).

## M2: equivalent dispatch and public calibration, GPT-5.6 Sol High

Add a new explicit experimental policy version. B0 uses
`[Sonnet-low, Sonnet-low, Opus-high]`. A candidate uses
`[candidate-first, Sonnet-low, Opus-high]`. Both use the same public feedback,
stopping rules, tools, prompt, token/turn limits and root USD 6 allocation.
The common tail is conditional on the same root verification result. Retain
every attempt and report, with the last stopped revision as the episode output.
Never feed hidden results into a repair or select a best hidden-scoring attempt.
Keep the historical `[selected, selected, fallback]` experiment supported under
its original version; it cannot support a first-cell-only claim.

Implement versioned Q4 evaluation adapter, launcher, fake provider and boundary
attestation. Admit only cells in the manifest and current registry; exact
identity mismatch blocks the arm, it never substitutes another model. Record
requested effort separately from served effort, which may remain unknown.
Test argument rejection, environment overrides, report capture, isolation,
writer stop, timeout, collection, protected edits, uncertain cost and replay
refusal before any provider call. Bind the new code and installed runtime
hashes in the new manifest; do not refresh old manifests to match new code.
If an additive executor change affects shipped code, run shared/Controller
regressions and rebuild through `tools/build_dist.py`. Do not edit `dist/` by
hand or alter Controller algorithms.

Build new public calibration revisions on P04, P05, P06 and P08 source families.
P04 is a B0-success control; the others have observed omissions explicitly
described by their public issues. Exclude P03 and P07 from new paid selection
while retaining them as measurement regression cases. Copy/version development
material rather than modifying a frozen actor, oracle or task hash. Apply M1's
report contract and audit every old predicate before reusing it. New scores
are not directly comparable to the old 100-point behavioural scores.

Require provider-free evidence for every calibration variant, independent
correct solutions, source provenance and actor denial of oracle/report-store
access. Check timer-sensitive graders at least ten times on unchanged baseline
and reference, then replace unstable wall-clock checks with synchronisation
predicates. Public development grading reveals no reserved material.

M2 exit: fake provider demonstrates identical repair tails, no hidden-feedback
repair, bounded costs and report binding; provider-free WSL calibration passes.
Full offline harness passes. Historical actors and bound files are unchanged.

Implementation record: M2 completed on 2026-09-26 local time. The versioned
common-tail policy, three-cell Q4 boundary, installed WSL launcher attestation
and four-family public calibration passed without a provider call. M3 is the
next stage and remains a development screen rather than a shipping-policy
change.

## M3: bounded public information screen, GPT-5.6 Sol High

Run only after M1/M2 exit. This is the prospective screen design, not an exact
manifest or claim of execution. Four public families each receive four fresh
episodes: B0 repetition A, B0 repetition B, Sonnet-xhigh and Opus-high. This is
16 episodes, at most 48 task calls with the common two-call repair tail.
Allow at most three current-host identity probes, one per distinct cell.
Episode allocations are USD 6 each; identity allocations are USD 1 each:
**USD 99 maximum local admission allocation, 51 calls maximum**. In-flight
provider overruns remain possible and must be reconciled, not hidden.

Use a four-by-four Latin order for the four episode labels, assigned by the
hash order of the four public task hashes. Give every episode a pristine
workspace and fresh conversation. The two B0 repetitions measure model-run
variation; repeating a grader alone does not. Record provider cache counters
and arm order; fresh local state does not prove a cold provider cache. Do not
force cache misses or subtract an assumed cache benefit from actual costs.

Before execution, create exact manifest, dated cost/time notice and authorisation
record bound to the operator's standing approval through Q4. Use authenticated
Claude Code in WSL. Preflight auth without printing credentials. Refresh prices
for the notice and distinguish API-equivalent usage from subscription billing.
Do not split an enlarged campaign into smaller notices to evade the USD 100
approval rule. A missing cell, failed calibration or unresolved charge stops
the run; a terminal failure is recorded, never automatically replayed.

Use these exploratory selection rules, fixed before responses:

1. A candidate must have zero observed critical errors, valid accounting and
   no more unsupported completions than either B0 repetition set.
2. Against each B0 repetition set separately, it must have non-negative net
   acceptance and mean quality, and improve acceptance on at least one task
   in both comparisons or improve mean quality by at least ten points in both.
3. Its total actual API-equivalent cost must be at most 1.5 times the mean
   total of the two B0 sets and at most USD 1 extra per triggered task. These
   adopt Q0's conservative provisional economic guards for screening. Final
   Q5 approval must explicitly include the same or a newly justified premium.
4. Of candidates meeting all guards, discard cost/quality dominated choices
   and select the least actual-cost candidate. Break an exact cost tie by higher
   mean quality, then Sonnet-xhigh. Freeze at most one candidate. No inference
   from four selected public families is a reserved-population claim.
5. If none qualifies, retain B0 and record Q4 as a no-candidate decision.
   Do not spend weeks building a reserved corpus for an absent policy. A new
   public design may later be proposed with a fresh budget and rationale.

Sonnet-xhigh is a candidate because the earlier 15-cell micro-screen found
it the cheapest cell with three successes; Opus-high tests changing model
instead of only effort. That evidence is weak, not a validated ordering.
Fable-high also passed those microtasks at higher observed cost without an
extra success. It is therefore not automatically added to this USD 99 screen.
Keep all supported effort levels and models in the registry and manual
selection; do not force usage quotas. If new public evidence identifies a
plausible Fable-only benefit, specify a new bounded comparison prospectively.
Higher effort is not assumed to improve quality monotonically.

M3 exit: completed/incomplete decision record, all receipts and stopped patches,
two B0 variability summaries, measured cost and either one provisional candidate
or explicit abstention. A favourable result permits Q4 preparation, not promotion.

Implementation record: M3 completed on 2026-09-26 local time. All 16 public
episodes were represented with 16 settled calls and USD 9.849044605 of
provider-reported API-equivalent usage. One stopped campaign was continued
without replay after a known terminal xhigh output-limit failure. The frozen
rule selected no candidate and retained B0. Opus-high passed all four executable
behaviour contracts but exceeded the 1.5x B0 cost guard; Sonnet-xhigh failed
quality and safety guards. Full details, evidence digests and limitations are
in [the M3 stage result](stage-results/worker-q4-m3-2026-09-26.md).

Predeclare the reserved repetition rule now: use one repetition per arm if
all four valid B0 pairs agree on acceptance and safety/reporting flags and
each pair differs by less than ten quality points; otherwise use two. This is
a cost-control rule based on a small public diagnostic, not proof of low model
variance. Freeze the resulting count before any reserved response. Report the
one-repetition limitation explicitly; never add a repeat because a reserved
answer disappoints. Invalid public accounting or grading is a stop, not a vote
for either repetition count.

## M4: independent reserved frame and freeze, GPT-5.6 Sol High

Proceed only if M3 supplies a provisional candidate. Retain Q0's narrow offline
Python service/CLI stratum and Q2 source-size, dependency, licence and isolation
limits. Prepare a prospective inventory before reserved worker outcomes with
canonical URL, full commit, upstream family, licence bytes/hash, source count,
dependency lock, setup, issue origin, mechanism, package size, eligibility and
exclusion reason. Search enough candidates to fill 24 independent families plus
an ordered replacement pool. Never pad small projects to the line threshold,
count sibling projects/templates twice, or count vendored dependencies as the
task's authored source. Source acquisition may use the network; actor grading
must remain offline.

Predeclare six families per coverage cell: cross-module contract, state/recovery,
concurrency/protocol, and diagnosis versus conflicting evidence. Assign one
primary cell per issue using its public trigger before seeing model output;
additional tags do not increase its weight. Within each cell use Q2's exact
`SHA256(worker-q2-2026-09-25|canonical-url|commit)` order. Publish exclusions and
the next-family replacement order. Exclude all earlier N5/N6/R and P01-P08
families, including forks and shared-template derivatives. Record reproducible
reasons for setup/licence exclusions; model difficulty never permits replacement.

Build M1-calibrated tasks after inventory freeze. Reserve 2-8 existing editable
source files, retain complete source provenance and licences, and do not expose
oracles, reference patches, inventory labels or rubric weights to the router or
actor. Store hidden artefacts outside the actor Graft index. Preserve invalid
tasks and reasons; after reserved worker output, an invalid grader makes the
study inconclusive unless the original analysis already specified its treatment.

Freeze a simple experimental public-feature policy separately from the current
unqualified selector priors. Inputs are public issue/source/test spans only.
Route to the one M3-selected cell when the task is in scope and at least one
of these public triggers is established:

- One required contract change crosses at least three distinct source modules.
- A state/recovery or concurrency/protocol requirement links at least two
  independently testable invariants across modules, such as returned object
  identity plus cached identity, or returned path selection plus creation scope.
- The stated diagnosis conflicts with a reproducible public observation, and
  resolving the conflict requires inspecting more than one source module.

Each positive feature requires concrete citations and observable mechanisms,
not a corpus tag or subjective difficulty label. Count semantic invariants,
not paraphrases of the same requirement. A routine two-module contract change
without those additional properties stays on B0 even inside the broad stratum.
Unclear public evidence also abstains. Unsupported cell or insufficient budget
abstains to B0 only when B0 is itself operationally admissible; otherwise stop.
Retain all abstentions in the intent-to-route denominator. Outside the stratum
keep B0. Apply this exact trigger rule in the M3 simulation before choosing a
policy; changed-cell observations on non-triggering tasks are diagnostic only.

Test that changing task ID, family label, hidden score or reference solution has
no effect on selection, while changing relevant public facts can. Bind public
assessment before any response. If assessment is operator-authored, the claim
is only about routing from supplied facts, not autonomous task understanding.
An automated public assessor must be frozen, validated and its calls/cost included
in both the manifest and economic comparison. Do not silently omit that cost.

Before freeze report the policy's coverage from public inputs, including
same-cell controls. Recalculate power with plausible task-level win/loss rates
that include abstentions. Do not use triggered-only power to promise an effect
in the full sample, or change the trigger threshold after reserved outcomes.

The planning sample is 24 families, with the M3 rule fixing one or two repetitions
per arm: 48 or 96 episodes total. With two, aggregate repetitions at family
level: both must pass for acceptance and quality is their mean. With one, use
its acceptance and score. Repetitions never double the independent sample count.
Freeze arm/repetition order by balanced blocks before any worker response. Analyse the
full intent-to-route sample with Q0's unchanged tests/effect sizes, and display
same-first-cell pairs as variance controls. Triggered-only summaries are secondary.

The existing exact-power tool gives the following hypothetical sensitivity at
one-sided alpha .025. Probabilities describe independent task-level wins/losses
after aggregation; they are assumptions, not pilot estimates:

| Independent families | Power, win .25/loss .05 | Power, win .35/loss .05 | Upper 95% adverse rate with zero events |
| ---: | ---: | ---: | ---: |
| 24 | 28.35% | 57.58% | 11.73% |
| 48 | 67.54% | 92.80% | 6.05% |
| 72 | 87.36% | 99.00% | 4.08% |

These are marginal directional-test powers, before economic, effect-size and
safety guards. A 24-family study is a bounded, low-power initial comparison,
not an 80%-powered qualification promise. Do not enlarge it after seeing reserved
results. A larger initial design requires a prospective corpus, budget and power
decision before freeze. Zero observed critical errors cannot establish low risk.

At the provisional USD 6 root cap, one repetition implies USD 288 local allocation
and at most 144 task calls; two imply USD 576 and 288 calls, before any separately
required probes. Those are not spend predictions. Recalculate prediction from M3
receipts, repair frequency, assessor overhead and uncertainty, and state it separately. Q5 needs its own exact
operator approval regardless of standing Q4 approval. Do not launch it here.

The freeze command must reject missing inventory/licence hashes, unresolved
calibration, unlabelled critical coverage, missing reports, unequal repair tails,
changed policy inputs, unavailable identity, absent cap/order/repeat rules or
mutable code dependencies. Include all runtime, adapter, grader, policy, prompt,
schema, source, reference/calibration and analysis hashes. Freeze abort rules for
integrity failure, unreconciled spend and critical errors; analyse incomplete
scheduled work conservatively under Q0 rather than deleting failed episodes.

M4 exit: immutable reserved inventory, validated independent task packages,
candidate policy, exact analysis and pending Q5 approval manifest. Publish a
stage record and stop. The existence of this design document is not that exit.

M4 disposition: not entered. M3 supplied no provisional candidate, so the
predeclared entry rule forbids building or running the reserved frame for this
policy. Q5 is not authorised or prepared.

## Development sequence and estimates

Use GPT-5.6 Sol High for M1-M4 implementation under this explicit design. No
subagent is needed. Return a focused design question only for an unresolved
contract, rather than repeatedly switching at stage boundaries. Preserve the
existing dirty worktree, run focused tests during implementation and the full
offline harness at delivery. Consumer files change only when implementation
actually changes their contract; developer-only evidence is not copied to `dist/`.

M1-M2 engineering is estimated at 4-8 hours; M3 adds 1-3 hours of preparation
and approximately 1-4 hours elapsed live work, subject to new host measurements.
M4's 24 independent families can require 12-30 hours of curation and validation.
These are planning estimates, not completed work or guaranteed turnaround.
The next [implementation handoff](../handoffs/2026-09-25-worker-q4-measurement-repair.md)
prices only M1-M2. Re-estimate remaining development and the paid screen when
its manifest exists. Do not imply the handoff's development cost buys Q4 or Q5.
