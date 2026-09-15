# Routing score summary, reporting, 9 runs, 2026-09-14 02:41 at a19a815

Orchestrator model: opus. Bundle: 2026-09-14-b6605f4. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes. Mode: assess and select.

Grade: reporting (at or above 9 runs).

Overall agreement 134/162 (82.7%, 95% Wilson [76.2%, 87.8%]). Mean cost per run: USD 1.9673; total across 9 costed of 9 runs: USD 17.7057.

13 of 18 fixtures clear the 70% Wilson lower bound.

| Fixture | Agreements | Runs | Rate | 95% Wilson interval | Clears 0.7 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | 9 | 9 | 100% | [70%, 100%] | yes |
| F02 | 9 | 9 | 100% | [70%, 100%] | yes |
| F03 | 9 | 9 | 100% | [70%, 100%] | yes |
| F04 | 9 | 9 | 100% | [70%, 100%] | yes |
| F05 | 9 | 9 | 100% | [70%, 100%] | yes |
| F06 | 9 | 9 | 100% | [70%, 100%] | yes |
| F07 | 9 | 9 | 100% | [70%, 100%] | yes |
| F08 | 9 | 9 | 100% | [70%, 100%] | yes |
| F09 | 7 | 9 | 78% | [45%, 94%] | no |
| F10 | 1 | 9 | 11% | [2%, 44%] | no |
| F11 | 0 | 9 | 0% | [0%, 30%] | no |
| F12 | 2 | 9 | 22% | [6%, 55%] | no |
| F13 | 9 | 9 | 100% | [70%, 100%] | yes |
| F14 | 9 | 9 | 100% | [70%, 100%] | yes |
| F15 | 9 | 9 | 100% | [70%, 100%] | yes |
| F16 | 9 | 9 | 100% | [70%, 100%] | yes |
| F17 | 9 | 9 | 100% | [70%, 100%] | yes |
| F18 | 7 | 9 | 78% | [45%, 94%] | no |

A wide interval on a fixture run only a few times is sample noise, not necessarily a wrong rule; widen --runs before concluding the rubric is wrong for that cell (ROUTING.md section 4 still wants three or more disagreements on one starting cell). "Clears 0.7" is the same reporting bar benchmark.py uses; below nine runs it cannot read yes at all, even for a perfect record (eight of eight gives a lower bound of 67.6 percent, nine of nine is the smallest perfect record that clears 70 percent), so a "no" at steering grade is structural, not evidence the rubric is wrong.
