# Decision ledger

Append-only. One entry per decision, newest last. An entry records what was
decided, why, and what would reverse it. Do not edit earlier entries; add a
superseding entry instead.

## 2026-09-05 D1. Adopt the CLAUDE.md layout on disk

Decision: move the deliverables under `src/`, add `docs/`, `test/`, `tools/`
and `dist/`, and rename the consumer install guide from `README.md` (briefly
`PERSONA.md`) to `src/README.md`.

Why: `CLAUDE.md` described this layout while the tree was flat, so every path
in the charter was wrong. Moving `.claude/agents/` out of the repository root
also stops the fifteen workers loading into development sessions, which the
charter forbids outside the dogfooding protocol.

Reversal: none expected. `tools/` is an addition to the charter layout because
the generator and the bundle builder are neither deliverables nor tests.

## 2026-09-05 D2. Generated persona files stay at the root, without their generator

Decision: `ENGINEERING_PERSONA.*.md` and `ENGINEERING_PERSONA_LANGUAGES/` remain
at the repository root as copied-in generated artefacts. Their source
(`source/core.source.md`, `source/languages.source.md`) and builder
(`build_persona.py`) live in another repository and are not vendored here.

Why: the persona documents locate themselves at the root and the loading matrix
in section 3.2 depends on that. Vendoring the generator would duplicate a
build that has one owner elsewhere.

Guard: `test/harness/persona.sha256` records a hash of each file with carriage
returns stripped. The harness fails if a hash changes, so a hand edit of a
generated file is caught. To update: rebuild from source, copy in, run
`python3 test/harness/check.py --update-persona-manifest`, commit both.

Reversal: vendor the generator if the persona starts changing in step with this
repository.

## 2026-09-05 D3. Worker definitions are generated with the persona inlined

Decision: `src/agents/*.md` are produced by `tools/generate_workers.py` from
`src/WORKER_PERSONA.md` and the routing table in `src/ROUTING.md`. The shared
persona is inlined into each definition. A cell's `model-specific-*` section is
inlined only when non-empty. Each description states the cell, the assessments
that route to it (or that none do), and the instruction never to pass `model`.

Why: the hand-written definitions told each worker to read `WORKER_PERSONA.md`
by bare relative name, which fails when the definitions are installed globally,
and cost a tool call at startup to load an empty section. Descriptions are the
one field the orchestrator sees in the Agent tool listing without reading the
rubric; identical descriptions carried no information. Deriving the routed
assessments from the table keeps one source of truth.

Kept: all fifteen cells, because CLAUDE.md fixes the count. Six are not in the
routing table and their descriptions say so. Dropping them is a charter change.

Reversal: if the empirical checklist shows a worker benefits from knowing its
cell, fill the sections in; no generator change is needed.

## 2026-09-05 D4. dist/ is committed and built only on a green harness

Decision: `tools/build_dist.py` runs `test/harness/check.py` and refuses to
build on any FAIL. The bundle is committed, stamped in
`.claude/ORCHESTRATOR_VERSION` with the date and the source commit it was
built from, and `-dirty` if the tree was not clean. The bundle carries
`ORCHESTRATOR.md` (ROUTING.md and LIFECYCLE.md concatenated) rather than the two
files separately, so a consumer installs one file beside `CLAUDE.md`.

Why: the charter says nothing ships from `dist/` until the harness passes and
that dogfooding must name the bundle version. A build step that can be
bypassed would make both unenforceable.

Reversal: split `ORCHESTRATOR.md` back into two files if a consumer needs to
adopt routing without lifecycle management.

## 2026-09-05 D5. Haiku is permanently excluded from the worker matrix

Decision: haiku is not, and will not become, a worker cell. Invariant 5 in
CLAUDE.md stands as a decision, not a carry-over pending review.

