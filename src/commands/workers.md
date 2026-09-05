---
description: Collated status of every worker agent in this session
---

Report the state of all worker agents, running and finished.

Gather from these sources, in order:

1. Run `/tasks` and read every row. Each row carries the worker's name, the
   model it is running on, and its effort level where the definition sets one.
2. Your own lifecycle tracking for workers whose rows have already cleared from
   the panel. A successful worker's row is removed immediately; a failed or
   stopped worker's row persists for 30 seconds.
3. The transcript directory, for anything you cannot account for from the above:

   ```
   ls -la ~/.claude/projects/*/`basename $CLAUDE_SESSION_ID`/subagents/ 2>/dev/null
   ```

   Each `agent-{agentId}.jsonl` is one worker. File mtime gives last activity.
   A `compact_boundary` system entry means that worker auto-compacted, which is
   a signal its task was larger than its cell was sized for.

Present one table, sorted running first, then stopped, then done:

| Name | Worker cell | State | Last activity | Task |
| :--- | :--- | :--- | :--- | :--- |

Then add, in at most four lines:

- Count of workers currently running against the concurrency limit of 20.
- Any worker whose `/tasks` row shows a model or effort level that differs from
  what its `subagent_type` should have produced. This means a substitution
  happened, from an `availableModels` allowlist or a forced subagent model, and
  the routing is not doing what you think it is. Say so plainly.
- Any worker in `partial` or `failed` state, with what it would take to resume.
- Any worker running longer than its cell predicts, which is evidence the
  routing under-provisioned it.

Do not summarise the workers' findings here. This command reports on the fleet,
not on the work.
