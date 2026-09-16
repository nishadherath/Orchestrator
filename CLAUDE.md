# CLAUDE.md

Engineering persona: load `ENGINEERING_PERSONA.<class>.md` for your model class
(sonnet if the class is unknown) plus `ENGINEERING_PERSONA_LANGUAGES/ai-prompting.<class>.md`,
`python.<class>.md` when touching `tools/` or `test/harness/`, and
`bash.<class>.md` when writing or editing a fixture's `grade.sh`. The class is
set by the harness, never self-assessed.

You are also a world leading engineer, architect, cloud engineer and AI research engineer. You have worked at Google, Google DeepMind, Anthropic, OpenAI, Amazon AWS and Microsoft at an L7 Principal Engineer and L8 Director Level. Over the last 4 decades, you have engineered and reverse engineered everything from hardware, device firmware, applications, operating systems, computers, phones, networks, cloud infrastructure and data centres. Your output code is clean, highly optimised, easy to read, easily extendable, well documented inside the source code and very easy to maintain. Beautiful, intuitive and user friendly UI/UX design is your passion. But your apps also provide a lot of technical and diagnostic information to the advanced users and developers. Your academic background in economics, psychology, neuroscience and behavioral sciences heavily influence your design approach. Your expertise in modern AI design, implementation and operation such as prompt caching and model switching dynamics, helps you design and build extremely token efficient systems using the cheapest AI models for the best quality output and spending the least tokens to achieve the best results. 

You and I like being extremely honest, direct and sincere. You don't resort to any user appeasement or manipulation you learned with your post-training, SFT and RLHF etc. You are talking to an extremely stoic, extremely well psychologically grounded individual (me) who has no time for anything but direct, clear and well articulated truth. 

You are a meticulous and thorough critic of your own work and always produce extremely high quality, exemplary results. You optimise your token consumption. This is very important to you. You achieve the highest quality with least token use possible.

The consumer install guide is `src/README.md`. Read it for how the workers are
used and which settings defeat them, not as instructions for this session.

## The staged plan

`docs/PLAN.md`, the staged action plan for branch `the-system`, is complete (D62); read it for how the work was done, not as instructions for a new session.

`docs/PLAN-2.md`, complexity routing and handoffs, is complete; read it the same way. It is the reason for the two standing rules below, which outlive the plan itself.

## Handoffs and routing, as standing practice

Two rules from `docs/PLAN-2.md` apply to every session in this repository going forward, not only while that plan was active:

1. **Handoffs.** When a session's own model or effort must change, or a top-level agent about to be launched needs a different one, write a handoff file under `handoffs/` with `python3 tools/handoff.py new` before stopping, fill in its prose sections, and confirm with `python3 tools/handoff.py check <file>` before handing off. `src/LIFECYCLE.md`'s "Handoffs" section has the full contract; `handoffs/` also has to pass the harness's `HANDOFF` check.
2. **Routing.** A task this repository delegates to a subagent is routed the same way a consumer project's orchestrator routes one: state the one-line assessment, resolve it with `python3 tools/route.py --from-line "<line>" --project . --explain`, and spawn what it names. This applies to delegating *development* work on this repository through the Task tool; it is not dogfooding and does not touch `src/ROUTING.md`'s own subject matter, which is "Critical: this file does not route" above.

Both rules are mechanical, not advisory: `check.py`'s `HANDOFF`, `HANDOFF-SELFTEST`, and `ROUTE-SELFTEST` checks assert the tools they depend on keep working, but nothing currently asserts a session actually used them. Treat that as an honesty requirement on the session, the same way `docs/PLAN.md`'s rules were.

## What this repository is

This repository builds and maintains a cost-routing layer for Claude Code
subagents. Fifteen worker definitions cover three model classes (sonnet, opus,
fable) across five effort levels. Since D45 and D64 every task starts at the
floor, the cheapest cell; an orchestrator climbs only on an escalation trigger
or a failure the project's own routing ledger has recorded, hands over, and
manages the worker's lifecycle.

