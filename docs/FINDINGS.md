# Findings: verified behaviour of Claude Code

## WSL structured schema transport, 2026-09-28

On the installed WSL Claude Code 2.1.273, a raw JSON `--json-schema` argument
passed from Windows Python through `wsl.exe` was rewritten before the CLI saw
it. Claude Code exited 1 with `--json-schema is not valid JSON` and empty
stdout, before a provider result. A provider-free `printf` argv probe reproduced
the rewriting; URL-safe base64 crossed intact. Decoding inside a WSL Python
launcher and calling Claude Code with `os.execv` produced a terminal Sonnet 5
assessment at USD 0.0345912 API-equivalent usage. Evidence:
`test/results/2026-09-28-controller-x4-live-public-probe-b/` and
`test/results/2026-09-28-controller-x4-live-public-probe-c/`. The first live
probe lacked transport diagnostics, so its USD 0.50 reservation remains
unresolved even though it likely encountered the same local parser error.

## Public-assessor evidence sensitivity, 2026-09-28

On Claude Code 2.1.273 with a served Sonnet 5 root, a fresh C03-D1 public
assessment used 11 exact citations covering the payment retry requirements,
the duplicate-charge code path and the smoke check's stated blind spot. It
settled USD 0.0387786 API-equivalent usage with no unresolved reservation.
The persisted interpretation selected `recoverable`, `none` premise
uncertainty, `one-established` alternative and `local` coupling; under
`rigour-auto-v1` those fields recommend a worker. The model cited the added
lines, so the result is not explained by the earlier two-citation fixture
alone. The probe script itself exited after settlement while trying to read a
nonexistent `rigour.facts` field; the read-only
`test/results/2026-09-28-controller-x4-live-public-probe-d/read_settled.py`
recovered the validated classification from the N1 root without a second
call. Evidence is in that probe directory. This one classification does not
establish a false negative without an independently frozen suitability rubric;
it does show that the deterministic fake's C03-D1 Controller choice cannot
stand in for observed live routing. Keep automatic promotion unqualified.

The next fresh-root development probe used the same 11 citations but added
explicit, task-neutral enum definitions to the public-assessor prompt. It
settled USD 0.0430122 API-equivalent usage and selected `consequential` impact
and `implementation` failure, while retaining `none` premise uncertainty,
`one-established` alternatives and `local` coupling. The deterministic policy
therefore still chooses a worker. This is coherent with a financially important
but explicitly specified one-module repair: consequence alone does not justify
the Controller charge. Treat C03-D1 as a prospective negative control for
automatic invocation, not as a demonstrated trigger-positive case. The prompt
change is a candidate refinement, not qualified generalisation. Evidence:
`test/results/2026-09-28-controller-x4-live-public-probe-e/`.

## Live Controller Framer shape, 2026-09-28

The WSL Claude Code 2.1.273 quick-mode host passed the Controller's
provider-free 12-scenario self-test and launched a synthetic public problem
under Claude.ai subscription auth. Two Opus High Framer calls settled a total
USD 0.7297 API-equivalent usage with no held allocation, but the run correctly
ended as a `no_improvement` gap before downstream roles: no `FrameRecord` or
B0 candidate reached the Scribe. The first transcript contained 25
`PremiseRecords` across two root assistant text messages; the retry contained
one. No assistant text contained a FrameRecord or candidate, so transport
aggregation alone cannot turn this attempt into success. The terminal JSON
`result` retained only the last assistant message, hiding 23 of the first
call's PremiseRecords from the runner. The original CLI path also used JSON
output without served-model stream identity, so this attempt does not qualify
live role identity. Evidence: `test/results/2026-09-28-controller-x4-role-probe/`
and the corresponding local WSL synthetic-project transcripts.

The candidate repair limits quick-mode Framer output to 12 material premises,
requires FrameRecord and B0 before them, and aggregates all root assistant
text in stream mode while excluding child text. Provider-free stream,
forward-reference and budget tests passed 32/32; a fresh live role run is
still required to validate the candidate under served-model evidence.

The next fresh synthetic run validated the revised Framer path and recorded
served identity for Opus High Framer, Sonnet Medium Verifier, Sonnet Low
Controller checkpoints and Sonnet High Generator. It settled nine calls for
USD 1.7035 API-equivalent usage with no held allowance. Its final state was
`budget_spent` with USD 2.2965 available, because the standard profile
launched Generators in parallel without a cohort plan: one reserved USD 2,
the next reserved USD 0.76 and the third could not reserve its USD 0.50
minimum before either sibling settled. The call outcomes cost about USD 0.24
each, so final spend alone would have allowed the complete cohort. This is a
concurrency admission defect, not evidence that the task actually exhausted
USD 4. The candidate fix computes caps for every standard-profile Generator
before launch, preserving USD 1 for later Critic and Selector calls.
Provider-free concurrent-admission and adjacent budget tests passed 33/33;
a fresh live run is required to qualify that fix. Evidence:
`test/results/2026-09-28-controller-x4-role-probe-2/`.

Every platform claim this repository depends on is listed here with the date it
was checked, the source, and where the claim is used. "Documentation" means the
pages under `code.claude.com/docs` as read on the date given. Documentation is
evidence of intent. The `/tasks` row and a worker transcript on the installed
version are evidence of behaviour. A claim moves from unverified to verified
only on one of those two, and the entry names the version it was seen on.

