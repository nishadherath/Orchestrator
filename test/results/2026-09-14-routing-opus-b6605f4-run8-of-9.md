# Routing score, reporting (run 8 of 9) 2026-09-14 02:35 at a19a815

Orchestrator model: opus. Bundle: 2026-09-14-b6605f4. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes. Mode: assess and select.

Grade: reporting (at or above 9 runs).

Agreement 14/18. Over-provisioned 4, under-provisioned 1, unparsed 0. Cost reported by claude: USD 1.6335.

| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F02 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F03 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, medium, contained; worker: worker-sonnet-low; action: spawn |
| F04 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: structured, short, contained; worker: worker-sonnet-low; action: spawn |
| F05 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: structured, medium, contained; worker: worker-sonnet-low; action: spawn |
| F06 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-low; action: spawn |
| F07 | worker-sonnet-low | worker-sonnet-low | yes | 2/3 | exact | assessment: structured, long, consequential; worker: worker-sonnet-low; action: spawn |
| F08 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-low; action: spawn |
| F09 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: open, short, contained; worker: worker-sonnet-low; action: spawn |
| F10 | worker-opus-high | worker-sonnet-low | no | 2/3 | under | assessment: open, short, contained; worker: worker-sonnet-low; action: spawn |
| F11 | worker-sonnet-low | worker-opus-high | no | 2/3 | over | assessment: open, medium, consequential; worker: worker-opus-high; action: spawn |
| F12 | worker-sonnet-low | worker-opus-high | no | 2/3 | over | assessment: open, medium, consequential; worker: worker-opus-high; action: spawn |
| F13 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: open, long, contained; worker: worker-sonnet-low; action: spawn |
| F14 | worker-opus-max | worker-fable-max | yes | 2/3 | over | assessment: open, long, contained; worker: worker-fable-max; action: spawn |
| F15 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F16 | [clarify] | [clarify] | yes |  | n/a | assessment: open, medium, consequential; worker: none; action: clarify |
| F17 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, consequential; worker: worker-sonnet-low; action: spawn |
| F18 | worker-sonnet-low | worker-opus-high | no | 2/3 | over | assessment: open, medium, consequential; worker: worker-opus-high; action: spawn |

Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4).