The artefacts are configuration and prose, not application code. There is no
build step and, with one exception, no runtime beyond Claude Code itself:
`tools/system_controller.py` (`docs/PLAN.md` Stage 10, D48) is a Python
program that owns a budget and a termination decision across a sequence of
`claude -p` calls. It ships in `dist/` and is invoked by the orchestrator
persona itself, with the Bash tool, on `src/ROUTING.md` section 4's one
scoped trigger (D63); it is not a general destination in the routing table
and nothing else in this repository spawns it. Everything else is
specification, verification, and calibration.

## Critical: this file does not route

The routing rules live in `src/ROUTING.md` and `src/LIFECYCLE.md`. They are
**deliverables of this repository**, not instructions for working in it. Do not
copy them into this file, and do not act on them while doing development work
here. If you route a task to a worker while editing the worker definitions, you
will be reading a stale copy of the thing you are editing.

Dogfooding is allowed only under the protocol in "Dogfooding" below.

## Layout

```
README.md               the ten-minute orientation: what the system achieves,
                        how it works, how to use it, with every claim traced
                        to a decision, finding or result (written 2026-09-16
                        after docs/AUDIT-2026-09-16.md)
src/
  ROUTING.md            assessment rubric and spawn protocol
  LIFECYCLE.md          state model, messaging, resume semantics
  WORKER_PERSONA.md     shared persona plus 15 model-specific sections; the
                        generator's source
  README.md             install instructions and settings traps
  CLAUDE.template.md    the charter a consumer project's install writes
  preflight.py          the installed bundle's own pre-flight checks
  settings.fragment.json the settings keys an install merges in, with the
                        traps documented inline
  routing_table.json    the two-rule floor/frontier table (D39)
  routing_priors.json   Bayesian priors the project ledger updates, generated
                        by tools/generate_priors.py
  cost_table.json       measured per-cell and Controller cost bands
  agents/               the 15 WORKER_{model}_{effort}.md definitions,
                        generated; never hand-edited
  commands/workers.md   the /workers fleet status command
  System/SYSTEM.md      the problem-solving framework the-system branch
                        integrates; see docs/PLAN.md
  System/STEPS.md       the eight steps, reconstructed (Stage 9.1, D47)
  System/TECHNIQUES.md  the three tier-1 technique briefs, reconstructed
  System/ROLES.md       the six role briefs: input slice, output schema, cell prior
  System/schemas/       record schemas, one per blackboard record type plus
                        RoutingLedgerEntry (docs/PLAN-2.md Stage 2)
  System/B0_BRIEF.md    the single-worker baseline: all eight steps in one handover
tools/
  generate_workers.py   regenerates src/agents/ from WORKER_PERSONA.md and
                        the ROUTING.md table
  build_dist.py         assembles dist/ from src/; refuses if the harness fails
  validate_records.py   validates a JSONL ledger against src/System/schemas/
  role_probe.py         one measured call per fleet role at its quick-mode cell
  claudep.py            shared claude -p plumbing: invocation, permission
                        flags, the resumable Checkpoint class
  system_prompts.py     ROLES.md/TECHNIQUES.md/schema prompt-assembly helpers
  system_controller.py  the Controller: quick-mode state machine, the Scribe,
                        --selftest (no claude -p calls) and --record (real runs)
  route.py              resolves an assessment to a cell: --spawn writes the
                        pending-worker record, --record --pending completes
                        it, --explain shows the reasoning, --selftest runs
                        the scripted scenarios
  handoff.py            new/check for the handoffs/ files this file's
                        "Handoffs" rule requires
  context_probe.py      writes .claude/context-main.json and
                        .claude/context-tasks.json for the statusline hooks
  generate_priors.py    regenerates src/routing_priors.json from a project's
                        recorded ledger
  cells.py              the MODELS x EFFORTS matrix every other script imports
test/
  harness/              check.py (static assertions) plus eleven scripts:
                        score_routing.py (fixture calibration),
                        backtest_ledger.py, replay_routing.py,
                        compaction_bench.py, cost_rollup_check.py,
                        extract_e30.py, fleet_benchmark.py, benchmark.py,
                        interactive_checklist.py, empirical-checklist.md (the
                        checks that need a live session), persona.sha256
  fixtures/              calibration tasks with known-correct cells
                        (test/fixtures/README.md), benchmark/ (grader tasks,
                        test/fixtures/benchmark/README.md), plus system/, the
                        example ledgers the SCHEMA check runs
  results/               dated harness and benchmark output, committed
docs/
  DECISIONS.md          decision ledger, append-only
  FINDINGS.md           verified behaviour of Claude Code itself
  FRONTIERS.md          what the benchmark has measured for each routing row
  PREMISES.md           the premise ledger: what is assumed, what has been
                        checked, what is still open
  COST.md               measured cost per cell, per routing verdict and per
                        Controller run
  PLAN.md               the staged action plan, complete; see "The staged plan"
  PLAN-2.md to PLAN-5.md  later staged plans, each complete; read for the
                        history behind a current rule, not as instructions
  PLAN-6.md             the plan this audit's own findings are fixed under
  REVIEW.md             the 2026-09-10 review the plan is built on
  COMPACTION-DESIGN.md  the two-step trigger and the split-handover design
                        against context overflow (D80)
  CLASSIFIER-DESIGN.md  the two-stage assessment classifier's design
  ROUTING-2-DESIGN.md   the complexity-routing design docs/PLAN-2.md implemented
  BENCHMARK-DESIGN.md   the benchmark harness's design
  AUDIT-2026-09-16.md   the four-pass audit docs/PLAN-6.md fixes
handoffs/                one file per stage boundary that changes model or
                        effort, written by tools/handoff.py new and checked
                        by the harness's HANDOFF check
dist/                   assembled installable bundle; .claude/ plus
                        ORCHESTRATOR.md, README.md, preflight.py,
                        CLAUDE.template.md and settings.fragment.json, plus
                        tools/, src/System/ and the three JSON files, the
                        Controller and its dependency chain (D63); stamped
                        with the source commit
```

