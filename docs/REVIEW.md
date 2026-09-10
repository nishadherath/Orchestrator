# Review, 2026-09-10

Two analyses written by Claude (Fable 5.1) in the Cowork session that closed
the F05, F08, F09 and F11 diagnostics (D26 to D34), at Jeb's request, before
the project moved to Claude Code on branch `the-system`. They are the evidence
`docs/PLAN.md` cites. Nothing here is a decision; decisions are in
`docs/DECISIONS.md`.

Scope of what was read for Part 1: the charter, all of `src/`, the generator
and dist builder, the three harnesses (`check.py` and `benchmark.py` by
structure and key sections, `score_routing.py` fully), FINDINGS,
BENCHMARK-DESIGN, COST, all thirty-four ledger entries, the attractor
diagnosis, both six-task benchmark outcomes, every fixture, and the
engineering persona by headings. Part 2 adds `src/System/SYSTEM.md` in full.

---

## Part 1. The orchestrator as it stands

### What it is

A cost-routing layer for Claude Code subagents, and, more importantly, the
measurement apparatus needed to justify one. The deliverable is small: a
rubric (`ROUTING.md`), a lifecycle protocol, fifteen generated worker
definitions across sonnet, opus and fable at five effort levels, a `/workers`
command, and a preflight script. There is no runtime. An orchestrator reads
the rubric, classifies each task on sensitivity, horizon and blast radius,
and routes to the cheapest cell the table says clears the bar.

But the prose is maybe a fifth of the repository by weight and much less by
effort. The rest is the machinery for finding out whether the prose is right:
a static harness asserting seven invariants that would otherwise fail
silently, a fixture suite testing whether an orchestrator reads the table the
way a human would, a benchmark testing which cell can actually do a task, a
findings file separating verified platform behaviour from assumed, and an
append-only ledger where every decision carries the condition that would
reverse it. The project's real thesis is not "route to the cheapest cell". It
is "routing claims are unfalsifiable without this apparatus, so build the
apparatus first". That thesis has been borne out repeatedly.

### The three instruments and why the split matters

The design separates two questions that are easy to conflate.
`score_routing.py` asks: given the table, does the orchestrator classify
tasks the way the fixture author did? `benchmark.py` asks: independent of any
table, what is the cheapest cell that passes a deterministic grader on this
task? The first measures the classifier; the second measures the workers.
BENCHMARK-DESIGN states the dependency between them correctly: fixture
`expected_cell` values are Jeb's judgement until the benchmark supplies a
measured frontier, at which point ROW-BACKED stops meaning "someone believes
this row" and starts meaning "this row is grounded in evidence". That loop
has now closed for the floor of the ladder and nowhere else, which is the
crux of everything below.

### What the project has actually learned

**The attractor.** This is the central empirical result and it is a real
finding, not folklore. Adding a table row changed how tasks that never route
to it were classified: F03 bent its horizon and F07 bent its sensitivity to
reach the new row, a control fixture stayed put, and removing the row
recovered both at 3 of 3 with every pre-registered prediction landing. It was
then re-confirmed the expensive way in D22 through D27, when a narrower row
with T2's evidence behind it reproduced the same regression on an unchanged
bundle. The consequence, that a row is not a passive destination and every
table edit needs a before-and-after fixture run, is now load-bearing policy,
and it is the reason the table has gaps the harness explicitly allows.

**Eight for eight at the floor.** Every benchmark task built so far, T1
through T8, has confirmed `worker-sonnet-low` at 9 of 9 once its grader was
correct. Two rows were lowered on this evidence (D19, D21) and F13 was
reassigned six rungs down.

**Grader defects, not worker failures, are the benchmark's dominant failure
mode.** T4's own docstring tripped its grader (D16), T6 hinted at its own
answer (D17), T8 required a filename that correct reports do not restate
(D30). Every apparent capability failure in the benchmark's history has
resolved, on inspection, into a fixture or grader defect. The project's
discipline caught each one, but the pattern deserves naming: the project has
more experience finding defects in its own instruments than in the workers
those instruments measure.

**Opus is the better orchestrator** (88 percent against 63 percent,
non-overlapping intervals) at five times the cost per correct verdict, and
only after the clarify rule removed opus's habit of asking instead of
routing.

**Fixture calibration drifts.** F08, F11 and F05 all needed correction in
the week to 2026-09-08, and the corrections were mostly about horizon.

