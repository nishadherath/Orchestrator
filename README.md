# Orchestrator

A cost-routing layer for Claude Code subagents, and the measurement
apparatus that says whether it is worth having. Read this file in ten
minutes; every claim below names the decision entry (`D<n>` in
`docs/DECISIONS.md`), the finding (`E<n>` in `docs/FINDINGS.md`) or the
result file it rests on, and anything unverified says so in the same
sentence. `docs/AUDIT-2026-09-16.md` is the audit this file was written
after; where the two disagree, the audit is the record of what was checked.

## What it achieves

The bundle in `dist/` installs into any Claude Code project and makes the
top-level session an orchestrator: it assesses each task on a fixed rubric,
resolves a worker cell in code from that assessment plus the project's own
history, spawns exactly that cell, and records the outcome so the next
resolution is better informed. Fifteen worker definitions cover three
models (sonnet, opus, fable) at five effort levels (low to max), one
definition per cell, generated from one persona (D3).

What has been measured, which is the part to hold on to:

- Ten of the eleven benchmark tasks built for this repository cleared at
  the cheapest cell, `worker-sonnet-low`, at the reporting bar of nine
  runs with a 95 percent Wilson lower bound above 0.7 (`docs/FRONTIERS.md`,
  D42). The one exception, T10, failed at every sonnet effort level and
  passed at `worker-opus-high` nine of nine; what it failed on was
  obeying a stated constraint whose justification the worker had itself
  shown to be false, not capability (D42).
- A routing verdict from an opus orchestrator costs about as much as the
  floor run it routes: the ratio was 1.003 when first measured and 1.40
  after a platform-side price shift on 2026-09-15 (`docs/COST.md`, E27).
  The premise ledger's arithmetic on those two figures is that no
  floor-failure rate can make routing cheaper than sending everything to
  the floor and escalating on failure (`docs/PREMISES.md`, "Dissolution
  check"). The honest product claim is therefore insurance against an
  undetected wrong answer on consequential work, not money saved.
- Because of the first two points, the shipped routing table has one row:
  every task starts at `worker-sonnet-low` (D44, D45). Cells above it are
  rungs on a ladder that a project's own recorded failures activate
  (D64), plus two escalation triggers described below.
- A separate multi-role problem-solving system, the Controller, was built
  and measured against the floor on T10: right in every run that finished,
  six of nine finished, at 10.8 times the floor's cost per solved task
  (D59). It ships and is invoked only on the one trigger where that
  head-to-head evidence exists, by explicit choice (D63).
- A worker whose context compacts mid-task fails most of the time on the
  one task shape tested; the same task split into two sub-handovers before
  the compaction point failed never: 11 of 12 against 0 of 12,
  non-overlapping intervals (D80). The orchestrator is told to split when
  the ledger's overflow advisory fires.

## How it works

Everything the orchestrator does comes from `ORCHESTRATOR.md`, which
`tools/build_dist.py` assembles from `src/ROUTING.md` and
`src/LIFECYCLE.md` with the evidence stripped out, so the model making the
assessment never sees which cells exist or how they have performed. That
stripping is the fix for a measured defect: an orchestrator that can see
the destinations bends its assessment toward the one it prefers, on the
same fixtures under the same rubric (D13, D44).

One task, end to end:

1. **Assess.** The orchestrator writes one line: sensitivity
   (mechanical, structured, open), horizon (short, medium, long), blast
   radius (contained, consequential), plus `self_directed` and
   `prior_failure`. Two of the five fields are recorded but not used to
   choose a cell (D64).
2. **Resolve.** It runs `python3 tools/route.py --from-line "<line>"
   --project . --explain` with the Bash tool. The script reads
   `src/routing_priors.json` (a Beta prior per assessment bucket, seeded
   from the benchmark with capped effective sample sizes of 3 to 10) and
   the project's `.claude/routing-ledger.jsonl`, computes the posterior
   pass probability of the floor and each active rung, decides whether the
   Controller pre-empts, and prints the cell to spawn. With an empty
   ledger the answer is the floor for every assessment except an open,
   consequential one, where a labelled risk-appetite policy runs the
   Controller first (D64; `routing_priors.json` `controller_rule`).
3. **Spawn.** The Agent tool (also called the Task tool) with
   `subagent_type` set to the cell name and never a `model` parameter,
   because a per-invocation model silently overrides the definition
   (invariant 2, `CLAUDE.md`). The handover states objective, constraints,
   acceptance criteria and return contract; the worker has no other
   context.
4. **Record.** `route.py --record` appends the outcome, cost and any
   escalations to the ledger. A rung outside the default ladder activates
   for a bucket after three recorded outcomes at that cell with a
   posterior above 0.5; the project's own cost figures replace the shipped
   table after five (`routing_priors.json` `steering`). A floor failure
   recorded with `--outcome fail` and no `--escalation` counts in the
   posterior the same as an escalated one (fixed 2026-09-16, audit A4,
   docs/PLAN-6.md B.5).

Escalation has two triggers beyond "the next rung on failure". A worker
that reports it cannot meet its acceptance criteria without acting against
a constraint whose stated reason it has checked and found false sends the
task straight to the Controller, T10's shape (D63). And the resolver itself
can name the Controller before any worker runs, on the policy dial above or
on expected-cost arithmetic that fires nowhere on the shipped priors (D64).
A Controller run is `tools/system_controller.py` in quick mode: a Python
state machine that calls `claude -p` for six roles over a validated
record ledger and writes `REPORT.md`; measured at USD 2.62 per run plus
USD 0.36 to apply the answer through one floor worker
(`src/cost_table.json`).

Context is handled on disk, never in the model's memory. A status-line
script writes the orchestrator's own context usage to
`.claude/context-main.json` and each subagent's peak token usage to
`.claude/context-tasks.json`, one file per writer so the two status lines
racing each other cannot clobber one another's data (audit A12);
`--explain` reads `context-main.json` and compares it against a 70 percent
threshold and says when to write a handoff (`tools/handoff.py`, a
ten-heading file with computed cost and time lines) before the platform
compacts. A `SessionStart` hook on the `compact` matcher prints the
routing rule and the newest handoff after a compaction. The hook's
pending-worker listing is fed by `route.py --spawn`, run immediately
after the orchestrator's own Agent tool call (fixed 2026-09-16, audit
B1, docs/PLAN-6.md B.4): before this fix the step that feeds the
listing was not in `ORCHESTRATOR.md`, so the listing could never
populate in a consumer project.

