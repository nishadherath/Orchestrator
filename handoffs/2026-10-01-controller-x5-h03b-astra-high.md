# Handoff: controller-x5-h03b-astra-high

<!-- handoff.py new --slug controller-x5-h03b-astra-high --reason model-change --to-model gpt-6-astra --to-effort high --project . -->
Written 2026-10-01 by Codex; updated after the approved H03b pilot. The host emitted a model-switch event, but the exact active model and effort are not independently exposed to this session.

## Goal

Continue the X5 Controller uplift from the stopped H03b result. B0 failed public acceptance, so no matched Controller comparison ran. Close the next evaluator's exception-reporting gap and freeze both public-failure and residual-risk entry branches before any new producer.

## Decisions already made

- Use Graft MCP first on every repository task, starting with `graft_check_freshness`; read `docs/GRAFT.md`, `CLAUDE.md`, and `src/LIFECYCLE.md` as required. Treat Graft output as evidence, not authority.
- H03b was explicitly approved within USD 16 and stopped after one settled producer. Do not replay it, reuse its ready root for another call, change its frozen oracle or assign a retrospective score.
- H03b is an authored retrospective development case. No private unresolved task was supplied. Keep observations, inferences, and untested risks distinct.
- GPT-6 Astra / High remains the recommendation. A host model-switch event occurred; the exact setting has not been independently verified.

## Files and links that matter

- `test/results/2026-10-01-controller-x5-h03b-pilot-manifest.json`
- `test/results/2026-10-01-controller-x5-h03b-pilot-cost-notice.json`
- `docs/stage-results/controller-x5-h03b-pilot-preflight-2026-10-01.md`
- `docs/stage-results/controller-x5-h03b-result-2026-10-01.md`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/B0-analysis.json`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/B0.patch`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/B0-public-diagnosis.json`
- `docs/stage-results/controller-x5-h03-pilot-preflight-2026-10-01.md` (retired H03 context)
- `tools/controller_x5_h03_pilot.py`
- `CLAUDE.md`; `docs/GRAFT.md`; `src/LIFECYCLE.md`; `tools/handoff.py`

## Verified facts

- `graft_check_freshness` reported STALE because this checkout has extensive pre-existing uncommitted work; continue using the index with source verification where needed.
- H03b manifest SHA-256: `218e0f70b4f2e80a313b07c90cd0275ce65416b4a1ce12a8c82ab8724b5c02f8`. Its approved notice binds that digest.
- Root `0475ead5cd55ed149d3747cf` made one terminal, identity-valid `claude-sonnet-5` attempt, requested low effort, served effort unknown. Ledger spend is USD 0.184233601, with no unresolved charge or breach. Worker wall time was 41.999747 seconds. All 51 protected actor files are unchanged.
- Public acceptance failed. The unchanged public-check diagnostic captured an invalid committed frame, then a corrected frame, two Framer calls and two Verifier calls before script exhaustion. The worker truthfully reported partial work and an unrun check.
- The frozen private grader raised the same Verifier-script exception; quality and critical-error fields are unavailable. There were no public-risk, S or A calls and no measured Controller uplift.
- The final full offline harness passed 82 checks, including DIST, RELEASE and HANDOFF, and failed only PROSE on a US spelling in this handoff. That spelling was corrected; the focused post-correction result is `test/results/2026-10-01-controller-x5-h03b-doc-checks.json`. No runtime code changed after the full run.
- Claude.ai login completed successfully on 2026-10-01. The guarded installed `worker_wsl_auth.py sync` command then succeeded as WSL root, promoting the fresh login into the protected runtime store without exposing credentials. Login session `19746` is closed; do not reuse its callback code.

## Work completed

Claude.ai login and guarded runtime credential synchronisation succeeded. The approved H03b producer settled, its stop rule was enforced, and the immutable patch, receipt, public verification and provider-free diagnostic were saved. The result report documents the failed repair and unscored private evaluation. No commit was made; preserve all pre-existing work.

## Unresolved questions

- The H03b result is closed and its paid cost settled. Controller uplift is still unestablished; the next candidate must clear the provider-free repairs below before paid admission.
- The next evaluator needs bounded per-scenario failure results and a separate infrastructure-error status. Preserve the frozen H03b score as unavailable.
- A provider-free counterfactual reproduced a separate `accepted_producer` exact-float equality bug: the authentic raw receipt cost differs from the rounded ledger by less than one nanodollar. A counterfactual accepted/pass state is rejected until cost is normalised. This did not cause the actual public failure. Use canonical ledger units in a newly frozen successor gate; evidence is `test/results/2026-10-01-controller-x5-h03b-pilot-run/cost-equality-diagnosis.json`.
- The frozen Q4U launcher requires `Read,Edit,Write,Glob,Grep` and Graft retrieval, with no worker execution tool (`tools/worker_wsl_namespace_q4u.sh:112`). Use host verification feedback between matched worker attempts and make that workflow explicit. Future public-failure and residual-risk entry branches must be frozen before producer outcomes, with identical evidence and acceptance in S/A.

## Exact next action

Read the completed H03b result and the focused doc-check record. Continue provider-free evaluator and protocol design under the standing autonomous-work direction; a new paid experiment requires a fresh frozen manifest and cost notice. Do not dispatch H03b S/A. Runtime operations use WSL root; after any future reauthentication, use the installed credential helper's guarded `sync` before `inspect`.

## Model and effort to set

Select `gpt-6-astra`, effort `high`, in this host's model picker if the operator chooses to switch. This handoff does not itself change the active model. Do not assume a Claude `/model` command controls this Codex host.

## Cost projection

Development session estimate for GPT-6 Astra / High: about USD 4–25 in direct API-equivalent charges, **not** a claim about Codex subscription billing or measured usage. Based on OpenAI's published GPT-6 Astra API prices consulted 2026-10-01 ([model page](https://developers.openai.com/api/docs/models/gpt-6-astra)): USD 10 per million uncached input tokens, USD 1 per million cached reads, USD 12.50 per million cache writes, and USD 50 per million output tokens. Assumes roughly 0.2–0.8 million uncached input, 0.2–0.7 million cached reads, 0.02–0.1 million cache writes, and 0.03–0.12 million billed output tokens across the remaining pilot analysis; actual reasoning output, cache behaviour, tool usage, and requests above the context pricing threshold may move the result outside this range. Unknown cost is not zero.

The H03b **paid experiment** is separate: USD 0.184233601 settled under its USD 16 ceiling. S/A were ineligible and unrun. These Claude benchmark amounts are not used to price the Codex development session. No further paid call is projected by this handoff.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Estimated active elapsed time for authentication follow-through, guarded pilot, and evidence review: 1–4 hours, subject to user sign-in and approval timing and provider latency; this is an estimate, not a measured duration.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
