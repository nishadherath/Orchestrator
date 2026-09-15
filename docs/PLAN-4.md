# Action plan 4: calibrate the compaction mechanism against observed behaviour

Adopted 2026-09-15 on branch `the-system`, after `docs/PLAN-3.md` closed.
Authored by Claude (Fable 5.1) at Jeb's direction; the analysis and the
plan were described and approved in conversation before this file
existed. Status of the plan as a whole: **in progress (since 2026-09-15)**.

Jeb's brief, in his words: resolve what Plan 3 left unanswered (the
status line never fired headless, `tokenSamples`' shape, E31, E32), and
resolve the caveat that the constraint-survives-compaction result was one
run of one task shape; decide which option to take and why; describe how
the results improve the system.

## What Plan 3 left, and what the transcripts already answer

Plan 3 shipped a compaction mechanism designed against documentation and
two hundred recorded benchmark runs, none of which had ever compacted.
Stage E then produced four live runs, and their transcripts, read after
the fact (`test/results/2026-09-15-e30-transcripts.md`, D72), settle more
than the runs were designed to:

- Every assistant message in a subagent transcript carries `usage`, the
  model, and the effort. The transcript is a strictly richer source of a
  worker's context history than the status line, and it works headless.
  Plan 3's section 5 precedence (status line first) is upside down.
- The compaction summary is in the transcript (`isCompactSummary`), in the
  platform's own nine-section format, and it preserved the E30 constraint
  under three headings. The compact instructions Plan 3 shipped were not in
  that `CLAUDE.md` (pointer install), so their effect is untested.
- The 50 percent drop heuristic in `context_probe.py` is falsified: the
  observed ratios after compaction were 0.57 and 0.87, because the fixed
  prefix never shrinks. Every real compaction observed would have been
  missed.
