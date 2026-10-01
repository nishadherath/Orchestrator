# Handoff: controller-remediation-x3

<!-- handoff.py new --slug controller-remediation-x3 --reason spawn --to-model gpt-5.6-sol --to-effort high --from-model gpt-5.6-sol --from-effort high -->
Written 2026-09-27 Australia/Sydney by Codex. The generator's `spawn` reason
denotes a same-model fresh-session handoff here; no agent was launched. The
operator confirmed Sol High for this task, but the host does not independently
expose its active model or effort.

## Goal

Complete X3 of the experimental Controller remediation: replace the R5
label-based plumbing corpus with 48 independently checkable task cases and a
protected grader, then compare arms through the common production public
assessment path. The operator directed autonomous X1-X6 completion subject to
evidence gates; do not promote the Controller or run paid X5 calls during X3.

## Decisions already made

- Preserve B0 as the shipping default. X6's capped comparison remains
  exploratory without promotion authority; see
  `docs/CONTROLLER-REMEDIATION-CONTRACT-X0.md`.
- Retain the 48-row R5 corpus as a historical plumbing fixture. Its labelled
  mechanisms and self-reported evidence are unsuitable for quality claims.
- X3 needs 24 development plus 24 newly reserved cases over the frozen 12
  families, two per family per split, with different mechanisms. Cases reused
  from N/Q work are development-only. Preserve old manifests and receipts.
- The protected parent owns scoring and serialization; never import actor code
  into that parent. Actor stdout, reports and exit codes are untrusted. Tests
  must include N7's monkeypatch/forged-output and oracle-leak attacks.
- No model switch is needed for X3: stay on user-confirmed GPT-5.6 Sol / High.
  No subagent is scheduled. No paid provider call is required for X3.

## Files and links that matter

- `AGENTS.md`, `CLAUDE.md`, `docs/GRAFT.md`, and
  `docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md`.
- `docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md` X3 exit;
  `docs/CONTROLLER-REMEDIATION-CONTRACT-X0.md` sections 2, 6, 7, 9.
- `docs/stage-results/controller-x2-2026-09-27.md`,
  `test/results/2026-09-27-controller-x2-build.log`.
- `src/controller_evaluation_contract.json`, `tools/controller_corpus.py`,
  `tools/controller_evaluation.py`, `tools/controller_pilot_runtime.py`,
  `tools/worker_selector.py`, `tools/controller_policy.py`.
- N4/WSL reuse candidates: `tools/worker_corpus.py`,
  `tools/worker_wsl_q3_grade.py`, `tools/worker_wsl_transport.py`,
  `tools/realworld_isolation.py`, `test/fixtures/worker_n4/`.
- `test/harness/check.py`, `tools/build_dist.py`, `tools/release_check.py`.

## Verified facts

- X2's `python -B tools/build_dist.py` completed with exit 0, running the
  full offline harness before writing the bundle. Targeted `DIST` passed:
  78/78 generated files match. `tools/release_check.py --json` passed source
  equivalence and sensitive-material exclusions. `release_ready: false` is
  due to the dirty stamp and separate operator publication action.
- Focused X2 8/8, X1 12/12, R4 28/28, R5 33/33, registry 8/8,
  Controller self-test 12 scenarios and N1 executor 39/39 passed. Q4 historical
  continuation test passes 4/4 after a test-only frozen-source replay fix.
- Graft scoped MCP queries worked and refreshed changed source. A later
  freshness check timed out after 60 seconds, but scoped retrieval still
  worked. A complete deep rebuild remains unverified; do not claim a measured
  Graft cost saving.
- The R5 `controller_corpus.grade_task` awards milestone/evidence credit from
  names in submitted JSON; actor materialization only checks result shape.
  This is source-observed, not evidence of real task quality.
- Official OpenAI pricing checked 2026-09-27: GPT-5.6 Sol Standard short-
  context rates are USD 4 ordinary input, 0.40 cached input, 5 cache writes
  and 20 output per million tokens; Fast mode doubles these rates.
