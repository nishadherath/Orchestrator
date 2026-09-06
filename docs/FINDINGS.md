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
| A worker stopped by the user (`x` in the panel) refuses `SendMessage` and is not resumed | `worker-sonnet-low` stopped via `x`, then messaged "continue"; the orchestrator received: "Agent ... was stopped by the user and won't be resumed. Treat its work as cancelled; only launch a new agent if the user explicitly asks." No running row reappeared | E4; the other half of invariant 7. Invariant 7 is now fully confirmed: `TaskStop` resumes, `x` does not |
| A named worker's `SendMessage` to `main` reaches the orchestrator | Named worker `ping-test` sent "PING" to `main`; a distinct incoming notification "Message from @ping-test" appeared in the orchestrator session, separate from the task-completion summary | E5; `main` is a working address, delivery is labelled by the sender's name on arrival, not literally "main" |
| `CLAUDE_SESSION_ID` is empty in a session's Bash context | `echo "[$CLAUDE_SESSION_ID]"` in the orchestrator session printed `[]` | E6; `src/commands/workers.md`'s documented fallback (most recently modified session directory) is the path actually exercised, not a defensive extra |
| Worker transcript path, and that it records both effort and model | `ls ~/.claude/projects/*/*/subagents/` while a worker ran listed 8 `agent-{agentId}.jsonl` files (accumulated from earlier E1-E6 spawns, not all from one worker), each paired with an undocumented `agent-{agentId}.meta.json`; `grep -c` on the running worker's `.jsonl` found 6 lines matching `effort` and 7 matching `model` | E7; confirms the path, and answers open question 1: effort appears in the transcript, not only the panel |
| A new definition added to an already-existing `.claude/agents/` directory is picked up without restarting the session, but only after a lag, not on the next message | `probe-haiku.md` was absent from the listed subagent types immediately after being written; it and a second file (`probe-sonnet.md`) written moments later both appeared together on the next check | Incidental to E8; bears on open question "the startup-only file watcher" and on E11, which still needs to test a directory that did not exist at startup |
| `SendMessage` is available to a plain, unnamed background worker, and works | An unnamed `worker-sonnet-low` called `SendMessage` to send "test" to `main`; it returned `{"success":true,"message":"Message queued for the main conversation's next turn."}` | E9 (retried with a direct-use task after the self-reported tool list omitted it); resolves `src/README.md`'s "Known limits" worry. New fact: `SendMessage` is queued for the orchestrator's next turn, not delivered mid-turn |
| Only the top-level worker's own reply reaches the orchestrator from a nested spawn, with the inner worker's result folded in, not surfaced separately | `worker-sonnet-medium` spawned `worker-sonnet-low` (reply "inner"), then itself replied "outer" plus what it got back; the orchestrator received exactly "outer inner", one message | E10; nesting to depth 2 works and only one summary surfaces |
| The agents file watcher covers only directories that existed at session startup | In a fresh scratch project with no `.claude/` at all, `.claude/agents/probe.md` created mid-session never appeared in the subagent-type listing, even after a wait. Contrast E8, where a file added to an `.claude/agents/` that already existed at startup did appear, after a lag | E11 (with E8); `src/README.md`'s restart advice is correct only for the never-existed-yet case; an already-existing directory hot-reloads new files on a lag, no restart needed |
| `score_routing.py` runs against a live install; its `claude -p --output-format json` field names (`result`, `total_cost_usd`) are correct | Both a sonnet and an opus orchestrator run parsed all 17 fixtures cleanly | E12; see `test/results/2026-09-05-routing-sonnet.md` and `test/results/2026-09-05-routing-opus.md` |
| A sonnet orchestrator scored higher fixture agreement than an opus orchestrator on the same 17 fixtures, at a fraction of the cost: sonnet 11/17 (USD 0.7623), opus 8/17 (USD 3.5808), one run each | Opus's disagreements were overwhelmingly not misjudgment: on F01, F09, F11, F15 and F17 it assessed all three axes the same as the human fixture, then chose `action: clarify` instead of `action: spawn` anyway (10 of 17 opus verdicts were `clarify`, versus 4 of 17 for sonnet; excluding F16, where clarify is the confirmed answer, the spurious counts are 9 and 3). Sonnet's disagreements were mostly axis misjudgment (under-provisioning), not excess caution | E12 (both halves). **Superseded 2026-09-06, see the row below.** This run predates the fixed calibration instruction (D6) and the clarify rule (D10), and the caution it measured was an artefact of both |
| An opus orchestrator scores higher than a sonnet one, reversing E12, once the calibration instruction is fixed and the clarify rule is in place: opus 45/51 (88.2 percent, 95 percent Wilson [76.6, 94.5]), sonnet 32/51 (62.7 percent, [49.0, 74.7]), three runs each on bundle `2026-09-05-4cf35f7` | The intervals do not overlap. Opus clarified exactly once per run, on F16, where clarify is the confirmed answer, against nine spurious clarifies at E12. Cost: opus USD 10.1015 total against sonnet's 1.4447, which is 7.0 times more in total and 5.0 times more per correct verdict (USD 0.2245 against 0.0451) | Supersedes the E12 row above; answers open question 6 in `CLAUDE.md`. Evidence in `test/results/2026-09-06-routing-{sonnet,opus}-summary.md`, predicted in advance in `test/results/2026-09-05-preregistration.md` |
| Prompt caching makes repeated runs substantially cheaper, and unevenly by model | Across three consecutive runs of the same 17 fixtures, sonnet fell from USD 0.7311 to 0.3379 (54 percent) and opus from 3.8083 to 3.0536 (20 percent). Sonnet's first run matched its cold-cache E12 figure (0.7623), so per-run cost did not rise despite `ORCHESTRATOR.md` growing 18 percent | Changes the arithmetic for any repeated-run measurement, including the planned cost and quality benchmark: N runs cost well under N times a single run |

