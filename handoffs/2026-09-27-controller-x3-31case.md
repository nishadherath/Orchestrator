# Handoff: controller-x3-31case

<!-- handoff.py new --slug controller-x3-31case --reason spawn --to-model gpt-5.6-sol --to-effort high --from-model gpt-5.6-sol --from-effort high --project . -->
Written 2026-09-27 Australia/Sydney. The generator's spawn reason means a
same-model fresh-session handoff; no agent was launched. The operator
previously confirmed Sol / High, but this host cannot verify its active setting.

## Goal

Continue X3's protected 48-task Controller corpus, then its fair common
assessment and paired campaign checks. Do not start X4 or paid Controller
calls before X3's exit gate. B0 remains the shipping default.

## Decisions already made

- Start every session with Graft `graft_check_freshness`; use scoped Graft
  discovery before broad reads. This session's freshness call timed out,
  while scoped `graft_find_code` worked. Check the new session's own access.
  See `AGENTS.md` and `docs/GRAFT.md`. Do not treat Graft savings text as
  measured cost evidence.
- Freeze the 24 development and 24 newly reserved IDs, two mechanisms
  per family. Reserved outcomes must not tune routing policy or prompts.
- Actor packages contain only public code and checks; root-owned oracles
  and scoring stay outside actor access. Preserve label-copy, JSON forgery
  and safe incomplete controls. See `docs/CONTROLLER-REMEDIATION-CONTRACT-X0.md`.
- Complete X3's common assessment and fake paired campaign path before
  X4. X6 remains exploratory without automatic promotion authority.

## Files and links that matter

- Repository root: `C:\Users\Bob\Desktop\Code\Claude\Orchestrator`;
  branch `v1.0-rc1`, HEAD `15ecf66`, with extensive pre-existing dirty work.
- `CLAUDE.md`, `docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md`,
  `docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md` and
  `docs/stage-results/controller-x3-progress-2026-09-27.md`.
- `docs/CONTROLLER-X3-RESERVED-AUTHORING-2026-09-27.md` lists the
  remaining designs, starting with C04-R2 pooled tenant state.
- `tools/controller_x3_{corpus,grade,language,probe,isolation_probe}.py`,
  `test/harness/controller_x3_tests.py`, `test/fixtures/controller_x3/`,
  `test/oracles/controller_x3/` and
  `test/results/2026-09-27-controller-x3-inventory.json`.

## Verified facts

- Inventory: 31/48 ready, 17 pending; hash
  `5007a1f2d45112e332f1c030b457577ca33e6612c7aa28d5be46f55d4461ccfd`.
- C04-R1 passed six WSL root protected controls: both complete repairs
  scored 100, safe incomplete repair 75, baseline/label-copy/forgery zero.
  All actor oracle reads were denied, and provider calls were zero. See
  `test/results/2026-09-27-controller-x3-tenant-lookup-probe.json`.
- C04-R1 passed 14 actor/Graft isolation checks with oracle reads denied;
  see `test/results/2026-09-27-controller-x3-tenant-lookup-isolation.json`.
- Focused X3 tests passed 22/22; prose check passed 855 files;
  `git diff --check` passed. The 30-case and 31-case full host-permission
  offline gates each passed 81/81. The latter is
  `test/results/2026-09-27-controller-x3-31case-offline-harness.json`.

## Work completed

- Added C03-R1 lease-transfer, C03-R2 webhook-identity and C04-R1
  tenant-lookup reserved mechanisms, each with protected controls and
  actor-isolation receipts; updated the live X3 progress record and plan.
- No commit was made. Preserve all pre-existing work and local config.
  No `src/` consumer files changed in this checkpoint, so no distribution
  rebuild was needed.

## Unresolved questions

- The 17 remaining reserved mechanisms, common assessor, paired fake
  campaigns, runtime seal and X3 exit gate are unfinished. X4-X8 are
  unstarted; there is no Controller default qualification.
- The lexical report rubric is bounded but gameable. Fixture-level
  resource checks do not establish total process memory limits.
- Historical full-gate failures at 28 cases were host timing issues;
  do not erase their records or infer all future WSL checks are stable.

## Exact next action

Run `graft_check_freshness` in the new session at the root above, then
read the C04-R2 row in the reserved authoring brief. Build the pooled
tenant-session case so that complete repairs reset state at checkout
and on every return path. A safe partial may quarantine a connection
after an error and lose availability without leaking another tenant.
Register its task-specific rubric, run six protected WSL controls and
14 isolation checks, refresh inventory, then continue remaining rows.

## Model and effort to set

Set GPT-5.6 Sol with High reasoning in the new host task. Do not assume
this task's setting carries over.

## Cost projection

Direct API-equivalent forecast for the next Sol High implementation
session: USD 3.25-19.50, including 30% token contingency. The low
bound uses Standard and the high bound Fast pricing. Assumptions: 0.25-
0.75M ordinary input, 0.50-1.50M cached input, 0.05-0.15M cache writes,
and 0.05-0.15M output tokens including reasoning. This is not an observed
Codex bill; cache mix, long context and tool charges are unknown. No paid
Claude experiment is planned in this session. Across remaining X3-X8,
the rough development forecast is USD 40-400 API-equivalent, with a
separate provisional USD 200-650 Claude experiment allocation and
USD 1,376.75 proposed maximum local experiment allocation. Actual
Claude Code subscription charges may differ. Source: official
[GPT-5.6 Sol pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [Fast mode](https://developers.openai.com/api/docs/guides/fast-mode),
checked 2026-09-27; project experiment budget in the Controller action plan.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Allow 2-4 engineering hours for the next C04-R2 case and its protected
checks. Across the remaining X3-X8 plan, allow about 42-88 hours of
engineering and serial paid-campaign time plus operator or authentication
waits; host instability and the X7 adjudication may extend this.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
