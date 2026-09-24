# Orchestrator

A cost-routing layer for Claude Code subagents, and the measurement
apparatus that says whether it is worth having. Read this file in ten
minutes; every claim below names the decision entry (`D<n>` in
`docs/DECISIONS.md`), the finding (`E<n>` in `docs/FINDINGS.md`) or the
result file it rests on, and anything unverified says so in the same
sentence. `docs/AUDIT-2026-09-16.md` is the audit this file was written
after; where the two disagree, the audit is the record of what was checked.

The project and redistributable are licensed under Apache-2.0. The W09
candidate is mechanically release-ready; publication remains an explicit
operator action.

The next planned development programme is
[worker routing, execution and delegation remediation](docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md).
[Experimental Controller remediation](docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md)
is a separate deferred programme. Both follow the
[staged execution protocol](docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md);
the worker programme started on operator direction. N0 is the historical
contract baseline; N0A through N3 are complete for offline review. The Controller
programme remains deferred. Each stage stops for review. The N0 outputs are the
[worker execution contract](docs/WORKER-EXECUTION-CONTRACT.md) and
[stage record](docs/stage-results/worker-n0.md).

The [worker-first sequencing plan](docs/WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md)
adds N0A before N1 to correct shared contracts and test dependencies. It is the
current planning entry point and includes model/effort choices, acceptance
gates and costs. N0A through N3 are complete for offline review: see the
[v2 contract](docs/WORKER-EXECUTION-CONTRACT-v2.md),
[N1 acceptance matrix](docs/WORKER-N1-ACCEPTANCE-v2.md) and
[N1 stage result](docs/stage-results/worker-n1.md) and
[N2 stage result](docs/stage-results/worker-n2.md) and
[N3 stage result](docs/stage-results/worker-n3.md). N1 adds a durable B0
executor and installable worker adapter. N2 adds an opt-in managed child graph
under one root and budget, tested with fake transports. The real adapter rejects
managed delegation until host isolation is proven; automatic interactive
dispatch still follows the existing route. N3 adds a public-evidence
[experimental worker selector](src/WORKER-SELECTOR.md) with all 15 cells,
failure classification and provenance-checked overrides. Its decisions are
journalled beside B0; no N3 candidate can change automatic dispatch yet.
Controller work remains deferred.

The earlier [Controller-aware routing programme](docs/CONTROLLER-ROUTING-PLAN.md)
has completed R0-R4 records and R5 offline scaffolding. The 2026-09-19 review
reopened R5 readiness: its current synthetic grader accepts public-label-only
results, and campaign restart/dependency coverage needs repair. The deferred
plan records the fixes and the replacement quality evaluation. The direct
Controller enforces integrity-v1 and
emits validated evidence packets, while one registry resolves every Sonnet,
Opus and Fable effort cell without implicit fall-through. Durable project,
session and task `auto/on/off` controls now resolve with explicit precedence
through the `/controller` command and provider-free CLI. The qualified router
remains B0 until the evaluation stages pass. The provisional R4 path can plan
and execute a Controller under explicit structured dispatch, but is not the
automatic shipping default. R5 now includes a 48-task, 288-variant synthetic
corpus with a separate grading area, a 60-call all-cell matrix runtime and
an 18-episode B/S/A pilot runtime. These are plumbing fixtures, not qualified
task-quality evidence; campaign safety is limited by the restart defect above.
The paid matrix and pilot remain paused and have not run, so live
Fable/effort behaviour and Controller uplift remain unmeasured.

## What it achieves

The bundle in `dist/` installs into any Claude Code project and makes the
top-level session an orchestrator: it assesses each task on a fixed rubric,
starts at `worker-sonnet-low`, permits one same-cell repair after observable
failure, then permits one `worker-opus-high` fallback. It records outcomes for
cost, capability and overflow diagnostics; history does not change this
reserved-qualified default. Fifteen worker definitions cover three
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
- Because of the first two points, every task starts at `worker-sonnet-low`.
  The real-world reserved comparison then selected the fixed B0 sequence over
  the adaptive B1 policy: B0 accepted 12/24 episodes and B1 accepted 10/24,
  with two B0 paired wins and no B1 wins. B1 also increased false successes
  from 12 to 14 and cost 20.97 percent more per accepted result (D107). The
  fixed sequence therefore allows one floor repair and one Opus-high fallback,
  with no Controller.
- The complete staged campaign executed 104 live episodes: 24 pilot, 32
  development and 48 reserved. Identity, accounting, hash-chained event
  records, actor boundaries and protected external graders were validated for
  the recorded runs. The comparison qualified B0; it did not demonstrate that
  either policy solves every task family (`docs/REAL-WORLD-EVALUATION-PLAN.md`).
