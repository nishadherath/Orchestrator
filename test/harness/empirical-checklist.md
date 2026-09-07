# Empirical checklist

The checks that need a live Claude Code session. `check.py` cannot run these
and reports invariant 7 as SKIP until they are done. Each item names what to
run, what to record, and which `docs/FINDINGS.md` row it settles. Record the
outcome in `docs/FINDINGS.md` with the version from E1, and log the session in
`test/results/<date>-empirical.md`.

Preconditions for every item: a consumer project (not this repository) with
the `dist/` bundle installed per `src/README.md`; `CLAUDE_CODE_EFFORT_LEVEL`,
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
unset in the shell that starts the session; the session started on Sonnet
unless the item says otherwise.

| Item | Run | Record | Settles |
| :--- | :--- | :--- | :--- |
| E1 | `claude --version` | The version string, at the top of FINDINGS.md | The version every later row refers to |
| E2 | Spawn `worker-sonnet-low` with "reply with the word ready and stop". Run `/tasks` while it runs. | Model and effort shown on the row | Effort on the `/tasks` row on this version; that routing took effect |
| E3 | Spawn `worker-sonnet-medium` with a task that takes two or three tool calls. `TaskStop` it. `SendMessage` it "continue". | Whether a running row reappears with the same agent ID | Auto-resume on message |
| E4 | Same as E3, but stop it with `x` in the panel. `SendMessage` it. | The exact refusal text, or the resumption | Invariant 7: user-stopped not resumable |
| E5 | Spawn a named worker with "send the word PING to main with SendMessage, then stop". | Whether the message arrives, and how it is addressed | The `main` address |
| E6 | In the orchestrator session, Bash: `echo "[$CLAUDE_SESSION_ID]"` | Empty brackets or a value | `CLAUDE_SESSION_ID`; the `/workers` fallback if empty |
| E7 | While a worker runs: `ls ~/.claude/projects/*/*/subagents/`. Open one `.jsonl`; `grep -c effort`, `grep -c model`. | The path that exists; which of model and effort the transcript records | Transcript path; open question 1 (effort in transcript) |
| E8 | In a scratch project add `.claude/agents/probe-haiku.md` with `model: haiku` and `effort: high`. Spawn it. `/tasks`. Delete it after. | Whether an effort level appears on the row | Invariant 5: haiku has no effort levels |
| E9 | Spawn `worker-sonnet-low` with "list the names of every tool available to you, one per line, then stop". | The list | Whether background workers lose built-in tools; whether `SendMessage` is present |
| E10 | Spawn `worker-sonnet-medium` with "spawn worker-sonnet-low to reply with the word inner, then reply with the word outer plus whatever it returned". | What reaches the orchestrator | Nested summaries only |
| E11 | Start a session in a scratch project with no `.claude/agents/`. Create the directory and one definition mid-session. Ask the session to list available subagent types. | Listed or not, without restart | The startup-only file watcher |
| E12 | From this repository: `python3 test/harness/score_routing.py --project <consumer> --model sonnet --record`, then again with `--model opus`. Review `test/fixtures/routing.jsonl` first and replace `assigned_by` on rows you agree with. | The two results files; the reported cost | Routing appropriateness; open question 6 (orchestrator model) |
| E13 | Give the orchestrator one real task from the consumer project's backlog. Let it route and run. | Bundle version, task, cell chosen, whether you agreed, `/tasks` row, tokens | The dogfooding log the charter requires |
| E14 | `python3 test/harness/cost_rollup_check.py --project <consumer> --reps 2 --record` | The two `total_cost_usd` means and the printed ratio | Whether a spawned worker's cost reaches the parent `total_cost_usd` (`test/harness/benchmark.py`'s whole cost measurement depends on it, still unverified) |

Cost of E12, with assumptions stated so you can substitute your own: one
orchestrator turn per fixture, 17 fixtures, about 3K tokens of bundle text
(ROUTING.md, LIFECYCLE.md and fifteen descriptions at four characters per
token) plus the Claude Code system prompt, assumed 15K to 20K tokens, and
under 100 output tokens per verdict. That is roughly 350K input tokens per
model; multiply by your per-million input price for sonnet and again for opus.
The `total_cost_usd` field, if `claude -p` reports it, replaces this estimate.

Items E3, E4 and E5 spend worker tokens; keep the tasks trivial. E8 and E11
must run in a scratch project so the probe definition never enters `dist/`.
