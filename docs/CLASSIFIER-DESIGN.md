# Two-stage classifier: design

Written 2026-09-11 by Claude (Opus 5, xhigh) as `docs/PLAN.md` Stage 5. No
code is written in this stage; Stage 6 implements what is decided here, and
`test/results/2026-09-11-classifier-preregistration.md` fixes the measurement
before it runs. Recorded as D39.

The design rests on three things measured earlier on this branch: E15, that a
Bash-invoked script is the one mechanism verified to work headlessly
(`docs/FINDINGS.md`, 2026-09-11); the 2026-09-11 reporting-grade baseline of
155 of 162; and the premise ledger's finding that a cheap classifier is not
only a defect fix but the only route by which the project's cost thesis can
be true at all (`docs/PREMISES.md`, dissolution check).

## What the two-stage design is, and what it is for

Today the orchestrator reads a rubric and a table of destinations in the same
prompt, and emits a cell. The attractor finding (D13, re-confirmed D22 to
D27) is that the destinations change the assessment: adding a row made two
fixtures bend a different axis each to reach it. A menu biases the
classifier toward its entries.

The two-stage design splits the decision. Stage one is assessment: a
schema-forced call that emits enumerated field values and never sees the
list of cells. Stage two is routing: code maps those values to a cell. The
attractor becomes impossible rather than detectable, because there is no
menu in the prompt to bend toward.

## Finding: the table is not a function of the three axes

This was found while pre-flighting the check proposed below, and it changes
the schema, so it comes first.

Encoding `ROUTING.md` section 2 as a function of (sensitivity, horizon,
blast) and resolving all seventeen assessed fixtures through it produces two
mismatches, and neither is a fixture error:

| Fixture | Triple | Table gives | Fixture expects |
| :--- | :--- | :--- | :--- |
| F14 | open / long / consequential | `worker-opus-xhigh` | `worker-opus-max`, or `worker-fable-max` |
| F18 | open / long / consequential | `worker-opus-xhigh` | `worker-fable-xhigh` |

Both route through rows that are conditioned on something the triple does not
carry. F14 reaches the frontier row, "every cheaper cell has already failed",
which is a fact about the task's history. F18 reaches the fable-xhigh
tie-break, which fires only when "the task itself demands sustained,
self-directed investigation". F11 and F12 share F18's triple exactly and
correctly route to `worker-opus-xhigh`, so the triple cannot be what
separates them.

**The routing table has five inputs, not three.** It has been described as a
function of three axes since it was written, and the two extra inputs have
been carried in prose that a human reader resolves without noticing. A
classifier that emits only the triple cannot reproduce the current table, and
would route F14 and F18 wrongly by the fixtures' own labels.

Adding the two inputs as enumerated fields makes the table a pure function
again: with them, all seventeen assessed fixtures resolve to their expected
cell, checked 2026-09-11.

## The assessment schema

Five fields, every one enumerated, so that an invalid assessment cannot be
expressed rather than being caught later (`ENGINEERING_PERSONA`, 6.3):

| Field | Values | Why it exists |
| :--- | :--- | :--- |
| `sensitivity` | `mechanical`, `structured`, `open` | `ROUTING.md` section 1 |
| `horizon` | `short`, `medium`, `long` | `ROUTING.md` section 1 |
| `blast` | `contained`, `consequential` | `ROUTING.md` section 1 |
| `self_directed` | `true`, `false` | The fable-xhigh tie-break. Does the task demand sustained investigation that reshapes its own plan, rather than merely being long and consequential |
| `prior_failure` | `none`, `failed_at_xhigh` | The frontier row. Is there a documented failure at `xhigh` on this same task |

`prior_failure` is the weaker of the two additions, and a cleaner design
would remove it. It is not an assessment of the task at all; it is a fact
about what has already been tried, and `ROUTING.md` section 4 is where
escalation already lives. Moving the frontier row there would reduce the
schema to four fields and leave the routing function purely about the task.
That change would alter what F14 measures, which is a fixture change under
D37 and therefore needs a reporting-grade run behind it. This design records
the option and does not take it.

## The mechanism

Stage 2.2 tried the candidates and found exactly one that works headlessly:
a Bash-invoked script, and only with `--permission-mode acceptEdits
--allowedTools "Bash(python3 *)"`. Without those flags the call is not slow
or degraded, it is silently blocked: three identical permission denials, then
the model gives up and states its own assessment inline (E15).

