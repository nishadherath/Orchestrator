# Premise ledger: the routing layer

Built 2026-09-11 by Claude (Opus 5, xhigh) as `docs/PLAN.md` Stage 4, the
Framer's step from `src/System/SYSTEM.md`. Forty premises, the cap
`SYSTEM.md` sets. The seed is `docs/REVIEW.md`'s five-row sketch under "The
premise ledger, turned on the routing table"; every row there survives here,
four of them reclassified more precisely.

The ledger's purpose is not to catalogue what the project believes. It is to
separate what the project has verified from what it has assumed, so that
effort goes to the assumptions that are load-bearing rather than to the ones
that are merely visible.

## How to read this

Each premise carries a class, in `SYSTEM.md`'s vocabulary:

| Class | Meaning | What to do with it |
| :--- | :--- | :--- |
| law | A fact of the platform or of mathematics that no decision here can change | Depend on it, and re-verify it on a version bump |
| maths | An exact consequence of arithmetic | Depend on it; check the arithmetic once |
| policy | A choice someone made, reversible by another choice | Know whose choice, and what it costs; never mistake it for a fact |
| habit | Inherited practice nobody chose deliberately, usually from human project management | Interrogate it first; this is where the cheap wins are |
| unverified | Asserted but never measured | Either measure it, or stop resting weight on it |

And a status: `live` (in force), `pressured` (in force, but the evidence is
running against it), `falsified` (disproved and retained here so the
disproof is not relearned), `open` (nobody has checked).

A premise is load-bearing when removing it changes what the system does. The
last section names the load-bearing unverified ones, which is the list
`SYSTEM.md` says a quick-mode answer must always carry.

## Group A. The assessment axes

| Id | Premise | Class | Source | Confidence | Cheapest verification | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P01 | Task difficulty, for routing, decomposes into exactly three axes | policy | `ROUTING.md` section 1 | low | Score a two-axis variant against the same fixtures; Stage 6 builds it | open |
| P02 | Intelligence sensitivity predicts which model class a task needs | unverified | `ROUTING.md` section 1; the axis carries the model choice in every row | low and falling | A benchmark task whose openness forces a cell above the floor; Stage 7 | pressured |
| P03 | Horizon can be assessed before any tool call is made | habit, from human project estimation | `ROUTING.md` section 1 | low | Already done, five times over: F03, F05, F08, F11 and F18 each needed correction on horizon specifically (D23 to D33) | pressured |
| P04 | Blast radius is a property of the deliverable, not of the situation it concerns | policy (a stipulation) | `ROUTING.md` section 1, added after F13's wobble | high as a definition | Not applicable; a stipulation cannot be wrong, only unhelpful. Its usefulness shows as fixture stability on F13 and F18 | live |
| P05 | Blast radius warrants a higher cell | policy (risk appetite, not capability) | `ROUTING.md` section 2, where blast separates `worker-sonnet-low` from `worker-opus-xhigh` on open work | unmeasurable by current instruments | None exists. See P33 | live, load-bearing |
| P06 | The three axes are independent enough that a triple is a meaningful address | unverified | Implicit in the table's shape | low | Free, and done below: sensitivity predicts horizon at 70.6 percent against a 35.3 percent base rate across the seventeen assessed fixtures | pressured |

## Group B. The routing table

