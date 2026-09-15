# Action plan 3: context compaction as an efficiency mechanism

Adopted 2026-09-15 on branch `the-system`, after `docs/PLAN-2.md` closed.
Authored by Claude (Fable 5.1) at Jeb's direction; the analysis was
described and approved in conversation before this file existed. Status
of the plan as a whole: **in progress (since 2026-09-15)**.

Jeb's brief, in his words: integrate context compaction, as needed, to
maximise efficiency, into what has been built; analyse the problem deeply
before planning; do not implement until the plan is approved.

## The findings this plan rests on

Three findings, all from existing data and documentation read on
2026-09-15, none from a new run.

**Compaction never happens where the project has been measuring.** All
303 benchmark runs that recorded `claude -p` usage
(`test/results/*benchmark*.md`, 2026-09-07 to 2026-09-14) show a median
of 111,793 cumulative cache-read tokens per run at the floor and a maximum
of 172,669, summed across every turn. Peak context in any one turn is far
below that, so no worker or forwarder ever approached a 200K window, let
alone the native 1M window of Sonnet 5 and the Fable models. P29
(`compact_boundary` signals an undersized cell, `docs/PREMISES.md`) was
never untestable for lack of a probe; it was untestable at benchmark
scale, and E20 as designed (T7 or T11 at the floor) would find nothing.
Compaction demonstrably occurs in the long-lived orchestrator session: the
session that wrote this plan compacted, unprompted, earlier the same day.

**Compaction is not a worker-cost lever at benchmark scale.** Cost shares
across those runs, median at the floor: 34 percent cache write, 40 percent
cache read, 22 percent output (list-price multipliers, write 1.25, read
0.1, output 5 times input). The read share is the CLI's own prefix, about
43K tokens (E26), re-read on every turn. Compaction cannot remove it: the
system-prompt layer is reused and project context reloaded after
compaction (`docs/en/prompt-caching`). What compaction removes is the
conversation layer, which for a two-to-four-turn worker is a few thousand
tokens. A summarisation call would cost more than it saved on every run
on record.

**The platform exposes more than the charter assumed.** Verified against
documentation on 2026-09-15 (D68 has the page for each): the auto-compact
threshold is settable from 100K to 1M tokens and defaults to the model's
full window; a `SessionStart` hook with matcher `compact` has its stdout
injected into context after every compaction; a `# Compact instructions`
section in `CLAUDE.md` shapes the summary; the status line script
receives `context_window.used_percentage` after every API response and
per-subagent `tokenCount` samples in the tasks status line, with a
`refreshInterval` that keeps it running while a coordinator waits on
subagents; subagents auto-compact independently; `PreCompact` and
`PostCompact` exist but their stdout is not injected; nothing gives an
agent a tool to compact itself.

## The design decision this plan rests on

**Compaction in a worker is a horizon measurement, not a capability
signal.** A worker that compacted did not need a smarter model; it needed
a smaller task or a leaner handover, since every cell has the same window.
A compacted failure fed into the floor's posterior would teach the ladder
to climb for tasks that needed decomposition, which is money spent on the
wrong remedy. So compacted attempts are excluded from the capability
posterior and counted in a separate per-bucket overflow rate whose action
is "split or trim", never "escalate".

**State that must survive compaction lives on disk, never only in
context.** The ledger already does this for outcomes; the gap is in-flight
work between a spawn and its `--record`. Two-phase ledger writes close it.

**The handoff is the structured compaction; auto-compact is the
unstructured fallback.** The orchestrator learns its own context size at
zero marginal cost because it already runs `route.py` on every task, and a
task boundary is where a handoff belongs. Recovery after the fallback
fires is mechanical: a hook runs code that prints the pending work from
the ledger, never a model remembering.

**Settings first.** The threshold, the cache TTL, the hook and the status
line are documented platform knobs; they cost nothing per turn and
`preflight.py` can check them.

## Rules

The rules `docs/PLAN-2.md` ran under, carried forward unchanged:

1. One stage per session where the model class changes. Each stage names
   its model class and effort; the session states them and Jeb confirms
   before work starts.
