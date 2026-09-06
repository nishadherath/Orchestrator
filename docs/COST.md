# Recurring token cost

Bundle version `2026-09-06-04d2acc` (`dist/.claude/ORCHESTRATOR_VERSION`). The mechanical,
long-horizon row D12 removed for a measurement was never reinstated: D13 made the gap
permanent policy, so this bundle is not experimental, it is current.
Measured 2026-09-05 by counting UTF-8 bytes in `dist/` and dividing by four,
the same approximation `test/harness/empirical-checklist.md` uses for its E12
cost estimate. This is an estimate, not a token count: the real count comes
from the provider's usage report (persona section 7.3), not a client-side
guess, and belongs here once a live run reports it. Recompute after any
change to `src/ROUTING.md`, `src/LIFECYCLE.md`, `src/WORKER_PERSONA.md` or
`src/commands/workers.md` and a `dist/` rebuild.

| Artefact | Paid on | Chars | Tokens (chars / 4) |
| :--- | :--- | :--- | :--- |
| `dist/ORCHESTRATOR.md` | every orchestrator turn, once appended to the consumer's `CLAUDE.md` | 11,913 | ~2,978 |
| 15 worker descriptions (`dist/.claude/agents/*.md` frontmatter) | every orchestrator turn, in the Agent tool's subagent_type listing | 2,502 | ~625 |
| One worker definition (`dist/.claude/agents/WORKER_*.md`, persona inlined) | once per worker start, to that worker only | 1,918 to 1,999 (mean 1,948) | ~479 to ~499 (mean ~487) |
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
sees about each cell without opening its definition, about 167 characters
each; a worker definition is a self-contained persona so a worker needs no
file read at startup (D3); `/workers` is invoked rather than persistent, so
its cost is per call rather than per turn.

The largest single addition to date is the clarify rule (`ROUTING.md` section
1.1, D10), about 1,810 characters or 452 tokens of the figure above, a rise of
roughly 18 percent in what every orchestrator turn pays. What it buys: E12
measured an opus orchestrator answering clarify on 9 of 17 fixtures, 5 of them
with a correct axis assessment, which is a whole wasted turn each time plus the
user's attention. If a measured run under this rule shows the clarify rate is
no better than it was without it, this section is the first thing to prune.

What is not measured here: actual provider token counts (characters per token
vary by tokeniser and content), the Claude Code system prompt itself, and
anything the orchestrator reads while assessing a task, such as the task text
or a file it opens. Those sit outside this repository's control.