### Where the tensions are

**The benchmark is quietly dismantling the table's reason to exist, and the
project has not yet said so in one place.** Eight of eight tasks at the
cheapest rung means every row above `worker-sonnet-low` is backed only by
judgement fixtures, which is exactly the standing the benchmark was built to
replace. The pre-registration itself flagged the two readings: either these
synthetic tasks are easier than the work they stand in for, or the ladder's
middle is over-provisioning. The evidence cannot currently distinguish them,
and nothing on the roadmap does. Nobody has yet built a task that
`worker-sonnet-low` fails. Until one exists, the upper rungs are hypotheses
and the routing layer's measured value is the difference between sonnet-low
and the rows the orchestrator was reaching for before, which is real but is
not the system that was designed. This is the most important open question
and it is absent from CLAUDE.md's list.

**Blast radius carries the table and cannot be measured.** BENCHMARK-DESIGN
says plainly that blast is unmeasurable by exit code. But look at where the
current table's cost lives: blast is what separates `worker-sonnet-low` from
`worker-opus-xhigh` on open work. The expensive half of the table rests
entirely on the one axis the project's best instrument is structurally blind
to. That is not a flaw in the design document, which admits it; it is a flaw
in the project's evidential position that the document's admission does not
resolve.

**Horizon is the unreliable axis, and the table has been quietly adapting to
that.** F03, F05, F08, F11 and F18 all wobbled on horizon. The definitions
ask the orchestrator to predict tool-call counts before any tool is called,
which is a guess by construction. Meanwhile the table has evolved so that
horizon barely matters: open plus consequential is "any horizon",
`worker-sonnet-low` takes short of everything and long-contained of open, and
F11 is now scored correct through a row that ignores horizon entirely (D32
records this plainly). CLAUDE.md's open question about whether three axes
beat two guessed that blast and sensitivity might be redundant. The evidence
points at horizon instead. A worker-side signal already exists for it:
`compact_boundary` in the transcript, named in the charter as evidence a
cell was undersized. Horizon may belong to escalation, not to assessment.

**The project's own standards prescribe the fix to its own central defect,
and it has not been tried.** The attractor diagnosis ends by asking whether
assessment should be a schema-forced classifier that never sees the cell
list, with the table applied afterwards in code. The ai-prompting persona
says the same thing as a general rule: schema-forced output, never free text
parsed afterwards. A two-stage design, classify with no table visible then
route deterministically, makes the attractor class impossible rather than
merely detected, turns `score_routing.py` into a pure axis-classification
test, and removes the USD 9 fixture run that every table edit currently
costs. The obstacle is that the Agent tool call is made by the model, so
routing in code needs a hook or a small tool the orchestrator calls, and
whether that is achievable is a FINDINGS question nobody has asked yet.
`preflight.py` and `/workers` already ship Python, so "no runtime" is a
convention, not a constraint.

**The routing side has no reporting bar.** The benchmark refuses to claim
anything below nine runs and a 0.7 Wilson lower bound. The routing side has
made real table decisions (D23, D24, D27) on three runs with intervals of
[44 percent, 100 percent], and D27 is the written record of what it cost to
call two runs clean. The asymmetry is unjustified. Either the routing side
needs its own reporting threshold or its decisions should be labelled as
steering-grade in the ledger.

**Classification may cost more than the work it routes.** An opus verdict
costs about USD 0.20. A `worker-sonnet-low` run on the tasks measured so far
costs USD 0.07 to 0.25. For most of the benchmark, the routing decision is
as expensive as the task. The opus-versus-sonnet pre-registration said the
answer "depends on what one wrong routing decision costs", and that number
still does not exist. For a system whose stated purpose is cost, the cost of
the router itself is not on the ledger.

**Smaller and concrete.** `test/fixtures/README.md` says seventeen fixtures
and that F17 exposes a gap; both are stale (D9 closed the gap, there are
eighteen). `test/fixtures/benchmark/README.md` says only T1 and T5 exist.
`COST.md` was measured on bundle `04d2acc` and `ROUTING.md` has changed
materially since. `benchmark.py`'s docstring says six tasks and it still has
the filename collision D34 fixed in its sibling; the original six-task result
file was in fact overwritten by the T7 run and survives only in git history.
The fifteen `model-specific-*` persona sections are all empty, so every
worker has an identical persona and the charter's open question about
whether a worker should know its cell has never been tested, though the
benchmark now makes that test cheap. Six of fifteen cells are unrouted and
their descriptions are paid on every orchestrator turn.

