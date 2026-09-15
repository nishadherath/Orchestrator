# Empirical session 2026-09-11

`docs/PLAN.md` Stage 2. Consumer project: `orchestrator-scratch` (scratch
project, not this repository). `dist/` installed, bundle
`2026-09-07-af94deb`, current with `src/`. Preconditions checked before
starting: `CLAUDE_CODE_EFFORT_LEVEL`, `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`,
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` and `CLAUDE_CODE_SUBAGENT_MODEL`
unset in the shell; `claude --version` 2.1.263. Interactive checks (E2, E4,
E5, E7, E19) were run by Jeb directly, in a live session with cwd
`orchestrator-scratch`, since the session driving this stage has no way to
become an agent in a different project's context. Spend items (E12's parse
half, E15 through E18) were run by Jeb per `CLAUDE.md`'s rule that any
`claude -p` spend is started by Jeb, not the session; commands were
prepared with real local paths by the session driving this stage.

| Item | Run | Observed | Settles |
| :--- | :--- | :--- | :--- |
| E1 | `claude --version` | `2.1.263 (Claude Code)` | The version every row in this session refers to |
| E2 | Spawned `worker-sonnet-low` as `ready-check` with "reply with the word ready and stop" | Finished in 1.6 seconds, too fast for the agent driving the spawn to observe any live row; no callable equivalent of `/tasks` exists for an agent to check anyway (see E19) | Not re-verified on 2.1.263: needs a human watching `/tasks` live during a task with enough tool calls to leave a visible window, which this round did not attempt |
| E4 | Spawned `worker-sonnet-medium` as `stop-resume-check` (agent `a6d6f3d5f66a243dc`) with a three-step task; `TaskStop`'d (notification: `status: killed`); `SendMessage`'d "continue" | `ListAgents` showed a running row reappear under the identical agent ID; the worker finished normally, itself reporting the interruption | `TaskStop`-then-`SendMessage` resume confirmed unchanged on 2.1.263, via `ListAgents` rather than `/tasks` |
| E5 | Spawned `worker-sonnet-low` as `ping-check` with "send the word PING to main with SendMessage, then stop" | A distinct "Message from @ping-check" notification arrived, separate from the completion summary | A named worker's `SendMessage` to `main` confirmed unchanged on 2.1.263 |
| E7 | Spawned `worker-sonnet-medium` as `transcript-check` (agent `a3d19e886f017abba`); read its `.jsonl` and `.meta.json` | `.jsonl` contains `"model":"claude-sonnet-5"` and `"effort":"medium"`; `.meta.json` carries only `agentType`, `name`, `description`, `toolUseId`, `spawnDepth`, no model or effort | Confirmed unchanged on 2.1.263, and sharper than the original: effort and model live specifically in the `.jsonl`, never the sidecar |
| E12 (parse half) | `score_routing.py --project orchestrator-scratch --model opus --only F01 --record`, run twice minutes apart | Both runs: `worker-sonnet-low` expected and chosen, exact agreement. Second run collided on filename with the first and landed on the `-2` variant automatically. Cost USD 0.1974 then USD 0.0852 | `claude -p --output-format json` field parsing confirmed unchanged on 2.1.263; incidentally re-confirms `unique_path` (D34) and sequential-run caching |
| E15 | Attempt 1, bare `claude -p` with no permission flags, instructed to run `probes/e15_fake_route.py` for its own axis assessment | Three identical `permission_denials` on the same Bash command; gave up, stated its assessment inline ("sensitivity=structured, horizon=short, blast=contained") instead of running the script | Confirms the existing "`claude -p` starts in Manual permission mode" finding still holds on 2.1.263 |
| E15 (retry) | Attempt 2, same task with `--permission-mode acceptEdits --allowedTools "Bash(python3 *)"` | Zero permission denials, zero subagents spawned; reply was exactly `worker: PROBE-STRUCTURED-SHORT-CONTAINED`, an exact match | A Bash-invoked routing script is workable headlessly and faithfully relayed, given the correct permission flags |
| E16 | `python3 probes/e16_cache_prefix.py`: three parallel `claude -p` calls, identical ~4,536-character static prefix | All three: `cache_creation_input_tokens` 18,609 / 18,607 / 18,609 (near-identical, not falling); `cache_read_input_tokens` 23,994 on all three (a separate, pre-existing layer) | No cross-process cache sharing observed between genuinely parallel calls on an identical prefix |
| E17 | Configured `probes/e17_reject_hook.py` as a `PreToolUse` hook on `Write`; `claude -p` spawned `worker-sonnet-low` with a task to write a file containing the hook's forbidden marker | File never created; top-level call reported zero `permission_denials`; worker's relayed report described the exact hook rejection message | A `PreToolUse` hook does reach a Task-tool-spawned worker's own tool calls |
| E18 | `python3 probes/e18_concurrency.py`: N = 3, 6, 12 parallel `claude -p` calls each asking for a distinct number back | 3/3, 6/6, 12/12 completed without error, exact expected reply every time; wall clock 13.4s, 13.2s, 19.1s | At least 12 parallel `claude -p` processes from one parent complete cleanly with no observed rate-limit failures, at this scale |
| E19 (new, unplanned) | `ToolSearch` for a `/tasks`-equivalent tool from a live session; observed that E2's task completed and cleared the panel before it could be read | No matching tool found; a successful row clears the panel the instant the task completes | No agent session, including the orchestrator, can invoke or read `/tasks` itself; it is a terminal-only panel a human must watch live. Contradicts `LIFECYCLE.md`'s "report from `/tasks`" and `src/commands/workers.md`'s "run `/tasks`", both of which instruct the orchestrator to do something it cannot do; flagged for the next stage that touches either file |

All probe scripts (`probes/e15_fake_route.py`, `probes/e16_cache_prefix.py`,
`probes/e17_reject_hook.py`, `probes/e18_concurrency.py`, `probes/README.md`,
`probes/settings.local.json.snippet`) live in `orchestrator-scratch`, not
this repository, and are throwaway: safe to delete once this stage's
findings are recorded, which they now are. The `PreToolUse` hook installed
for E17 and the `probe-e17.txt` non-file it was meant to prevent should be
removed from `orchestrator-scratch/.claude/settings.local.json` after this
session, so it does not affect later stages' own live checks.
