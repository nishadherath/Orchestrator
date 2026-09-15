# Routing score, steering, two-stage, 2 axes (run 2 of 3) 2026-09-11 16:34 at e776fe3

Orchestrator model: sonnet. Bundle: 2026-09-11-d65b476-dirty-rubric-only. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch-rubric-only`. Fixtures reviewed by a human: yes.

Grade: steering (fewer than 9 runs; steering only, not a basis for a table or fixture change, D37).

All fields agree 12/17 (the primary metric, per docs/CLASSIFIER-DESIGN.md: cell agreement forgives up to a third of single-field errors, docs/PREMISES.md). Cell agreement (derived via tools/route.py) 9/17. Cost reported by claude: USD 0.2126.

| Fixture | Expected | Chosen | Fields agree | Cell agree | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | mechanical/contained; self_directed=False; prior_failure=none | mechanical/contained; self_directed=False; prior_failure=none | 4/4 | yes | assessment: mechanical, contained; self_directed: false; prior_failure: none |
| F02 | mechanical/contained; self_directed=False; prior_failure=none | mechanical/contained; self_directed=False; prior_failure=none | 4/4 | yes | assessment: mechanical, contained; self_directed: false; prior_failure: none |
| F03 | mechanical/contained; self_directed=False; prior_failure=none | mechanical/contained; self_directed=False; prior_failure=none | 4/4 | no | assessment: mechanical, contained; self_directed: false; prior_failure: none |
| F04 | structured/contained; self_directed=False; prior_failure=none | structured/contained; self_directed=False; prior_failure=none | 4/4 | yes | assessment: structured, contained; self_directed: false; prior_failure: none |
| F05 | structured/contained; self_directed=False; prior_failure=none | structured/contained; self_directed=False; prior_failure=none | 4/4 | no | assessment: structured, contained; self_directed: false; prior_failure: none |
| F06 | structured/consequential; self_directed=False; prior_failure=none | structured/consequential; self_directed=False; prior_failure=none | 4/4 | yes | assessment: structured, consequential; self_directed: false; prior_failure: none |
| F07 | structured/contained; self_directed=False; prior_failure=none | structured/contained; self_directed=False; prior_failure=none | 4/4 | no | assessment: structured, contained; self_directed: false; prior_failure: none |
| F08 | structured/consequential; self_directed=False; prior_failure=none | structured/consequential; self_directed=False; prior_failure=none | 4/4 | yes | assessment: structured, consequential; self_directed: false; prior_failure: none |
| F09 | open/contained; self_directed=False; prior_failure=none | structured/consequential; self_directed=False; prior_failure=none | 2/4 | no | assessment: structured, consequential; self_directed: false; prior_failure: none |
| F10 | open/contained; self_directed=False; prior_failure=none | open/contained; self_directed=False; prior_failure=none | 4/4 | no | assessment: open, contained; self_directed: false; prior_failure: none |
| F11 | open/consequential; self_directed=False; prior_failure=none | open/consequential; self_directed=True; prior_failure=none | 3/4 | yes | assessment: open, consequential; self_directed: true; prior_failure: none |
| F12 | open/consequential; self_directed=False; prior_failure=none | structured/consequential; self_directed=False; prior_failure=none | 3/4 | no | assessment: structured, consequential; self_directed: false; prior_failure: none |
| F13 | open/contained; self_directed=False; prior_failure=none | open/consequential; self_directed=True; prior_failure=none | 2/4 | no | assessment: open, consequential; self_directed: true; prior_failure: none |
| F14 | open/consequential; self_directed=False; prior_failure=failed_at_xhigh | open/consequential; self_directed=True; prior_failure=failed_at_xhigh | 3/4 | yes | assessment: open, consequential; self_directed: true; prior_failure: failed_at_xhigh |
| F15 | mechanical/contained; self_directed=False; prior_failure=none | mechanical/contained; self_directed=False; prior_failure=none | 4/4 | yes | assessment: mechanical, contained; self_directed: false; prior_failure: none |
| F17 | mechanical/consequential; self_directed=False; prior_failure=none | mechanical/consequential; self_directed=False; prior_failure=none | 4/4 | yes | assessment: mechanical, consequential; self_directed: false; prior_failure: none |
| F18 | open/consequential; self_directed=True; prior_failure=none | open/consequential; self_directed=True; prior_failure=none | 4/4 | no | assessment: open, consequential; self_directed: true; prior_failure: none |

Cell agreement is reported for context, not as the grade: a model can misjudge one field and still be routed correctly by construction (the table is many-to-one), so all-fields agreement is what this run's grade and Wilson interval are computed from.