Why: Jeb's call, made after E8 (`docs/FINDINGS.md`) disproved the invariant's
original justification (a defined `effort: high` haiku worker showed "Haiku 4.5
(high)" on its `/tasks` row, so haiku does honour effort). The justification
was wrong; the exclusion stands anyway. This forgoes the cell most likely to
undercut `worker-sonnet-low` on cost for mechanical, short, contained work, a
trade-off recorded here rather than left implicit.

Reversal: none. Reopening this needs a new decision entry, not an edit to this
one.

## 2026-09-05 D6. The calibration instruction assumes referenced artefacts exist

Decision: score_routing.py's VERDICT_INSTRUCTION now tells the orchestrator
under test to assume every artefact a fixture task refers to exists, even
though orchestrator-scratch (the consumer project used for calibration, see
D8) has none of them: no ticket for F01, no pull request for F09, no gateway
logs for F11, no theme.css for F15, and more generally no existing codebase
for the fixtures that assume one (docs/duration.md and duration.spec.ts in
F04, RateLimiter's doc comment in F05, src/legacy/ in F07, and others).

Why: without the instruction, an orchestrator that checks its inputs before
spawning is correct to answer action: clarify on any of these, which is
indistinguishable in score_routing.py's output from an orchestrator that
cannot judge the task. The fixtures test routing judgement, not whether the
orchestrator notices a scratch project is empty; the instruction removes the
second effect so the score measures the first.

Impact: the results in test/results/2026-09-05-routing-sonnet.md and
test/results/2026-09-05-routing-opus.md (empirical-checklist.md item E12) were
recorded before this sentence existed and are not comparable with any run made
after it. Re-run E12 before drawing further conclusions from routing scores.

Reversal: seed orchestrator-scratch with the actual artefacts instead, and drop
the sentence, if a future stage wants the orchestrator scored on noticing
missing context as well as on axis judgement.

## 2026-09-05 D7. Clarify is a first-class routing outcome

Decision: `action: clarify` stands alongside `action: spawn` as a legitimate
orchestrator response, not a failure to route. `test/harness/score_routing.py`
already scores it and fixture F16 already expects it; `src/ROUTING.md` itself
states no rule for when clarify is the correct answer.

Why: Jeb's call, made after E12 showed a sonnet orchestrator and an opus
orchestrator disagreeing sharply on how often to clarify (3 of 17 verdicts
against 9 of 17, `docs/FINDINGS.md`) with no rule in `ROUTING.md` to referee
the disagreement. Leaving clarify unruled treats every clarify verdict as
unscoreable uncertainty instead of a defined choice.

Deferred: the rule itself, when clarify is correct as distinct from a
low-confidence spawn, is judgement work scoped for a later stage of the
improvement plan. This entry records only that clarify is in scope, not what
the rule says.

Reversal: drop clarify from `score_routing.py` and retire fixture F16 if a
future review decides the orchestrator should always spawn and let the worker
report underspecification instead (`ROUTING.md` section 4 already covers that
path).

## 2026-09-05 D8. orchestrator-scratch is the consumer project

Decision: `orchestrator-scratch` is the consumer project for fixture
calibration (`score_routing.py`), any cost or quality benchmark built later,
and dogfooding (`test/harness/empirical-checklist.md` item E13's protocol). It
is not this repository; `CLAUDE.md`'s Dogfooding section already forbids
running from here.

Why: Jeb's call. The project already has the `dist/` bundle installed and
carries the E1 to E13 empirical history and the two dogfood runs recorded in
`test/results/2026-09-05-dogfood.md`, so it continues existing work rather than
starting fresh in one of the six unconnected sibling directories (Book,
Provenance, TealElephant, Tsunami, WikiSkills, Wuxing).

Reversal: name a different project here if orchestrator-scratch's synthetic,
no-other-codebase nature becomes a problem for a specific measurement; D6
already works around this for fixture calibration.

## 2026-09-05 D9. The routing table names all eighteen triples; one documented tie-break

Decision: `src/ROUTING.md`'s table is total over the three axes it defines.
Five combinations that previously had no row now do: mechanical-short-
consequential (`worker-sonnet-medium`, closing the exact gap fixture F17 had
already worked around), mechanical-long-contained and mechanical-long-
consequential (one new row, "Mechanical, long horizon", at `worker-sonnet-high`,
mirroring structured's own long-horizon row in not splitting by blast),
structured-short-consequential (widened into the existing medium-consequential
row, now `worker-sonnet-high` for short or medium), and open-short-
consequential (widened into the existing medium-or-long-consequential row, now
any horizon, `worker-opus-xhigh`). The one remaining double match, open-long-
consequential (`worker-opus-xhigh` and `worker-fable-xhigh`), is not closed by
picking a winner; it is documented as a tie-break in the table's constraints:
prefer `worker-opus-xhigh`, and reach for `worker-fable-xhigh` only when the
task itself demands sustained, self-directed investigation, not merely because
it is long and consequential. Fixture F12 (open, long, consequential, no such
demand, confirmed `worker-opus-xhigh`) is cited as the worked example.
`test/harness/check.py`'s new ROUTE-TOTAL check enforces both: zero gaps, and
any remaining double match must name both workers in a tie-break sentence
still present in the file, or the check fails.

Why: Jeb asked for the fix and the check together so the tree is never red
between them (2026-09-05 conversation). Every new row uses a rule already
established and confirmed elsewhere rather than a fresh judgement call: the
mechanical-short-consequential fill is fixture F17's own rationale, made into
a table row instead of a worked-around gap; the mechanical-long row mirrors
structured's existing blast-agnostic long-horizon row, one model-effort step
below it; the two widened rows extend an adjacent row's horizon range rather
than inventing a new cell; the open-long-consequential tie-break's default
(`worker-opus-xhigh`) is fixture F12's own confirmed answer, not a new one.

Verified: ROUTE-TOTAL added to `test/harness/check.py`, passes (18 triples, 0
gaps, 1 documented tie-break). Checked it actually catches regressions, not
just the current state: removing the tie-break sentence and deleting the new
mechanical-long row each independently produced the expected FAIL, both
reverted before this commit. `tools/generate_workers.py` regenerated the three
affected worker definitions (`sonnet-medium`, `sonnet-high`, `opus-xhigh`) with
0 drift after. Fixture F17's rationale and note updated to describe a closed
gap rather than an open one; its `assessment`, `expected_cell` and
`assigned_by` are unchanged, so it did not need re-review.

Reversal: remove a row and its ROUTE_TOTAL_ALLOWED_CONFLICTS entry together;
the check will immediately say which triple lost coverage.

## 2026-09-05 D10. The clarify rule: ask only for what the repository cannot answer

Decision: `src/ROUTING.md` section 1.1 defines when the orchestrator asks the
user instead of routing. Spawn is the default. Clarify is correct only when
either the objective is not discoverable (no acceptance criteria exist and none
could be derived from the repository, so a worker would invent the definition of
done rather than find it) or the task is both irreversible and materially
ambiguous (it deletes, migrates, publishes or spends, and what the user wants is
genuinely unclear). Everything else routes, with the reading stated in the line
that names the worker. The section also names five reasons that are not grounds
to ask (urgency or seniority; irreversible but clear; an artefact the
orchestrator cannot see; wanting more context to feel confident; an unspecified
method), and requires a clarify to name the decision, give the options, and say
which one it would take absent an answer.

Why this shape rather than a confidence threshold: the two costs are asymmetric
and the asymmetry runs against asking. A worker started on a slightly wrong
reading costs tokens, and its persona already requires it to report back rather
than guess when acceptance criteria are absent, with `ROUTING.md` section 4
defining the recovery. A question to the user spends attention, which is the
scarcer resource and often unavailable in this system's normal mode of use, and
spends it at the worst moment: before anyone has read the code. A cheap worker's
question is grounded in what it found; the orchestrator's is not. That argument
is what selects "discoverability" as the test rather than "confidence": the
things a worker can find are not grounds to ask, and the things it cannot find
(the user's intent, the user's acceptance of an irreversible risk) are.

Validation: applied by hand to all seventeen calibration fixtures, the rule
reproduces every confirmed answer, including the three designed to punish
over-caution (F08 blast radius, F15 urgency, F17 irreversible but fully
specified), and it selects clarify only for F16. Applied to the E12 opus run,
it contradicts all nine of that run's clarify verdicts, five of which
(F01, F09, F11, F15, F17) had axis assessments matching the human fixture
exactly, meaning the model assessed correctly and asked anyway. This is a hand
check of the rule's logic against the fixture set, not a measured run; no live
run has been made under this rule.

Known gap: no fixture exercises the second condition. Every current fixture
either fails it or is covered by the first. F17 is its near miss, irreversible
but completely specified, and is therefore a spawn. A fixture for irreversible
plus genuinely ambiguous belongs in the fixture expansion Jeb has deferred; it
is not added here because an unreviewed row would flip the whole corpus's
human-reviewed flag to "no" in every future `score_routing.py` report.

Guard: `test/harness/check.py`'s CLARIFY check asserts the section and both
condition names are still present, and that at least one fixture sets
`expected_action: clarify`. Verified it fails when a condition is reworded away.

Reversal: D7 already records the alternative, which is to drop clarify from
`score_routing.py`, retire F16, and let workers report underspecification
through section 4 alone. That remains available; this rule narrows clarify
enough that the difference between the two is now small.

## 2026-09-05 D11. Erratum to D10: the E12 clarify counts

Correction: D10 says the clarify rule "contradicts all nine of that run's
clarify verdicts". The opus run recorded ten clarify verdicts, not nine
(F01, F04, F05, F07, F08, F09, F11, F15, F16, F17), and the sonnet run
recorded four, not three (F10, F13, F16, F17). Nine and three are the counts
with F16 excluded, where clarify is the confirmed answer and the rule agrees
with the model. D10's substance is unchanged: the rule contradicts nine of the
ten opus clarify verdicts and endorses the tenth.

Why this is an entry rather than an edit: this ledger's header forbids editing
earlier entries. The same miscount was also in `docs/FINDINGS.md`, which carries
no such rule and was corrected in place in the same commit.

How it happened: the count was taken from the "Chosen" column of the recorded
results tables, which renders a correct clarify as `[clarify]`, rather than from
the raw verdict strings. `grep -c "action: clarify"` on the two files in
`test/results/` gives ten and four.

## 2026-09-06 D12. Mechanical long-horizon work is temporarily uncovered, for a measurement

Decision: the row `| Mechanical, long horizon | worker-sonnet-high |`, added by
D9, is removed. The two triples it covered, mechanical-long-contained and
mechanical-long-consequential, are deliberately uncovered while a single
experiment runs. `ROUTE-TOTAL` gains an allow-list of documented gaps, keyed by
triple, each requiring a substring of this entry to still be present in this
ledger, so removing the argument re-fails the check.

Why: measured on 2026-09-06, that row cost more accuracy than the gap it
filled. Two fixtures answered correctly before it existed are answered
incorrectly after, reaching it from opposite directions: F03 bends its horizon
from medium to long, F07 bends its sensitivity from structured to mechanical.
Sonnet does this in 6 of 6 opportunities, opus in 3 of 6. F08 is a control,
assessed identically in 8 of 8 observations across both bundles and both
models. On the axis that flipped in each fixture, correct in 4 of 4
observations before the row and 3 of 12 after, Fisher exact one-sided
p = 0.0192. Full diagnosis in
`test/results/2026-09-06-attractor-diagnosis.md`.

The experiment this enables: remove the row, change nothing else, run sonnet
three times. Predictions were recorded in the diagnosis before the run. If F03
and F07 recover, adding a row can cost more than the gap it fills, and D9's
premise that coverage is worth having for its own sake is wrong. If they stay
wrong, the ambiguity was always in the axis definitions rather than the table,
and the row is exonerated and should be restored.

Why the argument lives here and not in `ROUTING.md`: that file ships to the
orchestrator on every turn, and naming the uncovered combination there would
put the very words whose effect is being measured back into the prompt. The
gap is therefore invisible to the orchestrator and documented only to whoever
edits this repository. That is a deliberate trade against the bundle being
self-describing, and it holds only while this experiment is open.

The bundle built from this state is experimental and should not be used for
real work: an orchestrator meeting a mechanical, long-horizon task has no row
and no guidance for it, which is exactly the pre-D9 condition being
re-measured.

Reversal: restore the row and delete both allow-list entries if the experiment
exonerates it, or record the replacement design if it does not. Either outcome
closes this entry; it is not intended to stand.

## 2026-09-06 D13. Rows must be fixture-backed; coverage is not a goal

Decision: a row in the routing table must be backed by a fixture whose confirmed
answer lands on it. `test/harness/check.py` asserts this as ROW-BACKED. Totality
over the eighteen triples is no longer a goal, and the mechanical long-horizon
gap opened by D12 becomes permanent until a fixture justifies filling it. This
supersedes D9's premise that covering every combination is worth having for its
own sake, and closes D12, which was written as a temporary state pending the
experiment that has now run.

Why: the experiment settled it. Removing D9's `Mechanical, long horizon` row and
changing nothing else recovered both fixtures it had broken, 3 of 3 each, and
lifted sonnet from 32/51 to 39/51. The control fixture stayed identically wrong
in 11 of 11 observations across three bundles. So a row is not a passive
destination that only matters when selected; its presence changes how tasks are
classified. A row with nothing behind it can therefore cost accuracy on tasks it
wrongly attracts, which is what D9's row did.

Retrospective check on the rule: of the nine classifying rows in the table
today, all nine are fixture-backed. The one row this rule would have rejected is
exactly the one that regressed. Reinstating it makes ROW-BACKED fail by name,
verified before this entry was written. The rule would have prevented D9's
regression.

Known and unmeasured: three covered triples have no fixture at all,
(mechanical, medium, consequential), (open, short, consequential) and
(structured, short, consequential). The last two were introduced by D9's
widening of two rows. They are reported by ROW-BACKED rather than failed,
because removing them is itself an untested change and adding fixtures needs
Jeb. They are the blind spots: by the mechanism proven above they could be
attracting real tasks, and no fixture would show it. Settle them during fixture
expansion, by adding backing or removing the widening, not by argument.

Also unresolved: F12 fell from 2 of 3 to 0 of 3 in the same experiment, twice
being read as structured rather than open, which may be a weaker pull toward
`Structured, long horizon` now that it is the only bare long-horizon row. Three
runs cannot separate that from noise, and F12 was already unstable in the
previous bundle. It is cheap to settle with more runs and should not be patched
on this evidence.

Reversal: restore the row and delete both ROUTE_TOTAL_ALLOWED_GAPS entries if a
fixture ever lands on mechanical long-horizon work. The fixture comes first; the
row follows it, not the other way round.

## 2026-09-06 D14. The benchmark is specified, staged behind a pilot, and graded only by exit codes

Decision: `docs/BENCHMARK-DESIGN.md` specifies the cost and quality benchmark.
Three commitments in it are decisions rather than details.

**Deterministic grading only.** Every task must have a grader that is a command
with an exit code. A model grading a model is circular when model capability is
the thing under test. Open-ended work is made gradable by planting a known
defect and matching on the location the worker reports, which converts a
judgement into a string comparison. A task whose quality cannot be reduced to
an exit code does not enter the benchmark, however representative it feels.

**A staircase, not a grid.** The question is where each task's cheapest
sufficient cell sits, so the protocol searches up the cost ladder and stops,
rather than filling a nine-by-six grid. Steering up the ladder uses a permissive
threshold (2 of 3) and claiming a frontier uses a strict one (8 runs, Wilson
lower bound above 0.7, and the cell below must fail the same bar). A report
never cites the steering threshold as evidence.

**A pilot before the benchmark.** Two tasks, full ladder, five runs each, no
confirmation phase, roughly 30 to 50 runs. Its purpose is to measure the
parameters the design guesses at, not to answer the question: tokens and wall
clock per run per cell, whether the planted-defect grader survives real worker
phrasing, and whether the repository reset between runs is reliable. Size the
full benchmark from those numbers. This project has twice been corrected by
cheap measurements that contradicted confident reasoning, most recently on
2026-09-06 when a predicted improvement turned out to be nothing at all.

Why this matters beyond cost: it is what makes the fixtures defensible. A
fixture's `expected_cell` is currently Jeb's judgement, and D13 requires every
routing row to be backed by such a fixture, so the table rests on opinion. A
measured frontier per task class lets expected cells be derived from evidence
and turns ROW-BACKED into a check that every row is grounded.

Recorded limits, so they are not discovered later: blast radius cannot be
measured this way, because it describes what a wrong answer costs the owner and
cannot change a grader's exit code, so any rule depending on it rests on
judgement. The benchmark also says nothing about whether the orchestrator picks
the frontier cell, which stays the fixtures' job, nor about quality above the
pass mark, since a grader is a boolean.

Reversal: if the pilot shows the planted-defect grader is unreliable, the open
row of the task set needs a different instrument, and the benchmark covers only
mechanical and structured work until it has one.

## 2026-09-06 D15. R_confirm corrected from 8 to 9: the original could not clear its own bar

Decision: `docs/BENCHMARK-DESIGN.md`'s confirmation sample size, R_confirm, is
corrected from 8 to 9, and `test/harness/benchmark.py`'s `--r-confirm` default
changes with it.

Why: D14's "Sample size, honestly" section asserted "eight successes out of
eight gives [67.6%, 100%], which clears the reporting bar." That is
arithmetically wrong: 67.6% does not exceed the stated 0.7 bar. Checked
directly against `wilson_interval()`: a perfect 8 of 8 record gives a lower
bound of 0.6756, which cannot clear ">0.7", not as a rounding artefact but by
the actual value. Nine is the smallest sample size where a perfect record
clears it: `wilson_interval(9, 9)` gives 0.7008, and the intended contrast
survives at the new size too (`wilson_interval(8, 9)`, one miss out of nine,
gives 0.5650, well short of the bar).

Found while smoke-testing an unrelated feature (the checkpoint/resume
mechanism added the same day), not by reviewing the arithmetic on its own: a
disposable smoke fixture happened to produce a perfect confirmation record,
which the harness then reported as "Frontier confirmed: no" despite the
record being flawless. That is the shape of defect this project's testing
discipline exists to catch before it costs real runs, and it did, though not
by the route anyone would have planned: had the six-task benchmark been run
against the old default first, every task's confirmation phase would have
reported "no" regardless of how well it actually performed, and the mistake
would have read as a finding about the tasks rather than an arithmetic error
in the harness.

What changes: `docs/BENCHMARK-DESIGN.md`'s "Sample size, honestly" section,
and its "Cost and wall clock" section's run counts and cost figures (12, not
11, runs for a task that clears at the ladder's floor; 27, not 25, runs for a
long-horizon task assumed to climb three rungs; the total estimate moves from
about USD 27 to 95 to about USD 30 to 103). `test/results/2026-09-06-
benchmark-full-preregistration.md` is corrected to match, since no run had
yet been made against it; the correction predates any measurement it would
otherwise have to account for.

Reversal: none anticipated. This is an arithmetic correction, not a
judgement call open to being weighed differently later.

## 2026-09-07 D16. T4 fixture defect: its own docstring tripped its grader; the real run's T4 result is invalidated

Decision: `store.py`'s pristine docstring in the T4 fixture is corrected to
remove its own "KVStore" self-reference. T4's result in the real six-task
benchmark run (`test/results/2026-09-07-benchmark-04d2acc.md`) does not
measure task difficulty and must be disregarded; T4 needs a fresh run
against the corrected fixture.

Why: that run's T4 confirmation phase reported "Frontier confirmed: no"
(worker-sonnet-xhigh 3/9, worker-sonnet-high 0/9) after search climbed
cleanly to the row ROUTING.md predicts. All 25 of T4's failing runs, across
every tested cell from worker-sonnet-low through worker-sonnet-xhigh, cited
the identical grader message, "FAIL: KVStore still appears 1 time(s), the
port is incomplete", and every one of those 25 also reported the full
functional test suite passing ("Ran 19 tests... OK"). The pristine
`store.py`'s own module docstring read "...this old interface (KVStore) is
being ported to a new one across every caller", planting a literal
"KVStore" mention that grade.sh's strict recursive grep counts alongside
genuine leftover code, by design going beyond "supplied tests pass" (see
grade.sh's own header comment). Workers uniformly and correctly identified
the mention as historical prose describing the task, not a leftover
reference, and left it exactly as task.md gave them no reason to touch a
comment describing the port rather than code participating in it. This is
the same defect class as `test_new_interface.py`'s docstring, which named
the same class in its own prose and was caught and rewritten before T4 was
first committed (`cf91c34`); this instance shipped because the reference
port built to verify the fixture used a hand-written docstring from the
start and never exercised the pristine one's wording.

What changes: `store.py`'s docstring now describes the old interface
without naming it, matching the treatment already given to
`test_new_interface.py`. All three fixture states (pristine fails, a
complete port passes, a partial port fails) reverified unchanged after the
edit.

Reversal: none anticipated. This is a fixture-authoring defect, not a
judgement call open to being weighed differently later.

## 2026-09-07 D17. T6 fixture: a docstring hinted at its own bug, ahead of the trace it was meant to require

Decision: `cart.py`'s docstring in the T6 fixture is corrected to use
consistent case, removing an inadvertent hint at the planted defect.

Why: the real six-task run found T3, T5, and T6 all clearing several rungs
below their assigned or fixture-backed rows, T6 by the widest margin (six
rungs below `worker-fable-xhigh`, the row F13 backs). Auditing all three for
a quieter version of T4's self-reference defect (D16) found nothing in T3
or T5, but T6's `cart.py` read "...region is a two-letter code such as
\"ca\" or \"NY\".\"\"\"", mixing case right next to a bug that is exactly a
missing case normalization in `tax.py`'s `RATES` lookup. That is not a
grading defect: grade.sh only checks the worker's relayed report, so
nothing here could produce a false pass or fail. It is a fixture-design
issue: a worker could notice the mismatched case before running the
reproduce command or tracing past `cart.py`, which is a shortcut past the
three-file trace this fixture, and by extension F13's row, is meant to
require.

What changes: the docstring now reads "CA" or "NY" consistently. All three
fixture states (no report fails, a correct diagnosis passes, a plausible
wrong diagnosis fails) reverified unchanged. T6's confirmed result in the
real run is not thereby invalidated the way T4's was, since the grading
itself was never wrong, but it should be re-measured against the corrected
fixture before the six-rung gap is read as a clean finding about F13's row
rather than partly an artefact of this hint.

Reversal: none anticipated for the fix itself. Whether the six-rung gap
survives re-measurement is an open question this decision does not settle.

## 2026-09-07 D18. Mechanical long-horizon work now has a fixture, and it confirms the gap should stay open

Decision: none to ROUTING.md itself. This closes the "known and unmeasured"
item D13 flagged for the mechanical-long-horizon gap: it is now measured,
and the measurement supports leaving the gap as is.

Why: T2, built for the full six-task benchmark, is exactly the fixture D13
said this gap lacked, a mechanical rename repeated across thirty files.
Confirmed at `worker-sonnet-low`, 9 of 9, twice, in both the original run
and its replication after D16/D17's fixture fixes (unrelated to T2, which
was never touched by either). Sheer volume does not move this task off the
cheapest cell on the ladder, which is the outcome D13's own reasoning
predicted: the axis that makes mechanical work long-horizon (repetition
count) is not the axis that makes work harder (judgement, ambiguity,
consequence).

What changes: nothing in ROUTING.md or `check.py`. D13's reversal condition
("if a fixture ever lands on mechanical long-horizon work") does not fire
here, since landing means a fixture forcing a row above the floor, and T2
does the opposite. Recorded so the blind spot D13 named is marked settled
rather than still open.

Reversal: unchanged from D13's own terms. A future fixture landing above
`worker-sonnet-low` on this triple would reopen the question; T2 alone
does not.

## 2026-09-07 D19. ROUTING.md: two rows lowered to worker-sonnet-low on double-confirmed benchmark evidence

Decision: two of ROUTING.md's rows are split by horizon and lowered for
their short-horizon half, on the strength of the full six-task benchmark
and its clean replication:

- `Structured, short or medium, contained` (`worker-sonnet-medium`) becomes
  `Structured, short, contained` (`worker-sonnet-low`) and `Structured,
  medium, contained` (`worker-sonnet-medium`, unchanged).
- `Open, short or medium, contained` (`worker-opus-high`) becomes `Open,
  short, contained` (`worker-sonnet-low`) and `Open, medium, contained`
  (`worker-opus-high`, unchanged).

`test/fixtures/routing.jsonl`'s F04 and F09, the routing-classification
fixtures for these exact triples, have their `expected_cell` updated to
match (`worker-sonnet-low` for both), since `score_routing.py` scores an
orchestrator's table-reading against these fields and a stale expectation
would mark a correct reading of the new table as wrong.

Why: T3 (structured, short, contained) and T5 (open, short, contained), the
benchmark's fixtures for these exact triples, each confirmed
`worker-sonnet-low` at the 95% Wilson reporting bar in two independent full
runs, with zero failing runs across 24 confirmations each (T5 also cleared
the pilot's search phase at the same cell before the full protocol
existed, a third data point). Both rows previously bundled short and medium
horizon together on one cell; only the short-horizon instance has capability
evidence behind it (F04 and F09 are both short-horizon), so the medium half
of each row is left exactly as it was rather than extended past what was
measured. `docs/BENCHMARK-DESIGN.md` and `test/results/2026-09-06-
benchmark-full-preregistration.md` (original run and replication) carry the
measurements this decision rests on.

What does not change here: the `worker-fable-xhigh` row for `Open, long
horizon, sustained autonomous investigation`. T6, that row's benchmark
fixture, also confirmed `worker-sonnet-low` twice, a six-rung gap below F13,
the row's own backing fixture. That result is real and not yet acted on:
F13's actual task ("p99 latency doubled across four services... no single
obvious cause... traces, profiles and the repositories") describes
substantially more scope than T6's three-file, single-repo trace, and
whether T6 is a fair proxy for what F13's row is meant to cover is an open
question raised back to Jeb rather than settled by this entry.

Also not done here: re-running `score_routing.py` against the new table, to
check the orchestrator still reads it correctly. That is the table-
compliance question this benchmark does not measure (it measures worker
capability, not orchestrator classification); worth doing before treating
this change as fully verified end to end.

Reversal: a future fixture landing above `worker-sonnet-low` on either
short-horizon triple would reopen this; none is expected on the current
evidence, which is now two independent full runs plus, for T5, a third
pilot data point.

## 2026-09-07 D20. First observed forwarder hallucination: T7's confirmation is inconclusive, not a capability result

Decision: T7's first confirmation attempt (8 of 9, Wilson lower bound
56.5%, does not clear 0.7) does not settle T7's frontier. One of the nine
runs is a forwarder failure, not a worker result, and should be treated as
void rather than as evidence against `worker-sonnet-low`.

Why: that run's raw checkpoint record shows `num_turns: 1`, `duration_ms:
6010` (six seconds), and no tool use at all. Its entire "report" is the
forwarder inventing, in its first and only turn, a fictional prior
exchange: a "misrouted worker" spawned as `worker-opus-high`, an
"automated background-task event" reporting that worker's completion, and
a claim of already having flagged this and being unable to proceed without
a decision. None of this happened. `run_cell()` invokes `claude -p` with
no `--resume` or `--continue` flag (confirmed by reading
`test/harness/benchmark.py` directly), so there is no mechanism by which
state from an earlier run could leak into this one, and the prompt
template (`BENCHMARK_INSTRUCTION`) contains nothing resembling background
tasks or worker mismatches. The forwarder fabricated the entire scenario
from a clean context and never attempted to spawn the worker it was asked
to spawn.

This is a new failure shape, not one of the three the pre-registrations
anticipated (a refusal, an unparseable reply, a spawned worker that is not
the one asked for). Across the six-task benchmark's 162 runs (90 original,
72 replication) plus T7's 12, this is the first occurrence: 1 in 174,
about 0.6%, still consistent with the "under 1 in 20" prediction but no
longer "zero", and the first time the specific shape (a confabulated
narrative rather than a plain refusal or mis-spawn) has been seen.

What changes: nothing in the harness or the fixture. T7's confirmation
needs a fresh attempt before its frontier is known; a single anomalous run
this rare does not by itself indicate anything about T7's actual
difficulty, and repeating it costs one more run of the same task.

Reversal: if this recurs at a rate meaningfully above the observed 1 in
174 baseline, or recurs specifically on T7 rather than spread across
tasks, it stops being a rare flake and becomes something to investigate on
its own, per the harness-level-errors reasoning already in the full
pre-registration.

## 2026-09-07 D21. The `worker-fable-xhigh` row is split: the contained case moves to `worker-sonnet-low`, and its own backing fixture is replaced

Decision: `ROUTING.md`'s single row for `Open, long horizon, sustained
autonomous investigation` (worded with no blast term, so it matched both
`contained` and `consequential` by the parser's own rule that an absent
axis means "any value") is split into two rows. `Open, long horizon,
contained` now routes to `worker-sonnet-low`. `Open, long horizon,
consequential, sustained autonomous investigation` keeps
`worker-fable-xhigh`, unchanged.

Why: T6, run twice, and T7 (a harder, more faithful fixture built for this
exact purpose after D19 flagged T6 as a possibly weak proxy), both
confirmed `worker-sonnet-low` for this shape of task, with zero failures
across 27 of 27 confirmation runs (T6 original 9 of 9, T6 replication 9 of
9, T7 second attempt 9 of 9; T7's first attempt was voided by D20's
forwarder hallucination, not counted here). F13, the routing fixture
behind the old row, describes a multi-service p99-latency investigation
whose output is a ranked cause list, a report. Its own `note` field says
so: "Contained because the output is a report." F13's `expected_cell`
changes from `worker-fable-xhigh` to `worker-sonnet-low` to match.

What the fixture check caught: once the row's blast term is made
explicit, `check_row_backed` (D13) fails on the narrowed
`worker-fable-xhigh` row, because F13 was its only backing fixture and F13
was never really an instance of the case that row's own text describes
(consequential, and demanding sustained investigation that reshapes its
own plan). F13 backed the old row only through the wildcard reading of an
absent blast term, a parsing technicality, not because anyone had judged
it a fit. Making blast explicit was the correct fix (it is what lets the
`contained` half route honestly to `worker-sonnet-low`), and it happens to
also remove a fixture that was propping the row up on a mismatch. The two
are the same change; the gap was latent before this entry, not created by
it.

`test/fixtures/routing.jsonl` gains F18 to close that gap: a
multi-tenant billing pipeline double-charging customers after a
retry-logic change, where the diagnosis has to adapt as each hypothesis is
ruled out and the finding itself drives an irreversible-in-practice
refund decision over real money, not merely a written report. Unlike F12
(open, long, consequential, but a fixed contract once the cause is found,
confirmed `worker-opus-xhigh`), F18 demands the self-directed,
plan-reshaping investigation the row's own constraint text requires.
Drafted by Claude and reviewed and confirmed by Jeb, 2026-09-07, the same
standing every other fixture in this file carries.

Also in this entry: `worker-sonnet-low`'s three separate `short, contained`
rows (`Mechanical`, `Structured`, `Open`) are merged into one row,
`Mechanical, structured or open, short, contained`, using the same
`... or ...` convention the table already uses on other axes (for example
`Structured, short or medium, consequential`). This is a mechanical
consolidation forced by `tools/generate_workers.py`'s
`MAX_DESCRIPTION_CHARS` limit: adding the new `Open, long horizon,
contained` row pushed `worker-sonnet-low`'s generated description past
200 characters. The three merged rows cover exactly the same three
triples as before, at the same worker, so `ROUTE-TOTAL`'s coverage is
unchanged; `ROW-BACKED` now needs only one of the three triples backed
rather than all three, which is the same relaxation the table already
accepts elsewhere for `or`-joined rows.

Reversal: a future fixture confirming `worker-fable-xhigh` (or a cell
above it) for the `contained` triple would reopen the first half of this
entry. A future benchmark result or documented failure against F18's
scenario, or Jeb's own reassessment of it, would reopen the second half.

## 2026-09-07 D22. The mechanical long-horizon gap is half closed: `contained` gets a row, `consequential` stays open

Decision: `ROUTING.md` gains `Mechanical or open, long horizon, contained`
routed to `worker-sonnet-low`, merged with the existing `Open, long
horizon, contained` row from D21 for the same reason D21 merged
`worker-sonnet-low`'s short-horizon rows: `tools/generate_workers.py`'s
200-character description cap. `(mechanical, long, consequential)` stays an open gap in
`ROUTE_TOTAL_ALLOWED_GAPS`, now under its own argument rather than
sharing D12's ("D22. Mechanical long-horizon, consequential work remains uncovered"),
pending a fixture of its own the way T2 was for the contained half.

Why: T2, benchmarked specifically for the mechanical-long-contained
triple, confirmed `worker-sonnet-low` at 9 of 9 in both the original run
and its replication, the same standard of evidence D19 and D21 already
acted on for other rows. D13 made this exact gap "permanent until a
fixture justifies filling it"; T2 is that fixture.

The history this has to reckon with: D9 added a `Mechanical, long
horizon` row pointing to `worker-sonnet-high`. D12 removed it after
measurement showed its presence, not its destination worker, pulled two
unrelated fixtures into wrong classifications: F03 (bending its horizon
from medium to long) and F07 (bending its sensitivity from structured to
mechanical), both scored correctly before the row existed and wrongly
after, recovering cleanly once it was removed. `docs/DECISIONS.md` D13
then closed the question by ruling the gap fixture-backed-or-permanent,
which is the standing this entry now acts on. Nothing about T2's
evidence rules out the same attractor recurring with a different
destination worker: the row's mere presence, not what it points to, was
the mechanism D12 measured. This entry does not claim the row is safe,
only that it is now evidenced and narrower in scope than D9's (blast
made explicit, `contained` only, `consequential` still uncovered).

What still has to happen before this counts as settled: a
`score_routing.py` run against this table must show F03 and F07 still
resolving correctly. Jeb reviewed and confirmed this decision to proceed
on that basis, 2026-09-07.

`test/fixtures/routing.jsonl` gains F19, a mechanical rename across
roughly thirty files with the existing test suite defining correctness,
matching T2's shape. Drafted by Claude and reviewed and confirmed by
Jeb, 2026-09-07.

Reversal: if the re-run shows F03 or F07 regressing, remove the row and
restore D12's full two-triple gap rather than narrowing it, since that
would reproduce the exact failure mode D12 measured. If it holds, this
entry stands and `(mechanical, long, consequential)` remains the only
open half, pending its own fixture.
## 2026-09-07 D23. Section 1's axis definitions gain two lines; F13 and F19 were correctly authored all along

Decision: ROUTING.md section 1 gains two clarifying sentences. Blast
radius: "Judge the deliverable itself, not how serious the situation it
concerns sounds: a report on a severe incident is still contained if it
is read and checked before anyone acts on it." Horizon's Long bullet
gains: "Sheer repetition counts too: a mechanical task repeated across
enough files or call sites is long horizon on volume alone, with no
exploration or judgement required." No fixture or table row changes.

Why: D22's re-run, done as two independent opus runs against the
681f8d8 bundle, answered its own question cleanly: F03 and F07 both land
exact both times, no attractor. But the same two runs also repeated a
pattern already visible in the stale ccd6350 run: F13 misjudged blast as
consequential three times running, and F19 misjudged horizon as medium
twice running, in both cases landing one cell above the fixture's own
expected_cell.

Re-examining the two fixtures, rather than the live orchestrator's
verdicts, found both were authored correctly and deliberately. F13's own
note field already states the reasoning: "Contained because the output
is a report; the horizon and openness carry it," a distinction D21 drew
on purpose against F18's explicit downstream-action framing. F19's long
horizon rests on D18's own settled reasoning, "the axis that makes
mechanical work long-horizon (repetition count) is not the axis that
makes work harder," reasoning T2 was built specifically to test. Neither
fixture needed changing.

What the fixtures got right, though, was never written into ROUTING.md
section 1 itself, only argued out in DECISIONS.md and in the fixtures'
own rationale fields, none of which the orchestrator reads when
classifying a live task. That gap, not a fixture defect and not a
recurrence of D12's attractor, is the more likely explanation for three
consistent F13 misses and two consistent F19 misses.

What still has to happen before this counts as settled: a fresh
score_routing.py run against the rebuilt bundle must show F13 and F19
landing on their expected cells, or at least closer to them, without
disturbing F03, F07, or any other fixture currently agreeing. Jeb
reviewed and confirmed this approach before the wording was drafted,
2026-09-07.

Reversal: if the re-run shows no improvement on F13 or F19, or a
regression elsewhere, these two sentences come out and the gap goes back
to being logged as an open, unexplained live-classification pattern
rather than a documentation fix.
## 2026-09-07 D24. D23's horizon sentence reverted: it fixed F19 but broke F03 on its first run

Decision: ROUTING.md section 1's Long-horizon bullet goes back to its
pre-D23 wording. The blast radius sentence D23 added stays; it fixed F13
with no observed side effect. Only the horizon sentence, "Sheer
repetition counts too: a mechanical task repeated across enough files or
call sites is long horizon on volume alone, with no exploration or
judgement required," is withdrawn.

Why: the score_routing.py run against the D23 bundle (70b2eed) landed
exactly where D23 asked it to on the two fixtures it targeted, F13 and
F19 both exact, but F03 misjudged for the first time across four runs
on this bundle lineage, horizon bent from medium to long, the same
failure shape D12 measured and D22's re-run was built to guard against.
F03 moves about forty files with one uniform operation each; F19's
underlying benchmark fixture, T2, renames a function across about
thirty files but has to find and verify every call site per file. The
sentence named only volume, so nothing in it stopped the orchestrator
from reading F03's larger file count as long horizon too, even though
F03 was deliberately authored as medium. Sheer repetition count was
never the real distinguishing factor; D18's own reasoning ("the axis
that makes mechanical work long-horizon... is not the axis that makes
work harder") was correct about T2 specifically, but generalising it
into a volume-only rule in ROUTING.md's own text asked the orchestrator
to apply a threshold that does not actually exist.

D23's own reversal clause named this exact contingency, "a regression
elsewhere," as grounds to withdraw the wording. Jeb chose to act on it
immediately rather than wait for a second run to confirm, and to keep
the blast sentence, which showed no comparable harm.

What still has to happen: a fresh score_routing.py run against a
rebuilt bundle should show F03 back to exact and F19 back to its old
miss (medium instead of long), confirming the reversal undid what it
was meant to and nothing else moved. F19 goes back to being a
documented, open live-classification gap rather than a solved one; a
correct, properly scoped statement of what actually distinguishes F03
from T2's task, if one exists, is future work, not this entry.

Reversal: if the confirming run does not show F03 recovering, or shows
some other unexplained shift, this entry's own account of the cause is
wrong and needs redoing before anything further is attempted.
## 2026-09-07 D25. D24's reversal confirmed: F03 recovered, F19 back to its documented miss, nothing else moved

Decision: none. This closes D24's own "what still has to happen"
clause rather than opening a new question.

Why: the confirming score_routing.py run against the rebuilt bundle
(2f1651a) landed exactly where D24 predicted. F03 is exact again
(mechanical, medium, contained), recovered from the single miss that
triggered the reversal. F19 is back to misjudging horizon as medium
instead of long, the same miss it had before D23, now standing as the
open gap D22 already logged rather than a new problem. F13 stayed
exact on the blast sentence D23 kept. F08, F09, and F11 disagree,
unchanged from every run so far on this fixture set. Agreement reached
15 of 19, the best of any run recorded this session.

What this settles: the blast sentence added in D23 is confirmed
working with no observed cost across two runs now. The horizon
question, why F19's task reads correctly as long horizon by D18's
reasoning but no wording tried so far states that correctly without
also pulling in F03, remains open and unattempted again this session.

Reversal: not applicable; this entry only records a confirmation.
## 2026-09-07 D26. F08's horizon was miscalibrated at authoring, corrected from long to medium

Decision: F08's assessment changes from structured/long/consequential to
structured/medium/consequential, and its expected_cell from
worker-sonnet-xhigh to worker-sonnet-high, an already-covered cell backed
independently by F06. No change to ROUTING.md or any table row.

Why: F08 has been misjudged the exact same way in every recorded run
since 2026-09-05, both orchestrator models, across every table state
this project has had, roughly seventeen observations with zero
exceptions. D12 itself used F08 as a stability control for the
attractor experiment ("assessed identically in 8 of 8 observations
across both bundles and both models") without checking whether that
identical answer was the correct one; it was treated as a baseline, not
a target.

Re-reading F08's task against ROUTING.md's own definitions rather than
against the live verdicts: it ports one payment webhook handler,
following a written migration guide, keeping the log format
byte-identical. That is a single bounded translation, not repeated
work. Compare F07, structured/long/contained, converting thirty
callback-style modules one at a time, correctly and consistently read
as long horizon every run this session, where the repetition genuinely
drives the horizon call. F08 has no repetition to drive it. Its actual
shape matches F06, structured/medium/consequential, a single schema
change other work depends on, which has never once been misclassified.
F08 was authored to test something else entirely, whether the
orchestrator rounds up on blast radius alone (its own note field says
so), and that purpose survives the correction unchanged: worker-sonnet-
high is still the blast-adjusted cell a correct reading lands on,
distinct from over-provisioning to an opus-tier worker.

What changes in check.py's accounting: the triple (structured, long,
consequential) moves from fixture-backed to speculative, since F08 was
its only direct instance. The row itself, Structured, long horizon,
carries no blast qualifier and stays backed through F07's contained
instance; ROW-BACKED still passes.

Reversal: a future fixture built specifically for structured, long,
consequential work, confirmed at worker-sonnet-xhigh, would restock
that triple with real evidence rather than leave it speculative.
## 2026-09-07 D27. D22's row is reverted: F03 and F07 regressed on the identical, unchanged bundle

Decision: the merged row `Mechanical or open, long horizon, contained`
is split back apart. `Open, long horizon, contained` (`worker-sonnet-
low`) is restored to D21's original wording. The mechanical half D22
added is removed outright, and D12's full two-triple gap is restored:
`(mechanical, long, contained)` and `(mechanical, long, consequential)`
both go back into `ROUTE_TOTAL_ALLOWED_GAPS`, both keyed to the reason
"D27. Mechanical long-horizon work is uncovered again after D22's row regressed F03 and F07". F19, the fixture D22
added to back the mechanical half, is removed from
`test/fixtures/routing.jsonl`; there is no longer a row for its triple
to test against, and a fixture asserting a cell for an intentionally
uncovered gap would only read as a permanent, uninformative failure in
every future run.

Why: D22's own reversal clause said plainly what a regression on F03 or
F07 means, remove the row and restore D12's full gap rather than
narrow it. Three more runs came in against the identical, unchanged
bundle (2f1651a) after D24's earlier fix, no code difference between
any of them. F03 and F07 were both exact in one of the three; in the
other two, one or the other regressed, each time bending toward
exactly D12's original signature, F03's horizon from medium to long,
F07's sensitivity from structured to mechanical. Two regressions in
three identical runs is not the occasional flakiness the earlier
"confirmed clean" call (based on two runs before this data existed)
took it for.

Why only the mechanical half comes out, not D21's own open, long,
contained row: the one data point available for D21 alone, before D22
ever merged the mechanical case in, showed F03 and F07 both exact (the
stale ccd6350 run, recorded before this session's D22 reinstall). Every
regression observed happens to bend toward the mechanical reading
specifically, matching D9's original row, which was mechanical-only
and produced this same signature at a similar rate. D22's own reversal
clause is scoped to what D22 itself added; D21 carries its own separate
T6/T7 evidence and is not implicated by this data. One clean
observation is not strong confirmation D21's row is safe on its own,
only that reverting exactly D22's contribution, rather than both
decisions' combined contribution, is the change the evidence actually
points at.

What this leaves open: T2's worker-capability evidence (worker-
sonnet-low, 9 of 9 twice) for a large mechanical rename is still real
and still stands; what is missing is a way to route the orchestrator
there without also making it misread nearby fixtures, the same
unsolved problem D12 originally identified and D18 confirmed measured
rather than solved. `(mechanical, long, contained)` and `(mechanical,
long, consequential)` are both open again, exactly as D12 left them.

Reversal: a future row for this space, built and tested against a
wider batch of runs before being called settled rather than after two,
would reopen this. Jeb chose to act on the reversal clause immediately
rather than gather further data first, 2026-09-07.
## 2026-09-08 D28. F11 corrected and reworded: horizon raised to long, the fable-xhigh test settled explicitly

Decision: F11's horizon changes from medium to long. Its task text
gains a sentence naming why the investigation converges (the gateway's
own logged fields correlate cleanly to one upstream service), so it no
longer stays silent on the fable-xhigh versus opus-xhigh test D21
introduced. `expected_cell` stays `worker-opus-xhigh`, unchanged.
ROUTING.md section 2's tie-break note now cites F11 alongside F12 as a
confirmed no-such-demand instance.

Why the horizon correction: the same evidence class as F08 (D26).
Roughly fourteen of fifteen recorded observations across every model
and every table state since 2026-09-05 read F11 as long horizon, not
the fixture's assigned medium, including runs from before the
fable-xhigh/opus-xhigh split existed, where the misread had no effect
on the chosen cell and so was never visible as a disagreement.

Why the reword, not just the correction: once horizon reads correctly
as long, F11 sits on the exact boundary D21 built for F12 and F18,
and F11's text, authored 2026-09-05, predates that boundary and never
settles which side it falls on. Live runs after the horizon issue
alone would still land on worker-fable-xhigh close to the rate already
observed (4 of 5 recent runs), not because the task demands sustained,
plan-reshaping investigation, but because nothing in its text said it
did not. Rather than retarget the fixture to match that drift, or
leave the ambiguity open, the task gains the same kind of concrete,
narrative detail F18 and F12 already carry, so the fixture tests the
distinction on purpose instead of by accident.

Why this reading rather than the other one: F11 could have been
reworded either way, toward F18's plan-reshaping shape or toward F12's
fixed-contract one. Retargeting to fable-xhigh would have made F11
redundant with F18, both testing the same thing under different
window dressing. Keeping it a fixed-contract case alongside F12 gives
the suite a genuine minimal pair instead: two intermittent,
no-reproduction, ships-on-diagnosis scenarios, identical in shape,
opposite only on the one dimension the tie-break actually turns on.
That is more informative than either fixture alone, and it is why
ROUTING.md section 2 now names both.

Reversal: a future run showing F11, correctly read as long horizon,
still landing on worker-fable-xhigh despite the added correlating-
fields language would mean the reword did not do its job, and either
the wording needs to be stronger or the fixture should be retargeted
after all.
## 2026-09-08 D29. D28's reword overcorrected: it settled the fable-xhigh test but broke sensitivity instead

Decision: F11's task text is reworded a second time. `assessment`,
`expected_cell` and horizon all stay exactly as D28 left them (open,
long, consequential; worker-opus-xhigh); only the task's wording
changes again.

Why: the confirming run requested after D28 landed showed F11 at 0 of
3, and all three raw verdicts were identical: sensitivity read as
structured, horizon as medium, not the assessed open and long at all.
D28's fable-xhigh fix worked exactly as intended wherever the run did
reach the tie-break, but the reword never reached it, because naming
the gateway's specific correlating fields ("upstream target, latency,
and connection state... point cleanly at one upstream service once
correlated") made the whole task read as a known, mechanical
correlation exercise rather than an open judgement call with no clear
reproduction. The fix for one axis broke the axis the fixture depends
on to be tested at all.

The correction keeps D28's structural idea, that the task should say
outright why the investigation converges rather than leave it silent,
but stops naming which fields do the correlating. The new text says
nothing is obvious at a glance and judgement is needed about where to
even look, which is what open sensitivity with no reproduction
actually requires, while still saying the evidence confirms the right
hypothesis cleanly once found, rather than sending the investigation
chasing a different theory, which is what keeps it on the fixed-
contract side of the fable-xhigh boundary rather than F18's plan-
reshaping one. Nothing else about F11 changes: same triple, same
expected_cell, same reason for existing.

What still has to happen: a fresh confirming run is needed to check
this wording lands on open sensitivity and worker-opus-xhigh together,
since no run has yet tested this exact text.

Reversal: a future run showing this wording still misread as
structured or medium, or landing on worker-fable-xhigh after all,
would mean two attempts at reworking F11's text have failed and the
fixture should be retargeted rather than reworded a third time.
## 2026-09-08 D30. T8's grader had a false-negative bug: it required naming the file, not just the function

Decision: `test/fixtures/benchmark/T8/grade.sh` drops its requirement
that the report contain the literal string `api_client.py`. The pass
condition is now: names `create_order` specifically, and names the
duplicate-side-effect risk. Both were already required; only the
filename check is removed.

Why: T8's real run (`2026-09-08-benchmark-af94deb.md`) reported search
2 of 3 and confirmation 7 of 9, below the 0.7 Wilson lower bound.
Reading the three failing reports in full (retrieved from the
consumer project's `.benchmark-checkpoint.jsonl`, no new `claude -p`
calls needed) found each one correctly identifying `create_order` as
the non-idempotent POST wrapped in the same retry policy as the
read-only calls, and each correctly describing the lost-response-after-
success duplicate-order mechanism, in as much or more precision than
the passing reports. All three failed the same grader line, "report
does not name api_client.py", because none of them happened to restate
the filename while discussing the function directly. `create_order` is
defined nowhere else in the fixture, so requiring it already
establishes correct localisation; the filename check added nothing but
a way for a correct answer to fail on phrasing.

The pre-registration for this run (`2026-09-07-T8-preregistration.md`)
had already named this as the more likely grader failure mode ahead of
time ("the reverse risk, a correct diagnosis phrased without any of the
accepted terms, remains the more likely failure mode") but the
construction-time test cases for it happened to phrase the correct
diagnosis with the filename included, so the risk went unverified until
real worker output triggered it.

What changed once corrected: re-grading all twelve stored T8 reports
offline against the fixed script (recorded in
`2026-09-08-benchmark-af94deb-T8-regrade.md`) flips the three false
negatives to passes and nothing else, since the fix only removes a
check. Search becomes 3 of 3, confirmation becomes 9 of 9, Wilson lower
bound 70.1%, clearing the bar. `worker-sonnet-low` is the confirmed
frontier. F09's row (open, short, contained, worker-sonnet-low) is
confirmed at F09's own scale rather than needing escalation, the
question this task was built to settle.

What still has to happen: none. F09's diagnostic closes here alongside
F08 (D26) and F11 (D28, D29).

Reversal: none anticipated for the grader fix itself, the same class of
correction as D16. If a future T8 run at a wider sample shows
`worker-sonnet-low` failing on the actual risk content rather than on
phrasing, that would be new capability evidence, not a reason to
reinstate this check.
## 2026-09-08 D31. F05 reworded: the hidden decision point behind "medium" made explicit

Decision: F05's task text gains a second sentence saying that
simulating the passage of time for the clock-skew and refill cases is
left for the worker to work out. `assessment`, `expected_cell` and
sensitivity are unchanged.

Why: F05 has disagreed with its own assessed medium horizon in roughly
half of every recorded run since 2026-09-05, both orchestrator models,
across every table state this project has had. It never matched F08's
or F11's pattern of unanimous or near-unanimous disagreement, which is
what would point to the assessed axis itself being wrong; the clearest
single data point is two opposite results at the identical commit,
nine hours apart, which rules out a table-wording cause entirely (the
same reasoning D27 used to separate genuine attractor regressions from
noise). Re-reading the task against F04, its nearest neighbour
(structured, short, contained, a single function to a written
contract with tests supplied): F05 gives the worker a doc comment
naming three cases, not a formal contract, and no existing test file
to bound scope, and correctly covering the clock-skew case requires
deciding how to simulate time passing, a genuine decision point the
compact original text left implicit. That fits "some exploration, one
or two decision points" in section 1's own definition of medium, and
distinguishes F05 from F04 on a real basis rather than by degree of
compactness in the task text alone. The live model's frequent short
reading looks like it is missing that decision point because the
original text reads as a flat enumeration of three named cases, not
because medium is the wrong call.

What still has to happen: a fresh confirming run is needed to check
whether stating the decision point explicitly resolves the split, the
same open question D29 left for F11.

Reversal: a future run against this wording still splitting roughly
evenly between short and medium would mean the reword did not supply
the missing signal, and F05 should be treated as a fixture that is
inherently borderline rather than one with a recoverable authoring gap.
## 2026-09-08 D32. F11 accepted as is: correct worker, imprecise horizon, by Jeb's call

Decision: no further change to F11. D29's reword stays as the fixture's
final wording for this round.

Why: the confirming run requested after D29 shows F11 choosing
worker-opus-xhigh in 3 of 3 runs, but horizon reads as medium in all
three, not the long that D28 corrected it to. The correct worker is
reached through ROUTING.md's "open, any horizon, consequential" row,
which does not depend on horizon at all, rather than through the
fable-xhigh versus opus-xhigh distinction section 2 exists to test.
F12, backing the same tie-break, reads long correctly in all three runs
of the identical batch, so the gap is specific to F11's own wording, not
a general problem with the test. The likely cause is a genuine tension
D29 introduced without noticing it: the sentence added to settle the
tie-break, that the investigation "converges cleanly... rather than
sending you chasing a different theory", reads as a quick resolution,
which pulls horizon toward medium even as it correctly keeps sensitivity
open and settles the tie-break itself.

Two reword attempts (D28, D29) have already gone into this fixture, each
fixing one problem while shifting another. Put the finding to Jeb rather
than attempting a third reword unprompted: worker choice, the thing that
actually drives cost, is correct in every recorded run; the horizon
misread does not change routing outcomes for this specific triple, only
the fixture's value as a clean test of the tie-break condition
specifically. Jeb chose to accept the current wording rather than
continue iterating.

What this leaves open: F11 is not, at present, a clean confirmation that
the orchestrator reads long horizon correctly under this task's shape,
only that it reaches the correct worker regardless. F12 remains the
fixture actually confirming correct long-horizon reading for this tie-
break; F11's contribution is narrower than D28 intended, limited to
demonstrating the fable-xhigh versus opus-xhigh choice resolves toward
opus once the task states its own convergence, independent of whether
horizon is read correctly alongside it.

Reversal: a future attempt at rewording, if one is wanted later, should
treat "converges cleanly" and "reads as long" as requirements in
tension for this specific task shape and test drafts against both
before committing, rather than optimising one axis at a time as the
last two rounds did.
## 2026-09-08 D33. F05 reworded again: a concrete obstacle, not just a named decision

Decision: F05's task text gains a specific reason simulating time is
non-trivial, that `RateLimiter` has no clock parameter to begin with, so
a seam has to be found or introduced before the clock-skew case can be
written at all. `assessment`, `expected_cell` and sensitivity are
unchanged from D31.

Why: D31 narrowed F05's split from roughly even across the whole session
to 2 of 3 in the confirming batch, an improvement but not a settled
result; one run still read horizon as short. Re-reading D31's own
wording against what actually earns medium in section 1's definition
("some exploration, one or two decision points"): stating that a
decision exists ("has to be worked out") without saying why it is
non-trivial reads as a small, quickly-resolved step, not exploration.
The gap is not the presence of a decision but its weight. Naming the
concrete obstacle, no clock parameter exists yet, turns "decide how to
simulate time" into "find or build a seam before you can even start
the hardest of the three cases", which is investigation-before-action
rather than a single quick call. This is still a standard, well-known
testing technique (dependency injection or monkeypatching for time), so
structured sensitivity is unaffected for the same reason D31 gave: the
expected behaviour per case remains fully specified by the doc comment,
only the mechanics of making time controllable are left to the worker.

What still has to happen: a fresh confirming run is needed to check
whether this wording settles the split D31 only narrowed. `--only F05`
is sufficient since nothing else changed.

Reversal: a future run still splitting between short and medium after
this reword would mean the fixture's actual scope, a single test file
with no existing scaffolding to bound it, is simply closer to the
boundary than a wording fix can settle, and F05 should be accepted as
an inherently borderline control (the way F18's single blip was
accepted as noise) rather than reworded a third time.
## 2026-09-08 D34. score_routing.py no longer silently overwrites recorded evidence

Decision: `score_routing.py` gains two safeguards. Result filenames now
include a `--only` tag when one is given, and any write that would still
land on an existing path is redirected to the first free `-2`, `-3`, ...
variant instead. No change to what gets scored or how; this is recording
only.

Why: date, model and bundle key result filenames, a scheme `bundle_tag`
already improved once after a 2026-09-06 collision, but it is still not
enough. A targeted `--only F05 --runs 3` run against the same bundle as
an earlier full-suite `--runs 3` run produces the identical filename,
and this session hit exactly that twice on 2026-09-08: once confirming
D26/D27/D28's fixes and again confirming D33's F05 reword, both times
silently overwriting an already-committed batch that had to be recovered
by hand from git history before the new evidence could be kept. A script
whose entire purpose is producing a dogfood record for CLAUDE.md should
not be able to destroy the record it already produced.

What changed: `only_tag()` folds `--only`'s fixture ids into the
filename, sorted and de-duplicated so argument order does not matter.
`unique_path()` is the backstop for every other way two runs can still
share a name (an identical rerun later the same day, an assess-only
variant, anything not yet anticipated): if the target exists it appends
a numeric suffix rather than writing over it. Verified against a
temporary directory: a first write lands on the plain name, a second
identical write lands on `-2`, a third on `-3`.

Reversal: none anticipated. A future scheme that keys filenames on
something more specific than date, model, bundle and fixture subset
could drop `unique_path` as no longer load-bearing, but keeping it costs
nothing and remains the correct behaviour regardless of what else keys
the name.

## 2026-09-11 D35. Branch the-system adopted; charter amended; plan revised

Decision: work proceeds on branch `the-system`, created from `main` at
`3f25243`. `CLAUDE.md` gaining an "Active plan" section is recorded here
as a charter amendment, since it binds every future session in this
repository to a stage-by-stage approval protocol rather than the free
delegation the charter previously described. The protocol: one stage per
session, the session confirms with Jeb that it is on the stage's required
model class and effort before starting, Jeb approves the stage explicitly
in the conversation, each task is its own commit with the harness green,
and the plan's checkboxes and status lines are updated in the same commit
as the work they record.

Why: `docs/PLAN.md` and `docs/REVIEW.md` were authored by Claude (Fable
5.1) on 2026-09-10, in the Cowork session that closed the F05, F08, F09
and F11 diagnostics (D26 to D34), and were reviewed and approved by Jeb
before the project moved to Claude Code. Jeb landed all four files
(`CLAUDE.md`'s amendment, `docs/PLAN.md`, `docs/REVIEW.md`, and
`src/System/SYSTEM.md`) on `main` in commit `3f25243`, the commit the
adopted plan cites as the handover point. This entry is Stage 0.3 of that
plan, the first task any session on `the-system` performs.

`src/System/SYSTEM.md` was repaired in the same 2026-09-10 session before
being committed: line endings converted from CRLF to LF, a trailing
newline added, and fourteen characters a code-page conversion had turned
into `?` were restored as the Unicode characters a re-read of context
made unambiguous (twelve arrows and one less-than-or-equal-to sign in
section 3's pseudocode, one further arrow in section 7), matching the
multiplication and division signs that had survived the same conversion
intact. The seven remaining question marks in the file (section 1's
Critic row, the six question headings at its end) are genuine content,
not corruption, and were left as written.

`SYSTEM.md` is the second half of an exchange. It refers throughout to
"the eight-step sequence from the previous answer" and "the forty
techniques from the previous answer", and neither is in this repository.
Stage 9 of the revised plan addresses this: ask Jeb for the missing half
first, and reconstruct only the minimum needed to proceed if he does not
have it.

What changed on 2026-09-11: the plan was revised by Claude (Sonnet 5,
running as the first Claude Code session on this machine) at Jeb's
request, after a full read of the repository and a harness run turned up
two things the adopted plan did not know about. First, the platform
version had moved from 2.1.245, the version every row of `FINDINGS.md`
was verified against, to 2.1.263, with nothing re-checked in between.
Second, `check.py`'s PERSONA check failed on this machine: a path-
separator mismatch between how the manifest stores names and how the
check compared them, not a content change (Stage 0.2 fixes this in the
same session). Both were artefacts of this being the first session run
outside the Cowork environment the plan and review were written in.

The revision's substantive reordering: the two-stage classifier, which
the review names as the fix to the routing table's central defect (an
attractor bending unrelated classifications toward a newly added row),
moves from an optional pull-forward late in the plan to the default path,
directly after a reporting bar is given to the routing side. The
experiment that would find a benchmark task the cheapest cell fails is
separated from the framework track and run first, because every task
built so far has cleared at the floor, and the framework's own
falsification test needs a task the floor cannot pass to have a subject.
The framework track (recovering `SYSTEM.md`'s missing half, building the
Controller, running the fleet against a baseline) is gated on that
result rather than built regardless. Full detail is in `docs/PLAN.md`,
"Revision of 2026-09-11".

Reversal: none anticipated for the branch or the charter amendment
themselves. The revision's reordering is itself reversible by a future
decision entry if a later stage's evidence contradicts the priority
judgement it rests on; the plan's own protocol requires such a change to
be recorded rather than made in place.

## 2026-09-11 D36. benchmark.py's own filename collision, fixed and recovered

Decision: `test/harness/benchmark.py` gains the same two safeguards D34
gave `score_routing.py`: a `tasks_tag()` helper folds a `--tasks` subset
into the result filename, and `unique_path()` redirects any write that
would still land on an existing path to the first free `-2`, `-3`, ...
variant. The two historical versions of `test/results/2026-09-07-
benchmark-04d2acc.md` that this collision overwrote are recovered from
git history into their own files, and the file at that name today,
which the collision left holding unrelated content, is renamed to
describe what it actually contains.

Why: this is the identical defect D34 fixed in `score_routing.py`, in
its sibling script. Result filenames were keyed on date and bundle
only. `git log --oneline -- test/results/2026-09-07-benchmark-04d2acc.md`
shows four commits touching that one path: `a6b7426`, the real six-task
benchmark run; `17b9052`, its replication, run to settle whether D16's
and D17's fixture fixes changed T4 and T6's results (they did, and did
not, respectively); `59babc4`, T7's first confirmation attempt,
overwriting the six-task replication under the same name; and `92c77d7`,
T7's clean second confirmation attempt, overwriting `59babc4` in turn.
Every `--tasks T7` run after the six-task run shared its filename because
neither carried the task subset. `test/results/2026-09-06-benchmark-
full-preregistration.md` already documents the first overwrite in its
own text (line 340, "the same filename as the first run; the first run's
content is preserved in git history at commit `a6b7426`"), written at
the time by the session that caused it, but nothing was done about it
until now.

What changed: `test/results/2026-09-07-benchmark-04d2acc-original.md`
holds `a6b7426`'s content, the real six-task run `docs/DECISIONS.md` D16
cites and `2026-09-06-benchmark-full-preregistration.md` line 179 cites.
`test/results/2026-09-07-benchmark-04d2acc-replication.md` holds
`17b9052`'s content, the replication `2026-09-06-benchmark-full-
preregistration.md` line 340 cites. Both citing documents are dated
evidentiary records and are left unedited, per the ledger's append-only
convention; this entry is the pointer from their stale filename to
where the content now lives. `test/results/2026-09-07-benchmark-04d2acc.md`,
which held `92c77d7`'s content (T7's confirmed run, not a six-task run
at all), is renamed to `test/results/2026-09-07-benchmark-04d2acc-tasks-
T7.md`, the name the fixed script would have produced for that run.
`benchmark.py`'s docstring is also corrected: it said six tasks with a
fixed list; there are eight, T1 through T8, discovered from the
directory rather than hardcoded.

Recovering `a6b7426`'s content reopened a second, separate defect its
own commit message had already flagged and left unresolved: `check.py`'s
PROSE check fails on a worker's verbatim quoted report, at a single US
spelling naming a category of test the worker's own report used,
because a raw benchmark result dump is checked as authored prose. That
commit's message argued correctly that rewriting a worker's exact words
to pass a style check would corrupt the evidentiary record, and left the
question of whether `PROSE_GLOBS` should exempt such files open.
Resolved here, narrowly:
`check_prose` now skips the banned-word, banned-phrase, US-spelling and
em-dash checks (not the CR and trailing-newline checks, which are about
the file's own formatting) on any line containing `benchmark.py`'s own
`render()` markers, the literal substrings `"grader: "` or
`" || worker: "` it inserts when relaying a run's grader output or a
worker's report. The exemption is keyed to that literal content, not to
a file name, so authored text sharing a result file with relayed
content stays checked.

Verified: a temporary-directory test of `tasks_tag()` and `unique_path()`
mirrors D34's own verification, an identical write lands on the plain
name, a second on `-2`, a third on `-3`; `--tasks T7` produces
`-tasks-T7` in the filename. `test/harness/check.py` reports 0 failing
(109 files clean, up from 107) after the rename, the two recovered
files, and the PROSE exemption.

Reversal: none anticipated, for the same reason D34 gave its own fix.

## 2026-09-11 D37. A table or fixture change is confirmed only at reporting grade

Decision: a change to `ROUTING.md`'s table, or to a fixture's `assessment`
or `expected_cell`, is called confirmed only when every fixture the change
touches has a reporting-grade `score_routing.py` run behind it, nine runs
or more per Stage 3.1's new grade label. Below that, the change is
steering: useful for narrowing where to look next, never cited as the
reason a change is correct. This is `score_routing.py`'s side of the
discipline `BENCHMARK-DESIGN.md` already states for `benchmark.py`
("A report never cites the steering threshold as evidence").

Retroactively, without editing any of them: D23 through D33 all rest on
steering-grade runs, three per batch. This is not a defect discovered now;
it is what those entries' own evidence sections already show, read against
a bar that did not exist in writing until this decision. Nothing about
their conclusions is withdrawn. A future session revisiting F03, F05, F07,
F08, F11, F13 or F19's history should read those entries' verdicts as
steering-grade findings, not reporting-grade confirmations, until a
reporting-grade run backs the same fixtures.

Why the asymmetry existed until now: an opus routing pass over the full
eighteen-fixture set costs about USD 3 (`docs/COST.md`'s own figures put a
run at USD 2.95 to 2.97), so nine passes is about USD 27. During the week
of calibration that produced D23 through D33, USD 27 per table edit was
judged too much to spend on each of what turned out to be a rapid sequence
of small wording corrections, most of them settled or reverted within the
same session. That judgement was reasonable for calibration, where the
question was "does this wording read differently at all", answerable at
three runs. It is not reasonable for a change this project intends to keep:
`ROUTING.md` is a shipped artefact, and USD 27 is not a large cost against
what a wrongly confirmed row then costs downstream, in over- or under-
provisioned routing on every task it touches from that point on.

What changes going forward: any session editing `ROUTING.md`'s table or a
fixture's `assessment`/`expected_cell` runs `score_routing.py --runs 9
--record` (or reuses an existing reporting-grade run against the identical
bundle and fixture set) before writing the confirming decision entry, the
same before-and-after discipline the attractor finding (D13) already
requires, now with the run count that discipline needs to mean something.

Reversal: none anticipated for the policy itself. The threshold of nine
is `benchmark.py`'s own (D15's corrected value, the smallest sample size a
perfect record can clear 0.7 at); a future change to that constant should
change both scripts together, since they are meant to agree on what
"reporting" means.

## 2026-09-11 D38. The premise ledger, and Gate A's fixed acceptance criteria

Decision: `docs/PREMISES.md` is adopted as the routing layer's premise
ledger, and the seven acceptance criteria below are fixed. Gate A passed
2026-09-11: Jeb accepted the ledger's three proposed amendments, the one
proposed addition, the multiplier, and the Gate D rule, all as
recommended. After this entry the criteria are not revised in the light of
results, per `SYSTEM.md`.

### The criteria, verbatim as fixed

1. A benchmark task set exists on which `worker-sonnet-low`'s confirmed
   pass rate fails the reporting bar (nine runs, 95 percent Wilson lower
   bound above 0.7) and some higher cell clears it. Without this, nothing
   above the floor is measured, and Stages 9 to 12 have no subject.
   Existence is the gate; the cost case additionally needs the rate at
   which tasks fail at the floor, which Stage 8 estimates from whatever
   sample exists, with the sample's limits stated.
2. If the framework track runs: on that set, the fleet in quick mode beats
   B0 (one cell running the eight steps as a single prompt) at the
   reporting bar, at a cost per solved task no more than three times B0's.
3. Every routing row above the floor is either backed by a measured
   frontier or removed, with one documented exception: a row whose only
   justification is blast radius is a policy row, and it is labelled as
   such in `src/ROUTING.md` itself, not only in the premise ledger, so a
   consumer reading the shipped table can tell a capability claim from a
   risk-appetite choice. Judgement fixtures alone no longer back a row
   that routes above `worker-sonnet-low`.
4. The harness stays green at every commit and no invariant is weakened.
   A charter amendment (Stage 10 names one) is a decision entry, not a
   quiet edit.
5. No routing-table change is described as confirmed below nine runs per
   affected fixture. Below that it is steering.
6. The cost of a routing verdict is on the ledger beside the cost of the
   work it routes, and the shipped routing mechanism is chosen on measured
   agreement and cost per verdict together, never on agreement alone. The
   comparison baseline includes zero router cost, which is B0: a mechanism
   cheaper than another router but still losing to not routing at all does
   not satisfy this criterion.
7. At close-out, the table's remaining case is stated in one sentence as
   either a measured cost saving or an accepted risk-appetite policy, and
   `src/ROUTING.md` says which.

### The Gate D rule, verbatim as fixed

Stages 9 to 12 run only if criterion 1 holds, meaning at least one
benchmark task where `worker-sonnet-low` fails the reporting bar and a
higher cell clears it. If criterion 1 fails after the two hardening rounds
Stage 7 allows, the framework track closes with a decision entry, and the
same failure triggers the question of whether the routing table should
collapse toward B0, which criterion 3 handles at Stage 8. Jeb may open the
track despite the rule; the reason is recorded.

### What the amendments were, and why

Criteria 1, 3 and 6 were amended and criterion 7 added, each because the
ledger found the proposal admitted an outcome nobody would want.

Criterion 1 asked only that a floor-failing task exist. The dissolution
arithmetic (`PREMISES.md`) shows the table beats B0 only when the router's
cost is below the floor-failure rate times one floor run, so an existence
proof is compatible with a rate of a fraction of a percent and the table
still losing on cost. Existence stays the gate, because it is the right
test for whether anything above the floor is measurable at all; the rate
is now named as what the cost case separately needs.

Criterion 3 allowed a blast-only row to be kept as policy, but only the
premise ledger would have said so. A consumer installing the bundle reads
`ROUTING.md`, not this repository's ledger, and was therefore going to
receive a risk-appetite choice written in the voice of a capability fact.
The amendment moves the label into the shipped file. The ledger also found
that four of the five table rows with no fixture behind them are
consequential, so this amendment covers most of the unbacked set rather
than an edge case.

Criterion 6 as proposed could have been satisfied by choosing the cheaper
of two routers while both lost to not routing at all, which is the actual
situation measured on 2026-09-11 (`docs/COST.md`: an opus verdict costs
USD 0.1645 against a floor run's USD 0.1641). The amendment names B0, at
zero router cost, as part of the comparison.

Criterion 7 is new. Without it the project could reach Stage 13 having
measured everything and never stated what it concluded about its own
central claim.

### The caveat recorded at Gate A

The benchmark gives B0 a free and perfect failure detector, because a
deterministic grader runs on every attempt. Real use has no such detector:
failure is caught by whoever reads the output against acceptance criteria,
and some fraction of wrong-but-plausible answers is not caught at all.
Every comparison these criteria describe is therefore biased in B0's
favour by an unknown amount, and the size of that bias is precisely the
value of the routing table. The criteria cannot correct for this, and no
instrument in the repository can measure it. A result that goes against
the table by a narrow margin is read with this in mind.

### What else the ledger fixed

The goal ladder's third rung, which the plan left to the Framer, is stated
as total cost in tokens, wall clock and the user's attention per unit of
work that can be trusted without re-checking. At that rung routing competes
with levers this project has never compared it against, of which handover
quality (P15) is the largest and is untested by construction.

The dissolution verdict: the routing problem does not dissolve, but it
shrinks from a cost problem to an insurance problem, and to something much
smaller than a fifteen-cell table implies. B0 for the project is
`ROUTING.md` sections 1.1, 3 and 4 unchanged with section 2 deleted, which
is to say every mechanism B0 needs already ships.

The consequence for Stages 5 and 6, which were scheduled as a fix for the
attractor defect: a cheap classifier is also the only route by which the
cost thesis can be true at all. At an opus verdict's price no floor-failure
rate suffices; at USD 0.02 a verdict the required rate falls to about 12
percent. E22 was added to the empirical checklist to measure that figure
before either stage commits to a mechanism.

Reversal: the criteria are fixed and are not reopened on results, which is
the point of fixing them. If a criterion is found to be incoherent rather
than merely demanding, that is a new decision entry saying so, not an
edit here.

## 2026-09-11 D39. The two-stage classifier design, and a table with five inputs

Decision: `docs/CLASSIFIER-DESIGN.md` is adopted as the design, and
`test/results/2026-09-11-classifier-preregistration.md` fixes Stage 6's
measurement. No code is written in Stage 5. The design's load-bearing
choices are recorded here.

**The routing table is a function of five inputs, not three.** This is the
finding the rest of the design turns on, and it was made by pre-flighting
the free check the design proposes rather than by reasoning. Encoding
`ROUTING.md` section 2 as a function of the assessment triple and resolving
all seventeen assessed fixtures through it mismatches on two. F14 routes
through the frontier row, which is conditioned on a documented failure at
`xhigh` on the same task. F18 routes through the fable-xhigh tie-break,
which fires only when the task demands sustained self-directed
investigation. F11 and F12 carry F18's triple exactly and correctly route to
`worker-opus-xhigh`, so the triple is not what separates them.

The table has been described as a three-axis function since D9 wrote it
total, and the harness's ROUTE-TOTAL check counts eighteen triples on that
basis. Both are right about what they cover and silent about the two rows
that need more. A human reading the prose resolves the extra conditions
without noticing them; a classifier emitting only the triple cannot, and
would route F14 and F18 wrongly by the fixtures' own labels. Adding
`self_directed` and `prior_failure` as enumerated fields makes the table a
pure function again, and all seventeen fixtures then resolve, checked
2026-09-11.

`prior_failure` is the weaker of the two and the design says so. It is not
an assessment of the task; it is a fact about what has already been tried,
and escalation already has its own home in `ROUTING.md` section 4. Moving
the frontier row there would leave a four-field schema that is purely about
the task. That change alters what F14 measures, which is a fixture change
under D37 and needs a reporting-grade run behind it, so the design records
the option and does not take it.

**Measurement is separated from delivery, and measurement comes first.**
E15 verified exactly one workable mechanism, a Bash-invoked script, and only
with `--permission-mode acceptEdits --allowedTools "Bash(python3 *)"`.
Without them the call is silently blocked. Shipping that mechanism would add
a Bash-permission requirement to an install that currently needs none, and a
consumer who declines would get an orchestrator that quietly falls back to
its own judgement, which is the silent-substitution class this repository
exists to prevent. Measuring the classifier needs no shipped mechanism at
all: the harness asks for the assessment and applies the table in Python.
So the design measures first and builds the delivery mechanism only if the
measurement earns it, which is the null-hypothesis rule applied to the
project's own proposal.

**Field agreement replaces cell agreement as the primary metric**, because
cell agreement forgives 24 of 72 possible single-field errors, 33.3 percent.
Horizon is the most forgiven at 42.9 percent, sensitivity 28.6, blast 25.0.
Sixteen covered triples map to six cells, so the table absorbs axis error by
construction. Two consequences are recorded. The 2026-09-11 baseline's 95.7
percent is an upper bound on assessment quality rather than an estimate of
it. And horizon is simultaneously the least reliable axis (P03) and the one
the metric penalises least, which is a sufficient explanation for why
horizon is exactly the axis that drifted across F03, F05, F08, F11 and F18:
nothing was pushing back on it.

**The two-axis variant cannot be decided by this fixture suite**, and the
pre-registration says so before the run rather than after. Two independent
reasons. Dropping an axis changes the correct answer, and the fixtures
encode three-axis answers, so scoring the variant on cell agreement marks it
wrong four times in seventeen by construction (F03, F05, F07 and F10 all
collapse to the floor). And the suite confounds the two axes at issue:
sensitivity predicts horizon at 70.6 percent against a 35.3 percent base
rate (`docs/PREMISES.md`). The variant is still measured, because the
marginal cost is a few dollars once the flag exists, but a null result is
agreed in advance to be uninformative.

One further finding came out of the collapse arithmetic and does not depend
on any model run. **Open and contained is not monotonic in horizon**: short
routes to `worker-sonnet-low`, medium to `worker-opus-high`, long back down
to `worker-sonnet-low`. That shape is the result of real measurement, D19
and D21 lowering the long-horizon row on T6 and T7 evidence, so it is not an
error. But it means horizon is not ordinally coherent in the band where the
table has the most evidence behind it, and a model reasoning that longer
implies harder implies a stronger cell would be wrong there. That is an
argument against the axis that needs no classifier measurement at all.

**The shipping rule's cost ceiling is derived, not chosen.** A router pays
for itself only when it costs less than the floor-failure rate times one
floor run. The observed rate is 0 of 8 benchmark tasks, whose 95 percent
Wilson upper bound is 32.4 percent, and a floor run costs USD 0.1641. So the
ceiling is USD 0.0532 per verdict, and a router above it cannot pay at any
failure rate the current evidence permits. The opus router measured on
2026-09-11 exceeds it by 3.1 times. If no configuration clears the ceiling,
none ships and the prose table stands; that outcome is a result, and it
would say the mechanism cannot be made cheap enough to pay for itself on
this evidence.

Reversal: the design is reopened if E20 finds `compact_boundary` is not a
reliable undersizing signal, which would remove the two-axis variant's
escalation mechanism, or if E22 measures a minimal schema-forced verdict
above the USD 0.0532 ceiling, which would close the cheap-router route to
acceptance criterion 6 and make the whole two-stage question a defect fix
rather than an economic one.
