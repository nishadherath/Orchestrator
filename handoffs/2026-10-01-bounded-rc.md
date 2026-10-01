# Handoff: bounded-rc

<!-- handoff.py new --slug bounded-rc --reason model-change --to-model user-selected --to-effort user-selected --project . -->
Written 2026-10-01 by Codex after the operator selected the session settings. No further switch or delegation is requested.

## Goal

Finish the bounded, unpublished RC described in `docs/RELEASE-CANDIDATE-2026-10-01.md`. Keep B0 default, Controller experimental and Controller uplift explicitly unfinished.

## Decisions already made

Use Graft MCP in every session, starting with freshness; repository root is `C:/Users/Bob/Desktop/Code/Claude/Orchestrator`. Follow `CLAUDE.md`, `docs/GRAFT.md` and the lifecycle handoff contract. Preserve existing work. No new paid X5 screens, automatic promotion, publication or global Git configuration changes. An immutable source/bundle snapshot retains the honest dirty stamp; clean-source publication still needs a source commit and checked rebuild.

## Files and links that matter

`docs/RELEASE-CANDIDATE-2026-10-01.md`; `tools/build_dist.py`; `tools/release_check.py`; `test/harness/install_tests.py`; `test/harness/check.py`; `src/README.md`; `src/CONTROLLER.md`; `docs/stage-results/controller-x5-h03b-result-2026-10-01.md`.

## Verified facts

Graft is callable; its committed snapshot is stale (21 changed files, 1222 unindexed files, 108 stale summaries), with source spans checked directly. Four added provenance tests failed before the fix and passed afterwards. Git inspection under the sandbox needs an exact per-command safe.directory override or owner execution; no global setting was changed. The checkout contains extensive pre-existing source, research and configuration changes.

## Work completed

Recorded RC scope, corrected documentation and repaired build/release provenance. The checked build passed; the frozen 84-file bundle reproduces from 90 source inputs. Clean install, actual-baseline upgrade, rollback, consumer-drift refusal and configuration/task-journal preservation passed. Final full offline harness: 83/83 PASS. See `docs/stage-results/release-candidate-2026-10-01.md` and `test/results/2026-10-01-rc/verification.json`. No commit or publication performed.

## Unresolved questions

Controller uplift, general host isolation, served effort and frontier qualification are unfinished. H03b is closed at USD 0.184233601, with no matched S/A continuation and no private score. Its evaluator work is deferred. The unpublished RC is verified by the new complete offline result and exact artefact hashes. Clean-source publication still requires the intended source commit, a checked rebuild and explicit publication authority.

## Exact next action

Bounded RC work is complete. Read the RC result and preserve its frozen archives. If publication is requested, review and commit intended source changes, rebuild from the clean source commit and verify that newly stamped artefact. Keep Controller uplift unfinished; do not restart paid qualification experiments under the completed RC scope.

## Model and effort to set

Keep the operator-selected host model and effort. Their exact active values are not exposed here. No model-picker action is needed.

## Cost projection

Development API-equivalent cost range: unknown as of 2026-10-01 because the active model, pricing tier and billed token/cache usage are unavailable. No price is inferred from Claude benchmarks. Planning assumption: roughly 0.2-1 million input tokens and 20-100 thousand output/reasoning tokens, with unknown cache reuse; these are uncertain workload estimates, not billing. Pricing source is unavailable for the unexposed setting. Paid RC experiment cost is USD 0 because no provider experiment is planned; development cost is not zero.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Estimated focused elapsed work: 6-12 hours, conditional on review findings and local harness duration. No provider latency or user sign-in is required for this offline RC scope.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