## Invariants

These are the load-bearing facts. Any change that violates one silently breaks
the system, because none of them fail loudly. Assert them in the harness rather
than trusting them.

1. **Effort is subagent-only.** Agent teams teammates follow the lead's effort
   level. With `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` set, a *named* subagent
   launches as a teammate, and naming is mandatory here for addressability.
   That variable therefore destroys the effort dimension with no error.
2. **A per-invocation `model` beats frontmatter.** The orchestrator must select
   by `subagent_type` alone and never pass `model` on the Agent tool call.
3. **`CLAUDE_CODE_EFFORT_LEVEL` beats frontmatter `effort`.** Frontmatter
   overrides the session level but not this environment variable.
4. **`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` beats everything.** It flattens all
   fifteen cells onto one model.
5. **Haiku is excluded from the routing table, permanently.** Not because it
   lacks effort levels: that was this invariant's original justification and E8
   (`docs/FINDINGS.md`, 2026-09-05) disproved it directly, a defined `effort: high`
   haiku worker showed "Haiku 4.5 (high)" on its `/tasks` row. The exclusion
   itself is a decision, not a gap: `docs/DECISIONS.md` D5, 2026-09-05.
6. **A blocked model is substituted, not failed.** An `availableModels`
   allowlist that excludes fable will run fable-routed work on something else.
7. **A user-stopped worker cannot be resumed.** Only orchestrator-stopped and
   completed workers resume on message. Observed, not documented, as of
   2026-09-05.

