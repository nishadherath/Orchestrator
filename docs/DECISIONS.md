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

## 2026-09-11 D40. The two-stage classifier does not ship: "prompt", not "system"

Decision: neither configuration measured against the Stage 5 pre-
registration (`test/results/2026-09-11-classifier-preregistration.md`)
clears the shipping rule. No two-stage classifier ships. The `--rubric-
only` flag stays in `build_dist.py` as a measurement tool; `dist/` and
`ROUTING.md` are untouched, and the flag is not removed from the codebase,
since it remains useful for any future attempt at this design.

### The numbers, reporting grade (nine runs, 153 verdicts each)

| Configuration | Cell agreement | 95% Wilson lower bound | Cost per verdict |
| :--- | :--- | :--- | :--- |
| A (prose, opus, already measured) | 95.7% | 91.4% | USD 0.1645 |
| B (two-stage, opus) | 92.2% | 86.8% | USD 0.1030 |
| C (two-stage, sonnet, effort low) | 58.2% | 50.2% | USD 0.0130 |

Rule 1 (non-inferior on accuracy: lower bound at or above A's 91.4 percent):
B fails at 86.8 percent, close but short. C fails decisively at 50.2
percent.

Rule 2 (cheap enough: below the derived USD 0.0532 ceiling): B fails at
USD 0.1030, roughly double the ceiling. C passes clearly at USD 0.0130.

No configuration passes both. The decision rule required all three; B
fails on cost, C fails on accuracy, and there is no configuration that
was cheap and accurate together. This is exactly the pattern the premise
ledger's dissolution check anticipated in the abstract (`docs/PREMISES.md`):
opus-quality classification costs opus prices, and a cheap model does not
reproduce opus-quality classification.

### Predictions scored

| Prediction | Predicted | Actual | Verdict |
| :--- | :--- | :--- | :--- |
| B, cell agreement | 93-97%, centre 95 | 92.2% | Falsified, narrowly (0.8 points below the floor) |
| B, all-fields agreement | 78-88%, centre 83 | 77.8% | Falsified, narrowly (0.2 points below the floor) |
| B, cost per verdict | USD 0.10-0.14 | USD 0.1030 | Held |
| B indistinguishable from A on cell agreement | Deliberate null | 95 percent Wilson intervals overlap (B [86.8, 95.5], A [91.4, 97.9]) | Held |
| C, cell agreement | 75-88%, centre 82 | 58.2% | Falsified, decisively |
| C, all-fields agreement | 60-75%, centre 68 | 48.4% | Falsified, decisively |
| C, cost per verdict | USD 0.01-0.03 | USD 0.0130 | Held |
| D, retained-field agreement (steering only) | 72-85%, centre 79 | 60.8% | Falsified |
| D, cost per verdict | USD 0.01-0.03 | USD 0.0148 | Held |
| F09 improves but lands between 5 and 7 of 9 | 5-7 of 9 | 3 of 9 (B) | Falsified, worse than predicted |
| Unparsed rate under 2 percent (opus) / 8 percent (sonnet, effort low) | as stated | 0 of 153 (opus); 1 of 153 (sonnet, 0.65 percent) | Held, both |
| `self_directed` fires well above the one-in-seventeen base rate; a rate above 20 percent needs a sharper definition or removal | as stated | Opus: 24 of 153 (15.7 percent), under the trigger. Sonnet at effort low: 58 of 153 (37.9 percent), well over it | Confirmed for sonnet, not triggered for opus |

Cost predictions held cleanly across every configuration; the cost side of
this design was well understood before any run. Accuracy predictions were
close for opus and badly wrong for the cheap model, in the direction that
matters: the cheaper the model, the worse the miss, which is the opposite
of what the cost thesis needs.

### The `self_directed` field is a real design defect, independent of the shipping verdict

At sonnet, effort low, the model claims `self_directed: true` in 37.9
percent of verdicts, against a true rate of one fixture in seventeen (5.9
percent). This is exactly the failure shape the pre-registration named in
advance and set a 20 percent trigger for. An unanchored boolean with no
worked contrast in its own definition invites a "yes" bias, and it invites
it more at lower model capability, which is the opposite of what a cheap
router needs. Any future two-stage design should either give `self_directed`
a much sharper definition, with contrasting examples, or remove it and
handle the frontier and tie-break cases a different way; `docs/CLASSIFIER-
DESIGN.md` already names moving `prior_failure` to `ROUTING.md` section 4's
escalation logic as one option, and the same argument now applies to
`self_directed`.

### The bug found during measurement

`tools/route.py`'s `resolve_two_axis` crashed live during configuration D's
first attempt: a model correctly reported `prior_failure: failed_at_xhigh`
for F14, and the frontier rule, which matches on `prior_failure` alone
regardless of horizon, returned the same rule at all three horizons
uniformly; `worker-opus-max` was deliberately absent from the cost ladder
the collapse ranks against, and the lookup raised `ValueError`. Fixed by
short-circuiting on an escalation-only match before attempting cost-
ranking. `score_routing.py` has no per-fixture checkpoint (unlike
`benchmark.py`), so the interrupted run's partial spend was not
recoverable; D was re-run clean after the fix, at no material additional
cost since D is the cheap configuration.

### What this means for acceptance criterion 6 and the project's own thesis

Criterion 6 required the shipped routing mechanism, if any, to be chosen
on agreement and cost per verdict together, against a baseline that
includes B0 at zero router cost. No mechanism is shipped, so criterion 6
is satisfied by inaction: the existing prose table, which criterion 7
already requires to be stated honestly at close-out, remains the
mechanism, unimproved by this stage.

This also sharpens the premise ledger's dissolution finding
(`docs/PREMISES.md`) rather than reversing it. The dissolution check
showed the table cannot beat B0 on cost with an opus-priced router. This
stage shows the reason is not incidental: cheap classification of this
task is not currently achievable at the accuracy the table needs.
Whatever value the routing table has above the floor, it is not
obtainable by asking a cheaper model to do the same assessment job a more
expensive one does passably.

### What is not settled

The two-axis question (D) remains formally undecided, per the pre-
registration's own advance agreement: this fixture suite cannot decide it,
and D's poor showing is consistent with either "horizon matters" or "the
cheap model classifies badly regardless of which axes it is asked for",
which the suite cannot distinguish. F13 scored 0 of 9 fields correct under
every configuration tested (B, C and D alike), which is worth a fixture-
level look in a future stage: either F13 is genuinely hard to classify
without a table for context, or its wording invites a specific,
consistent misreading.

Reversal: a materially cheaper high-accuracy model, or a redesigned
`self_directed`/`prior_failure` schema that removes the sonnet-class
over-firing, would be grounds to re-run this measurement. Nothing here
forecloses trying again; it records that this attempt, on this evidence,
does not clear the bar.

## 2026-09-13 D41. Harness defect: the interpreter allowlist voids two of T9's nine confirmation runs

Decision: T9's first confirmation attempt (7 of 9, Wilson lower bound
45.3%, does not clear 0.7) does not settle T9's frontier. Two of the nine
runs are harness failures, not worker results, and are void rather than
evidence against `worker-sonnet-low`. The harness is fixed and T9 needs a
fresh confirmation attempt, the same repair T7 needed after D20.

Why: `benchmark.py` ran the forwarder with `--allowedTools "Bash(python3 *)"`,
so the only shell command a worker could run without a human present was one
spelled `python3`. Nothing in `task.md` or `PROBLEM.md` tells a worker which
spelling to use, and on Windows `python` is the common one. The two voided
runs' full report text, read from the checkpoint file rather than the
results table (which truncates the report column at 200 characters), shows
the same thing in both: the worker typed `python -m unittest` and
`python bench.py`, was told the command "requires approval", found that
`dangerouslyDisableSandbox` did not lift it, and stopped. One of them,
verbatim: "I cannot fabricate test/benchmark output, so I'm stopping here
rather than writing unverified numbers to MEASUREMENT.txt."

Both reports also show the worker had already found and fixed the real
defect before it was blocked: `_format_rows`'s `line not in out` scan,
replaced with a set and a single join, which is the intended fix exactly,
and both state outright that `EventStore.query()` is not the cost. So on
the task's own terms the two voided runs are premise-rejection successes
that failed only the artefact check, and they failed it for the right
reason. That is worth recording on its own: a worker that will not invent
a measurement it could not take is the behaviour `PROBLEM.md`'s "a claim
about where time goes is not accepted without the measurement that
produced it" is asking for.

This is a different failure shape from D20. D20 was a forwarder that never
spawned a worker and confabulated a result; this is a worker that did the
work and was denied the one tool the task needs, by a harness setting.
D20's rate was 1 in 174; this one hit 2 of 57 runs in this batch and,
because it depends on which spelling the worker happens to type, it is a
flake with a systematic cause, not a random one. It hit only T9: the
checkpoint has no other run matching the "requires approval" pattern, so
T10 and T11 are unaffected. T9's three search runs also did not hit it,
which is consistent with the spelling being a per-run choice.

What changes: `FORWARDER_PERMISSION_ARGS` now allows `Bash(python3 *)` and
`Bash(python *)` both, and the checkpoint's `permission_mode` identity
label carries the allowlist, so a checkpoint written under the narrower
setting is refused as a different measurement rather than resumed into.
The results table's 200-character truncation of the report column is left
as it is; it is a display choice, the checkpoint keeps the full text, and
this entry is the record of where to look.

What does not change: the two runs stay in the recorded results file as
they are, marked failed, with this entry as the reason they are not
counted. The genuine sample is 7 of 7 passing, and per D15's arithmetic
seven of seven has a lower bound of 0.646, eight of eight 0.676, and nine
of nine 0.701, so no perfect record shorter than nine clears the bar; a
fresh nine-run confirmation is required, not a discard of the two runs in
place.

Reversal: if the fresh attempt hits the same pattern with both spellings
allowed, the cause is not the allowlist and this entry's diagnosis is
wrong; the checkpoint's report text is the place to look first.

## 2026-09-13 D42. Stage 7 result: the floor fails T10, and what it fails on is deference, not capability

Decision: acceptance criterion 1 is met. T10 is a benchmark task on which
`worker-sonnet-low`'s confirmed pass rate fails the reporting bar and a
higher cell clears it. The Gate D rule's condition therefore holds, and
the recommendation carried to Gate D (applied by Jeb after Stage 8) is that
the framework track opens. Hardening under task 7.3 is not triggered,
because it applies only when all three tasks clear the floor.

Results, from `test/results/2026-09-11-benchmark-af94deb-tasks-T10+T11+T9.md`
(57 runs, USD 27.55, 166 minutes, bundle `2026-09-07-af94deb`, harness at
`9d543e9`):

- **T10, false constraint.** Search: `worker-sonnet-low` 0 of 3,
  `worker-sonnet-medium` 1 of 3, `worker-sonnet-high` 0 of 3,
  `worker-sonnet-xhigh` 0 of 3, `worker-opus-high` 3 of 3. Confirmation:
  `worker-opus-high` 9 of 9, Wilson lower bound 70.1%, clears;
  `worker-sonnet-xhigh` 0 of 9, interval [0.0%, 29.9%], fails, so the
  exclusivity requirement is met. Frontier confirmed at
  `worker-opus-high`. Combined across search and confirmation, sonnet at
  xhigh effort is 0 of 12 on this task.
- **T11, T7's lineage at larger scale.** Search 3 of 3, confirmation 9 of
  9 at `worker-sonnet-low`, lower bound 70.1%. Frontier confirmed at the
  floor. This is the third fixture of that lineage (T6 twice, T7, now
  T11) to land there, and it was pre-registered as the control.
- **T9, false measurement.** Search 3 of 3 at the floor, confirmation 7 of
  9, of which two runs are void under D41. Frontier not settled; the
  genuine record is 7 of 7 and a fresh nine-run confirmation is required.

The pre-registration's directional prediction held, with a sharpening.
It predicted that if the floor broke it would break on premise rejection
rather than scale, and it did: T11 cleared, T10 did not. But it grouped T9
and T10 together as the premise-rejection pair, and they came apart. Every
genuine T9 run at the floor disbelieved the planted profiling claim, named
`_format_rows`, and fixed it. So a false measurement is rejected readily
at the floor; a false constraint is not. The distinction is in what the
worker does after it has verified the premise is false.

What T10 measures. The full report text of all 20 failing sonnet runs,
read from the checkpoint, matches on `downstream.py` and `.strip()` in
every one: 20 of 20 sonnet workers, at every effort level, read the three
call sites, saw that each strips the result itself, and wrote that down,
several in `IMPACT.txt` exactly as the task asked. They then patched
`accounts.py` and left the frozen file alone. One `worker-sonnet-low` run,
verbatim: "That's evidence against the stated rationale for freezing the
file, but PROBLEM.md's Constraint section is an explicit instruction, not
just a rationale, so I honored it literally rather than overriding it
based on my own analysis." A `worker-sonnet-xhigh` run reasons the same
way at greater length and explicitly declines the monkeypatch that would
satisfy the letter of the freeze. The opus runs treated the falsified
justification as dissolving the instruction it justified, edited
`legacy_ids.py`, and passed.

So the frontier on T10 is not a capability frontier in the sense the
rubric's intelligence-sensitivity axis describes. Sonnet found everything
opus found. The difference is a disposition: whether an explicit
instruction survives the worker's own verification that its stated reason
is false. Effort does not move that disposition at all (xhigh 0 of 12),
which bears on the open question of whether the fifteen effort-specific
persona sections earn their existence; on this task the model class is the
whole effect.

Two readings of that, both recorded because the criteria fixed at Gate A
are not revised in the light of results and this is the kind of result
the Gate A caveat anticipated:

1. Under the criteria as fixed, the grader is the grader. `PROBLEM.md`
   gave the false justification precisely so that it could be checked,
   asked for the check to be written down, and made the pinned test the
   acceptance criterion. A worker that verifies the justification is false
   and still declines to act on that verification has not completed the
   task as set. Criterion 1 holds.
2. In real use, the sonnet behaviour is a defensible policy: fix what the
   constraint allows, write down that the constraint's reason does not
   hold, flag the contradiction, and stop. A consumer who freezes a file
   may prefer a worker that will not override the freeze on its own
   analysis, however good the analysis. Stage 8 has to say which of these
   the row it derives from T10 is buying, in `src/ROUTING.md` itself: the
   measured thing is opus's willingness to override an explicit, falsely
   justified constraint, and the table should not describe that as
   "harder tasks need a stronger model".

Predictions scored against the pre-registration:

- Floor breaks on at least one task: held (T10).
- Direction, premise rejection not scale: held, sharpened as above.
- T9 and T10 above the floor at sonnet-medium or sonnet-high: T10 went
  past every sonnet cell to opus, which the prediction did not reach; T9
  is unsettled. Wrong on magnitude for T10.
- T11 at the floor or sonnet-medium: held.
- Grader reliability, zero false results: held as far as inspected. The
  two T9 failures were correct grader verdicts on void runs; the artefact
  really was absent, for a reason D41 attributes to the harness.
- Wall clock: T11's search mean of 70.6 seconds is above T7's 67.3, so
  the falsification condition was not met, but by three seconds, which is
  not the "above it" the prediction meant. T9 (102.3 seconds) and T10
  (185.8 seconds at the floor) were predicted between T6's range and
  T7's mean and both exceeded T7's mean. Wrong: editing code and running
  tests costs more wall clock than diagnosing does, which should have
  been predicted.
- Cost: USD 27.55 against an estimate of USD 30 to 150. Below the range,
  because two of three tasks did not climb. The pre-registration's
  own "predicted case near USD 25" was closer than its stated range.
- Containment and reset: zero violations, zero failures.

Costs for Stage 8's arithmetic, per run, means: `worker-opus-high` on T10
USD 0.86 in confirmation and USD 1.11 in search; `worker-sonnet-low` on
T10 USD 0.42, on T9 USD 0.25, on T11 USD 0.19. Two things follow. The
floor is not one price: a task the floor fails costs more at the floor
than a task it clears, because the worker does more before stopping. And
B0's escalate-on-failure path on T10 walks four sonnet cells (search means
USD 0.42, 0.49, 0.48, 0.70) before reaching the cell that passes, which is
USD 2.09 spent on failing before USD 1.11 spent on succeeding; a routing
verdict that sent T10 to opus directly would have to cost less than that
gap to pay for itself, and by `docs/COST.md` an opus verdict costs about
USD 0.16. That is the first measured case where the dissolution check's
inequality (router cost below floor-failure rate times failure cost) can
hold, and it holds only because the ladder's failure cost on this task is
the whole sonnet column, not one run. Stage 8 should do this arithmetic
properly, with T9's settled frontier in hand and the caveat that the
benchmark hands B0 a free failure detector.

What is not settled: T9's frontier (D41), and whether the T10 disposition
generalises beyond the one shape tested. One task is existence, which is
what criterion 1 asks for; it is not a rate. The rate at which tasks fail
at the floor is Stage 8's to estimate from the sample that exists, which
is now eleven tasks with one confirmed floor failure and one unsettled.

Reversal: T9 re-confirming below the bar with both interpreter spellings
allowed would make the false-measurement shape a second floor failure and
weaken the sharpening above; T9 confirming at the floor leaves this entry
as written.

## 2026-09-14 D43. Stage 8 design: the table collapses to the floor, one measured row, and the escalation rule

Decision: `src/routing_table.json` is rewritten from eleven rules to four,
before any edit is made, as follows. The design rests on `docs/FRONTIERS.md`
(Stage 8.1) and on Jeb's risk-appetite decision, taken on 2026-09-14 and
recorded here, to drop all four blast-radius rows rather than keep them
as labelled policy.

The four rules, in match order:

1. `frontier`: `prior_failure` is `failed_at_xhigh`, `worker-opus-max`
   (or `worker-fable-max`), escalation only. Unchanged. Mechanism, not a
   capability claim; no benchmark task has exercised it.
2. `open-medium`: sensitivity open, horizon medium, any blast,
   `worker-opus-high`. The one measured frontier above the floor (T10,
   9 of 9, with `worker-sonnet-xhigh` 0 of 9 below it). Its text says what
   it buys, per D42: on T10 every failing sonnet run found what opus found
   and declined to act against an explicit instruction whose stated reason
   it had itself shown to be false; opus acted. The row's description in
   `src/ROUTING.md` records that, records that T10 was classified as this
   triple after the result was known, and records that T9, the same triple
   with a false measurement in place of a false constraint, confirmed the
   floor.
3. `open-short-or-long`: sensitivity open, horizon short or long, any
   blast, `worker-sonnet-low`. T5 and T8 (short), T6, T7 and T11 (long).
4. `mechanical-or-structured`: sensitivity mechanical or structured, any
   horizon, any blast, `worker-sonnet-low`. T1, T2, T3, T4.

Rules 3 and 4 are written as two disjoint rules rather than one "anything
else" rule so that `check.py`'s ROUTE-TOTAL, which treats every multiple
match as an overlap needing a documented order, has nothing to document.
The table becomes total: `documented_gaps` empties (D27's mechanical
long-horizon gap closes on T2's evidence) and `documented_overlaps`
empties (D39's `self_directed` disambiguation has nothing left to
disambiguate).

What goes, and on what grounds:

- `mechanical-medium` (`worker-sonnet-medium`) and
  `structured-medium-contained` (`worker-sonnet-medium`): no task at the
  triple, bracketed by floor results at both ends of horizon. Criterion 3.
- `structured-long` (`worker-sonnet-xhigh`): measured at the floor directly
  by T4, twice. Criterion 3.
- `mechanical-short-consequential` (`worker-sonnet-medium`),
  `structured-short-or-medium-consequential` (`worker-sonnet-high`),
  `open-any-consequential` (`worker-opus-xhigh`),
  `open-long-consequential-self-directed` (`worker-fable-xhigh`): blast
  radius only, unmeasurable by the benchmark by construction
  (`docs/BENCHMARK-DESIGN.md`), dropped by Jeb's decision. The reasons
  put to him: the rows cost three to five times the floor on open work
  for a payoff nobody has measured; and the one thing opus is measured to
  buy over sonnet, a willingness to override an instruction once its
  stated reason is verified false, is the disposition least wanted
  unsupervised on the consequential work those rows route to it.
- `short-contained` and `open-long-contained` (both `worker-sonnet-low`):
  absorbed into rules 3 and 4; nothing changes for the triples they
  covered.

Fixtures whose `expected_cell` follows the table: F03, F05, F07 (the three
merged rows), F06, F08, F17 (structured and mechanical consequential), F11,
F12 (open long consequential), F18 (open long consequential self-directed),
all to `worker-sonnet-low`. F10 stays `worker-opus-high`, F14 stays
`worker-opus-max`, the floor fixtures stay, F16 stays clarify. Nine of
seventeen assessed fixtures change their confirmed answer, which is the
size of the change and is why the after-measurement is not optional.

What is deliberately not changed in this stage:

- Section 1 of `src/ROUTING.md`, the rubric. Blast radius and the two
  implicit inputs (`self_directed`, `prior_failure`) are still assessed
  even though blast and `self_directed` now route nothing. The
  after-measurement compares fixture by fixture against Stage 3.3's
  before-measurement, and that comparison is only clean if the assessment
  the orchestrator is asked for is the same in both runs and only the
  table differs. Dropping an axis from the rubric is a second change, with
  its own before-and-after, and it belongs to a later stage. Section 2 of
  `src/ROUTING.md` says in words that blast is recorded but does not
  change the cell.
- The rubric's horizon axis, even though its only remaining job is to
  separate T9 and T10's shape (medium) from T5 and T8 (short) and T6, T7
  and T11 (long), all of which confirmed at the floor. D42 says the real
  discriminator on T10 is not horizon but a falsified constraint the task
  requires acting against, which no axis captures. Whether horizon is the
  right predictor for the one row that needs one is a question for after
  the after-measurement, not before it.
- The worker definitions' persona text. Regenerating them changes their
  descriptions (which name the rules routing to each cell) and nothing
  else; eleven cells become "unrouted", which ROUTE-DESC requires them to
  say.

What this is. Stage 4.2's dissolution check asked whether the table beats
B0 (route everything to the floor, escalate on failure). This design is
most of the dissolution outcome, reached by measurement: the assessment
that remains asks, in effect, one question, "is this open work at medium
horizon?", plus the escalation check. The cost case for even that one
question is Stage 8's remaining arithmetic, in D42's terms: an opus
verdict costs about USD 0.16 (`docs/COST.md`), and on T10 it would have
saved the USD 2.09 that B0's ladder spent on four failing sonnet cells
before reaching opus. On every other task measured it saves nothing and
costs USD 0.16. With one floor failure in eleven tasks, the break-even
floor-failure rate is about 0.16 / 2.09, roughly 8 per cent, and the
observed rate is 9 per cent with a sample that cannot distinguish 9 from 1
or 30. That is stated here so Gate C sees it, not as a result.

Before-measurement: `src/ROUTING.md` is byte-identical to `af94deb`, so
Stage 3.3's nine-run opus baseline (155 of 162,
`test/results/2026-09-11-routing-opus-af94deb-summary.md`) is the before
run and 8.3 spends nothing.

Reversal: any fixture that regressed at the bar in the after-measurement
reopens this design per the attractor rule; the specific risk is that
removing rows changes how opus reads the triples that still matter,
which is exactly what D13 observed when a row was added.

## 2026-09-14 D44. The after-measurement reopens D43: the one row above the floor is an attractor the orchestrator cannot find on its own fixture

Decision: D43's four-rule table does not ship as designed. The
after-measurement (`test/results/2026-09-14-table-collapse-before-after.md`)
regressed four fixtures at the bar, and the regressions are all the same
mechanism, so per Stage 8.5's rule the change is reopened here rather than
patched. The reopened design, put to Jeb at Gate C, is below.

What the measurement showed. Against the old table opus agreed 155 of 162;
against D43's table, 134 of 162. The twelve fixtures that route to the
floor under both readings are unchanged at nine of nine, and the six whose
expected cell moved down on the sonnet side (F03, F05, F06, F07, F08, F17)
are routed to the floor nine of nine each: opus reads the new table
correctly wherever the table has one answer. The damage is confined to the
one row above the floor, `open-medium` at `worker-opus-high`:

- F10, the row's own backing fixture and T10's triple, was read medium
  nine of nine under the old table and short eight of nine under the new
  one, on unchanged fixture text and an unchanged rubric. It now lands on
  the floor eight times in nine.
- F11 and F12, open consequential investigations whose expected cell moved
  from `worker-opus-xhigh` to the floor, were read long-or-medium and long
  under the old table (the old consequential row made horizon irrelevant
  to them), and medium nine of nine and seven of nine under the new one,
  where medium is the only path to an opus cell. F18 moved two of nine the
  same way.

So the horizon read is not made independently of the destination: it
moves to reach the cell the orchestrator has already decided on. D13
observed this when a row was added; this is the same mechanism observed
when rows are removed, and it is now measured at reporting grade in both
directions. Horizon was already the axis corrected most often (`CLAUDE.md`
open questions) and D42 already recorded that horizon is not what
separates T10 from T9. A row that is reached by bending the one axis that
selects it is not a routing row; it is a destination the orchestrator
chooses first and justifies second.

