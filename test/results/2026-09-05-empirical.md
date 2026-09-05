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
| E4 | Spawned `worker-sonnet-low` with a two-tool-call task; stopped via `x` in the panel; `SendMessage` "continue" | Orchestrator received: "Agent ... was stopped by the user and won't be resumed. Treat its work as cancelled; only launch a new agent if the user explicitly asks." No running row reappeared | The `x`-stopped half of invariant 7; invariant 7 is now fully confirmed |
| E5 | Spawned named worker `ping-test` (worker-sonnet-low) with "send the word PING to main using SendMessage, then stop" | A distinct "Message from @ping-test" notification arrived, separate from the completion summary | `main` is a working `SendMessage` address; arrival is labelled by sender name, not literally "main" |
| E6 | `echo "[$CLAUDE_SESSION_ID]"` in the orchestrator session | Printed `[]`, empty | `CLAUDE_SESSION_ID` unset; the `/workers` fallback path (most recent session directory) is the one actually used |
| E7 | Spawned worker-sonnet-medium with a three-file-read task; while running, `ls ~/.claude/projects/*/*/subagents/`, then `grep -c` on its `.jsonl` | 8 `agent-{agentId}.jsonl` files present (accumulated across the session), each with a sibling `agent-{agentId}.meta.json`; the running worker's `.jsonl` had 6 `effort` matches and 7 `model` matches | Transcript path confirmed; open question 1 resolved (effort is in the transcript); the `.meta.json` sibling is a new, previously undocumented fact |

Remaining checklist items (E8-E13) not yet run this session.
