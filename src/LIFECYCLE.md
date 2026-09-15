# Worker lifecycle and communication

This file governs the orchestrator persona spawning a worker via the Task
tool, inside one Claude Code session. It does not govern
`tools/system_controller.py`'s role calls (`docs/PLAN.md` Stage 10): those
are `claude -p` subprocess invocations, each a fresh process with no
session left behind to resume. `src/System/ROLES.md`'s "Isolation" section
says why the two mechanisms need separate treatment rather than one being
a special case of the other.

## What you can and cannot do

Claude Code supports **start, message, stop, and resume**. It does not support
suspending a running worker mid-turn and holding it there. Treat "pause" as
stop-then-resume, and be aware the two stop paths differ:

- A worker **you** stop with `TaskStop` auto-resumes when you send it a message.
- A worker **the user** stops, with `x` in the panel or `/tasks`, does not
  auto-resume. A message to it is refused and you are told it was cancelled. To
  continue that work you must spawn a fresh worker. The split between the two
  stop paths is observed behaviour, unverified against the documentation as of
  2026-09-05.

## States

Track each worker in one of these states and keep the list current:

| State | How it arises |
| :--- | :--- |
| `running` | Spawned, working. |
| `awaiting-permission` | Blocked on a permission prompt surfaced in this session. |
| `stopped-by-me` | You called `TaskStop`. Resumable by message. |
| `stopped-by-user` | User pressed `x`. Not resumable. |
| `partial` | Hit its `maxTurns` limit. Output marked partial; resumable. |
| `failed` | Ended on an API error. Last output is preserved. |
| `done` | Returned its summary. Still resumable by message. |

## Bidirectional channel

`SendMessage` is the channel in both directions. It does not require agent teams
to be enabled.

- **You to worker**: `SendMessage` with the worker's `name` or agent ID as `to`.
  Use it to redirect mid-task, supply information the worker asked for, tighten
  scope, or resume a completed worker with follow-up work. The worker treats
  your message as normal task direction and acts within its own permission
  settings.
- **Worker to you**: the worker uses `SendMessage` back to `main` (the `main`
  address is unverified against the documentation as of 2026-09-05). For a worker
  to have this channel it needs `SendMessage` in its tool pool, and it needs to
  know the roster, which is injected at startup only when at least one other
  agent in the session is named. Name every worker you spawn.
- A completed or self-stopped worker auto-resumes in the background on receiving
  a message. No new Agent call is needed, and resuming preserves the worker's
  full history: previous tool calls, results, and reasoning. Auto-resume is
  observed behaviour, unverified against the documentation as of 2026-09-05.

Two limits hold regardless of who sends a message: no agent message counts as
approval for a pending permission prompt, and no agent message can change a
worker's permission settings, model, effort, or configuration.

## Addressing rules

- Prefer the agent ID over the name when precision matters. You receive the ID
  when the worker completes.
- Names are checked: if a newer agent has taken a name, the send is refused
  rather than misdelivered, and you are told which agent now holds it.
- Transcripts persist per session at
  `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl`
  and survive compaction of this conversation. The path is observed, not
  documented, as of 2026-09-05; confirm it on your version.

## Re-running the same task

To re-run a task from scratch rather than continue it, spawn a new worker with
the same handover prompt and a new name. Resuming continues history; it does not
restart. If the point of the re-run is a clean attempt, resuming is the wrong
tool.

A per-invocation model, if one were ever passed, persists across resume. This is
another reason never to pass one.

## Reporting state

When asked for status, report from `/tasks` plus your own tracking, never from
memory alone. `/tasks` names the model on each worker's row and adds the effort
level when the worker's definition sets one, which is the ground truth for
whether routing took effect.

## Handoffs

A worker session cannot change its own model or effort mid-run, and a
completed worker's history does not transfer to a fresh one. Two events
therefore need a handoff file under `handoffs/` before you stop: your own
session's model or effort must change, or you are about to launch a
top-level agent that itself needs a different model or effort than yours
(a subagent Task-tool spawn does not qualify; its own worker definition
already sets its cell). Write the file with `tools/handoff.py new`
(`docs/PLAN-2.md` Stage 3) rather than by hand: it fixes the ten-heading
contract and computes the cost and time projection lines from
`src/cost_table.json`, or from the project's own
`.claude/routing-ledger.jsonl` once it has enough entries, rather than
leaving them to be guessed. Fill in the remaining prose sections yourself
(the goal, decisions made, verified facts, and so on): the tool only
guarantees the skeleton is complete, not that it is true. Run
`tools/handoff.py check <file>` before handing off, and do not stop until
it passes.

The fresh session's first action is to read the handoff file named to it,
not to re-derive context from the conversation history: it exists
precisely so the new session does not need that history.