| Id | Premise | Class | Source | Confidence | Cheapest verification | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P07 | Routing each task to the cheapest sufficient cell costs less overall than sending everything to one capable cell | unverified (the project's thesis) | `CLAUDE.md`, "What this repository is"; `BENCHMARK-DESIGN.md`'s opening | low, and contradicted for the measured territory | Compare cost per solved task against B0 on Stage 7's task set | pressured |
| P08 | A routing row is a passive destination: adding one affects only tasks that route to it | falsified (was habit) | D13, re-confirmed D22 to D27 | high that it is false | Done twice, about USD 9 a pass | falsified |
| P09 | Covering all eighteen axis triples is desirable in itself | falsified (was habit) | D9 proposed it, D13 withdrew it | high | Done: the attractor experiment | falsified |
| P10 | Fifteen cells, three models by five efforts, is the right granularity | policy | `CLAUDE.md` fixes the matrix; `tools/cells.py` declares it | medium as policy, untested as design | Count what is reachable: nine of fifteen are routed, six are labelled "not in the routing table" and are paid on every orchestrator turn | live, with measured waste |
| P11 | `max` shows diminishing returns; sonnet at `max` loses to opus at `high`; fable at low effort wastes the model | unverified (three claims, merged) | `ROUTING.md` section 2 constraints, stated as fact | low; no measurement exists for any of the three | One benchmark task at two cells, nine runs each | open |
| P12 | Taking the cheaper of two defensible cells and escalating on evidence beats rounding up | policy, and the one the design leans on hardest | `ROUTING.md` sections 2 and 4 | medium | Count escalations in real use; nothing instruments this today | live, uninstrumented |
| P13 | `worker-opus-xhigh` is preferred to `worker-fable-xhigh` unless the task demands sustained self-directed investigation | policy with fixture backing | D9's tie-break, D21; F11 and F12 against F18 | medium | Reproducibility is at reporting grade (all three 9 of 9, 2026-09-11); the destinations themselves are unmeasured | live |
| P14 | Asking the user costs more than a worker starting on a slightly wrong reading, so spawn is the default | policy | D10, `ROUTING.md` section 1.1, 1,810 characters paid every orchestrator turn | medium | Measured once: nine spurious clarifies before the rule (E12), exactly one correct clarify per run after | live |
| P15 | Handover quality is fixed, so the cell is the only lever on outcome | habit, never stated aloud until now | Implicit: no decision entry, fixture or benchmark task varies the handover prompt while holding the cell constant | none | Run one benchmark task at the floor with a deliberately better handover, nine runs, against the same task's recorded floor result | open |

## Group C. The fixtures

| Id | Premise | Class | Source | Confidence | Cheapest verification | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P16 | Each fixture's assessment triple is the correct reading of its task | policy (one person's judgement, confirmed 2026-09-05 and 2026-09-07) | `routing.jsonl` `assigned_by`; `test/fixtures/README.md` | medium for reproducibility, unmeasured for correctness | Reproducibility is measured: 16 of 18 clear the bar at reporting grade (2026-09-11). Correctness has no instrument | live. Merges 51 premises |
| P17 | Each fixture's `expected_cell` is the cheapest sufficient destination for its triple | unverified above the floor, measured at it | `routing.jsonl`; `BENCHMARK-DESIGN.md` states plainly that expected cells are judgement until the benchmark supplies a frontier | high at the floor (T1 to T8, each 9 of 9), low above it | Stage 7 | pressured. Merges 17 premises |
| P18 | Fixture agreement measures routing appropriateness | false as stated; it measures agreement with a human label | `score_routing.py`'s own docstring uses the phrase | high that the two differ | Definitional; see the metric section | corrected here |
| P19 | Eighteen fixtures represent the work the orchestrator will actually meet | unverified | Implicit in tuning the table against them | low | Route a sample of real backlog tasks and score agreement, which is E13 repeated at more than two tasks | open |

## Group D. The platform

