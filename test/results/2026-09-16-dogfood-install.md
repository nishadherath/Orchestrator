# Dogfood install log 2026-09-16

Per `CLAUDE.md`'s Dogfooding protocol: install from `dist/`, never from
`src/`, into a consumer project. Project: `orchestrator-scratch`. Bundle
version `2026-09-16-b55d618` (source commit `b55d618`, clean tree),
replacing `2026-09-15-ce7d78d-dirty`. This is `docs/PLAN-6.md` Stage B,
task B.10.

## What changed in the bundle

Everything from Stage B (B.1 through B.9): the `--spawn` handoff path in
`src/ROUTING.md`, the `ledger_cell_means`/`--record --pending` rewiring in
`tools/route.py` and `tools/handoff.py`, the `.claude/context-main.json` /
`.claude/context-tasks.json` file split (A12) across `tools/context_probe.py`,
`tools/route.py`, `tools/generate_priors.py` and
`test/harness/interactive_checklist.py`, the Controller's
`RoleOutputMismatch` handling and `--budget-usd` default of 4.0
(`tools/system_controller.py`), `tools/claudep.py`'s subprocess/JSON error
boundary, atomic writes in `route.py`'s ledger completion, and
`src/settings.fragment.json` gaining `permissions.allow` for
`Bash(python3 *)` and a real top-level `autoCompactWindow: 200000` key (no
more `_user_settings` block). `preflight.py` gained an eighth
(now non-bundle) check, "python3 on PATH". `test/harness/check.py` gained
the ROUTE-MODES check; the harness is 32 checks total.

## Install

`dist/.claude/`, `ORCHESTRATOR.md`, `README.md`, `preflight.py`,
`CLAUDE.template.md`, `tools/*.py`, `src/*.json` and `src/System/` copied
over the prior `orchestrator-scratch` install (previously
`2026-09-15-ce7d78d-dirty`). `ORCHESTRATOR_VERSION` confirmed updated to
`2026-09-16-b55d618`.

The new `autoCompactWindow` fragment key is not merged automatically by the
install steps (`src/README.md`'s existing-project path only says to merge
`settings.fragment.json` by hand); confirmed it was not already set via any
other precedence layer (`~/.claude/settings.json`, the
`CLAUDE_CODE_AUTO_COMPACT_WINDOW` env var, or `.claude/settings.local.json`)
before merging `"autoCompactWindow": 200000` into
`orchestrator-scratch/.claude/settings.json` by hand, as the fragment
specifies.

`python3 preflight.py` from the project root: 0 failing, 1 needing manual
follow-up (organisation effort limits), of 18 checks. Claude Code 2.1.273.
`route.py --selftest`: PASS, 15 scenarios, matching this bundle's harness.

## Runs against this install

None. This is a mechanical bundle upgrade to close out Stage B before
Stage C and D begin; no live task was routed through this install. The
first task that does route through it should log the cell chosen and
whether it was agreed with, per the protocol's normal entry shape.