- The trigger is the window minus a reserve of about 34,000 tokens on
  plain-text content (bracketed by four compactions across two windows and
  matched by the documentation's 967,000-of-1M figure), and the reserve is
  content-conditional: the platform evaluates it on its own estimate, and
  run 1's Greek-letter content triggered ten thousand tokens later on the
  same window. The floor after a structured compaction is about 59,000
  regardless of window, so headroom is window minus about 93,000, and a
  task refilling that within three turns is aborted outright by the
  platform. The shipped 200,000 is safe below about 36,000 tokens per turn
  and not above it; the platform's own 100,000 minimum thrashes on ordinary
  file reads.
- A refused summariser produces a stub summary that keeps nothing (run 1:
  1,124 and 1,482 characters, no headings, no constraint) and the platform
  carries on. Plan 3 never named this failure mode; the pre-registration
  scores it.

## The design decisions this plan rests on

**The fixes do not wait for the answers.** Transcript-first `fill_context`,
the effective-window `min()` in `context_probe.py`, retiring drop
detection, a hook-written session pointer, and a thrash-floor warning are
each correct under every outcome of E31 and E32 (D72 argues each one), so
they ship before the observation that would confirm them. The shipped
default may be silently dead on the models this orchestrator runs on
(D69's pessimistic branch); waiting is the expensive choice.

**One run of one shape is not evidence; a controlled measurement is.**
The claim "a compaction summary preserves a handover constraint" is
measured the way this repository measures everything else: three task
shapes whose constraints are load-bearing (the unconstrained path is the
natural one), a control arm without compaction so a violation is
attributable, mechanical grading from artefacts and transcripts, and a
pre-registered decision rule at the repository's two grades (five runs to
steer, nine to report). The pre-registration is
`test/results/2026-09-15-compaction-preregistration.md` and nothing in it
changes after the first run.

**The interactive session is an acceptance test, not a probe.** It runs
last, after the fixes, so the one session that can observe the status
line, `tokenSamples`, E31 and E32 also verifies the shipped fixes live.
Reading the installed binary (feasible: the identifiers are present in
`claude.exe`) is held in reserve, since it is the weakest evidence class
this repository recognises and everything it could give, the session
gives as observation.

## Rules

The rules `docs/PLAN-3.md` ran under, carried forward with one change:

1. One stage per session where the model class changes. Each stage names
   its model class and effort; the session states them and Jeb confirms
   before work starts.
2. Each task is its own commit on `the-system` with `python3
   test/harness/check.py` green first. Checkboxes and status lines in this
   file change in the same commit as the work.
3. A `claude -p` run is started by the session, after stating what will
   run and the projected cost; Jeb is asked first only above USD 100
   (D57). This plan projects **USD 26 to 42** of live spend, all in
   Stages B and D; Stages A, C and E project zero.
4. Every reopened decision or premise gets its own entry in
   `docs/DECISIONS.md`. Nothing is reversed silently.
5. A stage boundary that changes the model or effort produces a handoff
   file under `handoffs/` (`src/LIFECYCLE.md`, "Handoffs").

## Stage A. Mine what exists, pre-register, specify

Status: **done (2026-09-15, see the A.6 commit)**
Model: fable, high. Judgement over the evidence.

Tasks:

- [x] A.1 This file, committed.
- [x] A.2 `test/results/2026-09-15-e30-transcripts.md`, generated by a
      script from the four transcripts (per-turn input totals, every
      `compact_boundary` with `preTokens`, the first request after each,
      the summary's length and headings and whether it names the
      constraint, tool-use names per turn), and D72: the reserve interval,
      the floor, the thrash inequality, the precedence reversal, drop
      detection falsified, the summary finding, and why each Stage C fix
      is a dominant strategy.
      Done 2026-09-15. The extraction corrected D71 on a point of fact:
      run 1's worker did start, compacted twice, and both summaries were
      stubs (1,124 and 1,482 characters, no headings, no constraint)
      because the [bio] refusal hit the summariser, not the task. That
      is a failure mode Plan 3 never named and the pre-registration now
      scores. The trigger reserve is content-conditional: plain-noun
      compactions bracket [33,622, 35,147), run 1's two do not overlap
      each other. Script committed as `test/harness/extract_e30.py`.
- [x] A.3 `test/results/2026-09-15-compaction-preregistration.md`: the
      three shapes, the three arms, sample sizes, grading, exclusion and
      calibration rules, decision rules, predictions with numbers, cost.
      Done 2026-09-15. Six exclusion and calibration rules (the sixth,
      `stub-summary`, added from A.2's run 1 finding before any run),
      four decision rules, predictions per shape and arm as counts out
      of five, USD 27 to 40.
- [x] A.4 `docs/COMPACTION-DESIGN.md` gains a "Revisions from Plan 4"
      section: the spec Stages B to E execute (the harness script's
      contract, the fixture and grader contracts, the transcript-first
      precedence, the `min()`, the session pointer, the preflight rule,
      every pass condition).
      Done 2026-09-15. Section 13, nine subsections; earlier sections
      left in place as the record of the pre-evidence design, with 13
      governing where they disagree.
- [x] A.5 `handoffs/2026-09-15-plan4-stageB.md`, written with
      `tools/handoff.py new --pending-workers` and passing `check`.
      Done 2026-09-15. The first handoff written with `--pending-workers`
      (Plan 3 Stage D); the ledger had no pending entry, so the listing
      reads "(none)". Also corrects this file's own opening bullet, which
      still called the reserve fixed after A.2 found it content-conditional.
- [x] A.6 Update this stage's status line and commit it.

Exit criteria: D72 present and citing the generated evidence file; the
pre-registration fixes every rule before any run; the design revisions
name every file Stages B to E touch and every pass condition; the handoff
names sonnet, high; harness green. All met 2026-09-15: D72 at `6271187`
cites `test/results/2026-09-15-e30-transcripts.md`; the pre-registration
at `02b76b0` with its sixth rule added before any run; section 13 at
`6572147`; the handoff names sonnet, high; harness 28 of 28.

## Stage B. Build the measurement, run it

Status: **done (2026-09-15)**
Model: sonnet, high. Live spend: the dry pass about USD 2, the 45 runs
about USD 25, confirmation up to about USD 10 (the pre-registration's
own "USD 27 to 40" total for this stage). Actual: dry pass USD 1.70
(D73), 45 runs USD 22.42 (D75), confirmation USD 17.92 (D77, larger
than projected since Arm C was extended to nine runs alongside Arm A
and B rather than left at five, D75's own resolution of a gap the
pre-registration left open). Stage B total USD 42.04, narrowly above
the pre-registration's own USD 40 ceiling for this stage (by about USD
2, entirely the Arm C extension) but inside this file's rule 3, the
whole plan's USD 26 to 42 ceiling, and under the USD 100 line
regardless.

Tasks:

- [x] B.1 Fixtures `test/fixtures/benchmark/T12`, `T13`, `T14` (shapes S1,
      S2, S3 of the pre-registration): `task.md`, `repo/` with committed
      chunk files and the generator that made them, `grade.sh` printing
      `CONSTRAINT: kept|violated` and `TASK: done|not-done` and exiting 0
      only on both. Each grader tested, per the fixture README's own
      rule, against two correct phrasings, two plausible wrong answers
      and one adversarial one, before any live run.
      Done 2026-09-15 across three commits (`e71357d`, `85c6508`,
      and this one): T12 (S1, tool prohibition, 6 grader tests), T13
      (S2, detail fidelity, 5 grader tests, no transcript check since
      the constraint is the final artefact), T14 (S3, negative scope, 6
      grader tests, including one where a letter-perfect artefact hides
      a transcript-level violation, which is why S3 needs the transcript
      check and S2 does not). Every grader matched on its first run;
      `constraint.json` per fixture names what each shape's transcript
      check (if any) looks for, read by `compaction_bench.py` in B.2.
- [x] B.2 `test/harness/compaction_bench.py`: arms, `--autocompact-window`,
      `--compact-instructions on|off`, fixed cell, N runs, the transcript
      located per run and its compaction count, `preTokens`, peak and
      post-compaction totals recorded, `BENCH_TRANSCRIPT` exported to the
      grader; checkpointed per (task, arm, cell); `--record`. Reuses
      `benchmark.py`'s `seed_task`, `reset_task`, `run_cell`, `grade`,
      `load_task`, `fixture_fingerprint` and `claudep.Checkpoint`.
      Done 2026-09-15. CLI matches section 13.6 exactly (`--arms`,
      `--runs`, `--window`, not the two flag names this task line first
      sketched, which section 13.6 superseded before any code existed).
      `run_one` wraps `benchmark.run_cell`/`reset_task`/`seed_task`
      directly; `grade_with_env` is a sibling of `benchmark.grade` (which
      takes no `env` parameter) carrying `BENCH_TRANSCRIPT` and
      `BENCH_BOUNDARY_INDEX` to the grader. `with_instructions_appended`
      verified byte-identical restore of a real `CLAUDE.md`
      (`orchestrator-scratch`'s own). Found and fixed a real gap while
      writing it: a run whose transcript cannot be located would have
      graded `CONSTRAINT` as "kept" by default rather than being excluded,
      exactly the "absence is not evidence" mistake D72 warns against;
      added a `no_transcript` outcome, excluded from scoring. `--selftest`
      (3 scenarios) against a new committed fixture,
      `test/fixtures/system/transcript-sample.jsonl` (a redacted,
      restructured copy of E30 run 4's shape). New harness check
      COMPACT-BENCH-SELFTEST; 29 checks. `seed_task`/`reset_task`/
      `fixture_fingerprint` verified directly against all three fixtures
      in `orchestrator-scratch`, no live spend.
- [x] B.3 Dry pass: one run per shape in arm A. The compaction must land
      before the constrained action (the boundary's index precedes the
      first constrained tool call in the transcript); adjust the window
      per shape if not, and record the calibration. All three landed
      before the constrained action (D73); `calibration:
      boundary_before_constrained` for T12/T13, `T14` likewise. Fixture
      defect (a trailing-newline phantom line) found and fixed, D73.
      A second, deeper defect found after that: `bash` on this machine
      resolves to a WSL launcher stub that drops every environment
      variable `compaction_bench.py` sets for `grade.sh`, invalidating
      two of the three shapes' dry-pass verdicts (T12's silently
      defaulted "kept" was actually a violation once graded for real,
      T13 errored outright); root-caused to Windows' executable-search
      order, fixed by resolving a real Git Bash explicitly
      (`benchmark.resolve_bash()`), and the existing transcripts
      re-graded at no further live cost rather than re-run, D74. 29/29
      harness checks pass with the fix in place.
- [x] B.4 The 45 runs, in the background, `--record`; the result file per
      arm with Wilson intervals per shape.
      Done 2026-09-15, USD 22.42. `test/results/2026-09-15-compaction-bench.md`
      committed. Found and fixed the same day: `render_arm`'s reported
      violation rate was computed from `outcome` (task-and-constraint
      combined) instead of `constraint_status` alone, inflating two
      cells (arm A T14, arm C T14) from a true 0 of 5 to a reported
      3 of 5 and 2 of 5, and one (arm C T12) from a true 2 of 5 to a
      reported 4 of 5, D75. Corrected numbers, all three shapes retained
      (arm B under 0.30 on every shape): T12 arm A 4/5, arm C 2/5; T13
      arm A 1/5, arm C 3/5; T14 arm A 0/5, arm C 0/5, arm B 0/5
      throughout. Every shape lands on "Neither" at steering grade
      (Wilson's own upper bound at n=5 does not clear 0.30 even at 0 of
      5), so B.5 confirms all three, and arm C is extended alongside arm
      A and B so the compact-instructions rule is evaluated at the same
      grade it depends on (D75's resolution of a gap the pre-registration
      left open).
- [x] B.5 Confirmation to nine runs in every cell (all three shapes, all
      three arms, D75); the decision on each shape and on the compact
      instructions, as the pre-registration fixes it, applied to the
      nine-run data.
      Done 2026-09-15, USD 17.92 (Stage B total USD 40.34, inside the
      plan's own USD 26 to 40 projection at the top of the range). Also
      implemented and backfilled pre-registration rule 7
      (injection-refusal, never actually automated before this, only
      identified by manual reading in the dry pass), finding 21 of 81
      runs across the whole measurement, D77. Decisions at n=9: T14
      supported, steering grade (arm A 0/9, Wilson upper bound 0.2992,
      at or below 0.30); T12 and T13 remain undecided even at
      confirmation grade (neither shape's arm A lower bound exceeds arm
      B's upper bound, T12 by the narrowest margin this measurement
      produced, 0.2666 against 0.2992); compact instructions clear the
      non-overlap bar on no shape and are removed in Stage E. Zero
      `aborted` runs across all 81; the thrash floor is unexercised, not
      confirmed. `test/results/2026-09-15-compaction-bench.md` holds the
      final nine-run data for every cell.
- [x] B.6 Update this stage's status line and commit it.

Exit criteria: revised from "three result files" (a planning-stage
assumption; the actual instrument writes one consolidated file covering
every arm, which is what is committed) to: the result file committed
with every cell at its final grade; every arm-A and arm-C run confirmed
compacted from its transcript or excluded per the rule; the
pre-registered decisions applied, not re-argued. Met 2026-09-15.

## Stage C. The dominant-strategy fixes

Status: **done (2026-09-15)**
Model: sonnet, high. Zero live spend. May run in the same session as
Stage B, while B.4's runs are in the background; nothing here depends on
their result.

Tasks:

- [x] C.1 `route.py`: `fill_context` transcript-first (`peak_tokens` from
      the largest of `preTokens` and per-turn input totals, `window` from
      the model id, `compactions` from the boundary count), status line
      second, `source: "none"` last. `--record` prints which applied.
      Done 2026-09-15. `_find_transcript_compactions` replaced by
      `_transcript_context_stats` (compactions, peak_tokens, window) and
      `_resolve_transcript` (the session-pointer-scoped-else-every-session
      search); `src/cost_table.json` gained `context.model_windows`
      keying the three routed model ids to their documented 1,000,000-token
      windows. `--record`'s existing `print(f"context: {context['source']}")`
      already surfaced the source field; no change needed there.
- [x] C.2 `context_probe.py`: `used_percentage` recomputed against
      `min(context_window_size, resolved autoCompactWindow)`, resolution
      in the documented precedence (environment, then settings scopes);
      drop detection removed; `compactions` in the tasks key dropped in
      favour of the transcript. The JSON contract's `main.used_percentage`
      documented as already effective-window relative, under D69's own
      reversal clause.
      Done 2026-09-15. `_resolve_autocompact_window` added (a cited
      duplicate of `preflight.py`'s equivalent scan, since this file
      ships standalone in `dist/`); `main_record` gained `project`,
      `platform_used_percentage`, `effective_window` and
      `effective_window_source`; `merge_task_record`'s drop-detection
      block and its `compactions` key removed entirely. Selftest rewritten:
      scenario (a) confirms today's behaviour is preserved when nothing is
      configured, (c)/(c2)'s compaction assertions removed, new scenario
      (f) proves the 200,000-against-1,000,000 recomputation from section
      13.8. 6 scenarios (was 5).
- [x] C.3 `settings.fragment.json`: a `SessionStart` hook (matchers
      `startup`, `resume`, `compact`) running `route.py --session-pointer`,
      which writes `session_id` and `transcript_path` from the hook's own
      input to `.claude/session.json`.
      Done 2026-09-15. `route.py --session-pointer` reads the hook's stdin
      JSON and writes `.claude/session.json` (`session_id`,
      `transcript_path`, `cwd`, `event` from the hook's own `source`
      field, `written_at`), atomic temp-file-then-rename; never raises on
      malformed stdin, prints one line to stderr and exits 1 instead.
      `settings.fragment.json`'s `compact` matcher now carries two hooks
      (`--recover`, then `--session-pointer`); `startup` and `resume` each
      carry `--session-pointer` alone. Section 13.3's `--explain` change
      (the sentence above) was missed by this stage's first pass, caught
      and closed the same day: `context_explain_line` now falls back to
      `_orchestrator_transcript_stats` through `.claude/session.json`
      when `.claude/context-usage.json` is absent entirely, computing the
      last assistant message's total against the effective window
      (`_resolve_autocompact_window`, a third cited duplicate of the same
      small scan, capping the model's native window from
      `context.model_windows`). The fallback fires only on an absent
      file, matching this bullet's own "when the status line file is
      absent" wording exactly, not on a stale or not-yet-populated one,
      which would be a different, untested change. `--selftest` gained
      scenario m proving both the fallback and its absence-only scope.
- [x] C.4 `preflight.py`: a thrash-floor check, `WARN` when the resolved
      window minus 93,000 is below three times a footprint the consumer
      states (`--per-turn-tokens`, default 8,000, the E30 read size).
      Done 2026-09-15. `_resolved_autocompact_window` factored out of
      `check_autocompact_window` and shared with the new
      `check_autocompact_headroom`, which assumes the documented
      ~967,000-token default only when nothing is configured and never
      returns FAIL. Manually verified against section 13.8's two cases:
      PASS at a resolved 200,000 (headroom 107,000 against a 24,000
      threshold), WARN at 100,000 (headroom 7,000).
- [x] C.5 Selftests for each; ROUTE-SELFTEST, PROBE-SELFTEST, BACKTEST,
      REPLAY green; `dist/` rebuilt and installed into
      `orchestrator-scratch`, preflight clean.
      Done 2026-09-15. `route.py --selftest` gained scenario l (transcript-first
      `fill_context` plus the session-pointer scoping round trip, proven
      against a decoy transcript in a different, newer session) and,
      after closing the 13.3 gap above, scenario m (the `--explain`
      transcript fallback and its absence-only scope): 13 scenarios (was
      11). `check.py`'s ROUTE-SELFTEST and PROBE-SELFTEST docstrings
      updated to match; neither hardcoded a scenario count as an
      assertion. Full harness: 29 of 29 checks pass (INV7 skipped, as
      always, needing a live session), including COST-TABLE against the
      new `context.model_windows` block and COMPACT-BENCH-SELFTEST
      unaffected. `dist/` rebuilt and reinstalled into `orchestrator-scratch`
      per `src/README.md`'s existing-project steps; `preflight.py` run
      there shows 0 failing of 17 checks, the new "auto-compact headroom"
      row PASSing (no window configured there, so it falls back to the
      assumed default, headroom 874,000 against a 24,000 threshold), and
      the two WARNs (auto-compact window unset; organisation effort
      limits) both pre-existing and unrelated to this stage.
- [x] C.6 Update this stage's status line and commit it.

Exit criteria: harness green; the four fixes each carry a selftest that
would fail on the pre-fix behaviour; `dist/` reinstalled. All met
2026-09-15, including section 13.3's `--explain` change, caught as a gap
against this file's own C.3 text and closed the same day rather than
left open.

## Stage D. One interactive session, Jeb's

Status: **not started**
Model: sonnet, high for the checklist script; the session itself is
Jeb's, on whatever the desktop app is set to. Live spend USD 0.5 to 2.

Tasks:

- [x] D.1 `test/harness/interactive_checklist.py`: prepares
      `orchestrator-scratch` (fragment merged, instructions appended,
      `autoCompactWindow` set at project scope only, `.claude/context-usage.json`
      removed) and afterwards reads back everything the session should
      have produced: whether `context-usage.json` exists and when it was
      last written, `main.context_window_size` against the configured
      window (E32), the raw `tasks` entry with `tokenSamples` verbatim,
      and `.claude/session.json`. Prints a FINDINGS-ready table.
      Done 2026-09-15. `--prepare` also removes `.claude/session.json`
      (not named explicitly by this bullet, added so `--check` can tell
      a freshly-written pointer from a stale one) and seeds T12 so D.2
      has a fixture ready to point at, reusing the same task Stage B
      measured. `--check` takes `--autocompact-readback` as an argument
      since no file records what `/autocompact` prints on screen; D.2
      supplies it from what was observed. `--selftest`, 4 scenarios,
      against a throwaway git repository; new harness check
      INTERACTIVE-CHECKLIST-SELFTEST, 30 checks. Run for real against
      `orchestrator-scratch`: `autoCompactWindow` set to 130000, T12
      seeded, `.claude/session.json` removed (`.claude/context-usage.json`
      was already absent). Zero live spend.
- [ ] D.2 Jeb's session, about five commands the checklist prints: open a
      session in `orchestrator-scratch`, run `/autocompact` and read the
      value back (E31), spawn one worker on T12 at window 130,000, wait,
      exit. The session's own compaction, if any, exercises the
      `SessionStart(compact)` hook live.
- [ ] D.3 Record every row in `docs/FINDINGS.md`; replace
      `test/fixtures/system/statusline-sample.json` with the live capture;
      close E31, E32 and D69 with what was observed.
- [ ] D.4 Update this stage's status line and commit it.

Exit criteria: E31 and E32 answered as observation; the fixture is a live
capture; Stage C's fixes seen working in a session.

## Stage E. Close-out

Status: **not started**
Model: sonnet, medium. Zero live spend.

Tasks:

- [ ] E.1 D73: the measured preservation rates and intervals per shape
      replacing "one run, one shape"; the compact instructions kept or
      dropped per the pre-registered rule; if a shape lost, `src/ROUTING.md`
      section 3 gains the file-borne constraint mitigation (the platform
      re-reads recently modified files after compaction).
- [ ] E.2 `docs/COST.md`, `src/README.md`, `docs/COMPACTION-DESIGN.md`
      updated for what shipped; `docs/PREMISES.md` P29 closed or narrowed.
- [ ] E.3 Final `check.py --record`; this file marked complete.

Exit criteria: harness green; plan marked complete; D73 present.

## Projection

Live API spend: USD 26 to 42 (Stage B about USD 25 to 40, Stage D USD
0.5 to 2). Session cost, estimated since no telemetry exists for it: USD
30 to 60 equivalent across four to five sessions. Time: five to eight
hours of session time, of which about ninety minutes is Stage B's runs in
the background.
