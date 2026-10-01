# Q4T prospective report transport repair

Date: 2026-09-26 Australia/Sydney. This is an evaluation-only successor to
Q4S. It does not change the shipping B0 router, Controller, frozen Q4S S4
manifest or sealed S03 receipts.

## Failure and scope

The sealed S4 Sonnet-medium S03 call repaired the source and passed every
protected executable case, but Claude Code ended with
`error_max_structured_output_retries` after 14 turns. The frozen Q4S adapter
correctly recorded no valid report, zero diagnosis/report credit, no hidden
acceptance and its settled USD 0.2309386 charge. The S4 campaign stopped after
the complete family under its frozen invalid-transport rule. The saved stream
has no raw transcript or internal validation errors, so the precise cause of
the two exhausted structured-output attempts is unknown.

Q4T changes two prospective behaviours:

1. [`worker_q4t_structured.py`](../tools/worker_q4t_structured.py) keeps the
   exact six-field schema and local 16 KiB validator, but permits five CLI
   validation attempts and asks for a short final report immediately after
   work. Its transport mode is `claude-code-json-schema-v2`; the bounded
   receipt records result subtype, retry limit, return code, turn count,
   model identity and usage without retaining raw stderr or transcript.
   Missing, malformed or unvalidated reports still fail closed. Five attempts
   can cost more; the existing per-call and per-episode ceilings remain
   necessary. This is a reliability hypothesis, not a demonstrated cure.
2. [`worker_q4t_policy.py`](../tools/worker_q4t_policy.py) lets a *settled*
   terminal report-format failure remain a scored episode. It requires
   validated stopped-writer and charge evidence, model identity, verified
   protected-source integrity, a grade with no hidden acceptance, and a known
   report-failure subtype before continuing. Unknown blocked roots,
   positive-candidate critical errors, inconclusive grades, identity mismatch,
   source drift, accounting differences and allocation overrun still stop.
   A new campaign driver must validate hashes
   and bind this policy in its manifest before dispatch; Q4S never silently
   changes stop rules.

The isolated Q4T launcher and adapter are in
[`worker_wsl_namespace_q4t.sh`](../tools/worker_wsl_namespace_q4t.sh) and
[`worker_wsl_q4t_adapter.py`](../tools/worker_wsl_q4t_adapter.py). They keep
Q3 actor isolation, Claude.ai subscription auth, pinned model cells and
exact schema argv. The [installer](../tools/worker_wsl_q4t_install.sh) writes
new runtime paths and leaves the attested Q4S launcher and schema intact.
The zero-provider [boundary probe](../tools/worker_wsl_q4t_probe.py) checks
three cells, edits, source binding, retry environment and report parsing.
The [auth probe](../tools/worker_wsl_q4t_auth_probe.py) diagnoses an early
login/launcher failure before trying to collect an actor that never started.

## Rules for the next screen

- Freeze a new, non-replayed public corpus and exact Q4T source/runtime hashes
  before any paid dispatch. Do not append to or reinterpret S4. The S03
  family is development evidence; its three paid arms cannot be replayed.
- Bind the new driver, transport mode, five-retry setting, stop policy,
  corpus, quality rubric, model cells and dated spend notice in a new
  manifest and approval. The driver must copy `q4t_diagnostics` into its
  bounded attempt record and set `protected_integrity=True` only after
  verifying source hashes. It must call `settled_stop_reason` only after
  receipt, ledger, snapshot and grade digests have been checked. It must pass
  `candidate_positive=True` only for the predeclared positive candidate arm.
- Preserve and score every stopped patch once, including a failed report.
  A report failure earns zero report/diagnosis credit and cannot become hidden
  acceptance. Do not add a free retry or synthesize a worker report from
  evaluator results. Compare quality and cost within each frozen family.
- Keep the completed C1 canary as transport evidence only. Its one
  Sonnet-medium call returned a valid bound report and passed the isolated
  public check at USD 0.0881134 API-equivalent usage. A single small-task
  success cannot prove the intermittent failure is eliminated. The candidate
  policy remains unqualified until a prospective, balanced screen passes its
  frozen guards.

The [C1 result](stage-results/worker-q4t-c1-2026-09-26.md) records the one
paid canary and its limits. The remaining empirical risk is whether the
five-attempt compact report reduces invalid-report frequency on longer tasks
at acceptable cost. Existing S4 quality and routing conclusions stay as
recorded in [the S4 result](stage-results/worker-q4s-s4.md).

## S2 design freeze after C1

The [Q4T S2 manifest](../test/results/2026-09-26-worker-q4t-s2-manifest.json)
selects the five upstream Q4S families that had no S4 provider invocation
(S01, S02, S04, S05 and S06), plus one new, explicitly synthetic, positive
cross-module atomicity family T07. This gives four trigger-positive and two
trigger-negative families. T07's baseline, partial and reference overlays
score 0, 40 and 100 on evaluator-only cases. The prior S4 S03 campaign remains
sealed and is excluded. This is six independent task/issue pairs but only five
upstream repositories; the synthetic family must be shown separately in
analysis and cannot support a six-repository external-validity claim.

The S2 parent manifest freezes task/grade hashes, trigger assessments,
three-arm rotations, model cells, report transport, corrected stop policy and
the [dated screen cost notice](stage-results/worker-q4t-s2-spend-notice-2026-09-26.md).
The correction is material: `quality_v2` marks a transport-invalid report
inconclusive, so the policy now recognises a proved, settled blocked report
failure before applying the general inconclusive stop. Other missing or
inconclusive reports still stop. A regression test reproduces the former
contradiction.

S2 is provider-free. The next stage must implement and source-bind the paid
driver, independently verify the historical S4 and C1 seals and live Q4T
runtime, test receipt/ledger/snapshot/grade validation with forged evidence,
then run the full offline harness. It must stop for review before live dispatch
under the staged execution protocol. The paid screen itself is a later stage;
neither S2 nor C1 qualifies a routing change.

## S3 prospective screen outcome

The [S3 result](stage-results/worker-q4t-s3-2026-09-26.md) records the
completed, non-replayed screen under child manifest
`6b5b5d92bab2360494dfc9c7501f4dd7044baec81ec07dc1742f73a46ba263d6`.
All 18 episodes settled with 22 valid structured reports and USD 3.621417509
in provider-reported API-equivalent cost. This provides prospective transport
evidence on the six frozen families, but does not establish that the earlier
intermittent S03 report failure is eliminated. Claude Code reported actual
Sonnet/Opus model identities; the requested low/medium/high efforts were bound
in launcher arguments, while served effort was not separately observable.

The predeclared policy decision is **retain B0**. Medium effort did not improve
any of the four trigger-positive families. The trigger-negative S05 family did
show a large diagnostic medium-effort gain and hidden acceptance, so the
current task trigger missed a useful escalation. The all-medium diagnostic
portfolio is not a validated replacement policy. B0 remains the shipping
default; the next evaluation must address trigger sensitivity, unnecessary
escalation cost and baseline variability before any new candidate is frozen.
