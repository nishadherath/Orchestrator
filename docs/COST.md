# Recurring token cost

Bundle version `2026-09-07-af94deb` (`dist/.claude/ORCHESTRATOR_VERSION`). Recomputed
2026-09-11 against this bundle; the prior figures here were measured against
`2026-09-06-04d2acc`. Measured by counting UTF-8 bytes in `dist/` and dividing
by four, the same approximation `test/harness/empirical-checklist.md` uses for
its E12 cost estimate. This is an estimate, not a token count: the real count
comes from the provider's usage report (persona section 7.3), not a
client-side guess, and belongs here once a live run reports it. Recompute
after any change to `src/ROUTING.md`, `src/LIFECYCLE.md`, `src/WORKER_PERSONA.md`
or `src/commands/workers.md` and a `dist/` rebuild.

| Artefact | Paid on | Chars | Tokens (chars / 4) |
| :--- | :--- | :--- | :--- |
| `dist/ORCHESTRATOR.md` | every orchestrator turn, once appended to the consumer's `CLAUDE.md` | 12,185 | ~3,046 |
| 15 worker descriptions (`dist/.claude/agents/*.md` frontmatter) | every orchestrator turn, in the Agent tool's subagent_type listing | 2,550 | ~638 |
| One worker definition (`dist/.claude/agents/WORKER_*.md`, persona inlined) | once per worker start, to that worker only | 1,910 to 1,990 (mean 1,951) | ~478 to ~498 (mean ~488) |
| `dist/.claude/commands/workers.md` | once per `/workers` invocation | 1,983 | ~496 |

Command that produced these counts, from the repository root:

```
wc -c dist/ORCHESTRATOR.md
grep -h '^description:' dist/.claude/agents/*.md | wc -c
wc -c dist/.claude/agents/*.md | grep -v total | sort -n
wc -c dist/.claude/commands/workers.md
```

What this buys: `ORCHESTRATOR.md` is the whole routing rubric and lifecycle
protocol, paid once per orchestrator turn so the orchestrator can classify and
select without a file read; the fifteen descriptions are what the orchestrator
sees about each cell without opening its definition, about 170 characters
each; a worker definition is a self-contained persona so a worker needs no
file read at startup (D3); `/workers` is invoked rather than persistent, so
its cost is per call rather than per turn.

The largest single addition to date is the clarify rule (`ROUTING.md` section
1.1, D10), 1,810 characters or 452 tokens of the current figure above,
unchanged since D10 added it: this section has not been edited since. It was
a rise of roughly 18 percent in what every orchestrator turn paid at the time
it was added. What it buys: E12 measured an opus orchestrator answering
clarify on 9 of 17 fixtures, 5 of them with a correct axis assessment, which
is a whole wasted turn each time plus the user's attention. If a measured run
under this rule shows the clarify rate is no better than it was without it,
this section is the first thing to prune.

## The cost of a routing verdict against the cost of the work it routes

The point `docs/REVIEW.md` makes qualitatively ("classification may cost
more than the work it routes") stated as a number, added 2026-09-11 per
`docs/PLAN.md` Stage 1.4.

**Mean opus routing verdict cost per fixture**: USD 0.1645. Computed as
total cost divided by fixtures times runs, pooled across the two
reporting-grade-sized routing batches recorded against this bundle,
`test/results/2026-09-08-routing-opus-af94deb-summary.md` (USD 8.9070
across 18 fixtures times 3 runs) and `test/results/2026-09-08-routing-opus-
af94deb-5a7585d-summary.md` (USD 8.8624 across the same 18 times 3): pooled
total USD 17.7694 across 108 verdicts. The smaller F05-only follow-up batch
(`2026-09-08-routing-opus-af94deb-b86c53d-F05only-summary.md`, USD 0.5111
across 3 verdicts) is a single-fixture recalibration run, not representative
of the general routing mix, and is not pooled in.

**Mean `worker-sonnet-low` cost per benchmark run**: USD 0.1641. Computed
across every individual run recorded at `worker-sonnet-low` in the search
and confirmation phases of T1 through T8, 96 runs total (12 per task: 3
search, 9 confirm, since the floor is the confirmed frontier for every task
built so far), pooled from `test/results/2026-09-07-benchmark-04d2acc-
replication.md` (T1 to T6), `test/results/2026-09-07-benchmark-04d2acc-
tasks-T7.md` (T7) and `test/results/2026-09-08-benchmark-af94deb.md` (T8).
Per-task means range from USD 0.103 (T6) to USD 0.281 (T7).

**Ratio: 1.003.** A routing verdict costs almost exactly as much as the
`worker-sonnet-low` run it routes to, for every benchmark task measured so
far. This is not "the router costs more than trivial work and less than
substantial work"; at the cheapest cell, which is where every measured task
has landed (`docs/REVIEW.md`), the router and the work are cost parity. The
question `docs/REVIEW.md` raises, what one wrong routing decision costs, is
still unanswered, but the router's own overhead is no longer invisible: it
roughly doubles the cost of every task that turns out to belong at the
floor, since routing plus doing the task costs about twice doing the task
alone. This is the number the two-stage classifier (`docs/PLAN.md`
Stage 5-6) is measured against under acceptance criterion 6, since a
cheaper-to-run classifier that reaches the same routing agreement is a
direct win on this ratio.

## The fixed load of a stage session

Added 2026-09-11 per `docs/PLAN.md` Stage 1.4, so the development side's
overhead is on the same ledger as the product's. A session working this
plan reads, before its first task, the charter (`CLAUDE.md`), one
model-class persona file, that persona's `ai-prompting` language profile,
the plan (`docs/PLAN.md`) and the review it is built on (`docs/REVIEW.md`).
Measured for the sonnet class, 2026-09-11:

| File | Chars |
| :--- | :--- |
| `CLAUDE.md` | 14,958 |
| `ENGINEERING_PERSONA.sonnet.md` | 50,520 |
| `ENGINEERING_PERSONA_LANGUAGES/ai-prompting.sonnet.md` | 2,156 |
| `docs/PLAN.md` | 55,795 |
| `docs/REVIEW.md` | 25,743 |
| **Total** | **149,172 (~37,293 tokens)** |

This is paid once per stage, cached within the session for the rest of that
stage's work, and is not part of the shipped product's recurring cost above:
it is what running this repository's own development process costs before
any task-specific work begins. `docs/PLAN.md` is the largest single
contributor and grows with every stage completed, since finished stages'
detail stays in the file rather than being pruned; Stage 13's close-out is
the point at which that growth is expected to be addressed.

## What is not measured here

Actual provider token counts (characters per token vary by tokeniser and
content), the Claude Code system prompt itself, and anything the
orchestrator reads while assessing a task, such as the task text or a file
it opens. Those sit outside this repository's control.