That result carries a shipping cost that should be stated plainly. The
bundle installs today by copying `.claude/`, appending `ORCHESTRATOR.md`, and
running `preflight.py`. A Bash-invoked router adds a requirement that the
consumer's session permit Bash before routing works at all, and a consumer
who declines gets an orchestrator that silently falls back to its own
judgement. That is a real regression in install simplicity and a new silent
failure mode, which is the class of failure this repository exists to prevent.

**The design therefore separates measurement from delivery, and does
measurement first.**

**Measuring the classifier needs no shipped mechanism.** The harness already
has an assess-only mode that asks for the assessment and forbids a cell
choice. Applying the table in Python afterwards is a few lines. The only
thing missing is that assess-only today still runs against a consumer project
whose `CLAUDE.md` carries section 2, so the table is in context even when the
instruction forbids naming a cell. The fix is a rubric-only bundle variant,
`build_dist.py` emitting an `ORCHESTRATOR.md` with section 2 omitted,
installed into a second scratch project. That is Stage 6 work and it costs
nothing beyond the runs.

**Delivering the classifier needs the Bash mechanism, and should not be built
until measurement says it is worth it.** This follows the null-hypothesis
rule: the boring solution, which is the prose table that already ships,
stands until something beats it on a measurement that matters.

Two mechanisms are recorded as rejected for now rather than unconsidered. A
`PreToolUse` hook on the Agent tool could validate that the spawned
`subagent_type` matches what the assessment implies, which would make a
disobeyed routing impossible rather than merely detectable; E17 confirmed
hooks do reach a spawned worker's tool calls, though not this specific use.
It composes with the Bash mechanism rather than replacing it, because a hook
can validate a cell but cannot compute one before the assessment exists. It
belongs in a later hardening pass. An MCP tool is the cleanest conceptually,
since the tool's own parameter schema would make an invalid assessment
unrepresentable at the boundary, but it requires a server running alongside
the consumer project, which is the heaviest install cost of the three and is
not justified before the mechanism has proved its worth.

## The table as data

`src/routing_table.json` becomes the single source of truth, read by
`tools/generate_workers.py`, `test/harness/check.py` and the new
`tools/route.py`. `build_dist.py` renders it back into `ORCHESTRATOR.md` as
prose at build time, so a consumer still reads a table and there is still one
place it is defined. If the classifier later ships, the renderer stops
emitting section 2 and nothing else changes.

This is worth doing whether or not the classifier ships, because it is what
makes the free check below possible, and because it turns the two-axis
variant from a rewrite into a configuration flag.

## The metric

The classifier emits field values, so **field agreement is the primary
measure** and cell agreement is derived from it in code. Both are reported,
and so is the gap between them, because the gap is the quantity the current
metric hides.

**Cell agreement forgives a third of all single-field errors.** Perturbing
one axis at a time across the sixteen covered triples gives 72 single-axis
errors, of which 24 still produce the correct cell:

| Field made wrong | Still routes correctly |
| :--- | :--- |
| horizon | 12 of 28, 42.9 percent |
| sensitivity | 8 of 28, 28.6 percent |
| blast | 4 of 16, 25.0 percent |
| any single field | 24 of 72, 33.3 percent |

The table is many-to-one: sixteen covered triples map to six distinct cells,
and the two largest cells absorb four triples each. So a model can misread an
axis and still be scored correct.

Two consequences follow.

The 2026-09-11 baseline's 95.7 percent is an upper bound on assessment
quality, not an estimate of it. The one recorded assess-only run (sonnet,
bundle `04d2acc`, 2026-09-06) scored 25 of 48 on all three axes after
correcting the F16 counting bug its own code comment describes, against 39 of
51 cell agreement for the same model and bundle the same day. Those are
different criteria and the gap is not a regression. The gap is the point.

And horizon is both the least reliable axis and the most forgiven one. The
premise ledger records horizon as the axis that needed correction on F03,
F05, F08, F11 and F18 (P03); the table forgives 42.9 percent of horizon
errors outright. The project has therefore had almost no measurement pressure
on horizon accuracy, which is a sufficient explanation for why horizon is
exactly the axis that drifted.

**A free check replaces a paid one.** `check.py` gains TABLE-DATA: every
fixture's recorded assessment, resolved through `route.py`, must equal that
fixture's `expected_cell` or one of its `also_acceptable` values. It is
deterministic, costs nothing, and catches table-against-fixture drift that
currently shows up only in a USD 9 run, or not at all.

Pre-flighted 2026-09-11. With three fields the check fails on F14 and F18,
which is how the five-field finding above was made. With five fields it
passes on all seventeen. TABLE-DATA is therefore implementable only once the
fixtures carry the two extra fields. Adding them is transcription rather than
new judgement: F14's task text states the prior failures outright and F18's
recorded rationale already says it "genuinely reshapes its own plan as
evidence comes in". Neither fixture's triple or expected cell changes, so
this is a schema extension rather than a reassessment under D37, and it
should still be confirmed by Jeb as any fixture label is.