### What to do next, in order

Build one task that `worker-sonnet-low` demonstrably fails. Everything above
the floor is unmeasured until that exists, and it is the single experiment
most likely to change the table. Then try the two-stage classifier against
the existing fixture set, because it removes an entire class of defect rather
than a single instance. Then give the routing side a reporting threshold, or
label its decisions honestly. The documentation fixes and the benchmark.py
collision are an afternoon and should just be done.

The apparatus is the achievement here. It has caught an arithmetic error
that would have voided every confirmation, two grader defects that read as
capability results, a premature "clean" call, and a feedback loop between
menu and classifier that no static check could see. What it has not yet done
is find the ceiling of its cheapest worker, and until it does, the routing
table is a well-instrumented hypothesis.

---

## Part 2. `SYSTEM.md` and its integration with the orchestrator

One framing note first. `SYSTEM.md` is the second half of an exchange. It
opens with "three commitments before the numbered answers" and refers to
"the eight-step sequence from the previous answer" and "the forty techniques
from the previous answer", neither of which is in the repository. It cites
Jeb's Wu Xing engine's v14 truncation bug and his Censor's pre-v11
strictness as the failures it is designing against, and it addresses "your
sonnet/opus/fable cell scheme" directly. So it is a design answer written
with this orchestrator already in view, not an independent framework being
bolted on afterwards.

### What the document describes

Strip the role table away and the methodology underneath is this: **most
hard problems are hard because of a premise that is being treated as a law
when it is actually a habit or a policy.** The eight-step sequence exists to
find that premise. The Framer builds a ledger in which every premise is
classified (law, maths, policy, habit, unverified), builds a goal ladder so
the stated goal can be replaced by the goal behind it, interrogates the
metric so the problem is not solved against a proxy, checks whether the
problem dissolves once a premise is reclassified, fixes acceptance criteria
before anyone generates anything, and produces B0, the deductive baseline
that any candidate has to beat. The Verifier then measures the unverified
premises with tools, and only tools; it is "the only role that touches
reality". Only once the ledger is frozen do generators run, each applying
one family of premise operations (remove, re-represent, add, replace goal,
search), in isolation from each other. A blind Critic ranks failure modes
and, crucially, flags derivability: could this candidate have been deduced
from the ledger? That flag is what separates novel from exotic. The Selector
scores against acceptance and B0. The Verifier instantiates the shortlist
with the cheapest falsification test first. A failed candidate is not
edited; it becomes a verified negative premise and the loop continues.
Convergence is guaranteed because the ledger monotonically gains verified
premises, so the untested candidate space strictly shrinks on every pass.

The lineage is recognisable and sound. The premise classification is
Ackoff's dissolve-rather-than-solve and the TRIZ contradiction move made
operational. The goal ladder is means-ends analysis. B0 and the derivability
flag are a null-hypothesis discipline applied to creativity. The
architecture is a blackboard (Hearsay-II onwards), chosen explicitly because
it solves interference by construction: single writer per record type,
append-only, versioned, agents as stateless functions over typed records
that never talk to each other. The isolation argument cites Diehl and
Stroebe, the finding that nominal groups out-produce interacting groups, and
applies it to model ensembles: generators that read each other converge on
the first plausible idea. The Controller is code, not a model, with exactly
two classification calls, both routed to the cheapest cell.

The three opening commitments are the load-bearing part, and they are more
disciplined than most multi-agent designs. A role earns separation only for
isolation, an adversarial objective, or a different cost tier; otherwise it
is a section of one prompt. The fleet earns its cost in exactly three
places: parallel independent generation, blind critique, and tool-backed
verification. And the document sets its own falsification bar: one strong
model running the eight steps as a single prompt gets roughly 70 percent of
the value, so build that first, and if the fleet does not beat it by a
margin that pays for itself, "you have a prompt, not a system". That last
sentence is the same discipline as the benchmark's "cheapest cell that
clears the bar", arrived at from the other direction.

What is a prior rather than a measurement, and the document mostly says so:
the importance ratings, the 70 percent, the roughly 40 percent critic return
rate, the fifty runs before Librarian statistics take over, the
forty-premise ledger cap, and the whole of section 5's role-to-cell table.
That table is the part this orchestrator's history has the most to say
about.

