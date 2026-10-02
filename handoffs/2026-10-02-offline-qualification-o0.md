# Handoff: offline-qualification-o0

<!-- handoff.py new --slug offline-qualification-o0 --reason model-change --to-model gpt-6-astra --to-effort high --project . -->
Written 2026-10-02. Current session model/effort not independently observed.
Reason: prepare the operator's next model-change checkpoint; no switch executed.

## Goal

Complete only O0 of the offline qualification implementation plan: freeze the
engineering contract, acceptance matrix, trust boundaries and module ownership
needed before implementing evaluator, admission/feedback and campaign-local
identity qualification. Controller uplift remains unestablished.

## Decisions already made

The operator accepted offline qualification as the next deliverable and asked
for manual model/effort handovers at each stage. Automatic new-chat and subagent
launches were a capability question only; none is authorised by this handoff.
O0-O6 use offline transports and make no experimental provider calls. Preserve
B0, experimental Controller status, the frozen RC and historical evidence.
V7 and the older W programme are complete; H03b remains closed with no private
score. Create a new research version and reuse existing execution/accounting.
O0 must freeze interfaces before independent implementation can overlap.

## Files and links that matter

Repository root: `C:\Users\Bob\Desktop\Code\Claude\Orchestrator`.

- [Stage plan](../docs/OFFLINE-QUALIFICATION-IMPLEMENTATION-PLAN-2026-10-02.md).
- [Analysis and historical evidence](../docs/POST-RC-QUALIFICATION-ANALYSIS-2026-10-02.md).
- [Host controls and parallel boundaries](../docs/DEVELOPMENT-SESSION-CONTROLS-2026-10-02.md).
- [Root engineering rules](../CLAUDE.md), [Graft](../docs/GRAFT.md),
  [lifecycle handoffs](../src/LIFECYCLE.md).
- [Historical pilot](../tools/controller_x5_h03_pilot.py),
  [freeze](../tools/evaluation_freeze.py), [launcher](../tools/evaluation_pilot.py),
  [registry](../src/model_registry.json), [harness](../test/harness/check.py).

Use Graft MCP in this session, starting with `graft_check_freshness`. Discover
all deferred Graft tools together. Use scoped retrieval and call graphs before
broad reads or refactoring. Check your own connection and correct root; if
unavailable, report and repair it before discovery. Carry this rule into every
later handoff. Current-source reads are required when stale summaries matter.

## Verified facts

Graft MCP was available. Initial freshness reported 81 changed indexed files
and a stale semantic snapshot. `graft_file_api tools/handoff.py` established the
ten-heading generator/checker contract. The planning task read the Q1 analysis,
root rules and Handoffs section. Host tool schemas expose the planned model and
effort combinations, chat creation and four collaboration slots including lead.
No launch, current-session model telemetry or served reasoning was verified.

Documentation verification passed: existing `check.check_prose` reported 920
authored files clean, 51 local links resolved, `tools/handoff.py check` returned
OK and scoped `git diff --check` passed. These checks do not qualify O0-O6.

Scoped Git status before this plan showed modified `CLAUDE.md` and untracked
post-RC analysis. Preserve them and the pre-existing generated RC outputs.
Historical RC PASS and source `f9f141c` come from the prior evidence record;
this planning task does not claim a fresh full runtime harness execution.

## Work completed

Created the staged plan and host-control record, with this initial handoff.
Updated the root current-work pointer and the analysis implementation pointer.
These are working-tree documentation changes, not a new commit. No O0 contract
or implementation is complete. No runtime, registry or generated distribution
change was made for this planning task.

## Unresolved questions

O0 must settle exact module reuse, schema versions, canonical money conversion,
evaluator error taxonomy, actual host isolation, identity provenance/freshness,
dependency sealing and ownership. The product population, promotion margins and
future paid campaign envelope are not prerequisites to implement the offline
mechanism, but must be fixed before relevant live claims. A valid local model
receipt does not automatically qualify WSL or served effort. Future handoffs
must refresh pricing and real token/host assumptions.

## Exact next action

Read this handoff first, run your Graft freshness check, read root instructions
and O0 in the stage plan. Inspect current branch/status without overwriting
pre-existing work. Use Graft to trace the historical admission, money helper,
evaluator boundary and candidate identity blockers. Then write the O0 contract
and executable acceptance matrix with stable IDs, named owners and concrete
negative controls. Do not launch a paid producer or a subagent. Finish O0 with
its stage-result evidence and a newly generated, validated O1 handoff, then
return for the operator's next stage selection.

## Model and effort to set

In the Codex model picker select **GPT-6 Astra**, **High**. Host identifiers:
`gpt-6-astra`, `high`. Continue with: "Read
handoffs/2026-10-02-offline-qualification-o0.md and execute O0 only."
This is a requested setting, not a claim about the active model. Do not use a
Claude `/model` command or worker class as a substitute for Codex host controls.

## Cost projection

Development API-equivalent scenario, dated 2026-10-02:
[OpenAI pricing](https://developers.openai.com/api/docs/pricing) lists Astra
Standard USD 10 input, 1 cache read, 12.5 cache write and 50 output per million
tokens. Assume 100K-300K cache-write input, 200K-1M cache-read input and 20K-80K
output including billed reasoning across the stage. Categories are disjoint;
all requests stay below the long-context threshold. Arithmetic gives USD
2.45-8.75 at Standard. Allowing up to 25% additional retry usage and 2x Fast
rates gives a planning range of approximately USD 2.45-21.88. If caching fails,
the conservative upper sensitivity case is about USD 50.63. Recalculate if
actual tokens, tier or context length differ. These are estimates, not spending
ceilings or observed Codex charges. Desktop plan billing/usage is unavailable.
External paid tools and semantic refresh are excluded and need separate costing.
Experimental Claude calls: zero planned, USD 0 experiment subtotal. The
generator's load estimate below is historical context sizing, not a measured
OpenAI token count or a price estimate for this session.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

O0: 45-90 minutes active elapsed time, excluding operator waits and substantial
design expansion. Low-confidence planning estimate; there is no paid runtime
component and no parallel work within this stage. Whole-package scheduling is
in the stage plan, not included in this stage estimate.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
