# Q4S prospective worker candidate screen

Date: 2026-09-26 Australia/Sydney. Status: **S1 and S2 complete; S3's two-call
transport canary passed; S4 stopped after the first of six families under its
frozen invalid-transport rule. S5's six-family selection is not available.**
The [S4 record](stage-results/worker-q4s-s4.md) reports the three settled
calls, partial executable quality and stop evidence. The
[S2 record](stage-results/worker-q4s-s2.md) gives the corpus and freeze
evidence; the [S3 record](stage-results/worker-q4s-s3.md) gives the live
transport and cost evidence. This plan follows the
[transport investigation](stage-results/worker-q4s-transport-investigation-2026-09-26.md)
and the [stopped Q4R result](stage-results/worker-q4r-r1-2026-09-26.md).
The [S1 stage record](stage-results/worker-q4s-s1.md) gives implementation
and verification evidence.
Historical Q4 and Q4R artefacts remain frozen. B0 remains the default; M4 and
Q5 remain closed.

## Decision to test

Test exactly one new first-cell policy: request `worker-sonnet-medium` when a
public issue has a cross-module behavioural contract, otherwise request the
existing B0 `worker-sonnet-low`. Both arms keep the same prompt, Claude Code
version, constrained report schema, actor isolation, public feedback, root
allocation and conditional repair tail `[worker-sonnet-low,
worker-opus-high]`. Sonnet-medium is the least expensive untested effort step
above B0 in the same priced model family. Its registry wiring and availability
have been observed, but its live task quality is unqualified. Q4R's
Sonnet-high failure is a reason to bound this experiment, not evidence that
medium will succeed.

The trigger is determined before calls from the public issue and source
inventory alone. Mark **positive** only if the issue explicitly describes a
behavioural interaction between at least two named components, declares at
least three editable source modules and identifies an invariant or error path
that must remain correct across those components. Mark **negative** only if
the requested change is confined to at most two editable modules and the
public issue has no cross-component invariant. All other tasks abstain and
use B0. Store a one-sentence mechanism, exact issue/source references and
their hashes for each assessment. Do not inspect hidden tests, reference
patches or earlier model outcomes while classifying. This narrower definition
is a hypothesis about where extra reasoning might pay; it is not a fitted
rule from the Q4/Q4R task outcomes.

## S0: observed diagnosis and boundary decisions, complete

The [investigation](stage-results/worker-q4s-transport-investigation-2026-09-26.md)
separates known symptoms from unknown cause. Claude Code 2.1.273 returned
`success` without `structured_output` in one high-effort call; the same schema
worked in both B0 repetitions. No permitted source file changed in the
failed call. The current receipt lacks enough final-event metadata to
distinguish validation retries, fallback or other CLI causes. No historical
receipt will be repaired or regraded. The next stage owns prospective
instrumentation, not a retrospective reinterpretation.

## S1: evaluation-only admission and evidence hardening

Recommended development setting: GPT-5.6 Sol, High. Implement in new Q4S
evaluation files; leave production routing, Q4 and Q4R sources and `dist/`
unchanged. Finish provider-free tests and the full offline harness before
any Claude call.

1. Preserve bounded final-event metadata: subtype, structured-output
   presence, error codes, turn count if emitted, process exit, event-type
   counts, model markers, reported usage and cost, and hashes of raw stdout
   and stderr. Never store credentials or full prompt/response text in a
   tracked file. If content capture proves necessary, store it only in an
   ignored, root-owned, mode-0600 audit path with an explicit retention rule.
2. Record synthetic root markers separately from real root model markers.
   Require exactly one real root equal to the requested model, no unexpected
   child model and no protected-source drift. Retain billed-model entries as
   separate evidence; never treat a synthetic marker as proof of substitution
   or infer served effort from the CLI argument. Any ambiguity blocks
   qualification and requires reconciliation.
3. Check WSL credential freshness and the pinned launcher/schema before
   creating a campaign directory or a provider-call intent. A failed preflight
   has no episode number and cannot look like a started paid call.
