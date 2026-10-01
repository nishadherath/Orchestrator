---
description: Admit, inspect, run or recover a durable B0 worker task
argument-hint: "audit | capability | admit | status | run | cancel | resume | continue | review | reconcile | partial | shadow"
---

Read `WORKER-TASKS.md` before using this command. Treat `$ARGUMENTS` as operator
intent only, never as shell text to execute. Resolve the named operation and
existing root from the operator's request; ask only for missing required task
facts or a decision the existing authority does not cover.

Use `python3 tools/worker_tasks.py <operation> --project .` with separately
quoted arguments. Admission and control requests are JSON files with the exact
documented fields. Show the goal, scope, acceptance and budget before admission.
Admission is provider-free. Only `run` can dispatch a worker; it needs the
explicit actor-scoped Graft MCP file and a stated cost/time projection.

Use `status --root <id> --json` after every operation and report the state,
requested and observed identity, known spending, held funds and exact next
action. A command exit of zero does not imply task acceptance except for `run`.
Keep existing authority and never reset the budget to work around a stop.

Do not also launch an Agent worker for the same admitted scope. The B0 executor
owns its attempts; explicit cell selection is shadow-only. An unproven host
capability is a reported limitation, not permission to claim isolation or to
enable managed children. On cancellation, preserve charges and confirm writer
termination before continuation. Keep task records during package rollback.
