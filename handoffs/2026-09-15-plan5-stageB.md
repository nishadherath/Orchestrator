# Handoff: plan5-stageB

<!-- handoff.py new --slug plan5-stageB --reason model-change --from-model fable --from-effort high --to-model sonnet --to-effort high --project . --pending-workers -->
Written 2026-09-15 by fable, high. Reason: model-change.

## Goal

Execute `docs/PLAN-5.md` Stage B: repair the three compaction fixtures
(T12, T13, T14) so nothing a worker can read names this repository,
broaden `detect_injection_refusal` against the 82 labelled transcripts
already on disk, and give `compaction_bench.py` an arm D that runs a
task as two sub-handovers. Zero live spend; every deliverable is code,
fixtures and a calibration table, all specified in
`docs/COMPACTION-DESIGN.md` section 14.

## Decisions already made

The measurement shape is fixed: T12 only, arms A and D, twelve runs per
arm, combined pass/fail as the outcome, the decision rule and its
sensitivity (`test/results/2026-09-15-decomposition-preregistration.md`).
Stage B changes none of it; a correction found before Stage C's first
live run goes at the top of that file with its date, nothing else. The
detector's acceptance test is fixed there too: match Stage D's
transcript, match all 21 D77 positives, match none of arm B's 27. The
harness does the splitting, not an orchestrator (section 14.2). Stage
B's closed checkpoint in `orchestrator-scratch` will stop matching once
the generators move; that is by design, not a defect (D76 removed only
`runs` from the identity, not the fixture hashes).

## Files and links that matter

`docs/PLAN-5.md` (Stage B tasks B.1 to B.4); `docs/COMPACTION-DESIGN.md`
section 14 (14.1 fixtures, 14.2 arm D, 14.3 detector, 14.5 pass
conditions including FIXTURE-CLEAN); `test/results/2026-09-15-decomposition-preregistration.md`;
`test/harness/compaction_bench.py` (`detect_injection_refusal`,
`INJECTION_REFUSAL_PHRASES`, `run_one`, `render_arm`, `checkpoint_identity`,
`ARM_SETS_WINDOW`, `ARM_APPENDS_INSTRUCTIONS`); `test/fixtures/benchmark/T1{2,3,4}/`
(`repo/make_chunks.py` to move, `GRADER-TESTS.md` to re-run);
`test/fixtures/benchmark/README.md` (D16, D17, D30, the prior leak
kinds); `test/harness/check.py` (`check_compact_bench_selftest` as the
pattern for FIXTURE-CLEAN); D73 through D77 in `docs/DECISIONS.md`;
`docs/FINDINGS.md`, "Plan 4 Stage D" (the leak as observed).

## Verified facts

All three generators cite this repository (`sed -n 1,8p
test/fixtures/benchmark/T1{2,3,4}/repo/make_chunks.py`: each names
`docs/PLAN-4.md`, E30 or D72). Stage B's combined failure rates from the
checkpoint, `outcome` counts per cell: arm A T12 7 of 9, T13 4 of 9, T14
4 of 9; arm B 0 of 9 everywhere. Wilson at n=12 from
`claudep.wilson_interval`: 0/12 [0.000, 0.243], 1/12 [0.015, 0.354], 2/12
[0.047, 0.448], 7/12 [0.320, 0.807], 8/12 [0.391, 0.862], 9/12 [0.468,
0.911]. The 82 calibration transcripts are under
`~/.claude/projects/C--Users-Bob-Desktop-Code-Claude-orchestrator-scratch/`,
`agentType == worker-sonnet-low`, mtime after 1789461937.4 for the 81
(D77's own cutoff), plus session `9175cc55-b344-47a9-9adb-4772be3e6415`'s
`subagents/agent-aa88b8dba96f6d856.jsonl` for Stage D's. Harness: 30 of
30 at `974c24b`.

## Work completed

`docs/PLAN-5.md` (`9c4c47d`); the pre-registration (`069a1de`);
`docs/COMPACTION-DESIGN.md` section 14 (`974c24b`); this handoff (the
A.4 commit). Plan 4 closed at `8eca348` with every stage done.

## Unresolved questions

Whether the widened phrase family in 14.3 survives calibration intact:
any phrase matching an arm-B transcript is removed, and the final list
is whatever survives, not the list as written. Whether the 33 unlabelled
arm-A and arm-C transcripts hold refusals the broadened detector newly
finds; each such match needs a hand read before it counts. Whether
`GRADER-TESTS.md`'s synthetic cases still pass after the generator
moves (expected yes, since grader paths are unchanged; the rule requires
the check). Whether `orchestrator-scratch/CLAUDE.md`'s replacement
sentence should keep the `ORCHESTRATOR.md` pointer line: keep it
(section 14.1 point 3 says so).

Pending workers (spawned, outcome not recorded):
  (none)

## Exact next action

`git mv test/fixtures/benchmark/T12/repo/make_chunks.py
test/fixtures/benchmark/T12/make_chunks.py`, rewrite its docstring to
describe only what it writes, repeat for T13 and T14, then run
`python3 test/harness/check.py` and confirm the fixture fingerprints
changed (`python3 -c "import sys; sys.path.insert(0,'tools');
sys.path.insert(0,'test/harness'); import benchmark;
print(benchmark.fixture_fingerprint(benchmark.load_task('T12')))"`
against the value in the closed checkpoint's meta line). That is B.1's
first half; B.1's second half is the `GRADER-TESTS.md` re-run and the
scratch `CLAUDE.md` note.

## Model and effort to set

`/model` sonnet, effort high.

## Cost projection

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