4. Distinguish a settled terminal failure from uncertain cost. For a settled
   missing structured object, save the stopped patch, charge, report-invalid
   classification and executable partial grade automatically. Do not replay
   the invocation. Stop on unresolved charge, active writer, protected drift
   or source/manifest mismatch.
5. Use the same `--json-schema` and local 16 KiB exact-field validator for
   both arms. Set `MAX_STRUCTURED_OUTPUT_RETRIES=2` in the pinned actor
   environment to bound repeated report attempts; retain the 8,192-token
   per-request output setting and add an equal 20-turn guard. Q4S S1 uses the
   documented `CLAUDE_CODE_MAX_TURNS=20` environment equivalent because the
   pinned WSL CLI's `--help` omits `--max-turns`. These
   are prospective cost controls, not a claimed fix for Q4R's unknown cause.
   If the canary shows they prevent normal completion, stop and write a new
   frozen design rather than silently changing a live screen.
6. Add fake-stream tests for `success` without structured output, retry-limit
   error, nonzero exit with settled cost, `<synthetic>` plus one real root,
   genuine substitution, malformed stream, expired auth and no-replay after
   provider intent. The host probe must show zero provider calls, stopped
   writers, protected-source integrity and a source-bound attestation.

Exit gate: all focused tests and full harness pass; the WSL provider-free
probe passes; a reviewer can derive every terminal outcome and charge from
the saved evidence without raw model text. Record the stage under
`docs/stage-results/worker-q4s-s1.md`. Do not rebuild the redistributable:
this is evaluation instrumentation only.

## S2: independent corpus, trigger and analysis freeze

Recommended development setting: GPT-5.6 Sol, High. Build **six new
upstream-backed issue families from six repositories** not used in Q3, Q4,
Q4R or the N5/Q5 reserved corpus: four trigger-positive and two
trigger-negative. Prefer different change mechanisms, including API
compatibility, error propagation, asynchronous or stateful behaviour, and
platform-specific behaviour. A family is a repository and issue pair, not a
repeat run. Do not choose or replace a family using model output.

For each family, freeze the upstream repository URL, pre-fix source commit,
fix commit, issue URL or authored regression rationale, compatible licence
and licence bytes, exact actor file inventory, editable paths, public check,
evaluator-only oracle, reference and partial overlays, and task digest.
Confirm that the public issue does not reveal hidden cases. The reference
must pass all oracle cases and the baseline/partial overlays must expose a
nontrivial, reproducible failure. Freeze the six trigger assessments from
public material before any Q4S model call. If four positive and two negative
independent families cannot be sourced with credible oracles, do not shrink
the screen or pay for it; extend the corpus stage instead.

Freeze one immutable manifest binding the corpus, schema, CLI and launcher
hashes, prompt, model registry, actor permissions, grading code, Latin-square task
and arm order, cost/stop rules, and dated spend notice. Do not use an N5/Q5
reserved task, Q4R response or hidden score to adjust the trigger. The
manifest records the user's standing paid-call authorisation and its exact
scope; a changed scope needs a new frozen record. The operator reviews this
nonpaid design decision before S3. Record the stage under
`docs/stage-results/worker-q4s-s2.md`.

## S3: two-call transport canary

Recommended development setting: GPT-5.6 Sol, High. Use one separate,
small synthetic multi-file task excluded from the six-family screen and
reserved corpus. Run one Sonnet-low and one Sonnet-medium fresh head-only
episode, no repair tail. Each has a USD 3 root allocation: **two calls and
USD 6 maximum local allocation**. Project USD 0.5-3 of direct API-equivalent
usage and 15-60 minutes elapsed from the recent Q4/Q4R receipts. Claude Code
subscription invoice impact is unknown. State the dated pricing, token/cache
assumptions and exact manifest before dispatch. The local allocation is not
a guarantee against an in-flight provider overrun.

