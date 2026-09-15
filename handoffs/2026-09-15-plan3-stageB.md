# Handoff: plan3-stageB

<!-- handoff.py new --slug plan3-stageB --reason model-change --to-model sonnet --to-effort high --from-model fable --from-effort high --project . -->
Written 2026-09-15 by fable, high. Reason: model-change.

## Goal

Execute Stage B of `docs/PLAN-3.md`: settings, hooks, recovery. Give the
orchestrator a way to know its own context usage (`tools/context_probe.py`
writing `.claude/context-usage.json` from the status line), a durable
roster of in-flight workers (`route.py --spawn` and `--record --pending`),
a mechanical recovery after a platform compaction (`route.py --recover`
behind a `SessionStart(compact)` hook), the settings fragment and compact
instructions that ship in `dist/`, and `preflight.py` checks for all of
it. Zero live `claude -p` calls.

## Decisions already made

- D68 (`docs/DECISIONS.md`): compaction in a worker is a horizon signal,
  never a capability one; compacted attempts never enter the capability
  posterior; the overflow action is an advisory, never a rung; recovery
  is code, not a compaction instruction asking the model to remember;
  the auto-compact window is set below the model's limit; no stage
  before E makes a live call. None of these may change in Stage B
  without a new decision entry.
- Every file, flag, field, threshold, text and pass condition is fixed
  in `docs/COMPACTION-DESIGN.md` sections 1 to 9 and 11. Implement to
  it; where it is silent, choose the boring option and note the choice
  in the commit message.
- Stage B does not touch `posterior()`, the schema, or the priors; those
  are Stage C (sections 3 and 6). `--spawn` therefore writes a
  version-1 entry only once Stage C's schema accepts it: in Stage B,
  `--spawn` writes a version-0 entry with `notes` beginning `pending:`
  and `--record --pending` completes it, and Stage C adds the `context`
  field to both. Say so in B.1's commit message.
- Existing `route.py` functions and CLI flags keep their behaviour;
  TABLE-DATA, ROUTE-TOTAL, REPLAY and BACKTEST call them.

## Files and links that matter

- `docs/COMPACTION-DESIGN.md` (the spec), `docs/PLAN-3.md` (Stage B's
  task list and exit criteria), D68 in `docs/DECISIONS.md`.
- `src/cost_table.json`, `context` section: the documented settings
  names, TTL buckets, window bounds, and the measured shares the
  `--explain` line and `preflight.py` messages cite.
- `tools/route.py` (extend), `tools/handoff.py` (untouched until Stage
  D), `src/preflight.py` (four new checks, section 9), `src/ROUTING.md`
  section 2 (the `--spawn` step after the Agent call; the advisory
  handling is Stage C), `src/LIFECYCLE.md` and `src/CLAUDE.template.md`
  (the compact instructions text, section 8), `src/README.md` (the
  fragment's merge instructions), `tools/build_dist.py` (ships
  `context_probe.py` and `settings.fragment.json`).
- `test/harness/check.py` (add PROBE-SELFTEST), `test/fixtures/system/`
  (the status line sample the probe's selftest reads).
- `test/harness/empirical-checklist.md` E29, E30, E31.

## Verified facts

- Harness green at `05ab8c8`, 27 checks; `python3 tools/route.py
  --selftest` 7 scenarios; `python3 tools/handoff.py --selftest` 4.
- Documentation read 2026-09-15 (pages in D68's table): the status line
  settings key is `statusLine` with `type`, `command` and an optional
  `refreshInterval` in seconds; the per-task one is `subagentStatusLine`
  with per-task `model`, `effort`, `contextWindowSize`, `tokenCount`,
  `tokenSamples` (v2.1.205 or later); the main script runs at session
  start, after each assistant message, after `/compact` finishes, and on
  the refresh timer; `context_window.current_usage` is `null` before the
  first API call and again after `/compact` until the next one.
- `SessionStart` hooks with matcher `compact` have stdout added to
  context; `PreCompact` and `PostCompact` do not.
- `autoCompactWindow` is documented as a user-settings key; the
  environment variable `CLAUDE_CODE_AUTO_COMPACT_WINDOW` takes precedence
  and accepts a plain token count only.
- `tools/claudep.py` already captures `usage` from every `claude -p`
  JSON result (line 126), and 303 benchmark rows on disk carry it; the
  floor's cost shares are 0.335 write, 0.404 read, 0.219 output
  (`cost_table.json`, `context.measured`).
- No benchmark transcript can carry a `compact_boundary` entry (D68):
  the harness has no historical compaction to test against, which is
  why section 11's backtest condition is parity, not movement.

## Work completed

Stage A in full: `docs/PLAN-3.md` (`2bae02a`), D68 (`7f13e2d`),
`src/cost_table.json` `context` section with COST-TABLE extended
(`4e57b5f`), `docs/COMPACTION-DESIGN.md` (`883f0c4`), E29 to E31 and
P29 reclassified (`05ab8c8`), this handoff.

## Unresolved questions

- E31: whether `autoCompactWindow` in project-scope settings takes
  effect. Until checked, the fragment carries it under `_user_settings`
  as section 7 says and `preflight.py` reads all three scopes plus the
  environment. Do not assume either way.
- The shape of `tokenSamples` is undocumented. For PROBE-SELFTEST, build
  the fixture from the documented example input on the status line page
  (`code.claude.com/docs/en/statusline`, the JSON under "context window
  fields" and the subagent rows section), mark the fixture
  documentation-derived in its own `_comment`, and let E30 replace it
  with a live capture. Record `tokenSamples` verbatim; take
  `peak_tokens` from `tokenCount` and any numeric sample.
- Whether a hook command of `python3 tools/route.py --recover --project .`
  runs under the shell Claude Code uses for hooks on Windows (Git Bash
  here). `preflight.py` checks the setting's presence only; the first
  live compaction in `orchestrator-scratch` is the observation, and it
  belongs in `docs/FINDINGS.md` when it happens.
- Headless sessions have no status line, so `.claude/context-usage.json`
  is absent there. Section 2 says every reader treats absence as
  unknown and none fails; keep it that way.

## Exact next action

Confirm the session is on sonnet at high effort, read
`docs/COMPACTION-DESIGN.md` sections 1, 2, 4 and 5 in full, then start
task B.1: `route.py --spawn`, `--record --pending <id>` and `--recover`
with the exact output of section 4, `python3 tools/route.py --selftest`
extended for the round trip, `python3 test/harness/check.py` green, one
commit, tick the box.

## Model and effort to set

`/model` sonnet, effort high. No worker cell: this is a session handoff.

## Cost projection

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

Live API spend: USD 0.00 (no `claude -p` calls in Stage B; the probe's
selftest and every check run on recorded or documentation-derived data).
Session cost for the stage beyond the computed session-load line above,
estimated since no telemetry exists for it: USD 10 to 25 equivalent.

## Time projection

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.

Stage B as scoped: 3 to 5 hours of session time (six tasks; one new
script with a selftest, a `route.py` extension of a few hundred lines,
four preflight checks, the fragment and its README text, a `dist/`
rebuild and reinstall into `orchestrator-scratch`; no waiting on runs).