2. Each task is its own commit on `the-system` with `python3
   test/harness/check.py` green first. Checkboxes and status lines in this
   file change in the same commit as the work.
3. A `claude -p` run is started by the session, after stating what will
   run and the projected cost; Jeb is asked first only above USD 100
   (D57). Stages A to D project **zero** live-run spend. Stage E is the
   one optional stage that spends, USD 2 to 5, and the plan is complete
   without it.
4. Every reopened decision or premise (P29, D63's trigger text, D64's
   ledger fields) gets its own entry in `docs/DECISIONS.md`. Nothing is
   reversed silently.
5. A stage boundary that changes the model or effort produces a handoff
   file under `handoffs/` (`src/LIFECYCLE.md`, "Handoffs").

## Stage A. Design, evidence, the spec

Status: **done (2026-09-15, see the A.7 commit)**
Model: fable, high. Judgement over the evidence; everything after this
stage is implementation from what this stage writes down.

Tasks:

- [x] A.1 This file, committed (`2bae02a`).
- [x] A.2 D68: P29 reopened on the existing-data finding; the four design
      decisions above with their evidence; the documentation pages each
      platform claim rests on; what each later stage may not change.
      Done 2026-09-15. Also records the economics as arithmetic (payback
      2.7 turns warm, 1.0 cold, model price cancelling) and the TTL
      finding that precedes it: an API-key orchestrator waiting on a
      Controller run turns into a cold cache.
- [x] A.3 `src/cost_table.json` gains a `context` section: the price
      multipliers and TTL buckets the docs state, the payback formula, the
      303-run cost shares and cache-read distribution with provenance and
      the aggregation script quoted. `check.py`'s COST-TABLE check requires
      provenance on it.
      Done 2026-09-15. Five subsections (multipliers, ttl, auto_compact,
      compaction_cost, measured), each with provenance; measured is
      written by the aggregation script quoted in its method, never by
      hand: 303 rows, floor shares 0.335 write, 0.404 read, 0.219 output
      with the write multiplier applied per row (31 rows carried one-hour
      writes), cache read median 111,763 and maximum 172,669 across all
      cells. COST-TABLE now requires the section and provenance on each
      subsection.
