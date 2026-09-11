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
| E15 | In `orchestrator-scratch`: `claude -p "<assess the axes for a task, then run python3 probes/e15_fake_route.py with the answers, relay its output verbatim>" --output-format json --permission-mode acceptEdits --allowedTools "Bash(python3 *)"` | Whether the reply matches the script's actual output exactly, and whether it works at all without the permission flags | Whether a Bash-invoked routing script is a workable mechanism for the two-stage classifier (`docs/PLAN.md` Stage 5); done 2026-09-11, workable only with the permission flags shown, silently blocked without them |
| E16 | `python3 probes/e16_cache_prefix.py` in `orchestrator-scratch`, three parallel `claude -p` calls sharing an identical static prefix | `cache_read_input_tokens` and `cache_creation_input_tokens` per call | Whether prompt caching is shared across genuinely parallel `claude -p` processes; done 2026-09-11, no sharing observed, each call created its own cache entry independently |
| E17 | Configure a `PreToolUse` hook on `Write` in `orchestrator-scratch` (`probes/e17_reject_hook.py`), then `claude -p` spawning a worker whose task would trip it | Whether the file was created, and whether the top-level call reports a permission denial or the hook's own block | Whether a hook reaches a Task-tool-spawned worker's own tool calls; done 2026-09-11, confirmed it does |
| E18 | `python3 probes/e18_concurrency.py` in `orchestrator-scratch`, N = 3, 6, 12 parallel `claude -p` calls | Completion rate, reply correctness, wall clock, and any rate-limit or failure detail | The largest N of parallel `claude -p` processes observed to work cleanly from one parent; done 2026-09-11, 12 of 12 clean with no rate-limit failures |
| E19 | From a live session, use `ToolSearch` to look for a `/tasks`-equivalent tool; separately, spawn a worker with several tool calls and try to observe its row while it runs | Whether a callable tool exists, and whether the row is visible to the agent itself | Whether `LIFECYCLE.md`'s "report from `/tasks`" and `src/commands/workers.md`'s "run `/tasks`" describe something an agent can execute, or only something a human watching the panel can do (`docs/FINDINGS.md`, "Contradicted by empirical check, 2026-09-11"; done 2026-09-11, confirmed no such tool exists) |
| E20 | Run one benchmark task at a deliberately undersized cell (T7 or T11 at `worker-sonnet-low` is the natural pair, since both are built to need more), then `grep -c compact_boundary` on that worker's `agent-{agentId}.jsonl`. Repeat at a cell that clears the task. | Whether the entry appears, and whether it appears only when the cell was in fact too small | P29 (`docs/PREMISES.md`): whether `compact_boundary` is the reliable undersizing signal `CLAUDE.md` claims. Stage 5 needs this before it designs the two-axis variant, which proposes replacing the whole horizon axis with this one signal |
| E21 | In `orchestrator-scratch`, give an orchestrator a task whose first worker will fail its acceptance criteria, let it escalate per `ROUTING.md` section 4, then look for any machine-readable trace of the escalation: a field in the parent session's JSON, a marker in either transcript, or a relationship between the two `agent-{agentId}` records | Whether an escalation is detectable without reading prose, and if so from where | Whether the escalation rate can be counted automatically. `ROUTING.md` section 4 requires the orchestrator to record every escalation and nothing collects the record; it is one of the two missing terms in cost per solved task (`docs/PREMISES.md`, metric interrogation) |
| E22 | Time and price a minimal schema-forced classification call: `claude -p --model sonnet --effort low` with a short task, asked for three enumerated axis values and nothing else, ten times, recording `total_cost_usd` each time. Corrected 2026-09-11 (E23): a bare `--model sonnet` call has no way to request low effort without the separate `--effort` flag this same finding confirms exists | Mean and spread of cost per verdict | The `R` term the whole cost thesis turns on (`docs/PREMISES.md`, dissolution check). At USD 0.1645 the table can never beat B0; at USD 0.02 it needs a 12 percent floor-failure rate. Stages 5 and 6 need the real figure before choosing a mechanism |
| E23 | `claude -p --help`, free, no session started | Whether `--effort <level>` exists as a top-level session flag, distinct from a subagent's frontmatter effort | Done 2026-09-11: confirmed, `--effort` accepts `low, medium, high, xhigh, max` for the current session. Corrects a defect in the Stage 5 pre-registration (`test/results/2026-09-11-classifier-preregistration.md`), which named a configuration "sonnet-low" without checking whether a bare `--model` value could express effort at all; it cannot, `score_routing.py` needed a separate `--effort` argument, added in the same commit |

Cost of E12, with assumptions stated so you can substitute your own: one
orchestrator turn per fixture, 17 fixtures, about 3K tokens of bundle text
(ROUTING.md, LIFECYCLE.md and fifteen descriptions at four characters per
token) plus the Claude Code system prompt, assumed 15K to 20K tokens, and
under 100 output tokens per verdict. That is roughly 350K input tokens per
model; multiply by your per-million input price for sonnet and again for opus.
The `total_cost_usd` field, if `claude -p` reports it, replaces this estimate.

Items E3, E4 and E5 spend worker tokens; keep the tasks trivial. E8 and E11
must run in a scratch project so the probe definition never enters `dist/`.
