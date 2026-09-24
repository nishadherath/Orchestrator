# CLAUDE.md

Read `ORCHESTRATOR.md` before delegating any task. Load only the relevant
section of `ORCHESTRATOR-REFERENCE.md` when the core document directs you to it.

## Required retrieval

Every task, session, agent and subagent starts with `graft_check_freshness`.
Use scoped Graft search, file API and call graph tools before broad repository
reads. Direct reads remain appropriate for exact edits, tests and unindexed
documents. If Graft is unavailable, repair or report the connection before
repository discovery. Put this rule and the repository root in every handover;
each child verifies its own access. The bundle README describes installation.

## Managed worker records

Before using a legacy routing or worker launch path after a bundle rollback,
run `python3 tools/task_executor.py --audit --project .` while that tool is
installed. An open or unsettled `.claude/task-executor-v2/` root blocks another
launch of the same work. Preserve its journal and budget, reconcile the writer
and charge, then use the authorised continuation path. If the older bundle no
longer has the audit tool, inspect those records before any relaunch.
The optional managed child plan shares this root balance. Consult
`MANAGED-DELEGATION.md` before using it; the current live adapter reports child
isolation as unproven and rejects managed delegation.

## Handoffs

Before changing model or effort, starting a fresh session, or launching any
agent or subagent, create and validate a concise file under `handoffs/`:

```text
python3 tools/handoff.py new --slug <name> --reason <model-change|effort-change|spawn> \
  --to-model <sonnet|opus|fable> --to-effort <low|medium|high|xhigh|max> \
  [--cell <resolved-worker>]
python3 tools/handoff.py check handoffs/<file>
```

Fill every prose section and retain the computed workload projection. Add a
dated direct API cost range and elapsed-time range for the session work. Notify
the operator before any switch or launch they must perform. The receiving
session reads the named handoff first. `ORCHESTRATOR.md` contains the operating
contract; its reference-loading section identifies when more detail is needed.
