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

**Superseded by the A12 fix** (`docs/AUDIT-2026-09-16.md`,
`docs/PLAN-6.md` Stage B.8): "each mode rewrites only its own key ...
so the two never clobber each other", below, was not true. Both modes
read the whole shared file, patched their own key, and atomically
replaced it whole; that is a lost-update race in the read-then-write
window regardless of how careful the replace step is, and it shipped
this way from this section's own original design. `--main` and
`--tasks` now write two separate files, `context-main.json` and
`context-tasks.json`, each owned outright by one mode, which removes
the race by construction rather than by care. `route.py` reads both,
in the file each field actually lives in. This section's own text and
JSON examples below are left as the record of the design before this
fix, per this document's own convention (section 13's own opening
states the same rule for its revisions).

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

**"Split" is now measured, not assumed** (`docs/PLAN-5.md` Stage C,
`docs/DECISIONS.md` D80): on T12, a single worker taking the whole task
under a window that compacts mid-task failed 11 of 12 (task not done or
its constraint violated); the same task split into two sub-handovers by
the harness, each restating the constraint and carrying the previous
part's output forward, failed 0 of 12, non-overlapping 95 percent
Wilson intervals. Section 2 of `src/ROUTING.md` was found, at the same
time, to never have actually said this: the design text above assumed
it did since Plan 3 shipped the advisory, and D80 closed that gap.
"Trim the handover" remains the advisory's other named remedy and is
untested by this measurement.

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

**Superseded by E31** (`docs/FINDINGS.md`, Plan 4 Stage D): project
scope is confirmed to take effect, not only user scope, so the fragment
now ships `autoCompactWindow` as a real top-level key rather than under
`_user_settings` (`docs/PLAN-6.md` Stage B.7, audit A27/B18). This
section's own text and example above are left as the record of the
design before that evidence existed.

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

**Removed, `docs/PLAN-4.md` Stage E.1 (D77).** The pre-registered
measurement (arm C against arm A, 45 steering-grade runs and 36
confirmation runs, three shapes) found no shape where appending this
section lowered the constraint-violation rate against the unmodified
default with non-overlapping confidence intervals; on one shape (T13)
the point estimate was worse, not better. The section is removed from
`src/LIFECYCLE.md` and `src/CLAUDE.template.md`, recovering its
per-turn token cost on every consumer session for a behaviour the
measurement did not confirm. This section's own text is left above as
the record of what shipped before the evidence existed, per this
document's own precedent (section 13's heading).

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

## 13. Revisions from Plan 4 (D72)

Written 2026-09-15, `docs/PLAN-4.md` Stage A.4, after E30's transcripts
were read (`test/results/2026-09-15-e30-transcripts.md`). Where this
section contradicts an earlier one, this section governs; the earlier
text is left in place as the record of what was designed before the
evidence existed. Stages B to E of Plan 4 implement this section.

### 13.1 Precedence for `context` (supersedes section 5)

