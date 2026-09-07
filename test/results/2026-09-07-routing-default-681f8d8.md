# Routing score 2026-09-07 18:51 at f912030

Orchestrator model: session default. Bundle: 2026-09-07-681f8d8. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes. Mode: assess and select.

Agreement 8/19. Over-provisioned 4, under-provisioned 3, unparsed 1. Cost reported by claude: USD 0.7466.

| Fixture | Expected | Chosen | Agree | Axes agree | Direction | Raw verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F02 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F03 | worker-sonnet-medium | worker-sonnet-low | no | 2/3 | under | assessment: mechanical, long, contained; worker: worker-sonnet-low; action: spawn |
| F04 | worker-sonnet-low | worker-sonnet-medium | no | 2/3 | over | assessment: structured, medium, contained; worker: worker-sonnet-medium; action: spawn |
| F05 | worker-sonnet-medium | worker-sonnet-high | no | 3/3 | over | assessment: structured, medium, contained; worker: worker-sonnet-high; action: spawn |
| F06 | worker-sonnet-high | worker-sonnet-high | yes | 3/3 | exact | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F07 | worker-sonnet-xhigh | worker-sonnet-xhigh | yes | 2/3 | exact | assessment: structured, long, consequential; worker: worker-sonnet-xhigh; action: spawn |
| F08 | worker-sonnet-xhigh | worker-sonnet-high | no | 2/3 | under | assessment: structured, medium, consequential; worker: worker-sonnet-high; action: spawn |
| F09 | worker-sonnet-low | worker-opus-high | no | 1/3 | over | assessment: open, medium, consequential; worker: worker-opus-high; action: spawn |
| F10 | worker-opus-high | worker-opus-high | yes | 3/3 | exact | assessment: open, medium, contained; worker: worker-opus-high; action: spawn |
| F11 | worker-opus-xhigh | worker-opus-xhigh | no | 2/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: clarify |
| F12 | worker-opus-xhigh | worker-opus-xhigh | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F13 | worker-sonnet-low | worker-fable-xhigh | no | 2/3 | over | assessment: open, long, consequential; worker: worker-fable-xhigh; action: spawn |
| F14 | worker-opus-max | worker-opus-max | yes | 3/3 | exact | assessment: open, long, consequential; worker: worker-opus-max; action: spawn |
| F15 | worker-sonnet-low | worker-sonnet-low | yes | 3/3 | exact | assessment: mechanical, short, contained; worker: worker-sonnet-low; action: spawn |
| F16 | [clarify] | worker-fable-xhigh | no |  | n/a | assessment: open, long, consequential; worker: worker-fable-xhigh; action: spawn |
| F17 | worker-sonnet-medium | [clarify] | no | 3/3 | n/a | assessment: mechanical, short, consequential; worker: none; action: clarify |
| F18 | worker-fable-xhigh | worker-opus-xhigh | no | 3/3 | under | assessment: open, long, consequential; worker: worker-opus-xhigh; action: spawn |
| F19 | worker-sonnet-low | [unparsed] | no |  | n/a | assessment: mechanical, long; contained; worker: worker-sonnet-low; action: spawn |

Three or more disagreements on one starting cell mean the rubric is wrong for that task class (ROUTING.md section 4).