### The premise ledger, turned on the routing table

The single most useful thing the document does for this project is give a
vocabulary for what the week to 2026-09-08 found. Run the Framer over
`ROUTING.md`'s own premises:

| Premise the table rests on | Class, on current evidence |
| :--- | :--- |
| Sensitivity determines which model class is needed | Unverified. Eight of eight benchmark tasks, including open ones, cleared at sonnet-low |
| Horizon can be assessed before the task is attempted | Habit, inherited from human project practice. The model is asked to predict tool-call counts before making any; F03, F05, F08, F11 and F18 all wobbled on it, and a worker-side signal (`compact_boundary`) already exists |
| Blast radius warrants a higher cell | Policy. It encodes a risk appetite, not a capability fact, and BENCHMARK-DESIGN concedes no grader can measure it |
| A row is a passive destination | Was a habit; falsified by the attractor experiment |
| Fifteen cells are needed | Policy. CLAUDE.md fixes the count; six are unrouted and their descriptions are paid every turn |

The table's expensive half rests on a policy premise and a habit premise.
That is not a criticism the document invents; it is the state D32 and
BENCHMARK-DESIGN already record, named more sharply. It is also the cheapest
exercise in this whole review and should be run on the fixture set as well
(`PLAN.md` Stage 3).

### Where the two fit

**The cultural match is complete, because this methodology has been running
on the orchestrator already.** DECISIONS.md is a premise ledger with
reversal clauses. FINDINGS.md classifies every platform claim as verified,
unverified or contradicted, which is the ledger's class field applied to the
substrate. Pre-registration is acceptance criteria fixed before generation.
"Diagnostic before patch" is Frame and Verify before Generate. The attractor
diagnosis is a textbook run: two hypotheses, a discriminating experiment
with predictions written first, a premise ("coverage is good in itself")
reclassified from habit to falsified, and a consequence written into policy.
The document is a description of how this repository has actually been
worked on.

**Its Controller is the two-stage classifier the attractor finding asks
for.** Section 3 says the Controller is code apart from two classification
calls, and both go to the cheapest cell. Classification that never sees the
menu of destinations, with routing done deterministically afterwards, makes
the attractor class of defect impossible rather than merely detectable. This
is the highest-leverage architectural change Part 1 identified, and the
document already embodies it.