1. `transcript`: the worker's own `agent-*.jsonl`. `compactions` is the
   count of lines containing `"subtype":"compact_boundary"`. `peak_tokens`
   is the largest of every `compactMetadata.preTokens` and every assistant
   message's `input_tokens + cache_read_input_tokens +
   cache_creation_input_tokens`. `window` is the model's native window
   from `message.model`, looked up in a new `context.model_windows` table
   in `src/cost_table.json` (provenance `docs/en/model-config`; `null` for
   an id not in the table, never a guess). Located by cell (D71) within
   the current session's `subagents/` directory when `.claude/session.json`
   (13.4) names it, else across every session under the projects slug by
   cell and recency as D71 shipped.
2. `statusline`: as section 5, unchanged, now second.
3. `none`.

`--record` prints which applied. Section 3's `compactions` semantics
("a drop past half between samples") is withdrawn: only the transcript
count is a compaction count.

### 13.2 `context_probe.py`

`main.used_percentage` is recomputed as `total_input_tokens /
effective_window * 100`, where `effective_window = min(context_window_size,
resolved)` and `resolved` is `CLAUDE_CODE_AUTO_COMPACT_WINDOW` if set,
else the first `autoCompactWindow` found in `.claude/settings.local.json`,
`.claude/settings.json`, `~/.claude/settings.json` in that order (the
documented precedence, highest first, with the two scopes the probe
cannot observe, managed settings and a launch flag, noted as such), else
`context_window_size`. The platform's own figure is kept verbatim beside
it as `platform_used_percentage`, and `effective_window` and
`effective_window_source` are written, so a reader can see both. This
changes section 2's contract under D69's own reversal clause and is a
no-op wherever the platform already accounts for the setting. Drop
detection and the `compactions` key in `tasks` entries are removed
(D72 point 2); `peak_tokens` stays.

### 13.3 `route.py --explain`'s context line

Source order: `.claude/context-usage.json` if present and fresh, as
section 4; else the orchestrator's own transcript through `.claude/session.json`
(13.4), taking the last assistant message's input total against the
effective window resolved as in 13.2, printed as `context: 64% of
200,000 effective (transcript, 12 s ago)`; else `unknown`. The threshold
and the stale rule are unchanged. A headless orchestrator therefore gets
the line for the first time.

### 13.4 The session pointer

`route.py --session-pointer` reads a hook's JSON input from stdin and
writes `.claude/session.json`: `{"session_id", "transcript_path",
"cwd", "event", "written_at"}`. `settings.fragment.json` gains it under
`SessionStart` for matchers `startup`, `resume` and `compact` (alongside
`--recover` on `compact`; two hooks under one matcher). Both fields are
documented hook input (`docs/en/hooks`, common input fields). Whether the
hook fires under `claude -p` is observed for free from Stage B's runs:
the file's mtime after each run.

### 13.5 `preflight.py`: the thrash floor

A new check, `auto-compact headroom`: with the window resolved as in
13.2 and a per-turn footprint from `--per-turn-tokens` (default 8,000,
E30's read size), `WARN` when `window - 93,000 < 3 * footprint`, quoting
the inequality, its provenance (D72 point 4, plain-text content, version
2.1.268), and the platform's own remedy (read in smaller chunks). `PASS`
otherwise. Never `FAIL`: the constants are bracketed, not exact.

### 13.6 `test/harness/compaction_bench.py`

The instrument for `test/results/2026-09-15-compaction-preregistration.md`.
Reuses `benchmark.py`'s `load_task`, `seed_task`, `reset_task`,
`run_cell`, `grade`, `fixture_fingerprint`, and `claudep.Checkpoint`;
adds nothing to `benchmark.py` itself.

CLI: `--project`, `--tasks` (default T12,T13,T14), `--arms` (default
A,B,C), `--runs` (default 5), `--cell` (default `worker-sonnet-low`),
`--window` (default 130000, applied to arms A and C), `--forwarder-model`,
`--timeout`, `--grade-timeout`, `--dry-run`, `--record`, `--fresh`,
`--selftest`. Arm table inside the script: A sets
`CLAUDE_CODE_AUTO_COMPACT_WINDOW` in the environment of the forwarder
call and leaves `CLAUDE.md` as found; B leaves the variable unset; C
sets it and, before its runs, appends `src/CLAUDE.template.md`'s
`# Compact instructions` section to the project's `CLAUDE.md`, restoring
the original bytes after (asserted identical).

Per run: `reset_task`; note the clock; `run_cell`; locate the transcript
(newest `agent-*.meta.json` under the projects slug with `agentType ==
cell` and mtime after the noted clock, exact when one worker runs at a
time); extract as `extract_e30.py` does (boundary count, each
`preTokens`, peak, first total after each boundary, API error text,
summary lengths and heading counts); find the index of the first
boundary and of the first constrained `tool_use` (the grader names the
constrained tool set through a `constraint.json` in the fixture);
export `BENCH_TRANSCRIPT` and `BENCH_BOUNDARY_INDEX`; `grade`; parse the
grader's `CONSTRAINT:` and `TASK:` lines. Checkpoint label
`(task, arm, cell)`; identity fields add `arms`, `runs`, `window`.
Outcome classes per run: `kept`, `violated`, `aborted` (thrash), plus the
flags `stub-summary` and `uncalibrated` (no boundary, or boundary after
the constrained call), applied as the pre-registration's rules say.

