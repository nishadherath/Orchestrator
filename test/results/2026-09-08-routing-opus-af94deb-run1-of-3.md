# Routing score (run 1 of 3) 2026-09-08 07:50 at 9393ab9

Orchestrator model: opus. Bundle: 2026-09-07-af94deb. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes. Mode: assess and select.

Agreement 14/18. Over-provisioned 1, under-provisioned 3, unparsed 0. Cost reported by claude: USD 3.5411.

| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F02 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F03 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: mechanical, medium, contained; worker: worker-sonnet-medium; action: spawn |
| F04 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: structured, short, contained; worker: worker-sonnet-low; action: spawn |
| F05 | worker-sonnet-medium | worker-sonnet-low | no | 2/3 | under | assessment: structured, short, contained; worker: worker-sonnet-low; action: spawn |
| F06 | worker-sonnet-high | worker-sonnet-high | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F07 | worker-sonnet-xhigh | worker-sonnet-xhigh | yes | 2/3 | exact | assessment: structured, long, consequential; worker: worker-sonnet-xhigh; action: spawn |
| F08 | worker-sonnet-high | worker-sonnet-high | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F09 | worker-sonnet-low | worker-opus-high | no | 2/3 | over | assessment: open, medium, contained; worker: worker-opus-high; action: spawn |
| F10 | worker-opus-high | worker-opus-high | yes | 3/3 | exact | assessment: open, medium, contained; worker: worker-opus-high; action: spawn |
| F11 | worker-opus-xhigh | worker-sonnet-high | no | 1/3 | under | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F12 | worker-opus-xhigh | worker-opus-xhigh | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F13 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: open, long, contained; worker: worker-sonnet-low; action: spawn |
| F14 | worker-opus-max | worker-opus-max | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-max; action: spawn |
| F15 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F16 | [clarify] | [clarify] | yes |  | n/a | assessment: open, medium, contained; worker: none; action: clarify |
| F17 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: mechanical, short, consequential; worker: worker-sonnet-medium; action: spawn |
| F18 | worker-fable-xhigh | worker-opus-xhigh | no | 2/3 | under | assessment: open, medium, consequential; worker: worker-opus-xhigh; action: spawn |

Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4).
