# Handoff: worker-q4-measurement-repair

<!-- handoff.py new --slug worker-q4-measurement-repair --reason model-change --from-model gpt-6-astra --from-effort high --to-model gpt-5.6-sol --to-effort high --project . -->
Written 2026-09-25 by gpt-6-astra, high. Reason: model-change.

The source setting above records the requested architecture-stage model. This
host does not independently expose the active model or reasoning setting.

## Goal

Implement M1 and M2 of the Q4 measurement/freeze contract: evidence-based partial
quality and reporting, then equal repair tails and public WSL calibration.
The operator has authorised work through Q4. Stop before Q5 reserved dispatch.

## Decisions already made

- Follow `docs/WORKER-Q4-MEASUREMENT-AND-FREEZE-2026-09-25.md`. Architecture
  decisions are specified there; implement them without inventing a new study.
- B0 remains the shipping default. Old Q3 scores, source/oracle hashes, receipts
  and one-shot runners remain unchanged. Never rerun Q3 expansion `--run`.
- No paid screen until M1/M2 pass. M3 is bounded at USD 99 local allocation,
  but still needs an exact manifest, fresh dated spend notice, host evidence
  and approval record citing the standing authorisation. Do not ask again
  merely because a new manifest hash was generated. Ask for scope beyond the
  standing authority or the project rule above USD 100.
- Use authenticated Claude Code in WSL `kali-linux`, never a Claude API key.
- Q4 is not frozen. If M3 supplies no worthwhile candidate, retain B0 and
  stop corpus construction with an explicit no-candidate decision.
- No subagents, commit, push or release are required. Preserve the dirty
  worktree. Developer-only artefacts do not require a `dist/` rebuild; shared
  shipped executor changes do, through `tools/build_dist.py` after checks.
- Graft MCP is required. Check freshness on resume, then scoped discovery.
  The root is `C:\Users\Bob\Desktop\Code\Claude\Orchestrator`. Eight semantic
  summaries in `tools/task_executor.py` remain stale; use exact source spans.
  Do not repeat a paid deep rebuild for this known request-shaping failure.

## Files and links that matter

- `AGENTS.md`, `CLAUDE.md`, `src/LIFECYCLE.md`, `docs/GRAFT.md`.
- `docs/WORKER-Q4-MEASUREMENT-AND-FREEZE-2026-09-25.md`.
- `docs/WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md` and Q2 companion.
- `docs/stage-results/worker-q3-contract-audit-2026-09-25.md`.
- `tools/worker_q3_contract_audit.py` and
  `test/results/2026-09-25-worker-q3-contract-audit.json`.
- `tools/worker_adapter.py`, `tools/task_executor.py`,
  `tools/worker_wsl_q3_adapter.py`, `tools/worker_wsl_namespace_q3.sh`,
  `tools/worker_wsl_q3_public.py`, `tools/worker_wsl_q2_verify.py`.
- `test/harness/worker_q3_contract_audit_tests.py`,
  `test/harness/worker_experimental_dispatch_tests.py`, `test/harness/check.py`.
- `test/fixtures/worker_q3_public/`, `test/oracles/worker_q3_public/`,
  `test/results/2026-09-25-worker-q3-expansion-evidence.json`.

## Verified facts

- The new root-owned WSL audit ran with zero provider calls and returned
  `PASS`, digest `cccb964a8127908ec44cc6abb2c3dda914fe1e270cec47ad9b2c64f21b685278`.
- P03 outputs sorted multi-suggestions with a missing colon relative to the
  oracle. Its public issue does not require the oracle's new exception class.
  P07 rejects invalid states with valid package-specific exceptions. Old
  grades remain 55 and 90, both hidden-fail. Retrospective contract sensitivity
  is 5/8 and 94.375 across the pilot, versus frozen 3/8 and 87.5.
- Source inspection confirms the Q3 grader omits diagnosis/reporting, treats
  root-pass/hidden-fail as `false_success`, and has no enabled critical cases
  in P03-P08. `WorkerAdapter.run` discards final result text. The experimental
  ladder changes both initial and retry cell. The Q3 adapter AND launcher
  restrict cells to Sonnet-low and Opus-high.
