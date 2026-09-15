# Recurring token cost

Bundle version `2026-09-15-2203a02` (`dist/.claude/ORCHESTRATOR_VERSION`).
Recomputed 2026-09-15 per `docs/PLAN-2.md` Stage 5.3, against the
routing-2 bundle (Stage 4); the prior figures below this point were
measured against `2026-09-15-9b5f64b`, before Plan 2. Measured by
counting UTF-8 bytes in `dist/` and dividing by four, the same
approximation `test/harness/empirical-checklist.md` uses for its E12 cost
estimate. This is an estimate, not a token count: the real count comes
from the provider's usage report (persona section 7.3), not a
client-side guess, and belongs here once a live run reports it.

| Artefact | Paid on | Chars | Tokens (chars / 4) |
| :--- | :--- | :--- | :--- |
| `dist/ORCHESTRATOR.md`, rationale stripped (shipped) | every orchestrator turn, once appended to the consumer's `CLAUDE.md` | 16,559 | ~4,140 |
| `dist/ORCHESTRATOR.md`, `--with-rationale` (harness only, never shipped) | not paid by a live orchestrator turn; measured here for comparison | 22,109 | ~5,527 |
| 15 worker descriptions (`dist/.claude/agents/*.md` frontmatter) | every orchestrator turn, in the Agent tool's subagent_type listing | 2,641 | ~660 |
| One worker definition (`dist/.claude/agents/WORKER_*.md`, persona inlined) | once per worker start, to that worker only | 1,909 to 1,971 (mean 1,957) | ~477 to ~493 (mean ~489) |
| `dist/.claude/commands/workers.md` | once per `/workers` invocation | 1,983 | ~496 |
| `dist/.claude/B0_BRIEF.md` | read on demand, only when `ROUTING.md` section 4's falsified-constraint trigger fires, and only by the orchestrator deciding the handover, not by every turn (D60, Stage 12) | 5,836 | ~1,459 |
| `tools/route.py --from-line ... --explain` output | every orchestrator turn, read as command output, not as a file | 408 to 718 across two representative buckets | ~102 to ~180 |

Command that produced these counts, from the repository root:

```
wc -c dist/ORCHESTRATOR.md dist-with-rationale/ORCHESTRATOR.md dist/.claude/B0_BRIEF.md
grep -h '^description:' dist/.claude/agents/*.md | wc -c
wc -c dist/.claude/agents/*.md | grep -v total | sort -n
wc -c dist/.claude/commands/workers.md
python3 tools/route.py --from-line "assessment: mechanical, short, contained; self_directed: false; prior_failure: none" --project . --explain | wc -c
```

What this buys: `ORCHESTRATOR.md` is the whole routing rubric and lifecycle
protocol, paid once per orchestrator turn so the orchestrator can classify
and select without a file read; the fifteen descriptions are what the
orchestrator sees about each cell without opening its definition, about
176 characters each; a worker definition is a self-contained persona so a
worker needs no file read at startup (D3); `/workers` is invoked rather
than persistent, so its cost is per call rather than per turn;
`B0_BRIEF.md` is the one artefact in this table that is not a recurring
per-turn cost at all, since section 4's trigger fires rarely (D60 measured
it on one task shape; the first live fire in the installed bundle had not
happened as of the Stage 12 dogfood log) and the file is read only then.