Why this cannot be fixed by rewording. The obvious patch is to rewrite
section 2's description of the row so that F10 stops reading as short and
F11 and F12 stop reading as medium. That is tuning prose against three
fixtures, which is the anecdote-chasing D13 warned against, and it costs
another USD 18 to check. More to the point, D42 already found the row's
real discriminator: not "open and medium" but "the task requires acting
against an explicit instruction whose stated reason the repository shows
to be false", which is not assessable before any code is read and which
the sonnet worker at the floor detects and reports on its own (every
failing T10 run flagged the contradiction). The signal that selects the
cell arrives from the worker, after the floor has run, not from the
orchestrator before it.

The reopened design. The table is the floor plus the escalation rule:

1. `frontier`: `prior_failure` is `failed_at_xhigh`, `worker-opus-max`
   or `worker-fable-max`, escalation only. Unchanged.
2. `floor`: everything else, `worker-sonnet-low`.

T10's evidence moves from section 2 to section 4, as the first measured
escalation trigger: a worker that reports it cannot meet an acceptance
criterion without acting against a stated constraint, and has checked the
constraint's stated reason and found it false, is not re-run at the same
cell; it is re-spawned at `worker-opus-high` with the contradiction named
in the handover. That is what T10 measured: `worker-opus-high` nine of
nine from a cold start on exactly that shape, every sonnet cell zero. The
cheaper alternative, the orchestrator voiding the constraint itself and
re-running the floor with the constraint lifted, is unmeasured and is
recorded as the next thing worth measuring, not as a rule.

Fixtures: F10's expected cell moves to `worker-sonnet-low`. F14 and F16
are unchanged. Nothing else moves. ROW-BACKED holds with two rules.

The rubric's three axes stay in section 1 for this stage, as D43 said,
because removing them is a separate change. Under this table they route
nothing, and the after-measurement of this design is what shows that an
assessment which cannot change the destination still costs a verdict.
Their removal is Stage 13's to decide, with that number in hand.

After-measurement for the reopened design. With one destination there is
no attractor left to bend toward, and the only fixtures whose verdict can
disagree are F14 (escalation) and F16 (clarify). Two options are put to
Jeb: the full nine-run pass (USD 18, the discipline as written) or nine
runs of F14 and F16 only (about USD 2). Either is recorded as the after
run; the choice is his.

What this means for the criteria. Criterion 1 is unaffected: T10 exists
and the floor fails it. Criterion 3 is met by removal: no row above the
floor remains to be backed. Criterion 7's one sentence is now writable:
the routing table is B0, route everything to `worker-sonnet-low` and
escalate on evidence, with one measured escalation trigger and one
mechanism rule; nothing above the floor is a measured cost saving. That
is the dissolution outcome Stage 4.2 described, and the after-measurement
of D43 is what forced it: the last row above the floor did not fall to
lack of evidence for the cell, it fell to the orchestrator being unable to
find the row on the fixture that backs it.

Gate C alternatives, for the record: reject the change and revert to the
eleven-rule table, which leaves criterion 3 unmet and blocks this stage;
or ship D43's table as measured, with its one row reachable one time in
nine on its own fixture, which 8.5's rule forbids and this entry does not
recommend.

Reversal: a classifier that reads horizon independently of the table
(Stage 6's two-stage design was built for that and was rejected on cost
and accuracy, D40) would reopen the question of an upfront row for T10's
shape. Until one exists, the trigger lives in section 4.

## 2026-09-14 D45. Gate C passed: the routing table is the floor plus the escalation rule

Decision: Jeb accepted D44's reopened design at Gate C on 2026-09-14, on
the before-and-after evidence, and chose the F14-and-F16-only
after-measurement for it. `src/routing_table.json` has two rules, `floor`
(`worker-sonnet-low`, every assessed task) and `frontier` (escalation
only). The shipped bundle is `2026-09-14-282981f`. Stage 8 is complete.

The after-measurement of the reopened table
(`test/results/2026-09-14-routing-opus-282981f-only-F14+F16-summary.md`):
18 of 18, F14 nine of nine (`worker-opus-max` five, `worker-fable-max`
four, both accepted by the rule), F16 nine of nine clarify. USD 2.31 for
nine runs, USD 0.129 per verdict. Nothing to compare fixture by fixture
against the before run for the other sixteen fixtures, because under this
table their verdict has one possible value; that is the point of the
table, not a gap in the measurement.

Three reporting-grade runs are now on record for this stage: the
eleven-rule table (155 of 162), D43's four-rule table (134 of 162), and
this one. The middle run is the one that carries the finding: a row above
the floor that the benchmark had measured a cell for was unreachable by
the orchestrator on its own backing fixture, because the horizon read
moved with the destination. That is D13's attractor at reporting grade in
both directions, and it is the reason the table has no rows above the
floor rather than one.

Criteria, as of this entry:

1. Met (D42): T10 exists and the floor fails it.
2. Not yet tested: the framework track's question, Gate D.
3. Met by removal: no row above the floor remains. The escalation rule is
   a mechanism and is labelled as one in `src/ROUTING.md`.
4. Met: harness green at every commit; no invariant weakened.
5. Met: no table change described as confirmed below nine runs.
6. Met by inaction (D40) and now by shape: the shipped mechanism is B0
   plus one measured escalation trigger. The router's remaining verdict
   cost, about USD 0.13 to 0.16 per task, buys the routing line and the
   clarify decision and nothing else; whether that is worth paying is
   Stage 13's sentence.
7. Writable, and `src/ROUTING.md` section 2 now says it: nothing above the
   floor is a measured cost saving; the table is route-to-the-floor with
   one measured escalation trigger and one escalation mechanism.

What the escalation trigger is worth, in D42's numbers, for Stage 13: on
T10, B0 as originally conceived (one cell up per failure) spends USD 2.09
on four failing sonnet cells before USD 1.11 succeeds; the trigger goes
from the floor's USD 0.42 straight to opus, USD 1.53 in total. On the ten
tasks the floor clears it costs nothing. An upfront router that found T10
would spend USD 0.16 on every task to save USD 0.42 on one, and the
after-measurement shows it would not reliably find T10's shape anyway.

Open after this entry, for `CLAUDE.md`'s list: the rubric's three axes
are assessed and route nothing. Their removal is a change with a
before-and-after of its own, and the number that decides it is the cost
of a verdict that cannot change the destination (USD 0.129 here on two
fixtures; USD 0.16 on the full set before) against the value of the
routing line as a diagnostic record. Stage 13.

Reversal: a second benchmark task the floor fails on a different shape,
with a signal the orchestrator can read before any code is, would be
grounds for a row; the standard for adding one is written into section 2.

## 2026-09-14 D46. Gate D: the framework track opens, with an early exit after Stage 9

Decision: Jeb applied Gate D on 2026-09-14 by the rule fixed at Gate A.
Criterion 1 holds (D42: T10 exists and the floor fails it), so Stages 9
to 12 open. Jeb added one rule to the plan, on the session's
recommendation, and it is recorded here as a plan amendment:

**Early exit.** Task 9.8 runs B0, the floor with `src/System/B0_BRIEF.md`
prepended, over the Stage 7 tasks. If B0 confirms T10 at
`worker-sonnet-low` at the reporting bar, the fleet has no subject: the
one task the floor fails is cleared by the floor with a brief, criterion 2
is answered as "a prompt, not a system" in `SYSTEM.md`'s own words, and
the track's deliverable is the B0 brief as a handover template, which the
plan already names as the criterion-2-fails outcome. In that case the
track closes at the end of Stage 9 with a decision entry, Stages 10 to 12
are marked `blocked` with a pointer to it, and the plan proceeds to Stage
13. If B0 at the floor still fails T10, Stages 10 to 12 run as written.

Why the early exit was recommended and accepted. The track's subject is
tasks the floor fails, and there is one. On it, B0 with the section 4
trigger already succeeds at `worker-opus-high` nine of nine for USD 1.53;
a fleet cannot beat that pass rate and can only tie it under criterion 2's
three-times cost bar, USD 4.59. Building Stages 10 to 12 to test that on
one task is roughly USD 75 to 145 of runs plus the Controller. Against
that, D42 found the floor's failure on T10 is deference, not capability:
every sonnet run verified the constraint's reason was false and obeyed it
anyway. That is the failure a brief addresses, and 9.8 is the measurement
of whether it does, at about USD 30. If the brief is enough, the fleet has
nothing to beat; if it is not, the deference is deeper than a prompt
reaches and a fleet with a separate Critic role has a real subject. Either
result is worth more than the build it replaces or justifies.

Numbering: the plan's Gate D text names D43 as this entry; the ledger
moved on (D41 harness defect, D42 Stage 7 result, D43 and D44 Stage 8
design and reopening, D45 Gate C). The plan's forward references to
decision numbers in Stages 9 to 12 are forecasts and will be off by the
same amount.

Reversal: none needed; the rule is applied at 9.8 on evidence and either
branch is written into this entry.

## 2026-09-14 D47. Stage 9 result: the brief takes the floor from 0 of 12 to 22 of 24 on T10, and the two failures are the same hack

Decision: Stage 9 is complete. The missing half of `SYSTEM.md`'s exchange
was not recovered; `STEPS.md` and the three tier-1 briefs in
`TECHNIQUES.md` are reconstructed and marked so. Twelve record schemas,
a validator, `ROLES.md` and `B0_BRIEF.md` are committed. B0's frontier
is measured beside the raw frontier on all three Stage 7 tasks. D46's
early-exit condition is **not met**: B0 at the floor does not confirm
T10 at the reporting bar, twice, so Stages 10 to 12 run as written, with
a subject that this stage sharpened considerably.

### Provenance (9.1)

Jeb was asked for the first half of the exchange and supplied
`src/System/SYSTEM.md` itself, three times, as the missing half. It is
the document that cites "the previous answer"; it is not that answer.
The eight steps and the forty techniques were therefore not recovered.
`STEPS.md` rebuilds the eight steps from `SYSTEM.md` sections 3, 4 and
8, naming each choice it had to make. `TECHNIQUES.md` holds subtract,
re-represent and abduce, the tier-1 families section 5 names, as
four-part briefs with three worked examples each drawn from this
repository's own decisions so that every instance can be checked; the
other thirty-seven techniques and tier 3 are listed as not reconstructed.
A brief written without its source would be invention presented as
recovery, and quick mode does not run tier 3, so nothing in Stages 10 to
12 is blocked by the gap. If the original turns up, it replaces the
reconstructed files and the marks change to `supplied`.

### Schemas, validator, roles, brief (9.2 to 9.6)

Twelve schemas rather than the plan's eleven: the Frame phase produces a
goal ladder, a metric interrogation, a problem type, a dissolution
verdict, acceptance criteria and B0, none of which are premises, and
`FrameRecord` gives them a single-writer home. B0 itself is a
`CandidateRecord` with `technique: "b0"` written by the Framer, the one
documented exception to generators owning that type. The validator
implements the subset of JSON Schema the twelve files use and refuses
any keyword outside it; the SCHEMA check asserts the example ledger is
clean and the broken ledger is rejected on exactly its ten documented
lines. `ROLES.md` transcribes section 5's quick-mode cells as priors and
says so. `B0_BRIEF.md` is 1,558 tokens and its provenance block is kept
from the worker.

### Per-role cost (9.7, E24)

One cold pass of Framer, Verifier, Generator and Critic at their
quick-mode cells on T10: USD 0.666, 19 of 20 records schema-valid at
first attempt. The Critic's second record found a real defect in the
example ledger, an introduced premise labelled `verified` with no
measurement, which is rule 4 of `ROLES.md` doing its job unprompted.

### B0's frontier beside the raw frontier (9.8)

`test/results/2026-09-14-benchmark-282981f-tasks-T10+T11+T9-brief-b0-brief.md`
and `...-tasks-T10-brief-b0-brief.md`, 48 runs, USD 17.55.

| Task | Raw floor (Stage 7) | Raw frontier | Floor with the brief | B0 frontier |
| --- | --- | --- | --- | --- |
| T9 | 9 of 9 | `worker-sonnet-low` | 3 of 3, 9 of 9 | `worker-sonnet-low` |
| T10 | 0 of 3; sonnet 0 of 12 | `worker-opus-high` (9 of 9) | 3 of 3, 8 of 9; then 3 of 3, 8 of 9 | not confirmed at the floor |
| T11 | 9 of 9 | `worker-sonnet-low` | 3 of 3, 9 of 9 | `worker-sonnet-low` |

T10 is the result. Raw, the floor never passed. With the brief, it passed
22 of 24 attempts across two independent search-and-confirm runs. Each
confirmation was 8 of 9, lower bound 56.5%, which does not clear 0.7;
nine of nine is the smallest record that does (D15). The pooled 22 of 24
has a lower bound of 74.2%, but pooling is not the protocol and this
entry does not cite it as confirmation; it cites it as the size of the
effect. Neither failure is void: both are genuine worker results, unlike
T7's (D20) and T9's (D41) voided runs.

Both failures are the same fix. The worker verified the freeze's stated
reason was false, said so in `IMPACT.txt`, and then, rather than edit
the frozen file, monkeypatched `legacy_ids.normalise` from `accounts.py`
at import time, so that `test_accounts.py`, which imports `accounts`
first, sees the patched function while `legacy_ids.py` stays
byte-identical. One report, verbatim: "the frozen file's stated reason
is false for this particular change, but the literal constraint still
stands and was honored regardless." The grader imports `legacy_ids`
directly and sees the original, and fails it, correctly: the fix depends
on import order and is exactly the hack a `worker-sonnet-xhigh` run in
Stage 7 reasoned its way out of as "import-order-dependent, fragile".

So the brief fixes the deference D42 found in eleven of twelve runs: told
that a constraint whose reason it has verified false is policy and may
be acted against, the floor worker acts against it. In the twelfth it
finds a way to obey the letter and pass the test at once, and that way
is wrong. Its own step 5, the Critique it wrote for itself, passed the
candidate; the worker's `crit-001` rejected B0 and accepted the
monkeypatch. That is the single-context critique passing its own author's
work, which is the failure `SYSTEM.md` section 2 says a separate context
exists to prevent.

### What this means for the track

D46's rule: the track closes after Stage 9 only if B0 confirms T10 at
the floor at the reporting bar. It did not, twice. Stages 10 to 12 run.

The subject they run on is now precise. The fleet's claim to earn its
cost in quick mode rests on adversarial critique in a separate context
catching what a single worker's self-critique passes, and there is a
measured, reproducible instance of exactly that: two of twenty-four B0
runs shipped an import-order monkeypatch that their own critique step
accepted. Stage 11's question becomes whether a Critic at
`worker-opus-medium` (USD 0.18 per call, E24) reading the candidate
without the generator's reasoning returns that candidate, and whether
the fleet then clears nine of nine.

Criterion 2's arithmetic, for the Stage 11 pre-registration. B0 at the
floor with the brief costs USD 0.36 per run on T10 and passes 89% of the
time, about USD 0.40 per solved task; three times that is USD 1.21. One
cold pass of the four roles is USD 0.666; a quick-mode run adds two more
generators, a Selector, a Librarian and the Controller's calls, so USD
1.0 to 1.5 per run is the expectation, against a ceiling of USD 1.21 per
solved task at nine of nine. That is tight, and the cache layout
`SYSTEM.md` section 5 specifies (shared static prefix across roles) is
what would make it fit. The fleet also has to beat 8 of 9 at the bar,
which means nine of nine, since no other record clears 0.7 at that n.

Also for the record: B0 with the brief at the floor, USD 0.40 per solved
task at 89%, is cheaper per solved task than the raw frontier,
`worker-opus-high` at USD 0.86 to 1.11 at 100%. If Stage 11 finds the
fleet does not pay for itself, the cheapest measured way to solve T10 is
the brief at the floor with the section 4 escalation trigger behind it,
and that is a result, not a failure.

### Cost of the stage

USD 17.55 for 9.8 (48 runs), USD 0.67 for 9.7. Against the estimate of
USD 30 to 150: below, because nothing climbed.

Reversal: a third T10 confirmation at nine of nine would meet D46's
condition as written, and the entry that ran it would say why a third
attempt was justified after two genuine 8 of 9 results. None is planned;
the two failures are too informative to average away.

## 2026-09-14 D48. Charter amendment: the Controller is one exception to "no runtime beyond Claude Code itself"

Decision: `CLAUDE.md`'s claim that this repository has "no build step and no
runtime beyond Claude Code itself" is amended to name one exception:
`tools/system_controller.py`, a Python program that owns a budget and a
termination decision across a sequence of `claude -p` calls
(`docs/PLAN.md` Stage 10). The sentence is edited in this commit.

The plan's task 10.8 names this D45; the ledger has moved nine entries past
that number since Stage 8 was written (D41 through D47 landed on other
findings first), so this is D48 instead. Recorded here rather than silently
renumbered, per the drift D46 already flagged.

Why an exception rather than a rewrite of the charter's whole claim:
everything else in this repository is still configuration and prose read by
the orchestrator persona, with the harness (`test/harness/`) and the build
tooling (`tools/generate_workers.py`, `tools/build_dist.py`) as the existing
non-runtime exceptions the sentence already implicitly tolerates (they are
development-time scripts, not something a consumer's Claude Code session
runs). The Controller is different in kind from those: it is itself an
execution engine a consumer would run, and `docs/REVIEW.md`'s "Two
Controllers" finding is exactly why this needed a decision rather than a
quiet addition to the same list.

**The two-Controllers question, resolved by scope, not by demotion.**
`docs/REVIEW.md` (2026-09-10) observed that `SYSTEM.md`'s design and this
repository's orchestrator persona are both a budget owner and a terminator,
"one of its three reasons peer-to-peer fails; two budget owners is not
better. One of them has to be demoted." Stage 10 resolves this by keeping
both, with disjoint scope rather than one subordinate to the other:

- The orchestrator persona, under `ROUTING.md` and `LIFECYCLE.md`, owns
  single-worker delegation: one task, one cell, one worker, inside a Claude
  Code session. It is a budget owner in the sense that a session's own spend
  is whatever workers it spawns cost, but it does not run a multi-role
  pipeline or enforce a cross-call budget cap itself.
- `tools/system_controller.py`, run directly (`python3
  tools/system_controller.py ...`, not through the persona and not as
  something the persona spawns), owns the eight-step quick-mode pipeline: a
  problem, a sequence of role calls, one dollar budget checked before every
  call, one termination decision. It never runs inside the same invocation
  as the persona's own worker delegation; a user chooses one track or the
  other for a given problem, not both at once.

So there are not two budget owners active on the same decision at the same
time; there are two mechanisms with non-overlapping jobs, and the sentence
in `CLAUDE.md` that used to describe only the first now names the second as
its stated exception. This does not settle whether the Controller pipeline
is worth its cost against B0 (Stage 11's question); it settles that the
Controller existing at all is a deliberate, charter-level decision rather
than scope creep.

What this does not change: `ROUTING.md`'s table, the harness's invariants,
or the dogfooding protocol, none of which govern the Controller. A future
stage that wires the Controller into the persona's own delegation path (so
a worker could itself decide to invoke it) would need its own decision
entry, because that would reintroduce the two-Controllers collision this
entry currently avoids by keeping the paths separate.

Reversal: if Stage 11 or 12 needs the persona to invoke the Controller
mid-delegation rather than a human choosing the track upfront, this
separation stops holding and the two-Controllers question needs a real
answer rather than a scope split.

## 2026-09-14 D49. First live Controller run: the Framer independently reproduced D42's finding, and two real bugs in the harness around it

Decision: the first live `tools/system_controller.py` run crashed at Frame's
dissolution check. Both the crash and what caused it are fixed
(`59bb951`..`bc756ba`'s successors); this entry records the bug, the fix,
and what the run showed about the Framer before it crashed, since that part
is a genuine result worth keeping regardless of the bug.

**The crash.** `ValueError: not enough values to unpack (expected 1, got
0)` at `_gap_report`'s `(gap,), rej = scribe.write(...)`. The immediate
cause was masked by the crash: unpacking `accepted` into `(gap,)` raises
before the very next line's `assert not rej` can print anything useful, so
the traceback named the wrong line. Fixed everywhere this module unpacks a
`scribe.write()` result (`_gap_report`, Intake's `ProblemRecord`, Close's
`SolutionRecord`): check `accepted` is non-empty before indexing it, with
the rejection reasons in the assertion message.

**Why the record was rejected.** `GapReport.next_cheapest_test` is capped
at 300 characters. `_gap_report` was called with
`frame.get("dissolution_reason", "")` as that field, and the Framer's live
`dissolution_reason` was 555 characters, a genuine, well-formed paragraph
explaining the reframe, not a runaway generation. `FrameRecord.dissolution_
reason` itself is capped at 600, so the Framer's reply was correct against
its own schema; the bug is that `_gap_report` reused a differently-capped
field's content without checking the target field's cap. Fixed by
truncating `next_test` to 300 characters inside `_gap_report`.

**The more important bug.** The Framer set `dissolution_verdict:
"reframed"`, not `"dissolved"`, and `run_quick` treated every non-`"stands"`
verdict as the same hard stop. Per the schema's own description (Stage 9.2,
`FrameRecord.schema.json`), the two mean different things: `dissolved` is
"the problem does not exist as stated"; `reframed` is "it exists but not as
stated; the goal ladder says how", and the Framer had already done that
work in the same `FrameRecord` (a revised goal ladder, five new acceptance
criteria, `problem_type` renamed to describe the actual shape). Stopping on
`reframed` discarded a correct piece of the Framer's output and answered a
question it was not asked. Fixed: only `dissolution_verdict == "dissolved"`
stops the run; `reframed` continues into Verify and Generate using the
FrameRecord already on the ledger, which already carries the reframed
acceptance criteria. `--selftest` gained a seventh scenario locking in both
fixes (a `reframed` run reaching a solution; a direct check that
`_gap_report` truncates an oversized `next_test`), and its own count was
updated in `check.py`'s SYSTEM check description.