- `test/harness/controller_x3_tests.py` passed 22/22, plus public assessment
  3/3. The provider-free WSL vertical probes passed six controls each for
  C03-D1, C03-D2, C01-D1, C02-D1, C04-D1, N02-D1, N03-D1, C06-D1,
  C07-D1, C08-D1, C05-D1, N01-D1, N04-D1, N02-D2, N03-D2 and N01-D2:
  all reference/alternative solutions score 100 and pass. Useful partials
  remain unaccepted, scoring 61-92 for implementation cases and 72.5 for
  the three clarification cases. N03-D1 requires an operator retention decision
  with no policy edit; N03-D2 needs an approved target region with routing
  unchanged; C08-D1 leaves lock-order code unchanged.
  Consequential implementation baseline/label-copy/JSON-poison controls score
  zero and fail. Ordinary N01-D1/N02-D1 baselines and label copies score
  16/rejected. N01-D2's baseline scores 16 and label copy 28.5/rejected;
  N02-D2's baseline scores 10 and label copy 22.5/rejected;
  N04's baseline scores 16 and label copy 28.5/rejected because one unchanged
  worker-pin probe is real evidence. Their JSON poisons score zero.
  N03/C08 unsupported completion scores 40/rejected and concealed edits zero.
  Actor reads of all protected oracles were denied.
  Read `test/results/2026-09-27-controller-x3-wsl-vertical-probe.json` and
  `test/results/2026-09-27-controller-x3-outbox-probe.json` and
  `test/results/2026-09-27-controller-x3-order-alias-probe.json` and
  `test/results/2026-09-27-controller-x3-migration-probe.json` and
  `test/results/2026-09-27-controller-x3-cache-probe.json` and
  `test/results/2026-09-27-controller-x3-slice-probe.json` and
  `test/results/2026-09-27-controller-x3-retention-probe.json` and
  `test/results/2026-09-27-controller-x3-clock-probe.json` and
  `test/results/2026-09-27-controller-x3-money-probe.json` and
  `test/results/2026-09-27-controller-x3-lock-order-probe.json` and
  `test/results/2026-09-27-controller-x3-stream-join-probe.json`,
  `test/results/2026-09-27-controller-x3-symbol-rename-probe.json` and
  `test/results/2026-09-27-controller-x3-manifest-probe.json`,
  `test/results/2026-09-27-controller-x3-null-profile-probe.json` and
  `test/results/2026-09-27-controller-x3-region-probe.json` and
  `test/results/2026-09-27-controller-x3-config-key-probe.json`.
- The first JSON-poison overlays patched too late to forge application output.
  Their original scores did not demonstrate a successful forgery. After fixing
  import-time patching, the 16-task selective WSL attack run passed 16/16:
  all public checks passed, protected grades stayed zero/rejected and oracle
  reads were denied. See
  `test/results/2026-09-27-controller-x3-forged-output-controls.json`.
- The first scorer required exact hidden diagnosis and next-step slugs, unfair
  to genuine actors using ordinary language. `tools/controller_x3_language.py`
  now allows bounded task-specific prose equivalents, and `_report` retains
  bounded actor-chosen probes. Diagnosis still needs verified causal probes.
  Focused tests accept natural-language descriptions for all sixteen cases,
  exercise two full scorer paths, and reject vague claims. A confident
  completion cannot gain partial next-step credit. An unrelated actor-chosen
  probe may earn evidence but cannot replace the causal diagnosis;
  calibrate all tasks before X3 exit because lexical checks remain gameable.
- The first full WSL rerun exposed partial next-step credit on a confident
  label-copy claim; that gate is fixed. The post-fix sweep passed 96/96
  controls across 16 tasks, accepted 32 reference/equivalent solutions, denied
  all actor oracle reads and made zero provider calls. See
  `test/results/2026-09-27-controller-x3-fair-prose-regression.json`.
- Four actor issue files needed British spelling under the repository's PROSE
  check. Their 24-control WSL refresh passed, the inventory remained 16/48,
  and the final host-permission full offline harness passed 81/81 checks.
  See `test/results/2026-09-27-controller-x3-prose-fix-probe.json` and
  `test/results/2026-09-27-controller-x3-offline-harness.json`.
- `tools/controller_x3_corpus.py` inventories 48 frozen IDs: sixteen ready and
  32 pending. All 12 families now have a development example, but neither split
  is complete. Read `test/results/2026-09-27-controller-x3-inventory.json`.
- The X3 actor isolation probe passed 14/14 separately for all sixteen cases
  on WSL, including direct and
  shell read denial, inherited-instruction absence, actor-scoped Graft
  search/map/escape checks and protected-file write denial. Staging rejects
  an extra public-check edit. Read
  `test/results/2026-09-27-controller-x3-isolation-v3.json` and
  `test/results/2026-09-27-controller-x3-outbox-isolation.json` and
  `test/results/2026-09-27-controller-x3-order-alias-isolation.json` and
  `test/results/2026-09-27-controller-x3-migration-isolation.json` and
  `test/results/2026-09-27-controller-x3-cache-isolation.json` and
  `test/results/2026-09-27-controller-x3-slice-isolation.json` and
  `test/results/2026-09-27-controller-x3-retention-isolation.json` and
  `test/results/2026-09-27-controller-x3-clock-isolation.json` and
  `test/results/2026-09-27-controller-x3-money-isolation.json` and
  `test/results/2026-09-27-controller-x3-lock-order-isolation.json` and
  `test/results/2026-09-27-controller-x3-stream-join-isolation.json`,
  `test/results/2026-09-27-controller-x3-symbol-rename-isolation.json` and
  `test/results/2026-09-27-controller-x3-manifest-isolation.json`,
  `test/results/2026-09-27-controller-x3-null-profile-isolation.json` and
  `test/results/2026-09-27-controller-x3-region-isolation.json` and
  `test/results/2026-09-27-controller-x3-config-key-isolation.json`.
- `test/harness/controller_public_assessment_tests.py` passed 3/3. The new
  bounded public collector calls the actual N3 and rigour validators using
  one cited interpretation. This is offline boundary evidence, not live
  interpretation quality or root-budget settlement.