| Id | Premise | Class | Source | Confidence | Cheapest verification | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P20 | Effort is subagent-only; agent teams flatten it (invariant 1) | law | Documentation 2026-09-05; harness INV1 | high | `preflight.py`, free, every run | live |
| P21 | A per-invocation `model` beats frontmatter (invariant 2) | law | Documentation, resolution order | high | Harness INV2 asserts the instruction; obedience is measured by `score_routing.py` | live |
| P22 | `CLAUDE_CODE_EFFORT_LEVEL` beats frontmatter effort (invariant 3) | law | Documentation | high | `preflight.py` | live |
| P23 | `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` flattens every cell (invariant 4) | law | Documentation | high | `preflight.py` | live |
| P24 | Haiku is excluded from the matrix (invariant 5) | policy; its original justification was falsified | D5; E8 disproved "haiku has no effort levels" | high that it is a policy | Not applicable; the exclusion is a decision | live as policy, open as a question |
| P25 | A blocked model is substituted, not failed (invariant 6) | law | Documentation | high | `preflight.py` checks `availableModels` | live |
| P26 | A user-stopped worker cannot be resumed; a `TaskStop`-stopped one can (invariant 7) | law, verified | E3 and E4 (2.1.245); E4 re-verified 2026-09-11 on 2.1.263 | high | Done twice | live |
| P27 | The `/tasks` row is the ground-truth signal for what actually ran | falsified for any agent reader | `CLAUDE.md` "Verification is the hard problem" signal 1; `LIFECYCLE.md`; `src/commands/workers.md` | high | Done, free: E19, 2026-09-11 | falsified for agents |
| P28 | The worker transcript records model and effort and is readable by the orchestrator | law | E7 (2.1.245), re-verified 2026-09-11: the `.jsonl` carries both, the `.meta.json` sidecar carries neither | high | Done | live, and now the only agent-readable verification signal |
| P29 | A `compact_boundary` entry is a reliable signal the cell was undersized | reclassified 2026-09-15 (D68): a horizon signal, not a capability one, since every cell has the same window. The entry itself is now confirmed real (D71, E30): observed 3 times and once, shape and countability confirmed live | `CLAUDE.md` "Verification is the hard problem", signal 2; `docs/COMPACTION-DESIGN.md` section 6; D71; narrowed further by `docs/PLAN-4.md` Stage B (D75, D77): 81 runs across three task shapes (T12, T13, T14), same cell and window | live, 2026-09-15: four `claude -p` runs (E30), then 81 more (Stage B). `test/results/2026-09-15-compaction-bench.md` has the committed record; E30's own four are still an uncommitted throwaway probe, per Dogfooding practice | done for existence and shape across more than one task now, not just one: every one of Stage B's nine cells (three shapes, three arms) that compacted did so within a narrow band of the window regardless of shape, a repeatable, shape-independent artefact of this cell and window. Reliability as a signal that decomposition specifically would help remains untested | narrowed, not closed: the boundary's existence and shape-independence across three tasks is now confirmed, well beyond the one task E30 gave it. What Stage B never measured is the actual open question, whether a compacted cell would have done better decomposed; it measured constraint preservation across a compaction, a different question that happens to use the same signal. Still open, and would need a comparison Stage B was not designed to run |
| P30 | A spawned worker's cost rolls up into the parent's `total_cost_usd` | law, verified | E14, 2026-09-07 | high | Done | live |

## Group E. The benchmark method

| Id | Premise | Class | Source | Confidence | Cheapest verification | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P31 | A deterministic exit code is the only trustworthy grader when capability is the thing under test | policy, well argued | `BENCHMARK-DESIGN.md` | high | Not applicable | live |
| P32 | Planting a known defect converts diagnosis into a string match without changing the task's difficulty | unverified, and three times defective in practice | `BENCHMARK-DESIGN.md`; D16, D17, D30 | medium | The five-phrasing grader test the plan requires from T9 on | live with a known failure mode |
| P33 | Blast radius cannot be measured by this method | law of the method, conceded by the design | `BENCHMARK-DESIGN.md` | high | Not applicable | live. Consequence: P05 can never be verified by the benchmark |
| P34 | Synthetic plantable-defect tasks stand in for the real work the orchestrator will route | unverified, flagged by the design itself | `BENCHMARK-DESIGN.md`, "What this cannot answer" | low | The same experiment as P19 | open |
| P35 | R_search of 3 steers, R_confirm of 9 reports, at a 0.7 Wilson lower bound | maths on a policy base | `BENCHMARK-DESIGN.md`; D15 corrected R_confirm from 8 | high | Verified this session: eight of eight gives 67.6 percent, nine of nine gives 70.1 percent | live, now applied to routing too (D37) |

## Group F. The economics