**Its verification rules are the ones the benchmark learned by being
burned.** "No measurement record without an artefact" is the guard against
D20's forwarder hallucination, where a clean-context forwarder confabulated
an entire prior exchange. "Critic class is never below generator class" is
the escalation rule in `ROUTING.md` section 4. "Return rate tracked and
recalibrated if it exceeds roughly 40 percent" is "three escalations from
one cell means the rubric is wrong", with a number attached. "Acceptance
criteria are fixed before generation, always" is the pre-registration
discipline, and the reason given ("deciding what done means after seeing
candidates is how exotic-but-worse solutions get accepted") is exactly what
R_confirm's separate steering and reporting thresholds protect against.

**It answers for the part of the table the benchmark cannot.** The rows
without measured backing are open/medium/contained (opus-high),
open/long/consequential (opus-xhigh and fable-xhigh) and the frontier row.
Look at their fixtures. F10 asks for three candidate designs with
trade-offs: that is Generate, Critique, Select. F11 and F18 are root-cause
investigations with no reproduction: that is a Frame and Verify loop. F14
hands over failed attempts from two cells and asks for the actual race: that
is deep mode with the failures already entered as verified negative
premises. The tasks the routing table can only reach by judgement are the
tasks the document's methodology is built for.

**The benchmark harness is the evaluation layer the document lacks.** The
document says build the single-model baseline first and measure whether the
fleet beats it. Nothing in the document says how. `benchmark.py` is that
instrument: deterministic grading, a staircase protocol, Wilson bars,
checkpointing, and a forwarder that spawns a named cell. It is,
structurally, already a thin Controller that invokes cells via `claude -p`
and grades with code.

### Where they conflict

**The role-to-cell table in section 5 is exactly the kind of judgement this
project has spent a week dismantling.** "Framer: opus/high in quick mode,
fable/xhigh in deep, highest value per token in the system" is a prior.
F13's row was a prior of the same shape, reviewed and confirmed, and it sat
six rungs above where the evidence landed, twice. Every assignment in that
table is a routing row that must earn its place, and the benchmark's history
says such priors have been wrong in one direction only. The document
half-knows this ("measure it on your evals before trusting the prior") but
applies the caveat only to `max`.

**Interaction models are incompatible.** `LIFECYCLE.md` is built around
`SendMessage` in both directions, named workers, `TaskStop`, and
resume-with-full-history. The document's rule is "agents never talk; they
read and write records", and its memory model discards role-private state
at phase end because "persisting these contaminates independence in later
phases and in future runs". Resume-with-history is a feature for a single
delegated worker and a contamination hazard for a generator. Hub-and-spoke
worker-to-orchestrator messaging is tolerable under the document's rules;
peer messaging and resumed generators are not.

**There would be two Controllers, and the document names that as a failure
mode.** The orchestrator persona is a budget owner and terminator by prose
instruction. The document's Controller is a budget owner and terminator by
code. "No budget owner" is one of its three reasons peer-to-peer fails; two
budget owners is not better. One of them has to be demoted.

**The substrate has no blackboard.** Claude Code gives you a Task tool
return value and a queued `SendMessage`. Typed records, single writer per
type, schema rejection before any model sees a record: all of that has to
be files on disk with a code Scribe in front of them. The benchmark's
checkpoint JSONL is the precedent, so it is feasible, but it is not free,
and the cache layout in section 5 (static block, ledger block, role brief)
assumes an identical prefix across N parallel generators, which `claude -p`
per role can arrange and the Task tool cannot guarantee. That is a
FINDINGS-grade question with a real cost attached.

**The attractor generalises to the technique library.** The Controller's
second classification call, "which technique families for this problem
type", is a classification against a menu of forty. The orchestrator's
central finding is that a menu biases the classifier toward its entries.
The document's mitigation, replace the call with Librarian statistics after
about fifty runs, is correct but means fifty runs of a 50-to-200-call system
before the classifier is data-driven. Until then every edit to a technique
brief needs a before-and-after fixture run, which nobody has budgeted.

**The grader boundary.** Deterministic exit codes cover plantable-defect
tasks. The document's domain includes design, research and business
problems whose acceptance is not an exit code, and for those its own
Selector and Critic are models judging models, which BENCHMARK-DESIGN
rejects as circular when capability is the thing under test. The document's
mitigations (B0 comparison, derivability flag, Verifier instantiation) are
real, and "artefact or it did not happen" is a rule both sides share. But
the honest position is that the orchestrator's evidence machinery covers
only the slice of the document's territory where acceptance is
deterministic, and that slice is where sonnet-low has so far done
everything.

**Complexity, by the document's own rule.** "Most multi-agent designs
over-split and pay twice" is its own opening line. Eight roles, forty
technique briefs, six record schemas, three memory tiers, a state machine
and a library is a large prompt surface, and `ai-prompting.sonnet.md` in
this repository says every prompt is a hypothesis that expires on a model
bump. The orchestrator, at fifteen prose files and three harnesses, needed
thirty-four ledger entries in four days to stay honest.

### The integration proposed

Not at the persona level. At the substrate level, with the document's
Controller as a Python program in `benchmark.py`'s lineage that spawns the
orchestrator's cells via `claude -p` with role briefs and a file-based
ledger. The orchestrator repository contributes the fifteen cells,
`preflight.py`, the invariants, the harness discipline, and the benchmark as
the fleet-versus-baseline instrument. The orchestrator persona is not in
that loop at all; its job is to route ordinary tasks to single workers, and
for its top three rows the destination becomes "a quick-mode run" rather
than "one big model".

The first experiment is the one both documents independently prescribe.
Build B0: one worker cell running the eight steps as a single prompt against
F14-shaped tasks, graded deterministically. Then run quick mode against the
same tasks. The margin, or its absence, is the answer to whether there is a
system here or a prompt. This also produces, as a by-product, the missing
benchmark artefact from Part 1: a task that sonnet-low can be shown to fail,
because a Frame-and-Verify problem with planted false premises has a
deterministic grader (which premises were reclassified, with what artefact)
and a difficulty that scales with the number and subtlety of the false
premises rather than with file count.

If that margin exists, the routing table's expensive rows finally get
measured backing, and the document's section 5 gets replaced by numbers. If
it does not, the orchestrator's cheap rows plus a single-prompt eight-step
brief is the whole product, and that is worth knowing for the cost of a few
days rather than the cost of building the fleet first.
