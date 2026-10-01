# Handoff: worker-n8-b0-packaging

<!-- handoff.py new --slug worker-n8-b0-packaging --reason model-change --to-model gpt-5.6-sol --to-effort high -->
Written 2026-09-27 Australia/Sydney by Codex. Reason: model-change.

## Goal

Complete N8 consumer integration and release preparation for the qualified B0
worker path and N1-N3 mechanics. Verify clean installation, upgrade, rollback
and interactive behaviour, then hand the actual worker result to Controller X0.

## Decisions already made

- [N7's independent decision](../docs/stage-results/worker-n7-2026-09-26.md)
  rejects Q4U as an automatic default. Keep B0 shipping; expose any Q4U path
  only as explicitly experimental. The ten-episode development canary had zero
  paired quality gain, while cost and latency rose in matched cells.
- N6 stopped before the four reserved tasks under its predeclared negative or
  ambiguous development gate. Its reserved-comparison exit remains unmet. Do
  not run reserved cases to manufacture a promotion claim.
- N7 reproduced a hidden-grader false-full-credit exploit and found an
  incomplete execution-dependency seal. No further paid Q4U calls are
  justified. Future evaluation infrastructure must repair these boundaries.
- Controller X0-X8 have not started. Controller work follows N8 and uses this
  negative worker result. Do not commit, merge, tag or publish in N8 without
  separate applicable operator direction.

## Files and links that matter

- `docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md` (N8 contract)
- `docs/stage-results/worker-n7-2026-09-26.md` (release adjudication)
- `docs/stage-results/worker-n6-pre-reserve-disposition-2026-09-26.md`
- `docs/stage-results/worker-q4u-u3-canary-2026-09-26.md`
- `test/results/2026-09-26-worker-n7-grader-probe.json`
- `test/results/2026-09-26-worker-n7-dependency-audit.json`
- `src/ORCHESTRATOR_CORE.md`, `src/ROUTING.md`, `src/LIFECYCLE.md`,
  `src/SELF-LEARNING.md`, `src/README.md`, root `README.md`.
- `tools/build_dist.py`, `test/harness/check.py`, `docs/GRAFT.md`, `CLAUDE.md`,
  `AGENTS.md`, and `docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md`.

## Verified facts

- Branch `v1.0-rc1`, HEAD `15ecf66`; extensive pre-existing dirty and
  untracked work must be preserved. No commit in this stage.
- The operator reported GPT-6 Astra / High for N7; the host did not expose its
  setting for independent verification.
- Q4U's ten settled Claude Code subscription calls total USD 1.022577203 in
  API-equivalent usage. All hidden scores and public checks were 100/pass, all
  six paired quality deltas zero, and every episode used one call. Actual
  subscription invoice impact and served effort are unknown.
- A provider-free disposable probe changed one allowed actor file and made a
  baseline hidden score of 15 appear as 100. No live exploit was observed.
  Static import audit found 18 directly imported local Python modules outside
  the frozen 16-file Python source seal, plus unbound runtime JSON.
- Graft MCP was used for N7. Structural retrieval worked; the earlier deep
  semantic refresh remained partial after three unparseable summaries. Do not
  claim complete semantic coverage or repeat the unchanged paid request.
- N7's full offline harness result is recorded in its stage result. Recheck
  after any N8 source change and rebuild `dist/` through the builder only.

## Work completed

N7 adjudication, static dependency audit, disposable grader attack probe and
machine-readable receipts were written. Q4U's experimental executor and
historical receipts were preserved. The shared `tools/task_executor.py` pinned
Q4 source SHA-256 remains
`64cd58eafe128649f61dc865d875f3161f6f12cb3932ff487abbfd1c1450706c`.
N8 consumer changes have not begun; HEAD is unchanged.

## Unresolved questions

- N8 must establish clean consumer install, upgrade, rollback, source/bundle
  parity, interactive task admission, explicit cell choice, cancellation,
  resume and nested budget behaviour. Do not infer these from N7 review.
- Document supported launch mechanisms separately from prompt-only
  obligations. Verify whether B0 and N1-N3 are wired in the redistributable.
- The root-owned campaign journal may need WSL root read access. Windows
  sandbox WSL calls may return `E_ACCESSDENIED`; escalated WSL was used.
- Controller X0-X8 remain a separate later programme. The host must set the
  next task's actual model and effort; this task cannot verify that setting.

## Exact next action

After the operator sets GPT-5.6 Sol / High, call `graft_check_freshness` for
`C:\Users\Bob\Desktop\Code\Claude\Orchestrator` and use scoped Graft
retrieval. Read the N8 contract and N7 decision, inventory current consumer
source and bundle boundaries, then implement the B0 documentation and
interactive wiring. Run the offline harness before `tools/build_dist.py`, test
clean install/upgrade/rollback and interactive flows with fake adapters first,
record evidence, and write the Controller X0 transition handoff.

## Model and effort to set

`/model` gpt-5.6-sol, effort high. This is the N8 plan's requested setting;
the host must apply it and report it, as this session cannot inspect it.

## Cost projection

**Next development session, direct OpenAI API-equivalent projection:** USD
**2-15** for 3-5 hours of GPT-5.6 Sol / High engineering. This is not a
quoted Codex subscription charge. At 2026-09-27, [official OpenAI model
pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol) lists
Standard USD 4 uncached input, USD 0.40 cached input, USD 5 cache writes and
USD 20 output per million tokens. [Fast pricing](https://developers.openai.com/api/docs/pricing)
is USD 8, 0.80, 10 and 30 respectively. Assumed
range: 0.2-0.8M ordinary input, 0.2-1.0M cached reads, 0.02-0.10M cache
writes, 0.03-0.15M output including reasoning. Standard arithmetic gives
USD 1.58-7.10; the high Fast calculation is USD 12.70, rounded with
uncertainty to USD 2-15. A request over
272K input tokens, actual cache mix, service tier, hosted tools and retries
could raise it. No cross-model cache carryover is assumed. **New Claude paid
experiment calls: zero projected**; any proposed smoke run requires a new
dated spend notice and fixed manifest. Historical Q4U spend is excluded.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**N8 elapsed engineering time: 3-5 hours**. Provider-free install and fake
adapter checks are included; any authentication or operator wait is extra.
Controller X0-X8 work is outside this estimate.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
