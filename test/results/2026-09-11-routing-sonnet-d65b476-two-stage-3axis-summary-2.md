# Routing score summary, reporting, two-stage, 3 axes, 9 runs, 2026-09-11 17:44 at 594810a

Orchestrator model: sonnet. Bundle: 2026-09-11-d65b476-dirty-rubric-only. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch-rubric-only`. Fixtures reviewed by a human: yes.

Grade: reporting (at or above 9 runs).

All-fields agreement (primary) 74/153 (48.4%, 95% Wilson [40.6%, 56.2%]). Mean cost per run: USD 0.2203; total across 9 costed of 9 runs: USD 1.9831.

Cell agreement (derived, reported for context) 89/153 (58.2%, 95% Wilson [50.2%, 65.7%]).

4 of 17 fixtures clear the 70% Wilson lower bound on all-fields agreement.

| Fixture | Fields agree | Runs | Rate | 95% Wilson interval | Cell agree rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | 7 | 9 | 78% | [45%, 94%] | 7/9 |
| F02 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F03 | 2 | 9 | 22% | [6%, 55%] | 2/9 |
| F04 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F05 | 7 | 9 | 78% | [45%, 94%] | 7/9 |
| F06 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F07 | 0 | 9 | 0% | [0%, 30%] | 5/9 |
| F08 | 8 | 9 | 89% | [56%, 98%] | 8/9 |
| F09 | 0 | 9 | 0% | [0%, 30%] | 0/9 |
| F10 | 8 | 9 | 89% | [56%, 98%] | 9/9 |
| F11 | 0 | 9 | 0% | [0%, 30%] | 0/9 |
| F12 | 0 | 9 | 0% | [0%, 30%] | 0/9 |
| F13 | 0 | 9 | 0% | [0%, 30%] | 0/9 |
| F14 | 0 | 9 | 0% | [0%, 30%] | 9/9 |
| F15 | 4 | 9 | 44% | [19%, 73%] | 4/9 |
| F17 | 9 | 9 | 100% | [70%, 100%] | 9/9 |
| F18 | 2 | 9 | 22% | [6%, 55%] | 2/9 |

A wide interval on a fixture run only a few times is sample noise, not necessarily a wrong rule; widen --runs before drawing a conclusion. All-fields agreement, not cell agreement, is what this summary's grade is computed from, per docs/CLASSIFIER-DESIGN.md.
