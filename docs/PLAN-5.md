# Action plan 5: what Plan 4 left open

Adopted 2026-09-15 on branch `the-system`, after `docs/PLAN-4.md` closed.
Authored by Claude (Fable 5.1) at Jeb's direction; the analysis and the
plan were described and approved in conversation before this file
existed. Status of the plan as a whole: **in progress (since 2026-09-15)**.

Jeb's brief, in his words: make a plan to implement the four threads Plan
4 left open, as per the usual protocol, with cost projection and a model
and reasoning-effort staging sequence. The four threads, numbered as
they were offered:

1. The T12 fixture gives itself away: `make_chunks.py` ships inside the
   worker's own working directory and its docstring names the plan, the
   decision entries and the purpose of the data (`docs/FINDINGS.md`,
   Plan 4 Stage D). T13 and T14 carry the same generator with the same
   citations; the scratch consumer project's `CLAUDE.md` says the same
   thing in its own words, and the Stage D worker quoted both.
2. P29's real question is unanswered: Stage B measured whether a
   constraint survives a compaction, not whether a task that compacted
   would have done better decomposed. The overflow advisory this
   repository ships ("split the task or trim the handover") rests on
   the second claim, and nothing has measured it.
3. `detect_injection_refusal` is four verbatim phrases from two
   observed instances (D77). Stage D produced a refusal in different
   words that it does not match, inside the summary text itself rather
   than the turn after, which it does not look at.
4. `tokenSamples`' shape has never been observed: the status line does
   not fire headless (E30), and Stage D's worker finished in 38 seconds,
   before any subagent refresh populated a `tasks` entry.

## The design decisions this plan rests on

**Fix the instrument before measuring with it.** Thread 1 is a defect in
the fixtures Thread 2 must reuse, so it goes first, and Thread 2's
baseline is re-run against the repaired fixture rather than borrowed
from Stage B's 81 runs: reusing arm A across a fixture change would be
a confound with a price tag of about USD 7 to avoid, which is cheap.

**Measure the one shape that can decide.** Under a single compacting
worker at window 130,000, Stage B's combined failure rate (task not
done, or constraint violated) was 7 of 9 on T12, 4 of 9 on T13, 4 of 9
on T14 (`test/results/2026-09-15-compaction-bench.md`, D77). At the
sample sizes this repository can afford, a decomposed arm can only
separate from a baseline that fails often: against 7 of 9, twelve runs
per arm can reach non-overlapping intervals; against 4 of 9, even a
perfect decomposed arm cannot (0 of 12 has a Wilson upper bound of
0.24, above 4 of 9's lower bound of 0.19). So Thread 2 measures T12
alone, at twelve runs per arm, and says so in advance rather than
running T13 and T14 to a foregone "undecided". T13 and T14 stay
available for a later, larger sample if T12 decides.

**Decomposition is done by the harness, not the orchestrator.** The
question is whether splitting helps, not whether the orchestrator
splits well; conflating the two would leave a negative result
unattributable. The harness issues two forwarder calls per run with
fixed sub-handovers, carries the first worker's subtotal into the
second's handover, and restates the constraint verbatim in both, which
is what a competent orchestrator would do and what the decomposed arm
is meant to represent.

**Broaden the refusal detector against a labelled set, at zero spend.**
Stage B's 81 transcripts (21 phrase-matched positives, 27 arm-B
negatives that can contain no refusal) plus Stage D's one miss are a
calibration set that already exists on disk. A broadened detector is
accepted only if it recovers the Stage D case and stays at zero
matches on arm B; Thread 2's fresh transcripts then test it
prospectively. A model-graded classifier is held in reserve, not
built: the repository grades mechanically, and the labelled set is
large enough to calibrate a mechanical rule.

**One more interactive session, longer.** Thread 4 needs a worker that
outlives the subagent status line's refresh, so it gets a task built to
run for minutes, not seconds, and Jeb opens the tasks panel while it
runs in case the line only renders when shown. The same session
re-observes the `.claude/session.json` `event: "compact"` anomaly Stage
D recorded (`docs/FINDINGS.md`): on a fresh session with no prior
lineage the field should read `startup`, and whether it does is a free
second observation.

## Rules

The rules `docs/PLAN-4.md` ran under, carried forward unchanged:

1. One stage per session where the model class changes. Each stage names
   its model class and effort; the session states them and Jeb confirms
   before work starts.
2. Each task is its own commit on `the-system` with `python3
   test/harness/check.py` green first. Checkboxes and status lines in this
   file change in the same commit as the work.
