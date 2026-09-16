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
| `self_directed` | unless `expected_action` is set | `true` or `false`. Whether the task demands sustained, self-directed investigation that reshapes its own plan (`ROUTING.md` section 1, not section 2 as this row once said: the assessment moved there before this note was corrected). `false` for every fixture except F18, added 2026-09-11 (D39, `docs/DECISIONS.md`) when the table was found to have five inputs, not three |
| `prior_failure` | unless `expected_action` is set | `"none"` or `"failed_at_xhigh"`. Whether a documented failure at `xhigh` on this same task already exists (the frontier row). `"none"` for every fixture except F14, added alongside `self_directed` |
| `expected_cell` | unless `expected_action` is set | A worker name from `src/agents/` |
| `also_acceptable` | no | Further worker names that score as agreement |
| `expected_action` | no | `clarify` when the correct response is to ask rather than spawn; `expected_cell` is then null |
| `rationale` | yes | Why that cell, in one sentence |
| `note` | no | What the fixture is designed to expose |
| `assigned_by` | yes | Who assigned the expected cell and when |

## Coverage

**Rewritten 2026-09-16 (docs/PLAN-6.md Stage C.3, B5).** D44 and D45
(2026-09-14) collapsed the eleven-rule table this section used to
describe to two rules: the floor (`worker-sonnet-low`, every assessed
task) and the frontier (`worker-opus-max`/`worker-fable-max`, reached
only on `prior_failure: failed_at_xhigh`). Sixteen of the eighteen
fixtures land on the floor and back it trivially (`check.py`'s
ROW-BACKED check); F14 sets `prior_failure: failed_at_xhigh` and backs
the frontier rule; F16 sets `expected_action: clarify` and tests the
clarify rule (`ROUTING.md` section 1.2) rather than a destination. No
fixture is a "trap" against a table row any more, since there is only
one row below the frontier to trap against. `(mechanical, long,
contained)` and `(mechanical, long, consequential)` remain an open,
documented gap in `ROUTING.md`, unchanged by the table's collapse.

The history below predates D44 and is kept for provenance, not as a
description of the current table:

F01 to F14 covered every row of the eleven-rule table at least once. F15
and F16 were traps (importance language, underspecification) against
that table; F16 is still the clarify fixture today. F17 formerly exposed
a gap (no table row covered a mechanical task with consequential blast
radius); D9 closed that gap by adding the row F17's own rationale had
already worked around, so F17 backed that row rather than exposing its
absence. F18 backed the `worker-fable-xhigh` row, replacing an earlier
fixture (F19) that briefly backed a different attempt at the
mechanical-long-horizon gap: D22 added that row and F19 to test it, both
were reverted by D27 once F03 and F07 regressed on the identical,
unchanged bundle across repeated runs, and F19 was removed outright
because a fixture asserting a cell for a triple the table deliberately
leaves uncovered would only read as a permanent, uninformative failure.
