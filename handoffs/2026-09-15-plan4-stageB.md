# Handoff: plan4-stageB

<!-- handoff.py new --slug plan4-stageB --reason model-change --to-model sonnet --to-effort high --from-model fable --from-effort high --project . --pending-workers -->
Written 2026-09-15 by fable, high. Reason: model-change.

## Goal

Execute Stage B of `docs/PLAN-4.md`: build the constraint-preservation
measurement and run it. Three benchmark fixtures (T12, T13, T14, one
load-bearing constraint shape each), `test/harness/compaction_bench.py`
(three arms, fixed cell, transcript-read compaction evidence per run), a
dry pass to confirm the compaction lands before the constrained action,
then 45 runs in the background and confirmation to nine where the
pre-registered rules say. Live spend USD 27 to 40, started by the session
with the projection stated first (rule 3). The pre-registration is
already written and does not change after the first run.

## Decisions already made

- D72 (`docs/DECISIONS.md`): the transcript is the first source for a
  worker's context; the trigger reserve is content-conditional (plain-noun
  [33,622, 35,147) tokens), never to be quoted as a constant; a refused
  summariser produces a stub summary that keeps nothing, and the
  measurement counts those (`stub-summary`); the Plan 4 fixes are Stage
  C's, not this stage's, and ship regardless of what this stage finds.
- `test/results/2026-09-15-compaction-preregistration.md`: shapes, arms,
  sample sizes, six exclusion and calibration rules, four decision rules,
  predictions. Apply them; do not re-argue them. A correction found
  before the first live run is recorded at the top of that file, as its
  precedent did; after the first run nothing changes.
- `docs/COMPACTION-DESIGN.md` section 13.6 and 13.7 fix
  `compaction_bench.py`'s and the fixtures' contracts; 13.8 the pass
  conditions. Where silent, choose the boring option and say so in the
  commit message.
- `benchmark.py` itself is not modified; its functions are imported.
- Stage C (sonnet, high, zero spend) may run in the same session while
  B.4's runs are in the background; nothing in C depends on B's result.

## Files and links that matter

- `docs/PLAN-4.md` Stage B; D72; the pre-registration; `docs/COMPACTION-DESIGN.md`
  sections 13.6, 13.7, 13.8.
- `test/results/2026-09-15-e30-transcripts.md` and `test/harness/extract_e30.py`:
  the extraction logic to lift into `compaction_bench.py` (boundary count,
  `preTokens`, per-turn totals, first total after a boundary, API error
  text, summary length and heading count).
- `test/harness/benchmark.py`: `load_task`, `seed_task`, `reset_task`,
  `run_cell`, `grade`, `fixture_fingerprint`, `BENCHMARK_INSTRUCTION`.
  `tools/claudep.py`: `call_claude`, `Checkpoint`, `wilson_interval`,
  `FORWARDER_PERMISSION_ARGS`, `unique_path`.
- `test/fixtures/benchmark/README.md` (the fixture contract and the
  five-case grader test rule); `test/fixtures/benchmark/T9` as the layout
  template.
- `tools/route.py` `_find_transcript_compactions` and `_claude_projects_slug`
  (D71): the transcript location logic, reusable as is.
- `src/CLAUDE.template.md`: the `# Compact instructions` section arm C
  appends to the consumer project's `CLAUDE.md`.
- `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch\probe-e30\`: E30's
  chunk generator pattern (350 lines of ten plain nouns per file, seeded).

## Verified facts

- Harness green at `6572147`, 28 checks.
- E30 calibration (`test/results/2026-09-15-e30-transcripts.md`): at
  window 130,000, five reads of about 6,400 tokens each compact exactly
  once, after the fourth read and before the fifth and the write; at
  100,000 the platform aborts for thrashing; at 150,000 no compaction.
  Forwarder plus worker cost USD 0.48 to 0.63 per run, 40 to 100 seconds.
- `claudep.call_claude` passes no `env=` to `subprocess.run`, so the
  forwarder inherits the harness process's environment; setting
  `CLAUDE_CODE_AUTO_COMPACT_WINDOW` in `os.environ` before the call is the
  mechanism, and E30 showed it reaches the spawned worker.
- `agent-*.meta.json` carries `agentType` and no `name` (D71); locate the
  run's transcript by cell and mtime after the run's own start clock.
- The status line does not fire under `claude -p` (D71), so nothing in
  this stage depends on `.claude/context-usage.json`.
- `seed_task` copies `repo/` into the consumer project and commits it
  there, so the chunk files must exist in `repo/` before seeding, which
  is why 13.7 commits them beside their generator.
- Plain-noun filler drew no safety refusal in three runs; Greek-letter
  filler drew a `[bio]` refusal of the summariser in one (run 1). Use
  plain nouns.

## Work completed

Stage A in full: `docs/PLAN-4.md` (`ef1559c`), the E30 transcript
extraction and D72 (`6271187`), the pre-registration (`02b76b0`),
`docs/COMPACTION-DESIGN.md` section 13 (`6572147`), this handoff.

## Unresolved questions

- Whether 130,000 calibrates for S3 (five reads of six chunks) and S2
  the same as it did for E30's task. The dry pass (B.3) decides per
  shape; the run 1 finding that the trigger tracks the platform's own
  estimate, not the API count, means run 4's calibration is a starting
  point, not a given.
- Whether the `SessionStart` hook fires under `claude -p`. The pointer
  (13.4) is Stage C's; if C ships it before B.4 runs, the runs observe it
  for free (`.claude/session.json` mtime after a run); if not, Stage D.
- Whether arm C's appended `# Compact instructions` reach the worker's
  own context: `CLAUDE.md` is read at session start and every `claude -p`
  is a fresh session, so it should; not directly observable from the
  transcript. Record the assumption, not a claim.
- Whether five runs per cell separate anything. The pre-registration's
  "neither" rule sends overlapping cells to nine; expect S3 to need it.

Pending workers (spawned, outcome not recorded):
  (none)

## Exact next action

Confirm the session is on sonnet at high effort, read
`docs/COMPACTION-DESIGN.md` sections 13.6 to 13.8 and the pre-registration
in full, then start task B.1 with T12 (shape S1): `task.md` with the
constraint as its first sentence, `repo/make_chunks.py` and its five
committed chunk files, `constraint.json`, `grade.sh` printing the two
verdict lines, and `GRADER-TESTS.md` recording the five grader test cases
run before any live call. `python3 test/harness/check.py` green, one
commit, tick the box; then T13 and T14 the same way.

## Model and effort to set

`/model` sonnet, effort high.

## Cost projection

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
