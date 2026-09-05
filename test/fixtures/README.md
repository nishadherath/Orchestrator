# Routing fixtures

`routing.jsonl` holds calibration tasks with a human-assigned correct cell. The
harness validates the file; `test/harness/score_routing.py` runs the tasks
through an orchestrator and scores the cell it picks. Tune the routing table
against these, never against anecdote.

Review status: every row is marked `assigned_by: claude, 2026-09-05; pending
human review`. Until a human replaces that value, the expected cells are a
proposal, not ground truth, and a scored run measures agreement with the
proposal.

## Schema, one JSON object per line

| Field | Required | Value |
| :--- | :--- | :--- |
| `id` | yes | `F` followed by two digits, unique |
| `task` | yes | The task text as the orchestrator receives it |
| `assessment` | unless `expected_action` is set | `{"sensitivity": mechanical or structured or open, "horizon": short or medium or long, "blast": contained or consequential}` |
| `expected_cell` | unless `expected_action` is set | A worker name from `src/agents/` |
| `also_acceptable` | no | Further worker names that score as agreement |
| `expected_action` | no | `clarify` when the correct response is to ask rather than spawn; `expected_cell` is then null |
| `rationale` | yes | Why that cell, in one sentence |
| `note` | no | What the fixture is designed to expose |
| `assigned_by` | yes | Who assigned the expected cell and when |

## Coverage

F01 to F14 cover every row of the routing table at least once. F15 and F16 are
traps (importance language, underspecification). F17 exposes a gap: no table
row covers a mechanical task with consequential blast radius.
