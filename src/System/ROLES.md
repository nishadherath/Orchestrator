# Role briefs

Provenance: written 2026-09-14 for `docs/PLAN.md` task 9.4 from
`SYSTEM.md` sections 1, 2, 4, 5 and 6 and from `STEPS.md`. Not
reconstructed: `SYSTEM.md` defines the roles directly. What this file adds
is the contract each role runs under, in the form the Controller (Stage
10) enforces.

Six model roles. The Controller and the Scribe are code
(`tools/system_controller.py`, Stage 10), not briefs. A role earns its
separation only by needing a different context, a different objective or
a different cost tier (`SYSTEM.md`'s first commitment); each brief below
says which of the three it has.

## Rules that bind every role

1. **Records in, records out.** A role receives its input slice as
   records and returns records that validate against
   `schemas/`. It never receives a transcript and never writes one.
   Free text lives only in the schema's capped fields.
2. **Single writer.** A role writes only the record types its brief
   names. It never edits a record another role wrote, or one it wrote
   earlier; a correction is a new record whose `references` (or
   `supersedes`, `refines`) names the old one. The Controller alone
   changes nothing either: status is derived from the records.
3. **Cite the ledger version.** Every record carries the `ledger_version`
   it was written against. The Scribe rejects a candidate against a stale
   version before any model sees it.
4. **No artefact, no measurement.** A `MeasurementRecord` or
   `EvaluationRecord` without a non-empty `artefact` does not validate
   and is not written. A role that could not take the measurement says so
   in the digest, not in an invented number.
5. **Say what is unverified.** Any role whose output rests on an
   unverified premise names it. The Librarian's close record carries the
   list in every mode, empty or not.
6. **Select by `subagent_type` only.** The cell per role is
   configuration below, spawned by name; never pass a `model` parameter
   (`CLAUDE.md` invariant 2). The fleet's cells are not chosen through
   `ROUTING.md`'s table; that table routes single-worker delegation, and
   the cells below are each role's own prior.

## Cells per role, quick mode

`SYSTEM.md` section 5's quick-mode column, transcribed. **These are
priors, not measurements.** Stage 11 measures the fleet against B0 with
these cells; nothing here has been confirmed at the reporting bar, and
Stage 7's result that the floor clears ten of eleven tasks is evidence the
priors are high, not low. Several of these cells are escalation-only in
`ROUTING.md`; that is a statement about delegation routing, not about
role configuration.

| Role | Cell (quick) | Deep, for reference | Section 5's reason |
| --- | --- | --- | --- |
| Controller calls | `worker-sonnet-low` | `worker-sonnet-low` | Classification, not reasoning |
| Framer | `worker-opus-high` | `worker-fable-xhigh` | Highest value per token; a wrong ledger wastes everything after it |
| Verifier | `worker-sonnet-medium` | `worker-sonnet-high` | Many cheap tool calls; correctness comes from artefacts |
| Generator, tier 1 | `worker-sonnet-high`, three instances | `worker-opus-high`, five | Structured techniques run well from a good brief |
| Critic | `worker-opus-medium` | `worker-opus-high` | Never below the generator's class, or it rubber-stamps |
| Selector | `worker-sonnet-medium` | `worker-opus-medium` | Scoring against explicit criteria |
| Librarian | `worker-sonnet-medium` | `worker-sonnet-high` | Abstraction to relational form is compression |

Two rules from section 5 that the Controller enforces as configuration
checks: the Critic's class is never below the Generators' class, and
Generators cap at `xhigh`.

---

## Framer

Separation: cost tier (the most expensive cell in quick mode) and
objective (it is the only role allowed to change what the problem is).

**Input slice.** The `ProblemRecord`; the false-premise catalogue from the
library, read first; on re-entry, every `MeasurementRecord` and every
`CritiqueRecord` with a falsified-premise claim since the last freeze,
plus the current `PremiseRecords` and `FrameRecord`.

**Output.** `PremiseRecords` (one per premise, each classified law, maths,
policy, habit, unverified or verified, with source, confidence, cheapest
verification and load-bearing flag), one `FrameRecord` (goal ladder,
metric interrogation, problem type, dissolution verdict, acceptance
criteria, B0's id, premise count, stability), and exactly one
`CandidateRecord` with `technique: "b0"`. The B0 candidate is the one
exception to generators owning `CandidateRecords`, and the schema says
so.

**Contract.** Every statement in the problem becomes a premise with a
class; nothing is carried as true because it was stated. A constraint
with a stated reason is `unverified` until the reason is checked, and its
cheapest verification names the check. Acceptance criteria are fixed at
the first freeze and not revised after candidates exist. At most 40
premises; merge above that. On re-entry, a premise that changed class is
a new `PremiseRecord` with `supersedes` set, never an edit. If the
premises as classified leave no problem, the dissolution verdict says so
and the run ends with a reframe.

**Fails silently when.** It carries a policy as a law, or an unverified
claim as verified. Nothing downstream recovers from that.

## Verifier

Separation: context (it receives one measurement task, not the problem)
and objective (it touches reality; every other role reasons).

**Input slice.** One `PremiseRecord` to measure and its
`cheapest_verification`, or one shortlisted `CandidateRecord` and its
`falsification_test`, plus the `ProblemRecord`'s context. Not the goal
ladder, not the other candidates, not the critiques. In quick mode only
premises whose verification is one tool call and no code.

**Output.** `MeasurementRecords` in Verify; `EvaluationRecords` in
Instantiate (deep mode only). Each with method, result with numbers, and
a non-empty artefact path.

**Contract.** Run the check; write down what it showed and where the
evidence is. If the check cannot be run at the mode's ceiling, write
nothing and say so in the return. Never extend the task to the problem
itself: a Verifier that starts solving is a generator with no brief and
no isolation. The outcome field is `supports`, `falsifies` or
`inconclusive`; `inconclusive` with an artefact is a valid result.

**Fails silently when.** It reports a number it did not measure. Rule 4
exists for this role.

## Generator (template; the technique family is the parameter)

Separation: context (isolation from every other generator is the whole
point; `SYSTEM.md` section 2, the Diehl and Stroebe argument).

**Input slice.** The frozen ledger (`PremiseRecords` and `FrameRecord`
at version n, including B0), one brief from `TECHNIQUES.md`, and at most
three retrieved structural patterns from the library. Never another
generator's output, never a critique, never a transcript, never the
technique name of any other generator running.

**Output.** `CandidateRecords`, each with `technique` set to the brief's
family, `ledger_version: n`, the premise operation, the mechanism in
relational form where possible, the claimed gain against B0, the premises
it introduces, its cheapest falsification test and a cost estimate. Zero
candidates is a valid output when the trigger question has no answer in
this ledger; an invented candidate is not.

**Contract.** Answer the brief's trigger question against the ledger and
apply its premise operation; do not apply another family's operation
because it seems more promising. State the gain against B0 in terms the
Selector can score. Name the falsification test; a candidate without one
is rejected at the schema.

**Fails silently when.** It produces B0 in different words. The Critic's
derivability flag catches this after the fact; the brief's trigger
question is meant to prevent it.

## Critic

Separation: objective (adversarial) and context (blind to the
generators).

**Input slice.** The frozen ledger and the `CandidateRecords` of the
tier. Not the generators' reasoning, not which generator wrote which
candidate, not the Selector's scores.

**Output.** One `CritiqueRecord` per candidate: ranked failure modes,
the derivability flag, falsified-premise claims with the reason, and a
verdict.

**Contract.** Passing is the expected outcome; `return` only for a
material defect, and the return rate is tracked and the brief
recalibrated if it exceeds roughly 40 per cent. The derivability flag is
the first question: could this candidate have been deduced from the
ledger without the technique? If yes, it is B0 in disguise, whatever it
reads like. A claim that a ledger premise is false goes in
`falsified_premise_claims` with its reason and re-enters Frame; it is not
buried in a failure mode. Never propose a fix; a critique that becomes a
candidate has left its role.

**Fails silently when.** It rubber-stamps because it is a weaker class
than what it reviews, which is why its class is never below the
generators'.

## Selector

Separation: cost tier only. It is the role most nearly a section of the
Controller, and `SYSTEM.md` rates it 5 of 10.

**Input slice.** The `CandidateRecords`, their `CritiqueRecords`, the
`FrameRecord`'s acceptance criteria, and the current baseline (B0's id
until something beats it).

**Output.** One `SelectionRecord`: the shortlist ranked by claimed gain
divided by falsification cost, with the basis stated per entry, and the
excluded candidates with a reason from the enumeration.

**Contract.** Exclude before ranking: derivable, loses to B0, rejected by
the Critic, or stale ledger. An exotic candidate that loses to B0 is
excluded however clever it reads. Score against the acceptance criteria
as fixed, not against what the candidates make seem desirable. An empty
shortlist is a valid output and means the run returns the baseline.

## Librarian

Separation: context (it alone reads the whole blackboard) and lifetime
(it alone writes across runs).

**Input slice.** Everything in the run's blackboard, at Close.

**Output.** A `SolutionRecord` or a `GapReport`, and the library
write-back: the structural pattern in relational form indexed by form and
never by domain; the technique's outcome for this problem type (the
training signal; log it from the first run); any premise that turned out
false, for the catalogue the Framer reads first; any candidate shape that
failed and why.

**Contract.** The non-negotiable list, `unverified_load_bearing`, is
present in every close record in every mode. The library receives
relational forms, never verbatim solutions, and a future generator
receives at most three of them; that cap is what keeps the library from
becoming a conformity channel. Reasoning traces, transcripts and
generator scratch are not retained.

---

## What is deliberately not a role

From `SYSTEM.md` section 1, so nobody adds them back: Instantiator (the
Verifier), Judge (the Selector), Reframer (the Framer re-entered), Human
liaison (the Controller's gate points), Baseline solver (the Framer's B0).
