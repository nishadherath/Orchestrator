# Technique briefs

Provenance: **reconstructed**, 2026-09-14, `docs/PLAN.md` task 9.1.
`SYSTEM.md` names "the forty techniques from the previous answer" as the
system's actual intellectual property and says each is a brief with a
trigger question, a premise operation, an output schema and three worked
examples in relational-form language. That answer was not recovered
(D47). This file holds the three tier-1 families `SYSTEM.md` section 5
names (subtract, re-represent, abduce), rebuilt from the premise
operations section 1 assigns to generators (remove, re-represent, add,
replace goal) and from nothing else. The other thirty-seven techniques
and the tier-3 families (analogy, lens rotation, side channel) are named
in `SYSTEM.md` and not reconstructed here; a brief written without its
source would be invention presented as recovery.

Every brief is marked `reconstructed`. If the original is recovered, its
briefs replace these and the marks change to `supplied`.

## How a generator uses a brief

A generator receives the frozen ledger, one brief, and at most three
retrieved patterns. It answers the brief's trigger question against the
ledger, applies the brief's premise operation to produce a candidate, and
emits one `CandidateRecord` per candidate with the brief's family in the
`technique` field. It never sees another generator's output. A candidate
that the Critic can derive from the ledger without the technique is
flagged derivable and loses to B0 by construction; the brief's job is to
produce what the deductive baseline cannot.

Relational form: a problem written as entities, relations and quantities
with the domain nouns removed. "A system S optimises O subject to
constraint C whose stated reason R depends on entity E" is relational
form; "the account index must not change `normalise()` because billing
depends on it" is the instance. The library is indexed by form, never by
domain, so the worked examples below give the form first and the instance
second. The instances are taken from this repository's own record
(`docs/DECISIONS.md`, `test/fixtures/benchmark/`), because those are the
cases whose truth can be checked.

---

## Family 1: Subtract (`reconstructed`)

**Premise operation.** Remove. Take a premise the ledger carries as law
or maths, show it is policy, habit or false, and delete it. The candidate
is whatever the problem becomes without it.

**Trigger question.** Which premise, if it were simply not there, would
make this problem easy, and what class is it actually?

**Procedure.**
1. List every premise of class law or maths in the ledger whose removal
   would shorten the path to the goal.
2. For each, ask what its stated justification depends on, and whether
   that dependency is in the repository, the data or the world where it
   can be checked.
3. Where the justification is checkable, name the check as the
   candidate's cheapest falsification test. Where it is not, the premise
   stays and the candidate is not emitted.
4. Emit the candidate as: premise P reclassified from class X to class Y
   on evidence E; the problem with P removed is Q; Q's solution is S.

**Output schema.** A `CandidateRecord` with `technique: "subtract"`,
`premise_operation: "remove"`, `premises_introduced` empty or naming
only the reclassification, and `falsification_test` naming the check on
the premise's justification, not on the solution.

**Worked examples.**

1. Form: system S must reach objective O under constraint C, stated as
   law. C's stated reason R is that entities E1..En depend on C's exact
   form. Each Ei transforms C's output before use, so C's form is
   invisible to every Ei. R is false; C is policy; remove C; S reaches O
   directly.
   Instance: T10 (`test/fixtures/benchmark/T10`). The frozen file's
   justification named three consumers; each called `.strip()` on the
   result, so the freeze protected nothing. Every sonnet run found this
   and kept the constraint; opus removed it (D42). The technique is the
   removal, and the measurement is that the removal is what the floor
   would not do unprompted.

2. Form: cost of process P is attributed to component A by a prior
   measurement M, stated as fact. M is not in the ledger as an artefact.
   Measuring P shows the cost in component B; the premise "A is the
   bottleneck" is unverified and false; remove it; optimise B.
   Instance: T9. The stated profiling result blamed `EventStore.query()`;
   the cost was a quadratic scan in `_format_rows`. Every floor run
   removed the premise on its own (D42), which is why T9 is not a floor
   failure and T10 is: a false measurement is subtracted readily, a false
   constraint is not.

3. Form: a decision table with rows R1..Rn, each claiming a distinct
   outcome for a distinct input region. Measurement shows the outcome is
   the same across regions R2..Rn. The premise "the regions differ" is
   habit; remove the rows; the table is one row plus its exceptions.
   Instance: Stage 8 (D43, D44, D45). Eleven routing rules measured at
   the floor for every input class but one became two rules.

**When not to use.** When the premise's justification is not checkable at
the mode's verify ceiling. A subtraction with no falsification test is a
guess wearing the technique's name, and the Critic's derivability flag
will not save it because it is not derivable either.

---

## Family 2: Re-represent (`reconstructed`)

**Premise operation.** Re-represent. Keep every premise, change the form
the problem is stated in so that it becomes an instance of a problem with
a known solution, or so that a hidden quantity becomes explicit.

**Trigger question.** What is this problem an instance of, once the
domain nouns are removed, and is the answer to that instance already
known?

**Procedure.**
1. Write the problem in relational form: entities, relations,
   quantities, the objective, the constraints. Strip every domain noun.
