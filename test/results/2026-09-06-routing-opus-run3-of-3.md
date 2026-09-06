# Routing score (run 3 of 3) 2026-09-06 18:46 at 182aa1b

Orchestrator model: opus. Bundle: 2026-09-05-4cf35f7. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes.

Agreement 14/17. Over-provisioned 2, under-provisioned 2, unparsed 0. Cost reported by claude: USD 3.0536.

| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F02 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F03 | worker-sonnet-medium | worker-sonnet-high | no | 2/3 | over | assessment: mechanical, long, contained; worker: worker-sonnet-high; action: spawn |
| F04 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: structured, short, contained; worker: worker-sonnet-medium; action: spawn |
| F05 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: structured, medium, contained; worker: worker-sonnet-medium; action: spawn |
| F06 | worker-sonnet-high | worker-sonnet-high | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F07 | worker-sonnet-xhigh | worker-sonnet-high | no | 2/3 | under | assessment: mechanical, long, contained; worker: worker-sonnet-high; action: spawn |
| F08 | worker-sonnet-xhigh | worker-sonnet-high | no | 2/3 | under | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F09 | worker-opus-high | worker-opus-high | yes | 2/3 | exact | assessment: open, medium, contained; worker: worker-opus-high; action: spawn |
| F10 | worker-opus-high | worker-opus-high | yes | 3/3 | exact | assessment: open, medium, contained; worker: worker-opus-high; action: spawn |
| F11 | worker-opus-xhigh | worker-opus-xhigh | yes | 2/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F12 | worker-opus-xhigh | worker-opus-xhigh | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F13 | worker-fable-xhigh | worker-fable-xhigh | yes | 2/3 | exact | assessment: open, long, consequential; worker: worker-fable-xhigh; action: spawn |
| F14 | worker-opus-max | worker-fable-max | yes | 3/3 | over | assessment: open, long, consequential; worker: worker-fable-max; action: spawn |
| F15 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F16 | [clarify] | [clarify] | yes |  | n/a | assessment: open, medium, contained; worker: none; action: clarify |
| F17 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: mechanical, short, consequential; worker: worker-sonnet-medium; action: spawn |

Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4).