Seven platform settings defeat all of this silently, each documented with
its source in `docs/FINDINGS.md` and listed as an invariant in `CLAUDE.md`:
the agent-teams flag flattens effort, a session effort variable overrides
frontmatter, a subagent model force flattens models, a model allowlist
substitutes rather than fails, haiku is excluded by decision (D5), a
user-stopped worker cannot be resumed (E4), and a per-invocation model
beats the definition. `dist/preflight.py` checks the ones a shell can see.

## How to use it

Install from `dist/`, never from `src/`; `dist/README.md` has the full
walkthrough for a new project and for one with an existing `CLAUDE.md`.
The short form:

```bash
CONSUMER=/path/to/your/project
mkdir -p "$CONSUMER/.claude" "$CONSUMER/tools" "$CONSUMER/src/System" "$CONSUMER/handoffs"
cp -r dist/.claude/. "$CONSUMER/.claude/"
cp dist/ORCHESTRATOR.md dist/README.md dist/preflight.py "$CONSUMER/"
cp dist/tools/*.py "$CONSUMER/tools/"
cp dist/src/*.json "$CONSUMER/src/"
cp -r dist/src/System/. "$CONSUMER/src/System/"
```

Then merge `dist/settings.fragment.json` into the project's
`.claude/settings.json`, add the line `Read ORCHESTRATOR.md before
delegating any task.` and the Handoffs section from
`dist/CLAUDE.template.md` to the project's `CLAUDE.md`, run
`python3 preflight.py` from the project root, and restart Claude Code if
`.claude/agents/` did not exist before the session started (E11).

Verify by giving the orchestrator one small task and reading its routing
line, which must state the assessment, the resolved cell and the reason.
A human watching the `/tasks` panel sees the model and effort on the
worker's row (E2); no agent, including the orchestrator, can read that
panel itself (E19), so the routing line and the worker transcript under
`~/.claude/projects/` are the signals a session can act on.

Two settings the fragment carries, added 2026-09-16 (docs/PLAN-6.md
B.3, B.7; both previously missing, audit A26): `autoCompactWindow`,
set to 200,000, project scope, confirmed to work (E31), so the handoff
threshold fires before the platform compacts; and the `Bash(python3
*)` permission, so the orchestrator can run `route.py` without a
prompt on every task. The commands in the fragment call `python3` by
that name; `preflight.py`'s "python3 on PATH" check now FAILs, naming
the fix, if it does not resolve.

## How to work on it

The repository is specification, verification and calibration; the only
runtime is the Controller. `CLAUDE.md` is the charter and applies to every
session here; `docs/PLAN.md` through `docs/PLAN-5.md` are the five
completed plans that built the current state, read for how, not as
instructions.

