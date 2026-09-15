# Compaction design: the spec Stages B to D of `docs/PLAN-3.md` execute

Written 2026-09-15 (Stage A.4, D68). Every format, flag, file, threshold
and pass condition a later stage needs is fixed here. Where this document
is silent, the implementing stage chooses the boring option and says so in
the commit message. Nothing here is measured against a live compaction;
D68 records why none exists on disk and Stage E is the one place one is
produced.

## 1. What is observed, and by whom

Three contexts exist, and compaction means something different in each.

| Context | How it grows | Who can see its size | Compaction |
| :--- | :--- | :--- | :--- |
| The orchestrator's session | one turn per task: assessment, `route.py` output, spawn, worker summary | the status line script, after every API response (`context_window.used_percentage`) | the platform's, at `autoCompactWindow`; the handoff, at a task boundary, before that |
| A worker | its own tool loop, in its own window | the subagent status line, per task (`tokenCount`, `tokenSamples`, `contextWindowSize`) | the platform's, independently; recorded, never induced |
| A Controller role call | one fresh `claude -p` process per role, handed an input slice | `claudep.call_claude`'s captured `usage` | none needed: the slice and the digest are the compaction (SYSTEM.md section 6) |

The orchestrator cannot read its own context size and cannot compact
itself (D68, E29). Everything below routes that information through
files on disk that `route.py` reads, because `route.py` is already run on
every task.

## 2. The context probe: `tools/context_probe.py`

One script, two modes, ships in `dist/tools/`.

