Before you touch the task below, run it through the following sequence.
Keep a ledger as you go, as one JSON object per line in `ledger.jsonl`
in your working directory, and finish with `REPORT.md` there. The task's
own acceptance criteria still apply in full; the sequence is how you get
to them, not a substitute for them.

**1. Intake.** Write the task as given into one `ProblemRecord`:
statement, context, constraints as stated, acceptance criteria as stated.
Record nothing as true yet.

**2. Frame.** Turn every statement in the task into a `PremiseRecord`
with a class: `law` (cannot be otherwise), `maths` (follows from
definitions), `policy` (someone chose it and could choose otherwise),
`habit` (nobody chose it), or `unverified` (stated as fact, not yet
checked). A constraint with a stated reason is `unverified` until the
reason is checked; write the cheapest check that would settle it in
`cheapest_verification`. Then write one `FrameRecord`: the goal in one
rung (what the requester actually needs), what the stated metric or test
measures and misses, the problem's shape with the domain nouns removed,
whether the problem still exists once the premises are classified, the
acceptance criteria you will hold yourself to (the task's own, verbatim,
if it gives them), and B0: the answer a competent single pass would give
taking every stated premise at face value. Write B0 as a
`CandidateRecord` with `technique: "b0"`.

**3. Verify.** For each `unverified` premise whose check is one tool
call and no new code (read a file, run the existing tests, grep, time
the existing script), run it and write a `MeasurementRecord` with the
method, the result with numbers, and the path of the artefact you read
it from. No artefact, no record. A premise whose check you ran becomes a
new `PremiseRecord` with `supersedes` naming the old one and its class
changed to `verified`, or to `policy` or `habit` if the check showed its
stated reason does not hold. Then write a new `FrameRecord` at ledger
version 2. If a stated constraint's reason turned out false, the
constraint is `policy`, not `law`, and you may act against it; say that
you are, and why, in the report.

**4. Generate.** Against the version-2 ledger, apply each of the three
techniques in turn and write a `CandidateRecord` for any that yields
something B0 does not:
- *Subtract.* Which premise, if it were simply not there, would make
  this easy, and what class is it actually? Remove a premise you have
  shown to be policy, habit or false and solve the problem without it.
- *Re-represent.* What is this problem an instance of once the domain
  nouns are removed, and is that instance's answer known? Restate and
  solve the known form.
- *Abduce.* What would have to be true for the observations to be
  unsurprising, and what is the cheapest test that would show it false?
  Add that premise as `unverified` with its test, and solve as if it
  holds.
Each candidate names its technique, its premise operation, its mechanism,
its gain over B0, the premises it introduces, and its cheapest
falsification test. A candidate B0 already covers is not a candidate.

**5. Critique.** For each candidate, including B0, write a
`CritiqueRecord`: ranked failure modes; whether it could have been
deduced from the ledger without the technique (`derivable`); any ledger
premise it shows to be false; and a verdict of `pass`, `return` or
`reject`. Passing is the expected outcome. If a critique falsifies a
premise, go back to step 3 for that premise before continuing.

**6. Select.** Write one `SelectionRecord`: exclude candidates that are
derivable, lose to B0, or were rejected; rank the rest by gain over B0
divided by the cost of their falsification test; name the baseline.

**7. Instantiate.** Take the top candidate (or B0 if the shortlist is
empty) and do the task with it: make the change, run the task's own
checks, write whatever artefact the task requires. Write an
`EvaluationRecord` with the test you ran, the result with numbers, the
artefact path, and whether the task's acceptance criteria are met. If
they are not, the failure becomes a `PremiseRecord` of class `verified`
and you try the next candidate; a refinement is a new candidate with
`refines` set, never an edit of the old one.

**8. Close.** Write a `SolutionRecord` (the answer, the technique that
produced it, the audit trail of record ids) or, if acceptance was not
met, a `GapReport` (unmet criteria, the next cheapest test). Either way,
list every premise the answer depends on that is still `unverified` in
`unverified_load_bearing`, even when the list is empty. Then write
`REPORT.md` with four sections: **Answer**; **B0** (what the face-value
answer was and why the chosen one beats it, or that B0 was chosen);
**Unverified and load-bearing** (the same list, in words); and
**Ledger** (the path to `ledger.jsonl` and the record count).

Record format. Every line of `ledger.jsonl` is one JSON object with at
least `type` (the record name above), `id` (a lower-case prefix, a
hyphen, three or more digits: `prem-001`), `ledger_version` (an integer
from 1), and `references` (the ids this record derives from). Free text
goes in the fields named above and nowhere else; keep each field under
300 characters, statements and mechanisms under 1200. The arbiter of the
format is `tools/validate_records.py` in the orchestrator repository and
the schemas beside it; when in doubt, fewer fields and shorter text
validate more often than more.

Budget. This is quick mode: one rung, one verify pass at one tool call
per premise, three techniques, one critique pass, one instantiation. If
you find yourself designing an experiment, you have left the mode; write
the experiment as the `next_cheapest_test` in a `GapReport` instead.

Then report back what the task asks for, as it asks for it.
