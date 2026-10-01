# Handoff: controller-x5-graft-restart

<!-- handoff.py new --slug controller-x5-graft-restart --reason model-change --from-model gpt-5.6-sol --from-effort high --to-model gpt-5.6-sol --to-effort high -->
Written 2026-09-28 for a fresh session, with the same GPT-5.6 Sol / High setting. The generator's `model-change` flag only supplies its ten-heading template; no model or effort change is requested.

## Goal

Continue the full worker and Controller remediation programme through its evidence gates. Restore Graft MCP retrieval, finish the independent X5 candidate review and, only if the pending design decision permits it, freeze and run a new prospective development screen; X6-X8 remain pending.

## Decisions already made

- Preserve X5 v1-v3 as failed/stopped development evidence. Do not replay their single-use roots, relax the frozen v3 gate, count unreported v2 cost as zero, or alter the router to make the clear C03-D2 task invoke Controller.
- The B0 consumer default stays unchanged. The Q4R boundary is the qualified three-cell development host; the historical Q3 two-cell launcher stays unchanged.
- The operator has standing approval for paid project calls but explicitly wants decisions other than paid calls brought to them. A question is pending: redesign the X5 screen using an independent case audit (recommended) or stop the Controller programme. No new paid screen should run before its design is settled.

## Files and links that matter

- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md`, `docs/stage-results/controller-x5-screen-v3-stop-2026-09-28.md`, `docs/stage-results/controller-x5-public-candidate-audit-2026-09-28.md`.
- `docs/stage-results/controller-x5-redesign-brief-2026-09-28.md`, `test/results/2026-09-28-controller-x5-candidate-baseline-probe.json`.
- `docs/stage-results/controller-x5-v2-prelaunch-proof-2026-09-28.md`, `test/results/2026-09-28-controller-x5-v2-prelaunch-audit.json`.
- `test/results/2026-09-28-controller-x5-screen-manifest-v3.json`, `test/results/2026-09-28-controller-x5-v3-canary-receipt.json`, `test/results/2026-09-28-controller-x5-v3-screen-results.jsonl`.
- `tools/controller_x5_screen.py`, `tools/controller_x5_worker_adapter.py`, `tools/controller_x5_host_canary.py`; exact v1-v3 snapshots are under `test/results/`.

## Verified facts

- V3 Sonnet High canary served `claude-sonnet-5`, completed Q1 collection and passed its public check at USD 0.2724994 API-equivalent. C03-D1 auto-selected Controller for USD 0.043493601; C03-D2 selected worker for USD 0.0506614. V3 settled subtotal USD 0.366654401. X5 v1 adds USD 0.0330442 settled. A read-only v2 prelaunch audit inferred zero provider invocations from the frozen guard and signed records, while its independent USD 1 local hold remains uncertain and no provider cost receipt exists. Four v3 assessments and all pilot worker/Controller episodes remained unused.
- Q4R structured/boundary regression scripts passed 8 tests; the repository prose check passed 817 files; Windows Git `diff --check` passed. The earlier X4 checked `build_dist.py` passed before the X5 development-only scripts were added; no consumer source was changed after that build.
- Graft MCP freshness and scoped code queries each timed out at this session's 60-second limit. The current `.codex/config.toml` requests 180 seconds but a live session may need restart. `graft check` before repair reported 20 changed source files and 667 unindexed fixture files. A provider-free `graft build` completed with 19,148 wiring nodes, 38,035 edges and 1,880 cards; the MCP still timed out after this rebuild. Do not claim semantic freshness from the structural build.

## Work completed

- Preserved v1-v3 manifests and stopped evidence; documented the v2 prelaunch guard mismatch, v3 Q4R remediation, prospective gate failure, provider-free candidate audit and four-case redesign brief. Reproduced C01/C06/C07 baseline outputs and bound their public source hashes in a probe JSON. Updated `CLAUDE.md` and the remediation plan. No commit was made; branch `v1.0-rc1` has extensive pre-existing uncommitted work.

## Unresolved questions

- The operator's pending choice between a new independently audited X5 development screen and stopping the Controller programme.
- Graft MCP availability in a fresh session, and whether its 180-second configured timeout takes effect. Structural index was rebuilt; semantic summaries may remain stale.
- The v2 no-launch audit supports zero provider invocations, but its USD 1 local hold remains uncertain. The generic budget API has no signed prelaunch-zero release path; do not replay the actor or silently finalise its ledger.
- C04-D1, C06-D1 and potential C01/C07 overlays are not qualified Controller-suitable cases. A Graft CLI source audit found that C01/C03/C04/C06/C07 actor comments announce their faults. Provider-free baseline probes for C01/C06/C07 passed, but a trace added to these simple actors would not create a genuinely unresolved premise. A new X5-only actor or open-source case with competing causes and independent acceptance needs design if the programme continues.
- Claude Code subscription auth and the installed Q4R launcher/schema must be freshly checked before any new paid call. X6-X8 have not started.

## Exact next action

In a new task opened on this same repository with GPT-5.6 Sol / High, call `graft_check_freshness` first. If it works, use scoped Graft retrieval to design a non-leaking, genuinely multi-hypothesis X5-only task and an independent acceptance check; consult the candidate audit and baseline-probe JSON first. If it still times out, diagnose the MCP connection rather than scanning indexed source. Respect the pending programme decision before freezing or spending on a new screen.

## Model and effort to set

Set GPT-5.6 Sol with High reasoning in the new task's host controls. This is the same requested setting; the host cannot verify it from inside the task.

## Cost projection

Development-session direct OpenAI API-equivalent estimate: **USD 1.24-4.60**, not an invoice. Assumptions: 150k-500k uncached input tokens at USD 4/M, 100k-500k cached input at USD 0.40/M, and 30k-120k output tokens including reasoning at USD 20/M, Standard short-context rates, no per-request >272k long-context uplift. Formula: USD 0.60-2.00 + 0.04-0.20 + 0.60-2.40. Source: [official GPT-5.6 Sol model pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol), checked 2026-09-28. Unknown actual cache mix, hidden output and host billing make this a wide estimate. Separate Claude Code experiment spend for provider-free audit is USD 0; a later separately frozen six-assessment screen has a USD 3 local ceiling and expected USD 0.15-0.60 API-equivalent usage. No Claude `-p` call is included in this handoff itself.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Allow **3-7 hours** for fresh-session Graft recovery, source audit, provider-free trace reproduction and a reviewable prospective design. This excludes any later paid pilot and X6-X8. A six-assessment screen, if selected and frozen later, adds roughly 1-2 hours; the 18-episode pilot is separately estimated at 2-8 hours.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
