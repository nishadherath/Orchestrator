# Handoff: controller-routing-stage-0

<!-- handoff.py new --slug controller-routing-stage-0 --reason model-change --to-model gpt-5.6-sol --to-effort high --project . -->
Written 2026-09-18 by the planning session. Reason: model-change.

## Goal

After operator review of the proposal, execute Stage R0 of the Controller-aware
routing programme. Establish the baseline and executable contracts for automatic
Controller dispatch, operator overrides and the full model/effort matrix.

## Decisions already made

- User requirements: suitable tasks use Controller automatically; interactive
  manual on/off overrides win; Sonnet, Opus and Fable plus all five efforts
  must be usable appropriately; useful partial outcomes count in evaluation.
- The proposed design separates workflow selection from model/effort selection.
  All implementation details and numerical gates remain subject to plan review.
- Keep historical B0 and its evidence intact. Introduce a new policy version;
  do not promote it before reserved validation and installed-consumer checks.
- No paid provider calls in R0. No new agents or model switch merely because
  a stage ends. Preserve pre-existing uncommitted work.
- Graft MCP is mandatory on every task/resume. Each receiving session checks
  its own access and freshness before scoped discovery; use exact reads for edits.

## Files and links that matter

- Repository: `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`.
- [Plan](../docs/CONTROLLER-ROUTING-PLAN.md), especially sections 2, 5 and 6.
- [Evaluation](../docs/CONTROLLER-ROUTING-EVALUATION.md), especially sections 3-6.
- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `tools/route.py`, `tools/cells.py`, `tools/system_controller.py`.
- `tools/evaluation_live_worker.py`, `tools/evaluation_runner.py`,
  `tools/evaluation_live_episode.py`, `tools/dispatch_budget.py`.
- `src/routing_priors.json`, `src/cost_table.json`, `src/CONTROLLER.md`.
- `test/harness/check.py`, existing Controller/live-adapter test suites.

## Verified facts

- `graft_check_freshness` reported graph and wiring in sync on 2026-09-18.
- The full offline `test/harness/check.py --json` passed 51/51 checks with
  required child-process access. Two sandbox-only failures cleared on the
  complete rerun without code changes; no paid provider calls were made.
- Baseline HEAD `1eb0fbe`, branch `v1.0-rc1`; recheck before edits.
- Graft/source inspection: 15 cells exist, but live `cell_identity` accepts
  only Sonnet/Opus, and evaluator `expected_model` treats non-Opus as Sonnet.
- Current qualified default disables Controller. Earlier real-world campaign
  ran 104 episodes but no live Controller: it cannot establish Controller uplift.
- Quick mode records stability without gating on its classification and picks
  the first survivor before Selector. These are inspection findings needing
  focused executable characterisations, not claimed reproduced incidents.
- Historical completed-only Controller mean USD 2.623, plus USD 0.3628 worker;
  three failed runs were excluded. It is not a Fable or all-attempt cost estimate.

## Work completed

Two linked planning documents and this handoff were written; root README and
current-roadmap pointers identify them as proposed. No runtime implementation,
paid experiment, new commit or change to the shipped default occurred here.
Pre-existing Controller documentation and generated bundle edits remain intact.

## Unresolved questions

- Incorporate the operator's plan-review changes before freezing contracts.
- Exact Fable provider ID, prices, availability and served effort evidence
  must be verified at R2/R5; unknown is not permission to substitute Opus.
- Reproduce inspection gaps and determine minimal compatibility adapters.
- Paid tranches, quality weights, risk policy and statistical gates are
  proposals. Reprice after calibration; reserved evidence may be inconclusive.

## Exact next action

Read the operator's review and the two linked documents, then run Graft
freshness and record current git status/HEAD. Start R0 only: save the offline
baseline, characterise the listed Controller/identity gaps, and document the
exact assessment, decision, control and evidence-packet contracts. Current
behaviour characterisations must pass; future desired behaviour is a clearly
tracked R1/R2 gate, not a silently ignored test. Stop with R0 evidence and its
next action; do not start the paid matrix screen.

Use the bundled Python if `python` is absent:
`C:/Users/Bob/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.
Run `test/harness/check.py --json` from the repository. If Git safe-directory
is required, scope `safe.directory` to this process/command, not global config.

## Model and effort to set

Select **GPT-5.6 Sol, High** in the host's model/effort controls and open this
handoff in a fresh session after plan review. Claude worker names are product
identities, not Codex session settings. No subagent is requested.

## Cost projection

R0 development estimate: **USD 2-7 API-equivalent**, not a subscription bill;
zero Claude experiment spend. Official [Sol model information](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [pricing](https://developers.openai.com/api/docs/pricing), checked 2026-09-18:
USD 4/M ordinary input, 0.40/M cached input, 5/M separately billed cache writes,
20/M output including billed reasoning, standard short-context tier. Assume
0.10-0.25M ordinary input, 0.02-0.05M writes, 0.20-0.60M reads and 0.02-0.05M
output, mutually exclusive usage categories. This gives USD 0.98-2.49 standard
or USD 1.96-4.98 fast/priority; add 30% contingency and round. Cache hits and
actual tier are uncertain. Reprice long-context calls or excess work.

The later Claude campaign is separate: provisional USD 300-700 expected,
USD 1,800 proposed core ceiling across gated tranches. This is neither a new
paid-run approval nor a commitment to spend the ceiling.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

**2-4 hours** for R0 including repository checks and contract decisions. Full
programme estimate: 40-80 engineering/analysis hours, plus 12-30 hours of serial
live experiments and operator review. These are planning ranges, not measured
Sol runtime or a promise of completion within one context window.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