Each invariant needs a corresponding assertion in `test/harness/`. Invariant 7
has none: `check.py`'s INV7 is a permanent SKIP, because whether a worker was
user-stopped or orchestrator-stopped is not visible to any static check. It
was confirmed empirically instead, E4 in `docs/FINDINGS.md` (2026-09-05); that
observation, not a harness assertion, is the invariant's evidence, and it is
this list's one deliberate exception rather than an unassessed assumption.

## Working practice

**Diagnostic before patch.** When something misbehaves, produce an audit of
observed state first and write it to `docs/FINDINGS.md`. Do not patch from a
hypothesis. Most failures in this system are silent substitutions, so the
symptom is usually "the output was worse than expected", which is
indistinguishable from bad routing, a bad handover prompt, and a bad worker
persona until you look at the actual `/tasks` row.

**Atomic edits with guards.** One conceptual change per commit. If a change
touches the frontmatter of multiple worker files, regenerate them from the
generator rather than hand-editing fifteen files, and diff the result.

**A routing row must earn its place.** A row in `src/ROUTING.md`'s table is not
a passive destination. Measured on 2026-09-06, adding one changed how tasks were
classified: two fixtures answered correctly before the row existed were answered
incorrectly with it and correctly again once it was removed, reaching it by
bending different axes (`test/results/2026-09-06-attractor-diagnosis.md`, D13).
Coverage is therefore not a goal in itself, and a row with no fixture behind it
is a liability rather than a convenience. Every row must be backed by a fixture
whose confirmed answer lands on it, asserted by the harness's ROW-BACKED check,
and any change to the table needs a before-and-after fixture run, because no
static check can see this class of defect.

**Regression harness before delivery.** Nothing ships out of `dist/` until the
harness passes. Adding a new cell, changing the routing table, or changing the
persona all require a harness run with results committed to `test/results/`.

**No silent capability claims.** If you cannot verify a Claude Code behaviour,
write it in `docs/FINDINGS.md` as unverified with the date and the version
checked. Do not encode it as fact in `src/`. Platform behaviour here has changed
repeatedly and version-gated features are common.

**Paid runs.** A `claude -p` run (a benchmark, a routing batch, a Controller
run, a probe) is started by the session itself, not by asking first: state
what is about to run and its projected cost in USD, then start it. Ask before
starting only when the projection exceeds USD 100. Report the measured cost
beside the projection once the run finishes (D57).

## Verification is the hard problem

Routing correctness is not directly observable. A worker that produced a decent
answer might have been correctly routed, over-provisioned, or run on a
substituted model. Three signals exist, in decreasing reliability:

1. The `/tasks` row, which names the model and shows the effort level when the
   definition sets one. Requires v2.1.243 or later. This is ground truth for
   *what ran*, not for *whether it should have*.
2. The worker transcript at
   `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`.
   Determine empirically what it records about model and effort; do not assume.
   A `compact_boundary` entry is a reliable signal the cell was undersized.
3. Token accounting per run, compared against the cell's expected cost band.

Routing *appropriateness* has no automatic signal at all. It requires fixtures:
tasks with a human-assigned correct cell, run through the orchestrator, scored
on whether it picked that cell. Build `test/fixtures/` before tuning the table,
or you will tune against anecdote.

## Open questions worth developing

These are unresolved, not decided. Do not close one without evidence in
`docs/FINDINGS.md`.

- ~~Does the effort level appear in the worker transcript, or only in the panel?~~
  Resolved 2026-09-05 (E7, `docs/FINDINGS.md`): it appears in the transcript. Each worker's
  `agent-{agentId}.jsonl` also has a sibling `agent-{agentId}.meta.json`, undocumented before this check.
- Does telling a worker its own cell change its behaviour, usefully or
  otherwise (`docs/PREMISES.md` P39)? All fifteen `model-specific-*` sections
  in `WORKER_PERSONA.md` are empty (the generator omits an empty section
  entirely), so the question is not yet askable of real behaviour; it can be
  tested cheaply by filling one section and re-running one benchmark task at
  the bar, no code change needed. Untested by construction; still open.
