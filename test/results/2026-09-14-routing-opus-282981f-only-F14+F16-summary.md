# Routing score summary, reporting, 9 runs, 2026-09-14 07:50 at a79a45b

Orchestrator model: opus. Bundle: 2026-09-14-282981f. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes. Mode: assess and select.

Grade: reporting (at or above 9 runs).

Overall agreement 18/18 (100.0%, 95% Wilson [82.4%, 100.0%]). Mean cost per run: USD 0.2570; total across 9 costed of 9 runs: USD 2.3132.

2 of 2 fixtures clear the 70% Wilson lower bound.

| Fixture | Agreements | Runs | Rate | 95% Wilson interval | Clears 0.7 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F14 | 9 | 9 | 100% | [70%, 100%] | yes |
| F16 | 9 | 9 | 100% | [70%, 100%] | yes |

A wide interval on a fixture run only a few times is sample noise, not necessarily a wrong rule; widen --runs before concluding the rubric is wrong for that cell (ROUTING.md section 4 still wants three or more disagreements on one starting cell). "Clears 0.7" is the same reporting bar benchmark.py uses; below nine runs it cannot read yes at all, even for a perfect record (eight of eight gives a lower bound of 67.6 percent, nine of nine is the smallest perfect record that clears 70 percent), so a "no" at steering grade is structural, not evidence the rubric is wrong.
