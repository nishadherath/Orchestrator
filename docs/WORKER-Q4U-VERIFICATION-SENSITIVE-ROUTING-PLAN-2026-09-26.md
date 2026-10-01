# Q4U: verification-sensitive worker routing

Date: 2026-09-26 UTC. Status: [U0 diagnosis](stage-results/worker-q4u-u0-2026-09-26.md),
[U1 acceptance guard](stage-results/worker-q4u-u1-2026-09-26.md) and
[U2 public-check hypothesis](stage-results/worker-q4u-u2-2026-09-26.md)
complete; [U3 corpus inventory](stage-results/worker-q4u-u3-inventory-2026-09-26.md)
has started. B0 is still the default. This plan does not authorise
replay of any Q4T or reserved episode, a model switch, or automatic promotion.
The operator's 2026-09-26 direction authorises autonomous completion of the
remaining worker and Controller programmes. Preserve this plan's prospective
freeze, cost, evaluation and promotion gates; do not treat historical paid
manifests as reusable authorisations.

## Diagnosis and boundary

The [Q4T S3 result](stage-results/worker-q4t-s3-2026-09-26.md) settled 18
episodes. Four public cross-component trigger-positive families showed no
medium-effort gain. Trigger-negative S05 did: Sonnet-medium passed hidden
acceptance at quality 90; both Sonnet-low repeats failed it at quality 40/50.
This single family is development evidence, not a reliable classifier label.

S05 exposed a second mechanism. Its issue asks for bounded retained memory
under repeated `peek()` calls, but its public check uses five calls and does
not measure memory. Both low-effort workers made no source edit and reported
that the existing implementation was already correct. The independent public
command passed, so `TaskExecutor` marked both roots accepted. The hidden
resource check rejected them. The medium worker replaced the accumulating
`chain()` nesting with a bounded slot. The current acceptance contract checks
output existence and command success, not whether a requested implementation
changed any output. The observed no-op acceptance and the coverage gap are
separate from the router's cross-component trigger.

Do not add an S05-specific string rule, read hidden graders at dispatch time,
or train a classifier on six families. A public-check gap is an assessment
uncertainty, not proof that a stronger model will fix a task.

## Stages

### U0: evidence and counterfactual boundary

Record exact S05 issue, public check, sealed attempts, changed-path inventory
and hidden grade as development diagnosis. Show that both baselines had zero
changed source paths, the public command passed, and the medium arm edited
`more_itertools/more.py`. Explain why the observed medium win cannot be
credited to a new policy that did not run. Preserve Q4T seals and B0.

Exit: a reproducible offline no-op acceptance test fails against the existing
contract only when an explicit change requirement is requested. No old paid
episode is relaunched.

### U1: opt-in changed-output acceptance

Add a version-1 command-contract option `require_changed_output: true`. At
admission, seal a baseline snapshot of the declared required outputs. A pass
then requires a successful command, intact protected files, all required
outputs present, and at least one required-output byte change or creation
*before* the verification command. The command must leave required outputs
unchanged; mutation blocks for review so a test-created file cannot be
mistaken for worker work on a later attempt.
An unchanged result is a qualified failure, allowing the normal bounded repair
ladder to continue. Record the comparison in evidence and recompute it in
`acceptance.qualified`; reject malformed baselines and forged pass claims.
The option is absent by default: already-correct/no-edit and investigation
tasks retain their current semantics. Do not set the option on frozen Q4T
contracts retroactively. Update the consumer schema and documentation, build
`dist/` from source, run focused and full offline checks.

Exit: a passing public command plus no edit fails *only* under the explicit
option; a real edit passes; a forged changed flag cannot qualify; a fake
executor uses its bounded repair cell after the no-op failure. Legacy
contracts and the already-correct N5 control still pass.

### U2: prospective routing hypothesis, provider-free

Define a structured public `verification_coverage` assessment with enumerated
values `direct`, `partial`, `unknown` and citations from the issue and public
checks. The same assessment turn should supply it, so it adds no separate
provider call by default. Validate evidence references and reject unsupported
certainty. Do not equate file count with difficulty. Compare three rules on
development evidence only: B0; unconditional medium for cross-component
tasks; and low-first with changed-output enforcement plus medium only when a
publicly cited acceptance criterion lacks a direct check. A low-first policy
must account for its first call and any second call; no observed S05 medium
result may be transplanted into an unrun adaptive continuation.

Exit: an offline, versioned rule table with explicit abstain/stop decisions,
cost ceilings, model availability checks and wording-stability tests. No
shipping selector edit or promotion yet.

### U3: fresh corpus and cheap canary

Build new, disjoint development tasks with public source and sealed hidden
graders. Include resource/state invariants with weak and strong public tests,
easy multi-file edits, hard single-module edits, a genuinely already-correct
no-edit control, and tasks where missing facts require clarification. Prefer
redistributable pinned upstream projects; synthetic cases must be labelled.
Freeze at least two distinct mechanisms per family and a separate reserved
set before reading any provider outcomes. Verify baseline/reference/partial
variants without a provider. Keep hidden oracles outside actor mounts and
Graft indexes. Apply the same acceptance and grading to every arm.
The existing N4 R-series generator and oracle inputs were inspected during
U0 and cannot be claimed as a blind Q4U reserve; create fresh reserved cases.

First run a small predeclared canary only where the candidate and B0 would
choose different actions. Stop if identity, report, accounting or protected
source evidence is uncertain. Do not spend on a dominated option. The actual
cost notice and manifest must precede calls. A provisional planning bound is
12 episodes, at most 36 calls and USD 48 in local allocations, with roughly
USD 3–20 API-equivalent usage and 1–5 hours; reprice and narrow this from the
fresh task inventory. Claude Code subscription invoice impact is unknown.

Exit: complete paired quality, false-success, cost and latency records for
the canary, including assessment overhead. Failure or ambiguous benefit retains
B0 and ends paid expansion.

### U4: qualification and reserved confirmation

Only if U3 justifies it, freeze the candidate and disjoint reserved campaign
before viewing reserved outcomes. Use two repetitions for changed dispatches
because S05's low-effort repeats varied by ten quality points and one
unsupported-completion flag. A policy-equivalent action may share one episode
between policies if the shared-outcome analysis is declared before dispatch;
never count that as two independent samples. Use task as the paired unit,
report intervals and family outcomes, and apply the existing N6 quality,
false-success and cost thresholds. Record all attempts and assessment overhead.
No post-result threshold changes, substitutions, or silent call replay.

Exit: either evidence qualifies a narrowly scoped shipping change followed by
`src/` to `dist/` build and full harness, or B0 remains the default with a
specific evidence deficit. Reserved results are never recycled for tuning.

## Economic guard

U0–U2 are provider-free apart from the development session itself. U3 is a
separate paid experiment with a fresh dated notice, exact manifest and
episode/call caps. U4 receives its own pre-result price and time estimate;
the prior screen's USD 3.621417509 reported API-equivalent cost is an empirical
reference, not a guarantee. Local allocations are ceilings for admission,
not invoice predictions. Unknown cache reuse is not counted as saving.