2. Ask which known form it matches: a search, a lookup, a fixed point, a
   classification before evidence, a classification after evidence, an
   allocation, a bound.
3. If a match exists, the candidate is the known solution to the matched
   form, translated back. Its cheapest falsification test is the one
   assumption the match rests on.
4. If no match exists, ask whether a quantity the current form treats as
   given is actually a variable, and restate with it explicit. The
   candidate is the restated problem and its solution.

**Output schema.** A `CandidateRecord` with `technique: "re-represent"`,
`premise_operation: "re-represent"`, `mechanism` stating the form before
and the form after, and `premises_introduced` naming the assumption the
match rests on.

**Worked examples.**

1. Form: a decision D is made on inputs X before evidence E is available,
   and D's accuracy on X is poor. E becomes available cheaply after a
   first attempt. Re-represent D as a decision on E after the attempt:
   the classification-before-evidence becomes an escalation-on-signal.
   Instance: D44. Routing T10's shape upfront failed because horizon is
   read after the destination is chosen; the floor worker reports the
   falsified constraint itself, so the decision moves to section 4 of
   `ROUTING.md` as a trigger on that report.

2. Form: per-item work W(i) rebuilds a structure over all n items and
   then uses one entry, so total work is n squared. Re-represent as
   build-once, look-up-n-times: n plus n.
   Instance: T11. `resolve()` built a dict over every record for every
   key; the shape was visible only by running at four sizes and reading
   the curve, and invisible in the diff.

3. Form: a rule set exists as prose read by a model and as nothing else,
   so its totality and consistency cannot be checked. Re-represent the
   rule set as data with a resolver in code; the prose becomes a
   transcription that can be diffed against it.
   Instance: D39, `src/routing_table.json` and `tools/route.py`. The
   ROUTE-TOTAL and ROW-BACKED checks exist only because the table became
   data.

**When not to use.** When the match is by vocabulary rather than by
structure. A problem that shares nouns with a known form but not its
relations produces a candidate that reads well and fails at
instantiation; the Critic's first failure mode to check on a
re-representation is whether the relations actually match.

---

## Family 3: Abduce (`reconstructed`)

**Premise operation.** Add. Given an observation the ledger does not
explain, infer the premise that, if true, would make the observation
expected, and add it as unverified with its cheapest test.

**Trigger question.** What would have to be true for this observation to
be unsurprising, and what is the cheapest thing that would show it false?

**Procedure.**
1. State the observation precisely, with its numbers, and state what the
   ledger currently predicts instead.
2. List candidate premises each of which alone would make the observation
   expected. Prefer premises that also explain something else already in
   the ledger.
3. For each candidate premise, name the cheapest test that would falsify
   it. A premise with no such test is not emitted.
4. Emit one candidate per premise: the premise, what it explains, the
   test, and what the solution becomes if the premise holds.

**Output schema.** A `CandidateRecord` with `technique: "abduce"`,
`premise_operation: "add"`, `premises_introduced` naming exactly the
inferred premise with `class: "unverified"`, and `falsification_test`
naming the test from step 3. The Verifier, not the generator, runs it.

**Worked examples.**

1. Form: process P fails k of n times with message M. The ledger says P
   is deterministic in its inputs. Inferred premise: P has an input the
   ledger does not list, taking one of two values, and M occurs on one
   value. Test: read the k failing records for the value.
   Instance: D41. Two of nine T9 confirmation runs failed with "requires
   approval"; the unlisted input was the interpreter's spelling, `python`
   against an allowlist admitting only `python3`. Reading the full report
   text confirmed it; widening the allowlist removed it.

2. Form: a classification C of fixed inputs changes when only the set of
   available outputs changes. The ledger says C is a function of the
   inputs. Inferred premise: C is computed after the output is chosen,
   not before. Test: hold the inputs and the rubric fixed, change only the
   output set, and count the classifications that move.
   Instance: D44. Horizon reads on unchanged fixtures moved toward
   whichever cell the orchestrator wanted when the table changed.

3. Form: a quantity Q grows badly with scale s in a subset of components
   and not in others. Inferred premise: the affected components share a
   dependency whose cost is superlinear in s, and the unaffected ones do
   not use it. Test: run at several s and compare growth rates per
   component; then find what the fast-growing components import that the
   others do not.
   Instance: T11's `INCIDENT.md`. Catalogue, checkout and search
   quadrupled per doubling; gateway and inventory doubled; the shared
   import was `registry.resolve`.

**When not to use.** When the observation is already explained by a
premise in the ledger and the generator has not read the ledger closely
enough to see it. That candidate is derivable, and the Critic will say
so.

---

## Not reconstructed

Tier 3 (analogy, lens rotation, side channel) and the remaining
techniques of the forty. `SYSTEM.md` section 5 assigns tier 3 to
`fable/xhigh` in deep mode only and says retrieval breadth is its
bottleneck. Quick mode, which is all Stages 10 and 11 build, does not run
tier 3, so nothing in the plan is blocked by their absence. They are
listed here so the gap is visible, not filled.