**What Plan 2 changed here.** `tools/route.py`, `tools/handoff.py`
(40,461 and 19,739 characters), `src/routing_priors.json`,
`src/cost_table.json`, and `src/routing_table.json` (30,699 characters
combined) all ship in `dist/`, but none of them are a recurring
per-turn cost: `ROUTING.md` section 2 invokes `route.py` with the Bash
tool and reads only its stdout, never the script or the data files
themselves. That stdout, the `--explain` line above, is the entire
marginal cost of resolution; a request never reads the destination
table or the ledger. `ORCHESTRATOR.md` itself grew by 1,827 characters
(14,732 to 16,559, both rationale-stripped) despite stripping every
evidentiary aside, because section 2's prose describing how to call and
read `route.py` is longer than the static table it replaced; that
prose is procedural, not evidentiary, so it was not a candidate for
stripping in the first place (D64's own distinction).

`ORCHESTRATOR.md` grew from 12,185 to 14,732 characters across the plan
(21 percent), almost entirely in Stage 12: section 4's falsified-constraint
trigger went from a one-step re-spawn to a two-step sequence naming the
brief, its measured record, and the cost arithmetic for using it first
(D60). This is the largest single addition since the clarify rule
(D10, below), and it buys the same thing D47 already measured: the floor
plus the brief clears the shape the floor alone cannot, at roughly a third
of the confirmed cell's cost, so most of section 4's growth is paid for by
avoiding the dearer escalation more often, not merely spent.

The largest single addition before that was the clarify rule (`ROUTING.md`
section 1.1, D10), 1,810 characters or 452 tokens, unchanged since D10
added it: a rise of roughly 18 percent in what every orchestrator turn
paid at the time it was added. What it buys: E12 measured an opus
orchestrator answering clarify on 9 of 17 fixtures, 5 of them with a
correct axis assessment, which is a whole wasted turn each time plus the
user's attention. Whether the clarify rate improved under it was never
re-measured at reporting grade in isolation; the routing fixtures'
agreement stayed at 100 percent through Stages 8 and 12 (D45, D59), which
is consistent with the rule working but does not isolate it.

## The cost of a routing verdict against the cost of the work it routes

The point `docs/REVIEW.md` makes qualitatively ("classification may cost
more than the work it routes") stated as a number, added 2026-09-11 per
`docs/PLAN.md` Stage 1.4, recomputed here with the caveat Stage 13
requires: the underlying per-call cost shifted platform-side between
2026-09-14 and 2026-09-15 by roughly 2x, for reasons outside this
repository's control (E27, `docs/FINDINGS.md`), so the two figures below
are not from the same cost regime and the ratio between them is not
recomputed on that account.

**Mean opus routing verdict cost per fixture, current bundle**: USD 0.23,
measured 2026-09-15 (E27; the nine-run after-measurement for Stage 12.4
averaged USD 4.06 across 18 fixtures, USD 0.226 per verdict). Against
D45's USD 0.13 to 0.16 (bundle `282981f`, 2026-09-14) and the original
USD 0.1645 above (bundle `af94deb`, 2026-09-08): the routing prompt and
the fixtures are effectively unchanged across all three measurements
(section 4's growth adds a few hundred characters to a prompt already
read whole), so the roughly 2x rise is attributed to E27's platform-side
shift, not to anything this plan changed.

**Mean `worker-sonnet-low` cost per benchmark run**: USD 0.1641, unchanged
from the original measurement (T1 through T8, 96 runs, 2026-09-07 and
2026-09-08 bundles); no later stage re-ran the floor on those tasks at a
cost worth pooling in. T9, T10 and T11's floor-with-brief runs (Stage 9.8)
cost USD 0.35 to 0.41 per run, since that arm always pays for the brief's
extra length, and are a different measurement (`docs/DECISIONS.md` D47),
not pooled here.

**The ratio is stale, by construction.** At USD 0.1641 pooled against the
original USD 0.1645 verdict cost, the ratio was 1.003, cost parity between
routing and the floor work it routes to. At the current USD 0.23 verdict
cost against the same unchanged USD 0.1641 floor cost, the ratio is 1.40:
a routing verdict now costs 40 percent more than the floor run it routes
to, on the same floor, under a shift this repository did not cause and
cannot correct from here. This is recorded as the honest current number,
not smoothed toward the earlier one; whoever next measures this ratio
should re-check E27's shift is still in effect before comparing against
either figure.

**Not re-measured for the routing-2 bundle.** The USD 0.23 verdict figure
above was measured against the pre-Plan-2 bundle, which read a full
`ORCHESTRATOR.md` with the destination table in context. The
rationale-stripped bundle this stage ships is 25 percent smaller than
the equivalent `--with-rationale` build (16,559 against 22,109
characters) and, per E27's own finding that a verdict's cost is
dominated by reading `ORCHESTRATOR.md` itself rather than by output
tokens, a smaller context should cost somewhat less per verdict. This
plan projects zero live spend (`docs/PLAN-2.md` rule 3), so that
expectation is not measured here; whoever next runs a live routing batch
against this bundle should record the new figure rather than assume the
old one still holds.

## The Controller: measured, not shipped

`tools/system_controller.py` (Stage 10) is the one runtime this
repository built beyond Claude Code itself (`CLAUDE.md`, D48). Stage 11's
verdict (D59) was "prompt": the fleet did not beat B0 at the reporting
bar within three times its cost, so the Controller does not ship into
`ORCHESTRATOR.md` or the routing table, and nothing above adds it to the
recurring cost of using the shipped bundle.

Its own cost, measured for the record since the question ("the
Controller's per-run cost if it shipped") was asked directly by this
task: USD 1.87 to 1.97 per run on the toy problem (three completed runs,
Stage 10.9), and USD 2.0 to 3.0 per run on the T10 benchmark fixture
across two batches (eleven completed runs, D56, D58), mean USD 2.7. Per
solved task, with one floor-cell instantiation added, USD 4.40 (D59)
against B0's USD 0.41 and the floor's own USD 0.16. The Framer at
`worker-opus-high`, called two to three times per run under quick mode's
verify-and-reframe loop, is 30 to 50 percent of that cost by itself. This
figure is not revisited unless a future stage reopens Stage 11's
question at a cheaper configuration (D59's own note on what would change
the verdict).

## The fixed load of a stage session

Added 2026-09-11 per `docs/PLAN.md` Stage 1.4; this is its final
measurement, since Stage 13 is the plan's last stage and there is no
future stage session to pay this load. A session working this plan read,
before its first task, the charter (`CLAUDE.md`), one model-class persona
file, that persona's `ai-prompting` language profile, the plan
(`docs/PLAN.md`) and the review it is built on (`docs/REVIEW.md`).
Measured for the sonnet class, 2026-09-15:

| File | Chars |
| :--- | :--- |
| `CLAUDE.md` | 18,391 |
| `ENGINEERING_PERSONA.sonnet.md` | 50,520 |
| `ENGINEERING_PERSONA_LANGUAGES/ai-prompting.sonnet.md` | 2,156 |
| `docs/PLAN.md` | 82,154 |
| `docs/REVIEW.md` | 25,743 |
| **Total** | **178,964 (~44,741 tokens)** |

Up from 149,172 characters (~37,293 tokens) at the first measurement.
`docs/PLAN.md` grew from 55,795 to 82,154 characters (47 percent), the
whole of the rise: each stage's detail (numbers, findings, decision
pointers) stayed in the file as it completed, per this plan's own rule
that a task's result is recorded in place rather than batched afterwards.
`CLAUDE.md` also grew, from 14,958 to 18,391 (23 percent), despite Stage
13.1 replacing the seven-step working protocol with a one-line pointer:
the open-questions section gained more prose closing questions than the
protocol it removed cost.

Stage 1.4's note flagged this growth as something Stage 13's close-out
was "expected to address". It is addressed here by not pruning: every
stage's detail is what task 13.4 requires ("every stage `done` or
`blocked` with its pointer"), and this plan's own working practice
(`CLAUDE.md`, "diagnostic before patch", "no silent capability claims")
treats the record of what was measured as the load-bearing artefact, not
overhead to trim. The 44,741-token session load was paid twelve times
across this plan's thirteen stages (once per stage's fresh confirmation,
`CLAUDE.md` step 3) and will not be paid again: no session opens this
repository under this protocol after Stage 13, since there is no next
stage for the pointer in `CLAUDE.md` to send it to.

## What is not measured here

Actual provider token counts (characters per token vary by tokeniser and
content), the Claude Code system prompt itself, and anything the
orchestrator reads while assessing a task, such as the task text or a
file it opens. Those sit outside this repository's control.
