# Handoff: controller-remediation-x3-reserved

<!-- handoff.py new --slug controller-remediation-x3-reserved --reason spawn --to-model gpt-5.6-sol --to-effort high --from-model gpt-5.6-sol --from-effort high --project . -->
Written 2026-09-27 Australia/Sydney. The generator's `spawn` reason denotes a
same-model fresh-session handoff; no agent was launched. The operator confirmed
GPT-5.6 Sol / High, but the host does not independently expose those settings.

## Goal

Finish X3's protected Controller corpus and fair comparison path, then proceed
through the staged Controller remediation only after X3 passes its exit gate.
Keep B0 as the shipping default. The user authorised autonomous work but asked
for fresh-session handoffs when needed.

## Decisions already made

- Graft MCP is required at the start of every project session. Check freshness
  first; use scoped Graft discovery before broad reads. See `AGENTS.md` and
  `docs/GRAFT.md`. Pass this requirement and this repository root to any later
  handoff. Graft's claimed token savings are not measured cost evidence.
- Keep the frozen 48-task contract: 24 development and 24 newly reserved,
  two mechanisms per family in each split. Do not turn R5's labelled fixture
  into quality evidence. See `docs/CONTROLLER-REMEDIATION-CONTRACT-X0.md` and
  `docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md`.
- Actor packages expose only public code and checks; root-owned oracles and
  scoring remain outside isolated actor access. Candidate stdout and reports
  are untrusted. Preserve the forged-output and prohibited-edit controls.
- Reserved outcomes must not tune the routing policy or prompts. Complete
  authoring controls before freezing the reserved set. X6 remains exploratory
  with no Controller promotion authority. No paid X5 calls during X3.

## Files and links that matter

- `C:\Users\Bob\Desktop\Code\Claude\Orchestrator` is the repository root;
  branch `v1.0-rc1`, HEAD `15ecf66`, with extensive pre-existing dirty work.
- `CLAUDE.md`, `docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md`,
  `docs/CONTROLLER-REMEDIATION-CONTRACT-X0.md` section 6 and
  `docs/stage-results/controller-x3-progress-2026-09-27.md`.
- `docs/CONTROLLER-X3-RESERVED-AUTHORING-2026-09-27.md` lists the 21 remaining
  distinct reserved designs, starting with C02-R2 append-log compaction.
- `tools/controller_x3_corpus.py`, `tools/controller_x3_grade.py`,
  `tools/controller_x3_language.py`, `tools/controller_x3_probe.py`,
  `tools/controller_x3_isolation_probe.py`,
  `tools/controller_public_assessment.py` and
  `test/harness/controller_x3_tests.py`.
- `test/fixtures/controller_x3/{development,reserved}/`,
  `test/oracles/controller_x3/` and
  `test/results/2026-09-27-controller-x3-inventory.json`.

## Verified facts

- `tools/controller_x3_corpus.py --out ...inventory.json` reports 27/48 ready,
  21 pending; inventory hash
  `14c03946b3f091613a653a8841b6f40f65f89b6457551e3282d506b19d4181b0`.
  All 24 development IDs are ready; three reserved IDs are ready: C01-R1,
  C01-R2 and C02-R1.
- `tools/controller_x3_probe.py --out ...development-sweep.json` passed
  144/144 controls over 24 development tasks, with 144 denied actor oracle
  reads and zero provider calls. All reference/equivalent controls were
  accepted, useful partials stayed incomplete, and false completion failed.
- The three reserved cases each passed six WSL protected controls and 14
  actor/Graft isolation checks. Receipts are
  `test/results/2026-09-27-controller-x3-sequence-probe.json`,
  `...stale-index-probe.json`, `...shadow-cutover-probe.json` and their
  matching `-isolation.json` files. All actor oracle reads were denied.
