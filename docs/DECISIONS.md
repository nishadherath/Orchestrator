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
