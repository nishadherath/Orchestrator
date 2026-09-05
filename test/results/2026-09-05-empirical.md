# Empirical session 2026-09-05

Consumer project: `orchestrator-scratch` (scratch project, not this repository).
`dist/` installed per `src/README.md` from commit `7437562` (bundle version
`2026-09-05-1708054`). Preconditions checked before starting: `CLAUDE_CODE_EFFORT_LEVEL`,
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
unset in the shell; session started on Sonnet. Jeb ran the session directly
(the Cowork VM's `claude` binary refuses all execution, `-p` included, so the
live checks cannot run from that sandbox).

| Item | Run | Observed | Settles |
| :--- | :--- | :--- | :--- |
| E1 | `claude --version` | `2.1.245 (Claude Code)` | The version every later row refers to |
| E2 | Spawned `worker-sonnet-low` with "reply with the word ready and stop"; read `/tasks` while it ran | Row read "Sonnet 5 (low)" | Effort appears on the `/tasks` row at v2.1.245 (above the v2.1.243 threshold); `worker-sonnet-low` routed to sonnet at low effort as its definition sets, confirming invariants 2 and 3 held with the env unset |
| E3 | Spawned `worker-sonnet-medium` with a four-tool-call task; `TaskStop` while running; `SendMessage` "continue" | A running row reappeared under the same agent ID | Auto-resume on message for the `TaskStop` half of invariant 7 |

Remaining checklist items (E4-E13) not yet run this session.
