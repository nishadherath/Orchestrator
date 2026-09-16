# Action plan 6: the audit's findings, fixed in ranked order

Adopted 2026-09-16 on branch `v1.0-beta`, after `docs/AUDIT-2026-09-16.md`
closed. Authored by Claude (Fable 5.1) at Jeb's direction; the audit and
the three decisions this plan rests on were put to Jeb and answered
before this file existed (D81). Status of the plan as a whole: **in
progress (since 2026-09-16)**.

Jeb's brief: fix everything the audit found, all 63 findings, in the
audit's own ranked order, consumer bundle first. Zero live spend.

## The decisions this plan rests on

Three findings qualified a recorded decision and were put to Jeb before
any task was written (D81). Each answer is the reading the original
decision intended, and each is now fixed:

1. **A4.** A floor failure recorded with `--outcome fail` and no
   `--escalation` counts as a floor failure in the bucket's posterior.
   D64's "learn from outcomes" meant every recorded outcome; the
   escalation-only rule in `posterior()` was an implementation shortcut.
2. **B1.** `route.py --spawn` ships in `ORCHESTRATOR.md` section 3 and
   section 2's record command becomes `--record --pending <id>`,
   completing Plan 3's two-phase ledger (D68) rather than removing the
   pending list from the recovery hook.
3. **A22.** `score_routing.py`'s two-stage mode becomes the default and
   the `-rubric-only` suffix check goes, since the shipped bundle has
   been rubric-only since D64; `build_dist.py --rubric-only`,
   `dist-rubric-only/` and `route.resolve_two_axis` go with it (D40
   rejected the two-axis design; nothing else calls it). Prose mode stays
   behind a flag so the recorded batches can still be replayed.

Everything else in the audit is a fix to code or prose that no decision
entry governs, and is done as the audit's "Fix" sentence says.

## Rules

The rules `docs/PLAN-5.md` ran under, carried forward unchanged:

1. One stage per session where the model class changes. Each stage names
   its model class and effort; the session states them and Jeb confirms
   before work starts.
2. Each task is its own commit on `v1.0-beta` with `python3
   test/harness/check.py` green first. Checkboxes and status lines in this
   file change in the same commit as the work.
3. A `claude -p` run is started by the session, after stating what will
   run and the projected cost; Jeb is asked first only above USD 100
   (D57). This plan projects **zero** live spend: every fix is verified
   by the harness, a selftest, or a scratch-directory run of the tool.
4. Every reopened decision gets its own entry in `docs/DECISIONS.md`.
   Nothing is reversed silently.
5. A stage boundary that changes the model or effort produces a handoff
   file under `handoffs/` (`src/LIFECYCLE.md`, "Handoffs").
6. Development work delegated to a subagent within a stage is routed
   through `python3 tools/route.py --from-line "<line>" --project .
   --explain` first (`CLAUDE.md`, "Handoffs and routing").
7. New: a task that closes an audit finding names it (`A4`, `B1`, ...)
   in its commit message, so `docs/AUDIT-2026-09-16.md` can be read
   against `git log` to see what is closed.

## Stage A. Plan, decisions, handoff

Status: **done (2026-09-16)**
Model: fable, high. Judgement over the audit; zero live spend.

Tasks:

- [x] A.1 This file, committed.
- [x] A.2 D81: the plan's adoption, the three decisions above with Jeb's
      answers, and the scope (all 63).
- [x] A.3 `handoffs/2026-09-16-plan6-stageB.md`, written with
      `tools/handoff.py new`, passing `check`.
- [x] A.4 Update this stage's status line and commit it.

Exit criteria: D81 present; the handoff names sonnet, high; harness green.

## Stage B. The consumer bundle

Status: **done (2026-09-16)**
Model: sonnet, high. Implementation from the audit's own fix sentences,
in its rank order. Load `python.sonnet.md`. Zero live spend; the dogfood
install in B.10 copies files and runs `preflight.py`, nothing paid.

Tasks:

- [x] B.1 C1: delete `USAGE_PROJECT.md`; `README.md`'s Map table drops
      its row.
- [x] B.2 B6, B7, D1: `src/LIFECYCLE.md` "Reporting state" and
      `src/commands/workers.md` step 1 reworded to what an agent can do
      (`ListAgents`, the transcript directory, completion notifications),
      with `/tasks` kept as the human cross-check, per
      `docs/FINDINGS.md`'s E19 entry; `src/README.md` "Verifying it
      works" step 1 replaced by `preflight.py`'s bundle row;
      `LIFECYCLE.md`'s opening states that the Agent tool and the Task
      tool are one tool.