## Contradicted by documentation, 2026-09-05

| Claim as previously written | What the documentation says | Action taken |
| :--- | :--- | :--- |
| Effort appears on the `/tasks` row from v2.1.242 | The changelog entry is v2.1.243 | Corrected in `CLAUDE.md` and `src/README.md` |
| Fork mode is on by default and gives workers a reduced built-in tool set | A fork inherits the parent's full conversation context; no reduced tool set is described | `src/README.md` bullet rewritten; the tool-set claim is now listed below as unverified |

## Contradicted by empirical check, 2026-09-05

Claims stated in this repository's own files that a live test disproved, as distinct from the documentation-contradicted claims above.

| Claim as previously written | What was observed | Action taken |
| :--- | :--- | :--- |
| Invariant 5: haiku has no effort levels, given as the reason for excluding it | A worker defined with `model: haiku, effort: high` (`probe-haiku`, scratch project only) showed "Haiku 4.5 (high)" on its `/tasks` row: haiku honours effort | Invariant 5's justification struck from `CLAUDE.md`; the exclusion itself is left in place pending a decision on whether to add haiku cells, an open question CLAUDE.md now flags under invariant 5 |

## Unverified, 2026-09-05

Not found in the documentation. Each is stated as unverified in the sentence
that uses it. Move an entry up only with a `/tasks` row, a transcript, or a
reproducible command on a named version.

| Claim | Used in | How to verify |
| :--- | :--- | :--- |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes the nesting depth | `src/README.md` | Set it to 1, spawn a worker that spawns a worker, observe the refusal |
| Background workers run with a reduced built-in tool set, beyond `SendMessage` (now confirmed present, see above) | `src/README.md` | A self-reported tool list is unreliable (E9 got "PowerShell" as a tool name, which does not exist); needs a test that exercises tools rather than lists them |
