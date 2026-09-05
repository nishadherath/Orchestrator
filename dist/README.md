# Worker orchestration setup

Install from the `dist/` bundle, never from `src/`. The bundle is versioned in
`.claude/ORCHESTRATOR_VERSION`; quote that version in any report.

## Layout of the bundle

```
.claude/
  agents/
    WORKER_sonnet_low.md ... WORKER_fable_max.md   (the 15 worker definitions)
  commands/
    workers.md                                      (the /workers status command)
  ORCHESTRATOR_VERSION                              (date and source commit)
ORCHESTRATOR.md                                     (ROUTING.md + LIFECYCLE.md)
README.md                                           (this file)
```

The shared worker persona is inlined into every definition, so the consumer
project needs no separate persona file.

Copy `.claude/` into the consumer project (or merge `agents/` and `commands/`
into `~/.claude/` to make the workers available everywhere). Then either append
`ORCHESTRATOR.md` to the project's `CLAUDE.md`, or copy it beside `CLAUDE.md`
and add the line "Read ORCHESTRATOR.md before delegating any task."

If `.claude/agents/` did not exist before your current session started, restart
Claude Code. The file watcher appears to cover only directories that existed
at startup; this is observed behaviour, unverified against the documentation
as of 2026-09-05.

## Settings that will break this

Verify each before relying on the routing.

| Setting | Required state | Why |
| :--- | :--- | :--- |
| `CLAUDE_CODE_EFFORT_LEVEL` | unset | Overrides frontmatter `effort` on every worker. Frontmatter overrides the session level but not this variable. |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` | unset or `0` | When on, Claude Code ignores the `model` field of every worker definition and flattens the whole scheme onto one model. |
| `CLAUDE_CODE_SUBAGENT_MODEL` | unset | A default for workers without a model. Harmless here since every worker sets one, but leave it clear to avoid confusion. |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | unset | With agent teams on, a named subagent launches as a teammate instead, and teammates follow the lead's effort level rather than their own definition. Naming is required for addressability, so this variable silently defeats the effort routing. |
| `availableModels` | must permit sonnet, opus, and fable | A blocked model is substituted, not failed. Interactive sessions warn; check the warning rather than assuming. |
| Organisation effort limits | check with your admin | Enterprise roles can cap effort per model. A capped level runs at the cap, silently under `json` output or in background agents. |

## Verifying it works

Spawn one worker and run `/tasks` while it runs. The row shows the model and,
because the definition sets `effort`, the effort level. If either differs from
the cell you routed to, a substitution happened. Requires Claude Code v2.1.243
or later for the effort level to appear on the row.

## Known limits

- No true pause. Stop and resume only, and a user-stopped worker cannot be
  resumed at all. The user-stopped case is observed behaviour, unverified
  against the documentation as of 2026-09-05.
- 20 concurrent workers per session. Resuming a finished worker takes a fresh
  slot without checking the limit, so resumes can push you past it.
- Workers nest three layers deep by default. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`
  is said to change this, but it is not among the documented environment
  variables as of 2026-09-05; verify before relying on it.
- Workers run as background subagents. The documentation describes a fork as
  inheriting the parent's full conversation context and says nothing about a
  reduced tool set, so the claim that background workers lose built-in tools
  is unverified as of 2026-09-05. Confirm `SendMessage` is in a worker's tool
  list before relying on the return channel (see `docs/FINDINGS.md`).
- Routing is a judgement made by a model reading a rubric, not a deterministic
  classifier. Expect to tune the table against your own task mix rather than
  trusting it out of the box.
