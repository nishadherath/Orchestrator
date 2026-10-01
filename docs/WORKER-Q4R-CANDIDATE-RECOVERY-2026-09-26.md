# Q4R candidate recovery before the Q5 reserved comparison

Date: 2026-09-26 Australia/Sydney. Status: **R0 complete; R1/R2 stopped
early with no qualifying candidate**. The [R1 stage
record](stage-results/worker-q4r-r1-2026-09-26.md) contains the manifest,
cost, stopped-patch grade and reconciliation evidence. The candidate had a
critical error on its first triggered family, so the remaining paid episodes
were not run.
This is a new prospective public experiment. It does not change the frozen
Q4 M3 result, reinterpret malformed reports, qualify a routing policy, or
open the Q5 reserved frame.

## Why this step is necessary

Q4 M3 ended with no provisional candidate. Its stronger code arm, Opus-high,
cost 3.16 times the mean B0 arm and exceeded the frozen 1.5 times screen guard.
Sonnet-xhigh failed quality and safety guards. Fifteen of sixteen final reports
also violated the strict JSON contract, so the current evidence cannot tell us
whether a cheaper intermediate cell would improve full-task acceptance under a
reliable report transport. Q5 requires a candidate and an immutable reserved
manifest; neither exists. Building the reserved corpus now would breach the
Q4 entry rule and spend curation time without a policy to compare.

The new testable hypotheses are narrower:

1. Claude Code's `--json-schema` may provide a valid final report after an
   agentic coding workflow. The installed WSL CLI is version 2.1.273 and lists
   the flag. Official [CLI documentation](https://code.claude.com/docs/en/cli-reference)
   describes schema-validated print output; [headless documentation](https://code.claude.com/docs/en/headless)
   places it in `structured_output`. We have not yet verified that this
   combination works in this restricted actor with stream JSON.
2. Sonnet-high may improve executable and full-task outcomes over Sonnet-low
   at a tolerable total cost. The old three-microtask N5 screen observed 2/3
   accepted at Sonnet-high versus 1/3 at Sonnet-low, but the later Q4 public
   tasks and report contract are materially different. That result justifies
   a bounded test, not a performance claim.

## R0: provider-free transport boundary, complete

`tools/worker_q4r_structured.py` adds an evaluation-only schema flag and reads
only a successful result event's `structured_output`. It never rescues JSON
from prose in `result`. It binds a canonical encoding of that object to the
invocation, prompt, task, requested cell, stream and final source revision.
The receipt explicitly says the bytes were canonicalised; it does not claim
they are verbatim model bytes. The existing quality-v2 parser still checks the
16 KiB cap, item counts, text lengths and exact fields. A successful CLI result
without structured output is transport-invalid and makes the comparison
inconclusive; a present but locally invalid report remains malformed. Both
retain the settled provider charge.

`tools/worker_wsl_namespace_q4r.sh` admits only the exact schema, Sonnet-low,
Sonnet-high and Opus-high, and the existing USD 6 per-call ceiling. It is
installed beside the historical Q4 launcher. `tools/worker_wsl_q4r_adapter.py`
keeps actor isolation, protected-file checks, writer-stop collection and the
common task executor. The ordinary production adapter and frozen Q4 M3 files
were not changed.

The source-bound WSL attestation is
`test/results/2026-09-26-worker-q4r-wsl-host.json`, evidence digest
`e8620d631cce912039a4bc2146fbcdbcbabcfcabbeac05935e2928bffb744ecf`.
Its 12 provider-free checks passed, including three exact requested cells,
stopped writers, two collected edits, protected source, schema provenance,
revision binding and zero provider calls. The focused structured tests passed
5/5; boundary tests passed 3/3. This verifies admission and fake transport,
not live schema compatibility or model quality.

## R1: freeze a small public comparison before any paid call

Use only the four already calibrated public families P04, P05, P06 and P08.
Revalidate upstream source, issue, oracle isolation, calibration and stable
graders without a provider call. Before seeing new responses, record for each
task whether the Q4 public-feature trigger applies, with exact issue/source
citations and the mechanism. IDs, family tags, hidden rubrics, references and
model outcomes may not influence that assessment. Bind those decisions in the
manifest. If fewer than two independent families trigger, abstain from a
qualification claim and reconsider the public corpus before paying for a
candidate screen.

Run a balanced twelve-episode schedule: B0 repetition A, B0 repetition B and
Sonnet-high on each of the four families. Each episode starts from pristine
source and a fresh conversation. All arms use the schema transport, the same
prompt, public feedback, root USD 6 allocation and conditional repair tail
`[Sonnet-low, Opus-high]`. Only the first cell differs. Predeclare order by
task hash and rotate the three labels; store the exact schedule in the
manifest. No response from Q4 M3 can be substituted for a new B0 episode.

The hard local allocation is **USD 72 for twelve episodes with at most 36
task calls**. The first Sonnet-high episode supplies live identity evidence;
no extra probe is scheduled. An in-flight provider overrun remains possible
and must be reconciled. Based on Q4 M3 receipts, plan for roughly USD 4-25 of
API-equivalent usage and 1-4 hours elapsed, with substantial uncertainty from
schema retries and Sonnet-high task length. Subscription invoice impact is
unknown. The dated notice must refresh current prices and distinguish these
three numbers. Do not split the campaign to evade a spend limit.

Freeze a manifest with hashes for the schema, launcher and installed schema,
adapter, executor, scorer, rubric, public source, actor files, trigger
assessments, schedule, cost cap, analysis, and the host attestation. The live
runner must validate an exact approval bound to that manifest and notice,
record a durable intent before each invocation, refuse replay after any
possible provider start, and stop on uncertain cost, identity substitution,
transport-invalid output, protected drift or stale hashes. The first task
episode serves as the live schema compatibility check; a failure is an
observed outcome and is not retried as a free probe.

## R2: screen and decision

Grade only stopped patches and bound reports. Report executable behaviour,
invariants, diagnosis, report validity, hidden acceptance, unsupported
completion, critical errors, all-attempt cost, cache usage and wall time by
family and arm. Compare the prospective task-sensitive policy against each
B0 repetition: use Sonnet-high only where a prebound public trigger is true,
otherwise use the corresponding B0 outcome. Keep the raw all-high arm visible
as diagnostic evidence. Treat family as the independent unit; repetitions do
not create eight independent families.

Keep Q4 M3's conservative exploratory guards: zero candidate critical errors,
no more unsupported completions than either B0 set, non-negative acceptance
and quality against each set, plus acceptance gain on at least one task in both
comparisons or at least ten mean quality points in both. Total candidate
policy cost must be at most 1.5 times mean B0 total and at most USD 1 extra per
triggered task. All guards are mandatory. If any fails, retain B0 and stop;
do not tune triggers or relax the economic rule against these responses.

A passing result is only a provisional public candidate. Before any reserved
work, amend the M4 entry wording prospectively to accept this separately
qualified Q4R candidate, then complete M4's independent corpus, policy,
power, cost and analysis freeze. Q5 still needs a new exact manifest, dated
spend notice and operator approval. The Q0 protected thresholds and Q6
independent adjudication remain unchanged.

## Checkpoints and ownership

Use GPT-5.6 Sol with High reasoning for R1 and R2 implementation and campaign
management. R1 is estimated at 3-6 engineering hours; R2 at 1-2 hours of
analysis plus 1-4 hours elapsed live. Stop after R1 for manifest review. Do
not launch R2 until the exact approval is recorded. If R2 fails, report the
negative result and do not enter M4 or Q5. A model or effort change requires a
checked handoff under `src/LIFECYCLE.md`; a stage boundary alone does not.