## Work completed

X1 and X2 implementation and stage records are present but uncommitted on
`v1.0-rc1`, HEAD `15ecf66`, alongside extensive earlier user work. Preserve
the dirty worktree. X2 added named standard/frontier Generator assignments,
one task-revision-wide Controller claim and N1 budget ownership, then rebuilt
`dist/` through the checked builder. The historical Q4 manifest and paid
receipts were not changed. X3 now has payment-retry, outbox-lease, order-ID
normalization, online-migration, tenant-cache, local-slice,
missing-operator-fact, clock-skew incident, cross-consumer money and
contradictory-lock-order, streaming-window-join, symbol-rename, release-pin,
nullable-profile, target-region and configuration-key
tasks under
`test/fixtures/controller_x3/development/` for
`C03-D1`, `C03-D2`, `C01-D1`, `C02-D1`, `C04-D1`, `N02-D1`, `N03-D1` and
`C06-D1`, `C07-D1`, `C08-D1`, `C05-D1`, `N01-D1`, `N04-D1`, `N02-D2` and
`N03-D2` and `N01-D2`, with
separate protected oracles,
`tools/controller_x3_grade.py`, corpus inventory and host probe. C03-D2 adds
a separate outbox lease/fencing task with task-specific causal probes. The
scorer uses Q1/Q2 WSL isolation and never imports actor code into the parent. See
`docs/stage-results/controller-x3-progress-2026-09-27.md` for its limits.
`tools/controller_public_assessment.py` adds the shared cited public packet
and interpreter validation path; the X3-specific actor/Graft isolation probe
is also present.

## Unresolved questions

- Thirty-two genuine X3 cases and the common public assessment bridge remain
  unbuilt. The sixteen-case grader is explicitly registered per task, not yet a
  complete corpus scorer. Existing R5 source
  must not be relabelled as valid.
- Runtime inventory is not yet sealed, and oracle isolation through inherited
  instructions, search and Graft is proven for sixteen case-specific host probes,
  not for all future cases or the eventual paid actor configuration.
- X4 still needs a real interpretation provider, versioned prompt/schema,
  requested/served identity and cost telemetry, and root-budget charging.
  An offline injected interpreter cannot be used as comparison-arm evidence.
- N4 fixtures offer some development mechanisms but their previously used
  reserved cases cannot become unseen X3 reserved cases. Review licence and
  source provenance before importing GitHub material; synthetic cases are
  acceptable if their failure mechanisms and checks are genuinely distinct.
- The frontier role profile has only fake dispatch evidence. Served Fable
  identity, effort and quality are unproved. X4 production workflow remains
  closed; X5 paid pilot has not begun.
- C05-D1's live-row wrapper cap does not prove total process memory use or
  malicious monkeypatch resistance. Do not overclaim that observation.
- Natural-language rubric adversarial calibration remains pending. The
  96-control WSL regression passed, but does not validate arbitrary prose.
- Current API charge for development is not visible; unknown is not zero.
  X3's offline test adapters imply USD 0 in planned Claude experiment calls.

## Exact next action

Start with `graft_check_freshness` for
`C:\Users\Bob\Desktop\Code\Claude\Orchestrator`, then use scoped
`graft_find_code`, `graft_file_api`, `graft_trace_calls` and `graft_find_all`;
if freshness times out, report it and continue only with working scoped Graft
access. Read the X3 progress record, sixteen WSL probes and inventory. Continue
extending the explicitly registered per-task grader while preserving its
independent observations and actor/root separation. Expand the actor/Graft
isolation probe to each new case. Extend to 48 distinct cases,
24/24 split, and wire the actual N3 public assessor into tiny paired fake
campaigns. Run focused checks, the full offline gate and checked dist build
if consumer `src/` changes. Record X3 honestly before X4.

## Model and effort to set

Keep gpt-5.6-sol, effort high; the operator has already set it.

## Cost projection

Direct API-equivalent projection for the next Sol High implementation session:
USD 3.25-19.50, inclusive of the staged protocol's 30% token contingency.
The high end spans Fast pricing; the low end uses Standard. The mutually
exclusive assumptions are 0.25-0.75M ordinary input, 0.50-1.50M cached
input, 0.05-0.15M cache writes and 0.05-0.15M output (including reasoning).
For the remaining X3 work, allow six to twelve such session units, roughly USD
19.50-234.00 API-equivalent; reprice if actual usage exceeds them. The range
reflects 32 independent cases plus campaign plumbing and the exit gate. Prices are
from the official [GPT-5.6 Sol model](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [API pricing](https://developers.openai.com/api/docs/pricing), checked
2026-09-27. Long-context requests, separately charged tools and any changed
prices are excluded. This is a forecast, not the observed Codex charge or a
Claude subscription charge. No paid Claude experiment is planned for X3.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Engineering elapsed time for the remaining X3 work is 15-30 hours over likely
multiple sessions, excluding any operator wait and unexpected host repair.
This assumes the current authoring pace for 32 more cases, plus paired fake
campaigns and the offline exit gate. No live experiment wall time is planned.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
