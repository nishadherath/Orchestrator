# Dogfood install log 2026-09-14

Per `CLAUDE.md`'s Dogfooding protocol: install from `dist/`, never from
`src/`, into a consumer project. Project: `orchestrator-scratch`. Bundle
version `2026-09-14-b6605f4` (source commit `b6605f4`, clean tree),
replacing `2026-09-07-af94deb`. This is `docs/PLAN.md` Stage 8.6, done
before 8.5 because the after-measurement has to run against the installed
table.

## What changed in the bundle

`src/routing_table.json` went from eleven rules to four (D43): the
escalation rule, `open-medium` at `worker-opus-high`, and two floor rules
covering everything else. `ORCHESTRATOR.md` section 2 is transcribed from
it. Seven worker definitions changed their description line only:
`worker-sonnet-low` and `worker-opus-high` name their new rules;
`worker-sonnet-medium`, `worker-sonnet-high`, `worker-sonnet-xhigh`,
`worker-opus-xhigh` and `worker-fable-xhigh` now say they are not in the
table and are reached only by escalation. No persona text changed
(`test/harness/persona.sha256` unchanged, PERSONA check green).

## Install

`dist/.claude/` copied over `orchestrator-scratch/.claude/` (agents,
commands, `ORCHESTRATOR_VERSION`), and `ORCHESTRATOR.md`, `README.md` and
`preflight.py` copied to the project root. `diff -rq` between `dist/.claude`
and the installed tree: identical. `python3 preflight.py` from the project
root: 0 failing, 1 needing manual follow-up (organisation effort limits,
not checkable from a shell), of 8 checks; "15 of 15 worker definitions
found; bundle version 2026-09-14-b6605f4".

Version noted by preflight: Claude Code 2.1.268. `docs/FINDINGS.md`'s
verified-against line says 2.1.263; nothing in this stage depends on a
behaviour that changed between them, but the after-measurement runs on
2.1.268 and the before-measurement ran on 2.1.263, and that is a
difference between the two runs besides the table.

## Runs against this install

The after-measurement (Stage 8.5) is the dogfood run for this bundle: nine
reporting-grade passes of the eighteen routing fixtures through an opus
orchestrator, recorded by `score_routing.py --record` as
`test/results/2026-09-14-routing-opus-b6605f4-*.md`. Whether the cell
chosen was agreed with is what those files score, fixture by fixture,
against `expected_cell`.
