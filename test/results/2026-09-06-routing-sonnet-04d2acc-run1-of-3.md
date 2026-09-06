# Routing score (run 1 of 3) 2026-09-06 19:05 at 8ed0845

Orchestrator model: sonnet. Bundle: 2026-09-06-04d2acc. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes.

Agreement 13/17. Over-provisioned 0, under-provisioned 4, unparsed 0. Cost reported by claude: USD 0.6630.

| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F02 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F03 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: mechanical, medium, contained; worker: worker-sonnet-medium; action: spawn |
| F04 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: structured, short, contained; worker: worker-sonnet-medium; action: spawn |
| F05 | worker-sonnet-medium | worker-sonnet-medium | yes | 2/3 | exact | assessment: structured, short, contained; worker: worker-sonnet-medium; action: spawn |
| F06 | worker-sonnet-high | worker-sonnet-high | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F07 | worker-sonnet-xhigh | worker-sonnet-xhigh | yes | 2/3 | exact | assessment: structured, long, consequential; worker: worker-sonnet-xhigh; action: spawn |
| F08 | worker-sonnet-xhigh | worker-sonnet-high | no | 2/3 | under | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F09 | worker-opus-high | worker-sonnet-high | no | 0/3 | under | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F10 | worker-opus-high | worker-opus-high | yes | 3/3 | exact | assessment: open, medium, contained; worker: worker-opus-high; action: spawn |
| F11 | worker-opus-xhigh | worker-opus-xhigh | yes | 2/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F12 | worker-opus-xhigh | worker-sonnet-xhigh | no | 2/3 | under | assessment: structured, long, consequential; worker: worker-sonnet-xhigh; action: spawn |
| F13 | worker-fable-xhigh | worker-opus-xhigh | no | 2/3 | under | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F14 | worker-opus-max | worker-opus-max | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-max; action: spawn |
| F15 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F16 | [clarify] | [clarify] | yes |  | n/a | assessment: open, long, consequential; worker: none; action: clarify |
| F17 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: mechanical, short, consequential; worker: worker-sonnet-medium; action: spawn |

Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4).