Both calls must return a terminal, schema-valid report, exactly one real root
model matching the request, a stopped writer, settled cost, protected-source
integrity and a non-empty permitted patch. The canary checks transport and
basic execution only; it cannot qualify medium or tune the six-family
trigger. If either fails, stop with no main-screen calls. Preserve and grade
any paid failure without replay. Record the stage under
`docs/stage-results/worker-q4s-s3.md`.

## S4: balanced public policy screen

Recommended development setting: GPT-5.6 Sol, High. On each of the six
frozen families, run B0 repetition A, B0 repetition B and a Sonnet-medium
arm from pristine source and independent conversations. Rotate all three
labels by a precommitted order derived from task hashes. The three arms use
the same report transport and conditional repair tail. This is **18 episodes,
at most 54 provider calls, USD 4 root allocation each and USD 72 maximum
local allocation**. Including S3, the programme's local admission allocation
is at most USD 78. Project USD 6-30 direct API-equivalent usage and 2-7 hours
elapsed for S4, based on Q4's 16 calls at USD 9.849 and Q4R's three calls at
USD 1.666, with wider allowance for medium effort, cache mix and repair.
Reprice and date the notice before execution. Subscription invoice impact
remains unknown.

Construct the task-sensitive policy counterfactual before seeing outcomes:
use the medium arm on the four positive families and the corresponding B0
repetition on the two negative families. Run medium on the negative families
only as a diagnostic for missed opportunities; count those calls in
experiment spend but not in deployed-policy cost. Compare the policy with
each B0 repetition using family as the independent unit. Report the raw
all-medium arm separately; never select between policies after viewing it.

Keep Q4's conservative guards: zero policy critical errors, no more
unsupported completions or invalid reports than either B0 set, non-negative
hidden acceptance and mean quality-v2 against both, and either an acceptance
gain on at least one family against both or at least ten mean quality points
against both. Policy cost must be no more than 1.5 times mean B0 cost and no
more than USD 1 extra per positive family. Report executable behaviour,
invariants and partial quality even for incomplete or transport-invalid
episodes; a missing report earns no report or diagnosis credit and cannot
become a hidden acceptance. Keep requested effort and observed model
identity separate from unobservable served effort.

After each complete family block, apply only predeclared futility stops. A
positive-family candidate critical error, unresolved charge, protected drift
or invalid identity makes qualification impossible and stops the remaining
calls. A terminal, settled invalid report is a scored failure, not an
uncertain charge and not a free retry. Negative-family diagnostic failure
does not silently relabel the trigger. Preserve every started episode,
including failures. If B0 repetitions disagree on acceptance, critical or
reporting safety, or differ by at least ten quality points, require two
reserved repetitions in any later Q5 design. Record the stage under
`docs/stage-results/worker-q4s-s4.md`.

## S5: decision and downstream boundary

Recommended development setting: GPT-5.6 Sol, High; request a separate
frontier-model review only if an evidence conflict cannot be settled by the
frozen grader. Produce a machine-readable pass/fail decision with source,
receipt, budget, stopped-patch and rubric hashes. Six public families support
only a provisional candidate, not a population-level routing claim. If any
mandatory guard fails, retain B0 and do not tune a replacement candidate on
these six outcomes. If every guard passes, amend M4 entry wording
prospectively, then freeze M4's independent corpus, power, cost and analysis
before Q5. No automatic promotion to the redistributable follows.

## Stage and cost controls

Each stage stops for operator review under the
[execution protocol](REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md). A model or
effort switch, new session or agent launch requires a checked handoff under
`src/LIFECYCLE.md`; a stage boundary alone does not. S1 and S2 are estimated
at 3-6 and 8-16 engineering hours respectively; S5 analysis at 1-3 hours.
The protocol's Sol-High development-session API-equivalent envelopes are
USD 3.25-19.50 for an implementation stage and USD 1.25-6.50 for a small
stage, subject to repricing and token/cache assumptions at handoff. These
development estimates are separate from S3/S4 Claude calls and from Graft
semantic-refresh cost, which is unknown rather than zero. No exact provider
charge is claimed for future work.