`--main` is the `statusLine` command. It reads the status line's JSON
from stdin, writes the `main` key of `.claude/context-usage.json`, and
prints a one-line status for the terminal (`[model] ctx 64% · cache warm`),
since `statusLine`'s stdout is the rendered row verbatim.
`--tasks` is the `subagentStatusLine` command. It reads the tasks JSON
from stdin, writes the `tasks` key, and prints nothing: `subagentStatusLine`'s
stdout is not free text but `{"id": ..., "content": ...}` override lines,
one per row the caller wants to *replace*, and omitting a task's `id`
keeps its default rendering (`docs/en/statusline`, "Subagent status
lines"). Emitting no lines observes every row without changing how any
of them display, which is this probe's whole purpose. Each mode rewrites
only its own key, read-modify-write, written to a temporary file and
renamed, so the two never clobber each other.

The file:

```
{
  "written_at": "<ISO 8601>",
  "session_id": "<from the input>",
  "main": {
    "sampled_at": "<ISO 8601>",
    "model": "<model.display_name>",
    "used_percentage": <number or null>,
    "total_input_tokens": <int>,
    "context_window_size": <int>,
    "current_usage": <object or null>,
    "prompt_cache": <object or null>
  },
  "tasks": {
    "<task name>": {
      "sampled_at": "<ISO 8601>",
      "id": "...", "type": "...", "status": "...",
      "model": "...", "effort": "...",
      "contextWindowSize": <int or null>,
      "tokenCount": <int or null>,
      "tokenSamples": <verbatim>,
      "peak_tokens": <int or null>
    }
  }
}
```

`peak_tokens` is the largest of `tokenCount` and any numeric value found
in `tokenSamples`, kept across refreshes for the same task name until the
task's status is no longer running. The shape of `tokenSamples` is not
documented beyond its name; it is recorded verbatim and Stage B's
selftest runs on a sample input captured from a live status line, stored
under `test/fixtures/system/statusline-sample.json`, the first observation
of that shape (`docs/FINDINGS.md`).

A headless session has no status line, so the file is absent or stale.
Every reader below treats absence as "unknown" and says so; none fails.

## 3. The ledger: `RoutingLedgerEntry` at `ledger_version` 1

`ledger_version` becomes an enum, `0` or `1`. A version-1 entry carries
one new required field and every version-0 field unchanged:

```
"context": {
  "peak_tokens": <int or null>,
  "window": <int or null>,
  "compactions": <int or null>,
  "source": "statusline" | "transcript" | "none"
}
```

`compactions` is the count of `compact_boundary` entries in the worker's
transcript when `source` is `transcript`, or the count of times a task's
`peak_tokens` fell by more than half between samples when `source` is
`statusline` (a compaction replaces the history with a shorter summary,
so a large drop is its signature; whether the tasks status line samples
often enough to see it is unverified, and `transcript` is the fallback).
`null` with `source: none` means unobserved, never zero.

Fixtures: `test/fixtures/system/valid.jsonl` gains one version-1 line
with `source: statusline`; `broken.jsonl` gains one with `compactions: -1`.
`validate_records.py` and the SCHEMA check need no change beyond the
schema itself.

## 4. `route.py`: spawn, record, recover, explain

**`--spawn`.** Same arguments as `--record` minus the outcome ones, plus
`--worker-name`. Appends a version-1 entry with `final_outcome: unknown`,
`escalations: []`, `cost_usd: 0`, `wall_clock_s: 0`, `context.source:
none`, and `notes` beginning `pending:` followed by the worker name.
Prints the entry id. Section 2 of `src/ROUTING.md` runs it immediately
after the Agent call.

**`--record --pending <id>`.** Completes that entry in place rather than
appending: rewrites the line with the outcome fields, cost, wall clock,
escalations, and `context` filled per section 5. A `--record` without
`--pending` behaves as today and appends. A pending entry is never
counted by `posterior()`: `final_outcome: unknown` already excludes it.

**`--recover`.** Prints, for the `SessionStart(compact)` hook, exactly:

```
Context was compacted. Routing rule: assess in one line, resolve with
python3 tools/route.py --from-line "<line>" --project . --explain, spawn
what it names (ORCHESTRATOR.md section 2).
Pending workers (spawned, outcome not recorded):
  led-042  worker-sonnet-low  open/medium/contained  spawned 14:02:11  name: refactor-parser
  (none)
Newest handoff: handoffs/2026-09-15-plan3-stageB.md (or: none)
If ORCHESTRATOR.md is not part of CLAUDE.md, read it now before the next task.
```

Zero model calls; every line comes from the ledger and the `handoffs/`
listing. Exit 0 always, including when the ledger is absent.

**`--explain` gains one line**, after `projection:`:

```
context: 64% of 200,000 (statusline, 12 s ago); handoff above 70%: not yet
context: unknown (no .claude/context-usage.json; expected in a headless session)
context: 73% of 200,000 (statusline, 5 s ago); handoff above 70%: WRITE A HANDOFF BEFORE THIS TASK
```

The threshold is `steering.handoff_context_percent` in
`routing_priors.json`, shipped at 70, and it must be below
`steering.autocompact_window_tokens` as a fraction of the window or
ROUTE-PRIORS fails. Stale is older than `steering.context_stale_s`
(shipped 600); a stale file prints `stale` in place of the age and the
threshold comparison is still made.

## 5. Filling `context` on record

Precedence, and `source` records which applied:

1. `statusline`: `.claude/context-usage.json` has a `tasks` entry whose
   name matches `--worker-name` (or the pending entry's name). `peak_tokens`,
   `window`, `compactions` from section 2.
2. `transcript`: `~/.claude/projects/<project slug>/<session>/subagents/`
   has an `agent-*.meta.json` whose `name` matches; count
   `compact_boundary` in the sibling `.jsonl`. The path is observed, not
   documented (`src/LIFECYCLE.md`, E7); `peak_tokens` stays null since
   the transcript's per-turn usage shape is unverified.
3. `none`.

`--record` prints which source it used.

## 6. Posterior, overflow, advisory

`posterior()` (D64) excludes from the floor's and every rung's pass/fail
counts any attempt whose entry has `context.compactions >= 1`. Those
attempts feed a new per-bucket overflow posterior instead: Beta prior
alpha 0.5, beta 9.5 (mean 0.05, effective n 10, kind `policy-default`,
provenance "no compaction has been recorded; a weak prior that three
overflows in a row can move"), updated by one success per compacted
attempt and one failure per uncompacted attempt in that bucket.

`plan()` gains:

```
"overflow": {"mean": 0.05, "n": 0, "advisory": false, "text": null}
```

`advisory` is true when `mean >= steering.overflow_advisory_min_mean`
(shipped 0.3) and `n >= steering.overflow_advisory_min_n` (shipped 3).
`first` is unchanged by it. `--explain` prints the advisory as its own
line: `overflow: 3 of 5 attempts in this bucket compacted; split the
task or trim the handover before spawning worker-sonnet-low`. Section 2
of `src/ROUTING.md` says what to do with it: split or trim, then
re-assess each part as its own task. `generate_priors.py` emits the
overflow prior for every bucket; ROUTE-PRIORS checks its `kind` and
provenance like any other.

`route.py --selftest` gains scenario j (a bucket with three compacted
floor failures: floor posterior mean unchanged from the empty-ledger
value, overflow mean crosses 0.3, advisory true, `first` still the floor)
and scenario k (three uncompacted floor failures: floor posterior falls
as in scenario b, overflow stays at its prior, advisory false). Scenarios
h and i are Stage B's (the spawn/record/recover round trip and the
`--explain` context line), so Stage C continues the letters from there.

## 7. Settings fragment and hook: `dist/settings.fragment.json`

A file the consumer merges into `.claude/settings.json` (project) and,
for `autoCompactWindow`, into `~/.claude/settings.json` (user), since
the docs name it a user-settings key. `src/README.md` gives the merge
instruction for both, and the environment variable alternative
(`CLAUDE_CODE_AUTO_COMPACT_WINDOW`, precedence over everything) for a
consumer who prefers one place.

```
{
  "promptCacheTtl": "1h",
  "statusLine": {"type": "command", "command": "python3 tools/context_probe.py --main", "refreshInterval": 30},
  "subagentStatusLine": {"type": "command", "command": "python3 tools/context_probe.py --tasks"},
  "hooks": {
    "SessionStart": [
      {"matcher": "compact", "hooks": [{"type": "command", "command": "python3 tools/route.py --recover --project ."}]}
    ]
  },
  "_user_settings": {"autoCompactWindow": 200000}
}
```

`_user_settings` is documentation inside the fragment, not a key Claude
Code reads; `preflight.py` checks the real key wherever it lands. The
window is 200,000 because the orchestrator's context is routing lines
and worker summaries (`docs/COST.md`); the economic break-even argued in
D68 sits far below a 1M window and the minimum the platform accepts is
100,000. `subagentPromptCacheTtl` is left at its five-minute default:
every worker run on record finished inside five minutes (`cost_table.json`
cells, wall clock) and a one-hour write costs 1.6 times more.

## 8. Compact instructions

The documented mechanism is a `# Compact instructions` section in the
root `CLAUDE.md`. It ships twice so both install paths get it: inside
`src/LIFECYCLE.md`'s "Handoffs" section for the appended install, and in
`src/CLAUDE.template.md` for the pointer install. The text, identical in
both:

```
# Compact instructions

When compacting, keep these, in this order, each as its own heading:
goal; decisions already made; files and links that matter; verified
facts (with the command or number); work completed (with commit hashes);
unresolved questions; exact next action; every worker spawned whose
outcome is not yet recorded, with its assessment line and cell. Drop
tool output, intermediate reasoning, and anything a fresh session would
not need. This is the shape of handoffs/ files; a compaction summary is
a handoff the platform wrote.
```

Whether the summariser honours the section when it arrives via appended
`ORCHESTRATOR.md` content rather than a hand-written `CLAUDE.md` is
unverified; Stage E's E30 reads the summary it produces and records the
answer. Stage B ships the text either way; the cost of it being ignored
is nothing.

## 9. `preflight.py`

Four checks, all reading settings files and the environment, none
spawning anything:

- **auto-compact window**: `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, else
  `autoCompactWindow` in `~/.claude/settings.json`, `.claude/settings.json`,
  `.claude/settings.local.json`. PASS if set and between 100,000 and the
  model's window; WARN if unset ("compacts at the model's limit, about
  967K on a 1M model; the handoff threshold in `route.py --explain` still
  fires, but the fallback summary will be large and expensive").
- **cache TTL**: `promptCacheTtl` or `CLAUDE_CODE_PROMPT_CACHE_TTL`. PASS
  if `1h`. WARN if unset or `5m` and the Controller is installed
  (`check_controller` PASS): "a Controller run is about 500 s; on a
  five-minute TTL the orchestrator's next turn reprocesses its whole
  context uncached (`docs/COST.md`)".
- **compaction hook**: a `SessionStart` entry with matcher `compact`
  whose command contains `route.py --recover`. PASS or WARN ("after a
  compaction the orchestrator will not be told which workers are
  pending; the ledger still has them, but nothing prompts a read").
- **context probe**: `statusLine` and `subagentStatusLine` commands
  contain `context_probe.py`. PASS or WARN ("`route.py --explain` cannot
  report context usage; the handoff threshold never fires").

## 10. Handoff and lifecycle text (Stage D)

`handoff.py new --pending-workers` appends, under "Unresolved questions",
one bullet per pending ledger entry (`--recover`'s middle block, as
prose). `check` accepts the section with or without them.

`src/LIFECYCLE.md`, "Handoffs", gains a closing paragraph: the
`--explain` context line is the trigger for a handoff at a task boundary;
the platform's compaction is the fallback and the `SessionStart(compact)`
hook is how the session recovers from it; the `# Compact instructions`
section follows.

## 11. Pass conditions

- SCHEMA: both ledger versions validate; the new broken line is rejected.
- ROUTE-SELFTEST: nine scenarios (seven existing plus h and i).
- BACKTEST: on the recorded data, every existing check reproduces
  exactly (no historical entry carries `context`, so no attempt is
  excluded) and the overflow posterior equals its prior in all 18
  buckets. A backtest that moves any overflow posterior on historical
  data is a defect in the reconstruction, not a finding.
- REPLAY: unchanged, 125 of 125.
- ROUTE-PRIORS: every bucket carries an `overflow` prior with kind and
  provenance; `handoff_context_percent` is below the window fraction
  `autocompact_window_tokens` implies for a 200K model.
- COST-TABLE: unchanged from A.3.
- HANDOFF: every `handoffs/` file still passes, including one written
  with `--pending-workers` against a ledger holding a pending entry.
- A new check, PROBE-SELFTEST: `context_probe.py --selftest` runs both
  modes on the recorded sample and the merged file round-trips.
- `preflight.py` in `orchestrator-scratch` after installing the
  fragment: the four new checks PASS or WARN as section 9 states, none
  FAIL.

## 12. What this design does not do

It does not make the orchestrator compact on demand; there is no tool
for it (E29). It does not induce a worker compaction to measure one; the
ledger fields fill when a consumer's task overflows, and Stage E is the
only place one is produced deliberately. It does not change what
`first` resolves to: the overflow advisory sits beside the cell, never
replaces it. It does not touch the Controller. It does not claim the
compaction summary follows the compact instructions; E30 checks.