- [x] B.3 A26, D2, A31 (A31 added here; omitted from Stage A's task
      list against the audit, found by a finding-ID diff before this
      task started): `preflight.py` FAILs when `python3` is not on
      PATH, naming the fix; `settings.fragment.json` gains
      `permissions.allow: ["Bash(python3 *)"]` and the README's merge
      step says so; `ROUTING.md` section 2's fallback names all three
      JSON files; `preflight.py`'s docstring says "seven things", not
      "six".
- [x] B.4 B1: `ROUTING.md` section 3 gains the `--spawn` step after the
      Agent call; section 2's record command becomes `--record --pending
      <id>`; `LIFECYCLE.md`'s Handoffs paragraph says the pending list
      is what `--spawn` feeds. New harness check ROUTE-MODES: every
      `route.py` flag named in `settings.fragment.json`'s commands is
      named in `src/ROUTING.md` or `src/LIFECYCLE.md`.
- [x] B.5 A4: `posterior()` counts `final_outcome == "fail"` at the
      floor whether or not an escalation was recorded; docstring says
      so; `--selftest` gains scenario n (three unescalated floor fails
      lower the floor mean); `backtest_ledger.py`'s pass conditions
      re-run and, if any bucket's `first` moves, that is a result to
      record in D82, not a reason to revert.
- [x] B.6 A13, A14, A15, A16: `system_controller.py --record` writes
      `runs/<id>/RECORD.md`, never `test/results/`; `--budget-usd`
      defaults to 4.0 and `ROUTING.md` section 4's command passes it;
      a `RuntimeError` from a role closes as a gap report with
      `REPORT.md` the way `BudgetExhausted` does; the three `assert`
      guards become explicit raises; the unreachable `return` goes.
      `--selftest` gains the RuntimeError-closes-as-gap scenario.
- [x] B.7 A27, A32, A28, A29, A30, A10, B14, B18: `settings.fragment.json`
      carries `autoCompactWindow: 200000` as a real key (E31) and drops
      `_user_settings`; its comment marks `refreshInterval` and the TTL
      keys as documented, not observed; `ROUTING.md` section 4 states
      one Controller cost with its `cost_table.json` provenance and
      states the "say the estimate first" rule inline; every citation of
      a file not shipped in `dist/` is inside a rationale span or
      replaced by a URL to the source repository; section 2 describes
      `--explain`'s real output order; `strip_rationale` trims
      whitespace-only lines; `docs/COMPACTION-DESIGN.md` section 7
      gains a one-line E31 note.
- [x] B.8 A7, A12, A5, A6, A8, A9 (A11 closed early in B.5: bumping
      the selftest scenario count to 14 meant fixing both the count
      route.py prints and the count check.py's ROUTE-SELFTEST
      docstring states, in the same edit, or a fresh instance of A11's
      own drift would have been introduced immediately): `route.py` catches
      `AssessmentLineError` in `main()` (message to stderr, exit 2);
      `context_probe.py` writes `context-main.json` and
      `context-tasks.json` and `route.py` reads both, ending the race;
      `ledger_cell_means` moves into `route.py` and `plan()` applies it,
      `handoff.py` imports it; `complete_ledger_entry` writes via a temp
      file and `os.replace`; the module docstring describes the two-rule
      table and D44; the selftest count in `check.py`'s docstring
      matches. `resolve_two_axis` moved to D.1 (A9's own fix sentence
      groups it with retiring the two-axis mode as a whole, which is
      `score_routing.py`'s change; deleting it here and fixing
      `score_routing.py`'s `--axes 2` call site in a later stage would
      leave a dangling reference to a deleted function across a stage
      boundary for no reason, since nothing runs it in this plan).
- [x] B.9 A17, A18, A19, A20: `claudep.call_claude` wraps
      `JSONDecodeError` and `TimeoutExpired` as `RuntimeError` with the
      stdout tail and elapsed time, and callers' duplicate handling is
      trimmed; `Checkpoint._append` writes LF; `handoff.py new` defaults
      its output under `<project>/handoffs/`; `generate_workers.py`'s
      marker and unrouted-cell description are corrected and the
      fifteen definitions regenerated.
- [x] B.10 `dist/` rebuilt; installed into `orchestrator-scratch` per
      `src/README.md`'s existing-project steps; `preflight.py` there 0
      failing; the install logged in `test/results/` per the dogfooding
      rule; this stage's status line updated and committed.

Exit criteria: harness green with ROUTE-MODES counted; `dist/` stamped
clean and reinstalled; every finding named above closed by a commit
that names it.

## Stage C. The repository's own documents

Status: **not started**
Model: sonnet, medium. Prose edits from the audit's fix sentences.

Tasks:

- [x] C.1 B9, C6, A2 (wording), C2: `CLAUDE.md`'s opening paragraph
      describes the floor-plus-ledger design; Layout regenerated from
      the tree; a "Paid runs" paragraph under Working practice states
      D57's rule; the invariants sentence admits the empirical class
      for invariant 7; the two persona-section open questions merge into
      one that cites P39; the escalation-rate question names
      `route.py --record --escalation`; the persona line names
      `bash.<class>.md` for grader work.
- [x] C.2 B2: `docs/COST.md` dated per section; the Controller paragraph
      rewritten to D63's state with the cost from `cost_table.json`; the
      bundle version, the `route.py` and `handoff.py` sizes, the
      `B0_BRIEF.md` row, the "section 1.1" citation and the "no session
      after Stage 13" sentence corrected.
- [x] C.3 B3, B4, B5, B15, B13, B17: `docs/PREMISES.md` gains a
      "last checked" column and a section naming the rows D44, D64 and
      D80 changed, with P05, P10, P13, P14 and the "eleven of eighteen"
      paragraph corrected; `docs/FRONTIERS.md` gains a banner naming
      D44/D45 and `routing_priors.json` as its successor;
      `test/fixtures/README.md`'s Coverage and schema row and
      `test/fixtures/benchmark/README.md`'s task list rewritten;
      `src/routing_table.json`'s comment names the real sync risk;
      `docs/ROUTING-2-DESIGN.md` and `docs/CLASSIFIER-DESIGN.md` gain
      one-sentence "as built" notes on the four unbuilt claims;
      `docs/PLAN.md`'s cost summary gains a one-line D57 note.
- [ ] C.4 B8, B10, B11, B12, B16, A33: `docs/FINDINGS.md`'s E3/E4
      label, duplicated heading and two moved paths ("now at");
      `docs/PLAN-4.md`'s Stage B total (42.04) and ceiling (26 to 42);
      one sentence beside each "9 of 9" or "12 of 12" citation of T10
      saying which count it is; an erratum entry for D54's broken
      heading; `test/harness/empirical-checklist.md` marks E4, E31 and
      E32 done with dates, corrects E8's Settles column, and lists E24
      to E28 with a pointer to FINDINGS.
- [ ] C.5 `README.md`: the sentences that say "the audit found" for A4,
      B1 and A26 rewritten to their fixed state; Map table updated.
      Update this stage's status line and commit it.

Exit criteria: harness green (PROSE covers every file touched); no
number for one measurement stated two ways across the documents.

## Stage D. Harness, tools, artefacts

Status: **not started**
Model: sonnet, high. Load `python.sonnet.md`.

Tasks:

- [ ] D.1 A22, A21, A9 (moved from B.8), C3: `score_routing.py` defaults
      to `--classifier two-stage`, accepts a plain `dist/` stamp, keeps
      prose mode behind the flag, drops the F03 note; `build_dist.py`
      loses `--rubric-only` and its docstring's stale sentence;
      `dist-rubric-only/` deleted locally and its `.gitignore` line
      removed; `route.py`'s `resolve_two_axis`, its two-axis CLI path in
      `main()`, and `score_routing.py`'s `--axes 2` call site and CLI
      option are all deleted together, since none of them has a caller
      once the two-axis mode retires.
- [ ] D.2 C7, A3, A2, B8, A1, A11: new DIST check (`planned_files()`
      with the committed stamp against `dist/`); `PROSE_GLOBS` gains
      `README.md`; INV7 reads `docs/FINDINGS.md` for a dated E4 row and
      PASSes on it, SKIPs otherwise; `build_dist.py --dry-run` prints
      `unchanged`/`changed`/`new` per file; scenario counts in
      `check.py`'s docstrings match the scripts.
- [ ] D.3 C5: `test/harness/results_index.py` writes
      `test/results/INDEX.md` (date, kind, bundle, size, citing D
      entries); `check.py --record` runs it; the first index committed.
- [ ] D.4 C9, A23, A24, A25, A34: `fixture_fingerprint` skips
      `__pycache__` and `*.pyc`; `role_probe.py` and
      `cost_rollup_check.py` call `claudep.call_claude`, import the cells,
      and use `unique_path`; `extract_e30.py` takes `--repo` and `--base`;
      `compaction_bench.py` drops arm C and the `(cost1 or 0) + 0`
      expression; `generate_priors.py` derives `generated_on` from the
      date it runs.
- [ ] D.5 `dist/` rebuilt if any shipped file changed; final
      `check.py --record`; D82: what the plan delivered against the
      audit, one line per stage, and any finding left open with the
      reason; this file marked complete. Update this stage's status
      line and commit it.

Exit criteria: harness green with DIST and ROUTE-MODES counted and
INV7 no longer a permanent skip; `docs/AUDIT-2026-09-16.md`'s 63
findings each closed by a named commit or listed in D82 as left open.

## Projection

Live API spend: USD 0 (rule 3). Session cost, estimated since no
telemetry exists for it: USD 30 to 60 equivalent across four to six
sessions. Time: five to eight hours of session time.