- `test/harness/controller_x3_tests.py` passed 22/22 after C02-R1 was
  registered. `tools/controller_x3_corpus.py` passed its layout inventory.
  A targeted PROSE check passed 848 authored files before the three reserved
  registrations. The full host-permission offline gate passed 81/81 at the
  24-development checkpoint and again after the three reserved registrations;
  see `test/results/2026-09-27-controller-x3-development-offline-harness.json`
  and `test/results/2026-09-27-controller-x3-reserved-checkpoint-harness.json`.
  The final targeted PROSE check passed 851 authored files, and
  `git -c safe.directory=C:/Users/Bob/Desktop/Code/Claude/Orchestrator diff --check`
  passed.
- Graft freshness reported a stale committed graph due to uncommitted code,
  while scoped Graft discovery refreshed and answered. No deep rebuild was
  claimed or needed for this local checkpoint.

## Work completed

This session added eight distinct development cases N04-D2, C01-D2, C02-D2,
C04-D2, C08-D2, C07-D2, C06-D2 and C05-D2, completing the development split.
It added three reserved cases C01-R1, C01-R2 and C02-R1 and extended the
grader, language checks and isolation probe to the reserved path. Each has
public actor code, a protected oracle, reference/equivalent/partial/label-copy/
forged-output overlays and its own causal rubric. The development sweep and
checkpoint full gate passed. The reserved authoring brief and progress record
were updated. No commit was made; preserve all pre-existing changes.

## Unresolved questions

- Twenty-one reserved packages are missing. C02-R2 append-log compaction is
  next. The authoring brief is a design, not verified fixture evidence.
- The runtime dependency inventory/seal, natural-language adversarial
  calibration, common production N3 assessment path, root-budget charging,
  paired fake campaigns and X3 exit gate remain incomplete. The assessor's
  current injected interpreter is an offline boundary test only.
- The current full offline gate passes 81/81, but no X3 exit gate exists yet
  for the incomplete 48-case corpus. Consumer `src/` did not change in this
  session; no distribution rebuild was required for these evaluation-only files.
- C05's fixture-level fetch and live-row observations do not establish total
  process memory limits or malicious monkeypatch resistance. Lexical report
  matching remains gameable. X4-X8 remain unfinished; do not promote B0 or
  start paid Controller calls from this evidence.

## Exact next action

Start with `graft_check_freshness` for the root above, then read the current
X3 progress record and C02-R2 row in the reserved authoring brief. Author
`test/fixtures/controller_x3/reserved/C02-R2/actor` and its protected
append-log compaction oracle with a tombstone/checkpoint failure, two
equivalent repairs, useful partial, label-copy and forged-output controls.
Register a task-specific rubric, run six protected WSL controls and 14
isolation checks, then refresh the corpus inventory. Continue the remaining
reserved rows without feeding their outcomes into routing-policy tuning.
After all 48 are ready, complete X3's common assessor, fake paired campaigns,
runtime seal and full exit gate before X4.

## Model and effort to set

Keep GPT-5.6 Sol with High reasoning. The operator has already set this for
the current task; a fresh host session may need its own model setting.

## Cost projection

Direct API-equivalent forecast for one Sol High implementation session:
USD 3.25-19.50 including a 30% token contingency. The low bound uses Standard
pricing; the upper uses Fast. Assumptions are 0.25-0.75M ordinary input,
0.50-1.50M cached input, 0.05-0.15M cache writes and 0.05-0.15M output
tokens, including reasoning. For the remaining X3 work, allow four to eight
such sessions, about USD 13-156 API-equivalent. These are forecasts, not
observed Codex charges; actual cache use, long context and tool charges are
unknown. No paid Claude experiment is planned for X3. Source: official
[GPT-5.6 Sol model pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [API pricing](https://developers.openai.com/api/docs/pricing), checked
2026-09-27. Reprice if usage or published rates change.

Computed: session load ~44,741 tokens (docs/COST.md, the fixed load of a stage session, 2026-09-15; chars/4, not a provider count); no claude -p calls projected for this handoff.

## Time projection

Allow 10-20 engineering hours for the remaining 21 cases, common assessment
path, fake paired campaigns, runtime seal and final offline exit gate. Host
failures or an independent rubric redesign could extend that range. There is
no live provider-run wall time in this X3 forecast.

Computed: no claude -p wall-clock component projected; session time is not derived from src/cost_table.json and belongs in prose above.
