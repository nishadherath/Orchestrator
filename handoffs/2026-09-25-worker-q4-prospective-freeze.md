# Handoff: worker-q4-prospective-freeze

<!-- handoff.py new --slug worker-q4-prospective-freeze --reason model-change --from-model gpt-5.6-sol --from-effort high --to-model gpt-6-astra --to-effort high --project . -->
Written 2026-09-25 by gpt-5.6-sol, high. Reason: model-change.

The outgoing Sol High setting was confirmed by the operator in this session;
the host does not independently expose its active model or reasoning level.

## Goal

Complete Q3's cost-sensitive, prospective public candidate-cell decision, then
design and freeze Q4's distinct reserved task frame and routing policy. The
operator has approved work through Q4. **Stop before Q5 paid reserved dispatch.**

## Decisions already made

- B0 remains the shipping default. N5's tiny 15-cell screen and synthetic
  development comparison are historical exploratory evidence, not promotion.
- Eight independent Q3 public B0 tasks are complete. P01-P08 cannot be
  reserved task units. Q0's difficulty ceiling/floor does not trigger.
- Preserve frozen grades. P07 has a disputed exception-type rubric detail;
  report frozen and contract-based sensitivity separately, without editing the
  oracle or replaying the run.
- The Q3 expansion live runner is one-shot. Never rerun its `--run` mode.
- Use Claude Code's WSL Claude.ai subscription authentication for any new
  experiment, never a Claude API key. A new paid screen needs its own dated
  notice, exact manifest, fake-provider checks, identity proof and no-replay
  accounting. The operator's standing approval covers bounded Q3/Q4 work, but
  the project rule still asks first if a projected campaign exceeds USD 100.
- Graft MCP is required on every session. Start with `graft_check_freshness`
  and use scoped retrieval first. A standing-approved deep refresh brought the
  structural graph into sync, but the semantic tier remains partial. Do not
  equate structural freshness with completed summaries.

## Files and links that matter

- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, `src/LIFECYCLE.md`.
- `docs/WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md` and
  `docs/WORKER-QUALIFICATION-PROTOCOL-Q2-2026-09-25.md`.
- `docs/stage-results/worker-q3-public-2026-09-25.md`,
  `docs/stage-results/worker-q3-canary-2026-09-25.md`,
  `docs/stage-results/worker-n5-screen-2026-09-25.md`,
  `docs/stage-results/worker-n5.md`.
- `test/results/2026-09-25-worker-q3-expansion-manifest.json`,
  `test/results/2026-09-25-worker-q3-expansion-evidence.json`,
  `test/results/2026-09-25-worker-q3-expansion-adjudication.json`,
  `test/results/2026-09-25-worker-q3-expansion-patches/`.
- `tools/worker_q3_expansion.py`, `tools/worker_q3_expansion_live.py`,
  `tools/worker_wsl_q3_adapter.py`, `tools/task_executor.py`,
  `tools/worker_selector.py`, `src/model_registry.json`.
- Ignore-root upstream clones are under `pilot-runs/q3-sources/` and
  `pilot-runs/q3-parents/`. Do not include their private tokens or WSL auth.

## Verified facts

- Q3 eight-family B0 hidden acceptance 3/8, mean quality 87.5/100, five
  public-pass/hidden-fail episodes, nine Sonnet-low provider calls, USD
  2.215058204 provider-reported API-equivalent. The six-task expansion alone
  was six settled calls, USD 1.774540602; served effort was unreported.
- The P07 hidden oracle expects `TypeError` for malformed marker and
  requirement states; its actor patch raises `InvalidMarker` and
  `InvalidRequirement`, both `ValueError` subclasses. Its public issue only
  says to validate malformed state. Frozen grade is 90/100 and not accepted;
  contract-equivalent sensitivity would make public acceptance 4/8, still
  within Q0's two-to-six window.
- P01 timer-sensitive baseline and candidate were each regraded ten times
  provider-free and stable. Harder P03-P08 run variability remains unknown.
- `git -c safe.directory=* diff --check` passed; the four focused
  `worker_q3_expansion_tests.py` tests passed. `python3
  tools/worker_q3_expansion.py --check` passed with the original manifest
  digest. `python3 test/harness/check.py` passed **68/68** offline checks at
  HEAD `15ecf66` with the dirty worktree. Focused prose validation passed on
  666 authored files.
- No Q4 reserved task has been built or run. Subscription invoice impact is
  unknown; the API-equivalent totals are not invoice charges.