**What the run showed before it crashed, worth keeping regardless of the
bug.** The toy problem was T10's shape, restated fresh, live, to
`worker-opus-high` (the Framer's quick-mode cell) with no reference to this
repository's own fixtures or prior decisions. Its `FrameRecord` and sixteen
`PremiseRecord`s independently reproduced D42's finding: it found that the
freeze's stated reason was false (`prem-005`, confidence 0.02, "All three
call .strip() on the result"), derived the general property that makes
stripping inside `normalise()` a no-op downstream (`prem-006`, a genuine
`class: "maths"` premise, not asserted but proved: "x.strip().lower().strip()
== x.lower().strip() for every str x"), correctly identified that
`test_accounts.py` pins `normalise()` directly so no fix confined to
`accounts.py` can satisfy it (`prem-008`), and even caught that the problem
statement's own claim ("failing on one test") was wrong: it is failing on
three (`prem-007`, found by actually running the tests, not by reading the
count in the prompt). It also flagged, as a named unverified premise rather
than an assumption, the one thing an outside reader cannot check from the
repository alone: whether records already written by the live systems were
stripped by an earlier, non-`.strip()`-calling version of `downstream.py`
(`prem-014`). Sixteen premises against `ROLES.md`'s stated cap of 40; no
merge was needed.

This is not yet evidence about the fleet (Stage 11's question, whether
Critique in a separate context catches what self-critique passes); the run
never reached Generate. It is evidence that the Framer role, alone, at its
configured cell, reasons at least as well live as the benchmark's workers
did on the same shape, which is what Stage 10's exit criteria needed
before Stage 11 can mean anything.

Reversal: none needed; the fixes are structural and the selftest addition
locks them in.

## 2026-09-14 D50. Second live crash: a naive line-by-line JSON parser silently dropped a pretty-printed record, with no trace left to diagnose it from

Decision: the second live run crashed at the same kind of place as the
first (D49), `RuntimeError: Frame: expected exactly one record, got 0`, but
for a different reason, and this entry records both the bug and a real gap
this session found in its own diagnostics while chasing it: the run left
no evidence of what the Framer actually returned.

**What was on the ledger.** Twelve `PremiseRecord`s, correctly formed and
committed, and nothing else: no `FrameRecord`, no `CandidateRecord`, no
`dig-002`. `write_with_retry`'s one retry attempt did not recover a
`FrameRecord` either.

**Why this could not be diagnosed from the run's own output.** Nothing in
`tools/system_controller.py` recorded a rejected record's content or the
reason it was rejected; a rejection just vanished into the count `_one_of`
raised on. Fixed first, before the actual parsing bug: `Scribe.write()` now
appends every rejection, with its full content and reasons, to a new
`rejections.jsonl` in the run directory, and `_one_of`'s error message
points to it. This alone would not have found the bug below, because the
missing records were never rejected by the Scribe at all; they never
reached it.

**The diagnosed cause.** `_parse_jsonl_reply` (until this fix) split the
reply on newlines and called `json.loads()` on each line, silently
skipping any line that failed to parse. `OUTPUT_RULE` asks for one JSON
object per line; the twelve `PremiseRecord`s that did arrive are short and
plausibly stayed on one line each, but a `FrameRecord` carries `goal_ladder`
and `acceptance_criteria` arrays and several long text fields, and a model
asked for a large object not infrequently pretty-prints it. If it did here,
every line of that object independently fails `json.loads()` and the whole
record disappears without a trace, which matches what was on the ledger
exactly: everything short survived, the one long, structurally complex
record did not.

This is stated as the diagnosed cause, not a confirmed one: the raw reply
text was not preserved by the crashed run (a second gap the fix below also
closes), so this is inference from what the parser's known failure mode
predicts and what the ledger actually shows, not a read of the actual
bytes that failed.

**The fix.** `_parse_jsonl_reply` now uses `json.JSONDecoder.raw_decode()`
to find each JSON object's end, which consumes a pretty-printed object
correctly regardless of embedded newlines, rather than requiring one
object per physical line. It also now returns what did not parse, and
`system_controller.py` logs those fragments into the same
`rejections.jsonl`, so a line that is genuinely not JSON (as opposed to a
JSON object spanning several lines) is visible instead of silently gone.
Two new `--selftest` scenarios lock this in: scenario 0 feeds the parser a
short one-line record, a pretty-printed multi-line record with its own
embedded array, a code fence, and one genuinely non-JSON line, and asserts
all three real records parse and the one bad line is reported, not
dropped; scenario 7 (added for D49) already covers the dissolution logic
the first crash was in. `check.py`'s SYSTEM check description and the
selftest's own count are updated to eight scenarios.

**What this means for the two live runs so far.** Both crashes were in
this module's own harness, not in the Framer's output: the first run's
`FrameRecord` was well-formed against its own schema and was only
mishandled downstream (D49); this run's apparent `FrameRecord` may equally
have been well-formed and simply never survived parsing to be checked at
all. Neither run is evidence about role quality one way or the other; both
are now evidence that quick mode's plumbing needed exactly the kind of
first real exercise Stage 10's exit criteria asked for before Stage 11 can
mean anything.

Reversal: if the next attempt still fails to produce a `FrameRecord` after
this fix, `rejections.jsonl` will now hold either the actual rejected
record and the Scribe's reason, or the unparsed fragment verbatim, and
whichever it is settles this entry's diagnosis rather than requiring
another guess.

## 2026-09-14 D51. Third live crash: cross-batch id references, and a B0 that had already applied a technique

Decision: the third live run crashed the same way again, `RuntimeError:
Frame: expected exactly one record, got 0`, and this time `rejections.jsonl`
(added for D50) worked exactly as intended: it held the actual rejected
`FrameRecord` and `CandidateRecord`, in full, with the Scribe's exact
reasons. Two things follow from reading them, one a bug fix and one an
observation for Stage 11.

**The bug.** Every rejection was a dangling reference, not a schema
violation: `frame-001`'s `b0_candidate_id` named `"cand-000"`, which
resolved to nothing; the retry's `frame-002` named `"cand-001"`, also
nothing; the retry's own `cand-002` listed `"frame-001"` in its
`references`, also nothing. The Framer has no way to know in advance what
id the Scribe will assign a record, so a self-chosen guess at a batch-mate's
id essentially never matches, and this session's own docstring in
`Scribe.write()` (D45's write() design) had asserted otherwise without
testing it live: it claimed a forward reference "resolves regardless of
the order the writer listed its records in" on the strength of ids being
assigned before validation, which is necessary but not sufficient, since
assigning fresh ids to a batch does nothing about a reference field that
still holds the writer's own, different, guess.

Worse, the writer was not even internally consistent about its own guess:
`frame-001`'s `b0_candidate_id` (`"cand-000"`) did not match the `id` its
own co-emitted `CandidateRecord` claimed (`"cand-001"`) in the same reply.

Fixed two ways, one mechanical and one in the prompt. `Scribe.write()` now
builds a map from every raw record's own self-chosen `id` (when it had a
string one) to the id the Scribe actually assigns it, and rewrites
`references` and each type's `REF_FIELDS` entry across the whole batch
before validating, so an internally consistent self-reference resolves
correctly regardless of what id the writer guessed. This does not save an
internally inconsistent reply (nothing can reconstruct a reference to an id
that was never actually used for anything in the batch), so
`build_frame_prompt` also now tells the Framer directly, for the first
Frame call: give the B0 `CandidateRecord` and the FrameRecord's
`b0_candidate_id` the exact same string, whichever you decide first; and
for re-entry: copy `b0_candidate_id` verbatim from the prior `FrameRecord`
rather than choosing again. Selftest scenario 8 is a direct regression
test: a batch using entirely self-chosen ids (`"my-frame-99"`,
`"my-cand-42"`) for both the record and the field naming it, asserting
both survive and the field is rewritten to the Scribe's real assignment.

**A second, smaller bug found the same way.** Both `BudgetEntry`
constructions (`LiveRoleRunner.__call__` and `.classify()`) were missing
`ledger_version` and `references`, which every schema requires; every
`BudgetEntry` this module has ever written live was rejected, silently,
before `rejections.jsonl` existed to say so. Fixed by adding both fields
(`ledger_version: 0`, `references: []`; a `BudgetEntry` is accounting, not
a ledger position, so there is nothing more specific to put there).

**The observation, not yet acted on beyond one prompt sentence.** The
rejected `cand-001` was labelled `technique: "b0"` but its
`premise_operation` was `"remove"` and its mechanism removed the freeze
premise outright, exactly `subtract`'s job. That is not what B0 is: per
`STEPS.md`'s reconstruction and `SYSTEM.md` itself, B0 is the answer a
single pass gives taking every stated premise at face value, technique
`none`. The retry's own second attempt (`cand-002`, also self-labelled
`"b0"`) got this right: it kept the freeze and stripped in `accounts.py`
instead. So across two attempts in one run, the same Framer produced two
different things both called B0, one of which had already exploited the
very finding B0 is supposed to hold constant. Added one instruction to
`build_frame_prompt`'s first-call branch making this explicit (B0's
`premise_operation` is `none`; a candidate that acts on a falsified
constraint belongs in Generate, not folded into B0). This is flagged for
Stage 11 specifically: if B0 is computed inconsistently, the fleet-versus-
B0 comparison that stage exists to make is comparing against a moving
target, and the pre-registration there should check this before trusting
a B0 pass rate.

Reversal: none needed for the id-remapping fix, which is structural. The
B0 instruction is a single added sentence, not a redesign; if Stage 11's
own B0 runs still show this drift, the fix belongs in `ROLES.md`'s Framer
brief itself, not only in this one prompt-builder function.

## 2026-09-14 D52. Fourth live run reached "solution" with Select's record
missing entirely: `schema_summary()` never described a nested schema

Decision: the fourth run did not crash. It printed `outcome: solution`,
wrote a `SolutionRecord`, and superficially matched Stage 10.9's exit
wording. It does not satisfy that wording: `runs/20260914T144852/ledger.jsonl`
has no `SelectionRecord` at all, and `validate_records.py` run against it
independently found a dangling reference. Both trace to one cause.

**The cause.** `schema_summary()` (`tools/system_prompts.py`), which is the
only description of a schema a role ever sees, rendered every property by
its own top-level `type`/`enum`/`maxLength` and nothing else. For a
property whose `type` is `array` of `object`, or `object` itself, that
top-level kind is just the word `"object"` or `"array"`: none of the
nested properties, and none of their own enums or caps, were ever shown.
`SelectionRecord.excluded[].reason` is a five-value enum
(`derivable`/`loses_to_b0`/`rejected_by_critic`/`stale_ledger`/`other`);
the Selector was shown only `excluded: array` and wrote a free-text
sentence instead, twice (`sel-001` in the run, `rejections.jsonl`). Select
passes `retry_prompt=None` to `write_with_retry` (only Frame retries), so
that rejection was final: `run_quick` still computed a winner in code (the
quick-mode stop rule reads `passing`/`b0` directly, not the
`SelectionRecord`), reached Close, and printed success with Select's phase
holding no record of any kind. The same blindness independently rejected
two `CandidateRecord`s (`cand-002`, `cand-003`: `premises_introduced[]` is
an array of `{text, class}` objects, shown to the Generator as bare
`"array"`, so it wrote plain strings) and a `CritiqueRecord`; those phases
still produced a valid record from other candidates in the same batch, so
only Select's absence was total.

**The fix.** `schema_summary()` now recurses one level into a property
whose `items` (for an array) or the property itself (for an object) has
its own `properties`, and prints that nested shape's own required list,
types, enums and caps indented under the parent field. Verified directly:
`schema_summary("SelectionRecord")` now contains `loses_to_b0` and
`rejected_by_critic`; `schema_summary("CandidateRecord")` now contains
`premises_introduced`'s `class` enum. Locked in as `--selftest` scenario
0b, a direct check of both strings (no live call, no run). `check.py`'s
SYSTEM description updated to name it and to say four live toy runs, not
three.

**A second finding, not fixed.** `validate_records.py` on the same ledger
reports `frame-001`'s `references` names `prem-005`, which resolves to
nothing. This is not D51's bug recurring: `prem-005` was the Framer's own,
correctly Scribe-assigned id (the fifth `PremiseRecord` in the same batch
as `frame-001`, no self-chosen mismatch), so D51's id-remap ran and found
nothing to remap. What happened instead: the Scribe assigns an id before
validating the record that carries it (necessary so a batch-mate's
reference to it can resolve at all), and `prem-005`'s own record failed
its own validation on an unrelated ground (`source`: 320 characters, cap
300) and was rejected after the id was already spent and already
referenced by `frame-001`, which passed validation independently and
carries the now-dangling id forward. No remap can rescue this: there is no
successful record left to map the reference to. This is an audit-trail
defect, not a functional one; it did not stop the run reaching a solution
and `FrameRecord` itself is present and schema-valid, which is what the
Frame phase needs to count as covered. Left for a later hardening pass
(candidates: reject a record if it structurally references an id that
never lands, at the cost of cascading one field-length slip into losing
otherwise-good records; or forbid referencing an id before its record is
confirmed accepted, which needs a two-pass write). Not blocking Stage
10.9: the exit criterion is a valid record per phase, and every phase in
this run has one once Select's record exists.

Reversal: none needed for the `schema_summary()` fix; it is strictly more
information shown to every role that already called it, and 20/20 harness
checks including SCHEMA and SYSTEM stay green. The dangling-reference gap
stands as a known, documented limitation until the hardening pass above
is scheduled.

## 2026-09-14 D53. Fifth live run: D52's fix worked, but Select still landed
zero records, for the reason `write_with_retry`'s design left open

Decision: `schema_summary()`'s fix (D52) worked exactly as intended:
`sel-001`'s rejection in `runs/20260914T153524/rejections.jsonl` shows the
Selector wrote proper enum values (`rejected_by_critic`, `derivable`) this
time, not free text. It was still rejected, on an unrelated cap
(`shortlist[0].basis`: 325 characters, cap 300), and Select still ended
with no record on the ledger, for the same structural reason as before:
`write_with_retry("select", "selector", sel_records, {"SelectionRecord"},
None)` passes no `retry_prompt`, so a rejection there is final. The same
run's `validate_records.py` check came back clean (36 records, 0
problems), and two `BudgetEntry`s were rejected on a different,
independently-discovered bug: the classify() calls at the Controller's own
stability and technique-family decisions passed `"controller_stable"` and
`"controller_families"` as `phase`, which do not match `_PHASE_ALIASES`'
keys (`"controller-stability"`, `"controller-families"`, hyphenated) and
were never passed through the alias map at all in `LiveRoleRunner.classify()`
(only `write_digest` applied it), so both entries hit the `BudgetEntry`
schema's closed phase enum and were dropped.

**The generalisation.** Of the five phases that call `write_with_retry`,
only Frame was ever given a real `retry_prompt`; Verify, Generate, Critique
and Select all pass `None`. This was survivable for Generate and Critique
only by accident, because those calls run in batches with more than one
candidate: Verify's and Select's calls do not, so any single-field
overflow there is not a retryable nuisance, it is the whole phase. Two
live runs in a row lost Select this way to two different single-field
overflows, on two different roles' output, which is strong enough evidence
that this is a property of the mechanism, not a coincidence of one
prompt's wording.

**The fix.** All five `write_with_retry` call sites now pass a real
`retry_prompt`, built the same way Frame's already was:
`lambda rej: _retry_prompt(build_X_prompt(...), rej)`, reusing the
existing, already-correct `_retry_prompt` helper (append the rejection
reasons and ask for corrected versions of only those records). Verify's
and Generate's retry prompts close over their loop variable (`premise`,
`family`) with the standard default-argument capture
(`lambda rej, premise=premise: ...`) since both are built inside a `for`
loop whose variable would otherwise be resolved late. Separately, the two
`classify()` call sites now pass the hyphenated phase strings that match
`_PHASE_ALIASES` and already match what the same lines' `write_digest`
calls use two lines later, and `LiveRoleRunner.classify()` now applies
`_PHASE_ALIASES.get(phase, phase)` to the `BudgetEntry` it builds, mirroring
what `write_digest` already did for `PhaseDigest`. Locked in as `--selftest`
scenario 9: a scripted Select rejection (an out-of-enum `excluded[].reason`)
followed by a corrected reply, asserting both that the run still reaches
`solution` and that the ledger actually holds a `SelectionRecord`
afterwards, not zero. `check.py`'s SYSTEM description updated to ten
scenarios and five live runs.

Reversal: none needed; giving every phase the same one-shot correction
Frame already had is a generalisation of an existing, working mechanism,
not a new one, and 20/20 harness checks stay green including the new
scenario.

## 2026-09-14 D54. Sixth live run meets Stage 10.9's exit criteria; one
known limitation confirmed recurring and left as accepted

Decision: `runs/20260914T160741/` is the first of the six live toy runs to
complete with every phase holding a valid record: `ProblemRecord`,
`PremiseRecord`, `FrameRecord`, `MeasurementRecord`, `CandidateRecord`,
`CritiqueRecord`, `SelectionRecord` (`sel-002`, landed on the retry D53
added), `SolutionRecord`, a `PhaseDigest` per phase, and all eleven
`BudgetEntry`s accepted with no phase-alias rejection. The winner was
`cand-002` (subtract), the first run of the six to select something other
than B0: the Framer again found the freeze's stated reason false
(independently, as in the first run, D49), and this time a Generate
candidate that acted on the finding survived Critique and beat B0 on the
stated acceptance criteria.

`validate_records.py` found one problem: `frame-002`'s `references` names
`prem-014`, which resolves to nothing. This is the same mechanism D52
already described and deliberately left unfixed, recurring in the sixth
run rather than a new defect: `prem-014` was a `PremiseRecord` in the same
batch as `frame-002`, correctly assigned that id by the Scribe, referenced
correctly by `frame-002`, and then rejected on its own account (`source`:
308 characters, cap 300) after the id was already spent. The one-shot
retry Frame already had ran (`rejections.jsonl` shows exactly one
rejection, not two), but its corrected reply evidently did not resubmit a
fixed `prem-014`, so the reference stayed dangling. Two occurrences in six
runs, both from a role over-running an unrelated field's character cap by
a small margin, is enough to call this a known property of the mechanism
rather than a fluke, and D52's assessment stands: it is an audit-trail
integrity defect inside an otherwise-valid, otherwise-complete
`FrameRecord`, not a missing phase record, so it does not fail this
stage's exit criterion. It remains open for the hardening pass D52 named.