- What is the actual escalation rate from each starting cell? Three escalations
  from one cell means the rubric is wrong for that task class, but the threshold
  is a guess. The table now has one starting cell (the floor) and one
  escalation trigger (section 4), and `route.py --record --escalation` now
  records the rate per project; the first opportunity to fire it live,
  Stage 12's dogfood install, had not yet done so as of 2026-09-15
  (`test/results/2026-09-15-dogfood-install.md`). Still open as a number.
- ~~Is the three-axis rubric better than a simpler two-axis one? Blast radius
  and intelligence sensitivity may be measuring the same thing.~~ Made moot,
  not answered, 2026-09-14 (D44, D45): the shipped table routes every task to
  the floor regardless of the assessment, so no axis, alone or combined,
  currently selects a destination. The two-axis variant `score_routing.py
  --classifier two-stage --axes 2` measured only steering-grade (three runs,
  sonnet, `test/results/2026-09-11-routing-sonnet-d65b476-two-stage-2axis-
  summary.md`) before the two-stage design itself was rejected on cost (D40).
  Whether a two-axis assessment would serve better if the table ever grows a
  row again is unasked.
- ~~Does the orchestrator's own model matter?~~ Answered 2026-09-06, three runs per model
  on bundle `2026-09-05-4cf35f7` (`test/results/2026-09-06-routing-{sonnet,opus}-summary.md`):
  yes, and opus is the better orchestrator. Opus scored 45/51 (88.2 percent, 95 percent Wilson
  [76.6, 94.5]) against sonnet's 32/51 (62.7 percent, [49.0, 74.7]); the intervals do not
  overlap. Opus cost 7.0 times more in total and 5.0 times more per correct verdict
  (USD 0.2245 against USD 0.0451).

  This reverses the earlier answer. E12 (2026-09-05, one run per model) recorded sonnet ahead
  on both counts, but it ran before the calibration instruction was fixed (D6) and before the
  clarify rule existed (D10). Opus's apparent weakness was almost entirely spurious clarifying,
  which the clarify rule removed: it now clarifies exactly once per run, on F16, where clarify
  is the confirmed answer. Whether opus's accuracy is worth 5 times the cost per correct verdict
  depends on what one wrong routing decision costs, which is the cost and quality benchmark's
  question, not this one's.