- A separate multi-role problem-solving system, the Controller, was built
  and measured against the floor on T10: right in every run that finished,
  six of nine finished, at 10.8 times the floor's cost per solved task
  (D59). It remains available for historical audit and explicit rollback, but
  the qualified default does not invoke it (D107). Its maintained functional
  and operational reference is [`src/CONTROLLER.md`](src/CONTROLLER.md).
  Its direct-run default now freezes acceptance, gates unstable ledgers,
  enforces complete critiques and Selector exclusions, and writes a validated
  `controller-evidence.json` handoff (D110). This does not change B0 routing.
- A worker whose context compacts mid-task fails most of the time on the
  one task shape tested; the same task split into two sub-handovers before
  the compaction point failed never: 11 of 12 against 0 of 12,
  non-overlapping intervals (D80). The orchestrator is told to split when
  the ledger's overflow advisory fires.

## How it works

Everything the orchestrator does comes from `ORCHESTRATOR.md`, which
`tools/build_dist.py` assembles from the concise `src/ORCHESTRATOR_CORE.md`.
Detailed routing and lifecycle material ships as
`ORCHESTRATOR-REFERENCE.md` and is loaded only for named recovery or diagnostic
triggers. Evidence remains stripped from that reference, so the model making
the assessment never sees which cells exist or how they have performed. That
stripping is the fix for a measured defect: an orchestrator that can see
the destinations bends its assessment toward the one it prefers, on the
same fixtures under the same rubric (D13, D44).

One task, end to end:

1. **Assess.** The orchestrator writes one line: sensitivity
   (mechanical, structured, open), horizon (short, medium, long), blast
   radius (contained, consequential), plus `self_directed` and
   `prior_failure`. Under B0 none of the five changes the first cell;
   sensitivity, horizon and blast radius choose the diagnostic bucket,
   `self_directed` is retained as evidence, and `prior_failure` is used only
   by explicit historical adaptive replay (D108).
2. **Resolve.** It runs `python3 tools/route.py --from-line "<line>"
   --project . --explain` with the Bash tool. The script reads the project's
   evidence and prints diagnostics, the fixed B0 sequence and the first cell.
   Every assessment and ledger state resolves to `worker-sonnet-low`, including
   open consequential work and historical frontier signals. Adaptive posterior
   calculations remain inspectable but cannot change dispatch (D107).
3. **Spawn.** Before dispatch, the orchestrator freezes a task-specific
   acceptance contract containing the required outputs, constraints, protected
   paths and an executable check or review rubric. It then uses the Agent tool
   (also called the Task tool) with
   `subagent_type` set to the cell name and never a `model` parameter,
   because a per-invocation model silently overrides the definition
   (invariant 2, `CLAUDE.md`). The handover states objective, constraints,
   acceptance criteria and return contract; the worker has no other
   context.
4. **Verify and record.** `route.py --record` owns verification and atomically
   completes the pending ledger row. It stores evidence tied to the contract,
   current artefacts, protected baseline and repository revision. Claimed
   success, stale evidence and rubric work awaiting review cannot train the
   router; measured cost remains reportable. The project's own cost figures
   replace the shipped diagnostic table after five measured attempts, but no
   posterior activates a dispatch cell under B0. A floor failure
   recorded with `--outcome fail` and no `--escalation` counts in the
   posterior the same as an escalated one (fixed 2026-09-16, audit A4,
   docs/PLAN-6.md B.5). `src/SELF-LEARNING.md` is the full account of
   what this mechanism learns, what it cannot, and its limitations.

The term self-learning therefore refers to local, deterministic evidence
aggregation rather than model training. The ledger updates per-bucket
capability posteriors, measured cost and wall-clock estimates, compatibility
cohorts and the compaction advisory. Those values are visible through
`route.py --explain` and `preflight.py --status --explain`; they cannot change
the qualified B0 dispatch sequence. The earlier adaptive B1 policy is retained
only for historical replay, diagnostics and the documented rollback (D108).

