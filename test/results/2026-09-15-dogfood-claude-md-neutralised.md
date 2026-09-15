# Dogfood note: orchestrator-scratch's CLAUDE.md neutralised

Per `CLAUDE.md`'s Dogfooding protocol and `docs/PLAN-5.md` Stage B.1
(`docs/COMPACTION-DESIGN.md` section 14.1 point 3). Project:
`orchestrator-scratch`.

Before:

```
Read ORCHESTRATOR.md before delegating any task.

This is a scratch consumer project used only to run the Claude Code
empirical checks in test/harness/empirical-checklist.md from the
Orchestrator repository. It has no application code of its own.
```

After:

```
Read ORCHESTRATOR.md before delegating any task.

This is a scratch project with no application code of its own.
```

Why: Plan 4 Stage D's worker read this exact sentence and quoted it back
as part of its refusal, treating "empirical checks... from the
Orchestrator repository" as proof the task was synthetic
(`docs/FINDINGS.md`, "Plan 4 Stage D"). The pointer line to
`ORCHESTRATOR.md` stays, since routing depends on it; everything naming
this repository, a plan, or a testing purpose is gone.

No other file in `orchestrator-scratch` was touched by this note.