| Id | Premise | Class | Source | Confidence | Cheapest verification | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| P36 | The router's own cost is small relative to the work it routes | falsified | `docs/COST.md`, 2026-09-11: mean opus verdict USD 0.1645 against mean floor run USD 0.1641 | high; 108 verdicts, 96 runs | Done | falsified at the floor, where every measured task has landed |
| P37 | Opus is the better orchestrator, and worth its cost | split: "better" verified, "worth it" unverified | 2026-09-06 (88.2 against 62.7 percent, non-overlapping); 2026-09-11 baseline, 95.7 percent at reporting grade | high on accuracy, none on value | Value needs the cost of a wrong routing decision, which nothing measures | live, half-measured |
| P38 | Prompt caching makes repeated routing runs cheaper | law with a boundary, measured | Sequential runs fall 20 to 54 percent; E16 found no sharing across three genuinely parallel launches | high | Done | live, boundary known |
| P39 | A worker performs the same whether or not it is told its own cell | unverified, and untested by construction | All fifteen `model-specific-*` sections in `WORKER_PERSONA.md` are empty; the generator omits an empty section entirely | none | Fill one section, re-run one benchmark task at the bar. No code change needed | open |
| P40 | The orchestrator obeys the rubric it is given | measured | 2026-09-11 baseline, 155 of 162 | high overall, with two known exceptions | Done, and repeatable at USD 27 a pass | live, with F09 a reporting-grade counter-example |

## What the merging cost

`SYSTEM.md` caps the ledger at forty and requires the Framer to merge. Two
merges did nearly all the work, and both are findings in their own right.

**The fixtures collapse 68 premises into 2 rows.** Seventeen fixtures carry
an assessment triple (F16 carries none, since its confirmed answer is to
clarify), so the suite asserts 51 axis judgements and 17 destination
judgements. P16 and P17 stand for all 68. The compression is honest only
because the 68 share one provenance and one epistemic status: they are one
person's readings, confirmed once in a review, and they rise or fall
together. The number is worth stating plainly. The routing table is tuned
against 68 judgements of which the project has measured the destinations of
eight, all at the floor.

**The constraints paragraph collapses 3 premises into 1.** P11 merges three
separate quality claims that `ROUTING.md` states as fact and nothing has
measured. They share a class, a source and a verification, so they merge
cleanly; the merge should not disguise that they are three distinct
unmeasured assertions shipped to every consumer on every turn.

The ledger fits the cap, so the fit is not itself a finding. What the fit
conceals is: the routing layer rests on about 110 distinct premises, and 40
is a readable summary of them, not a complete enumeration.

## Two free checks the ledger prompted

Both are arithmetic over files already in the repository, run 2026-09-11.
Neither needed a model call.

**The fixture suite confounds sensitivity with horizon (P06).** Across the
seventeen assessed fixtures, knowing a task's sensitivity predicts its
horizon 70.6 percent of the time, against a 35.3 percent base rate from
guessing the most common horizon. That is a 35 point lift. The other two
pairings are weak by comparison: horizon predicts blast at 70.6 percent
against a 58.8 percent base rate (12 points), and sensitivity predicts blast
at 64.7 percent against the same base rate (6 points).

The consequence is a warning for Stage 6, and it needs to reach Stage 5
before that stage pre-registers its comparison. The two-axis variant drops
horizon and keeps sensitivity, which is exactly the most confounded pair in
the suite. If dropping horizon barely moves agreement, the fixture suite
cannot distinguish "horizon was redundant" from "sensitivity was standing in
for horizon all along". Fixtures that break the confound, mechanical work
with a long horizon, open work with a short one, are the ones that would
make the experiment decisive, and the suite is thin in exactly those cells.

