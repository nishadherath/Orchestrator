# CLAUDE.md

## Required retrieval and persona

Every task, session, agent and subagent starts with `graft_check_freshness`.
Use scoped Graft search, file API and call graphs before broad repository reads.
Direct reads are for exact edits, verification and unindexed files. If Graft is
unavailable, repair or report the connection before discovery. Put this rule,
the repository root and relevant results in every handoff; each child verifies
its own access. Configuration and limits are in `docs/GRAFT.md`.

Load `ENGINEERING_PERSONA.<class>.md` for the configured model class, using
sonnet when unknown. Also load `ai-prompting.<class>.md`, `python.<class>.md`
for `tools/` or `test/harness/`, and `bash.<class>.md` for fixture `grade.sh`
work. The harness sets the class; never infer it from model quality.

Be direct, honest and economical with tokens. Verify assumptions and distinguish
observations, inferences and untested risks. Use Australian English, no em
dashes, and plain declarative prose.

## Current work

Stages 0-7 of `docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md` are complete.
The active programme is `docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md`.
Stage N0 is complete. Its historical design contract is
`docs/WORKER-EXECUTION-CONTRACT.md` and its evidence record is
`docs/stage-results/worker-n0.md`.
N0A's design amendment is recorded in
`docs/WORKER-EXECUTION-CONTRACT-v2.md`, with the implementation matrix in
`docs/WORKER-N1-ACCEPTANCE-v2.md` and evidence in `docs/stage-results/worker-n0a.md`.
N1's offline executor and installable adapter are complete for review in
`docs/stage-results/worker-n1.md`. The operator has directed N2 managed
delegation next; its scope is in
`docs/WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md`.
Experimental Controller remediation is separately deferred in
`docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md`; no X stage has started.
The operator chooses the start and reviews every completed stage. Follow
`docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md` for stage and cost gates.
The earlier Controller programme has R0-R4 records and R5 scaffolding, but its
live evaluation remains paused pending the documented remediation. The shipped
B0 default remains unchanged. Earlier plans and handoffs are historical
evidence, not active instructions.

This repository builds a cost-routing bundle for Claude Code subagents: fifteen
model/effort definitions, a ledger-aware resolver, acceptance verification,
handoffs and a budgeted multi-role Controller. The consumer guide is
`src/README.md`. Runtime behaviour belongs in `src/` and reaches `dist/` only
through `tools/build_dist.py` after the offline harness passes.

`src/ORCHESTRATOR_CORE.md`, `src/ROUTING.md` and `src/LIFECYCLE.md` are product
deliverables. They do not route development work in this repository. Do not
follow a half-edited product prompt as a session instruction. Dogfooding runs
only from a separate consumer project installed from `dist/`.

## Development handoffs and delegation

Before changing model or effort, starting a fresh session, or launching any
agent or subagent, create a concise handoff with `tools/handoff.py new`, fill
every section, validate it with `tools/handoff.py check`, and notify the
operator. Include target model/effort, dated direct API cost and elapsed-time
ranges, token/cache assumptions, uncertainty and any separate paid experiment
subtotal. Unknown cost is not zero. The receiving session reads the named file
first. A completed stage alone does not require a switch.

When development work is delegated, record the assessment line, resolve it with
`python3 tools/route.py --from-line "<line>" --project . --explain`, and launch
the named cell. This is repository-development routing, not product dogfooding.

## Load-bearing invariants

1. Agent teams must remain off; teammates inherit the lead's effort.
2. Agent-tool delegation selects through `subagent_type` and never passes
   `model`, which overrides worker frontmatter.
3. `CLAUDE_CODE_EFFORT_LEVEL` overrides worker effort.
4. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` flattens the model dimension.
5. Haiku remains excluded by decision D5, despite supporting effort levels.
6. An `availableModels` exclusion substitutes another model rather than failing.
7. A user-stopped worker is not resumable; E4 is the empirical evidence.

The harness asserts every statically observable invariant. Do not change the
routing table, persona or worker frontmatter without regeneration and the full
harness. A routing row also needs a confirmed fixture and before/after routing
measurement because visible destinations can bias assessment.

## Working practice

- Preserve pre-existing work and local configuration. Generated workers come
  from `src/WORKER_PERSONA.md`; never hand-edit all fifteen.
- Diagnose observed state before patching. Record new platform behaviour in
  `docs/FINDINGS.md`, labelled verified or unverified with date and version.
- Nothing ships from `dist/` until the harness passes. Rebuild through
  `tools/build_dist.py`; do not edit generated bundle files directly.
- A `claude -p` benchmark, probe or Controller run requires a stated USD cost
  projection before execution and measured cost afterwards. Ask first only
  above USD 100. Ordinary offline checks do not need approval.
- Model identity, routing correctness and routing appropriateness are separate.
  Use observed model/effort evidence, acceptance evidence and fixtures rather
  than treating a good-looking answer as proof of correct routing.
- Keep unresolved research in `docs/PREMISES.md`, `docs/FINDINGS.md` and the
  active roadmap instead of expanding this standing file.

## Source map

- `src/ORCHESTRATOR_CORE.md`: stable installed operating contract.
- `src/ROUTING.md`, `src/LIFECYCLE.md`: detailed shipped reference source.
- `src/WORKER_PERSONA.md`: generated worker source.
- `src/System/`: Controller role, technique and record contracts.
- `tools/route.py`: resolution, pending ledger, completion and recovery.
- `tools/system_controller.py`: budgeted quick-mode state machine.
- `tools/build_dist.py`: checked bundle assembly.
- `test/harness/check.py`: complete offline gate.
- `docs/DECISIONS.md`, `docs/FINDINGS.md`: decisions and verified behaviour.

Run dogfooding only from a consumer checkout installed from `dist/`. Record its
bundle version, tasks, selected cells and assessment in `test/results/`.
