---
description: Collated status of every worker agent in this session
---

Report the state of all worker agents, running and finished.

Run `python3 preflight.py --status --json` first. Use its routing,
acceptance, cost, prior and Graft fields as the durable project view. Add
`--explain` when actual-versus-requested model evidence, unresolved attempt
IDs or individual acceptance records are needed. Session agent tools remain
the live source for work that has not reached the ledger yet.

Gather from these sources, in order:

1. `ListAgents`, for every worker you can currently address by name in this
   session.
2. Your own lifecycle tracking for workers no longer in that listing, or
   already cleared from a human's own view of `/tasks` if one is watching.
3. The transcript directory, for anything you cannot account for from the
   above, and for the model and effort level each worker actually ran on
   (the ground truth for whether routing took effect; carried per turn in
   the `.jsonl`, never in the `.meta.json` sidecar):

   ```
   ls -la ~/.claude/projects/*/`basename $CLAUDE_SESSION_ID`/subagents/ 2>/dev/null
   ```

   `CLAUDE_SESSION_ID` is not among the documented environment variables as of
   2026-09-05. If it is unset, use the most recently modified session directory
   under `~/.claude/projects/*/`.

   Each `agent-{agentId}.jsonl` is one worker. File mtime gives last activity.
   A `compact_boundary` system entry means that worker auto-compacted, which is
   a signal its task was larger than its cell was sized for.

No agent session, including yours, can invoke or read `/tasks` itself: it is
a terminal-only interactive panel with no callable equivalent
(`docs/FINDINGS.md`, E19). If a human is watching it, ask them to read a row
back to you rather than reporting one you have not actually seen.

Present one table, sorted running first, then stopped, then done:

| Name | Worker cell | State | Last activity | Task |
| :--- | :--- | :--- | :--- | :--- |

Then add, in at most four lines:

- Count of workers currently running against the concurrency limit of 20.
- Any worker whose transcript shows a model or effort level that differs
  from what its `subagent_type` should have produced. This means a
  substitution happened, from an `availableModels` allowlist or a forced
  subagent model, and the routing is not doing what you think it is. Say
  so plainly.
- Any worker in `partial` or `failed` state, with what it would take to resume.
- Any worker running longer than its cell predicts, which is evidence the
  routing under-provisioned it.

Do not summarise the workers' findings here. This command reports on the fleet,
not on the work.