3. A `claude -p` run is started by the session, after stating what will
   run and the projected cost; Jeb is asked first only above USD 100
   (D57). This plan projects **USD 22 to 32** of live spend, all in
   Stages C and D; Stages A, B and E project zero.
4. Every reopened decision or premise gets its own entry in
   `docs/DECISIONS.md`. Nothing is reversed silently.
5. A stage boundary that changes the model or effort produces a handoff
   file under `handoffs/` (`src/LIFECYCLE.md`, "Handoffs").
6. Development work delegated to a subagent within a stage is routed
   through `python3 tools/route.py --from-line "<line>" --project .
   --explain` first (`CLAUDE.md`, "Handoffs and routing, as standing
   practice").

## Stage A. Plan, pre-register, specify

Status: **done (2026-09-15)**
Model: fable, high. Judgement over the evidence. Zero live spend.

Tasks:

- [x] A.1 This file, committed.
- [x] A.2 `test/results/2026-09-15-decomposition-preregistration.md`: the
      one shape (T12), the two arms (A, a single worker at window 130,000,
      as Stage B; D, the same task split into two fixed sub-handovers,
      chunks 01 to 03 then 04 to 05, each restating the constraint, the
      second carrying the first's subtotal), twelve runs per arm, the
      outcome (combined: task done and constraint kept, since the
      question is about outcomes, unlike Stage B's constraint-specific
      rate), exclusion rules (an arm-A run with no boundary, or an arm-D
      run with any boundary in either transcript, is uncalibrated and
      re-run under Stage B's cap; a forwarder failure likewise), the
      decision rule (decomposition supported for T12 when arm D's
      failure rate is below arm A's with non-overlapping 95 percent
      Wilson intervals; not supported when arm D's failure rate is at or
      above arm A's; undecided otherwise, recorded as such; the
      pre-registration's own wording governs where this summary differs), predictions with
      numbers, and cost. Also pre-registers the broadened refusal
      detector's acceptance test (Thread 3) and the interactive session's
      two observations (Thread 4), so nothing in Stages B to D is decided
      after seeing its own data.
- [x] A.3 `docs/COMPACTION-DESIGN.md` gains section 14: the fixture
      hardening contract (no generator inside `repo/`; no citation of
      this repository's own documents in anything the worker can read;
      the scratch project's `CLAUDE.md` neutral during measurement), the
      harness's arm-D contract (two calls, subtotal carried, transcripts
      concatenated for the grader, no boundary permitted), the broadened
      detector's contract (structural: the summary text and the first
      assistant turn after each boundary; lexical: the widened phrase
      family; acceptance as A.2 fixes it), and Thread 4's long fixture.
- [x] A.4 `handoffs/2026-09-15-plan5-stageB.md`, written with
      `tools/handoff.py new --pending-workers`, passing `check`.
- [x] A.5 Update this stage's status line and commit it.
      Done 2026-09-15: A.1 `9c4c47d`, A.2 `069a1de`, A.3 `974c24b`, A.4
      and this line in one commit. Harness 30 of 30 throughout.

Exit criteria: pre-registration committed before any Stage B code
exists; design section present; handoff names sonnet, high; harness green.

## Stage B. Repair the fixtures, broaden the detector, build arm D

Status: **not started**
Model: sonnet, high. Zero live spend.

Tasks:

- [ ] B.1 Thread 1. Move `make_chunks.py` out of `repo/` in T12, T13 and
      T14 to the fixture directory beside `grade.sh` (the chunk files
      stay committed, so `fixture_fingerprint` still covers the data);
      rewrite each docstring to describe what the script does without
      naming this repository's plans, decisions or purpose; `GRADER-TESTS.md`
      in each re-run against the moved layout. Note in `test/results/`
      that Stage B's checkpoint identity no longer matches these fixtures
      (it is closed; `compaction_bench.py` refuses a mismatch by design).
      Replace the scratch project's `CLAUDE.md` sentence naming
      "empirical checks" with a neutral description of a scratch project,
      recorded as a dogfooding note per `CLAUDE.md`'s Dogfooding rule.
- [ ] B.2 Thread 3. `detect_injection_refusal` broadened per section 14:
      scan the `isCompactSummary` message's own text and the first
      assistant turn after each boundary, not the whole file; widen the
      phrase family (candidates: "prompt injection", "not a legitimate",
      "abandon the task", "fake conversation summary", "fabricated
      conversation summary", "derail", "disregard", "not going to
      comply", "injected"), excluding bare words D77 found in boilerplate.
      Calibrate against the 82 labelled transcripts: must match Stage D's
      transcript, must match all 21 of D77's positives, must match none
      of arm B's 27. Report the confusion table in `test/results/`.
      `--selftest` scenario extended; harness green.
- [ ] B.3 Thread 2's instrument. `compaction_bench.py` gains arm D:
      `task-part1.md` and `task-part2.md` in T12 (with a `{subtotal}`
      placeholder in part 2), two `run_cell` calls per run, `partial.txt`
      read between them, both transcripts located and concatenated for
      `BENCH_TRANSCRIPT`, `uncalibrated` when either transcript carries a
      boundary, the per-run record carrying both workers' costs summed.
      `--selftest` scenario against synthetic two-part records; harness
      check count updated.
- [ ] B.4 `dist/` rebuilt (B.1 touches nothing shipped, but the harness
      gate runs anyway); update this stage's status line and commit.

Exit criteria: harness green; detector confusion table committed with
zero arm-B matches and the Stage D case recovered; arm D runs end to
end in `--dry-run`; fixtures carry no self-reference a worker can read.

## Stage C. Measure decomposition on T12

Status: **not started**
Model: sonnet, high. Live spend about USD 20 to 28: arm A twelve runs at
about USD 0.55 (Stage B's T12 mean), about USD 7; arm D twelve runs at
two calls each, about USD 0.45 per call on a shorter task, about USD 11;
re-runs under the exclusion cap up to about USD 6. Under the USD 100
line; the session states the projection and starts the runs.

Tasks:

- [ ] C.1 `compaction_bench.py --tasks T12 --arms A,D --runs 12 --fresh
      --record`, in the background; result file committed.
- [ ] C.2 The broadened detector applied prospectively to every Stage C
      transcript and its rate reported beside `stub-summary`, as D77's
      version was; any refusal it misses that a manual read of arm A's
      summaries finds is recorded, not folded in after the fact.
- [ ] C.3 The pre-registered rule applied at twelve; a decision entry
      with the table; P29's row in `docs/PREMISES.md` moved to closed,
      pressured or still open exactly as the rule says, and the overflow
      advisory's wording in `src/ROUTING.md` section 6 and
      `docs/COMPACTION-DESIGN.md` section 6 revised only if the rule
      supports or refutes it.
- [ ] C.4 Update this stage's status line and commit it.

Exit criteria: result file committed; every arm-A run confirmed
compacted and every arm-D run confirmed not, or excluded per the rule;
the decision applied, not re-argued.

## Stage D. One interactive session, longer, Jeb's

Status: **not started**
Model: sonnet, high for the checklist extension; the session itself is
Jeb's. Live spend USD 2 to 4.

Tasks:

- [ ] D.1 `test/harness/interactive_checklist.py` gains `--task T15`, a
      new fixture built for duration: twelve chunk files, read all, write
      a count, no compaction sought (window left unset), no generator in
      `repo/`; the printed steps tell Jeb to open the tasks panel while
      the worker runs, and to start from a fresh session, not a resumed
      one. `--check` prints `tasks` verbatim as before and adds
      `session.json`'s `event` against the expected `startup`.
- [ ] D.2 Jeb's session, the steps D.1 prints.
- [ ] D.3 `docs/FINDINGS.md`: `tokenSamples`' shape if observed, or the
      fact that a multi-minute worker with the panel open still did not
      populate it, either of which closes the question one way or the
      other; the `event` observation beside Stage D's anomaly. If
      `tasks` was observed, `test/fixtures/system/statusline-sample.json`'s
      `tasks` section is replaced with the capture and
      `context_probe.py --selftest` re-pointed at it.
- [ ] D.4 Update this stage's status line and commit it.

Exit criteria: `tokenSamples` observed or its non-observation explained
by something other than duration; `event` on a fresh session recorded.

## Stage E. Close-out

Status: **not started**
Model: sonnet, medium. Zero live spend.

Tasks:

- [ ] E.1 `docs/COST.md`, `src/README.md` and `docs/COMPACTION-DESIGN.md`
      updated for what Stage C decided about the overflow advisory;
      `CLAUDE.md`'s open-questions list amended for P29 and
      `tokenSamples`.
- [ ] E.2 Final `check.py --record`; this file marked complete.

Exit criteria: harness green; plan marked complete.

## Projection

Live API spend: USD 22 to 32 (Stage C about USD 20 to 28, Stage D USD 2
to 4). Session cost, estimated since no telemetry exists for it: USD 25
to 45 equivalent across four to five sessions. Time: four to six hours
of session time, of which about forty minutes is Stage C's runs in the
background.