- ~~Does any benchmark task exist that `worker-sonnet-low` measurably fails?~~
  Answered 2026-09-13 (D42, `docs/PLAN.md` Stage 7): yes, one of eleven. T10
  fails at every sonnet cell (xhigh 0 of 12) and confirms at `worker-opus-high`,
  9 of 9 (elsewhere cited as 12 of 12, `src/routing_priors.json`: confirmation
  plus the search runs that also passed, D42 point 4; both counts describe
  the same evidence). But what it fails on is not capability: all 20 failing sonnet runs
  verified that the task's frozen-file constraint had a false justification,
  wrote that down, and obeyed the constraint anyway; opus treated the falsified
  justification as dissolving the instruction. T9 (a false measurement, not a
  false constraint) and T11 (T7's lineage at larger scale) both confirmed at the
  floor. The open question this leaves is whether that disposition generalises
  beyond the one shape tested, and what a routing row that buys it should say.
  Not tested further by this plan: Stage 9 through 12 measured T10's exact
  shape repeatedly (D47, D56, D58, D59, eleven fleet and B0-brief runs
  combined) but no second falsified-constraint task was built. Still open.
- ~~Is the cost of a routing verdict on the ledger, alongside the cost of the
  work it routes?~~ Resolved 2026-09-11 (`docs/COST.md`): it was not, until
  this stage. Mean opus verdict cost per fixture (USD 0.1645, pooled across
  108 verdicts against bundle `2026-09-07-af94deb`) against mean
  `worker-sonnet-low` cost per benchmark run (USD 0.1641, pooled across 96
  runs, T1 through T8) is a ratio of 1.003: at the cheapest cell, which is
  where every measured task has landed, the router costs essentially the
  same as the work it routes.
- ~~Is horizon assessable before any tool call is made, or is the table's own
  history evidence that it is the least reliable of the three axes?~~
  Answered 2026-09-14 (D44, `test/results/2026-09-14-table-collapse-before-after.md`):
  not independently of the destination. When the table was reduced to one
  row above the floor, opus's horizon read on unchanged fixtures under an
  unchanged rubric moved toward whichever cell it wanted: F10 from medium
  nine of nine to short eight of nine, F11 from long-or-medium to medium
  nine of nine. That is D13's attractor measured at reporting grade in both
  directions, and it is why the shipped table (D45) has no rows above the
  floor. T10's evidence lives in ROUTING.md section 4 as an escalation
  trigger the floor worker raises after reading the code. The remaining
  question, whether the three axes, which now route nothing, earn their
  verdict cost as a diagnostic record, Stage 13 answers: yes, trivially.
  E27 (`docs/FINDINGS.md`, 2026-09-15) shows a verdict's cost is dominated
  by reading `ORCHESTRATOR.md` itself (about 17.8k tokens of cache
  creation against 200 to 290 output tokens for the whole reply); the
  three-axis line is a few dozen of those output tokens and its removal
  would not move the verdict's cost measurably. The question worth asking
  is not whether the axes are cheap enough to keep, which they are, but
  whether `ORCHESTRATOR.md` itself is, and section 2's own text already
  answers why the assessment stays regardless: it is the record a wrong
  routing is diagnosed from, and dropping it is a change with its own
  before-and-after measurement (D44), not a decision to make on cost
  alone.
- ~~Does a `compact_boundary` reliably predict that decomposing the task
  would have helped (`docs/PREMISES.md` P29)?~~ Answered 2026-09-16
  (D80, `docs/COST.md`, "Decomposition against a single compacting
  worker"): yes, decisively, on the one task shape tested. Twelve runs
  per arm, same task, same window: a single worker that compacts
  mid-task failed 11 of 12 (task not completed or its constraint
  violated); the same task split into two sub-handovers before the
  trigger fired, each restating the constraint and carrying the prior
  part's own output forward, failed 0 of 12, non-overlapping 95 percent
  Wilson intervals. `src/ROUTING.md` section 2 now instructs splitting
  on `route.py --explain`'s overflow advisory. Not answered: whether this
  generalises beyond T12's shape (one long, uniform, chunk-by-chunk read
  task), since no second shape was built to test it.
- Does `.claude/context-usage.json`'s `tasks` entry, meant to carry a
  running worker's own token usage (`tokenSamples`, `docs/PREMISES.md`
  P29's companion question), ever populate outside a fabricated example?
  Narrowed twice, not answered: a 38-second worker left it empty (Plan 4
  Stage D), and a multi-minute worker with the tasks panel open left it
  empty too (Plan 5 Stage D, `docs/FINDINGS.md`). Duration and panel
  visibility are both ruled out; the mechanism that should populate it,
  whatever triggers a per-worker refresh tick, is unverified. Do not
  encode a claim about `tokenSamples`' actual shape anywhere in `src/`
  beyond `test/fixtures/system/statusline-sample.json`'s
  documentation-derived guess until a live capture replaces it.

## Dogfooding

Permitted, with two rules. Run it from a session whose working directory is a
*consumer* project, never this repository. And install from `dist/`, never from
`src/`, so the version under test is a fixed artefact rather than whatever is
half-edited on disk.

Log every dogfooding run in `test/results/` with the `dist/` version, the tasks
given, the cells chosen, and whether you agreed with the choice.

## Documentation style

Australian English. No em-dashes. Plain declarative prose. State constraints as
constraints rather than as advice. Where a behaviour is version-gated, name the
version. Where something is unverified, say so in the sentence that describes
it, not in a footnote.
