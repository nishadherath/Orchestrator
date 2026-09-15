# Routing score summary, reporting, two-stage, 3 axes, 9 runs, 2026-09-11 17:27 at 594810a

Orchestrator model: opus. Bundle: 2026-09-11-d65b476-dirty-rubric-only. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch-rubric-only`. Fixtures reviewed by a human: yes.

Grade: reporting (at or above 9 runs).

All-fields agreement (primary) 119/153 (77.8%, 95% Wilson [70.6%, 83.6%]). Mean cost per run: USD 1.7505; total across 9 costed of 9 runs: USD 15.7541.

Cell agreement (derived, reported for context) 141/153 (92.2%, 95% Wilson [86.8%, 95.5%]).

10 of 17 fixtures clear the 70% Wilson lower bound on all-fields agreement.

| Fixture | Fields agree | Runs | Rate | 95% Wilson interval | Cell agree rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F02 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F03 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F04 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F05 | 8 | 9 | 89% | [56%, 98%] | 9/9 |
| F06 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F07 | 0 | 9 | 0% | [0%, 30%] | 4/9 |
| F08 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F09 | 3 | 9 | 33% | [12%, 65%] | 3/9 |
| F10 | 8 | 9 | 89% | [56%, 98%] | 8/9 |
| F11 | 7 | 9 | 78% | [45%, 94%] | 9/9 |
| F12 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F13 | 0 | 9 | 0% | [0%, 30%] | 9/9 |
| F14 | 3 | 9 | 33% | [12%, 65%] | 9/9 |
| F15 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F17 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F18 | 9 | 9 | 100% | [70%, 100%] | 9/9 |

A wide interval on a fixture run only a few times is sample noise, not necessarily a wrong rule; widen --runs before drawing a conclusion. All-fields agreement, not cell agreement, is what this summary's grade is computed from, per docs/CLASSIFIER-DESIGN.md.
