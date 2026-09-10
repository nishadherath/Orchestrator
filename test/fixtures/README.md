# Routing fixtures

`routing.jsonl` holds calibration tasks with a human-assigned correct cell. The
harness validates the file; `test/harness/score_routing.py` runs the tasks
through an orchestrator and scores the cell it picks. Tune the routing table
against these, never against anecdote.

Review status: eighteen fixtures, F01 to F18. Seventeen are marked
`assigned_by: claude, 2026-09-05; reviewed and confirmed by Jeb, 2026-09-05`.
F18 was added later, marked `assigned_by: claude, 2026-09-07; reviewed and
confirmed by Jeb, 2026-09-07`. The expected cells are ground truth, not a
proposal: a scored run measures routing agreement against a human-confirmed
label. A fixture added later without that confirmation is a proposal until it
gets one, and score_routing.py's report notes when any loaded fixture still
says "pending human review".

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
traps (importance language, underspecification). F17 formerly exposed a gap
(no table row covered a mechanical task with consequential blast radius);
D9 closed that gap by adding the row F17's own rationale had already worked
around, so F17 now backs that row rather than exposing its absence. F18 backs
the `worker-fable-xhigh` row, replacing an earlier fixture (F19) that briefly
backed a different attempt at the mechanical-long-horizon gap: D22 added that
row and F19 to test it, both were reverted by D27 once F03 and F07 regressed
on the identical, unchanged bundle across repeated runs, and F19 was removed
outright because a fixture asserting a cell for a triple the table
deliberately leaves uncovered would only read as a permanent, uninformative
failure. `(mechanical, long, contained)` and `(mechanical, long,
consequential)` remain an open, documented gap in `ROUTING.md`.