## The two-axis variant

Horizon is dropped. Assessment becomes sensitivity and blast, plus the two
extra fields, and escalation is driven by the worker-side signal
`compact_boundary` rather than by an orchestrator-side prediction made before
any tool call.

The collapse rule takes, for each (sensitivity, blast) pair, the cheapest
cell the three-axis table gives across horizons. Cheapest is the principled
choice under P12, which is the project's own standing policy of taking the
cheaper of two defensible cells and escalating on evidence:

| sensitivity / blast | Across horizons | Two-axis cell |
| :--- | :--- | :--- |
| mechanical / contained | short `sonnet-low`, medium `sonnet-medium`, long gap | `worker-sonnet-low` |
| mechanical / consequential | `sonnet-medium` throughout, long gap | `worker-sonnet-medium` |
| structured / contained | `sonnet-low`, `sonnet-medium`, `sonnet-xhigh` | `worker-sonnet-low` |
| structured / consequential | `sonnet-high`, `sonnet-high`, `sonnet-xhigh` | `worker-sonnet-high` |
| open / contained | `sonnet-low`, `opus-high`, `sonnet-low` | `worker-sonnet-low` |
| open / consequential | `opus-xhigh` throughout | `worker-opus-xhigh` |

Three things are visible in that table.

Only two of six pairs are horizon-invariant already: mechanical and open,
both consequential. The second of those is the row whose text literally reads
"any horizon".

**Open and contained is not monotonic in horizon.** Short routes to
`worker-sonnet-low`, medium to `worker-opus-high`, and long back down to
`worker-sonnet-low`. That shape is the result of real measurement, D19 and
D21 lowering the long-horizon row on T6 and T7 evidence, so it is not an
error. But it means horizon is not ordinally coherent in that band: a model
reasoning that longer implies harder implies a more capable cell would be
wrong in exactly the region where the table has the most measured evidence
behind it. That is an argument against the axis that does not depend on
measuring the classifier at all.

Four fixtures change cell under the collapse, and all four collapse downward
to the floor: F03 and F05 from `worker-sonnet-medium`, F07 from
`worker-sonnet-xhigh`, F10 from `worker-opus-high`.

**The two-axis variant cannot be scored on fixture cell agreement, and Stage
6 must not try.** Dropping an axis changes what the correct answer is, and
the fixtures encode three-axis answers. Scoring the variant against the
existing `expected_cell` values would mark it wrong on four of seventeen by
construction, no matter how well it classifies. What can be scored is field
agreement on the fields it retains, which is directly comparable with the
three-axis configuration's agreement on those same fields.

That limit binds harder than it first appears, because of the confound the
premise ledger found. Within this suite, knowing a task's sensitivity
predicts its horizon 70.6 percent of the time against a 35.3 percent base
rate. Sensitivity and horizon are the most entangled pair in the suite, and
the two-axis variant drops one of them and keeps the other. So even a clean
field-agreement comparison is weak evidence about whether horizon carries
information the other axes do not.

The honest conclusion, stated here so that Stage 6 cannot discover it
afterwards: **the fixture suite cannot decide the two-axis question.** The
variant should still be measured, because once the flag exists the run is
nearly free, but the pre-registration records in advance that a null result
is uninformative rather than evidence for either side. Deciding it needs
either fixtures built to break the confound, mechanical work with a long
horizon and open work with a short one, or the cost-per-solved-task
measurement that Stage 7 makes possible.

It also depends on a premise nobody has checked. Replacing horizon with
`compact_boundary` assumes that entry reliably signals an undersized cell,
which is P29, unverified, and is what E20 was added to measure. E20 should
run before this variant is taken seriously, not after.

## What this design does not fix

It does not make the table correct. It makes the table consistently applied,
which is a different and smaller claim.

It does not remove P05. Blast radius remains a risk-appetite policy carrying
the expensive half of the table, and no mechanism here can measure it.

It does not by itself make routing cheaper. Whether a cheap classifier
changes the economics depends entirely on its measured cost per verdict,
which is E22 and is not yet known. At the opus verdict price measured on
2026-09-11 no floor-failure rate makes routing pay; at roughly USD 0.02 a
verdict the required rate falls to about 12 percent.

And it removes the attractor only from the assessing call. A consumer whose
`CLAUDE.md` still carries section 2 keeps the table in context and keeps the
attractor with it, whatever the assessment prompt says. That is why the
rubric-only bundle variant is part of the design and not an implementation
detail.