- Four focused audit regression tests passed. `python3 test/harness/check.py`
  passed 69/69 checks at `15ecf66`, including 75-file source/bundle parity and
  all 19 handoffs. Prose validation passed on 670 files. `git diff --check`
  passed and the saved audit's source/evidence hashes were rechecked.
- Exact-power calculations for 24/48/72 families under win .25/loss .05 are
  .2835/.6754/.8736; under .35/.05 they are .5758/.9280/.9900. These are
  hypothetical marginal powers, not estimates of the candidate's effect.

## Work completed

Completed provider-free Q3 contract audit, its evidence and regression tests,
plus the M1-M4 implementation design. Corrected the interpretation and next
action in Q3 results, Q0/Q2 protocols, findings and the worker roadmap. Added
the audit test to the full harness. Nothing committed. Branch `v1.0-rc1`, HEAD
`15ecf66`; many prior changes are present and must be preserved. No paid
experiment, reserved construction or consumer change was made in this review.

## Unresolved questions

- Live final-report capture is not implemented or proven. Make its schema,
  revision binding and transport-error classification testable in M1/M2.
- A new multi-cell launcher and common-tail experimental version do not exist.
  Keep old experiment semantics under their original version.
- No public screen candidate has qualified. Fable and higher effort are not
  presumed better; the planned economical screen compares Sonnet-xhigh and
  Opus-high with two B0 repetitions on four public families.
- No Q4 reserved inventory or freeze exists. Twenty-four independent source
  families require substantial curation and still offer limited power.
- Requested effort is observable; served effort may remain unreported.
  Subscription invoice impact and development-session billing are unknown.

## Exact next action

After the operator selects GPT-5.6 Sol High, read this handoff and run Graft
freshness. Read M1 of the implementation contract, retrieve the adapter stream
parser and existing grader via scoped Graft, then implement the versioned
quality/report schema and its negative tests without touching Q3 frozen files.
Complete M1 before M2's live-boundary implementation. Keep Sol High through
bounded implementation; no new switch is needed just because M1 ends. Reprice
and issue the M3 notice only after M1/M2 pass. Stop before Q5.

## Model and effort to set

`/model` gpt-5.6-sol, effort high.

Select **GPT-5.6 Sol / High** in the Codex model controls, then continue this
task. The host has no exposed tool to change its own active model setting.

## Cost projection

Estimated direct OpenAI API-equivalent cost for **M1-M2 development only**:
**USD 4-20**, approximately 4-8 hours. This is an estimate, not measured billing.
Assume .25-.75 million ordinary input tokens, .50-1.50 million cache reads,
.05-.15 million cache writes and .05-.15 million output/reasoning tokens,
with input categories mutually exclusive. At Standard short-context rates,
`4I + 0.4R + 5W + 20O` gives USD 2.45-7.35; 30% contingency gives about USD
3.19-9.56, and Fast at twice Standard gives an upper USD 19.11. The stated
range is rounded for planning. Cache misses, longer context and retries may
exceed it. Hosted tools, additional Graft refreshes and later stages are not
priced here and are not assumed free.

Official sources fetched 2026-09-25: [GPT-5.6 Sol model](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [Fast mode](https://developers.openai.com/api/docs/guides/fast-mode).
Per million tokens the model page lists USD 4 input, .40 cached input and
20 output, with cache writes at 1.25 times ordinary input. High is supported.
The selected host service tier, actual cache behaviour and usage are unknown.

No Claude paid calls are needed for M1-M2. The later M3 **USD 99** is a maximum
local admission allocation, not its projected charge; create a separate dated
prediction and exact manifest before running it. The historical Q3 total remains
USD 2.215058204 API-equivalent plus its separate sentinel. This audit added zero
provider experiment cost. Q5 remains separately approved and unlaunched.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**4-8 hours** for M1-M2 development, focused tests, provider-free WSL calibration
and the offline harness, excluding operator delay. This does not include M3's
live screen or M4's independent corpus curation. Re-estimate those stages from
the completed boundary and source inventory rather than treating this as a
whole-programme forecast.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
