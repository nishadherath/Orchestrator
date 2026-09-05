# Recurring token cost

Bundle version `2026-09-05-c230619` (`dist/.claude/ORCHESTRATOR_VERSION`).
Measured 2026-09-05 by counting UTF-8 bytes in `dist/` and dividing by four,
the same approximation `test/harness/empirical-checklist.md` uses for its E12
cost estimate. This is an estimate, not a token count: the real count comes
from the provider's usage report (persona section 7.3), not a client-side
guess, and belongs here once a live run reports it. Recompute after any
change to `src/ROUTING.md`, `src/LIFECYCLE.md`, `src/WORKER_PERSONA.md` or
`src/commands/workers.md` and a `dist/` rebuild.

| Artefact | Paid on | Chars | Tokens (chars / 4) |
| :--- | :--- | :--- | :--- |
| `dist/ORCHESTRATOR.md` | every orchestrator turn, once appended to the consumer's `CLAUDE.md` | 9,320 | ~2,330 |
| 15 worker descriptions (`dist/.claude/agents/*.md` frontmatter) | every orchestrator turn, in the Agent tool's subagent_type listing | 2,462 | ~615 |
| One worker definition (`dist/.claude/agents/WORKER_*.md`, persona inlined) | once per worker start, to that worker only | 1,918 to 1,968 (mean 1,946) | ~480 to ~492 (mean ~486) |
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
sees about each cell without opening its definition, about 164 characters
each; a worker definition is a self-contained persona so a worker needs no
file read at startup (D3); `/workers` is invoked rather than persistent, so
its cost is per call rather than per turn.

What is not measured here: actual provider token counts (characters per token
vary by tokeniser and content), the Claude Code system prompt itself, and
anything the orchestrator reads while assessing a task, such as the task text
or a file it opens. Those sit outside this repository's control.
