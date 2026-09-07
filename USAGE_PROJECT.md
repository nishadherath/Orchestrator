# Using this orchestrator in another project

## Get a new project using it

1. Copy `dist/.claude/` into the new project's root, this brings the 15
   worker definitions (`agents/`) and the `/workers` status command. If you
   want every project to have the workers available without copying
   per-project, merge `dist/.claude/agents/` and `dist/.claude/commands/`
   into `~/.claude/` instead.
2. Wire up the routing instructions themselves: append `dist/ORCHESTRATOR.md`
   to the project's `CLAUDE.md`, or copy it alongside `CLAUDE.md` and add the
   line "Read ORCHESTRATOR.md before delegating any task." This step is what
   actually makes a Claude Code session consult the routing table, copying
   the agent definitions alone doesn't do that.
3. Run `python3 preflight.py` from the new project's root. It checks the
   settings that silently break routing without erroring:
   `CLAUDE_CODE_EFFORT_LEVEL` must be unset, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`
   off, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` off, and `availableModels` must
   permit sonnet, opus, and fable. Any organisation-level effort caps need an
   administrator to confirm separately.
4. One gotcha: if `.claude/agents/` did not exist before you started the
   session, restart Claude Code, a definition added after the session starts
   is not picked up, even after waiting.

## Verify a project is actually orchestrating, not just has the files present

- Spawn something, then run `/tasks` while it is running. Each row shows the
  model and effort level. If either does not match the cell you would expect
  from the task's classification, a substitution happened somewhere (an
  `availableModels` allowlist or a forced subagent model overriding the
  routing).
- Run `/workers` (the bundle's own command) for the fuller picture, it
  cross-checks every running worker's actual model/effort against what its
  `subagent_type` should have produced and says plainly if something has
  been substituted, flags anything running longer than its cell should take
  (a sign of under-provisioning), and reports any partial or failed workers.
- Watch the orchestrator's own narration: per `ROUTING.md`, it is supposed to
  state the assessment and the worker it is routing to in the same line,
  before spawning ("structured, short, contained, routing to
  worker-sonnet-medium"). If that line never appears, the session likely is
  not reading `ORCHESTRATOR.md`/`ROUTING.md` at all, check step 2 above.
- Having `.claude/ORCHESTRATOR_VERSION` present only proves the bundle is
  installed, not that it is being followed, the checks above are what
  actually confirm routing is happening.