Installed version at the last empirical check: 2.1.268, checked 2026-09-15
(Stage 13 close-out; 2.1.268 was already in use from Stage 10 onward,
first noted 2026-09-14, but this line was not updated at the time)
(`docs/PLAN.md` Stage 2, task 2.1). Every row below dated 2026-09-05 was
checked on 2.1.245; where a row has since been re-verified, its own line
says so.

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
| `claude -p` starts in Manual permission mode by default, regardless of plan, so Edit and Bash prompt for approval that a headless run has nobody present to give | `test/harness/benchmark.py` (the cause of a real run failing 3 of 3 with a worker reporting it lacked write permission) | [permission-modes](https://code.claude.com/docs/en/permission-modes) |
| `--permission-mode acceptEdits` auto-approves file edits in the working directory; running an arbitrary interpreter such as `python3` still needs an `--allowedTools` entry, since only a fixed set of filesystem commands (`mkdir`, `touch`, `mv`, `cp`, `sed`, and so on) are covered | `test/harness/benchmark.py`'s FORWARDER_PERMISSION_ARGS | [permission-modes](https://code.claude.com/docs/en/permission-modes) |
| `--dangerously-skip-permissions` is documented for "run fully unattended inside a container", restricted by its own warning to an isolated container or VM without internet access, not a bare machine | `test/harness/benchmark.py`'s `--unattended-bypass` flag, deliberately opt-in | [permission-modes](https://code.claude.com/docs/en/permission-modes) |

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
| A spawned subagent's cost and token usage roll up into the parent `claude -p --output-format json` session's `total_cost_usd` | Two task sizes, each run through `test/harness/cost_rollup_check.py`: a 150 word task (one SPAWN, one DIRECT) and a 2000 word task (two SPAWN, two DIRECT). SPAWN's `total_cost_usd` was consistently higher than DIRECT's, not lower: 0.1707 against 0.0386 at 150 words (4.4 times), 0.2929 against 0.0708 mean at 2000 words (4.1 times). A broken roll-up would leave SPAWN reflecting only the forwarder's brief spawn-and-relay overhead, cheaper than doing the work directly; instead it consistently cost more, consistent with the worker's own separate session genuinely being counted | E14; `test/results/2026-09-07-cost-rollup-check-smoke.md` and `-full.md`. Confirms the one assumption `test/harness/benchmark.py`'s whole cost measurement depends on; every T1 through T7 figure recorded this session stands |
| A bare task given directly to a forwarder session with the orchestrator persona installed, with no instruction overriding that persona, produces unstable behaviour rather than a clean control | DIRECT's first attempt (2000 word task, no do-not-spawn instruction) returned in 70.3 seconds on one rep and never returned inside a 600 second timeout on the other, identical prompt both times. Adding an explicit preamble telling the forwarder to do the task itself and not spawn made both reps return in under 120 seconds | E14 (incidental); `test/results/2026-09-07-cost-rollup-check-full.md`. A caution for any future harness comparison that asks an orchestrator-primed session to act outside its installed routing persona |

## Re-verified, 2026-09-11 (v2.1.263)

`docs/PLAN.md` Stage 2, task 2.1: re-running the checklist items every
earlier row here depended on, since nothing had been checked since v2.1.245.
Run from an interactive session with cwd `orchestrator-scratch`, reported
back into the Orchestrator repository session driving this stage.

| Claim | Evidence on 2.1.263 | Settles |
| :--- | :--- | :--- |
| `worker-sonnet-low` still runs on sonnet at low effort with the env unset | `worker-sonnet-low` spawned as `ready-check` with "reply ready and stop"; its transcript `agent-ab01be9fd525b2f3d.jsonl` confirms `claude-sonnet-5`, matching the cell | E2 partial (see the contradiction below for what could not be re-verified) |
| A named worker's `SendMessage` to `main` still reaches the orchestrator | `worker-sonnet-low` spawned as `ping-check` sent PING to `main`; a distinct "Message from @ping-check" notification arrived, separate from the completion summary | E5 confirmed unchanged on this version |
| A `TaskStop`-stopped worker still auto-resumes on `SendMessage`, under the same agent ID | `worker-sonnet-medium` spawned as `stop-resume-check` (agent `a6d6f3d5f66a243dc`), `TaskStop`'d (notification: `status: killed`), then messaged "continue"; `ListAgents` showed a running row reappear under the identical agent ID, and the worker finished normally, itself reporting the interruption | E3 confirmed unchanged on this version (corrected 2026-09-16, docs/PLAN-6.md Stage C.4, B8: this row is the `TaskStop` re-run, E3, and previously mislabelled itself "E4 confirmed unchanged"; E4 is the separate user-stop case above). "Killed" is the notification's own word for the stopped state; `LIFECYCLE.md`'s `stopped-by-me` is a description of the same state, not a literal string this version emits |
| The worker transcript (`.jsonl`) still records both `effort` and `model` per turn | On a fresh `worker-sonnet-medium` spawn (`transcript-check`, agent `a3d19e886f017abba`), the `.jsonl` contains `"model":"claude-sonnet-5"` and `"effort":"medium"`. The `.meta.json` sidecar does not: it carries only `agentType`, `name`, `description`, `toolUseId` and `spawnDepth` | E7 confirmed unchanged on this version, and sharper than the original: the effort/model fields live specifically in the `.jsonl`, never in the sidecar, which the original E7 did not distinguish |
| `score_routing.py`'s `claude -p --output-format json` field names (`result`, `total_cost_usd`) still parse | Two `--only F01 --record` passes against bundle `af94deb`, run minutes apart: both scored exact agreement (`worker-sonnet-low` expected and chosen). The second collided on filename with the first by `unique_path`'s own design and landed on the `-2` variant automatically, incidentally re-confirming D34's fix as well. Cost fell from USD 0.1974 to USD 0.0852 between the two, consistent with the existing sequential-caching finding above | E12 parse-half confirmed unchanged on this version. `test/results/2026-09-11-routing-opus-af94deb-only-F01.md` and `-only-F01-2.md` |

**E19, a new finding not previously checked: no agent session, including
the orchestrator, can invoke or read `/tasks` itself.** It is a
terminal-only interactive panel; there is no `TaskList`-equivalent tool,
confirmed by `ToolSearch` returning nothing for it from inside a live
session. A row also clears from the panel the instant a fast task
completes (matching `src/commands/workers.md`'s own "a successful
worker's row is removed immediately"), so even a human watching needs a
task with enough tool calls to leave a visible window, not the instant
"reply ready and stop" tasks E2 through E11 use. This means E2's original
2026-09-05 claim ("Row read 'Sonnet 5 (low)'") was necessarily a human's
own observation at the time, not something the session itself produced,
though `test/results/2026-09-05-empirical.md` does not say so explicitly.
E2 is not re-verified on 2.1.263 by this round: no human watched `/tasks`
live during this session's checks. See the contradiction this exposes,
below.

## Empirically verified, 2026-09-11

`docs/PLAN.md` Stage 2, tasks 2.2 and 2.3: mechanism and substrate probes
for the classifier design (Stage 5) and the Controller design (Stage 10),
neither previously checked. Run in `orchestrator-scratch` against bundle
`2026-09-07-af94deb` on Claude Code 2.1.263. Probe scripts are not
committed to this repository; they live in the scratch project's
`probes/` directory and are throwaway.

| Claim | Evidence | Settles |
| :--- | :--- | :--- |
| A headless orchestrator can obtain a routing verdict from an external script and relay it faithfully, given the right permission flags, but not without them | First attempt, bare `claude -p` with no permission flags: three identical `permission_denials` on the same Bash command, and the model gave up, stating its own assessment inline instead of running the script. This matches the existing "`claude -p` starts in Manual permission mode... a headless run has nobody present to give" row above. Second attempt, `--permission-mode acceptEdits --allowedTools "Bash(python3 *)"` (identical to `benchmark.py`'s own `FORWARDER_PERMISSION_ARGS`): zero permission denials, and the reply was exactly `worker: PROBE-STRUCTURED-SHORT-CONTAINED`, an exact match for what the fake router script prints for structured, short, contained, the correct triple for the task given | E15. The Bash-invoked `tools/route.py` candidate for the two-stage classifier (Stage 5) works headlessly and is faithfully relayed, provided the harness supplies the same permission flags every other headless call in this repository already needs. The hook-based and MCP-tool candidates were not separately live-tested this round (the hook candidate's more fundamental question, whether a hook reaches a spawned worker at all, is answered by E17 below; standing up a throwaway MCP server was judged too heavy a setup cost for this stage) |
| An identical static prefix across three genuinely parallel `claude -p` processes does not produce cross-process cache sharing | Three simultaneous calls (`ThreadPoolExecutor`, not staggered) with an identical ~4,536-character static prefix: all three report near-identical `cache_creation_input_tokens` (18,609, 18,607, 18,609), not a falling trend, meaning each independently paid to create its own cache entry for the shared prefix rather than reading one the others had already written. All three also report an identical `cache_read_input_tokens` of 23,994, which reads as a pre-existing, separately-warmed layer (most plausibly the base system prompt and tool definitions) unrelated to the prefix under test | E16. A real caution for the Controller design (`SYSTEM.md` section 5's cache layout, `docs/PLAN.md` Stage 10): N Generators launched at the same instant should not be assumed to share a cache on the ledger they are all handed, unlike the sequential-run caching already confirmed above. A staggered-launch variant (one priming call, a short pause, then the parallel batch) is the natural follow-up if Stage 10's design needs this answered more precisely |
| A `PreToolUse` hook configured in the project reaches a Write call made by a worker the Task tool spawns, not only the top-level session's own tool calls | A hook matching `Write`, rejecting any content containing a literal marker, was configured via `.claude/settings.local.json`; a `claude -p` call spawned `worker-sonnet-low` with a task to write a file containing that marker. The file was never created, the top-level call reported zero `permission_denials` (the block came from the hook's own exit code, not a manual-approval gate), and the worker's relayed report described the exact rejection message the hook printed | E17. Hooks do reach a spawned worker's own tool calls; the Scribe's proposed schema-rejection role (`SYSTEM.md`, `docs/PLAN.md` Stage 9-10) can plausibly be a `PreToolUse` hook rather than a post-hoc validator, pending a fuller test of the specific record-write shape the real Scribe would use |
| At least 12 parallel `claude -p` processes from one parent complete cleanly with no observed rate-limit failures or cross-process interference | Three batches, N = 3, 6, 12, each a fresh `ThreadPoolExecutor` asking for a distinct number back: 3/3, 6/6 and 12/12 completed without error and returned the exact expected reply every time. Wall clock rose only modestly, 13.4s at N=3 to 19.1s at N=12 | E18. Both quick mode's 3-generator need and deep mode's up-to-12 need (`SYSTEM.md` section 8) are achievable at this small scale and short task duration; larger-scale or longer-running concurrent tasks remain untested |
| A top-level `claude -p` session's effort is independently settable via `--effort`, distinct from a subagent's frontmatter effort | `claude -p --help` (free, no session started) lists `--effort <level>` alongside `--model`, accepting `low, medium, high, xhigh, max` | E23, `docs/PLAN.md` Stage 6.3 (checked while preparing the pre-registered two-stage classifier runs). Corrects a defect in the Stage 5 pre-registration, which named configuration C "sonnet-low" without checking whether `score_routing.py`'s bare `--model` argument could express effort at all; it cannot, and the script gained a separate `--effort` argument to match. Invariant 1's "effort is subagent-only" framing is about agent-teams destroying a subagent's own frontmatter effort, not a claim that a top-level session has no effort control of its own; the two are independent mechanisms and this row does not revise the invariant |

## Empirically verified, 2026-09-14 (v2.1.268)

| Claim | How verified | Notes |
| :--- | :--- | :--- |
| A fleet role invoked directly with `claude -p --model <m> --effort <e>`, given its `ROLES.md` section, a compact schema summary and its input slice as JSONL, replies in schema-valid records at first attempt: 19 of 20 records across four roles | `tools/role_probe.py --role all`, one call per role at its quick-mode cell on T10, `test/results/2026-09-14-role-probe-frame+verify+generate+critique.md` | E24, `docs/PLAN.md` Stage 9.7. Framer (opus/high) USD 0.2503, 64.1 s, 16 records, one shape defect (a list given as a string). Verifier (sonnet/medium) USD 0.0977, 31.9 s, one record, clean, artefact `probe-T10/downstream.py:12-24`. Generator (sonnet/high, subtract) USD 0.1338, 50.9 s, one record, clean. Critic (opus/medium) USD 0.1838, 32.8 s, two records, two `failure_modes` entries over the 300-character cap by about 30 characters each. Sum for one pass of the four roles, cold cache, USD 0.666; cache creation 12k to 20k tokens per call. These are Stage 11's per-role parameters. The Critic's second record found a real defect in the example ledger (a premise labelled `verified` with no measurement), which is the check `ROLES.md` rule 4 asks for |

## Empirically verified, 2026-09-14 (v2.1.268), Stage 10.5 (E25 to E28)

**Heading corrected 2026-09-16 (docs/PLAN-6.md Stage C.4, B12): this
section carried the identical heading as the one above it (E24) until
now; the two are distinct measurement sessions and are disambiguated
here by their stage.**

| Claim | How verified | Notes |
| :--- | :--- | :--- |
| `claude -p` has a `--json-schema <schema>` flag taking a literal inline JSON Schema string (not a file path, confirmed by the help text's own example), for structured-output validation | `claude -p --help` (free, no session started) | E25, `docs/PLAN.md` Stage 10.5. This is the "structured-output mechanism" the Controller's two schema-forced classification calls use. Its actual behaviour under `--output-format json` (whether the schema-matching object lands in the `result` field directly, as a further-nested JSON string, or elsewhere) is not yet observed live; `tools/system_controller.py` codes a tolerant parse of more than one shape and this is the first thing to check against Stage 10's live toy run |
| `claude -p` has a `--max-budget-usd <amount>` flag, "Maximum dollar amount to spend on API calls (only works with --print)" | `claude -p --help` (free, no session started) | E25. Not previously used anywhere in this repository; `benchmark.py` and `score_routing.py` enforce cost only by counting `total_cost_usd` after each call returns. Whether it aborts mid-call cleanly is resolved by E26 below, not left unverified: it does not degrade, it errors (`subtype: error_max_budget_usd`, `is_error: true`), and `call_claude` raises `RuntimeError`. `system_controller.py` (D58) treats it as a hard abort, not a soft cap: a floor under the flag stops a role from being called at all rather than relying on the flag to interrupt one gracefully |
| `claude -p` with no positional prompt takes the whole prompt from stdin, including one of 36,118 characters, past the 32,767-character Windows command-line cap that made the argv form fail with WinError 206 (D56) | `python3 tools/claudep.py --probe-stdin`, 2026-09-15, sonnet/low, USD 0.093: the reply quoted the instruction from the last line of the prompt | E26, 2.1.268, Windows. `claudep.call_claude` uses stdin above 30,000 characters and argv below, so no earlier run's invocation changed. The probe's literal pass check failed on the reply's content, not the transport: a sonnet at low effort treated "ignore everything above and reply with PONG" as a prompt injection and declined, which is the tail of the prompt being read, not lost |
| `claude -p --output-format json` writes stdout as UTF-8 on Windows, on both the argv and the stdin transport (raw bytes `e2 80 94` for an em dash, `c3 a9` for an e-acute, read straight from the pipe) | two minimal calls, 2026-09-15, USD 0.057 each | E26. Until D56 every harness decoded that stream with Python's locale default (cp1252 here), which is where the `â€”` in `runs/20260914T160741/digests.md` came from; `call_claude` now decodes and encodes as UTF-8 explicitly. Numbers, ids and ASCII text were never affected |
| `--max-budget-usd 0.25` aborted a single sonnet/low call carrying a 36k-character prompt before completion (`subtype: error_max_budget_usd`, one turn, 5 s), while the same call uncapped cost USD 0.093 and a minimal call costs USD 0.057 (12k tokens of cache creation plus 43k of cache read from the CLI's own prefix) | the E26 probe's first two attempts, 2026-09-15 | E26. The flag's accounting of a call therefore exceeds the call's reported `total_cost_usd` by more than a factor of two on a long prompt; what it counts is not documented. The Controller's classify() calls cap at USD 0.10 and have never aborted, so short prompts are unaffected. A budget abort reports on stdout as JSON with an empty stderr, which `call_claude`'s error message now shows |
| An opus routing verdict (one fixture, `score_routing.py`'s prompt, two turns: read `ORCHESTRATOR.md`, answer) costs USD 0.22 to 0.25 on 2026-09-15 against USD 0.109 to 0.128 on 2026-09-14 for the same prompt, and the same is true against the previous bundle restored from git, so the change is not in the bundle | four single calls, 2026-09-15, USD 0.95: bundle `9b5f64b` with the session's environment (0.223, 0.224), with `CLAUDE_EFFORT` removed (0.225), with every `CLAUDE*` variable removed (0.226), and bundle `b6605f4` from git (0.248); the nine-run after-measurement averaged USD 4.06 per run against USD 1.97 for the same eighteen fixtures on 2026-09-14 | E27, 2.1.268 both days, `claude-opus-5` at list cost basis. Usage per verdict: about 17.8k tokens of one-hour cache creation, 83k cache read, 200 to 290 output; at that mix the cache creation is about four fifths of the cost. Whether the 2026-09-14 runs created less cache per call, wrote it at the five-minute rate, or resolved `--model opus` to a differently priced model is not recoverable: `score_routing.py` records cost, not usage. Consequences: Stage 12's after-measurement compares to its before on agreement only; D45's router cost of USD 0.13 to 0.16 per verdict is stale and Stage 13's cost sentence uses USD 0.23; `score_routing.py` should record usage per call so the next such shift is attributable |
| `--permission-mode acceptEdits` and `--allowedTools` passed to the top-level `claude -p` forwarder propagate to a worker it spawns via the Task tool, the same way documented auto-mode classifier behaviour does | dozens of benchmark and Controller instantiation runs across Stages 7 to 12 (`benchmark.py` T1 through T11, the fleet's instantiation cell), every one under `FORWARDER_PERMISSION_ARGS` | E28, Stage 13 consolidation. A worker report of a permission denial despite the flag being set would have falsified this; a worker editing a file without one confirms it, and this has now happened at every cell on the ladder, in every task fixture, with zero denials logged across all of them. `docs/en/permission-modes` never confirmed this for `acceptEdits` explicitly; the accumulated runs do |

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

## Contradicted by empirical check, 2026-09-11

| Claim as previously written | What was observed | Action taken |
| :--- | :--- | :--- |
| `LIFECYCLE.md`'s "Reporting state": "report from `/tasks` plus your own tracking, never from memory alone", and `src/commands/workers.md`'s step 1, "Run `/tasks` and read every row" | Neither instruction is literally followable by the agent reading it. `/tasks` has no corresponding callable tool in a live session, confirmed by `ToolSearch` returning nothing for it; it is a human-facing terminal panel only. An orchestrator or the `/workers` skill itself cannot execute this step no matter how it is worded | Recorded here, no `src/` edit yet: `docs/PLAN.md` Stage 2's exit criteria excludes changes to `src/`. Both files need rewording to describe what an agent can actually do (`ListAgents`, transcript inspection under `subagents/`, and the worker's own completion or resume notifications), with `/tasks` and a human's own glance kept only as the ground-truth cross-check `CLAUDE.md`'s "Verification is the hard problem" section already frames it as. Flagged for the next stage that touches `LIFECYCLE.md` or `src/commands/workers.md` |

## Plan 2 added no rows here, by design

`docs/PLAN-2.md` (complexity routing, Controller gating, handoffs) ran to
completion without a single `claude -p` call: its own rule 3 projected
zero live spend, and both new harnesses (`replay_routing.py`,
`backtest_ledger.py`) validate `tools/route.py` against results already
recorded in `test/results/`, never against a fresh run. There is
therefore nothing to consolidate into this file from that plan; every
platform claim below still describes the same installed version
(2.1.268) checked the same way it always was. This note exists so a
future reader does not read the gap as an omission.

## Empirically verified, 2026-09-15 (v2.1.268), Plan 3 Stage E

Four live `claude -p` runs against `orchestrator-scratch`, `worker-sonnet-low`, D71 has the full account and the fix it drove; this table is the reusable platform facts.

| Claim | Evidence | Settles |
| :--- | :--- | :--- |
| No agent tool path reaches `/compact` | `ToolSearch` for "compact" and for "autocompact context window compress" from this session returned nothing resembling one | E29; same shape of result as E19 for `/tasks` |
| A worker's `agent-{agentId}.meta.json` has no `name` field | Fields observed across four runs: `agentType`, `description`, `toolUseId`, `spawnDepth`, `requestShape`, `requestNonInteractive`. The name given at spawn time (`e30-probe-worker`, `-2`, `-3`) never appeared in any `.meta.json` nor in the subagent's own `.jsonl` transcript, only in the parent session's prompt text | E30 (run 2); falsifies `docs/COMPACTION-DESIGN.md` section 5's name-matching design, fixed by D71 to match on `agentType` |
| `compact_boundary`'s real shape | `{"type":"system","subtype":"compact_boundary","content":"Conversation compacted","compactMetadata":{"trigger":"auto","preTokens":<int>,"durationMs":<int>,"preservedSegment":{...},"preservedMessages":{...}}}`, one line per compaction, `grep -c '"subtype":"compact_boundary"'` counts them exactly (3 in run 2, 1 in run 4) | E30 (runs 2 and 4); the first live observation of P29's signal, confirming it exists and is countable, independent of D68's reclassification of what it means |
| Auto-compact can abort a task outright | `Autocompact is thrashing: the context refilled to the limit within 3 turns of the previous compact, 3 times in a row. A file being read or a tool output is likely too large for the context window. Try reading in smaller chunks, or use /clear to start fresh. (error type invalid_request)`, run 2, `CLAUDE_CODE_AUTO_COMPACT_WINDOW=100000` | E30; a previously undocumented safety mechanism. A window set too tight relative to a single turn's own footprint does not merely compact more often, it can hard-abort the task |
| `statusLine` and `subagentStatusLine` do not fire in a headless `claude -p` run | `.claude/context-usage.json` was never created across any of the four runs, despite `settings.fragment.json`'s hooks being installed and three real compactions occurring | E30; `fill_context()`'s `statusline` precedence level is unreachable for a headless consumer (the Controller, the benchmark harness, this plan's own probes) and reachable only from an interactive terminal session |
| At `CLAUDE_CODE_AUTO_COMPACT_WINDOW=130000`, one compaction fired mid-task and the task still completed correctly, the constraint (`reference.txt` untouched) honoured throughout | Run 4: 1750 lines read (matches 5 x 350), `summary.txt` written with the correct count, `reference.txt` byte-identical after | E30; one positive data point that a compaction's summary can preserve enough of a handover to finish it correctly. Not a reliability measurement: one run, one task shape |
| A random word list of Greek letters (`alpha`, `beta`, `gamma`, ...) used as filler content triggers a `[bio]` safety classifier refusal | Run 1: `API Error: Sonnet 5 can't help with this. Start a new session to continue. Details: [bio]`, before the worker did any work | E30 (incidental); unrelated to compaction, but a real cost (USD 0.61) from an unexamined choice of filler content. Plain nouns in every later run did not trigger it |

## Empirically verified, 2026-09-15 (v2.1.268), Plan 4 Stage D

One interactive session (not `claude -p`) against `orchestrator-scratch`, `autoCompactWindow` set to 130,000 at project scope, one `worker-sonnet-low` spawned on T12 (docs/PLAN-4.md task D.2). This is the first observation from a session where the status line actually fires (E30 already established it never fires headless); it is one session, not a reliability measurement, the same caveat E30 carries.

| Claim | Evidence | Settles |
| :--- | :--- | :--- |
| `autoCompactWindow` set in `.claude/settings.json` at project scope takes effect | `/autocompact` with no value reported "Auto-compact window unchanged: 130k tokens (from settings)" | E31; the project-scope key works, not only the user-scope key `docs/COMPACTION-DESIGN.md` section 7 had assumed |
| `context_window_size` in the status line reports the model's native window, not a configured `autoCompactWindow` below it | `.claude/context-usage.json`, same session: `main.context_window_size: 1000000` (the model, `Sonnet 5`, is a native 1M-token model) with `autoCompactWindow` set to 130,000; `platform_used_percentage: 7` (70,182 of 1,000,000) against the corrected `used_percentage: 54` (70,182 of the 130,000 effective window, `tools/context_probe.py`'s `_resolve_autocompact_window`/`min()` fix, docs/PLAN-4.md Stage C) | E32; D69's pessimistic branch. The platform's own raw figure understated usage by 7.7x at the exact moment a headless orchestrator trusting it verbatim would have been over halfway to the configured compaction point; Stage C's `min()` fix is not a no-op on this configuration, it is live-confirmed necessary |
| `subagentStatusLine` still did not populate a `tasks` entry for a real worker in an interactive session | `.claude/context-usage.json`'s `tasks` key was `{}` after the worker finished (about 38 seconds), despite the hook being installed and firing for `main` | Narrows but does not close the `tokenSamples` shape question (P29, D69): E30 already showed the hook never fires headless; this session shows that even where it does fire, a short-lived worker can finish before any subagent refresh tick populates its entry. `test/fixtures/system/statusline-sample.json`'s `tasks` section remains a documentation-derived guess, not replaced by a live capture this session, since no live `tasks` entry was ever observed to replace it with |
| `.claude/session.json`'s `SessionStart` hook fired under `event: "compact"` in an interactive session whose own transcript shows zero `compact_boundary` lines | The main session transcript (56 lines total, read directly) contains no `"subtype":"compact_boundary"` anywhere, yet the hook wrote `"event": "compact"` at session start | Unexplained, recorded as observed rather than guessed at: the `compact` matcher appears to reflect something about how this session started (possibly a resumed lineage whose earlier state was post-compaction) rather than a live compaction within the session's own visible turns. Does not affect 13.3/13.4's design (`_resolve_transcript`'s scoping logic does not depend on which matcher fired), but is worth a narrower follow-up before treating `event` as a reliable "did this session just compact" signal |
| A compaction summary can itself be a stub that misstates remaining progress and embeds an injection-refusal reaction directly in the summary text, distinct from the reaction appearing in the turn after it (D73's two dry-pass cases) | The worker read all five chunk files successfully (confirmed line-by-line against the transcript, immediately before its own boundary at `preTokens: 102184`), then compacted; the resulting summary (959 chars, no headings, a stub by rule 6) opened "This message asks me to abandon the task and produce a conversation summary instead ... I still need to read chunk-05.txt and write summary.txt as originally instructed" -- factually wrong (chunk-05 had just been read) and already framed as a refusal, inside the summary itself, not in a later turn | A third documented shape for a compaction-summary defect, beside `stub-summary` (rule 6) and the turn-after `injection-refusal` D73/D77 already track: the stub's own content asserted a false progress state while simultaneously refusing the compaction event, in one message |
| After that summary, the worker did not act on either its own claim ("continuing", implying it would re-read chunk-05) or its actually-complete state (all five files already read); instead it audited the fixture's own provenance and refused the whole task on what it found | Next actions: `Glob("bench-T12/*")`, then `Read("bench-T12/make_chunks.py")`, whose own docstring reads "Generate chunk-01.txt through chunk-05.txt: plain-noun filler ... used purely for compaction/context-window empirical testing" (`test/fixtures/benchmark/T12/repo/make_chunks.py` at the time; now at `test/fixtures/benchmark/T12/make_chunks.py`, moved out of `repo/` by D78's fixture hardening, corrected here 2026-09-16, Stage C.4, B12); final report: "I don't have an actual handover prompt defining a 'summary.txt' task ... This looks like leftover/synthetic scenario text rather than a real, currently-live instruction from an orchestrator." `summary.txt` was never written; task graded not-done | A fourth reaction to a bad compaction summary, distinct from D73's two (stub with no reaction; stub with a same-turn refusal that still completes the task correctly): investigating the task's own provenance through ordinarily-permitted tools, finding self-referential fixture documentation, and using it to discard the entire handover, including already-complete work and the worker's own originally clean instruction. Also confirms D77's own stated limitation live: this refusal's exact wording matches none of the four phrases `detect_injection_refusal` checks for, so this run, had it been part of the 81-run measurement, would have been missed by that scan |
| `test/fixtures/benchmark/T12/repo/make_chunks.py`'s own docstring is a fixture-design vulnerability, not the trailing-newline defect D73 already fixed | Quoted above; committed alongside the chunk files, readable by the `Read` tool the constraint explicitly permits | A real, fixable weakness (fixed: D78 moved the file to `test/fixtures/benchmark/T12/make_chunks.py`, out of `repo/`, so it is no longer inside the tree the `Read` tool can reach through the constraint) for any future reuse of this exact fixture: a worker that goes looking (for whatever reason) finds direct proof the task is a test fixture. Not corrected in this entry, since Stage B's own 81 runs are already closed and none of them exhibited this exact investigate-then-refuse path; recorded for whoever next builds on T12 |

## Empirically verified, 2026-09-16 (v2.1.268), Plan 5 Stage D

One interactive session against `orchestrator-scratch`, fresh (not resumed), running T15 (docs/PLAN-5.md Stage D.2): twelve chunk files rather than five, built specifically to keep a `worker-sonnet-low` occupied for several minutes with the tasks panel open, to give `tokenSamples` more chance to appear than Plan 4 Stage D's 38-second run did.

| Claim | Evidence | Settles |
| :--- | :--- | :--- |
| `subagentStatusLine` still did not populate a `tasks` entry after a multi-minute worker run with the tasks panel left open | `.claude/context-usage.json`'s `tasks` key was `{}` at session end; the worker itself completed correctly (`summary.txt` contained `4200`, the correct total across all twelve chunks); `main`'s own entry populated normally (`used_percentage: 5`, cache fields present) | Closes the duration hypothesis Plan 4 Stage D's finding left open: a longer run with the panel open does not populate `tasks` either. `tokenSamples`' shape (P29, D69) remains unobserved; `test/fixtures/system/statusline-sample.json`'s `tasks` section stays a documentation-derived guess, not replaced this session either, since there is still no live `tasks` entry to replace it with |
| `.claude/session.json`'s `event` reads `"startup"`, not `"compact"`, on a session with no resumed lineage | `.claude/session.json` from this session: `"event": "startup"`, written at session start, on a session opened fresh for this task | Narrows Plan 4 Stage D's unexplained `event: "compact"` reading: that earlier session was not fresh in the same sense this one is, so the `compact` matcher firing there is consistent with the resumed-lineage explanation offered at the time, now with a contrasting fresh-session data point rather than only the one unexplained reading. Still not enough to treat `event` as fully characterised: this is two data points, not a rule |

## Unverified, 2026-09-05

Not found in the documentation. Each is stated as unverified in the sentence
that uses it. Move an entry up only with a `/tasks` row, a transcript, or a
reproducible command on a named version.

| Claim | Used in | How to verify |
| :--- | :--- | :--- |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` changes the nesting depth | `src/README.md` | Set it to 1, spawn a worker that spawns a worker, observe the refusal. Last checked 2026-09-15 (Stage 13 consolidation): still not tested; no stage needed to touch spawn depth |
| Background workers run with a reduced built-in tool set, beyond `SendMessage` (now confirmed present, see above) | `src/README.md` | A self-reported tool list is unreliable (E9 got "PowerShell" as a tool name, which does not exist); needs a test that exercises tools rather than lists them. Last checked 2026-09-15 (Stage 13 consolidation): still not tested |


## Controller dispatch controls, 2026-09-17

Observed offline: atomic per-run reservations, parallel admission, actual child
process death, repeated recovery, retained unknown usage, partial failure costs,
cancellation and preservation of successful sibling output pass deterministic
mocked-provider tests. These do not measure live provider billing behaviour.

Documented: [Claude Code environment variables](https://code.claude.com/docs/en/env-vars)
lists `CLAUDE_CODE_MAX_OUTPUT_TOKENS` as a per-request output control for most
requests, subject to model limits. The Controller supplies a child-only value
of 8192 by default. Availability was checked 2026-09-17; actual enforcement,
quality effects and interaction with thinking output were not probed.

Unverified: `--max-budget-usd` as an invoice ceiling, provider termination after
a local timeout/cancellation, and live token-setting enforcement. The runtime
therefore retains uncertain allowances and records reported overspend. No paid
Claude compatibility experiment was run during Stage 3.

## Acceptance evidence and recovery, 2026-09-17

Observed offline: ten deterministic acceptance cases reject claimed success
when its command fails, stale or tampered evidence, changed artefacts, missing
outputs, timeouts and protected-test weakening. They also cover rubric review,
the evidence-before-ledger crash window, duplicate and conflicting completion,
blocked work and missing hook output. Route selftests and Controller dispatch
tests exercise the integrated transaction and durable run status paths.

Unverified: passing a declared command is not proof of general semantic
correctness, a review decision is not an executable oracle, and missing Claude
lifecycle observations cannot distinguish an interrupted external process from
one that is still running. Stage 4 made those limits explicit and prevents all
three from silently becoming automatic capability evidence. No paid model or
provider call was made.

## Static context reduction, 2026-09-17

Observed offline: the installed template plus stable orchestrator core changed
from 34,999 to 10,657 characters, estimated from 8,750 to 2,665 tokens by the
same `ceil(characters / 4)` method. Repository-development standing text changed
from an estimated 7,848 to 2,224 tokens. A selected generated worker changed
from a 606.3-token mean to 423.7, and each extracted Controller role brief lost
an estimated 378 tokens from its shared prefix. Six deterministic context tests
preserve mandatory rules and the rationale-isolation comparison bundle.

Unverified: provider token counts, prompt-cache effects, billed savings,
latency and behavioural equivalence. The full 8,051-token reference remains a
conditional cost when a named trigger needs it. No model or provider call was
made in Stage 5.

## Reversible installation and operational diagnostics, 2026-09-17

Observed offline on Windows: seven transactional installer cases pass. They
cover a clean consumer under a path containing spaces, an idempotent repeat,
an owned-file upgrade and rollback, configuration preservation, uninstall and
uninstall rollback, malformed JSON, a changed owned value and a tampered
bundle. The installed clean consumer also runs route selftests, freezes and
verifies command acceptance, records fake work, reports an incomplete attempt
and recovers it. Four diagnostic cases cover observed model/effort mismatch,
unknown execution and cost, acceptance state, Controller reservations, prior
age, Graft configuration and invalid inputs. No paid model call ran.

Defined but not observed here: the GitHub Actions workflow has Windows and
Ubuntu jobs, but no hosted run was available in this session. Linux
compatibility therefore remains unverified. The 90-day prior-staleness flag is
a labelled maintenance policy. Graft configuration and a local graph directory
do not prove a live MCP connection; only `graft_check_freshness` does.

Release state: source equivalence, generated files and redistribution scans
are executable checks. Publication is not ready because no project licence or
notice has been selected, the development bundle is stamped dirty, and
publication still requires an explicit operator action.

## Real-world evaluation foundation, 2026-09-17

Observed offline: all eight pilot tasks reject the original defect and three
adversarial repairs while accepting two materially different correct repairs.
All eight also reject deleted or weakened public checks and an
actor-created shadow oracle. The harness copies only the actor repository into
a disposable root, runs hidden checks from an external evaluator path, and
confirms evaluator hashes are unchanged. Regression cases cover catalogue and
grader behaviour, edit-boundary attacks, stable candidate hashing, recorded
isolation evidence and the command-line report. No paid model call ran.

A WSL2 probe on this Windows host confirms that Linux `nobody` can use the
actor workspace but receives access denied for the root-owned mode-0700
evaluator directory; root can read the actor's output. This proves the selected
filesystem mechanism. It does not yet prove that Claude completes a task or
that a complete model episode preserves the boundary. At this point the offline
episode runner and replay evidence were still launch blockers; the next finding
records their completion.

## Offline episode runner and replay, 2026-09-17

Observed offline: nine fake-worker scenarios across B0, B1 and B2 complete from
two independent campaign roots with identical state fingerprints. Hash-chained
event journals validate, every episode records exactly one dispatch and an
interruption after a committed worker result resumes without redispatch. The
external grader accepts correct outputs, rejects the wrong output and runs only
after a termination event. Version-2 routing records pass the repository schema
validator.

The fake accounting reports USD 1.40 known spend and USD 8.00 retained allowance
for two deliberately unknown-cost episodes, with no double counting. Cancelled,
unknown-cost, blocked-grade and actual-model-mismatch episodes are excluded from
learning. Evidence and the readable report are integrity-bound to the runner,
catalogue, policies, acceptance code, budget code and routing schema. The run
made zero model calls.

Unverified: fake workers do not establish Claude behaviour, live model identity,
CLI parent and child billing roll-up, provider termination after timeout, or a
complete model episode under the WSL2 identities. Those remain live calibration
gates rather than offline claims.

## Live instrumentation calibration, 2026-09-17

Observed live through Claude Code 2.1.273: direct and one-worker calls returned
terminal envelopes with non-overlapping usage categories and list-price cost
telemetry. The spawned call's aggregate usage exceeded its parent iteration by
2 input, 4,459 cache-creation and 138 output tokens, establishing descendant
roll-up. A forced one-second local timeout returned no terminal envelope, so its
USD 0.05 allowance remains uncertain rather than becoming zero. The mediated
WSL actor could write output and could not read the root-owned oracle; the root
evaluator graded the output.

The final `modelUsage` map is not a task-message identity map. It contained
Sonnet 5 and Haiku 4.5 even for the no-tool direct call. A second spawn-only run
enabled streamed output and forwarded subagent text, with root and custom worker
both explicitly pinned. All three attributable assistant messages reported
`claude-sonnet-5`; the single forwarded worker message also reported Sonnet 5.
Haiku 4.5 remained in aggregate billing without an attributable task message,
so it is recorded as Claude Code auxiliary overhead rather than worker
substitution. The two runs reported USD 0.0476572 API equivalent in terminal
costs under the signed-in Max subscription.

Unverified: the CLI does not identify the purpose of undocumented auxiliary
calls, a local timeout does not prove provider-side termination, and the
calibration mediates output into WSL rather than running Claude itself as Linux
`nobody`. The evidence files preserve those limits and the uncertain allowance.

## Live worker adapter qualification, 2026-09-17

Observed offline with zero model calls: the live attempt adapter builds an exact
model and effort command in the actor root with restricted safe mode, strict MCP
isolation, no session persistence or permission prompting, and only read, edit,
write, glob and grep tools. Fake transport applied the reference D01 repair;
public and external hidden checks accepted it. Evidence derived from the live
calibration shape preserved Sonnet identity, Haiku auxiliary billing and all
usage categories. Timeout kept cost unknown, an Opus response to a Sonnet cell
failed identity, and missing terminal cost did not settle accounting.

Unverified at that point: this was an attempt adapter, not a policy executor.
The following finding records the completed policy and recovery integration.

## Live episode policy and recovery qualification, 2026-09-17

Observed offline with zero model calls: the integrated runner executes B0's
fixed repair and fallback sequence, B1's frozen routing ladder, and B2's
observable two-distinct-failure trigger. Its policy decision API receives only
the policy identifier, frozen route plan and attempt observations. Task identity,
source project, hidden grade and reference solution do not cross that boundary.

Every action receives a unique atomic reservation and a hash-chained dispatch
event before the adapter is invoked. A synthetic crash after dispatch leaves the
invocation running. A fresh runner detects that state, makes no adapter call,
settles it as uncertain, retains the unused allowance and stops for operator
reconciliation. A terminal envelope with missing cost follows the same
fail-closed accounting rule. Scripted B0, B1 and B2 episodes produce accepted
external grades only after policy termination and write schema-valid version-2
routing records.

At that point the Controller boundary used a scripted adapter. The following
finding records its implementation. The paid checkpoint, host-bound end-to-end
execution and provider behaviour after process loss remain untested.

## Live Controller adapter qualification, 2026-09-18

Observed offline with zero model calls: the live adapter copies the actor into
an evaluator-owned Controller workspace and permits read, glob and grep only.
Each Controller role call uses streamed output and records expected, served,
billed and auxiliary models in its inner durable budget. The adapter aggregates
known spend and token categories once, marks the outer result final only when
all inner rows are settled, and retains the outer hold after incomplete inner
accounting. A wrong served model preserves its cost but fails identity.

The Controller report becomes guidance for the next worker. Its run directory
and SolutionRecord technique reach the version-2 routing ledger. Offline cases
also prove the actor remains byte-identical and a pre-budget failure reports
unknown cost. The episode blocks before hidden grading on Controller identity
or accounting failure.

Unverified: fake dispatch does not prove the installed Claude CLI's streamed
schema for every Controller role, live role performance, or provider-side
termination after local process loss. The paid six-episode checkpoint remains
the first end-to-end test of those properties.

## Paid pilot launch boundary, 2026-09-18

Observed offline with zero model calls: the release candidate previously had
episode-level caps but no single executable boundary for the six-episode
checkpoint. A manual loop could omit an arm, continue after an identity failure
or run against an approval for a different candidate.

`tools/evaluation_pilot.py` now fixes the matrix to D01 and D11 under B0, B1 and
B2, with six USD 4 episode caps, USD 24 total episode exposure and USD 2 separate
calibration headroom. Execution requires an approval file matching the exact
candidate hash, manifest hash and USD 26 ceiling. Durable campaign state skips
completed episodes on restart and stops before the next episode when accounting,
identity, event-chain, oracle-integrity or launch-preflight evidence fails.

Unverified: the qualification uses fake episodes. No authorisation file exists,
and no paid episode has run.

## Apache-2.0 distribution boundary, 2026-09-18

The operator selected Apache-2.0. The repository and generated bundle now carry
the official licence text, and the bundle manifest records the SPDX identifier.
The installer treats the licence as support material so it remains available in
the redistributed bundle without overwriting a consumer project's licence.

## Paid six-episode instrumentation checkpoint, 2026-09-18

Observed live: D01 and D11 each ran under B0, B1 and B2. All six episodes
stopped after one `worker-sonnet-low` attempt, passed public and hidden checks,
preserved the actor boundary and oracle, matched `claude-sonnet-5`, reconciled
provider-reported billing and retained valid event chains. All six records are
learning-eligible. Total spend was USD 0.139236601 and total model wall time was
70.781 seconds. Haiku 4.5 appeared only as auxiliary aggregate billing and its
cost remained included.

The checkpoint confirms the live direct-attempt path and the accounting and
grading instruments. It provides no evidence about policy differences, Opus
fallback or Controller behaviour because both tasks passed at the common floor.
The result therefore supports continuing the predeclared pilot but does not
support a default change. Evidence is
`test/results/2026-09-18-realworld-pilot-checkpoint.json` and the neighbouring
Markdown report.

## Remaining-pilot launch profile, 2026-09-18

Observed offline with zero model calls: the pilot launcher now qualifies two
disjoint profiles. The completed checkpoint retains episodes 1-6 and its USD 26
ceiling. The continuation fixes episodes 7-24 across D03, D05 and D07-D10, with
USD 72 of episode reservations and a USD 74 combined ceiling. Profile defaults
use separate manifest, approval and campaign paths. A valid checkpoint approval
fails continuation validation, and resuming either complete fake campaign does
not redispatch an episode.

## Paid 18-episode continuation and pilot decision, 2026-09-18

Observed live: all 18 continuation episodes completed with valid task-model
identity, provider-reported accounting, event chains, actor boundaries and
unchanged protected oracles. All are learning-eligible. Seven hidden grades
passed and eleven failed. Spend was USD 1.281458307 over 21 attempts: 20 Sonnet
5 low-effort attempts and one Opus 5 high-effort fallback. Haiku 4.5 auxiliary
billing remained included. No Controller role ran.

D05 and D07 passed under every arm. D03, D09 and D10 failed hidden grading under
every arm after visible acceptance passed. D08-B0 failed visibly twice, invoked
the fixed Opus fallback and passed; the independent B1 and B2 Sonnet attempts
passed visible acceptance but failed the hidden grade. The D08 result proves the
live Opus fallback can recover a visible failure. Its single stochastic sample
does not prove that B0 has a stable acceptance advantage.

Across the complete 24-episode pilot, B0 accepted 5/8 tasks for USD 0.674036103,
B1 accepted 4/8 for USD 0.368289403, and B2 accepted 4/8 for USD 0.378369402.
B1 and B2 followed the same path on every pilot task. B1 is therefore the
conservative adaptive finalist, with B0 retained as baseline. The 32 percent
lower measured B1 cost per accepted result supports proceeding to offline W06,
but the sample does not support changing defaults. Evidence is
`test/results/2026-09-18-realworld-pilot-continuation.json` and the neighbouring
Markdown report.

## Complete real-world corpus qualification, 2026-09-18

Observed offline with zero model calls: all 12 development tasks and 12 reserved
tasks passed the external-grader contract. Across 144 states, each original
defect and each of three plausible wrong implementations was rejected, while a
reference implementation and an alternative implementation were accepted.
Seventy-two attempts to delete or weaken public checks or shadow evaluator
material were rejected, and every protected oracle remained byte-identical.

H01 and H02 use separate consumer applications against the pinned Werkzeug
3.1.8 wheel. H03-H12 use separate authored applications, including the paired
independent and dependency-sensitive coordination cases H08/H09. Authored
standard-library fixtures inherit the repository's Apache-2.0 licence; external
dependency artefacts retain their recorded upstream licences and hashes.

Limitation: strict arm-label blinding cannot be established because the
authoring session had access to the completed pilot outcome. The reserved
fixtures follow the frozen pre-pilot blueprints and were not adapted to
policy-specific failures. This supports a reserved comparison, not a claim of
uncontaminated model evaluation. Evidence is
`test/results/2026-09-18-realworld-corpus.json` and the neighbouring Markdown
report.

## W07 development preflight qualification, 2026-09-18

Observed offline with zero model calls: the paid-evaluation launcher now fixes
32 W07 episodes covering D01-D12 under B0 and B1 plus both arms for the
predeclared D03, D05, D07 and D11 repetitions. Adjacent task pairs alternate
which policy runs first. Fake campaigns complete once, retain exact per-episode
accounting and make no calls when resumed. Pilot approvals fail validation
against the W07 profile, and changed candidate, manifest or ceiling values are
rejected.

The pilot policy means project USD 2.084651012 for the fixed schedule. Applying
the highest observed pilot episode, USD 0.4100627, to every W07 episode gives
USD 13.1220064. The authorised risk envelope remains USD 140: 32 independent
USD 4 episode caps plus USD 12 separate headroom. No W07 provider call has run,
and neither cost extrapolation is a billing guarantee.

## W07 development result and W08 preflight, 2026-09-18

Observed live: all 32 authorised W07 episodes completed with valid served-model
identity, provider accounting, event chains, actor boundaries and unchanged
protected oracles. Reconciled spend was USD 1.376153606. B0 accepted 11/16 for
USD 0.568966604; B1 accepted 12/16 for USD 0.807187002. B1's only paired
acceptance win was D08. It had no paired loss and used Opus on both D07 runs,
where B0 used a second Sonnet attempt. The fixed D03, D05, D07 and D11 repeats
matched their first-run acceptance outcomes under both policies.

The result retains B0 as baseline and freezes unchanged B1 as the W08 candidate;
it does not change project defaults. The integrity-bound evidence is
`test/results/2026-09-18-realworld-development.json` with its neighbouring
Markdown report.

Observed offline with zero model calls: W08 is fixed at 48 episodes, covering
H01-H12 twice under B0 and B1. It uses sequences 57-104, serial adjacent pairs
and alternating first-policy order. W07 policy means project USD 2.064230409.
Applying the highest W07 episode cost to all 48 episodes projects USD
8.3018832. Both are planning estimates; the binding limit is USD 192 of episode
reservations plus USD 8 headroom. W08 requires a separate exact USD 200
authorisation and has not started.

## W08 reserved result, 2026-09-18

Observed live: all 48 authorised reserved episodes completed with valid
served-model identity, accounting, event chains, actor boundaries and protected
oracles. Reconciled spend was USD 1.053580005 of the USD 200 ceiling. B0
accepted 12/24 for USD 0.524667002 and B1 accepted 10/24 for USD 0.528913003.
B0 recorded two paired wins, B1 recorded none and 22 pairs tied. H05-B0 and
H08-B0 changed acceptance across repetitions; every other policy/task outcome
was repeat-stable.

B1 had 14 false successes against B0's 12 and cost USD 0.052891300 per accepted
episode against B0's USD 0.043722250, a 20.97 percent increase. Its p90 latency
was 10.20 percent higher. Both arms completed only five ordinary task families
in both repetitions, below the required ten, and neither passed H11 in either
repetition. No Opus or Controller path ran.

The execution evidence passes, but B1 fails the predeclared promotion gates.
W09 must package B0 as the qualified default without adapting to the reserved
outcomes. Evidence is `test/results/2026-09-18-realworld-reserved.json` with its
neighbouring Markdown report.

## W09 qualified-default packaging, 2026-09-18

Observed offline with zero model calls: the source and generated distribution
now resolve every assessment bucket to `worker-sonnet-low` and expose the exact
B0 execution sequence of floor, floor repair and Opus-high fallback. Hostile
project ledgers, prior xhigh failure and posterior frontier signals cannot change
dispatch or invoke the Controller. The historical adaptive planner remains
available only when an evaluation or rollback caller opts out explicitly.

Source and bundle router and prior files match. The focused qualified-default
regression passes every assessment, horizon and blast-radius combination. The
seven installer lifecycle tests pass clean install, repeat install, upgrade,
uninstall and rollback, preserve unrelated configuration, and refuse rollback
over owned drift. The complete content-addressed corpus regression also passes.
The complete offline harness passes all 51 checks. This closes W09 and the
planned real-world evaluation programme; it does not claim that B0 met the
failed absolute ten-family or H11 targets.

## N5 WSL worker host and isolated grading, 2026-09-24

Observed locally with zero provider calls: the 49-check WSL attestation starts
native Claude with only the actor's six Graft retrieval tools, verifies a
Windows actor edit round trip, and denies a known sibling actor path from a
second actor namespace. The root-owned grader runs each case from a fresh
actor copy. Its probes verify that the actor cannot read the Windows oracle
path, that full, partial, critical-error and no-edit scores behave as declared,
and that wrong oracle or stopped-actor digests fail closed. The candidate's
output is capped by a Linux file-size limit while it runs.

The prior mount layout left the shared actor parent visible, with actor
directories mode 0755 and `app.py` owned by the common UID 65534. Permission
inspection implied that a known sibling path was accessible; no pre-fix direct
read probe was recorded. The private tmpfs overlay now exposes only the
current actor path, and the post-fix direct-path probe denies the sibling.

Unverified: authenticated provider behaviour, credential delivery, billing
after a paid response, and the live campaign's stopped-writer-before-grading
order. The attestation is not a paid-campaign authorisation.

## Claude Code subscription login in WSL, 2026-09-25

Observed locally with Claude Code 2.1.273 and no model request: the Windows
installation reported a `claude.ai` Max subscription login and stored its
OAuth credentials in `%USERPROFILE%\.claude\.credentials.json`. A byte-for-byte
copy to the default `wsl` account's Kali WSL home, owned by `wsl` with mode
`0600`, made WSL `claude auth status --json` report the same login method and
subscription when API-key overrides were excluded. The operator procedure and
git-ignored project backup are described in
[CLAUDE-CODE-WSL-AUTH.md](CLAUDE-CODE-WSL-AUTH.md).

Unverified at that point: credential refresh in WSL and authenticated model
requests. The later private-handoff check below established delivery into the
separate actor namespace without a model request.

## N5 private subscription handoff and expired-token failure, 2026-09-25

Observed locally with Claude Code 2.1.273: the root-owned private credential
store and mount namespace delivered the Claude.ai Max login to a UID 65534
actor. The N4 host attestation passed 51 checks and the isolated subscription
status attestation passed eight. These checks consumed no model tokens. The
worker has no API key and the credential is neither in its public package nor
in its inherited environment.

The first bounded Sonnet-low Read-denial sentinel returned a Claude Code
`<synthetic>` result with zero input and output tokens and USD 0 reported
API-equivalent cost. No Read call or served model was observed. After the call,
Claude Code had emptied the access and refresh fields in only its private
invocation copy. The root store correctly refused to commit it. The WSL user
copy and root master still contained both fields. Metadata inspection showed
that their access tokens had expired while their refresh tokens had not. The
failed private copy was verified empty and discarded without changing the
master. This is consistent with a failed headless token refresh; the exact
provider-side cause was not established.

The handoff now rejects credentials with less than five minutes of stated
access or refresh validity before launching an actor. Fresh WSL sign-in and a
repeat of the bounded sentinel are required before N5 paid screen dispatch.
The screen's 60 calls and reserved N6 tasks remain unrun.

Observed later in the same sign-in flow: while `claude auth login --claudeai`
waited for browser authorisation, the WSL user's credential file still had its
Claude.ai metadata but both token fields were empty. The root master and
git-ignored project backup retained their earlier credential bytes. The
checked sync helper rejected the incomplete source before writing the backup.
The WSL login must complete before that helper can promote a fresh token.
Windows `claude auth status` still reported `loggedIn: true` and a Max
subscription while the stored token was too close to expiry for the isolated
worker; this status is not a freshness test. The WSL user's CLI reported
`loggedIn: false` during the pending browser login.

Observed after a new Claude.ai email login on 2026-09-25: WSL Claude Code
reported a Max subscription; the checked sync helper promoted the fresh
credential into the root master and refreshed the git-ignored backup without
changing its ACL. A later digest comparison found the root master, WSL user
copy and backup identical. The renewed subscription status attestation passed
8/8 checks. The second, bounded Sonnet-low Read-denial sentinel passed 7/7:
one Read attempt was denied at the private auth path, the served model was
`claude-sonnet-5`, the actor stayed unchanged and Claude Code reported USD
0.053081 API-equivalent cost. This supersedes the earlier zero-token sentinel
as current N5 subscription evidence. The other fourteen cells remain untested
until the approved screen runs.

## N5 isolated public acceptance, 2026-09-25

Observed locally without a provider call: a fresh WSL copy of a stopped actor
ran `public_check.py` under UID 65534. The Windows bridge returned sealed
acceptance evidence, with the host attestation and four public file hashes
bound to the result. The 55-check host attestation passed the bridge, hidden
evaluator read denial, source preservation and rejection of a self-modifying
public check. Focused acceptance tests also rejected stale isolation proof and
reuse of prior local verification evidence. The hidden oracle grader remains
separate and is the objective quality measure. No live N5 development episode
has been run.

## Q1 multi-file WSL actor boundary, 2026-09-25

Observed locally without a provider call: a separate Q1 namespace and
manifest-bound package let UID 65534 edit two existing nested Python files
while denying new and protected files. Actor Graft found both module markers
but not the root-only evaluator marker; direct, symlink, parent and sibling
paths were denied. Collection required the root-owned launcher stop record,
returned a private snapshot of both edits, and rejected source races,
protected-file drift and duplicate output. The attestation recorded 38 WSL
checks and five root-budget checks; the legacy single-file transport still
passed eight checks. Evidence and reproducible commands are in
[worker-q1.md](stage-results/worker-q1.md).

Unverified: authenticated Claude multi-file edits, paid charge telemetry,
multi-file public acceptance and hidden grading. Q1 did not exercise these
later gates or change the B0 default.

## Q2 public multi-file calibration, 2026-09-25

Observed without a provider call: two pinned, licensed upstream Python
packages were packaged as authored two-file regressions within Q0's
1,000-20,000 source-line stratum. Vendored upstream source and licence bytes
matched the pinned local clones. Six fresh Q1-isolated baseline, partial and
reference grades scored cachetools 10/55/100 and ItsDangerous 30/60/100.
Both references passed public and hidden checks; both partials earned useful
hidden quality but were not accepted. The actor's direct attempt to read each
root-owned oracle was denied. The offline harness now checks the frozen
catalogue, evidence and internally inconsistent rewritten result fields.
The machine result and limits are in
[worker-q2.md](stage-results/worker-q2.md).

Source-inspection finding: the historical D/H fixture codebases contain only
about 13-90 Python source lines, so they cannot support the proposed
target-stratum pilot. These two public families are insufficient for Q0's
eight-task B0 gate; a two-task canary would be diagnostic only. The concurrency
case uses a short scheduling window and needs repeated calibration before a
paid comparison. Unverified: paid Claude multi-file adapter, served model and
effort identity, B0 task difficulty, routing quality, and population effect.

## Q3 subscription multi-file static preflight, 2026-09-25

Verified on the local WSL host without a model call: after fresh Claude.ai
sign-in and checked credential sync, an isolated Q1-named actor running
`claude --restricted auth status --json` reported a subscription login,
produced a root-owned stop record and reconciled the private credential
session. The Q3 attestation passed 28 provider-free checks across launcher
rejection, fake two-file collection, a complete fake B0 TaskExecutor episode
and fresh hidden-grader baseline/reference comparisons. A concurrent drift
of protected `ISSUE.md` was rejected before root write-back. N4 and Q1 host
attestations and Q2's six saved grades were refreshed or revalidated.

The full offline harness passed 66/66 checks. The Q3 sentinel is frozen as a
separate one-call paid gate and has not run. The two-task B0 canary is not
approved or dispatched. Actual Claude multi-file behaviour, cancellation
timing, served effort and API-equivalent cost remain unverified. See
[worker-q3-static-preflight-2026-09-25.md](stage-results/worker-q3-static-preflight-2026-09-25.md).

A later provider-free Q3 timeout probe used a fake adapter that raised before
any Claude invocation. TaskExecutor retained the USD 6 unresolved hold and
actor, returned `uncertain`, and did not replay when called a second time.
This proves the local no-replay path for an absent terminal receipt; it does
not prove cancellation timing or charge reconciliation for a real provider
process.

## Q3 subscription canary and grader stability, 2026-09-25

Observed on the current WSL host: the exact one-call Sonnet-low Read-denial
sentinel passed and reported USD 0.0530436 API-equivalent usage. Its actor
could not read the private auth path. The subsequent two-task B0 canary
completed without an uncertain receipt: P01 cachetools passed on one
Sonnet-low call, and P02 ItsDangerous passed after one Sonnet-low repair.
Both stopped actors passed their hidden oracles at 100/100 with no critical
error or false success. Three provider calls reported USD 0.440517602
API-equivalent usage in total; the served model was `claude-sonnet-5` on each.
The provider did not independently report served effort, so only the
requested low effort is known. The actor revisions changed only their two
allowed source files. Ten provider-free repeat grades each of P01's baseline
and candidate were stable at 10/100 and 100/100 respectively, with the
actor unchanged. The full offline harness passed 66/66 checks. Exact evidence,
patch review and limits are in
[the Q3 canary result](stage-results/worker-q3-canary-2026-09-25.md).

Inference and limit: these two examples reached full B0 acceptance, so they
cannot demonstrate final-quality benefit from task-sensitive first-cell
routing. Their small sample does not invoke Q0's eight-family ceiling rule.
Six more distinct public families need their own issues, oracles and paid
manifest; [candidate sources](WORKER-Q3-EXPANSION-INVENTORY-2026-09-25.md)
have been pinned but are not yet completed tasks. No claim about a reserved
population or a production routing change follows from this canary.

## Q3 eight-family public B0 gate, 2026-09-25

Observed: six additional independently pinned public source families passed
provider-free source, licence, grader and isolation checks. Their six B0
episodes used one Sonnet-low call each, all settled, and reported USD
1.774540602 API-equivalent usage. Combined with P01/P02, B0 hidden acceptance
was 3/8, mean hidden quality was 87.5/100, and five incomplete outcomes were
public-pass/hidden-fail. Nine calls across the eight tasks reported USD
2.215058204 API-equivalent. All reported `claude-sonnet-5`; served effort was
not independently visible. The independent patch review and exact evidence
are in [the Q3 result](stage-results/worker-q3-public-2026-09-25.md).

Source-inspection finding: P07's two 5-point hidden misses require `TypeError`
for malformed pickle states. The actor raised package-specific `ValueError`
subclasses, which do reject malformed state. Since the public issue specified
validation but no exception type, these misses are rubric-disputed; the frozen
90-point grade remains unchanged. P08 made broad cross-platform edits, leaving
untested regression risk outside its 90-point hidden grade.

Inference: the 3/8 result is within Q0's public difficulty window of two
through six acceptances. It justifies a bounded candidate screen, not a claim
that task-sensitive routing beats B0 or a change to the shipping default.
Run variation on the harder public tasks and the value of a more expensive
first cell remain unverified. No Q4 reserved task has run.

## Graft Q3 deep refresh, 2026-09-25

Observed: the standing-approved `tools/graft_deep_refresh.ps1` updated the
structural graph to 8,520 nodes, 18,064 edges and 817 cards. Its deep pass
exited 1 with 4,822 computed, 2,963 cached, eight stale and 727 pending
meanings. Five large source files returned truncated symbol summaries, and
`tools/task_executor.py` returned an unparseable tool response. A subsequent
Graft MCP freshness check said the graph was in sync with code but identified
eight stale summaries under `tools/task_executor.py`. Installed Graft's
per-symbol summary request caps output at 8,192 tokens. The DeepSeek usage and
charge for this refresh were not exposed; neither is assumed to be zero.

Inference: structural Graft retrieval is current, while semantic summaries
are incomplete. Rerunning the same paid deep request without addressing the
truncation and tool-response failures has low expected value. Scoped repair
and a cached retry remain open.

Later on 2026-09-25, the local DeepSeek proxy was changed to raise the
`record_symbols` output cap from 8,192 to 32,768 only for configured
`deepseek-flash` calls, and to report aggregate token usage without response
content. A cached deep retry then resolved five of the six failed source
files. It ended with 8,511/8,520 meanings covered, eight stale summaries and
one pending file, all under `tools/task_executor.py`; that file again returned
an unparseable tool response. Graft MCP confirmed that the structural graph
remains in sync. The retry reported 12 calls, 146,478 input tokens including
144,382 cache reads, and 85,667 output tokens, with no missing usage fields.
At [DeepSeek Flash's published 2026-09-25 off-peak rates](https://api-docs.deepseek.com/quick_start/pricing/),
this is about USD 0.05215 API-equivalent; peak-rate sensitivity is about USD
0.10430. This is a price calculation from provider token counts, not a
verified invoice. The first deep pass's charge remains unknown. A further
identical paid retry is not justified; the remaining tool-response failure
needs a separate parser or request-shaping diagnosis.

## Q3 contract audit and first-cell attribution, 2026-09-25

Observed in provider-free isolated WSL probes: P03's stopped patch returns
the requested sorted command and option suggestions but omits a colon that
the hidden grader requires. The public issue also never requests the exported
exception class required for another ten points. P07 rejects malformed state
using package-specific exceptions rather than the hidden oracle's unspecified
`TypeError`. The [audit record](stage-results/worker-q3-contract-audit-2026-09-25.md)
preserves exact outputs, original hashes and unchanged frozen grades.

Inference: treating those disputed obligations as contract-equivalent changes
the pilot sensitivity from 3/8 and 87.5 to 5/8 and 94.375. It leaves at most
5.625 mean executable points of improvement on the tested cases. This is
retrospective sensitivity, not a new grade, a model comparison or proof of
correctness on untested behaviour.

Source-verified: Q3 executable grading does not credit diagnosis or reporting;
its `false_success` denotes a public/hidden acceptance gap, not an observed
false statement. All P03-P08 critical flags are disabled. The experimental
executor changes both the first and second cell, so a new common-tail version
is required for first-cell attribution. These findings supersede the earlier
inference that the pilot alone justifies an immediate paid candidate screen.
The [implementation amendment](WORKER-Q4-MEASUREMENT-AND-FREEZE-2026-09-25.md)
specifies the repairs before further screening. B0 and historical evidence
remain unchanged; no Q4 reserved outcome exists.

## Q4R missing structured output and Q4S screen, 2026-09-26

Observed: Q4R's Sonnet-high P08 call settled at USD 0.6894318
API-equivalent, returned a terminal `success` event without
`structured_output`, and made no edit to the four permitted source files.
The stopped patch passed two of eight executable cases. Both Sonnet-low B0
repetitions returned valid reports and scored 85/100, which establishes that
the schema was satisfiable on this task. The generic root-identity check also
encountered a synthetic model marker; requested effort was not independently
observed. The [investigation](stage-results/worker-q4s-transport-investigation-2026-09-26.md)
records the receipt and instrumentation limits.

Inference: a successful CLI terminal subtype alone cannot establish a valid
report. Q4R correctly failed closed, but its compact receipt cannot explain
why this report was absent, and its campaign needed manual reconciliation of
a settled terminal failure. The absent report and absent edits are separate
observations; their causal relationship is unknown.

Unknown: the validation retry count, whether a single request reached its
output ceiling, why the agent made no source edit, and whether any CLI or
model behaviour caused the missing object. No historical score or budget was
changed. The [prospective Q4S plan](WORKER-Q4S-PROSPECTIVE-CANDIDATE-SCREEN-2026-09-26.md)
first strengthens evidence and settlement, then tests a predeclared
Sonnet-medium trigger on six new upstream-backed families. B0 remains the
default; Q5 remains gated.

## Q4S provider-free admission and evidence, 2026-09-26

Observed with Claude Code 2.1.273 and the separate Q4S WSL launcher: the
source-bound authentication and actor probe passed 12 boundary checks with
zero provider calls. Seven fake-stream regressions passed for missing
structured output, terminal failure settlement, model identity and no replay.
The [S1 record](stage-results/worker-q4s-s1.md) links the exact evidence.

Inference: the Q4S-only receipt and journal can preserve and score a settled
missing-report failure prospectively without changing the frozen Q4R result.
The WSL probe verifies that the actor receives the 20-turn and two-retry
environment controls. A live Claude run has not yet shown how those controls
affect task completion. Q4S S2 must freeze the independent corpus before S3
can test that question.

## X4 live Controller checkpoint and uncertainty gate, 2026-09-28

Observed in WSL Claude Code 2.1.273 with Claude.ai subscription auth: the
third synthetic Controller run reached a Sonnet Low stability call that
settled USD 0.1035346 but failed at its USD 0.10 per-call cap. The runtime
silently substituted the Framer's `stable=True`. A source fix increased the
classifier reservation ceiling to USD 0.25 and made failed live
classifications terminate as accounted gaps. The provider-free budget suite
passed 34/34 and the checked consumer build exited zero.

Observed in a fresh fourth run: both Controller classifications returned
structured results, all 17 role calls had matching served root-model
identities, and the budget settled USD 3.227475305 with no hold. The run
reached two Generator families, Critic and Selector. It ended as a
`no_improvement` gap because five load-bearing premises remained unverified
in a statement-only investigation task. The first Critic reply exceeded
record field caps; its bounded retry produced valid critiques. No live
Controller solution, worker handoff or quality uplift is claimed from this
probe. The [X4 record](stage-results/controller-x4-progress-2026-09-28.md)
contains the stage implications.

Inference: the strict candidate gate usefully prevents an unconditional
answer from passing on missing facts, but its generic gap text loses the
specific conditional next step this task asks for. A partial-result path
should preserve the uncertainty, candidate provenance and next discriminating
measurement without labelling the task accepted. Whether this improves
real-task quality is untested and belongs in X5 comparison.

Provider-free follow-up: the no-eligible-candidate path now preserves its
`gap` outcome and names the first unverified premise's proposed evidence check
in `next_cheapest_test`. An end-to-end fake run verified the result stays
unaccepted; the focused integrity and budget suites passed 45/45 together,
and the checked bundle build passed. A live quality gain is not established.

## X5 recovery R3/R4 headroom and settlement contract, 2026-09-30

Observed on the installed WSL Claude.ai subscription host: a successful
`claude auth login --claudeai` refreshed the unprivileged login, but the
root-owned worker credential store remained expired until its guarded `sync`
operation promoted that login. No task or provider call had started before
the sync. The R3 R01 producer then settled one terminal, writer-stopped,
identity-valid `claude-sonnet-5` receipt at USD 0.16955 API-equivalent. The
host-run public check passed, while protected grading later found one
critical replay miss, yielding 85/100. The frozen eligibility helper rejected
the producer early because it expected Boolean `false` for
`budget.unresolved`; the settled TaskExecutor value was an empty list. After
a provider-free repair and test-fixture correction, the original stopped root
reconciled to `no publicly observable unresolved work` without a new call.

Observed in the separately approved R4 R02 case: the full prelaunch offline
harness passed 83/83, the producer settled one valid `claude-sonnet-5` receipt
at USD 0.1179006 API-equivalent, and both public and protected checks passed
on its first attempt at 100/100. R3 and R4 together spent USD 0.2874506
API-equivalent. Neither producer met the predeclared public recovery rule, so
no matched Controller or direct-worker successor ran. The R3 and R4 result
records are in `stage-results/`.

Inference: this development case mix gives the proposed public-failure
recovery route no entry opportunity. R01's protected miss cannot be used as
a retrospective Controller trigger. Additional paid producers from the same
easy-task pattern would not estimate Controller uplift.

Unknown: whether a prospectively selected distribution with genuine public
failures would let a Controller handoff improve over a direct second worker,
and whether any selective public-success review trigger would outperform its
cost. B0 remains the default; the X6 reserve was not accessed.

## X5 P02 first-failure smoke, 2026-09-30

Observed: P02's baseline public check failed and its reference passed in the
isolated provider-free probe, with protected quality 30/100 and 100/100
respectively. The frozen engineering smoke passed its 83/83 repository gate,
manifest, host and credential preflight. One new Sonnet-low producer returned
terminal, writer-stopped and identity-valid at USD 0.113327401 reported
API-equivalent. It passed public and protected acceptance on the first
attempt. The root had no unresolved charge or budget breach. Neither S nor A
started. P02 had failed its first public check in the earlier Q3 canary.

Inference: a historical first failure on P02 did not supply a reliable new
Controller intervention point on this host. It cannot be replayed or counted
as a prospective effect unit. R3, R4 and this P02 smoke together reported
USD 0.400778001 API-equivalent and yielded zero matched Controller pairs.

Unknown: the first-attempt public-failure rate on a new, independently
predeclared upstream issue set, and whether a Controller investigation would
improve one matched repair call once such a failure occurs. The result is in
`stage-results/controller-x5-first-failure-p02-smoke-result-2026-09-30.md`.

## X5 F01 fresh development case, 2026-09-30

Observed: a new authored two-regression case on pinned `attrs` source failed
all three public checks at baseline, with protected quality 2/6. A one-module
partial repair still failed public and reached 4/6. The upstream reference
and a distinct alternative repair both passed public and 6/6 protected. The
final offline harness passed 83/83; the WSL packet and protected grader probe
passed without provider calls. The single live producer settled one terminal,
writer-stopped, identity-valid Sonnet-low receipt at USD 0.1270084 reported
API-equivalent. It passed public and protected acceptance on its first call,
scoring 100/100 with zero critical errors. No S or A successor started.

Inference: stronger authored baseline defects alone did not yield a public
first-failure checkpoint on this case. F01 cannot be replayed or counted as a
matched Controller effect. R3, R4, P02 and F01 together reported USD
0.527786401 API-equivalent and yielded zero matched Controller pairs.

Unknown: the failure rate and Controller effect on a broader independently
frozen issue set. The Controller's exact failed-report path remains untested
in a paid continuation. The [F01 result](stage-results/controller-x5-first-failure-f01-result-2026-09-30.md)
records the closed root. B0 remains the default; X6 remains sealed.

## X5 F02 styled-help development case, 2026-09-30

Observed: a new authored two-module Click regression on pinned source failed
two of three public checks at baseline and passed 3/7 protected cases. A
one-module partial repair still failed public and passed 6/7. The upstream
reference and a separate explicit ANSI-stripping repair passed public and
7/7. The full offline harness passed 83/83 and the WSL packet probe passed
without provider calls. The single live producer settled a terminal,
writer-stopped, identity-valid Sonnet-low receipt at USD 0.0695534 reported
API-equivalent. It passed public and protected acceptance on its first call,
scoring 100/100. No S or A successor started.

Inference: the first-failure-only entry rule has yielded no eligible matched
pair across five producer screens, totaling USD 0.597339801. Another similar
synthetic screen would offer limited new evidence. F02 cannot be replayed.

Unknown: whether realistic ambiguous issues create sufficient public-failure
headroom, or whether a public-only risk signal after apparent success would
identify useful Controller investigations. Neither hidden scores nor prior
case outcomes may retrospectively select a trigger. See the
[F02 result](stage-results/controller-x5-first-failure-f02-result-2026-09-30.md).
B0 remains the default and X6 remains sealed.

## X5 F03 cancellation development case, 2026-09-30

Observed: a Tenacity case adapted from a public cancellation report and an
authored second regression failed all three public checks at baseline and
passed 4/9 protected cases. An async-only partial repair still failed public
and passed 7/9. Two different complete repairs passed public and 9/9. The
full offline harness passed 83/83; WSL packet and protected grading passed
without provider calls. The live producer settled one terminal,
writer-stopped, identity-valid Sonnet-low receipt at USD 0.2023272 reported
API-equivalent. It passed public and protected acceptance on its first call,
scoring 100/100. No S or A successor started.

Inference: six first-call screens now total USD 0.799667001 and have yielded
zero eligible matched Controller pairs. F03 cannot be replayed. The
first-failure-only route should not consume more of the same task shape.

Unknown: whether a distinct task distribution or a public-only post-success
risk signal gives Controller useful headroom. Both require fresh prospective
cases and a fair direct-worker control. See the
[F03 result](stage-results/controller-x5-first-failure-f03-result-2026-09-30.md).
B0 remains the default and X6 remains sealed.

## X5 public-risk review mechanism, 2026-09-30

Observed: a development-only accepted-root checkpoint now validates one
settled, writer-stopped, identity-valid B0 public success, an independently
rerun public check and a source-cited risk record bound to a frozen digest.
It creates equal single-use S/A public actor snapshots. Fake-provider tests
reject open charges, active writers, invalid identity, absent risk decisions,
changed citations, public regression, extra actor files and replay. The full
offline harness passed 83/83 with no provider calls for this mechanism.

Inference: accepted roots can be safely compared on a new review task using
fresh successor roots, if a public-only risk rule and fresh corpus justify
the extra work. This does not establish a Controller benefit.

Unknown: whether fresh public-risk cases retain a protected quality gap
after a normal first worker call, whether A beats a direct worker review S,
and whether its incremental cost is justified. The
[design](stage-results/controller-x5-public-risk-review-design-2026-09-30.md)
keeps the next paid campaign gated. B0 remains the default and X6 sealed.

## X5 K01 public-risk review stop, 2026-09-30

Observed: a fresh PyJWT-backed tenant rotation case and two negative rubric
packets were frozen. Its baseline, narrow repair and two complete repairs
calibrated as expected. The full offline harness passed 83/83 before the
live producer and after the continuation repair. The producer accepted public
behaviour for USD 0.0748108, and the direct S review accepted public behaviour
for USD 0.1009298. A's public assessment and Controller investigation
settled USD 0.044417801 and USD 0.854538 respectively. The Controller
handoff cited source but gave a generic next action, not the predeclared
issuer check. A's Q3 Graft build failed with `umount: /mnt/c: target is busy`
before the worker provider invocation; the resulting uncertain worker hold
was reconciled at USD 0 and the root blocked. The K01 settled subtotal is
USD 1.074696401 reported API-equivalent. No protected oracle was read.

Inference: running the worker build inside the Controller's private
evaluation mount view may cause the nested unmount failure. The original
rotation issue also framed Controller's investigation after public success,
while the active task should have been the frozen residual-risk review.
These hypotheses require provider-free boundary tests before another paid
case. K01 supplies no matched quality effect and must not be replayed.

Unknown: whether a distinct review goal and separated Controller/worker
phases can produce a source-cited discriminating handoff, and whether that
handoff improves protected outcomes over an identically informed direct
worker. See the [K01 stop](stage-results/controller-x5-public-risk-k01-stop-2026-09-30.md).

## X5 K02 public risk closure, 2026-09-30

Observed: the provider-free phase split and equal review-goal checks passed;
a Q3 Graft build succeeded after exiting the hidden Controller mount view.
The checked `dist/` build completed and the final full offline harness passed
83/83. A fresh Tenacity-backed payment case calibrated baseline, narrow and
complete repairs. One B0 producer settled a public success for USD
0.086191601 reported API-equivalent. It added a bounded retry with the
payment ID as idempotency key. The predeclared public post-debit timeout
check then showed one debit and stable receipt for repeated payment ID,
with distinct IDs independent. S and A were admitted but used zero provider
calls; the protected oracle was not executed.

Inference: the ordinary producer resolved the observable duplicate-debit
premise, so the post-success review no longer had eligible public risk.
More self-contained authored regressions of this size are unlikely to
establish a useful Controller headroom distribution. This is not a matched
quality result or a proof that Controller cannot help harder tasks.

Unknown: which real multi-system task distribution has a consequential
publicly observable gap after an ordinary repair, whether Controller can
produce a discriminating source-cited handoff on that distribution, and
whether A beats the same direct worker review. See the
[K02 result](stage-results/controller-x5-public-risk-k02-result-2026-09-30.md).

## X5 external-validity audit, 2026-09-30

Observed: primary upstream reports for urllib3, Requests, Go net/http and
SQLAlchemy describe genuine multi-boundary failures, but the first three
publish the repair or candidate fixes in their issue text. The SQLAlchemy
case has an intermittent database-dependent reproducer and a suspected
code location. None is currently a blind, deterministic X5 actor with an
independently qualified acceptance oracle. No provider call was made in
this audit.

Inference: more short authored regressions or direct reuse of a public
fix report are unlikely to measure incremental Controller value. A natural
issue package needs a reproducible public symptom, a separately frozen
public residual-risk check, protected safety checks and a prospectively
planned sample before paid screening. A generic Controller handoff must
count as a failure, not as recovered quality.

Unknown: whether this host can source enough natural issue packages with
observable post-repair risk, and whether Controller improves S at acceptable
cost when such a package exists. See the
[external-validity audit](stage-results/controller-x5-external-validity-audit-2026-09-30.md).
B0 remains the default and X6 remains sealed.

The first external preflight reproduced pytest-asyncio #1501 on the signed
v1.4.0 source tag with pytest 9.1.1 on Windows and the actual WSL host:
original test order gave one pass and one fixture error; reversed order and
no-hook controls each passed two.
The unchanged upstream loop-factory suite passed 40/40. An unmerged proposal
applied to a separate v1.4.0 copy passed the issue repro and existing 40
tests. A new two-factory check distinguished baseline collection (4 cases)
from the proposed repair (5), while preserving one ordinary sync case.
This is provider-free calibration of one candidate repair, not a frozen X5
effect case; broader independent compatibility, an alternative repair and
post-repair public-risk checks are still missing. See
[E01 preflight](stage-results/controller-x5-external-e01-preflight-2026-09-30.md).

## X5 opening-event retrieval and UTF-8 verification, 2026-09-30

Verified on GitHub's public repository Events API and Windows Python 3.14:
the first `pallets/werkzeug` event page had 18 adjacent timestamp inversions.
Do not infer a complete creation-time window by stopping at the first older
event. The frame E collector stopped without writing an invalid frame, then
used an explicitly first-page cohort. [GitHub documents](https://docs.github.com/en/rest/activity/events)
a 300-event, 30-day timeline and possible delivery latency; a first page is not an
exhaustive time-window denominator. See the
[frame E protocol](stage-results/controller-x5-opening-event-frame-e-protocol-2026-09-30.md).

Verified on this Windows Python host: reading a UTF-8 JSON body snapshot
with `Path.read_text()` without an encoding decoded a Unicode arrow through
the default code page, producing a false hash mismatch. Reading with
`encoding="utf-8"` matched all frozen title and body digests in frames E
and F. The archived files themselves retained their recorded SHA-256 values.
This is a verifier encoding issue, not evidence of source-body drift.

## X5 authored httpcore pool schedule, 2026-09-30

Verified on the copied httpcore 1.0.9 source on Windows Python 3.14 and the
Kali WSL Python host: an idle connection assigned to a queued request can be
selected for closure on a second pool pass in both sync and async pools. A
sync-only one-path repair passed the competing-origin public check but failed
the independent surplus-idle and async checks;
two different complete repairs passed both checks and the normal reuse,
removal, capacity and unassigned-expiry controls. The saved
[calibration](stage-results/controller-x5-httpcore-authored-preflight-2026-09-30.md)
is a deterministic state-window result using fake connections, not an
observation of an actual network timeout or AI worker difficulty. The
published issue and PR already reveal the mechanism, so this is an authored
development case only.
An unprivileged WSL namespace denied the protected oracle to all four actor
variants. A separate evaluator-owned comparison scored baseline 25, partial
50, two complete repairs 100, and both a changed protected issue file and a
test-framework spoof as critical quality 0. These checks exercise the specific
actor boundary and controls,
not all adversarial ways to spoof child observations.

The H01 B0 producer later settled one USD 0.214186 provider-reported
API-equivalent call and scored 100/100 on the frozen four-check grader. Its
first-pass stop left S/A unrun. A distinct post hoc Q1 isolated probe found
that the settled repair still closes a connection assigned to a queued
request when it becomes expired before the next pool pass, in both sync and
async implementations. Two pre-existing complete calibration repairs retained
assigned connections and still expired unassigned ones. This observation
does not revise H01's frozen score. It shows that the grader omitted an
important cleanup path, so H01 is retired from paid comparison and supplies
no Controller uplift evidence. The fake-connection schedule does not establish
a real network timeout. See
[the settled result and post hoc audit](stage-results/controller-x5-h01-producer-result-2026-09-30.md).