- [x] A.4 `docs/COMPACTION-DESIGN.md`: the spec Stages B to D execute. The
      ledger's `context` field and `ledger_version` 1; `route.py --spawn`,
      `--recover`, the `--explain` context line and its threshold; the
      status line script and the file it writes; the settings fragment and
      the hook; the compact-instructions text; `preflight.py`'s checks; the
      overflow posterior and advisory; every pass condition.
      Done 2026-09-15. Twelve sections; adds `tools/context_probe.py` (the
      status line script, both modes, one file), a PROBE-SELFTEST check,
      and the `--record --pending <id>` completion of a `--spawn` entry.
      Names the one unverified inference (a compaction seen as a large drop
      in a task's token samples) and routes it to E30.
- [x] A.5 `test/harness/empirical-checklist.md` gains E29 (no agent tool
      path to `/compact`) and E30 (E20 redesigned: a worker on a task that
      fills its window); `docs/PREMISES.md`'s P29 row points at D68.
      Done 2026-09-15. Also E31 (whether `autoCompactWindow` takes effect
      at project scope or only user scope, free, for Stage B's fragment)
      and a superseded note on E20 itself. P29's row and its entry in the
      ranked list both point at D68 and E30.
- [x] A.6 `handoffs/2026-09-15-plan3-stageB.md`, written with
      `tools/handoff.py new` and passing `check`.
      Done 2026-09-15. Carries the one sequencing decision Stage B needs
      that the design doc leaves implicit: `--spawn` writes a version-0
      entry until Stage C's schema accepts version 1.
- [x] A.7 Update this stage's status line and commit it.

Exit criteria: D68 present; the `context` section committed with
provenance; the design doc names every file Stages B to D touch and the
pass condition of every check; the handoff exists and names the model and
effort to switch to; harness green. All met 2026-09-15: D68 at `7f13e2d`;
`context` at `4e57b5f` with COST-TABLE asserting its provenance; the
design doc's section 11 lists every pass condition; the handoff at
`handoffs/2026-09-15-plan3-stageB.md` names sonnet, high; harness 27 of
27.

## Stage B. Settings, hooks, recovery

Status: **done (2026-09-15, see the B.6 commit)**
Model: sonnet, high. Implementation from a written spec.

Tasks:

- [x] B.1 `route.py --spawn` (a pending ledger entry at spawn time,
      completed by `--record`) and `--recover` (prints, for a
      `SessionStart(compact)` hook, the routing rule in one line, every
      pending entry, the newest handoff, and the re-read instruction).
      Done 2026-09-15. `--spawn` writes ledger_version 0 (Stage C's
      schema bump to version 1 is what lets it carry `context`, per this
      stage's own handoff); `--record --pending <id>` rewrites the entry
      in place via `complete_ledger_entry()` rather than appending a
      second record, raising `LedgerEntryNotFound` or
      `LedgerEntryNotPending` on a caller bug instead of silently
      appending a stray one. `--selftest` gained scenario h (spawn is
      excluded from the posterior while pending, `--recover` lists it,
      completing it removes it from both). Verified end to end in a
      scratch directory: spawn, recover-with-pending, record --pending,
      recover-after-complete, and the produced entry validates against
      `RoutingLedgerEntry.schema.json`.
- [x] B.2 `tools/context_probe.py`: the status line script; writes
      `.claude/context-usage.json` from the status line's JSON. Selftest
      on a recorded sample input.
      Done 2026-09-15. Also fixes a real gap section 2 had: `--tasks` is
      `subagentStatusLine`, whose stdout is `{"id", "content"}` override
      lines, not free text; printing a plain row per task would have
      either broken parsing or replaced every row's default rendering.
      Fixed to print nothing, observing every row without changing how
      any of them display; section 2 corrected to match. `peak_tokens` is
      the max of every numeric leaf found in `tokenCount` and
      `tokenSamples`, kept across refreshes, correct regardless of
      `tokenSamples`' undocumented shape (D69). The fixture is documentation-derived
      (the statusline page's own full-schema example for `main`;
      synthesised from its field list for `tasks`, since no literal
      example exists there), marked as such in its own `_comment`, for
      E30 to replace with a live capture. `--selftest`: 5 scenarios.
      New harness check PROBE-SELFTEST. Harness now 28 checks.
- [x] B.3 `route.py --explain` prints the context line from that file, or
      says the file is absent and why that is expected in a headless run.
      Done 2026-09-15. Also carries the steering thresholds this task and
      B.2 both need (`handoff_context_percent` 70, `context_stale_s` 600,
      `autocompact_window_tokens` 200000 in `routing_priors.json`, added
      to `generate_priors.py`), the ROUTE-PRIORS check that the first
      fires before the second on the 200K reference model, and D69: a
      real gap found while implementing this task, that `used_percentage`
      may be computed against the model's native window rather than a
      configured `autoCompactWindow`, which would make the threshold fire
      too late on Sonnet 5 or a Fable model with the fragment's own
      200,000 setting applied. Shipped as specified rather than guessed
      around; E32 checks which is true. `--selftest` gains scenario i
      (absent, under, over, and stale all print correctly); 9 of 9 pass.
      Also fixes a `%%` in an f-string in the ROUTE-PRIORS check added
      under A.3, which printed literally instead of one percent sign
      (only visible when that check fails; found while re-reading the
      code this task extends).
- [x] B.4 `dist/settings.fragment.json` and the `# Compact instructions`
      section in `src/ROUTING.md` (procedural, ships) and
      `src/CLAUDE.template.md`; `src/README.md` explains the fragment.
      Done 2026-09-15. Corrected against `docs/COMPACTION-DESIGN.md`
      section 8 while implementing: the compact instructions ship in
      `src/LIFECYCLE.md`'s "Handoffs" section (the appended install) and
      `src/CLAUDE.template.md` (the pointer install), not `src/ROUTING.md`
      as this line first said; the design doc is the authority Stage B
      works from and this file's own shorthand was imprecise.
      `src/settings.fragment.json` ships `promptCacheTtl`, both status
      line commands, and the `SessionStart(compact)` hook;
      `_user_settings.autoCompactWindow` is documentation only, since
      that key is user-scope. `src/README.md` gains a new numbered step
      in both install walkthroughs (merge the fragment, chaining rather
      than overwriting an existing statusLine/subagentStatusLine/hook)
      and updates the layout listing and the CLAUDE.md step for the
      compact instructions section. `build_dist.py` ships
      `context_probe.py` and `settings.fragment.json`.
- [x] B.5 `preflight.py`: the auto-compact window, the TTL against the
      Controller's wall clock, the hook, the status line command.
      Done 2026-09-15. Four checks: `check_autocompact_window` (env, then
      settings, 100,000 to 1,000,000, WARN unset); `check_cache_ttl`
      (WARN on 5m or unset only when the Controller is installed, since
      that is the one bundled thing whose wall clock reliably outlasts
      the default TTL); `check_compaction_hook` and `check_context_probe`
      (WARN if either half of `settings.fragment.json` is missing).
      Verified end to end: WARN on all four against this repository's own
      unmerged settings, PASS on all four in a scratch project with the
      fragment merged (`autoCompactWindow` via the environment variable,
      the rest via `.claude/settings.json`).
- [x] B.6 Update this stage's status line and commit it.

Exit criteria: harness green; `dist/` rebuilt and installed into
`orchestrator-scratch` with preflight clean; a `--spawn` followed by
`--record` produces one schema-valid entry. All three met
2026-09-15: harness 28/28; `orchestrator-scratch` reinstalled from a
clean (non-dirty) `dist/` build at `623b90d` with the fragment merged,
`preflight.py` reporting 0 failing (15 of 16 PASS, 1 expected WARN); a
`--spawn`/`--record --pending` round trip in that installed copy
produced one entry, confirmed schema-valid by `validate_records.py`.

## Stage C. Ledger and resolver

Status: **not started**
Model: sonnet, high.

Tasks:

- [x] C.1 `RoutingLedgerEntry.schema.json` accepts `ledger_version` 1 with
      the `context` field; fixture lines added, one valid and one broken.
      Done 2026-09-15. `context` is optional at the schema level (an
      object with peak_tokens/window/compactions/source, all four
      required within it once the object is present): `validate_records.py`
      is a hand-written validator that raises on any JSON Schema keyword
      outside its declared subset (its own module docstring), which does
      not include if/then/else, so "ledger_version 1 requires context"
      cannot be enforced in the schema itself. Enforced instead where
      route.py writes an entry, and the schema's own description says so.
      valid.jsonl gains led-003 (version 1, source statusline, one
      compaction, escalated and passed); broken.jsonl gains led-004
      (context.compactions: -1, rejected on the minimum constraint).
      BROKEN_LINES gains line 20. `validate_records.py` run directly on
      both files as well as through the harness.
- [x] C.2 `route.py --record` fills `context` from the probe's file (the
      last sample for that worker name) or from a transcript
      `compact_boundary` count as the fallback, and says which.
      Done 2026-09-15. `--spawn`, `--record --pending` and plain
      `--record` all now write `ledger_version` 1 with a `context` field
      (Stage B's sequencing note: Stage C is what upgrades both spawn and
      record together). `fill_context()` tries the probe's `tasks` key,
      then `_find_transcript_compactions()` (a best-effort search under a
      guessed `~/.claude/projects/<slug>` directory, matching E7's own
      "observed, not documented" caveat for that path), then `source:
      "none"`; never raises, and both `--record` forms print which source
      they used. `context_probe.py` gains `compactions` tracking in
      `merge_task_record()`: a drop past 50 percent of the immediately
      preceding raw `tokenCount` counts as one, since that component is
      the only one that ever sees two successive raw readings (route.py
      only reads the latest snapshot). Verified end to end in scratch
      directories: a simulated statusline sample fills `context` fully; a
      name the probe never saw falls through to `source: "none"`; the
      produced entries validate. Three new `--selftest` assertions for
      `fill_context` (no name, a match, no match); `context_probe.py`
      gains two more (a qualifying drop counted, a moderate one not).
- [x] C.3 `posterior()` excludes compacted attempts from the capability
      posterior; a per-bucket overflow posterior with a weak shipped prior;
      `plan()` emits a decomposition advisory when the overflow rate
      clears the named threshold. `generate_priors.py` and
      `routing_priors.json` gain the overflow priors and thresholds.
      Done 2026-09-15. `_is_compacted()` excludes only confirmed
      compactions (`context.compactions >= 1`) from the floor and rung
      counts; an entry with no observed status (`ledger_version` 0, or
      `source: "none"`) is treated exactly as it always was, absence
      being evidence of nothing either way. The overflow posterior draws
      from every entry in the bucket with a *known* status
      (`_known_compaction_count()`), regardless of `first_cell`, since a
      compaction is a property of the task, not of which cell handled it.
      Every bucket gets the same shipped prior (0.5, 9.5); a real
      arithmetic check while writing the selftest found that three
      compacted attempts give a mean of 0.269, under the 0.3 threshold
      section 6's own prose uses as its example: four are needed to
      cross it, and the selftest and this note use the number the
      arithmetic actually requires. `--explain` prints the advisory line
      when it fires; `first` never changes because of it.
      `generate_priors.py` gains the overflow prior (every bucket, same
      values, since D68 found no bucket has ever recorded a compaction to
      seed from) and the two `overflow_advisory_min_*` steering keys;
      ROUTE-PRIORS checks the prior's kind/provenance and that both
      steering keys are present. `--selftest` scenarios j (four compacted
      attempts: floor posterior exactly unchanged, overflow crosses 0.3,
      `first` unaffected) and k (three uncompacted floor failures: floor
      posterior falls as in scenario b, overflow stays near its prior,
      no advisory); 11 of 11 pass. Manually verified against a
      constructed ledger: the overflow line prints with the exact
      wording section 6 specifies.
- [x] C.4 Backtest: on the recorded data, which has no compactions, every
      existing check reproduces exactly and the overflow posterior stays
      at its prior in every bucket. Replay unchanged. `route.py
      --selftest` gains the compacted-failure and advisory scenarios.
      Done 2026-09-15. Every existing backtest check reproduces exactly
      (unchanged from D66's post-exclusion state); a new check per bucket
      confirms `overflow_mean` equals the shipped prior's mean exactly
      (0.05, `n=0` in all seven contained buckets checked), since no
      reconstructed entry carries a `context` field at all. `replay_routing.py`
      unchanged: 125 of 125 on the gating batch. `--selftest`'s j/k
      scenarios landed with C.3, per the task list's own note that they
      belong to this piece of work; recorded as
      `test/results/2026-09-15-backtest-ledger-2.md`.
- [ ] C.5 Update this stage's status line and commit it.

Exit criteria: harness green; backtest and replay pass; no fixture's
expected cell changed.

## Stage D. Handoff as compaction, propagation

Status: **not started**
Model: sonnet, medium.

Tasks:

- [ ] D.1 `handoff.py --pending-workers` from the ledger; the "Handoffs"
      section of `src/LIFECYCLE.md` gains the compaction paragraph.
- [ ] D.2 `docs/COST.md` gains the compaction economics; `src/README.md`
      explains the settings and why append beats pointer.
- [ ] D.3 D69: what this plan delivered, one line per brief item; this
      file marked complete (or complete pending Stage E).
- [ ] D.4 Final `check.py --record`.

Exit criteria: harness green; plan marked complete; D69 present.

## Stage E. One live probe (optional)

Status: **not started**
Model: sonnet, low.

- [ ] E.1 E29: whether any agent tool path reaches `/compact`. Free.
- [ ] E.2 E30: a worker on a task that fills its window; observe
      `compact_boundary`, the token samples, and whether the summary kept
      the handover's constraint. Projected USD 2 to 5.
- [ ] E.3 Record both in `docs/FINDINGS.md`; update P29.

Exit criteria: both findings recorded with the version checked.

## Projection

Live API spend: USD 0 for Stages A to D; USD 2 to 5 for Stage E. Session
cost, estimated since no telemetry exists for it: USD 30 to 60 equivalent
across four to five sessions. Time: four to seven hours of session time.