Escalation is fixed: one `worker-sonnet-low` repair after observable failure,
then one `worker-opus-high` fallback, then stop. The resolver cannot pre-empt
this order or name the Controller. `tools/system_controller.py` and the former
adaptive arithmetic remain in the bundle to interpret old records and support
the documented rollback; they are outside the qualified default.

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
before the orchestrator's own Agent tool call. This freezes the acceptance
contract and pending ledger row before work can finish or fail (D88).

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
python3 dist/install.py plan --target /path/to/your/project
python3 dist/install.py apply --target /path/to/your/project
python3 /path/to/your/project/preflight.py --status
```

The installer verifies `bundle-manifest.json`, merges only declared values,
preserves unrelated configuration and records reversible backups. Use
`install.py status`, `uninstall` and `rollback` for lifecycle operations.
Restart Claude Code if `.claude/agents/` did not exist before the session
started (E11).

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

The repository contains the runtime routing, acceptance, accounting,
installation and diagnostic tools as well as their specification,
verification and calibration evidence. `CLAUDE.md` is the charter and applies
to every session here; completed plans are historical implementation records,
read for provenance rather than as current instructions.

- **Harness.** `python3 test/harness/check.py` is the canonical check count:
  the fifteen definitions match the generator, the routing data
  resolves every fixture to its expected cell, priors and cost rows carry
  provenance, every script's selftest passes without a `claude -p` call,
  and every authored file is clean of em-dashes, US spellings and a short
  banned-word list. Results are committed under
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
- **Records.** `docs/DECISIONS.md` is append-only; each entry carries
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
- **Graft.** Every project-development session starts with Graft freshness and
  uses scoped graph retrieval before broad source reads. The graph itself is
  gitignored. An authorised DeepSeek-backed semantic refresh uses
  `tools/graft_deep_refresh.ps1`, which loads credentials from the Windows user
  environment, applies the local forced-tool compatibility adapter without
  logging content, resumes the cache and removes its temporary files. The
  current graph covers 2,284 structural nodes and has no stale or pending
  meanings (`docs/GRAFT.md`).

## Map

| Path | What it is |
| :--- | :--- |
| `src/ROUTING.md`, `src/LIFECYCLE.md` | The orchestrator's instructions; rationale spans are stripped on build |
| `src/SELF-LEARNING.md` | The per-project ledger mechanism: what it learns, what it cannot, capabilities and limitations |
| `src/CONTROLLER.md` | The maintained Controller role system, task-suitability, phase, budget, recovery and qualification reference |
| `src/WORKER_PERSONA.md`, `src/agents/` | The worker persona and the fifteen generated definitions |
| `src/routing_table.json`, `routing_priors.json`, `cost_table.json` | The two-rule table, the per-bucket priors, the measured unit costs |
| `src/System/` | The Controller's problem-solving framework: roles, techniques, record schemas |
| `src/README.md`, `preflight.py`, `settings.fragment.json`, `CLAUDE.template.md` | The consumer-facing install guide and its helpers |
| `tools/` | `route.py`, `handoff.py`, `context_probe.py`, `controller_control.py`, `system_controller.py` ship; the generators and `build_dist.py` do not |
| `dist/` | The installable bundle, stamped with its source commit |
| `test/harness/` | `check.py` and the paid measurement scripts |
| `test/fixtures/` | 18 routing fixtures, 15 benchmark tasks, the schema examples |
| `test/results/` | Dated benchmark, audit, live calibration and real-world evaluation evidence |
| `docs/` | Decisions, findings, premises, costs, audits, design records and completed plans |
| `handoffs/` | Checked session handoffs retained for model, effort and session transitions |
| `graft/`, `dist-with-rationale/` | Gitignored local artefacts: a code index for one machine's tooling, and a bundle built with `--with-rationale` for comparison, rebuilt on demand |

## What is not known

- Whether the benchmark and 24-task synthetic real-world corpus generalise to
  independently sampled production backlogs. The corpus exercises realistic
  software failure shapes and hidden grading, but it is not an uncontaminated
  sample of external work. Unverified.
- Whether the decomposition result (D80) holds on shapes other than the
  one measured. Unverified.
- Whether the subagent status line ever reports a running worker's
  tokens: two interactive sessions, one lasting minutes with the panel
  open, saw the field stay empty (`docs/FINDINGS.md`, Plan 4 and Plan 5
  Stage D). Unverified; nothing in the bundle depends on it.
- How often the fixed repair and Opus fallback are needed in an ordinary
  consumer project. The evaluation campaign measured its frozen corpus, but no
  independent consumer ledger has been aggregated. Unverified.
- Whether a live Controller invocation can satisfy the complete qualified
  episode contract. Its adapter and accounting paths pass offline tests, but
  no paid campaign episode reached the Controller. Unverified.
- Provider-side invoice caps, live token-ceiling enforcement and billed savings
  from the reduced recurring context remain unverified. Local reservations and
  static token reductions do not prove those external effects.
- The fifteen cell-specific persona sections are all empty, so whether
  telling a worker its own cell helps or hurts has never been tested
  (`docs/PREMISES.md` P39). Unverified.