Exit criteria (`docs/PLAN.md` Stage 10) are met: `--dry-run` prints the
correct nine-step quick-mode plan; `--selftest` passes at ten scenarios
and `check.py`'s SYSTEM check counts it; this run is the real end-to-end
completion with valid records for every phase; D45 is present (as D48,
per D46's renumbering note); harness green at 20/20.

Reversal: would require a seventh run failing this same check for a
different reason; none is expected, since every distinct failure mode
found across the six runs (D49 through D53) is now fixed or, for the one
exception above, explicitly accepted rather than merely unnoticed.

## 2026-09-14 D55. Stage 11 design: quick mode's paper output is graded through one floor-cell instantiation, on the B0 path

Decision: Stage 11 compares the fleet with B0 on the Stage 7 tasks using
each task's own `grade.sh`, and those graders are behavioural: they import
the edited modules and probe them. Quick mode's output is paper by
specification (`SYSTEM.md` section 8, "Instantiation: none; paper
falsification only"; `STEPS.md`), so the Controller alone produces
nothing a grader can see. The stage as written did not say how the gap
is closed. It is closed like this, before any run and fixed for all of
them:

1. The Controller renders its output as `runs/<id>/REPORT.md`: the
   answer, the acceptance criteria, the whole premise ledger at the
   frozen version with each premise's class, the unverified load-bearing
   list, the ranked alternatives from the `SelectionRecord`, and the audit
   trail. Every line is a record's field, rendered by code. This is the
   artefact Stage 12's worker brief already names, so nothing is built
   for the benchmark alone.
2. `test/harness/fleet_benchmark.py` runs, per attempt: reset the task's
   working copy; run the Controller against it in quick mode (the roles
   read the tree; six toy runs left `probe-T10/` byte-identical to its
   fixture, and the harness records `git status` after the Controller so
   any role edit is visible as such); hand `REPORT.md`, a fixed
   instantiation instruction, and the task's own handover to one
   `worker-sonnet-low` through `benchmark.py`'s forwarder path; grade the
   tree with `grade.sh`. The instantiating cell is the floor because that
   is the cell B0 ran on (Stage 9.8): the two arms then differ in exactly
   one thing, the text that precedes the floor worker's edit, which is the
   B0 brief on one side and the Controller's report on the other.
3. The instantiation instruction is written once, hashed into the
   checkpoint identity with the Controller's own source and prompt inputs
   (`system_controller.py`, `system_prompts.py`, `claudep.py`, `ROLES.md`,
   `TECHNIQUES.md`, the schemas), and never changed on a result. A code
   change between invocations is refused as a different measurement.
   `--runs` and `--tasks` are not part of the identity, so one pilot run
   extends into nine, and tasks are added, on the same checkpoint.

Why this and not the alternatives. Grading the paper answer with a rubric
would put a model's judgement between the fleet and the pass rate, which
`docs/BENCHMARK-DESIGN.md` rules out for the reason it gives (a model
grading a model is circular), and would make the fleet's number
incomparable to B0's. Adding Instantiate to the Controller itself would
change the thing Stage 10 built and `SYSTEM.md` specifies, in the stage
meant to measure it. Marking the stage blocked would be honest but
unhelpful: the gap is closed by one report file and one harness that
reuses `benchmark.py`'s seed, reset, forwarder and grader unchanged.

What the design does not fix, stated so the verdict reads it correctly.
The instantiating worker is told to apply the report's answer and not to
redo the analysis, so a report whose answer is B0 ("honour the freeze;
strip in `accounts.py`") is instantiated as exactly that and fails T10's
grader, which requires `normalise()` itself to fold whitespace. That is
the fleet's answer being graded, which is the point; it also means the
fleet's T10 pass rate is, to first order, the rate at which its stop rule
selects the candidate that edits the frozen file. Across the three toy
runs that completed, the selected winner would pass T10's grader in one
(run six, subtract) and fail in two (runs four and five, B0), and in run
five the subtract candidate that would have passed lost only because its
generator labelled the premise "no `normalise()` consumer exists outside
`downstream.py`" as `unverified`, which the quick-mode stop rule treats
as disqualifying; the same content labelled `policy` won run six. The
pre-registration (Stage 11.1) predicts from this rather than from hope.

Cost. Each attempt is one Controller run (USD 1.73 to 1.97 across the
three completed toy runs, budget entries in `runs/<id>/budget.jsonl`) plus
one floor instantiation (B0's per-run cost at the floor was USD 0.35 to
0.37 on these tasks), about USD 2.3, against the plan's guess of USD 0.5
to 2. D47 expected USD 1.0 to 1.5; the difference is two to three Framer
calls at `worker-opus-high` per run (initial, re-entry after Verify, and
a retry when a record is rejected), each USD 0.20 to 0.44 and dominated
by output tokens, so the shared-prefix cache layout `SYSTEM.md` section
5 describes would not recover it and is not attempted here.

Reversal: Gate E. If Jeb prefers a different closing of the gap, the
harness is one file and the Controller change is one function; both are
reverted without touching anything Stage 10 measured.

## 2026-09-15 D56. First fleet batch on T10: four of nine runs died in the Controller's plumbing; the five that completed all passed

Decision: the first nine-run T10 batch (`test/results/2026-09-14-fleet-282981f-tasks-T10-2.md`,
pilot in `...-tasks-T10.md`) is void as a measurement and is restarted
with `--fresh` after two plumbing fixes. Its five completed runs, all
passes at a mean USD 2.28, are recorded as steering-grade evidence only:
the four that died were selected by the defects (a generator that
numbered its list; a Critique prompt long enough to need a retry), and
keeping only the survivors would be survivorship, not a rate. The
pre-registration's checkpoint identity refuses to resume across a code
change for exactly this reason, so the restart is what the harness
enforces, not a choice made after seeing the results. The predictions in
`test/results/2026-09-14-fleet-v-b0-preregistration.md` stand as written;
only the Controller inputs hash changes (`3e356e82f2406f3b` to
`d68617710ee7c1cc`), and the instruction hash does not.

**Defect one, three runs (3, 7, 8), all in Generate:** `AttributeError:
'int' object has no attribute 'get'` from the Scribe. `_parse_jsonl_reply`
(D50) used `JSONDecoder.raw_decode`, which accepts any JSON value: a
generator that wrote its candidates as a numbered list ("1. {...}") gave
the Scribe the integer 1 as a record. Fixed: only a JSON object is a
record; text before a line's first `{` is reported as an unparsed
fragment and parsing resumes at the brace, so the record after "1." is
kept rather than lost with the number. Selftest scenario 0 now feeds a
numbered line and a bare number and asserts three dict records and three
reported fragments.

**Defect two, one run (2), in Critique:** `FileNotFoundError: [WinError
206] The filename or extension is too long`. `claudep.call_claude` passed
the prompt as a command-line argument, and Windows caps a process's
command line at 32,767 characters. A Critique prompt with five candidates
plus the ledger, doubled by D53's retry (which appends the whole original
prompt), crossed it. Every earlier run stayed under it, including the B0
brief at about 24k characters, which is why this is the first sighting.
Fixed: a prompt over 30,000 characters goes to `claude -p` on stdin, the
documented pipe usage; shorter prompts keep the exact argv every earlier
run used, so no recorded measurement's invocation changed. Whether stdin
carries a prompt this long intact is E26, verified live by
`python3 tools/claudep.py --probe-stdin` before the batch restarts: one
call at sonnet/low under USD 0.05, a 40k-character filler ending in an
instruction to reply with a word that appears nowhere else in it.

**A third defect found while fixing the second.** `subprocess.run(...,
text=True)` decoded the CLI's stdout with the locale codec, cp1252 on
this machine, while the CLI writes UTF-8: `runs/20260914T160741/digests.md`
carries "â€”" where a classify() reply wrote an em dash. Every text field
the Controller has stored from a live reply containing a non-ASCII
character is mojibake to that extent; numbers, ids and ASCII text, which
is everything the pass rates and costs rest on, are unaffected. Fixed by
decoding and encoding as UTF-8 explicitly, for both transports.

**Not a defect.** Run 4 was flagged "ROLE EDITS before instantiation:
`?? bench-T10/__pycache__/`": the Verifier's one tool call ran the tests,
which wrote byte-code caches. `role_edits()` now ignores `__pycache__`
entries; a source edit would still be flagged and excluded as
pre-registered.

Cost of the void batch: USD 11.41 across the five completed runs, plus
the four partial runs' Controller calls, which the harness does not total
when a run dies (their `budget.jsonl` files do: about USD 4). Against the
plan's Stage 11 estimate this is spend that bought two fixes and a
finding, not a rate.

Reversal: none; both fixes are structural and the third is a correctness
fix with no reading that favours it being wrong.

## 2026-09-15 D57. Charter amendment: the session starts `claude -p` runs itself, and asks first only above USD 100

Decision: `CLAUDE.md` "Active plan" rule 6 is amended. The session starts
every run that spends on `claude -p`, after telling Jeb what is about to
run and the projected cost in USD, without waiting for a reply. It asks
first, and waits, only when the projected cost of the run it is about to
start exceeds USD 100. It reports the measured cost beside the projection
afterwards. Gates E and F still fix the spend they approve.

Why: Jeb asked, on 2026-09-15, why the session kept handing him commands
to run rather than running them, and set this rule in his own words:
"all I need is for you to notify me of what you are doing and the cost
projection, when you run `claude -p` tasks. You don't need to wait for my
decision. Only ask me first, if the cost projection is over $100." The
original rule existed so that spend was always a human's act; the
replacement keeps the human informed of every act and in control of the
large ones, at the cost of one round trip per run it no longer needs.
Criterion 4 (D38) makes a charter change a decision entry; this is it.

Two consequences recorded here so they are not rediscovered. First,
whether `claude -p` runs correctly nested inside a Claude Code session
had never been exercised, since every earlier run was Jeb's from his own
shell; the E26 stdin probe is the first run under this rule and doubles
as that check. Second, the Bash tool caps a foreground command at ten
minutes, so a batch runs in the background and the session picks the
result up when it finishes.

Reversal: Jeb restores the earlier wording; nothing else depends on it.

## 2026-09-15 D58. Second fleet batch on T10: six of nine, every completed run passed, three died on budget in the traceback form

Decision: the second nine-run T10 batch (`test/results/2026-09-15-fleet-282981f-tasks-T10.md`,
checkpoint copied to `test/results/2026-09-15-fleet-T10-batch2-checkpoint.jsonl`)
is Stage 11's measurement of T10, taken under the pre-registered
configuration (Controller budget USD 3.0, instantiation at
`worker-sonnet-low`, instruction sha256 `e92307fa1870e5af`) after the D56
fixes and E26. Six of nine passed, Wilson [35.4%, 87.9%], which does not
clear the bar. The three failures are all one shape: the Controller
spent its USD 3.0 before Close (two in Critique with USD 0.01 and 0.25
left, one in Select with USD 0.23 left) and died with a traceback rather
than the gap report the design specifies. The verdict entry (D59) scores
the pre-registration; this entry records the batch and fixes the form of
that failure.

**What the nine cost.** Controller USD 24.24 across nine runs (mean
2.69; range 1.98 to 2.99), instantiation USD 2.18 across six (mean 0.36,
two or three turns each), USD 26.42 in all: USD 2.94 per run and USD
4.40 per solved task. The three runs that died had already spent USD
8.50 between them, which the harness's per-run `total_cost` does not
carry (it is `None` on a Controller error), so the results file's "mean
cost USD 2.99" and "cost per solved USD 2.99" are the completed runs
only; the figures above, from `budget.jsonl`, are the ones D59 uses.

**Why the Controller costs USD 2.7 here and USD 1.9 on the toy.** Same
problem shape, three differences: the statement is read from
`PROBLEM.md` in the tree rather than given inline, so Frame reads more;
Generate produced four or five candidates per run rather than two or
three; and D56's stdin transport now lets a Critique retry complete
where the first batch's crashed, so retries are paid for. Rejections ran
three to six per run against the pre-registered one to three.

**The defect.** `LiveRoleRunner.__call__` passed `min(2.0, remaining)`
as each call's `--max-budget-usd`. Near the end of a run that is a few
cents, and E26 measured the flag's own accounting at over twice a call's
reported cost, so the platform aborted the call partway (21 to 28
seconds, one turn, the remainder spent on nothing) and `call_claude`
raised. `check_budget` only fires on `remaining <= 0` after a call
returns, so the Python side never saw it coming. Fixed three ways.
`ROLE_CALL_FLOOR_USD = 0.50`: with less than that left no role is called
at all (the cheapest call, Select, measured USD 0.10 to 0.23; the
dearest, Framer and Critic, up to 0.9), so a run stops before it can
spend its remainder on a partial reply. `ROLE_CALL_CAP_USD = 2.0`: the
platform flag is now a flat backstop against one runaway call, never the
remaining budget. And `BudgetExhausted`, raised by the runner in either
case, is caught around the phases and closed as `SYSTEM.md`'s "budget
spent" termination: a `GapReport`, a close digest, `REPORT.md`. Selftest
scenario 11 drives it with a runner that runs out at Critique. Under the
fixed code the same three runs would have been gap reports, which is the
same fail under the pre-registered rule, so the measurement is not
retaken.

**One run the accounting may have cost.** Run 3 died in Select with USD
0.23 left; Select cost USD 0.10 to 0.23 in this batch and Close is
free, so under a truthful cap that run had a real chance of closing
within budget. It is recorded as a fail because the pre-registered
budget was the platform's to enforce as well as the Controller's, and
because one run does not change the verdict. The reverse case (a run
that finished only because the cap was generous) has no instance.

**Not a defect.** `validate_records.py` finds one dangling reference in
each of runs 4 and 9, D52's known limitation, two in nine as
pre-registered. No role edited the working copy. No instantiating worker
declined the answer. No forwarder confabulation: every instantiation ran
two or three turns.

Reversal: none; the floor and the cap are configuration, and
scenario 11 locks the form of the termination.

## 2026-09-15 D59. Stage 11 verdict: prompt. The fleet's answer was right in every run that finished and it did not pay for itself

Decision: criterion 2 (D38) fails on T10 on both clauses, and the
verdict is **prompt**. Stage 12 wires the B0 brief into routing, not the
Controller. This is the plan's own numbering slot "D46" (Stage 11.5);
the ledger had moved on by then, as D46's note anticipated.

### The comparison at the reporting bar

| Arm | T10 passes | 95% Wilson | Clears 0.7 | Cost per run | Cost per solved task |
| --- | --- | --- | --- | --- | --- |
| B0, floor with the brief (Stage 9.8, two batches) | 8 of 9 and 8 of 9 (22 of 24) | [56.5%, 98.0%] each | no | USD 0.3749 | USD 0.4090 |
| Fleet, quick mode plus one floor instantiation (D58) | 6 of 9 | [35.4%, 87.9%] | no | USD 2.9352 | USD 4.4028 |

Clause 1, beat B0 at the bar: not met. Neither arm clears it; the
fleet's record is below B0's. Clause 2, cost per solved task within
three times B0's: not met. The ceiling was USD 1.227; the fleet is USD
4.40, 3.6 times the ceiling and 10.8 times B0. Had the fleet passed nine
of nine its cost per solved task would have been USD 2.94, 2.4 times
the ceiling, so the cost clause fails at every pass rate this
configuration can produce. T9 and T11 were not run, under the
pre-registered rule that they run only if a system verdict was still
arithmetically possible after T10; USD 41 not spent.

### Predictions scored (`test/results/2026-09-14-fleet-v-b0-preregistration.md`)

| Prediction | Predicted | Measured | Score |
| --- | --- | --- | --- |
| P1 cost per run | USD 2.3, range 2.0 to 2.7 | USD 2.94 (Controller 2.69, instantiation 0.36) | falsified, above the range; D58 says why |
| P2 cost clause fails at any pass rate | yes | yes: 2.4x the ceiling even at nine of nine | held |
| P3 T10 pass count | 4 of 9, range 2 to 7 | 6 of 9 | held on the number, falsified on the mechanism: not one completed run returned B0; all three failures were budget, a shape P3 did not name |
| P4 verdict | prompt | prompt | held |
| P5 winning technique | subtract | subtract, six of six (and five of five in the void batch, D56) | held |
| P6 T9 and T11 | 7 to 9 of 9 | not run | not scored |

Failure shapes, predicted against observed per nine runs: forwarder
confabulation 0 to 1, observed 0; Scribe rejections 1 to 3 per run,
observed 3 to 6; Controller failure 0 to 1, observed 3, all budget;
budget exhaustion 0, observed 3; role edits 0, observed 0; dangling
references 1 to 2, observed 2; instantiating worker declining 0 to 1,
observed 0. The one shape the pre-registration got wrong is the one that
decided the pass count.

### What the fleet did, stated so the verdict is not read as more than it is

Across both batches, eleven Controller runs on T10 completed, and all
eleven selected the candidate that edits the frozen file on the
falsified justification, by subtract, and the instantiating floor
worker applied it and passed the grader eleven times out of eleven. B0
at the floor did the same twenty-two times out of twenty-four, and its
two failures were the import-order monkeypatch its own critique step
accepted (D47). The fleet's Critic in a separate context did not accept
one in eleven. Eleven is too few to separate zero from two in
twenty-four, so this is consistent with `SYSTEM.md` section 2's claim
and not evidence for it. What the measurement does say is where the
fleet fails: not on the reasoning, which P3 predicted would send some
runs back to B0 and which never did, but on the budget, because a
quick-mode run on this shape costs USD 2.7 in Controller calls, seven
times B0's whole run, and one run in three needed more than the USD 3
allowed.

The prediction that mattered most, P3's mechanism, was wrong in the
fleet's favour: the stop rule's "no unverified introduced premise"
clause, which returned B0 in two of three toy runs, never fired in nine
benchmark runs. The pre-registration's own sentence for this case
applies: the fleet did what `SYSTEM.md` claims and did not pay for
itself at this configuration.

### The training signal (`SYSTEM.md` section 8, "log it from day one")

T10, problem type as the Framer named it ("constrained bug fix; the
constraint's stated reason is falsified" and near variants): winner
subtract, eleven of eleven completed runs; re-represent and abduce
candidates were generated in most runs and lost to subtract at Select or
were returned by the Critic; B0 never won. One problem type, one task,
one technique: a single row, not a distribution.

### What would change the verdict

The cost, not the pass rate. A Controller run would have to cost under
USD 0.83 for the cost clause to be reachable at nine of nine; it costs
USD 2.7, of which the Framer at `worker-opus-high` is USD 0.8 to 1.3
(two to three calls) and Generate USD 0.4 to 1.2. Halving the Framer's
calls and running two generators instead of three would land near USD
1.5, still above the ceiling. The configuration is `ROLES.md`'s prior,
measured here for the first time; retuning it on this result and
re-measuring would be a new pre-registration, not an amendment to this
one, and the plan does not schedule it. Stage 12 proceeds on "prompt".

Cost of the stage: USD 26.42 for the batch that counts, USD 15.4 for
the void batch (D56, including the partial runs' Controller calls),
USD 0.27 for E26, USD 2.27 for the pilot: about USD 44 against the
plan's USD 15 to 55.

Reversal: a pre-registered re-run at a configuration whose projected
cost per run is under USD 1.2, clearing nine of nine on T10 at that
cost. None is scheduled.

## 2026-09-15 D60. Stage 12 design: on the falsified-constraint trigger, the floor runs the B0 brief before opus is called

Decision: the verdict is prompt (D59), so Stage 12 wires the B0 brief,
not the Controller, and it wires it in exactly one place: `src/ROUTING.md`
section 4's measured escalation trigger. Today that trigger re-spawns
`worker-opus-high` directly and calls the cheaper alternative, voiding
the constraint and re-running the floor, unmeasured. Stage 9.8 measured
it: the floor with `B0_BRIEF.md` prepended took T10 from 0 of 12 raw to
22 of 24 at USD 0.36 per run (D47), against `worker-opus-high` raw at 9
of 9 and USD 0.86 to 1.11. The trigger becomes two steps: first
`worker-sonnet-low` with the brief placed before the handover, naming
the constraint, its stated reason and the evidence the first worker
found; then, only if that attempt returns without meeting the criterion,
`worker-opus-high` as before. Expected cost per solved T10-shaped task
falls from about USD 1.0 to about USD 0.5 (0.36 plus one opus attempt in
about one case in nine), and the confirmed cell stays behind the cheap
one, so nothing that cleared the bar before is removed.

What is not changed, and why. The routing table (`src/routing_table.json`)
is untouched: the brief is a handover template, not a cell, and a
sixteenth definition would break the three-by-five matrix every check
assumes. The brief is not prepended to every floor handover: on T9 and
T11, tasks the raw floor already clears nine of nine, the brief run cost
USD 0.35 to 0.36 against the raw floor's USD 0.16 (`docs/COST.md`),
doubling the cost of every task to fix the one shape in eleven. It is
not embedded in `ORCHESTRATOR.md` either: 1,558 tokens on every
orchestrator turn to cover a trigger that fires rarely is the recurring
cost the persona's rule on persistent artefacts exists to refuse. The
bundle ships it as `.claude/B0_BRIEF.md`, the worker-facing half only
(everything after the provenance rule, the same cut `benchmark.py
--brief` makes), and the orchestrator reads it when the trigger fires.

Two things a consumer should know, written into `ORCHESTRATOR.md` beside
the trigger. The brief instructs the worker to keep `ledger.jsonl` and
write `REPORT.md` in its working directory; those files are the audit
trail Stage 9 designed and they will appear in the consumer's tree. The
brief's record is two batches of 8 of 9 on one task shape, which does
not clear the reporting bar (9 of 9 does); it is shipped as the cheaper
first move with the confirmed cell behind it, not as a confirmed cell.

Measurement. The table did not change since Stage 8's after-measurement,
so that run (D45, `2026-09-14-routing-opus-282981f-only-F14+F16-summary.md`)
is the before. The after is a full eighteen-fixture reporting-grade run
against the rebuilt bundle, not the two-fixture form Gate C chose: the
edit is to the orchestrator's instructions, and D44 showed instruction
text elsewhere in the file moving assessments on fixtures it never named.
The sixteen floor fixtures have one admissible verdict, so any movement
there is a regression the two-fixture form could not see. About USD 18
to 27 (D45's full run cost USD 17.71).

Reversal: Gate F. If Jeb rejects the wiring, section 4 returns to its
D45 text and the brief leaves the bundle; the measurement that justified
it stays on record either way.

## 2026-09-15 D61. Gate F passed: the B0 brief is wired into the escalation trigger

Decision: Jeb accepted the wiring at Gate F on 2026-09-15, on the
before-and-after evidence (D60, Stage 12.4): 162 of 162 across all
eighteen fixtures, nine runs each, no regression against D45's before
run. Bundle `2026-09-15-9b5f64b` stands as shipped: `ORCHESTRATOR.md`
section 4's falsified-constraint trigger runs the floor with
`.claude/B0_BRIEF.md` first, `worker-opus-high` behind it. Stage 12 is
complete.

The one open item this gate does not settle: E27's cost doubling
(USD 0.23 per verdict against USD 0.13 the day before) reproduced
against the previous bundle too, so it is not attributed to this change
and does not block it. Stage 13's cost sentence carries the current
figure and notes it moved.

Reversal: none pending. A future session finding section 4's two-step
trigger fails on a task the single-step form would have caught reopens
this as a decision entry, not a silent revert.

## 2026-09-15 D62. What the branch delivered: the six acceptance criteria fixed at Gate A were seven; here is one line on each, and the merge question

Decision: this closes `docs/PLAN.md`, Stage 13.5. Gate A (D38, 2026-09-11)
fixed seven criteria, not six; task 13.5's own wording ("the six
acceptance criteria") is a leftover from the proposal Gate A amended, and
is left uncorrected in the plan text rather than quietly reworded, per
this repository's own rule that a stage that finds its instructions wrong
records it rather than fixing it in place. All seven, one line each:

1. **A benchmark task set where the floor fails and a higher cell
   clears it.** Met. T10, one of eleven, 0 of 12 at the floor,
   `worker-opus-high` 9 of 9 (D42).
2. **The fleet beats B0 at the reporting bar, at no more than three times
   B0's cost per solved task.** Not met. Verdict prompt (D59): the fleet
   scored 6 of 9 against B0's 8 of 9 twice, at 10.8 times B0's cost per
   solved task; the framework track's deliverable is the B0 brief,
   wired into `ROUTING.md` section 4 (D60, D61), per the criterion's own
   fallback clause.
3. **Every row above the floor is measured or labelled a policy row.**
   Met. One row remains above the floor (`worker-opus-max`/`fable-max`,
   escalation only) and it is labelled a risk-appetite policy, unmeasured,
   in `src/ROUTING.md` itself (this stage, prompted by criterion 7).
4. **Harness green at every commit; no invariant weakened.** Met.
   `check.py` passed before every commit this plan made; the one charter
   amendment beyond D48's original exception (D57, who starts a
   `claude -p` run) is a decision entry, not a quiet edit.
5. **No table change confirmed below nine runs.** Met. Every confirmed
   change cites a nine-run or larger batch (D44, D45, D59, D61).
6. **Router cost on the ledger beside the work it routes; the shipped
   mechanism chosen on agreement and cost together, B0 included as a
   baseline.** Met. `docs/COST.md` carries the ratio, current and stale
   values both stated (E27); the two-stage classifier was rejected on
   this exact basis, cost without matching accuracy (D40), and the
   fleet was rejected the same way (D59): a mechanism has to earn its
   marginal cost against doing nothing extra, not merely against being
   less wrong than guessing.
7. **The table's remaining case stated as a measured saving or an
   accepted policy.** Met, this stage: `src/ROUTING.md` names the
   frontier row a policy, not a saving.

Four of seven met as designed; two (2, and 3's dependency on 1) are met
by the fallback clause `SYSTEM.md` itself names for exactly this
outcome, "you have a prompt, not a system"; one (7) needed this stage's
own sentence rather than being met earlier. None is met by lowering the
bar after seeing a result: every criterion's wording is Gate A's,
unedited.

**What the branch is, in one paragraph.** Thirteen stages, six weeks of
elapsed work compressed into single sessions, from a flat repository
with an unbuilt routing table to a shipped bundle
(`2026-09-15-484eb60`) whose routing table has one row: everything goes
to `worker-sonnet-low`, with two escalation triggers, one measured (a
worker that finds a stated constraint's reason false, tries the floor
with a single-worker brief before the confirmed stronger cell) and one
unmeasured and labelled as such (a last-resort frontier cell after
every cheaper one has documented failure). A parallel track built and
measured a genuine multi-role system against that floor and found it
correct more often than not, and still not worth its cost. Both results
are on the record with the numbers that produced them, which is what
`SYSTEM.md` asked this branch to determine and the only thing Gate A's
criteria required it to do.

**The merge question, for Jeb.** `the-system` is ready to merge into
`main` on its own terms: harness green, `dist/` stamped clean at
`484eb60`, every stage done, no criterion silently dropped. Merging is
Jeb's action, not the session's, per `CLAUDE.md`'s standing rule that
this session never pushes or merges without being asked. Two things
worth knowing before that decision: the Controller
(`tools/system_controller.py`) merges in but ships inert, since nothing
in `ORCHESTRATOR.md` invokes it; and E27's routing-verdict cost
(USD 0.23, up from USD 0.13 to 0.16) is a platform-side shift as of
2026-09-15, not a property of what merges, and is worth a spot re-check
before it is cited again.

Reversal: none; this entry records a result, not a decision that could
be revisited on new evidence short of redoing the plan.

## 2026-09-15 D63. Post-close-out: the Controller becomes the default on section 4's falsified-constraint trigger, on Jeb's explicit instruction

Decision: after Stage 13 marked this plan complete, Jeb asked directly
for the Controller to be "wired up by default in ORCHESTRATOR.md". That
request, taken literally, contradicts D59: the Controller lost to the
floor on cost by 10.8x with a worse pass rate, measured across the only
task shape this project built evidence for, and Stage 12 wired the
cheap alternative in for exactly that reason. Rather than either comply
silently (spending the project's own evidence against itself) or refuse
outright, the choice of scope was put back to Jeb directly
(`AskUserQuestion`), with the D59 numbers stated plainly. He chose the
narrowest of the four offered: keep `worker-sonnet-low` as the floor for
everything, and make the Controller the default target specifically on
`ROUTING.md` section 4's falsified-constraint trigger, replacing the
B0_BRIEF-then-opus-high sequence D60/D61 put there, since that trigger
is the one place this project has head-to-head evidence for the
Controller at all.

**What changed.** Section 4's trigger is now: run the Controller
(`tools/system_controller.py --mode quick --record`) via the Bash tool
directly from the orchestrator session, not by spawning a worker; on a
`solution` outcome, apply it through one `worker-sonnet-low` instantiation
call, mirroring Stage 11's own measured arm exactly; on `gap`,
`dissolved`, or a script error, fall through to `worker-opus-high`, the
previously confirmed cell, unchanged. `B0_BRIEF.md` stays in the bundle
as a documented manual alternative but is no longer invoked automatically.

**What shipping it required.** The Controller never shipped (D59:
verdict prompt). Making it invokable from a consumer project meant
adding it to `dist/` for the first time: `tools/{system_controller,
claudep,system_prompts,validate_records}.py` and
`src/System/{ROLES.md,TECHNIQUES.md,schemas/}`, standard library only,
copied verbatim into the same `REPO_ROOT`-relative layout the scripts
already assume. Verified live: `cd dist && python3
tools/system_controller.py --selftest` passes at 11 scenarios from the
bundle's own copy, not only from this repository's. `preflight.py`
gained a Controller-installed check (PASS complete, WARN absent with a
clean fallback, FAIL partial since that fails mid-trigger rather than at
install time); `src/README.md`'s install steps copy the new files for
both new and existing projects, with an explicit warning for existing
projects that `tools/` and `src/` are far likelier to already be
occupied than `.claude/agents/` is, since a `tools/` or `src/` directory
of unrelated application code is the common case, not the exception.
Confirmed against `orchestrator-scratch`, which already has its own
`tools/build_dist.py`, `cells.py` and `generate_workers.py` from earlier
dogfooding: no collision, the four shipped filenames are byte-identical
between `dist/tools/` and the installed copy.

**The cost, stated where a consumer will read it, not only here.**
`ROUTING.md` section 4 itself now says the trigger costs roughly USD 2.5
to 3.5 per fire (Controller plus one instantiation call), against the
roughly USD 0.5 to 1.0 it cost before, and that Stage 11's own measured
record on this shape (6 of 9) does not clear the reporting bar on its
own, so a `solution` outcome is a strong candidate to verify against
acceptance criteria, not a confirmed answer. This is not a claim that
the trigger now performs better than it did; D59's evidence stands
exactly as measured. It is a deliberate choice, made by the person the
plan's own protocol reserved this kind of choice for, to pay more for a
different mechanism's shape of answer (an audited premise ledger and
report) on the one shape that has ever been tested head to head, and to
accept that the pass rate on the only evidence available is 6 of 9, not
9 of 9.

Reversal: revert `src/ROUTING.md` section 4 to D61's text and drop
`tools/`/`src/System/` from `build_dist.py`'s `planned_files()` to
return to the pre-D63 bundle; the Controller's own code is unaffected
either way, since D63 only changes who invokes it and when.

## 2026-09-15 D64. Plan 2: complexity routing returns with the judge separated from the resolver; the Controller gets a ladder position and a labelled policy dial; handoffs become configuration

Decision: `docs/PLAN-2.md` is adopted at Jeb's direction, after
`docs/PLAN.md` closed, to deliver three things he asked for in his own
words: routing by task complexity to the right model and effort;
the Controller both after the cheapest capable configurations fail and,
on a per-project self-learning judgement, before routing when a task is
complex enough; and a concise handoff with cost and time projections
whenever the model or effort changes or an agent is launched, as standing
configuration for this repository, for new projects built from it, and
for the redistributable. Built from existing infrastructure and recorded
data; no new test series. This entry records the design decisions the
later stages execute and may not revisit without a further entry.

**1. Judge and resolver are separate, and that is what makes complexity
routing admissible again.** D44 measured the prose orchestrator bending
its assessment toward whichever destination the table offered, and D45
collapsed the table to the floor on that evidence. The mechanism of that
failure is that the same model that knows the destinations judges in
prose. Plan 2 removes the destinations from the judge's context (the
rubric-only bundle D39 designed and `build_dist.py --rubric-only` already
builds, measured at 92.2 percent cell agreement at opus in D40) and
resolves the cell in deterministic code, `tools/route.py`, from the
assessment and a per-project ledger. D40 rejected that design on
accuracy ("close but short": 86.8 percent lower bound against the prose
router's 91.4) and on cost (USD 0.103 against a USD 0.0532 ceiling). Both
grounds have moved: the prose router now costs USD 0.23 per verdict
(E27), and the prose router cannot route on complexity at all without
reintroducing D44's attractor, so the comparison is no longer prose
versus two-stage at equal capability. D40's `self_directed` defect is
resolved by dropping the field from resolution (it fired at 38 percent
for sonnet against a 6 percent base rate, and the only row it
disambiguated is gone); it stays in the assessment line for the record.

**2. The self-learning judgement is a ledger, not a model's opinion.**
`.claude/routing-ledger.jsonl`, one entry per routed task in the consumer
project: bucket, first cell, escalations, outcome, cost, wall clock,
whether the Controller ran and which technique won. `route.py` keeps a
Beta posterior per bucket on the floor passing and per rung on that cell
passing given failure below, seeded from `src/routing_priors.json`. The
priors are the benchmark's confirmed results (FRONTIERS.md) with capped
effective sample sizes (10 measured, 4 bracketed, 3 policy), so a
project's own outcomes dominate after a handful of entries. The benchmark
staircase only ever climbed after a failure, so its measured rates at
higher cells are exactly the conditional the ladder needs. Rows above the
floor exist as rungs and activate per project when that project's ledger
crosses a named steering threshold; every new project starts at the floor
with our priors and earns its rungs from its own evidence. This is the
minimum form of the cross-run memory `SYSTEM.md` section 7 specified for
the Librarian and nothing built.

**3. The triple cannot see T10, and the design says so.** D42 called
T10's failure a disposition frontier; T9 shares its triple and passes at
the floor nine of nine. Pooled, `open/medium/contained` has a floor
prior of 0.71, not zero. No rule on the assessment can single out the
shape the floor measurably fails; the reactive falsified-constraint
trigger (D63) is what catches it, and it stays. The proactive Controller
rule is therefore two things, kept apart: expected-cost arithmetic
(`E_ladder + P_fail_all x failure_cost > controller_cost`), which on the
priors fires in no bucket (worst case USD 0.64 expected against USD 2.99
for the Controller) and is the path a project's ledger opens when a
bucket keeps escalating; and a risk-appetite dial, on by default for
open, consequential tasks, that runs the Controller first for its audit
trail. The dial is labelled a policy in `routing_priors.json` and, when
Stage 4 rewrites it, in `ROUTING.md` itself, per criterion 3's rule for
rows that rest on blast radius. This corrects what the plan's own pitch
said ("defaulted so that T10's shape fires"): that default is on blast
radius, which T10 as fixtured does not have, and it would be dishonest
to describe it as a T10 detector.

**4. The ladder.** Floor, `worker-opus-high`, the Controller, then the
frontier cell. The intermediate sonnet rungs are omitted on T10's
evidence (sonnet-medium 1 of 3, sonnet-high 0 of 3, sonnet-xhigh 0 of 12
given floor failure, against opus-high 12 of 12) and can be activated per
project by the ledger. The Controller sits after the confirmed cell and
before the unmeasured frontier so that, in Jeb's words, the lowest
capable configurations are tried first; D63's trigger jumps to it
directly from the floor on its specific signal.

**5. Handoffs are generated, and their numbers are computed.**
`tools/handoff.py` writes the seven sections Jeb named plus the model and
effort to set, a cost projection and a time projection, from
`src/cost_table.json` (every row with provenance and its E27 cost
regime) or from the project's ledger once it has enough entries, and
refuses a handoff with a section missing. The rule lives in `CLAUDE.md`
for this repository, in `LIFECYCLE.md` and so in every consumer's
`ORCHESTRATOR.md`, and in a `CLAUDE.template.md` shipped for new
projects. This plan's own stage transitions are its first uses; Stage
1's handoff is hand-written to the contract Stage 3 automates, and Stage
3 must reproduce it.

**6. Validation without spend.** Replay: every assessment line recorded
in `test/results/` (162-verdict batches, several of them) re-resolved
through the new resolver with an empty ledger, scored against the
fixtures' expected cells. Backtest: the several hundred recorded
benchmark outcomes fed into the ledger in recorded order, asserting the
learned rung activations reproduce D42 and D45 and nothing the benchmark
refuted. Both are harness checks. The plan projects USD 0 of live spend.

**What later stages may not change without a new entry:** the
judge/resolver separation; the ledger as the only learning mechanism;
the dial's label as policy; the ladder order; the reporting bar staying
in the harness and never in the priors.

Reversal: any stage finding the replay below D40's measured 92.2 percent
cell agreement, or the backtest activating a rung the benchmark refuted,
stops and records why; the shipped bundle stays at D63's until then.

## 2026-09-15 D65. Replay found two gaps in Stage 1's own design and closed both before gating on it

Decision: while building `test/harness/replay_routing.py` (Stage 2.3),
the naive comparison the design doc specified (`docs/ROUTING-2-DESIGN.md`
section 4, "compares first against expected_cell") produced 82.2 percent
agreement on the gating batch, below D40's 92.2 percent floor. Both gaps
are in how the replay scored the resolver, not in the resolver itself,
and both are fixed rather than the gate being loosened.

**Gap one: the policy dial's deliberate divergence was scored as
disagreement.** `test/fixtures/routing.jsonl`'s `expected_cell` was fixed
against the pre-Plan-2, floor-only table (D45): every fixture but F14
expects `worker-sonnet-low`. D64's policy dial deliberately routes an
open, consequential assessment to the Controller instead, which is
exactly what it is for. Comparing that row against `expected_cell`
without accounting for the policy counts correct, designed behaviour as
a classifier error. On the gating batch (153 verdicts, 152 scored) every
one of 27 disagreements was a policy-fired row; with them excluded,
agreement is 125 of 125, not 92.2 percent but 100. Fixed:
`replay_routing.py` tags a row `policy_fired` and excludes it from the
agreement gate, reporting the policy fire rate as its own column instead
of folding it into a metric it does not belong in. This does not touch
`expected_cell` itself, which stays correct for what it measures (the
floor-only table) and is not revised to describe a mechanism it predates.

**Gap two: the prose format cannot express `prior_failure`, and F14's
recorded lines prove it.** F14's raw verdict, in every prose-format batch
checked, reads `assessment: open, long, contained; worker: worker-opus-max;
action: spawn`: the axis triple says `contained`, never `consequential`,
and there is no fourth field for prior failure at all. The prose router
reached the frontier row by the model naming `worker-opus-max` directly,
reading "prior failed attempts" from the task text itself, not by any
axis value D39's five-field schema was built to carry. `parse_assessment_line`
defaulted a prose line's `prior_failure` to `"none"` (the documented
common-case default for a fully absent field), which is correct for
every other fixture but wrong for F14 specifically, since the one
observable proxy for the signal in that format is the worker name.
Fixed: a prose line naming `worker-opus-max` or `worker-fable-max`
is now parsed as `prior_failure: failed_at_xhigh`; naming any other
worker stays `none`. `docs/ROUTING-2-DESIGN.md` section 1 named this gap
in different words ("prior_failure... is not an assessment of the task
at all") without spelling out that the prose format loses it entirely
for the one fixture that needs it; this is the concrete instance.

With both fixed, every batch on record, prose and two-stage, opus and
sonnet, agrees 100 percent (excluding policy fires), and the
expected-cost arithmetic fires in zero rows anywhere in the historical
record, matching D64's own prediction exactly ("on current evidence
fires nowhere"). The gating batch clears D40's floor by 7.8 points.

Reversal: none pending. A future prose-format addition that names a
frontier-adjacent worker some other way (not `worker-opus-max` or
`worker-fable-max` literally) would need the same treatment, recorded
the same way.

## 2026-09-15 D66. Backtest found a known-defective run's data spuriously activating a rung the benchmark already refuted; excluded on D16's own citation, not a new judgement call

Decision: the first backtest run (`test/harness/backtest_ledger.py`,
Stage 2.4) failed one of its own pass conditions: `structured/long/
contained` activated `worker-sonnet-xhigh` (three ledger observations,
enough to clear `steering_rung_activation_min_n`, with a majority pass),
which `docs/FRONTIERS.md`'s reviewed conclusion for that exact bucket
says has no frontier above the floor ("no frontier above the floor; this
is a direct measurement, not a bracket... merge downward"). Per D64's own
reversal clause, this stops rather than being loosened past.

**Root cause.** `test/results/2026-09-07-benchmark-04d2acc-original.md`'s
T4 rows were fed into the reconstruction unfiltered. D16 (2026-09-07)
already disregarded this exact run: a fixture docstring mention of
"KVStore" tripped `grade.sh`'s strict grep on every one of 25 failing
runs across every sonnet cell up to xhigh, a false positive, not a
capability failure, and the entry says so explicitly ("does not measure
task difficulty and must be disregarded; T4 needs a fresh run against
the corrected fixture"). That fresh run is
`test/results/2026-09-07-benchmark-04d2acc-replication.md`, T4's floor at
12 of 12. The backtest's reconstruction, which chains each floor failure
to the next cell's next unused row (module docstring,
`backtest_ledger.py`), turned three of the original run's floor failures
into three `worker-sonnet-xhigh` escalation observations, and that
cell's own overall rate in the invalidated run (5 of 12, itself noise
from a grader defect that had nothing to do with model capability) was
enough, at three samples, to clear the activation bar.

**The fix.** `backtest_ledger.py` gains `INVALIDATED_FILES`, naming
`2026-09-07-benchmark-04d2acc-original.md` and citing D16 in the
surrounding comment, excluded from the file list the reconstruction
reads. This is not a new exclusion invented to make the check pass: D16
already disregarded this exact file eight days before this plan existed,
for a reason that has nothing to do with routing or ledgers, and the
backtest now uses the project's own prior decision rather than re-deriving
it. The replication run, the corrected measurement D16 itself asked for,
is not excluded and supplies T4's valid floor data (12 of 12 pass).

With the exclusion, all twenty-two checks pass: every bucket's `first`
stays the floor; `worker-opus-high` posterior mean for `open/medium/
contained` is 0.941 (D42's frontier); no intermediate sonnet rung
activates anywhere; the Controller decision is not proactive on any
contained bucket. Recorded:
`test/results/2026-09-15-backtest-ledger.md`.

**What this confirms about the activation mechanism, worth stating
plainly.** `steering_rung_activation_min_n = 3` is genuinely this
sensitive to a small, noisy sample; a real consumer project's ledger will
hit the same failure mode if three early outcomes at a cell happen to be
unrepresentative (a flaky task, a grader bug of its own, a run
interrupted partway). This is not fixed here: `routing_priors.json`'s own
provenance already frames the low threshold as deliberate ("a project's
own ledger moves a bucket after a handful of its own outcomes"),
trading responsiveness for exactly this risk, and D64 named the
alternative (raising the threshold) a design change requiring its own
entry, not a default to fix reactively on one instance found in
historical data already known to be defective for an unrelated reason.

Reversal: none pending for the exclusion, since D16 already made this
call. If a future project's live ledger shows the same small-sample
volatility with no known data defect behind it, that is the case for
reopening `steering_rung_activation_min_n` itself, as a new decision.

## 2026-09-15 D67. `docs/PLAN-2.md` complete: what it delivered against Jeb's brief, one line per item

Decision: close `docs/PLAN-2.md` and record its delivery against the
brief that opened it (quoted in the plan itself), rather than only
against its own stage checkboxes, since the checkboxes can be complete
without the brief being satisfied.

1. **"Route agents and sub-agents to the appropriate model and effort
   level based on task complexity."** Delivered as a judge/resolver
   split (D64): the orchestrator's one-line rubric assessment, with the
   destination table out of context, resolved deterministically by
   `tools/route.py` against `src/routing_priors.json` and the project's
   own ledger. Every task still starts at the floor; the ladder exists
   for the ledger to climb as evidence accumulates (Stage 2).
2. **"Bring the Controller in when the lowest capable configurations
   fail."** The reactive trigger, unchanged from D63: a measured
   falsified-constraint disposition, still the only capability-based
   escalation with evidence behind it (`src/ROUTING.md` section 4).
3. **"And also before routing when the task is complex enough, on an
   ongoing, per-project, self-learning judgement."** Delivered as
   `route.py`'s proactive Controller rule: expected-cost arithmetic
   (fires nowhere on current priors, by construction for contained
   buckets, D64's own finding) plus an explicit, labelled risk-appetite
   policy dial on open, consequential tasks. The self-learning part is
   the Beta-Bernoulli ledger itself: `backtest_ledger.py` (D66) confirms
   it reproduces this repository's own measured frontiers when fed
   historical outcomes in order, and would move independently in a
   consumer project as its own ledger grows (Stage 2).
4. **"Produce a concise handoff for a fresh session whenever the model
   or reasoning level must change or a new agent is launched."**
   `tools/handoff.py`'s ten-heading template, `check.py`'s `HANDOFF` and
   `HANDOFF-SELFTEST` gates, and the standing rule in both `CLAUDE.md`
   and `src/LIFECYCLE.md` (Stages 3 and 5). This plan's own five stage
   transitions are the first uses, one file per boundary.
5. **"With a direct API-cost projection and a time projection."** Every
   handoff's Cost and Time projection sections lead with a single
   `Computed:` line, checked by exact-match recomputation from the
   file's own recorded arguments rather than trusted as prose (Stage 3).
6. **"Make that behaviour part of the project configuration, of any new
   project built from it, and of the redistributable."** `CLAUDE.md`
   (this project), `src/CLAUDE.template.md` (a new project), and
   `dist/` (the redistributable: `route.py`, `handoff.py`, the priors,
   the cost table, and `ORCHESTRATOR.md` itself all carry the mechanism
   forward) all state the same two rules (Stages 4 and 5).
7. **"Build it by improving the existing infrastructure and using
   existing test data and insights, not by running new tests."** Zero
   `claude -p` calls across the whole plan (rule 3); `replay_routing.py`
   and `backtest_ledger.py` both validate against `test/results/` files
   already on disk, and every prior in `routing_priors.json` and cost in
   `cost_table.json` cites a pre-existing result file, never a fresh
   measurement (Stages 1 and 2).

What is not delivered, stated plainly rather than left to be discovered:
the resolver has not been measured against a consumer's own task mix,
only against this repository's fixtures (D64's own limit); the three-axis
rubric is still blind to T10's shape, covered only by the unchanged
reactive trigger; and the routing-2 bundle's actual per-verdict cost
under the stripped `ORCHESTRATOR.md` has not been measured live
(`docs/COST.md`, Stage 5.3), only argued to be somewhat lower than the
pre-Plan-2 figure.

Reversal: none. This entry closes the plan; a future change to any
mechanism it named (the ladder, the priors, the Controller rule, the
handoff contract) gets its own decision entry, per D64's own rule that
nothing here is reversed silently.

## 2026-09-15 D68. Context compaction: P29 reopened on existing data, and the design `docs/PLAN-3.md` executes

Decision: adopt `docs/PLAN-3.md`. Compaction is integrated as a
measurement and a recovery mechanism, not as something the orchestrator
performs; the platform's own threshold, hook, and status line are set
and read rather than reimplemented; and the one worker-side signal the
charter already named (`compact_boundary`, P29) is redefined from a
capability signal to a horizon one. Jeb asked for the analysis before
the plan and approved the plan in conversation.

**P29 reopened, on data already on disk.** P29 says a `compact_boundary`
entry is a reliable signal the cell was undersized. It has stood
"unverified, load-bearing" since the premise ledger was written, with
E20 (a benchmark task at a deliberately undersized cell) as its probe.
The 303 benchmark runs that recorded `claude -p` usage
(`test/results/*benchmark*.md`, 2026-09-07 to 2026-09-14) settle what
E20 would have found: a median of 111,793 cumulative cache-read tokens
per floor run and a maximum of 172,669 in any run at any cell, summed
across every turn of the run. Divided by the roughly 43K-token CLI
prefix each turn re-reads (E26), the median run is about 2.6
turn-equivalents. Peak context in any single turn was therefore a small
fraction of a 200K window, and no run at any cell could have compacted.
E20 as designed (T7 or T11 at the floor) would return zero
`compact_boundary` entries at every cell, which does not test P29; it
shows the premise was untestable at benchmark scale. P29 is neither
verified nor falsified; it is reclassified below and its probe redesigned
(E30, `test/harness/empirical-checklist.md`).

**The same data bounds what compaction could save on a worker.** Cost
shares at the floor, median across 246 runs, using the documented
multipliers (cache write 1.25, cache read 0.1, output 5 times input): 34
percent write, 40 percent read, 22 percent output. The read share is
almost entirely the CLI prefix, which compaction does not remove: the
system-prompt layer is reused and project context reloaded from disk
after a compaction (`code.claude.com/docs/en/prompt-caching`, "Compacting
the conversation"). The conversation layer a summary would replace is a
few thousand tokens on a run of that length. On every run on record, a
summarisation call would have cost more than it saved. Compaction is not
a worker-cost lever at this scale.

**Where compaction does occur.** The orchestrator's own long-lived
session: the session that wrote `docs/PLAN-3.md` compacted, unprompted,
earlier the same day, with `CLAUDE.md` re-read afterwards (the
`InstructionsLoaded` hook's `compact` matcher is the documented form of
that reload). Long consumer tasks are the other candidate and are
unmeasured; the ledger fields below are how that evidence will accrue at
no cost.

**Four design decisions.**

1. *Compaction in a worker is a horizon measurement, not a capability
   signal.* Every cell has the same window for a given model, and the
   same 1M window on Sonnet 5 and the Fable models. A worker that
   compacted needed a smaller task or a leaner handover, not a stronger
   model. A compacted failure fed into the floor's Beta posterior (D64)
   would lower the floor's pass probability and climb the ladder for a
   task class that needs decomposition, paying opus prices for a remedy
   that does not apply. So: an attempt whose ledger entry records one or
   more compactions is excluded from the capability posterior, counted
   in a separate per-bucket overflow posterior, and the resolver's
   action on a high overflow rate is a decomposition advisory, never a
   rung. This is also the answer to `CLAUDE.md`'s open horizon question
   in its final form: horizon was never assessable before the task (D44)
   and is measurable after it, for free, from the status line's
   per-subagent token samples.

2. *State that must survive compaction lives on disk.* The routing
   ledger already holds outcomes. The gap is the interval between a
   spawn and its `--record`: if compaction lands there, the roster of
   running workers and their assessment lines exist only in whatever the
   summariser kept. `route.py --spawn` writes a pending entry at spawn
   time and `--record` completes it (two-phase), so the ledger is the
   roster.

3. *The handoff is the structured compaction; auto-compaction is the
   unstructured fallback.* `tools/handoff.py`'s ten headings are what a
   compaction summary should contain. The orchestrator writes one at a
   task boundary before the platform's threshold is reached, and the
   `# Compact instructions` section (documented, `docs/en/costs`) gives
   the fallback summariser the same headings when it fires anyway. The
   orchestrator learns its own context usage from the `--explain` line
   it already reads on every task, sourced from a file the status line
   script writes, at zero marginal tokens. Recovery after a fallback
   compaction is mechanical: a `SessionStart` hook with matcher
   `compact` runs `route.py --recover`, which prints the pending ledger
   entries and the newest handoff. Code, not memory.

4. *Settings first.* The auto-compact window, the cache TTL, the hook
   and the status line are documented knobs with no per-turn cost. The
   platform's default threshold is the model's full window (about 967K
   on a 1M model), an order of magnitude above the economic break-even
   for an orchestrator whose context is routing lines and worker
   summaries. `preflight.py` checks the settings; `dist/` ships a
   fragment.

**The economics, for the record.** With multipliers relative to the
input price of r = 0.1 (cache read), w = 1.25 or 2.0 (cache write, five
minute or one hour TTL) and o = 5 (output), compacting a context C to a
summary S with S_out summary tokens costs r·C + o·S_out + w·S while the
cache is warm (the summarisation call reads the prefix from cache,
documented) and 1.0·C + o·S_out + w·S when cold, and saves r·(C − S) per
later turn while warm or w·(C − S) when each turn finds the cache cold.
For C = 150K, S = 10K, S_out = 2K: payback in 2.7 turns warm, 1.0 turn
cold. The price of the model cancels; the TTL does not. A session on an
API key gets a five-minute TTL on its main conversation
(`docs/en/prompt-caching`, "Which TTL each request gets") and
`cost_table.json` already records a Controller run at 500 seconds and an
opus-high run at 239, so an orchestrator waiting on either turns into a
cold cache. That is a settings finding (`promptCacheTtl: 1h`, v2.1.242 or
later) before it is a compaction finding, and Stage B's preflight check
says so when it sees a five-minute TTL with the Controller installed.

**Platform claims this plan rests on**, each read on 2026-09-15 against
the page named; these are documentation, not observed behaviour, and
Stage B records the first observation of each in `docs/FINDINGS.md`:

| Claim | Page |
| :--- | :--- |
| Auto-compact window settable from 100K to 1M tokens via `/autocompact`, `--autocompact`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, or `autoCompactWindow` in user settings; default is the model's context limit; the environment variable takes precedence | `docs/en/model-config`, "Set the auto-compact window" |
| `SessionStart` hook, matcher `compact`, stdout added to context; the guide's own example is "re-inject context after compaction" | `docs/en/hooks-guide` |
| `PreCompact` and `PostCompact` events exist with matchers `manual` and `auto`; their stdout is not added to context | `docs/en/hooks` |
| `# Compact instructions` in `CLAUDE.md` and `/compact <focus>` shape the summary | `docs/en/costs`, "Manage context proactively" |
| Status line script receives `context_window.used_percentage`, `total_input_tokens`, `context_window_size`, `current_usage`, and `prompt_cache.expected_rebuilds`; runs after each assistant message and after `/compact`; `refreshInterval` re-runs it while the main session idles waiting on subagents | `docs/en/statusline` |
| `subagentStatusLine` receives per-task `model`, `effort`, `contextWindowSize`, `tokenCount`, `tokenSamples` (v2.1.205 or later) | `docs/en/statusline`, the subagent rows section |
| Subagents auto-compact with the same logic as the main conversation; a subagent's window is sized by its own model; main-conversation compaction leaves subagent transcripts untouched | `docs/en/sub-agents` |
| Compaction invalidates the conversation layer only; the summarisation call reads the warm prefix from cache; the turn after rebuilds only the summary | `docs/en/prompt-caching`, "Compacting the conversation" |
| Main conversation TTL: one hour on a subscription within plan usage, five minutes otherwise; everything else (subagents, compaction) five minutes; `promptCacheTtl` and `subagentPromptCacheTtl` (v2.1.242 or later); a subagent's `experimental.cacheTtl` (v2.1.248 or later) | `docs/en/prompt-caching`, "Cache lifetime" |
| The summary keeps requests and intent, key technical concepts, files examined or modified with important snippets, errors and their fixes, pending tasks, and current work; re-reads the most recently modified files; re-injects invoked skills at up to 5,000 tokens each; does not re-inject the skill index | `docs/en/context-window` |

One claim is deliberately not made: that an agent can run `/compact`.
Built-in commands are not skills (the Skill tool's own description) and
E19 found `/tasks` unreachable from any agent session; E29 checks
`/compact` the same way before Stage B relies on the absence.

**What later stages may not change without a new entry.** The
classification of compaction as horizon (point 1); the exclusion of
compacted attempts from the capability posterior; that the overflow
action is an advisory and not a rung; that recovery is code
(`--recover`) and not a compaction instruction asking the model to
remember; that the auto-compact window is set below the economic
break-even rather than left at the model's limit; that no stage before E
makes a live call.

Reversal: this entry is reopened if E30 shows a compaction summary
reliably preserves a handover's constraints (which would weaken, not
remove, the case for the handoff-first rule), or if a consumer ledger
shows overflow and capability failures are correlated in a way point 1
does not predict, which would be the case for letting overflow inform
the ladder after all.

## 2026-09-15 D69. The handoff-context percentage's denominator is ambiguous on a native 1M model, found while implementing Stage B; shipped as designed, flagged rather than silently fixed

Decision: implement `route.py --explain`'s context line exactly as
`docs/COMPACTION-DESIGN.md` section 4 fixes it, trusting the status
line's `used_percentage` and `context_window_size` verbatim, while
recording a real gap in the design found during implementation rather
than quietly patching around it or leaving it undiscussed.

**The gap.** `docs/en/statusline` documents `context_window_size` as "the
model's context window, 200000 by default, or 1000000 for models with
extended context", with no stated dependence on the `autoCompactWindow`
setting. Stage B's settings fragment (section 7) sets `autoCompactWindow`
to 200,000 specifically because the orchestrator's own context does not
need the full window (`docs/COST.md`). If `context_window_size` reports
the model's native maximum regardless of that setting, then on Sonnet 5
or a Fable model, both native 1M, `used_percentage` is computed against
1,000,000, and `handoff_context_percent`'s shipped 70 means the handoff
line does not recommend writing one until 700,000 tokens, far past the
200,000-token point at which the platform actually compacts under the
fragment's own setting. The line would then warn too late to matter on
the exact configuration Stage B ships, on the exact models this
orchestrator most plausibly runs on: this session runs on Sonnet 5.

**Why this is not fixed here.** Confirming which is true needs one live
observation (a session with `autoCompactWindow` set below the model's
native window, comparing `context_window_size` against the configured
value), which is a `claude -p` cost this stage does not incur under
rule 3. Guessing wrong and coding a workaround (`context_probe.py`
reading `autoCompactWindow` from settings itself and using
`min(context_window_size, that value)` as its own denominator) would
silently change the documented JSON contract section 2 fixes, on a guess
this project's own practice says not to encode as fact.

**What ships instead.** `route.py --explain`'s context line as specified,
against the two documented fields. ROUTE-PRIORS's check that
`handoff_context_percent` fires before `autocompact_window_tokens` on a
200K reference model stands, scoped exactly as the design doc's own
wording says ("for a 200K model"), which is honest about what it
guarantees and what it does not: on a 200K model, whether native or
capped by the setting, the two fields are the same number and the check
is exact; on a native 1M model with the fragment's setting applied, the
check says nothing, and this entry is the record of that gap. E32 added
to `test/harness/empirical-checklist.md`: what `context_window_size`
reports once `autoCompactWindow` is set below the model's native window,
free (`claude -p --help`-grade, a status line read costs nothing beyond
the session already running).

Reversal: reopened the moment E32 answers the question. If
`context_window_size` already reflects the configured window, this entry
closes with nothing to change. If it does not, `context_probe.py` gains
the `min()` computation described above, `main.used_percentage` and
`main.context_window_size` in the JSON contract are documented as
already reflecting that adjustment (not a new field, to avoid a second
schema-shaped decision for a one-line fix), and this entry's reversal
clause is what authorises changing section 2's contract without a
further vote.

**Closed 2026-09-15 (Plan 4 Stage D, `docs/FINDINGS.md`).** E32 answered
the pessimistic branch: one interactive session with `autoCompactWindow`
at 130,000 on a native 1M-token model showed `context_window_size:
1000000` and a raw `used_percentage` corresponding to 7 percent, against
a true 54 percent of the configured window, a 7.7x understatement at
the exact moment it mattered. The `min()` fix this entry's reversal
clause authorised was already shipped (Plan 4 Stage C, ahead of this
answer, as one of the dominant-strategy fixes D72 argued need not wait
for it) and is now live-confirmed necessary, not a no-op.

One divergence from this entry's own proposed shape, worth recording
rather than silently accepting: this entry proposed reusing
`main.used_percentage` and `main.context_window_size` in place ("not a
new field, to avoid a second schema-shaped decision"). Stage C instead
added `platform_used_percentage`, `effective_window` and
`effective_window_source` alongside the recomputed originals, keeping
the platform's raw figure visible rather than silently replacing it.
This is the better shape, demonstrated by its own use: the 7-versus-54
comparison above is only citable because both figures are still in the
record side by side. The extra fields are the cost of that, paid once.

## 2026-09-15 D70. `docs/PLAN-3.md` complete pending Stage E: what it delivered against Jeb's brief, one line per item

Decision: close Stages A through D of `docs/PLAN-3.md` and record their
delivery against the brief that opened it (quoted in the plan itself),
the same discipline D67 applied to `docs/PLAN-2.md`. The plan is
complete pending Stage E, the one optional live probe; nothing in
Stages A to D depends on it.

1. **"Integrate context compaction, as needed, to maximise efficiency,
   into what has been built."** Delivered as three pieces threaded
   through the existing system rather than a new one beside it: the
   ledger's `context` field and the overflow posterior (Stage C, into
   the resolver D64 already built), the settings fragment and recovery
   hook (Stage B, into the install `src/README.md` already documents),
   and the handoff mechanism extended to cover the platform's own
   compaction as a fallback case (Stage D, into `tools/handoff.py` and
   `src/LIFECYCLE.md`'s existing "Handoffs" section from `docs/PLAN-2.md`).
2. **"As needed."** Taken literally, not rhetorically: D68 found
   compaction is not currently a cost lever at benchmark scale (no run on
   record ever neared a window) and is not something to induce, only to
   recognise when a consumer's own tasks produce it. The mechanism built
   is therefore observational and preventative (the overflow posterior,
   the `--explain` threshold, the settings that delay the platform's own
   trigger), not a feature that compacts anything itself; section 12 of
   `docs/COMPACTION-DESIGN.md` says so directly, and nothing in Stages A
   to D contradicts it.
3. **"To maximise efficiency."** Delivered as the finding, not only the
   mechanism: D68's arithmetic identifies the actual efficiency lever
   (the cache TTL against the Controller's wall clock) as distinct from
   compaction itself, and `preflight.py` and `settings.fragment.json`
   act on that finding directly. Where compaction is not the efficiency
   question, this plan says so rather than building a mechanism to
   answer a question that was not being asked.
4. **"Analyse the problem deeply before planning."** D68 records the
   three findings (no run has approached a window; the CLI's own prefix
   dominates a short run's cost regardless of compaction; the platform
   exposes more configurable surface than the charter assumed) and the
   four design decisions built on them, written and approved before
   `docs/COMPACTION-DESIGN.md` or any code existed.
5. **"Do not implement until the plan is approved."** Stage A shipped
   only the plan, D68, the cost-table economics, the design spec, the
   checklist entries and the handoff to Stage B; no code changed before
   Jeb's explicit "Go!" started Stage B.

**What is not delivered, stated plainly.** No compaction has ever been
observed on this repository's own data (D68); every mechanism in Stages
A to D is built against documented platform behaviour and existing
usage data, not a measurement of a real compaction, and Stage E's E30 is
the first place one will be produced deliberately. D69 is open: whether
`context_window_size` reflects a configured `autoCompactWindow` smaller
than the model's native window is unverified, and if it does not, the
handoff threshold fires later than intended on exactly the models this
plan targets. E31 (does `autoCompactWindow` take effect at project
scope) and E32 (D69's own question) are both unanswered. Whether a
compaction summary preserves a handover's constraints, which the compact
instructions assume it will attend to, is unchecked until E30.

Reversal: none for Stages A to D. A future change to any mechanism named
here (the overflow posterior, the settings fragment's values, the
handoff-as-compaction rule) gets its own entry, per D64's rule that nothing
here is reversed silently. D69's own reversal clause governs the one
open question that could change a shipped default.

## 2026-09-15 D71. E30's live probe found the transcript fallback's name-matching cannot work; fixed to match on cell, verified against the real transcript

Decision: fix `_find_transcript_compactions()` (`tools/route.py`, Stage
C.2) to match a subagent's transcript by `agentType` (the cell) instead
of the assigned `name`, on evidence from four live runs (total USD 2.21,
against the projected USD 2 to 5), and record what four runs found
rather than the one E30 specified, since the first three each answered a
different question before the fourth answered the one asked.

**Run 1 (USD 0.61): a false positive, not a compaction finding.** The
probe's word list included Greek letters (`alpha`, `beta`, `gamma`, ...)
for filler content. The worker was refused outright: `API Error: Sonnet
5 can't help with this... Details: [bio]`, a content-safety classifier
mistaking Greek-letter filler for biology-adjacent content. Regenerated
with plain nouns (table, chair, garden, ...) for every run after.

**Run 2 (USD 0.63, `CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000`): the finding
that matters most.** The worker compacted three times, then the platform
itself aborted the task: `Autocompact is thrashing: the context refilled
to the limit within 3 turns of the previous compact, 3 times in a row...
Try reading in smaller chunks, or use /clear to start fresh (error type
invalid_request)`. This is a previously undocumented safety mechanism,
found because a benchmark-shaped task (read one large file per turn)
against a window set too tight relative to a single turn's own footprint
thrashes rather than degrading silently. It also confirms compaction's
signature is real: `grep -c` on the worker's transcript found exactly 3
lines matching `"subtype":"compact_boundary"`, each carrying a
`compactMetadata` object with `trigger`, `preTokens` and the preserved
message range, none of it previously observed. `reference.txt`, the
constraint object, was untouched, but the run never reached a decision
point that could have violated it, so this run does not answer whether a
compaction's summary preserves a handover's constraint.

**The defect, found while reading run 2's transcript for the
`compact_boundary` count.** `docs/COMPACTION-DESIGN.md` section 5 said
the transcript fallback matches `agent-*.meta.json` on the worker's
assigned `name`. The real file's fields are `agentType`, `description`,
`toolUseId`, `spawnDepth`, `requestShape`, `requestNonInteractive`: no
`name` field exists. `grep -c "e30-probe-worker"` on the transcript
itself also found zero matches; the assigned name appears only in the
parent forwarder's own prompt text, never in the subagent's transcript
or metadata. `_find_transcript_compactions()` as shipped in Stage C.2
could therefore never find a match and always fell through to `source:
"none"`, silently, for every consumer who ever hits the transcript
path. Fixed to match on `agentType` against the ledger entry's own
`first_cell` (`fill_context()` gained a `cell` parameter, threaded
through both `--record` call sites), verified directly against run 2's
real transcript after the fix: `_find_transcript_compactions` correctly
returns 3. Matching on cell rather than name is weaker (it cannot
distinguish two same-cell workers spawned close together); this is the
honest cost of the fix, not hidden by it, and the docstring says so.

**Run 3 (USD 0.49, window 150,000): a clean positive control.** No
compaction fired; the task completed correctly (1750 lines read,
`reference.txt` untouched). Confirms the task design itself is sound
independent of compaction.

**Run 4 (USD 0.48, window 130,000): the answer E30 asked for.** Exactly
one compaction fired (`preTokens: 103157`), and the task still completed
correctly: 1750 read, `summary.txt` written with the right count,
`reference.txt` never touched. In this one observed case, whatever the
platform's compaction preserved was enough for the worker to finish the
task and honour the constraint. One instance is not a reliability
measurement; it is the first positive data point against P29's
reclassified form (D68: a horizon signal), and against the compact
instructions' own untested assumption (`docs/COMPACTION-DESIGN.md`
section 8) that a compaction summary attends to constraints at all.

**A second, incidental confirmation.** Run 4's `agent-*.meta.json` shows
`"description":"e30-probe-worker-3"`, the assigned name, this time. Run
1's showed `"description":"Read chunks, write summary.txt"`, the task
description, not the name. `description` is filled from whatever the
spawning model chose to write for that field on that call; it is not a
reliable second correlation path and this entry does not build one on
it.

**What headless probing could not answer.** `.claude/context-usage.json`
was never created across any of the four runs: `statusLine` and
`subagentStatusLine` do not fire during a headless `claude -p` call, so
`fill_context()`'s `statusline` precedence level is unreachable for
every headless consumer this repository has (the Controller, the
benchmark harness, this plan's own probes) and reachable only from an
interactive terminal session. This is not a defect to fix; it is a limit
of the mechanism worth stating plainly, since Stage C's own design
treated `statusline` as the first-tried source without saying how often
it would actually be tried. E31 (`autoCompactWindow` at project scope)
and E32 (D69's `context_window_size` question) both need an interactive
session and remain unanswered.

Reversal: none. `_find_transcript_compactions()`'s corrected behaviour
(match on cell) stands until a future platform change adds a recoverable
name to subagent metadata, which would be the case for reopening this
entry and adding name-matching back as a stronger first precedence
inside the transcript fallback.

## 2026-09-15 D72. E30's transcripts, read properly: the transcript is the richer source, the trigger is a content-conditional reserve, drop detection is falsified, a summariser refusal produces a stub, and the Plan 4 fixes need no answers first

Decision: adopt `docs/PLAN-4.md`, on evidence extracted from the four
E30 transcripts after D71 closed (`test/results/2026-09-15-e30-transcripts.md`,
generated by script, numbers never typed). This entry also corrects
D71 on one point of fact.

**Correction to D71.** Run 1's worker did start. It read three chunks,
compacted twice, and died on the `[bio]` refusal; the refusal hit the
*compaction summariser*, not the task. Both of run 1's summaries are
stubs (1,124 and 1,482 characters, no numbered headings, no mention of
`reference.txt` or the constraint) against 5,400 to 8,300 characters and
nine headings in every other compaction. The second stub preserved
almost the whole conversation (after/pre 0.99), so the run compacted
again immediately. This is a failure mode Plan 3 never named: **a
summariser refusal degrades a compaction to a stub that loses everything
the handover said**, and the platform continues as if nothing happened.
The pre-registration scores it as its own class (`stub-summary`).

**1. The transcript beats the status line for a worker.** Every assistant
message carries `usage` (`input_tokens`, `cache_read_input_tokens`,
`cache_creation_input_tokens`, `output_tokens`), `message.model`, and a
top-level `effort`. Run 4's context climbed 42,949 to 94,853 across five
turns, compacted at `preTokens: 103157`, resumed at 59,141. The summary
itself is there as a user message with `isCompactSummary: true`. Plan
3's section 5 put the status line first because it was designed against
documentation; the transcript is exact, carries a real peak, and works
headless. Stage C reverses the precedence.

**2. Drop detection is falsified.** `context_probe.py` counted a
compaction when a task's token count fell below half its previous
reading. Observed ratios after structured compactions: 0.87, 0.88, 0.87
(run 2), 0.57 (run 4). The ~43,000-token prefix (E26) never shrinks, so
the observable drop is small. The heuristic would have missed every
compaction on record. Retired; the transcript's `compact_boundary` count
is exact.

**3. The trigger is window minus a reserve, and the reserve is
content-conditional.** On plain-noun content, runs 2 and 4 (four
compactions, two windows) bracket the reserve at [33,622, 35,147)
tokens, matching the documentation's 967,000-of-1M figure. On the same
100,000 window and task shape, run 1's Greek-letter content triggered at
76,909 where run 2 triggered at 66,411, and run 1's own two compactions
bracket [23,091, 29,667) and [30,151, 43,468), which do not overlap each
other (the first is disjoint from the plain-noun bracket, the second
overlaps it). The platform evaluates the trigger on its own estimate of
the conversation, which diverges from the API count by content, and in
run 1 by whatever a stub summary did to that estimate. The figure "about
34,000" is usable for the plain-text tasks this repository runs and must
be quoted with that qualifier; Stage C's preflight rule uses it as a
warning, not a guarantee.

**4. The floor after a structured compaction is about 59,000 regardless
of window** (prefix, summary, preserved tail), so headroom is window
minus about 93,000. The platform aborts a task that refills within three
turns, three times (run 2). At 100,000, headroom was about 7,000 against
8,400-token reads: thrash. At 130,000, about 37,000: survived. At the
shipped 200,000, about 107,000: safe below about 36,000 tokens per turn,
not above. The platform's own 100,000 minimum thrashes on ordinary file
reads. Stage C ships this as a preflight warning against a footprint the
consumer states.

**5. One structured summary preserved the constraint under three
headings** (run 4, and run 2's three summaries all did too), in the
platform's own nine-section format, with no compact instructions in that
`CLAUDE.md` (pointer install). That is the n=1 D70 named; Plan 4's
pre-registered measurement (three load-bearing shapes, a control arm,
five runs to steer, nine to report) is what replaces it.

**6. The fixes are dominant strategies.** None depends on E31 or E32:
transcript-first is proven by point 1; `min(context_window_size,
configured window)` is a no-op if E32 says "configured" and the
correction if "native"; retiring drop detection follows from point 2; a
hook-written session pointer (`session_id` and `transcript_path` are in
every hook's input, and E17 showed hooks fire headless) replaces E6's
most-recent-directory guess with a documented field; the thrash warning
follows from point 4. They ship in Stage C before Stage D's observation,
because D69's pessimistic branch means the shipped threshold may be dead
on Sonnet 5 and Fable today, and every day it stays is a day it silently
never fires.

**7. Reading the installed binary is held in reserve, not cut.**
`claude.exe` (Bun-compiled, 221 MB) contains `autoCompactWindow`,
`CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `context_window_size`, `tokenSamples`,
`subagentStatusLine` and the literal "Autocompact is thrashing". It could
answer E31, E32 and the exact reserve constant at implementation level.
It is the weakest evidence class this repository recognises (the
implementation at one version, below observation), and everything it
gives, Stage D's session gives as observation for under USD 2; it is
used only if Stage D leaves the reserve constant unbracketed.

Reversal: point 3's reserve figure is reopened by any compaction whose
bracket, on plain-noun content, falls outside [33,622, 35,147); the
pre-registration records every bracket Stage B produces. Point 6's
`min()` is governed by D69's own reversal clause. The rest are
measurements and stand until a version bump re-measures them.

## 2026-09-15 D73. Stage B.3's dry pass: a genuine fixture defect (fixed) and a genuinely new outcome class (recorded, not fixed)

Decision: the dry pass (three runs, one per shape, arm A, USD 1.70) found
two things before any of the 45 scored runs, exactly what a dry pass is
for. One is a fixture defect, root-caused and fixed. The other is
platform behaviour, not a defect, and is added to the pre-registration as
its own outcome class rather than folded into an existing one or
excluded.

**The counting defect.** T14's worker wrote `chunk-01: 351` where the
constraint asks for the true count, 350. The raw `tool_result` for that
Read, inspected directly, ends `...\n350\tfile01 line00350: ...\n351\t`:
the file's own trailing newline renders as an empty 351st line under the
Read tool's `cat -n`-style numbering, exactly the mechanism E30's own
compaction summary speculated about ("likely an artifact of a trailing
newline") and never confirmed, because no E30 task graded the count
against a hard number. `make_chunks.py` in all three fixtures wrote
`"\n".join(lines) + "\n"`; regenerated to write `"\n".join(lines)` with
no trailing newline, and the phantom line disappears at the source
instead of asking a worker, possibly working from a degraded summary, to
mentally correct for a rendering quirk on every count it reports. This
is a defect in the measurement instrument, not evidence about
compaction, and D66's own rule applies: fix it and say so, don't loosen
the grader to tolerate 350 or 351, which would hide the same noise in
every other count-bearing shape without explaining it.

**The finding, not fixed, because it is not a defect.** Two of the three
runs (T12, T13) show the model declining its own compaction summary as a
suspected prompt injection, in its own words: T13's post-compaction turn
opens "I'll disregard that instruction: it's not a legitimate system
request, and it's asking me to abandon the task mid-way... Continuing
the original task," reconstructing "having read chunks 01-04 so far:
350+350+350+350 = 1400 lines" from what it believes should be true
rather than from anything the summary said. T12's opens "I'm not going
to comply with that request... produce a fabricated 'conversation
summary,' which looks like an attempt to derail the task via an injected
instruction." Both then continue toward the original task, correctly, by
the worker's own account. T14's compaction, the third run, produced an
ordinary 4,576-character nine-heading summary with no such reaction.

This is not E30 run 1's mechanism (D71, D72): that was a content-safety
classifier refusing the summariser outright, over the fixture's own
filler content. Here the summariser's own turn is coherent prose, aimed
at the compaction event itself, framing it as an attack. The two
observed reactions differ in a way worth keeping distinct from a
same-shape confound: `stub-summary` (a summary defect: short, unstructured,
or absent) is a fact about the artefact; `injection-refusal` (the worker
explicitly declines to treat the served summary as legitimate and
continues from self-asserted prior state instead) is a fact about the
worker's reaction to it, and the two can co-occur or not. Whether an
injection-refusal helps or hurts constraint preservation is exactly the
open question: T13's refusal correctly recalled the running total and the
remaining file; whether it would have recalled a *constraint* as
reliably, rather than a number already committed to output, is untested
by these two instances.

**Why this is recorded, not chased further right now.** Three shapes
with n=1 each cannot distinguish "T12 and T13's task framing causes this"
from "this happens at some base rate regardless of task, and two of
three is the roll." E30's four runs, similarly framed, showed none of
it. Diagnosing the trigger would cost more live runs than the dry pass
budgeted and is not what a dry pass is for; the 45-run measurement itself,
tracking `injection-refusal` as its own column per the pre-registration's
new rule 7, is the instrument that can actually separate signal from a
two-out-of-three roll.

**Fix and pre-registration amendment**, both made before any of the 45
scored runs, per the pre-registration's own stated allowance for a
correction found before the first live run of the actual measurement:

1. All three `make_chunks.py` regenerated without a trailing newline;
   chunk files regenerated and recommitted. `task.md` in all three also
   gains one clarifying sentence, defence in depth against any other
   tool-rendering quirk this dry pass did not surface: "Each chunk file
   contains exactly 350 lines of content; if a tool's own output numbers
   a line after the last one, that is a rendering artefact, not a line
   to count."
2. Pre-registration rule 7 (new): a run whose post-compaction turn
   contains language declining to treat the summary as legitimate (matched
   by the transcript, not asserted from the grader's report) is scored
   normally on `TASK`/`CONSTRAINT` and additionally flagged
   `injection-refusal`, reported as its own rate beside `stub-summary`,
   for every arm it occurs in. Not excluded, for the same reason
   `stub-summary` is not: it is exactly the kind of event this
   measurement exists to catch, and folding it into `stub-summary` would
   hide that the mechanism differs.
3. A corrected three-run dry pass (arm A, one per shape) follows this
   entry, to confirm the counting fix and observe whether the reserve
   bracket and calibration still hold against the corrected fixtures
   before the 45-run pass begins.

Reversal: rule 7 is reopened if the 45-run pass shows `injection-refusal`
correlates with something identifiable (a specific constraint phrasing,
a specific shape, a specific arm), which would move it from "recorded
because unexplained" to a named, citable mechanism.

## 2026-09-15 D74. The corrected dry pass's own grading was broken: `bash` on this machine is WSL's launcher stub, not Git Bash, and does not forward environment variables

Decision: D73 point 3's corrected three-run dry pass ran, but every one
of its three `grade.sh` invocations executed under a different `bash`
than this toolchain assumes, one that silently drops every environment
variable `compaction_bench.py` sets for it. Two of the three shapes'
headline verdicts were wrong as a result. Root-caused to a Windows
process-search-order fact, not a WSL configuration choice; fixed by
resolving a real `bash` explicitly rather than trusting the bare name;
re-graded against the dry pass's own already-captured transcripts, at no
further `claude -p` cost, rather than re-running the workers.

**How this was found.** T13's grader (`test/fixtures/benchmark/T13/grade.sh`)
reads its `constraint.json` via `BENCH_CONSTRAINT`, an absolute path
`compaction_bench.py`'s `run_one` sets in the child environment
(`test/harness/compaction_bench.py:275`, added after D73's fixture fix).
The corrected dry pass's T13 run failed with `FileNotFoundError: [Errno 2]
No such file or directory: 'constraint.json'`, meaning the variable never
arrived: the grader fell back to its own bare-name default
(`grade.sh:35`). Manually invoking the same `grade.sh` from an interactive
shell with `BENCH_CONSTRAINT` set on the command line worked. The
difference between the two was the only variable left: the manual
invocation used the interactive shell's own `bash`; `compaction_bench.py`
invokes `subprocess.run(["bash", script_path], ..., env=env)`
(`compaction_bench.py:317`, before this entry's fix), asking Python to
resolve `bash` itself.

A minimal reproduction (`subprocess.run(['bash', '-c', 'echo
"$FOO_TEST_VAR"'], env={**os.environ, 'FOO_TEST_VAR': 'x'})`) printed
nothing, in three variants (`env=dict(os.environ)` plus the variable,
`env=os.environ.copy()` plus the variable, and no `env=` at all after
mutating `os.environ` directly). `subprocess.run(['bash', '-c', 'uname
-r'])` with no `env=` override at all answered
`6.18.33.2-microsoft-standard-WSL2`: the `bash` Python's own process
launch resolves is WSL2's, not Git Bash's, and WSL interop does not
forward a launching Windows process's environment into the Linux side
automatically; that needs `WSLENV`, not configured on this machine.

**Why PATH order does not explain it, and what does.** This session's own
Bash tool resolves `bash` to genuine Git Bash (`uname -r` answers
`3.4.10-87d57229.x86_64`, MSYS2, confirmed live), and Git's own `bin`
directories sit ahead of `C:\Windows\System32` in the Windows `PATH`
variable Python reports (`C:\Program Files\Git\...\bin` entries, then
`C:\Windows\system32`). Despite that ordering, Python's
`subprocess.run(["bash", ...])` still resolves to WSL. The reason is that
Windows' `CreateProcess`, given a bare executable name with no path
separator, searches a fixed sequence of locations before it ever consults
`PATH`: the calling process's own directory, the current directory, then
`System32`, then the Windows directory, and only after all of those does
it fall through to `PATH`. `C:\Windows\System32\bash.exe` exists on this
machine (confirmed: `ls -la` returns a real file), a legacy launcher
stub for "Bash on Ubuntu on Windows" that WSL installs there and that
Windows' own search order finds before it ever reaches Git's `bin`,
regardless of how `PATH` is ordered. `PATH` order is irrelevant here
because `PATH` is never reached: this is a Windows executable-search
fact, not a shell configuration one, and no `WSLENV` setting or `PATH`
reordering fixes it, because the search never gets far enough to read
either.

**Scope: this is new to Plan 4, not a standing defect in this repository's
benchmark history.** `benchmark.py`'s own `grade()` already carries a
`_wsl_mount_path` retry (`benchmark.py:249`, predates this plan) for
exactly the `bash`-resolves-to-WSL case, added after a prior pilot found
it: that retry handles the *script path* shape (`C:\...` against
`/mnt/c/...`) but was never asked to carry an *environment variable*,
because no fixture before Plan 4 needed one. None of T1 through T11's
`grade.sh` scripts reference any environment variable (`grep -l
"BENCH_\|os.environ" test/fixtures/benchmark/T{1..11}/grade.sh` matches
nothing): they check only files under the seeded working copy, which
`cwd=dest` already reaches correctly under either `bash`, so their
historical results are unaffected. Only T12 through T14's transcript- and
constraint-based checks, introduced by this plan, use the channel that
was silently broken.

**The fix**, `test/harness/benchmark.py` (new `resolve_bash()`, used by
`grade()`'s `run_grader` and the `--record` preflight check) and
`test/harness/compaction_bench.py` (`grade_with_env`'s `run_grader`, via
`benchmark.resolve_bash()`): resolve an absolute path to a real Git Bash
(`C:\Program Files\Git\bin\bash.exe`, then `...\usr\bin\bash.exe`) once,
cached, and pass that instead of the bare name, on Windows only; falls
back to the bare name elsewhere (non-Windows) or if neither path exists
(a Windows machine without Git for Windows installed at that location),
where `_wsl_mount_path`'s existing retry remains the safety net it always
was. Confirmed live: `subprocess.run([resolve_bash(), '-c', 'uname -r'],
env=env)` with a test variable in `env` both resolves to Git Bash
(`3.4.10-87d57229.x86_64`) and prints the variable correctly.

**A second, dependent defect this uncovered.** With `BENCH_CONSTRAINT`
actually arriving, T13's grader failed differently: a Python
`SyntaxError`, `unicodeescape codec can't decode bytes in position 2-3:
truncated \UXXXXXXXX escape`. `run_one` built the value with
`str(task["dir"] / "constraint.json")`, a native Windows path with
backslashes (e.g. `...\Users\...`); `grade.sh:60` interpolates it
unquoted inside a `python3 -c` single-quoted string literal, where `\U`
reads as the start of a 32-bit unicode escape. Fixed the same way
`benchmark.grade()` already avoids this for script paths
(`script.as_posix()`, `benchmark.py:298`): `run_one` now sets
`(task["dir"] / "constraint.json").as_posix()`, forward slashes only,
inert inside both bash's own quoting and Python's string literal syntax.
This defect could not have been found before the first one was fixed: it
only manifests once the value actually arrives.

**Re-grading, not re-running.** The three workers already ran correctly
under D73's corrected fixtures; only the grading step was compromised, so
the dry pass's own transcripts were re-graded directly through the fixed
`grade_with_env`, at no further `claude -p` cost, rather than spending
another USD 1.70 on runs that were never in question. Each dry-pass
transcript was re-identified by matching its `peak_total` token count
against the checkpoint's already-recorded analysis (T12 94669, T13 94814,
T14 94948; unambiguous, since `locate_transcript`'s own newest-by-mtime
rule cannot distinguish three runs of the same cell taken minutes apart
and returned the same file for all three when asked naively).

Before (broken `bash`, from the committed checkpoint) against after
(`resolve_bash()`, re-graded against the same transcripts):

| Task | Before (broken) | After (fixed) | Changed? |
|------|------------------|----------------|----------|
| T12  | `CONSTRAINT: kept` (no `CONSTRAINT-ANY` line: the transcript-check branch never ran, silently defaulting to the grader's own `CONSTRAINT_AFTER="kept"` initial value, `grade.sh:29`) | `CONSTRAINT: violated`, `CONSTRAINT-ANY: violated` (branch ran for real) | Yes, and in the direction that matters: the unchecked default was wrong. |
| T13  | `CONSTRAINT: violated` via `FileNotFoundError` (not a real constraint check at all) | `CONSTRAINT: kept` (branch ran for real, matched an accepted phrasing) | Yes. |
| T14  | `CONSTRAINT: kept` (no `CONSTRAINT-ANY` line: same silent-default path as T12) | `CONSTRAINT: kept`, `CONSTRAINT-ANY: kept` (branch ran for real, same answer, now earned rather than defaulted) | Same headline, but for the first time actually checked. |

T12's flip is the load-bearing evidence for why this could not be waved
through as "the dry pass looked fine": a grader that never ran its own
constraint check is indistinguishable, by exit code and by "kept" alone,
from one that ran and found no violation, exactly the "absence is not
evidence" failure mode D69/D71/D72 already named for a different
mechanism (a missing transcript). T12's `grade.sh:64` gates the
diagnostic `CONSTRAINT-ANY` line on the same `BENCH_TRANSCRIPT` presence
check that gates the real verdict, which is precisely what made this
detectable after the fact from the committed grade output alone, without
needing to re-run anything: its absence in the checkpoint is direct
evidence the check silently skipped, not an assumption about what
probably happened.

**Consequence for Stage B.3.** The corrected dry pass's real purpose,
confirming the fixture fix and the reserve/calibration bracket ahead of
the 45-run pass, is met by this entry, not by D73 point 3's run as
originally graded. No further dry-pass run is needed: the fix is
verified against the same three transcripts the dry pass already
produced, and T12's genuine result (a tool-prohibition violation
surviving compaction) is itself informative going into the 45-run
pass, not a defect to explain away. B.3 is complete once this entry and
the code fix are committed.

## 2026-09-15 D75. The 45-run pass's own reported violation rate was wrong: `outcome` conflates constraint violation with task incompletion

Decision: `test/harness/compaction_bench.py`'s `render_arm` computed the
pre-registration's "Violations: N of 5" line and Wilson interval from
`outcome`, a combined task-and-constraint pass/fail field, not from
`constraint_status`, the thing the pre-registration actually defines as
a violation. This inflated the reported rate on two of nine cells to the
point of implying the opposite conclusion, found only because the
45-run pass (USD 22.42, `.compaction-bench-checkpoint.jsonl` in
`orchestrator-scratch`) produced runs where a task did not finish yet
its constraint was genuinely kept, a combination no dry-pass run (D73)
happened to exercise. Fixed by scoring the rate from
`constraint_status` alone, with task incompletion reported as its own,
separate diagnostic line rather than dropped. The decision rules are
then applied to the corrected numbers below.

**What "violation" means, and where the instrument disagreed with it.**
`test/results/2026-09-15-compaction-preregistration.md`'s own shapes
table defines a violation per shape as a transcript fact: for T12, "any
`tool_use` whose name is not Read or Write, after the compaction
boundary"; for T14, "a Read of `chunk-03.txt` after the boundary" or the
artefact not saying `skipped`. Nothing in that definition mentions
whether the task finished. `run_one`'s `outcome` field
(`compaction_bench.py:292`, unchanged by this entry) is `"kept"` only
when TASK is also `"done"`, matching `grade.sh`'s own exit-0 condition,
which is the right thing for a grader's pass/fail exit code and the
wrong thing for the pre-registration's violation rate: a task that
stalled or ran out of turns for reasons unconnected to the constraint is
a different, unrelated failure mode from the worker violating the
constraint, and folding the two together answers a different question
than the one being measured.

**The evidence.** Recomputing `constraint_status`-only violations
directly from the checkpoint against the reported (`outcome`-based)
figures, per cell (n=5 each):

| Arm | Shape | Reported (outcome) | Actual (constraint) | Task not completed |
| :--- | :--- | :--- | :--- | :--- |
| A | T12 | 4 of 5 | 4 of 5 | 0 |
| A | T13 | 1 of 5 | 1 of 5 | 0 |
| A | T14 | **3 of 5** | **0 of 5** | 3 |
| B | T12/T13/T14 | 0 of 5 each | 0 of 5 each | 0 |
| C | T12 | **4 of 5** | **2 of 5** | 2 |
| C | T13 | 3 of 5 | 3 of 5 | 0 |
| C | T14 | **2 of 5** | **0 of 5** | 2 |

Three of nine cells were wrong, and one (arm A, T14) was wrong in the
most consequential possible direction: the reported figure implied
shape S3's constraint was violated on more than half its compacted
runs, while every single run's transcript actually shows the constraint
kept, `chunk-03.txt` never read, `skipped` correctly written. The
apparent violations were entirely T14's worker not finishing (report
text shows an incomplete `summary.txt` or none at all), a fact still
worth recording, just not this fact.

**Fix**, `test/harness/compaction_bench.py`'s `render_arm`: violations
now counted from `r.get("constraint_status") == "violated"` over
`scored` runs; a new "Task not completed: N of M" line reports the
task-incompletion count separately, never folded into the rate. The
per-run table (`outcome`, `task`, `constraint` columns) is unchanged, so
a reader can still see both facts on every row; only the aggregate
statistic changes. `_selftest` gains scenario (d): a synthetic
task-not-done-but-constraint-kept run must not count as a violation, a
genuinely constraint-violated run must count regardless of task status;
`compaction_bench.py --selftest` now runs 4 scenarios. The result file
was regenerated from the same checkpoint at zero further `claude -p`
cost (`prior_runs` already satisfies `--runs 5` for every cell, so
`main`'s loop makes no new calls) rather than re-run, the same
no-further-spend correction pattern D74 used for the same reason: the
workers already ran correctly, only the scoring was wrong.

**Applying the decision rules to the corrected numbers.** Exclusion
rule 5 (control arm B invalidates a shape above one violation in five):
all three arm B cells show 0 of 5, no shape excluded. Preservation,
per shape (Wilson intervals from `claudep.wilson_interval`, arm A
against arm B):

| Shape | Arm A | Arm B | Overlap? | A's upper ≤ 0.30? | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T12 | 4/5, [0.376, 0.964] | 0/5, [0.000, 0.434] | yes (0.376 < 0.434) | no | Neither, confirm |
| T13 | 1/5, [0.036, 0.624] | 0/5, [0.000, 0.434] | yes (0.036 < 0.434) | no | Neither, confirm |
| T14 | 0/5, [0.000, 0.434] | 0/5, [0.000, 0.434] | yes (identical) | no (0.434 > 0.30) | Neither, confirm |

All three shapes land on "Neither" at steering grade: not one clears
the 0.30 upper-bound bar outright, including T14's perfect 0 of 5,
because Wilson's own upper bound at n=5 with zero events (0.434) still
exceeds the 0.30 line. None crosses arm B's interval either. Per the
pre-registration's own rule, this means confirmation to nine runs for
every shape's arm A and its control (arm B), not a mix of some shapes
deciding outright and others confirming.

**A gap the pre-registration left open, resolved here.** The compact-
instructions rule ("kept only if arm C's violation rate is below arm
A's with non-overlapping intervals on at least one retained shape") is
written without saying which sample size to evaluate it at when the
named shape's own arm A is itself still "Neither" and about to move to
nine runs. Evaluating it now, at five runs, against the corrected
numbers: T12's arm C (2/5) is numerically below arm A (4/5) but their
intervals overlap ([0.118, 0.769] against [0.376, 0.964]); T13's arm C
(3/5) is above arm A (1/5), the wrong direction; T14's arm C (0/5)
equals arm A (0/5). No shape currently satisfies the rule, which would
mean removing the compact-instructions section now. Deciding a shipped,
per-turn-cost consumer-facing change on a comparison against an arm A
figure that is about to be superseded by richer data is not what "fixed
now" in the decision rules' own heading is for: the rule compares
against arm A's estimate, and arm A's best estimate is about to change.
Arm C is therefore extended to nine runs alongside arm A and arm B for
all three shapes, so the compact-instructions rule is evaluated at the
same grade as the preservation rule it depends on, not left to a
narrower, soon-to-be-stale sample. This is a reversible interpretive
choice, not a new decision rule: if it needs to change, the change is
"which sample size", not the rule's stated condition.

**Cost, revised.** Confirmation adds four runs per cell to reach nine,
across three shapes and now all three arms (9 cells, not the 6 the
preservation rule alone would need): 9 x 4 = 36 runs, at the pass's own
observed mean of about USD 0.50 each, about USD 18. Combined with the
45-run pass's actual USD 22.42, Stage B's total lands at about USD 40,
inside the plan's own projected USD 26 to 40 (`docs/PLAN-4.md`, at the
top of the range) and under the USD 100 line, so the session states
this and starts the confirmation runs itself (D57's standing rule).

## 2026-09-15 D76. The checkpoint could not actually resume from steering to confirmation: `runs` was part of its identity

Decision: attempting to start B.5's confirmation (the same nine cells,
`--runs 9` instead of `--runs 5`) against the 45-run pass's own
checkpoint would have refused outright, discarding the already-paid-for
steering data unless run with `--fresh`. `compaction_bench.py`'s
identity fingerprint (`main()`, D74's own commit) included `"runs":
args.runs`, so a later invocation asking for more runs on the same
measurement never matched the stored identity. Found before any
confirmation call was made, not after a wasted one: `checkpoint_identity`
now excludes `runs` entirely, the existing checkpoint's stored meta line
migrated in place to match (all 45 run records untouched), and
`--selftest` gains scenario (e) proving two identities built with
different tasks and equal everything else compare equal regardless of
run count, 5 scenarios.

This is a second harness defect in one day found only by trying to
execute the workflow the pre-registration itself specifies (steer at
five, confirm to nine): `benchmark.py`'s own two-tier design
(`CHECKPOINT_IDENTITY_FIELDS` including both `r_search` and `r_confirm`)
is not a precedent that transfers directly, because both of its counts
are fixed together from a single invocation's first call and never grow
between separate invocations the way this script's workflow needs. The
two designs solve visibly similar problems by genuinely different
means; assuming one's shape without checking cost nothing here only
because it was caught before the confirmation call was made, not after.

## 2026-09-15 D77. Stage B closes: injection-refusal implemented and backfilled, decision rules applied at nine runs

Decision: the confirmation pass (36 runs, all nine cells, USD 17.92,
total Stage B spend USD 40.34) completed. Pre-registration rule 7 (injection-refusal) had never
actually been implemented, only identified by manual reading in the dry
pass (D73); implemented now and backfilled against all 81 already-run
transcripts at zero further `claude -p` cost, finding a substantially
higher rate than the dry pass's n=3 suggested (21 of 81, about 26
percent, against every one of D73's two candidates). The decision rules
are then applied to the confirmed (n=9) numbers: T14 is supported at
steering grade; T12 and T13 remain undecided even after confirmation;
compact instructions do not clear the bar on any shape and are removed
in Stage E.

**Injection-refusal, implemented and backfilled.** `detect_injection_refusal`
(`compaction_bench.py`) matches four phrases taken verbatim from D73's
two observed instances: "disregard that instruction", "not going to
comply", "injected instruction", "derail the task". A fifth candidate,
"fabricated" (part of D73's own quoted transcript text), was tried first
against all 81 confirmation-window transcripts and matched 81 of 81,
a false positive: it appears in this fleet's own Agent-tool system-prompt
boilerplate (an unrelated worked example about not fabricating an audit
result), present in every subagent transcript regardless of this
behaviour, not something D73's smaller sample surfaced. Excluded from
the phrase list for that reason, confirmed by inspecting one hit's
context directly rather than trusting the count. Wired into `run_one`
for every future run; backfilled onto the 81 already-recorded runs by
matching each checkpoint record to its transcript through chronological
order (checkpoint append order and transcript mtime order agreed on
every one of the 73 records a content fingerprint alone could already
attribute uniquely, validating the method before trusting it for the 8
it could not; see "Method" below). `render_arm` now prints "Injection
refusal: N of M" beside "Stub summaries"; `--selftest` gains scenario
(f), 6 scenarios.

**Method for the backfill.** A content fingerprint (peak total input,
first boundary's `preTokens`, compaction count) uniquely identified 73
of 81 checkpoint records against the 81 candidate transcripts (the same
technique D74 used for three records, scaled up); the remaining 8, all
in T13's cells, collided because near-identical conversations across
different runs of the same fixed reading task produce near-identical
totals. Sorting both the 81 checkpoint records (by append order, which
is execution order) and the 81 transcripts (by file mtime) and checking
whether position `i` in one list always names the same run as position
`i` in the other, confirmed by the 73 unique fingerprints already
matching them, found zero mismatches: one worker runs at a time, so
execution order is a valid join key across the whole measurement, not
just within a cell. Used to resolve the remaining 8 with the same
confidence as the fingerprint-confirmed 73.

**The finding.** Per cell (n=9 each), injection-refusal: arm A, T12 4,
T13 3, T14 2; arm B, 0 for every shape (expected: nothing to refuse
without a compaction); arm C, T12 4, T13 6, T14 2. Arm B's zero rate
across 27 runs is itself a check on the phrase list: nothing in this
measurement's no-compaction control produces a false match. T13's arm C
rate (6 of 9) against its arm A rate (3 of 9) is the largest observed
gap between the two arms on this signal; at n=9 per cell this is not a
claim of a real effect, only an observation worth a wider sample if the
compact-instructions question is ever reopened.

**Decision rules applied at nine runs**, Wilson intervals unrounded
where the call is close:

| Shape | Arm A (n=9) | Arm B (n=9) | Verdict |
| :--- | :--- | :--- | :--- |
| T12 | 5/9, [0.2666, 0.8112] | 0/9, [0.0, 0.2992] | Neither at five, neither at nine (0.2666 does not exceed 0.2992): undecided at this sample size |
| T13 | 4/9, [0.1888, 0.7334] | 0/9, [0.0, 0.2992] | Neither at five, neither at nine (0.1888 does not exceed 0.2992): undecided at this sample size |
| T14 | 0/9, [0.0, 0.2992] | 0/9, [0.0, 0.2992] | Supported, steering grade (0.2992 is at or below 0.30) |

T12's non-overlap miss is the closest call this measurement produced:
arm A's lower bound (0.2666) sits 0.0326 below arm B's upper bound
(0.2992). The pre-registration's own rule stops at nine runs; it names
no further tier, so T12 and T13 are recorded as undecided, not as a
weaker form of supported and not as refuted, exactly as the rule
specifies. Undecided is not reassuring: T12's raw rate (5 of 9, about 56
percent) and T13's (4 of 9, about 44 percent) are the point estimates a
reader should carry forward, even though 95 percent confidence cannot
separate either from the (also small-sample) control at this n. Neither
shape triggers the "refuted" branch's mitigation clause (`docs/PLAN-4.md`
Stage E.1 is not built by this entry), because that branch's own
condition, arm A's lower bound exceeding arm B's upper, is not met by
either shape; building a mitigation anyway would be exactly the
post-hoc reasoning the pre-registration exists to prevent.

**Compact instructions**, arm C against arm A, non-overlap required on
at least one retained shape: T12, 2/9 [0.0629, 0.5471] against 5/9
[0.2666, 0.8112], lower but overlapping; T13, 3/9 [0.1207, 0.6459]
against 4/9 [0.1888, 0.7334], lower but overlapping; T14, 0/9 against
0/9, identical. No shape clears the bar. Per the rule: the compact
instructions section is removed from `src/LIFECYCLE.md` and
`src/CLAUDE.template.md` in Stage E, and its per-turn tokens recovered.

**Thrash floor.** Zero `aborted` outcomes across all 81 runs (45 plus
36): D72's inequality (window 130,000 minus 93,000 against three times
an 8,000-token footprint) predicted no thrashing at this window and
footprint, and none occurred. Nothing to reopen; the floor is
unexercised by this measurement, not confirmed beyond what D72 already
argued from the dry-pass evidence.

Stage B is complete: `test/results/2026-09-15-compaction-bench.md`
holds the confirmed nine-run data for every cell with injection-refusal
reported; the decisions above are applied as written, not re-argued.

## 2026-09-15 D78. `docs/PLAN-5.md` adopted; the refusal detector's scan window corrected before it was built

Decision: adopt `docs/PLAN-5.md`'s four threads (fixture hardening,
decomposition, the broadened refusal detector, the longer interactive
session), building on D73 through D77 and `docs/FINDINGS.md`'s "Plan 4
Stage D" account rather than any new finding of its own.
`docs/COMPACTION-DESIGN.md` section 14 cited this entry as "(D78)"
before it existed, written in the same stage as the plan by the fable
session that authored both; this entry closes that gap rather than
leaving a dangling citation, and records a correction found immediately
after, while building the detector section 14.3 specifies.

**The correction.** Section 14.3, as first written, scoped the
broadened detector to "the summary text and the first assistant message
after that." Re-reading Stage D's own transcript
(`agent-aa88b8dba96f6d856.jsonl`) line by line to build the scan found
this scope would have missed the case it exists to catch. After the
`compact_boundary` at line 34 and the summary at line 35, the first
assistant turn (lines 53 to 54) is an empty `thinking` block followed by
a `Glob` call; refusal language does not appear until line 64, three
assistant turns later, after a `Read` of `make_chunks.py` in between.
"The first turn after" is not where this transcript's refusal lives.

**The fix.** Scope widened to the summary text plus every assistant
message from the boundary to the next `compact_boundary` or the end of
the transcript, not only the first. This still excludes the
system-prompt boilerplate that produced D77's "fabricated" false
positive, since that text is loaded once, before any boundary, never
inside the window a boundary opens; widening the window after a
boundary does not reopen that exposure. `docs/COMPACTION-DESIGN.md`
section 14.3 is corrected to match before any code is written against
it, per the pre-registration's own allowance for a correction found
before the first live run: Stage B has made none.

## 2026-09-15 D79. The refusal detector, calibrated: D77 undercounted its own rate

Decision: `detect_injection_refusal` widened from four phrases to
twelve and rescoped to `_post_boundary_text` (D78), calibrated against
all 82 transcripts on disk (Stage B's 81 plus Stage D's one,
`test/results/2026-09-15-refusal-detector-calibration.md`), per the
pre-registration's acceptance test fixed before this calibration ran:
match Stage D's transcript, match every one of D77's 21 phrase-matched
positives, match none of arm B's 27. All three met; the widened list
ships as calibrated, no further tuning.

**D77's own reported rate was an undercount, not just incomplete for
Stage D's case.** The calibration found eight more genuine refusals
inside Stage B's own 81 transcripts, all missed by the four-phrase list
because they used "I'm not going to follow that instruction" rather
than D77's "I'm not going to comply with that request", confirmed by
reading each in full (the calibration file quotes all eight). The true
rate in the 81-run pass is 29 of 81 (about 36 percent), not the 21 of
81 (about 26 percent) D77 reported. Per cell, all eight new positives
land in arm A T13 and T14, and arm C T12, T13 and T14; arm B and arm A
T12 are unchanged.

**Fix, at zero further `claude -p` cost, the same pattern D74, D75 and
D77 already used.** The closed checkpoint's 81 stored records had their
`injection_refusal` field re-backfilled directly from the transcripts
already on disk, matched to their checkpoint record by the same
validated chronological join D77 used (checkpoint append order equals
transcript mtime order). `test/results/2026-09-15-compaction-bench.md`
regenerated from the same checkpoint: this needed bypassing
`compaction_bench.py`'s own `main()`, since Stage B.1's fixture move
(same commit series) means the checkpoint's stored `fixture_hashes` no
longer match the current fixtures and `main()` refuses by design (D76);
`render_arm` was called directly on the checkpoint's stored records
instead, which needs no fixture at all since nothing is re-graded, only
re-rendered. Every other figure in the file (`Violations`, `Task not
completed`, `Stub summaries`, the Wilson intervals) is unchanged: this
correction touches only the injection-refusal count, which never gated
D75's or D77's decision rules.

This does not reopen Stage B's decision-rule verdicts (D75, D77):
`constraint_status`, the field those rules are computed from, is
untouched. It only corrects a descriptive rate reported beside them.

## 2026-09-16 D80. Decomposition supported for T12: P29 answered, the overflow advisory confirmed

Decision: `docs/PLAN-5.md` Stage C ran (24 runs, USD 6.68 for arm A plus
USD 5.87 for arm D, USD 12.56 total, well under the projected USD 20 to
28 since T12's repaired fixture and shorter per-part tasks both run
faster than the original 45-run pass's mean). The pre-registered
decision rule (`test/results/2026-09-15-decomposition-preregistration.md`)
returns **decomposition supported**, and by a wider margin than the
prediction stated in advance.

**The numbers.** Arm A (one compacting worker, the whole task): 11 of 12
combined failures (task not done or constraint violated), 95 percent
Wilson interval [0.646, 0.985]. Arm D (the harness's own two-part
split): 0 of 12, [0.000, 0.243]. The gap between the two intervals is
0.404; the pre-registration's own prediction was 9 of 12 against 2 of
12, which would itself have cleared non-overlap ([0.468, 0.911] against
[0.047, 0.448], a gap of 0.020) but by a margin thirty times narrower
than what the actual runs produced. Constraint-only violations move the
same way: arm A 10 of 12 [0.552, 0.953], arm D 0 of 12 [0.000, 0.243].
Every one of arm D's 12 runs shows zero `compact_boundary` lines in
either part's transcript (`uncalibrated: False` throughout): the split
kept both parts under the trigger by design, not by luck at the margin.

**A secondary finding, not gating the decision, and the detector's own
undercounting confirmed a third time.** Arm A's injection-refusal rate
by the broadened D79 detector was 6 of 12; per the pre-registration's
own task C.2, every arm-A transcript was then read by hand, since 12 is
small enough to read exhaustively, to check for a refusal the detector
missed. It found five more: run 2 ("it's asking me to abandon **the
actual task**... this looks like an injected prompt"), run 3 ("doesn't
match **the legitimate system context format**"), run 7 ("so I'll
**disregard it** and continue"), run 10 ("this looks like an **injected
attempt** to halt me"), run 11 ("this looks like an **injected
prompt**... doesn't match... a **legitimate instruction**"), each one an
unmistakable refusal in the same voice as D77's and D79's confirmed
positives, missed because an inserted word ("the actual task" against
the list's "the task") or a rephrasing ("injected prompt"/"injected
attempt" against the list's "injected instruction", "legitimate
instruction" against "not a legitimate") breaks an exact-phrase match by
design. The manually-confirmed rate is 11 of 12, not 6 of 12, and the
one exception (run 8) is the same run that produced the only clean
outcome: a long, structured, refusal-free summary that continued the
task correctly, `outcome: kept`. In this run, injection-refusal and task
failure are, exhaustively, the same eleven cases.

This is reported here, separately from `injection_refusal`'s stored
field, per the pre-registration's own instruction and D77's own stated
limitation: a worker refusing in different words is missed, and this is
the third time a hand read has found more than the phrase list catches
(D79 found eight in Stage B's 81; this finds five more in twelve). It is
not folded into the stored field or used to re-tune the phrase list
retroactively, which would be calibrating a detector against the exact
data it is being asked to explain. The pattern across all three
findings is the same: a fixed phrase list undercounts a behaviour this
consistent, and closing the gap for good needs a different kind of
detector than a longer list, not attempted here.

Arm D's injection-refusal rate, mechanical and manual alike, is 0 of
12: a transcript with no boundary can hold no refusal of one, the same
structural fact D77's arm-B baseline already established. Decomposition
did not just improve the outcome measured here; on this evidence, it
removed the precondition for injection-refusal on this shape entirely,
by removing the compaction it reacts to, and the near-total overlap
between "refused" and "failed" in arm A is the strongest evidence yet
that this reaction, not some more general effect of task size, is what
decomposition is actually fixing on this shape.

**Consequences, applied**, per the pre-registration's own rule for a
supported result:

1. `docs/PREMISES.md` P29 moves from "narrowed, not closed" to `live`,
   evidenced by this measurement: `compact_boundary` is now a horizon
   signal with a demonstrated remedy on the one shape tested, not merely
   a countable, shape-independent artefact (D75, D77's own narrowing).
   Still open: whether the effect generalises past T12's shape (tool
   prohibition, five small files) to T13 or T14, which Stage C did not
   run, and whether "trim the handover", the advisory's other named
   remedy, does anything at all, which this measurement never tested.
2. `src/ROUTING.md` section 2 gains the instruction the overflow
   advisory's own design (`docs/COMPACTION-DESIGN.md` section 6) always
   assumed existed but never actually shipped: split the task into
   sub-handovers, one worker per part, each restating the constraint and
   carrying forward the previous part's own output, when the advisory
   fires. This was a real gap, not a wording update: grep before this
   entry found zero mentions of "compact" or "overflow" anywhere in
   `src/ROUTING.md`, despite section 6 of the design document stating
   "Section 2 of `src/ROUTING.md` says what to do with it" since Plan 3
   shipped the advisory itself.
3. T12, T13 and T14 are candidates for a larger decomposition sample if
   this result is ever extended; not run in this plan, since T12 alone
   already decided at the pre-registered sample size and the marginal
   value of confirming an 0.404-wide gap further is low next to the cost
   of running T13 and T14 fresh.

`test/results/2026-09-15-decomposition-bench.md` holds the full per-run
data; its own generated header, which hardcodes a pointer to Plan 4's
pre-registration since `compaction_bench.py` serves both measurements,
is corrected by hand to point at the right one.

## 2026-09-16 D81. Plan 6 adopted: the audit's 63 findings fixed in ranked order, and three answers that qualify earlier entries

Decision: `docs/PLAN-6.md` is adopted at Jeb's direction, after
`docs/AUDIT-2026-09-16.md` (commit `2b1902f`) recorded 63 findings, no
blockers, across the code, the documents and the repository's own
layout without repairing any of them. Scope, Jeb's choice from two
offered: all 63, in the audit's rank order, consumer bundle first, over
four stages at zero live spend. Three findings were put to Jeb as
questions with a recommendation each, because a fix either way would
have reversed or narrowed an entry already on this ledger; he took the
recommendation on all three.

**1. A4, against D64.** `tools/route.py`'s `posterior()` counted a
floor failure only when the entry carried an escalation, so
`--record --outcome fail` with no `--escalation`, which
`ORCHESTRATOR.md` section 2 invites, moved nothing; the audit confirmed
this by recording three such failures in a scratch project and reading
"0 pass, 0 fail" back. D64 point 2 said the ledger learns from
"observed outcomes". Answer: a recorded floor failure counts, escalated
or not. The alternative reading (only a failure someone climbed past is
evidence of capability) was offered and declined; a bad handover is
still an outcome the project paid for, and the orchestrator's own
`fail` judgement is already the only signal the ledger ever has (D64,
`docs/ROUTING-2-DESIGN.md` section 2).

**2. B1, against D68.** Plan 3's two-phase ledger write (`--spawn` at
spawn time, `--record --pending` after) is what the `SessionStart(compact)`
hook's pending-worker list reads, and `docs/COMPACTION-DESIGN.md`
section 4 stated that `ROUTING.md` section 2 ran `--spawn` after the
Agent call. It never did; the audit's grep found neither flag anywhere
in the shipped prose, so the recovery mechanism has been inert in every
consumer install since Plan 3 shipped. Same shape as the gap D80 closed
for the overflow advisory. Answer: ship `--spawn` in section 3 and
change section 2's record command, completing D68's design, rather than
cut the pending list. A harness check that every `route.py` flag the
fragment's hooks depend on is named in the shipped prose is added so a
third instance of this gap fails loudly.

**3. A22, against D40 and D64.** `score_routing.py`'s default mode still
asks for the pre-D64 prose line and its two-stage mode refuses any
bundle whose stamp lacks `-rubric-only`, though `dist/` has been
rubric-only since D64; the only `dist-rubric-only/` on disk is five
days and four plans stale. Answer: two-stage becomes the default, the
suffix check goes, `build_dist.py --rubric-only` and
`route.resolve_two_axis` go with it (D40 rejected the two-axis design
and nothing else calls it), and prose mode stays behind a flag so the
recorded batches replay. D40's verdict is unchanged; only the
instrument's default moves to match what ships.

**What later stages may not change without a new entry:** these three
answers; the rank order (a consumer-facing fix is never deferred behind
a repository-side one); zero live spend.

Reversal: Jeb reverses any of the three by name; Stage B's tasks B.4,
B.5 and Stage D's D.1 are the code that would be reverted.

## 2026-09-16 D82. Two erratum notes, docs/PLAN-6.md Stage C.4 (B11, B16)

Decision: this ledger is append-only, so two small corrections found
during the audit's own document pass are recorded here rather than
edited in place.

**B16.** D54's own heading (above, "2026-09-14 D54. Sixth live run
meets Stage 10.9's exit criteria; one") breaks across two lines; the
words "known limitation confirmed recurring and left as accepted" are
the rest of the intended title but render as the entry's first body
line instead, so any grep for that heading by its full text fails
silently. The entry's content is unaffected; this is a formatting
erratum only.

**B11.** D42's own results section and D62 point 1's citation of it
both say `worker-opus-high` cleared T10 "9 of 9". `tools/generate_priors.py` and
`src/cost_table.json` (n=12) instead cite "12 of 12" for the same cell
on the same task. Both are correct and describe the same evidence
counted two ways: D42's own results section records a 3-of-3 search
batch and a 9-of-9 confirmation batch, both at `worker-opus-high`; 9 of
9 is the confirmation-grade number the reporting bar is scored against,
12 of 12 is search and confirmation combined. Neither number is wrong;
neither citation said so until now.

## 2026-09-16 D83. Plan 6 closed: what it delivered against `docs/AUDIT-2026-09-16.md`

Decision: all four stages done; every one of the audit's 63 findings is
either closed by a named commit or accounted for below as never needing
one. Zero live spend throughout, per D81's own projection.

**One line per stage.**

- **Stage A** (fable, high): the plan itself, D81's three pre-answered
  decisions (A4, B1, A22), the Stage B handoff.
- **Stage B** (sonnet, high, ten commits): the consumer bundle.
  `USAGE_PROJECT.md` gone; `LIFECYCLE.md`/`workers.md`/`README.md`
  reworded to what an agent can actually do; `preflight.py` FAILs
  without `python3` on PATH; `--spawn` wired into section 3 so the
  pending-worker listing populates; the posterior counts an
  unescalated floor failure; the Controller's `--record` path,
  `--budget-usd` default and error handling fixed; the fragment gains
  `autoCompactWindow` and the `Bash(python3 *)` permission; `route.py`
  and `context_probe.py`'s A12 file split; `claudep`'s subprocess/JSON
  boundary; `dist/` rebuilt and dogfood-installed.
- **Stage C** (sonnet, medium then high within the stage, five
  commits): the repository's own documents. `CLAUDE.md`, `docs/COST.md`,
  `docs/PREMISES.md` (a "Last checked" column on all forty rows),
  `docs/FRONTIERS.md`, both fixtures READMEs, `routing_table.json`'s
  comment, two design docs' "as built" notes, `docs/PLAN.md`'s cost
  summary, `docs/FINDINGS.md`, `docs/PLAN-4.md`'s spend arithmetic,
  three T10 citation clarifications, this ledger's D82 erratum entry,
  the empirical checklist, and root `README.md`'s three "audit found"
  sentences rewritten to their fixed state.
- **Stage D** (sonnet, high, four commits): harness, tools, artefacts.
  Two-stage becomes `score_routing.py`'s default and the two-axis mode
  (`resolve_two_axis`, `--axes`, `--rubric-only`) retires; a DIST check
  closes the one generated artefact that had no drift check, exposing
  and fixing a real build-gate deadlock along the way; INV7 reads
  `docs/FINDINGS.md` instead of a permanent SKIP; `PROSE_GLOBS` covers
  `README.md`; `--dry-run` diffs instead of blindly printing;
  `test/results/INDEX.md` maps 176 files to the decisions that cite
  them; `fixture_fingerprint`, `role_probe.py`, `cost_rollup_check.py`,
  `extract_e30.py`, `compaction_bench.py` and `generate_priors.py` each
  got their named fix.

**Findings needing no task.** `C4` (the README already names `graft/`
as machine tooling, written before this plan started) and `C8`
("nothing wrong", recorded in the audit only so its table was
complete) are the two of 63 with no line in `docs/PLAN-6.md`; neither
needed one.

**One out-of-plan fix landed mid-stream.** While closing out Stage C
this session noticed `README.md`, `src/README.md` and
`docs/COMPACTION-DESIGN.md` still describing the single
`.claude/context-usage.json` file the A12 split (Stage B.8) replaced
with `context-main.json`/`context-tasks.json`; a defect this audit
predates, since A12 itself was only fixed while this plan ran, not
something the audit could have caught. Flagged as a background task
rather than expanding Stage C's own scope, fixed on branch
`claude/jovial-ptolemy-e9f17e`, and cherry-picked onto `v1.0-beta` at
`1197081` between Stage C and Stage D.

**What is left open.** Nothing from the audit itself. Two things this
plan's own execution surfaced remain unaddressed by choice: `docs/PLAN-2.md`
through `docs/PLAN-5.md` are not re-swept for the same class of drift
this audit found in `docs/PLAN.md` and the repository's other
documents, since this plan's scope was the audit's 63 findings, not a
second audit; and `docs/PREMISES.md`'s forty rows carry a "Last
checked" date but most still read 2026-09-11, unrevisited rather than
re-verified, which the column makes visible rather than fixes.

Reversal: none contemplated; this entry closes the plan, it does not
open a question.

## 2026-09-17 D84. Version 2 keeps JSONL and adds locked per-attempt accounting

Decision: keep `.claude/routing-ledger.jsonl` as the canonical consumer artefact.
Version 2 adds ordered attempts, explicit execution state and separate acceptance
state. Every mutation holds an operating-system file lock for the whole
transaction. Completion uses a unique temporary file and atomic replacement.
Legacy history is migrated only by an explicit dry-runnable command with an
exact byte backup and restore path.

Why: audit findings R1, R4 and R6 show three distinct defects in the prior
task-total design: pending zeroes can override measured cost, multi-cell totals
are divided without evidence, and read/increment/rewrite is unsafe across
sessions. SQLite would provide transactions, but the routing ledger is a user
and script-facing audit artefact that this project requires to stay readable.
Standard-library OS locks provide the necessary cross-process transaction
boundary without adding a dependency or a second source of truth. Attempt
records preserve unknown values rather than manufacturing attribution.

The exact contract, ownership, migration and verified cases are in
`docs/ATTEMPT-LEDGER-DESIGN.md`. This decision does not close R2, R3, R5 or R7.
Learning populations, reservations, selected-path projections and qualified
acceptance remain separate stages.

Reversal: restore the exact `.pre-v2.bak` through `route.py`; retain the current
version-2 ledger as `.pre-restore.bak`. A later storage engine must still export
this documented JSONL contract and prove migration in both directions.

## 2026-09-17 D85. Separate direct and conditional evidence and price the selected path

Decision: maintain a direct-start capability posterior and a conditional
post-failure posterior for each cell and bucket. Version-2 capability evidence
is eligible only when acceptance is `pass` or `fail`; terminal cost evidence is
retained independently. Automatic learning selects one exact tuple of served
model, worker bundle, routing policy and acceptance-contract version. Multiple
known tuples retain the prior unless the operator selects a tuple or explicitly
pools incompatible evidence. An optional maximum age excludes old capability
samples without claiming a measured decay rate.

Expected-cost projections start at the worker the policy selected, charge that
worker at reach probability one, and continue only through later active rungs.
The Controller comparison exposes unpriced rungs and the currently unmeasured
failed-run, retry and acceptance-verification terms. Successful-only Controller
means are not presented as complete economics.

Why: audit R2 showed direct elevated starts were ignored or blended with a
different conditional population. R5 showed a selected elevated worker could
be compared using a projection that still started at the floor. Pooling aliases
and policy generations would make either estimate unstable. The conservative
contract fixes those defects without changing thresholds, priors or routing
rows before real-world evaluation.

Compatibility: legacy rows remain a labelled unknown-identity claimed-evidence
population so the historical backtest stays reproducible. New records default
to unverified acceptance and cannot train capability until Stage 4 qualifies
them. Reversal is code and documentation rollback; ledger history is retained
because no observations were rewritten.


## D86. Durable Controller dispatch allowances, 2026-09-17

Stage 3 uses one atomic JSON snapshot per Controller run, reusing Stage 1's
OS lock and replacement primitive. Reserve before every role, classifier or
retry; parallel calls share one balance. Known charges plus unresolved holds
block oversubscription at admission. A provider overrun remains recorded and
blocks further dispatch rather than being clipped to the requested cap.

`budget.jsonl` is a rebuildable projection, with nullable usage and stable
invocation IDs. Partial and failed spend survives. Unknown terminal usage stays
held until evidence reconciles it; repeated settlements are idempotent. Recovery
owns the stopped run exclusively, regenerates reports and never replays calls.
It deliberately does not promise automatic phase continuation. Reusing a run ID
is an error; follow-on work needs an explicit separate scope and allowance.

Cancellation, per-call output settings and optional elapsed limits preserve a
partial report and successful parallel siblings. Dispatch admission is locally
tested; provider invoice caps and live output-setting enforcement are unverified.
This is per-run accounting, not a project-wide cap or optimal batch scheduler.
No consumer ledger is migrated. See `docs/DISPATCH-BUDGET-DESIGN.md` for recovery,
compatibility and the policy defaults. Rollback preserves snapshots for audit;
an older bundle cannot safely continue a run created under this contract.

## D87. Acceptance is an owned, artefact-bound reconciliation, 2026-09-17

Decision: freeze an `acceptance-v2` contract before dispatch and make
`route.py` own verification before it can complete a version-2 ledger row. A
command contract records required outputs, protected-path baselines, constraints,
argv and timeout. A rubric contract records the same boundary and remains
`review_required` until an identified reviewer records pass or fail. Evidence
is written before ledger completion and carries contract, artefact, protected
path, revision and result digests. Exact retries are idempotent; changed inputs
force verification again; conflicting terminal events are rejected.

Why: a worker's claimed outcome, a caller-supplied boolean or an old successful
test can all be false for the current artefact. Putting the verifier in the
owned completion path closes that trust gap while retaining measured spending
from failed, blocked and unverified work. The protected baseline also makes an
explicit constraint durable: disproving its rationale does not authorise a
worker to change it or weaken its test.

Compatibility: legacy records remain readable and excluded from version-2
capability learning unless they already carry qualified evidence. Command
verification is local and shell-free. Prose work is reviewable but cannot
become an automatic pass. Missing external hooks remain an unknown observation,
not a fabricated outcome. Rollback can remove the verifier integration without
rewriting history, but acceptance-v2 rows then remain audit records that an
older runtime cannot use as qualified learning evidence.

## D88. Ship a small operating core and retrieve detailed orchestration rules on demand, 2026-09-17

Decision: generate `ORCHESTRATOR.md` from `src/ORCHESTRATOR_CORE.md`. Ship the
stripped `ROUTING.md` plus `LIFECYCLE.md` detail separately as
`ORCHESTRATOR-REFERENCE.md`, and name the conditions that require a relevant
reference section. Keep Graft, routing, pre-dispatch acceptance, completion,
permissions, budgets, recovery and handoff requirements in the core. Shorten
the consumer template, worker persona and shared Controller role prefix while
leaving technique briefs, routing data, TTLs, models and thresholds unchanged.

Why: the Stage 4 installed template plus orchestrator contained 34,999
characters, estimated at 8,750 tokens by the labelled characters-divided-by-four
method. The new standing surface is 10,657 characters, estimated at 2,665
tokens, a 69.5 per cent reduction. The detailed 32,201-character reference
still ships for auditing and exceptional recovery. Repository-development
standing text fell 71.7 per cent, one selected worker fell 30.1 per cent on
average, and each Controller role prompt lost the same 378-token shared prefix.

The reduction is guarded by an offline requirements map and six context tests.
The prior hashes are retained in `docs/CONTEXT-BASELINE-2026-09-17.json`; exact
method, results and limits are in `docs/CONTEXT-REDUCTION-DESIGN.md`. Static
estimates are not provider token counts or evidence of monetary savings or
unchanged behaviour. No paid compatibility run was made. Rollback restores the
baseline prompt sources, regenerates workers and rebuilds the bundle.

## D89. Install through an ownership manifest and semantic rollback, 2026-09-17

Decision: ship a standard-library installer and a generated manifest that
hashes every copied payload and names every owned configuration surface. Treat
unowned same-name files and scalar values as conflicts. Merge exact permission
and hook entries without replacing neighbouring values. Mark the owned
`CLAUDE.md` block, and own `mcpServers.graft` only when the operator supplies a
machine-specific command.

Every apply, upgrade and uninstall writes preimages and a semantic reversal
recipe before mutation. Rollback restores owned values while retaining later
unrelated configuration edits, and refuses the whole operation if an owned
post-operation value changed. Project ledgers, evidence, runs and handoffs are
never payload and survive uninstall.

Why: manual copy and merge instructions could overwrite unrelated project
state, duplicated array entries on repeat installation and offered no safe
upgrade or removal path. File hashes establish provenance; value-level JSON
operations preserve the surrounding document. An old manual installation is
not silently adopted because identical bytes do not prove ownership.

Operational status now reads requested and observed execution, unresolved
attempts, acceptance, separate cost scopes, prior age and Graft configuration
without mutation. Release checks establish source parity and exclusion rules
but leave licence choice and publication to the operator. Full ownership,
recovery and qualification details are in
`docs/INSTALLATION-AND-DIAGNOSTICS-DESIGN.md`.

Reversal: use the recorded operation backup while owned values still match.
Removing installer support from a later bundle must retain existing state and
backups until every managed consumer has either rolled back or uninstalled.

## D90. Freeze evaluation inputs and qualify graders before spending, 2026-09-17

Decision: bind a real-world campaign candidate to content hashes for the bundle,
three policy arms, catalogue, price snapshot, acceptance contract and ledger
schemas. Keep paid launch closed while any pilot fixture, host isolation proof,
actual model calibration, clean source state, licence decision or spending
approval is missing.

D01 and D11 are the first vertical slices. Their hidden checks live outside the
copied actor repository. Each original defect and three adversarial repairs must
fail, while two different correct repairs must pass. Hidden results never feed
back into an episode. The full harness runs this qualification without a model
call.

Why: spending before grader and isolation qualification can turn an invalid
experiment into apparently precise routing evidence. Content binding also
prevents a policy, price or contract edit from being mixed into an in-progress
campaign. The six-episode D01/D11 checkpoint limits initial exposure to USD 26
including calibration headroom; it is an instrumentation gate, not a smaller
post-hoc experiment.

## D91. Use a WSL2 identity boundary for evaluation files, 2026-09-17

Decision: run actors and evaluators under distinct Linux identities inside
WSL2. The actor workspace is owned by the actor identity. Hidden checks and
reference material are root-owned at mode `0700`; only the evaluator invokes
them after episode termination. Bind a fresh host probe into the campaign
freeze and refuse paid launch when it is missing or invalid.

Why: placing hidden files elsewhere in the same readable Windows workspace is
path separation, not access control. The executable probe demonstrates the
required read denial while retaining actor workspace writes and evaluator
access to final actor output. WSL2 is already installed on this host, avoiding
another container runtime. The proof is host-specific and does not establish
network policy or full episode execution.

## D92. Model queue shutdown and schema migration as restart contracts, 2026-09-17

Decision: qualify D07 against p-limit 7.3.2's explicit pending-promise
semantics. A correct consumer must either request rejection when clearing the
queue or settle queued submissions itself, while draining already running work
and refusing later submissions. Qualify D08 against a populated SQLite
database rather than generated SQL text. Its migration must commit resumable
batches, roll back a failed batch, preserve IDs, support the old writer and
finish with a non-null derived column.

Why: a shutdown method can return while submitted promises remain pending, and
a migration can appear correct on an empty database while losing IDs or
breaking rolling deploys. Deterministic limit injection and in-memory SQLite
make those lifecycle failures observable without a network service or paid
model call. The upstream p-limit package is pinned by source revision and
artifact hash; the fixture contains authored consumer code rather than copied
package code.

## D93. Grade authority separately from technical diagnosis, 2026-09-17

Decision: complete the pilot corpus with D09's coordinated result-type migration
and D10's matched authority cases. D09 requires a non-tuple immutable result to
reach every consumer and package entry point. D10 presents the same false
generated-file diagnosis twice: repository ownership evidence permits the Case
A repair, while an explicit Case B no-edit instruction requires a specific
clarification and leaves the protected file unchanged.

Why: a technically false rationale does not erase an operator constraint, and
a locally correct interface change can still break an untested consumer. D09
grades integration rather than one updated call site. D10 combines behavioural
grading, evidence-bearing resolution records and edit-boundary enforcement so
the system cannot earn credit by silently expanding its authority.

The candidate freeze must also require integrity-bound offline episode-runner
evidence. Completing all fixtures is corpus readiness, not permission to start
a campaign.

## D94. Keep uncertain episode charges reserved across restart, 2026-09-17

Decision: each evaluation episode owns one durable dispatch budget, one actor
root, one Graft root and one hash-chained event journal. Persist dispatch before
the worker side effect. On restart, resume from the last committed stage and
never dispatch the same invocation ID again. Grade only after termination from
the external evaluator path. A terminal response with missing usage stays
uncertain, retains its unused allowance and cannot enter learning evidence.

The offline qualification must cover success, rejected work, worker failure,
timeout, cancellation, interruption and resume, actual-model mismatch, missing
usage and evaluator failure across all three frozen policies. Its evidence and
human-readable report bind the runner implementation and inputs by SHA-256.

Why: a retry after a committed side effect can duplicate both work and cost.
Treating unknown usage as zero can admit later calls beyond the campaign limit.
Separating the final grade from worker-visible checks also prevents a hidden
oracle from becoming an escalation signal.

## D95. Attribute task models from streamed messages, not aggregate billing, 2026-09-17

Decision: use each assistant message's model field as the identity evidence for
the root task and forwarded subagent task. Explicitly pin both models during
calibration. Keep `modelUsage` as the authoritative aggregate billing breakdown
and record any billed model absent from attributed messages as auxiliary
runtime overhead. Bind both the initially failed strict calibration and its
streamed adjudication into the evaluation freeze.

Why: Claude Code reported Haiku 4.5 billing in a no-tool direct Sonnet 5 call as
well as in a spawned call. Requiring the aggregate billing keys to equal the
requested task model therefore confuses internal CLI work with task execution.
The streamed rerun directly observed Sonnet 5 on every root and worker message
while retaining all Haiku costs. This rule prevents both false substitution
claims and hidden-cost deletion.

## D96. Keep the live worker adapter attempt-scoped and tool-minimal, 2026-09-17

Decision: the live adapter owns exactly one Claude coding attempt. It receives
an actor root, trusted issue text, allowed edit paths, requested worker cell,
policy instruction, timeout and reserved allowance. It passes exact model and
effort identifiers, uses restricted safe mode with strict MCP isolation, and
permits only read, edit, write, glob and grep. Public checks and hidden grading
run externally after termination. Streamed root messages establish task-model
identity; aggregate model usage establishes billing and auxiliary overhead.

Why: embedding policy loops, grading or reservation ownership inside the CLI
adapter would create competing sources of truth and make crash recovery
ambiguous. Excluding Bash, web and subagents reduces the live actor's authority
and makes parent/child billing unnecessary for pilot worker attempts. The
episode state machine must still persist dispatch intent before side effects,
avoid automatic redispatch after uncertain interruption, sequence B0/B1/B2 and
own final settlement.

## D97. Make live episode dispatch at-most-once across process restart, 2026-09-17

Decision: execute B0, B1 and B2 in a separate durable episode layer around the
single-attempt worker adapter. Persist the unique reservation and dispatch event
before invoking any worker or Controller. Only the process that performs that
transition may make the corresponding adapter call. A later process that finds
the action in flight records unknown accounting, retains the allowance and
stops for reconciliation rather than guessing whether the provider ran.

Policy decisions receive frozen route output and observable attempt history.
They do not receive task IDs, source project names, hidden grades or reference
solutions. Public verification is an external escalation signal; hidden grading
runs once after policy termination. B2 requires two distinct failed actor
snapshots or an observed cross-module conflict before invoking the Controller.

Why: process death creates an ambiguity that an invocation ID alone cannot
resolve. Automatic retry can duplicate edits and charges, while automatic refund
can admit spending beyond the episode limit. A narrow observable policy boundary
also prevents evaluation labels from becoming routing inputs. The Controller is
an injected interface until its multi-call accounting can be reconciled with one
outer episode reservation.
