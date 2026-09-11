# Routing score, steering, two-stage, 3 axes (run 2 of 3) 2026-09-11 16:11 at d3371ca

Orchestrator model: sonnet. Bundle: 2026-09-11-d65b476-dirty-rubric-only. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch-rubric-only`. Fixtures reviewed by a human: yes.

Grade: steering (fewer than 9 runs; steering only, not a basis for a table or fixture change, D37).

All fields agree 7/17 (the primary metric, per docs/CLASSIFIER-DESIGN.md: cell agreement forgives up to a third of single-field errors, docs/PREMISES.md). Cell agreement (derived via tools/route.py) 10/17. Cost reported by claude: USD 0.1623.

| Fixture | Expected | Chosen | Fields agree | Cell agree | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | mechanical/short/contained; self_directed=False; prior_failure=none | mechanical/short/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, short, contained; self_directed: false; prior_failure: none |
| F02 | mechanical/short/contained; self_directed=False; prior_failure=none | mechanical/short/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, short, contained; self_directed: false; prior_failure: none |
| F03 | mechanical/medium/contained; self_directed=False; prior_failure=none | mechanical/long/contained; self_directed=False; prior_failure=none | 4/5 | no | assessment: mechanical, long, contained; self_directed: false; prior_failure: none |
| F04 | structured/short/contained; self_directed=False; prior_failure=none | mechanical/short/contained; self_directed=False; prior_failure=none | 4/5 | yes | assessment: mechanical, short, contained; self_directed: false; prior_failure: none |
| F05 | structured/medium/contained; self_directed=False; prior_failure=none | structured/medium/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: structured, medium, contained; self_directed: false; prior_failure: none |
| F06 | structured/medium/consequential; self_directed=False; prior_failure=none | structured/medium/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: structured, medium, consequential; self_directed: false; prior_failure: none |
| F07 | structured/long/contained; self_directed=False; prior_failure=none | structured/long/consequential; self_directed=True; prior_failure=none | 3/5 | yes | assessment: structured, long, consequential; self_directed: true; prior_failure: none |
| F08 | structured/medium/consequential; self_directed=False; prior_failure=none | structured/medium/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: structured, medium, consequential; self_directed: false; prior_failure: none |
| F09 | open/short/contained; self_directed=False; prior_failure=none | structured/medium/consequential; self_directed=False; prior_failure=none | 2/5 | no | assessment: structured, medium, consequential; self_directed: false; prior_failure: none |
| F10 | open/medium/contained; self_directed=False; prior_failure=none | open/medium/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: open, medium, contained; self_directed: false; prior_failure: none |
| F11 | open/long/consequential; self_directed=False; prior_failure=none | open/long/consequential; self_directed=True; prior_failure=none | 4/5 | no | assessment: open, long, consequential; self_directed: true; prior_failure: none |
| F12 | open/long/consequential; self_directed=False; prior_failure=none | open/long/consequential; self_directed=True; prior_failure=none | 4/5 | no | assessment: open, long, consequential; self_directed: true; prior_failure: none |
| F13 | open/long/contained; self_directed=False; prior_failure=none | open/long/consequential; self_directed=True; prior_failure=none | 3/5 | no | assessment: open, long, consequential; self_directed: true; prior_failure: none |
| F14 | open/long/consequential; self_directed=False; prior_failure=failed_at_xhigh | open/long/consequential; self_directed=True; prior_failure=failed_at_xhigh | 4/5 | yes | assessment: open, long, consequential; self_directed: true; prior_failure: failed_at_xhigh |
| F15 | mechanical/short/contained; self_directed=False; prior_failure=none | mechanical/short/consequential; self_directed=False; prior_failure=none | 4/5 | no | assessment: mechanical, short, consequential; self_directed: false; prior_failure: none |
| F17 | mechanical/short/consequential; self_directed=False; prior_failure=none | mechanical/short/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, short, consequential; self_directed: false; prior_failure: none |
| F18 | open/long/consequential; self_directed=True; prior_failure=none | open/medium/consequential; self_directed=True; prior_failure=none | 4/5 | no | assessment: open, medium, consequential; self_directed: true; prior_failure: none |

Cell agreement is reported for context, not as the grade: a model can misjudge one field and still be routed correctly by construction (the table is many-to-one), so all-fields agreement is what this run's grade and Wilson interval are computed from.