- `powershell -NoProfile -ExecutionPolicy Bypass -File
  tools/graft_deep_refresh.ps1` completed structural indexing but its first
  deep pass exited 1: 8,520 nodes, 18,064 edges, 817 cards and six semantic
  file failures. After raising the DeepSeek Flash `record_symbols` output cap
  only in the local proxy, a cached retry resolved five files and left only
  `tools/task_executor.py` unparseable. It ended at 8,511/8,520 covered
  meanings, eight stale summaries and one pending file. Graft MCP reports the
  structural graph in sync. The retry reported 12 calls, 146,478 input
  tokens (144,382 cached) and 85,667 output tokens, no missing usage. At
  published DeepSeek Flash rates this is about USD 0.05215 off-peak or USD
  0.10430 peak API-equivalent; the first pass's usage and charge are unknown.
- After the local Graft helper and documentation changes, PowerShell parsing,
  `git diff --check`, handoff validation and the full offline harness passed.
  The harness reported **68/68** checks at HEAD `15ecf66`.

## Work completed

Q3 P03-P08 actors, oracles, calibrated variants, manifests, paid receipts and
independent stopped-patch adjudication were produced in the existing dirty
worktree. This session added `docs/stage-results/worker-q3-public-2026-09-25.md`
and updated `docs/FINDINGS.md` and
`docs/WORKER-Q3-EXPANSION-INVENTORY-2026-09-25.md`. No commit was made. Branch
`v1.0-rc1`, HEAD `15ecf66`; preserve all pre-existing changes.

## Unresolved questions

- Whether a small public candidate screen has sufficient information value
  after N5's weak/ceiling synthetic comparison. Consider Sonnet xhigh or high
  against Opus high/low on a few harder Q3 tasks at equal cap. Do not assume
  higher effort is monotone. Fable's identity was seen in N5 but the Q3 WSL
  adapter only currently admits Sonnet-low/Opus-high; any new identity must be
  proven under the revised adapter and current host.
- What Q4 reserved sample size, repeat count and target stratum are feasible
  under independent-project, licence, source-size, offline-oracle and power
  constraints. Q0 suggests 24 tasks, but this is not yet a frozen schedule.
- How to resolve P07 rubric ambiguity before using that mechanism in a
  future task frame; whether P08's broad patch has regressions outside its
  frozen hidden cases. These are not reasons to revise old scores.
- Repairing the one remaining Graft semantic file failure cost-sensitively.
  The installed Graft crux pass sends up to 18,000 source characters and all
  target IDs for a file in one request. `tools/task_executor.py` has many
  definitions beyond that source clip, and DeepSeek returns unparseable tool
  arguments for it even with the raised output cap. Diagnose request shaping
  or parse recovery offline before another paid retry; do not invent symbol
  summaries. Graft structural retrieval remains available and current.

## Exact next action

After switching to GPT-6 Astra High, run `graft_check_freshness` in this repo,
read the Q3 result and Q0/Q2 contracts above, then write the prospective,
cost-capped Q3 candidate-screen decision before any new paid call. If the
screen's value of information is low, record a no-screen decision with an
explicit candidate/abstention rationale and proceed to Q4. If useful, first
build fake-provider/identity checks, a dated notice and exact one-shot
manifest, then execute under standing approval. Carry the result into the Q4
reserved-frame and policy freeze. Stop before Q5.

## Model and effort to set

`/model` gpt-6-astra, effort high.

## Cost projection

Direct OpenAI API-equivalent projection for the **Astra High architecture and
evaluation-design session**: **USD 4-30**, about 0.15-0.40 million ordinary
input, 0.20-0.90 million cached input, 0.03-0.10 million cache writes and
0.03-0.10 million output/reasoning tokens, counted in mutually exclusive
categories. These imply roughly USD 3.58-11.15 at Standard short-context
rates; the outward range allows roughly 30% contingency and Fast up to 2x.
This is not measured session billing. Long-context, tools, changed cache
behaviour or provider pricing can exceed the estimate. Source checked
2026-09-25: [official Astra model pricing](https://developers.openai.com/api/docs/models/gpt-6-astra),
USD 10/1M ordinary input, 1/1M cached input, 12.50/1M cache writes and
50/1M output. The host's actual selected model, service tier and token
accounting are not exposed here.

Any **Claude Code paid Q3 screen** needs a separate prospective notice and
local allocation; no amount is assumed spent or authorised by this estimate.
The past Q3 B0 API-equivalent subtotal is USD 2.215058204, already spent.
The first Graft DeepSeek refresh has an unknown charge. Its cached retry
reported about USD 0.05215 at the published off-peak API rates, separate from
the OpenAI estimate. Neither figure is a verified provider invoice.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Estimated **2-6 hours** for the bounded Q3 candidate decision and Q4 design
freeze, excluding any paid screen execution, fixture curation and operator
delay. A screen or 24-task independent corpus build could add several hours;
re-estimate and hand off its implementation rather than treating the design
estimate as a total campaign forecast.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
