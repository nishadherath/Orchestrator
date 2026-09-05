# Routing score 2026-09-05 17:27 at ac6eaf2

Orchestrator model: opus. Bundle: 2026-09-05-1708054. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes.

Agreement 8/17. Over-provisioned 0, under-provisioned 1, unparsed 0. Cost reported by claude: USD 3.5808.

| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | worker-sonnet-low | worker-sonnet-low | no | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: clarify |
| F02 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F03 | worker-sonnet-medium | worker-sonnet-medium | yes | 3/3 | exact | assessment: mechanical, medium, contained; worker: worker-sonnet-medium; action: spawn |
| F04 | worker-sonnet-medium | [clarify] | no | 3/3 | n/a | assessment: structured, short, contained; worker: none; action: clarify |
| F05 | worker-sonnet-medium | [clarify] | no | 2/3 | n/a | assessment: structured, short, contained; worker: none; action: clarify |
| F06 | worker-sonnet-high | worker-sonnet-high | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F07 | worker-sonnet-xhigh | [clarify] | no | 2/3 | n/a | assessment: structured, long, consequential; worker: none; action: clarify |
| F08 | worker-sonnet-xhigh | worker-sonnet-high | no | 2/3 | under | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: clarify |
| F09 | worker-opus-high | [clarify] | no | 3/3 | n/a | assessment: open, short, contained; worker: none; action: clarify |
| F10 | worker-opus-high | worker-opus-high | yes | 3/3 | exact | assessment: open, medium, contained; worker: worker-opus-high; action: spawn |
| F11 | worker-opus-xhigh | worker-opus-xhigh | no | 2/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: clarify |
| F12 | worker-opus-xhigh | worker-opus-xhigh | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F13 | worker-fable-xhigh | worker-fable-xhigh | yes | 2/3 | exact | assessment: open, long, consequential; worker: worker-fable-xhigh; action: spawn |
| F14 | worker-opus-max | worker-opus-max | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-max; action: spawn |
| F15 | worker-sonnet-low | [clarify] | no | 3/3 | n/a | assessment: mechanical, short, contained; worker: none; action: clarify |
| F16 | [clarify] | [clarify] | yes |  | n/a | assessment: open, medium, contained; worker: none; action: clarify |
| F17 | worker-sonnet-medium | [clarify] | no | 3/3 | n/a | assessment: mechanical, short, consequential; worker: none; action: clarify |

Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4).