**Eleven of eighteen triples have a fixture behind them.** Of the eighteen
possible triples, eleven are fixture-backed, five are covered by a table row
with no fixture landing on them, and two are deliberate documented gaps.
This matches the harness's own ROW-BACKED count exactly, so it is not a new
measurement, but it reframes the five: `(mechanical, medium, consequential)`,
`(open, medium, consequential)`, `(open, short, consequential)`,
`(structured, long, consequential)` and `(structured, short, consequential)`.
Four of those five are consequential, which is to say the table's least
evidenced rows are concentrated on the axis the benchmark cannot measure at
all (P05, P33). That is not a coincidence. It is the same gap seen from two
directions.

## Goal ladder

`SYSTEM.md` asks for three rungs, so that the stated goal can be replaced by
the goal behind it where that turns out to be cheaper to reach.

**Rung 1, the stated goal.** Route each task to the cheapest worker cell
that clears the bar.

**Rung 2, the goal behind it.** Get the same quality for less money than
sending everything to one capable cell. This is `CLAUDE.md`'s own framing and
the reason the benchmark exists. Rung 1 is one mechanism for reaching rung 2,
not the only one.

**Rung 3, the goal behind that.** Spend the least total cost, in tokens, wall
clock and the user's attention, per unit of finished work that can be
trusted without re-checking. Rung 3 is where the project's value actually
sits, and at rung 3 routing competes for budget with levers this project has
never compared it against. The ledger names four: handover quality (P15,
untested by construction), the clarify rule's 1,810 characters on every turn
(P14), the escalation policy itself (P12), and the six unrouted cells whose
descriptions are paid on every turn for no traffic (P10). A better handover
might lift the floor's capability more cheaply than routing above it ever
can, and nothing here has tested that.

## Dissolution check

`SYSTEM.md` asks whether the problem stops existing once a premise is
reclassified. Reclassify P36, the router's cost, from assumed-small to
measured, and much of the routing problem does dissolve. The arithmetic is
below and it is not close.

Let `R` be the router's cost for one verdict and `F` the cost of one run at
the floor cell. Both are measured, 2026-09-11, `docs/COST.md`: `R` is USD
0.1645 across 108 opus verdicts, `F` is USD 0.1641 across 96
`worker-sonnet-low` benchmark runs.

Compare two designs on the same task. The table assesses, then runs the cell
it chose. B0 runs the floor, and escalates one cell up if the work fails its
stated acceptance criteria.

| Task | Table | B0 | Result |
| :--- | :--- | :--- | :--- |
| Belongs at the floor | `R + F` = USD 0.3286 | `F` = USD 0.1641 | B0 is 2.00 times cheaper |
| Needs one rung up, at cost `X` | `R + X` | `F + X` | B0 cheaper by USD 0.0004, a tie |

Generalise with `p`, the fraction of tasks that genuinely fail at the floor.
The table's expected cost is `R + (1 - p)F + pX`; B0's is `F + pX`. The table
wins when `R < pF`, which is to say when the router costs less than the floor
run it lets you skip, weighted by how often skipping it is right.

At the measured figures that condition is `p > 100.2 percent`. **No
floor-failure rate can make the current table cheaper than B0, because the
router costs slightly more than the entire floor run it exists to avoid.**
The most routing can ever save is one floor run, and it charges more than one
floor run to do it.

Three things this arithmetic does not say, all of which matter.

**It is generous to the table, not to B0.** It assumes the router is always
right. The 2026-09-11 baseline puts it at 95.7 percent, and every mis-route
adds a wasted run to the table's side.

**It assumes one rung of escalation.** A task needing two or more rungs above
the floor makes B0 pay for every cell it climbs through, and there the table
starts to win: the table beats B0 whenever `R` is less than the sum of the
cells B0 would climb past. No such task has been observed. All eight
benchmark tasks built so far land at the floor itself.

**It assumes failure at the floor is detected.** This is the real case for
the table and the arithmetic cannot see it. A cheap answer that is wrong and
looks right is not caught by an acceptance check, and on consequential work
it is expensive to discover later. That is exactly P05, the risk-appetite
premise the benchmark structurally cannot measure (P33).

A cheaper router changes the picture completely, because `R` is the only term
the project controls:

| Router cost per verdict | Floor-failure rate needed for the table to pay |
| :--- | :--- |
| USD 0.1645, opus today | impossible, over 100 percent |
| USD 0.08 | 48.8 percent |
| USD 0.04 | 24.4 percent |
| USD 0.02 | 12.2 percent |
| USD 0.01 | 6.1 percent |

This reframes Stages 5 and 6. A two-stage classifier that assesses axes
without the table in its prompt was proposed as a fix for the attractor
defect (P08). The arithmetic says it is more than that: **a cheap classifier
is the only route by which rung 2 can be true at all.** At USD 0.02 a
verdict, roughly one task in eight needs to fail at the floor for routing to
pay for itself. At opus prices, no rate suffices.

## B0 for the project

Stated so that it can be run, not just described:

> Send every task to `worker-sonnet-low` with the same handover contract the
> table's cells receive. If the returned work fails its stated acceptance
> criteria, re-spawn one cell up, including what the previous attempt
> produced and why it fell short. Ask the user only under the clarify rule.
> Never consult a routing table.

B0 is not hypothetical and it is not a strawman. It is a subset of the
shipped product: `ROUTING.md` sections 1.1, 3 and 4 unchanged, section 2
deleted. Every mechanism it needs already exists and is already paid for.

What would show the table beats B0, in order of what each costs to obtain:

1. A measured floor-failure rate `p` above `R/F`. Stage 7 establishes whether
   any task fails at the floor at all; a rate needs a task sample that
   resembles real work, which P19 and P34 both flag as unverified.
2. A router cheap enough that the rate in hand clears `R/F`. Stages 5 and 6.
3. A measured cost for an undetected-wrong answer on consequential work.
   Nothing in the repository measures this, and the benchmark cannot. Without
   it, P05 stays a policy, and the table's remaining case is a risk-appetite
   case rather than a cost case.

The verdict: the routing problem does not dissolve, but it **shrinks from a
cost problem to an insurance problem**, and it shrinks to a much smaller
thing than a fifteen-cell table implies. On the evidence available, the
honest product claim is not "routing gets the same quality for less money".
It is "routing buys a lower chance of an undetected-wrong answer on
consequential work, at a measured premium of about one floor run per task".
That is a coherent product. It has a different acceptance test from the one
this project has been running, and that test is not yet built.

## Metric interrogation

`SYSTEM.md` requires the metric to be interrogated before anything is
generated against it, so that the work is not optimised against a proxy.

**What the current metric measures.** `score_routing.py` reports agreement:
did the orchestrator pick the cell the fixture names. The fixture's cell is a
human label (P16, P17), so the metric measures agreement with one person's
judgement, recorded once in 2026-09-05 and 2026-09-07 reviews. It has three
properties worth separating.

It is reproducible, and now at reporting grade: 155 of 162, 2026-09-11. That
is a real property and the instrument is sound for what it does.

It is silent on whether the label is right. Above the floor, `expected_cell`
has never been checked against a measured frontier, which `BENCHMARK-DESIGN.md`
states plainly about its own inputs.

It has no term for the router's own cost. This is the sharp one. **A router
could score 100 percent agreement and still make the system strictly more
expensive than not routing at all**, because agreement measures where the
task was sent, never what the sending cost. The dissolution check above shows
this is not hypothetical: at the measured figures, the perfectly-agreeing
router loses to B0 on every task that belongs at the floor, which is every
task measured so far.

**The metric the project should optimise.** Cost per task solved at the
reporting bar:

> total spend across all attempts, including every routing verdict and every
> escalation, divided by the number of tasks whose grader passes at the
> reporting bar, compared against the same figure for B0 on the same tasks.

**How far the instruments are from measuring it.** Four terms, two of them
measured:

| Term | Status |
| :--- | :--- |
| Router cost per verdict | Measured. USD 0.1645, 108 opus verdicts, 2026-09-11 |
| Worker cost per run, per cell | Measured at the floor, 96 runs. Unmeasured above it: the only data point above the floor is a single `worker-fable-xhigh` dogfooding run at 103k tokens with no cost recorded |
| Escalation rate, and the cost of the attempts it discards | Not instrumented. `ROUTING.md` section 4 requires the orchestrator to record every escalation; nothing collects the record, and neither harness counts one |
| Tasks solved at the reporting bar | Measured for T1 to T8, all at the floor. No task requiring a cell above the floor has been built |

Both missing terms are about what happens above the floor, which is the same
gap the ledger finds everywhere else.

**The problem underneath the metric.** Even fully instrumented, cost per
solved task measured on this benchmark would not settle the question, and the
reason cuts against the dissolution check above rather than for it.

In the benchmark, every failure at the floor is caught, because a
deterministic grader runs on every attempt. B0 therefore gets a free and
perfect failure detector, and escalation is triggered exactly when it should
be. In real use no such detector exists; failure is caught by whoever reads
the output against acceptance criteria, and some fraction of wrong-but-
plausible answers is not caught at all. So a benchmark measurement of cost
per solved task is biased in B0's favour by an unknown amount, and the size
of that bias is precisely the value of the routing table.

This is the same quantity as P05, reached from the other direction, and it is
the honest reason the table cannot simply be deleted on the arithmetic above.
Measuring it needs an instrument nobody here has designed: a task set where
the floor produces answers that pass a grader and are still wrong, or a
detection-rate measurement on real work. The first is close to a
contradiction in terms. The second is E13 repeated at scale, with someone
reading every output.

**What would close the gap, cheapest first.** An escalation counter, which is
a harness feature nobody has built and which the metric cannot do without. A
cost per run for cells above the floor, which Stage 7 produces as a
by-product of climbing the ladder. A detection-rate measurement, which needs
a design that does not exist.

## The load-bearing unverified premises

`SYSTEM.md` requires that any answer name which premises are both unverified
and load-bearing, on the grounds that quick mode's characteristic failure is
not a worse answer but a confident one resting on an unmeasured premise. For
this project, ranked by what their falsity would cost:

1. **P07**, that routing to the cheapest sufficient cell costs less overall.
   The thesis. Contradicted for the measured territory; no territory where it
   holds has been measured.
2. **P05**, that blast radius warrants a higher cell. The expensive half of
   the table rests on it, and P33 says this method can never verify it. It is
   a risk-appetite policy shipped in the voice of a capability fact.
3. **P17**, that each fixture's `expected_cell` above the floor is the
   cheapest sufficient destination. Seventeen judgements; eight destinations
   measured, all at the floor.
4. **P02**, that sensitivity predicts which model class a task needs. The
   entire model axis rests on it, and eight of eight tasks including open
   ones cleared at the cheapest model.
5. **P29**, that `compact_boundary` reliably signals an undersized cell.
   Nobody has checked it, and Stage 5's two-axis variant proposes replacing
   an entire assessment axis with it. Reclassified 2026-09-15 (D68): the
   entry measures horizon after the fact, not capability, and no benchmark
   run could have produced one; `docs/PLAN-3.md` builds the instrument that
   records it in a consumer project. E30 ran 2026-09-15 (D71): the entry
   is real, its shape is confirmed, and one task survived a mid-task
   compaction with its handover constraint honoured; whether it reliably
   signals horizon across more than one task shape is still open.
6. **P15**, that handover quality is fixed so the cell is the only lever.
   Never stated aloud before this ledger, never tested, and at rung 3 it
   competes directly with routing for the same budget.
7. **P19** and **P34**, that eighteen fixtures and eight synthetic tasks
   represent the work this will actually meet. Everything generalises through
   these two, and the only contrary evidence is E13, where Jeb disagreed with
   the routing on both real tasks tried.
8. **P11**, the three cell-quality claims in `ROUTING.md`'s constraints
   paragraph. Shipped to every consumer as fact, measured never.

Numbers one to four are what Stage 7 exists to attack. Number five is a
single cheap run that should happen before Stage 5 commits to a design.
Number six is a single cheap run that nobody has scheduled.
