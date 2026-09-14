# Dogfood install log 2026-09-15

Per `CLAUDE.md`'s Dogfooding protocol: install from `dist/`, never from
`src/`, into a consumer project. Project: `orchestrator-scratch`. Bundle
version `2026-09-15-9b5f64b` (source commit `9b5f64b`, clean tree),
replacing `2026-09-14-282981f`. This is `docs/PLAN.md` Stage 12.5, done
before 12.4 because the after-measurement has to run against the installed
bundle, as Stage 8 did.

## What changed in the bundle

Nothing in the table, the fixtures or the fifteen worker definitions
(`generate_workers.py --check`: 15 definitions, 0 drifted; persona hash
unchanged). `ORCHESTRATOR.md` section 4's measured escalation trigger is
now two steps (D60): first `worker-sonnet-low` with `.claude/B0_BRIEF.md`
placed before the handover, then `worker-opus-high` if that returns
short. The bundle gains `.claude/B0_BRIEF.md`, the worker-facing half of
`src/System/B0_BRIEF.md` (5,836 characters, the same cut `benchmark.py
--brief` makes, so it is what Stage 9.8 measured). `preflight.py`'s
bundle check now fails if that file is missing. `README.md`'s layout
lists it.

## Install

`dist/.claude/` copied over `orchestrator-scratch/.claude/` (agents,
commands, `ORCHESTRATOR_VERSION`, `B0_BRIEF.md`), and `ORCHESTRATOR.md`,
`README.md` and `preflight.py` copied to the project root. `diff -rq`
between `dist/.claude` and the installed tree: identical.
`python3 preflight.py` from the project root: 0 failing, 1 needing manual
follow-up (organisation effort limits), of 8 checks. Claude Code 2.1.268.

## Runs against this install

The after-measurement (Stage 12.4) is the dogfood run for this bundle:
nine reporting-grade passes of all eighteen routing fixtures through an
opus orchestrator, recorded by `score_routing.py --record` as
`test/results/2026-09-15-routing-opus-9b5f64b-*.md`. The full eighteen,
not Gate C's two, because the change is to the orchestrator's
instructions and D44 showed instruction text moving assessments on
fixtures it never named; the before is D45's run against `282981f`.
Started by the session under D57.

The trigger itself (section 4, step 1 with the brief) is not exercised by
the routing fixtures, which stop at the assessment; its evidence is
Stage 9.8's benchmark (`2026-09-14-benchmark-282981f-tasks-*-brief-b0-brief.md`).
No task in this install has yet fired it live from an orchestrator
session; the first that does should be logged here.
