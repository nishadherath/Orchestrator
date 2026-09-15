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

Status: **not started**
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
- [ ] B.2 `tools/context_probe.py`: the status line script; writes
      `.claude/context-usage.json` from the status line's JSON. Selftest
      on a recorded sample input.
- [ ] B.3 `route.py --explain` prints the context line from that file, or
      says the file is absent and why that is expected in a headless run.
- [ ] B.4 `dist/settings.fragment.json` and the `# Compact instructions`
      section in `src/ROUTING.md` (procedural, ships) and
      `src/CLAUDE.template.md`; `src/README.md` explains the fragment.
- [ ] B.5 `preflight.py`: the auto-compact window, the TTL against the
      Controller's wall clock, the hook, the status line command.
- [ ] B.6 Update this stage's status line and commit it.

Exit criteria: harness green; `dist/` rebuilt and installed into
`orchestrator-scratch` with preflight clean; a `--spawn` followed by
`--record` produces one schema-valid entry.

## Stage C. Ledger and resolver

Status: **not started**
Model: sonnet, high.

Tasks:

- [ ] C.1 `RoutingLedgerEntry.schema.json` accepts `ledger_version` 1 with
      the `context` field; fixture lines added, one valid and one broken.
- [ ] C.2 `route.py --record` fills `context` from the probe's file (the
      last sample for that worker name) or from a transcript
      `compact_boundary` count as the fallback, and says which.
- [ ] C.3 `posterior()` excludes compacted attempts from the capability
      posterior; a per-bucket overflow posterior with a weak shipped prior;
      `plan()` emits a decomposition advisory when the overflow rate
      clears the named threshold. `generate_priors.py` and
      `routing_priors.json` gain the overflow priors and thresholds.
- [ ] C.4 Backtest: on the recorded data, which has no compactions, every
      existing check reproduces exactly and the overflow posterior stays
      at its prior in every bucket. Replay unchanged. `route.py
      --selftest` gains the compacted-failure and advisory scenarios.
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
