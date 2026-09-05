# Findings: verified behaviour of Claude Code

Every platform claim this repository depends on is listed here with the date it
was checked, the source, and where the claim is used. "Documentation" means the
pages under `code.claude.com/docs` as read on the date given. Documentation is
evidence of intent. The `/tasks` row and a worker transcript on the installed
version are evidence of behaviour. A claim moves from unverified to verified
only on one of those two, and the entry names the version it was seen on.

Installed version at the last empirical check: 2.1.245, checked 2026-09-05
(E1, `test/results/2026-09-05-empirical.md`).

## Verified against documentation, 2026-09-05

| Claim | Used in | Source |
| :--- | :--- | :--- |
| Subagent frontmatter `effort` accepts `low`, `medium`, `high`, `xhigh`, `max`, model-dependent | `src/agents/*` | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| `fable` is a documented `model` alias alongside `sonnet`, `opus`, `haiku` | `src/agents/*` | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| `CLAUDE_CODE_EFFORT_LEVEL` overrides frontmatter `effort` | `CLAUDE.md` invariant 3, `src/README.md` | [model-config](https://code.claude.com/docs/en/model-config) |
| `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` makes every subagent ignore its `model` frontmatter | `CLAUDE.md` invariant 4, `src/README.md` | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| `CLAUDE_CODE_SUBAGENT_MODEL` is the default for subagents without a `model` | `src/README.md` | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| Model resolution order: per-invocation `model`, then frontmatter, then the subagent default | `CLAUDE.md` invariant 2, `src/ROUTING.md` section 3 | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| With `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, teammates inherit the lead's effort level | `CLAUDE.md` invariant 1, `src/README.md` | [agent-teams](https://code.claude.com/docs/en/agent-teams) |
| At most 20 subagents run concurrently, configurable | `src/ROUTING.md` section 5, `src/README.md` | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| Subagents nest up to 3 levels deep by default | `src/ROUTING.md` section 5, `src/README.md` | [sub-agents](https://code.claude.com/docs/en/sub-agents) |
| A model blocked by the `availableModels` allowlist is substituted, not failed | `CLAUDE.md` invariant 6, `src/README.md` | [agent-teams](https://code.claude.com/docs/en/agent-teams) |
| `/tasks` shows the model and effort level each subagent ran on, from v2.1.243 | `CLAUDE.md`, `src/README.md`, `src/commands/workers.md` | [changelog](https://code.claude.com/docs/en/changelog) |

## Empirically verified, 2026-09-05

Confirmed by a live `/tasks` row or command output on the installed version, not just by documentation. See `test/results/2026-09-05-empirical.md` for the session this was run in.

| Claim | Evidence | Settles |
| :--- | :--- | :--- |
| Effort level appears on the `/tasks` row at v2.1.245 | Row read "Sonnet 5 (low)" for `worker-sonnet-low` spawned with a trivial task | E2 |
| `worker-sonnet-low` actually runs on sonnet at low effort with the env unset | Same `/tasks` row | E2; invariants 2 and 3 |
| A `TaskStop`-stopped worker auto-resumes on `SendMessage` | `worker-sonnet-medium` stopped mid-task via `TaskStop`, then messaged "continue": a running row reappeared under the same agent ID | E3; half of invariant 7 (the `TaskStop` half) |

## Contradicted by documentation, 2026-09-05

| Claim as previously written | What the documentation says | Action taken |
| :--- | :--- | :--- |
| Effort appears on the `/tasks` row from v2.1.242 | The changelog entry is v2.1.243 | Corrected in `CLAUDE.md` and `src/README.md` |
| Fork mode is on by default and gives workers a reduced built-in tool set | A fork inherits the parent's full conversation context; no reduced tool set is described | `src/README.md` bullet rewritten; the tool-set claim is now listed below as unverified |

## Unverified, 2026-09-05

Not found in the documentation. Each is stated as unverified in the sentence
that uses it. Move an entry up only with a `/tasks` row, a transcript, or a
reproducible command on a named version.

| Claim | Used in | How to verify |
| :--- | :--- | :--- |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes the nesting depth | `src/README.md` | Set it to 1, spawn a worker that spawns a worker, observe the refusal |
| A worker can `SendMessage` to the orchestrator addressed as `main` | `src/LIFECYCLE.md`, `src/WORKER_PERSONA.md` | Spawn a named worker whose only instruction is to message `main`; observe arrival |
| A worker stopped by the user with `x` refuses messages and cannot be resumed | `src/LIFECYCLE.md`, `CLAUDE.md` invariant 7 | Stop a worker from the panel, message it, record the response text |
| `CLAUDE_SESSION_ID` is set inside a session | `src/commands/workers.md` | `echo $CLAUDE_SESSION_ID` from Bash inside a session |
| Worker transcripts live at `~/.claude/projects/{project}/{sessionId}/subagents/agent-{agentId}.jsonl` | `src/LIFECYCLE.md`, `src/commands/workers.md`, `CLAUDE.md` | `ls` the path while a worker runs; note what the file records about model and effort |
| Haiku has no effort levels | `CLAUDE.md` invariant 5 | Define a haiku worker with `effort: high`; check whether `/tasks` shows an effort level |
| The agents file watcher covers only directories that existed at startup | `src/README.md` | Create `.claude/agents/` mid-session, add a definition, check whether it is listed without restart |
| Background workers run with a reduced built-in tool set | `src/README.md` | Spawn a worker that lists its available tools and reports them |
| Only the top-level worker's summary returns to the orchestrator from nested workers | `src/ROUTING.md` section 5 | Spawn a worker that spawns a worker; compare what returns |
