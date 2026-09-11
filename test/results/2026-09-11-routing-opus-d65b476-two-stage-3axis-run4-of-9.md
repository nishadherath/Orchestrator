# Routing score, reporting, two-stage, 3 axes (run 4 of 9) 2026-09-11 17:08 at 594810a

Orchestrator model: opus. Bundle: 2026-09-11-d65b476-dirty-rubric-only. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch-rubric-only`. Fixtures reviewed by a human: yes.

Grade: reporting (at or above 9 runs).

All fields agree 12/17 (the primary metric, per docs/CLASSIFIER-DESIGN.md: cell agreement forgives up to a third of single-field errors, docs/PREMISES.md). Cell agreement (derived via tools/route.py) 15/17. Cost reported by claude: USD 1.6210.

| Fixture | Expected | Chosen | Fields agree | Cell agree | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | mechanical/short/contained; self_directed=False; prior_failure=none | mechanical/short/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, short, contained; self_directed: false; prior_failure: none |
| F02 | mechanical/short/contained; self_directed=False; prior_failure=none | mechanical/short/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, short, contained; self_directed: false; prior_failure: none |
| F03 | mechanical/medium/contained; self_directed=False; prior_failure=none | mechanical/medium/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, medium, contained; self_directed: false; prior_failure: none |
| F04 | structured/short/contained; self_directed=False; prior_failure=none | structured/short/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: structured, short, contained; self_directed: false; prior_failure: none |
| F05 | structured/medium/contained; self_directed=False; prior_failure=none | structured/medium/contained; self_directed=False; prior_failure=none | 5/5 | yes | Writing tests against a stated contract is structured; the time-source investigation is one decision point (medium horizon); tests are easy to inspect and cheap to redo (contained); the task requires  |
| F06 | structured/medium/consequential; self_directed=False; prior_failure=none | structured/medium/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: structured, medium, consequential; self_directed: false; prior_failure: none |
| F07 | structured/long/contained; self_directed=False; prior_failure=none | structured/long/consequential; self_directed=False; prior_failure=none | 4/5 | yes | assessment: structured, long, consequential; self_directed: false; prior_failure: none |
| F08 | structured/medium/consequential; self_directed=False; prior_failure=none | structured/medium/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: structured, medium, consequential; self_directed: false; prior_failure: none |
| F09 | open/short/contained; self_directed=False; prior_failure=none | open/medium/contained; self_directed=False; prior_failure=none | 4/5 | no | assessment: open, medium, contained; self_directed: false; prior_failure: none |
| F10 | open/medium/contained; self_directed=False; prior_failure=none | open/short/contained; self_directed=False; prior_failure=none | 4/5 | no | assessment: open, short, contained; self_directed: false; prior_failure: none |
| F11 | open/long/consequential; self_directed=False; prior_failure=none | open/long/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: open, long, consequential; self_directed: false; prior_failure: none |
| F12 | open/long/consequential; self_directed=False; prior_failure=none | open/long/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: open, long, consequential; self_directed: false; prior_failure: none |
| F13 | open/long/contained; self_directed=False; prior_failure=none | open/long/contained; self_directed=True; prior_failure=none | 4/5 | yes | assessment: open, long, contained; self_directed: true; prior_failure: none |
| F14 | open/long/consequential; self_directed=False; prior_failure=failed_at_xhigh | open/long/consequential; self_directed=True; prior_failure=failed_at_xhigh | 4/5 | yes | assessment: open, long, consequential; self_directed: true; prior_failure: failed_at_xhigh |
| F15 | mechanical/short/contained; self_directed=False; prior_failure=none | mechanical/short/contained; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, short, contained; self_directed: false; prior_failure: none |
| F17 | mechanical/short/consequential; self_directed=False; prior_failure=none | mechanical/short/consequential; self_directed=False; prior_failure=none | 5/5 | yes | assessment: mechanical, short, consequential; self_directed: false; prior_failure: none |
| F18 | open/long/consequential; self_directed=True; prior_failure=none | open/long/consequential; self_directed=True; prior_failure=none | 5/5 | yes | assessment: open, long, consequential; self_directed: true; prior_failure: none |

Cell agreement is reported for context, not as the grade: a model can misjudge one field and still be routed correctly by construction (the table is many-to-one), so all-fields agreement is what this run's grade and Wilson interval are computed from.