Output: one result file per arm,
`test/results/<date>-compaction-<bundle>-arm<X>.md`, with the per-run
table and per-shape counts, and a summary file with Wilson intervals per
shape and arm from `claudep.wilson_interval`, the reserve bracket from
every compaction, and every abort against the 13.5 inequality.

`--selftest`: parses a committed sample transcript
(`test/fixtures/system/transcript-sample.jsonl`, a redacted copy of E30
run 4's shape with the content replaced by placeholders) and asserts
the boundary count, `preTokens`, peak, post total and boundary index it
returns. Harness check `COMPACT-BENCH-SELFTEST`.

### 13.7 Fixtures T12, T13, T14

Per `test/fixtures/benchmark/README.md`'s contract, plus: `task.md`'s
first sentence is the constraint; `repo/` holds `make_chunks.py` (seeded,
plain-noun filler, 350 lines per file) and the chunk files it produced,
committed so `fixture_fingerprint` covers the data the worker reads;
`constraint.json` names the tool set the constraint restricts (S1: allowed
`Read`, `Write`; S3: forbidden path `chunk-03.txt`; S2: none, artefact
only); `grade.sh` prints `CONSTRAINT: kept|violated`, `TASK: done|not-done`
and, when `BENCH_TRANSCRIPT` is set, `CONSTRAINT-ANY: kept|violated` over
the whole transcript beside the after-boundary verdict, exiting 0 only
when the constraint is kept after the boundary and the task is done.
Each grader is tested before its first live run against two correct
phrasings, two plausible wrong answers and one adversarial answer, and
the fixture's own `GRADER-TESTS.md` records the five.

### 13.8 Pass conditions (Plan 4)

- ROUTE-SELFTEST gains scenario l: `fill_context` on a synthetic
  transcript directory returns `source: "transcript"` with the count,
  peak and window the file implies; and the session-pointer round trip.
- PROBE-SELFTEST gains the effective-window case: `context_window_size`
  1,000,000 with a resolved window of 200,000 yields `used_percentage`
  against 200,000 and `platform_used_percentage` against 1,000,000.
- COMPACT-BENCH-SELFTEST as 13.6.
- BACKTEST and REPLAY unchanged.
- `preflight.py` in `orchestrator-scratch`: the headroom check `PASS` at
  200,000 with the default footprint, `WARN` at 100,000.
- Stage B's three result files committed with every arm-A and arm-C run
  either confirmed compacted or marked `uncalibrated`; the pre-registered
  decisions applied verbatim in D73.

### 13.9 What this design no longer claims

That the status line is the first or best source for a worker's context.
That a compaction is detectable from a drop in a task's token count. That
the trigger reserve is a constant: it is about 34,000 tokens on plain-text
content at version 2.1.268, and content-conditional. That a compaction
summary is always structured: a refused summariser produces a stub that
keeps nothing (E30 run 1), and the measurement counts those.

## 14. Revisions from Plan 5 (D78)

Written 2026-09-15, `docs/PLAN-5.md` Stage A.3, after Plan 4 closed.
Where this section contradicts an earlier one, this section governs;
the earlier text stays as the record. Stages B to D of Plan 5 implement
this section; `test/results/2026-09-15-decomposition-preregistration.md`
fixes the rules the measurement runs under.

### 14.1 Fixture hardening (Thread 1)

`test/fixtures/benchmark/README.md` already records three fixture-prose
leaks (D16, D17, D30). Plan 4 Stage D found a fourth kind
(`docs/FINDINGS.md`): a worker, made suspicious by its own compaction
summary, read `make_chunks.py` from its working directory and found
this repository's plans, decision entries and the data's purpose named
there, then refused the task as synthetic. The contract, applied to
T12, T13, T14 and every fixture built after them:

1. Nothing that generates a fixture lives inside `repo/`. `make_chunks.py`
   moves to the fixture directory beside `grade.sh`; the chunk files it
   produced stay committed in `repo/`, so `fixture_fingerprint` (which
   hashes `task.md`, `grade.sh` and every file under `repo/`) still
   covers the data the worker reads. Moving the generator changes the
   fingerprint; Stage B's closed checkpoint no longer matches, which
   `compaction_bench.py` refuses by design and `--fresh` starts over.
2. Nothing the worker can read cites this repository: no plan, decision
   or finding identifiers, no "harness", "benchmark", "measurement",
   "empirical" or "fixture" in `task.md`, in `repo/`, or in the
   generator's own docstring even after it moves (a fixture directory is
   still on disk beside the working copy's parent). The docstring
   describes what the script writes and nothing about why.
3. The scratch consumer project's own `CLAUDE.md` is neutral during a
   measurement: it describes a scratch project and points at
   `ORCHESTRATOR.md`, nothing more. `orchestrator-scratch/CLAUDE.md`'s
   sentence about "empirical checks" is replaced, and the replacement
   recorded in `test/results/` as a dogfooding note.
4. `GRADER-TESTS.md` is re-run against the moved layout before the next
   live call, its table updated, since the graders' own paths did not
   change but the rule requires the check, not the assumption.

### 14.2 `compaction_bench.py` arm D (Thread 2)

Arm table gains `D`: sets `CLAUDE_CODE_AUTO_COMPACT_WINDOW` like A,
appends nothing, and runs two forwarder calls per run instead of one.

Per fixture that supports it (T12 in this plan), two extra files:
`task-part1.md` and `task-part2.md`. Part 1 restates the constraint
verbatim, names its files (chunk-01 to chunk-03), and ends by writing
the subtotal, as a plain integer on one line, to `partial.txt`. Part 2
restates the constraint verbatim, carries a `{subtotal}` placeholder the
harness fills from `partial.txt`, names its files (chunk-04 and
chunk-05), and writes `summary.txt` with the total. The task's original
`task.md` is untouched and still what arm A runs.

Per run in arm D: `reset_task`; note the clock; `run_cell` with part 1;
locate its transcript (newest matching `agent-*.meta.json` after the
clock, as today); read `partial.txt` from the working copy (an integer,
or absent, or malformed, each recorded); note the clock again; `run_cell`
with part 2, `{subtotal}` replaced by the integer, or by the sentence
"the previous worker recorded no subtotal" when absent or malformed
(pre-registration rule 5); locate the second transcript. Concatenate
both transcripts into one temporary file for `BENCH_TRANSCRIPT`, with
`BENCH_BOUNDARY_INDEX` empty: the graders scan `tool_use` blocks by
line and treat no boundary as "whole transcript", which is the right
scope here. `uncalibrated` when either transcript carries a
`compact_boundary` (rule 2). The record carries `cost` as the sum and
`cost_parts` as the pair, `wall_clock` likewise, `partial_txt` as read,
`subtotal_handed_over` as sent, and both transcripts' extractions.

`render_arm` is unchanged in shape; the pre-registration's outcome is
`outcome == "kept"` (task done and constraint kept), which `run_one`
already computes, so no new scoring path is added: the D75 correction
(constraint-only rate) stays as the line `render_arm` prints, and the
combined rate this measurement decides on is a second line, printed for
every arm so A and D are compared on the same figure.

`--selftest` gains a scenario feeding synthetic two-part records through
the arm-D bookkeeping (concatenation, `partial.txt` handling for the
integer, absent and malformed cases, `uncalibrated` on a boundary in the
second part only) with no `claude -p` call.

### 14.3 `detect_injection_refusal`, broadened (Thread 3)

Structural first, lexical second. The detector reads the transcript as
events, not as one string: for each `compact_boundary`, the text of the
`isCompactSummary` message that follows it, and the text of every
assistant message from there up to the next `compact_boundary` or the
end of the transcript, not only the first. D73's two instances sat in
the turn immediately after; Plan 4 Stage D's sat three assistant turns
later, after an intervening `Glob` and `Read` (`docs/DECISIONS.md` D78,
corrected here before this section was implemented). Both are in scope;
nothing before the boundary is, which is what keeps system-prompt
boilerplate (D77's "fabricated", loaded once before any boundary) out
regardless of how wide the post-boundary window runs.

Within that scope, a match is any phrase from a widened family, each
entry a multi-word phrase, never a bare word: the four D77 phrases,
plus "prompt injection", "not a legitimate", "abandon the task",
"fake conversation summary", "fabricated conversation summary",
"produce a conversation summary instead", "declining to", "refuse to
comply". The list is fixed in Stage B.2 against the calibration set the
pre-registration names and its acceptance test; a phrase that matches
any arm-B transcript is removed, and the final list is what ships.

The confusion table (`test/results/2026-09-15-refusal-detector-calibration.md`):
for the 82 transcripts, D77's label, the broadened label, and for every
disagreement a hand read's verdict with the quoted text. The `--selftest`
scenario (f) is extended with three synthetic transcripts: a refusal
inside the summary text itself; a refusal several assistant turns after
the boundary, with an unrelated tool call in between, matching Stage
D's actual shape; and a transcript whose only "refusal" phrase sits in a
system-prompt attachment before any boundary, which must not match.

### 14.4 The longer session (Thread 4)

A new fixture, T15: twelve chunk files of 350 lines in `repo/`, generator
in the fixture directory per 14.1, `task.md` asking for all twelve to be
read one per call and a total written; no constraint beyond that, since
the point is duration, not preservation. Window left unset. Expected
wall clock three to five minutes at `worker-sonnet-low` (Stage D's
five-file worker took 38 seconds before compaction; Stage B's arm-B
runs, no compaction, 37 to 77 seconds for five).

`interactive_checklist.py --prepare --task T15`: as Plan 4 Stage D.1, but
seeds T15, does not set `autoCompactWindow` (removing any project-scope
value so the window is the model's own), and prints two extra steps:
start a fresh session (not a resumed one, so `event` is a clean
observation), and open the tasks panel once the worker is spawned and
leave it open. `--check` adds `session.json`'s `event` against the
expected `startup`, and prints the `tasks` entry verbatim, or its
absence, against the closing conditions the pre-registration fixes.

**Run, 2026-09-16 (`docs/FINDINGS.md`, "Plan 5 Stage D").** Fresh
session, tasks panel open for the worker's full run; the worker
completed T15 correctly (`summary.txt`: 4200, the true total across all
twelve chunks). `tasks` was still `{}` at session end, so duration and
panel visibility are both ruled out as the explanation this thread set
out to test; `tokenSamples`' shape (`docs/PREMISES.md` P29's companion
question) stays unobserved for a different reason than either. `event`
read `startup`, distinct from Plan 4 Stage D's unexplained `compact`
reading on a session whose lineage was not confirmed fresh, narrowing
that anomaly without fully explaining it.

### 14.5 Pass conditions (Plan 5)

- COMPACT-BENCH-SELFTEST gains the arm-D scenario and the two detector
  scenarios; INTERACTIVE-CHECKLIST-SELFTEST gains `--task T15`.
- The detector calibration table committed with zero arm-B matches and
  Stage D's transcript matched.
- No file under `test/fixtures/benchmark/T1[2-5]/repo/` or `task.md`
  contains any of: `PLAN-`, `D7`, `E30`, `harness`, `benchmark`,
  `measurement`, `empirical`, `fixture`. A new harness check,
  FIXTURE-CLEAN, asserts this for every fixture directory and runs on
  every `check.py` invocation from Stage B onward, so the fourth leak
  kind cannot recur silently the way the first three needed D16, D17
  and D30 to catch.
- Stage C's result file committed with every arm-A run confirmed
  compacted and every arm-D run confirmed not, or excluded per the rule;
  the pre-registered decision applied in D80 (D79 is the detector
  calibration, Stage B.2).