- **Harness.** `python3 test/harness/check.py` runs 31 static checks:
  the fifteen definitions match the generator, the routing data
  resolves every fixture to its expected cell, priors and cost rows carry
  provenance, every script's selftest passes without a `claude -p` call,
  and every authored file is clean of em-dashes, US spellings and a short
  banned-word list. A green run is 30 passes and one permanent skip
  (invariant 7 needs a live session). Results are committed under
  `test/results/` and `dist/` is rebuilt only from a green tree (D4).
- **Generated files.** `src/agents/` comes from `tools/generate_workers.py`
  over `src/WORKER_PERSONA.md` and `src/routing_table.json`;
  `src/routing_priors.json` from `tools/generate_priors.py`; `dist/` from
  `tools/build_dist.py`. Edit the source, regenerate, diff. The four
  `ENGINEERING_PERSONA.*.md` files and their language profiles are
  generated too, elsewhere, and are kept here without their generator
  (D2); a session loads its own class's core, `ai-prompting` and, for
  Python work, `python`; the other 52 profiles are unused here.
- **Measurement.** `test/harness/benchmark.py` climbs the cost ladder on a
  task fixture and grades with the fixture's own `grade.sh`;
  `score_routing.py` scores an orchestrator's verdicts against
  `test/fixtures/routing.jsonl`; `compaction_bench.py` measures
  constraint survival across a compaction; `fleet_benchmark.py` runs the
  Controller against a task. All spend money and none is run by the
  harness. Two thresholds hold throughout: three runs steer, nine runs
  report, and a claim below nine is labelled steering (D37).
- **Records.** `docs/DECISIONS.md` is append-only, eighty entries, each
  with the condition that would reverse it. `docs/FINDINGS.md` separates
  what the platform is documented to do from what a live session showed
  it doing, by version. `docs/PREMISES.md` is the forty-row ledger of
  what the routing layer assumes, classed as law, policy, habit or
  unverified.
- **Standing rules.** A session that must change its own model or effort
  writes a handoff with `tools/handoff.py` first; development work
  delegated to a subagent is routed through `tools/route.py` like any
  consumer task (`CLAUDE.md`, "Handoffs and routing"). A session starts
  paid `claude -p` runs itself after stating the projected cost, and asks
  first only above USD 100 (D57).

## Map

| Path | What it is |
| :--- | :--- |
| `src/ROUTING.md`, `src/LIFECYCLE.md` | The orchestrator's instructions; rationale spans are stripped on build |
| `src/WORKER_PERSONA.md`, `src/agents/` | The worker persona and the fifteen generated definitions |
| `src/routing_table.json`, `routing_priors.json`, `cost_table.json` | The two-rule table, the per-bucket priors, the measured unit costs |
| `src/System/` | The Controller's problem-solving framework: roles, techniques, record schemas |
| `src/README.md`, `preflight.py`, `settings.fragment.json`, `CLAUDE.template.md` | The consumer-facing install guide and its helpers |
| `tools/` | `route.py`, `handoff.py`, `context_probe.py`, `system_controller.py` ship; the generators and `build_dist.py` do not |
| `dist/` | The installable bundle, stamped with its source commit |
| `test/harness/` | `check.py` and the paid measurement scripts |
| `test/fixtures/` | 18 routing fixtures, 15 benchmark tasks, the schema examples |
| `test/results/` | 176 dated result files (2026-09-16); no index yet (audit C5, Stage D.3) |
| `docs/` | Decisions, findings, premises, cost, the design documents, the six plans, this audit |
| `handoffs/` | Seven session handoffs, each passing `handoff.py check` |
| `graft/`, `dist-with-rationale/` | Gitignored local artefacts: a code index for one machine's tooling, and a bundle built with `--with-rationale` for comparison, rebuilt on demand |

## What is not known

- Whether the ten-of-eleven floor result generalises past synthetic
  tasks with plantable defects to real backlog work; the two real tasks
  tried were both routed in ways the owner disagreed with (E13,
  `docs/PREMISES.md` P19 and P34). Unverified.
- Whether the decomposition result (D80) holds on shapes other than the
  one measured. Unverified.
- Whether the subagent status line ever reports a running worker's
  tokens: two interactive sessions, one lasting minutes with the panel
  open, saw the field stay empty (`docs/FINDINGS.md`, Plan 4 and Plan 5
  Stage D). Unverified; nothing in the bundle depends on it.
- How often the escalation triggers fire in real use: the instrument
  exists (`route.py --record --escalation`) and no consumer ledger has
  been read yet. Unverified.
- The fifteen cell-specific persona sections are all empty, so whether
  telling a worker its own cell helps or hurts has never been tested
  (`docs/PREMISES.md` P39). Unverified.
