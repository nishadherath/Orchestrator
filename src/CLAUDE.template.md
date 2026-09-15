# CLAUDE.md

Read ORCHESTRATOR.md before delegating any task.

## Handoffs

When this session's own model or effort must change, or you are about to
launch a top-level agent that needs a different model or effort than this
session's, write a handoff file under `handoffs/` before stopping:

```
python3 tools/handoff.py new --slug <short-name> --reason model-change \
    --to-model <sonnet|opus|fable> --to-effort <low|medium|high|xhigh|max>
python3 tools/handoff.py check handoffs/<the file it wrote>
```

Fill in the prose sections the tool leaves blank (goal, decisions already
made, verified facts, work completed, unresolved questions, exact next
action) before handing off; `check` refuses a file with an empty or
placeholder section. The tool computes the cost and time projection lines
itself, from `src/cost_table.json` or this project's own
`.claude/routing-ledger.jsonl`; do not estimate them by hand.

The fresh session's first action is to read the handoff file named to it,
not to re-derive context from conversation history. `src/LIFECYCLE.md`
(bundled into `ORCHESTRATOR.md`) has the full rule.
