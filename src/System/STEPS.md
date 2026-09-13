# The eight steps

Provenance: **reconstructed**, 2026-09-14, `docs/PLAN.md` task 9.1.
`SYSTEM.md` refers to "the eight-step sequence from the previous answer";
that answer was not recovered (D47). The steps below are rebuilt from
`SYSTEM.md` section 4's phase table, section 3's control loop, and section
8's mode dials, and from nothing else. Where this file states something
`SYSTEM.md` does not, it says so. If the original is recovered, it replaces
this file and the header changes to `supplied`.

Each step is owned by one role, consumes an input slice, produces one
record type, and has an exit condition the Controller can test without a
model call. Steps do not talk to each other; they read and write records
(`SYSTEM.md` section 6). The record types are defined in `schemas/`.

## 1. Intake (Controller)

Input: the problem as given, any context, constraints, budget, mode, and
acceptance criteria if the requester supplied them.
Output: one `ProblemRecord`.
Exit: the record validates. Nothing else; the Controller does not judge.
Premise operation: none. Everything in the statement is recorded as
stated, not as true. Classifying it is the Framer's job.

## 2. Frame (Framer)

Input: the `ProblemRecord`, the false-premise catalogue from the library
(read first), and on re-entry the `MeasurementRecords` and `CritiqueRecords`
since the last freeze.
Output: ledger version n: `PremiseRecords` (every premise classified law,
maths, policy, habit or unverified, with source, confidence and cheapest
verification), the goal ladder (one rung in quick mode, three in deep),
the metric interrogation, the problem type, the dissolution verdict, the
acceptance criteria (proposed if absent, then fixed), and B0.
Exit: the ledger validates, has at most 40 premises (merge above that),
and every unverified premise names its cheapest verification.
Premise operations: remove, replace goal.
Reconstruction note: B0 is produced here, not by a separate role, per
section 1's "Baseline solver (Framer output B0)". B0 is what a competent
single pass would do with the premises as classified: the deductive
answer, no technique applied. It is the bar every candidate is scored
against and the answer returned when nothing beats it.

## 3. Verify (Verifier)

Input: the unverified premises whose cheapest verification costs at or
under the mode's verify ceiling (quick: one tool call, no code; deep: full
experiments), each as a measurement task, not the whole problem.
Output: `MeasurementRecords`, one per premise measured, each with method,
result and an artefact link. No artefact, no record.
Exit: every premise under the ceiling has a record, or the verify budget
is spent.
Premise operation: add true premises.
Loop: Frame and Verify alternate until the ledger is stable (no premise
changed class this pass) or the budget is spent. If the Framer's
dissolution verdict becomes "dissolved" during the loop, the run returns
a reframe report and stops: the problem no longer exists as stated.
Reconstruction note: `SYSTEM.md` section 3 puts the stability test in the
Controller as one of its two model calls. In quick mode this file makes it
deterministic instead: stable means the set of (premise id, class) pairs
is unchanged from the previous freeze. That loses nothing at one rung and
one verify pass, and removes a model call.

## 4. Generate (Generators, N isolated)

Input: the frozen ledger at version n, one technique brief
(`TECHNIQUES.md`), and at most three retrieved structural patterns from
the library. Never another generator's output, never a transcript.
Output: `CandidateRecords`, each citing ledger version n, the technique,
the premise operation applied, the mechanism, the claimed gain against
B0, the premises it introduces, its cheapest falsification test, and a
cost estimate.
Exit: every generator in the tier has returned or timed out. A candidate
citing a ledger version other than n is rejected by the Scribe before any
model sees it.
Premise operations: remove, re-represent, add, replace goal, one per
technique family.

## 5. Critique (Critic, blind)

Input: the frozen ledger and the `CandidateRecords`. Not the generators'
reasoning, not the generators' identities.
Output: one `CritiqueRecord` per candidate: ranked failure modes, the
derivability flag (could this have been deduced from the ledger without
the technique?), any falsified-premise claims, and a verdict.
Exit: every candidate has a critique. If any critique falsifies a ledger
premise, the Controller re-enters Frame with the critique and restarts
the tier; that is the only backward edge in the sequence.
Premise operation: search.
Calibration: passing is the expected outcome. The return rate is tracked
and the Critic recalibrated if it exceeds roughly 40 per cent.

## 6. Select (Selector)

Input: the candidates, their critiques, the acceptance criteria, and the
current best (B0 until something beats it).
Output: one `SelectionRecord`: the shortlist with scores, ranked by
claimed gain divided by falsification cost, with derivable candidates
and candidates that lose to B0 excluded whatever they read like.
Exit: the shortlist is non-empty, or it is empty and the record says so.
Premise operation: search.

## 7. Instantiate (Verifier)

Input: one shortlisted candidate at a time, cheapest falsification test
first.
Output: an `EvaluationRecord`: the smallest concrete instance, the test
run, the result, the artefact.
Exit per candidate: the test ran. If it meets the acceptance criteria the
run returns that candidate with its audit trail. If it fails, the failure
becomes a verified negative premise in the ledger and the next candidate
is tried; refinement, when the mode allows it, is a new candidate that
references the failure record, never an edit in place.
Quick mode does not run this step: falsification is on paper only, and
the stop rule is the first candidate that survives critique with no
unverified load-bearing premise, else B0.
Premise operation: add true premises.

## 8. Close (Librarian)

Input: everything in the run-scoped blackboard.
Output: a `SolutionRecord` (the answer, its audit trail, which technique
produced it) or a `GapReport` (unmet criteria, unverified load-bearing
premises, the next cheapest test); plus the library write-back: the
structural pattern in relational form, the technique's outcome for this
problem type, any premise that turned out false, any candidate shape
that failed and why.
Exit: the record validates and the write-back is committed.
Non-negotiable in every mode: the output names which premises are
unverified and load-bearing.
Premise operation: add, cross-run.

## Termination

Acceptance met; problem dissolved; budget spent; or two consecutive tiers
without improvement over the current best. Hard cap of three reframes.
Convergence is structural: every loop adds verified premises and never
removes them, so the untested candidate space only shrinks.
