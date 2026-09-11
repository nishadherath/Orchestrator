# Routing score summary, steering, 3 runs, 2026-09-11 12:16 at 3e7db09

Orchestrator model: opus. Bundle: 2026-09-07-af94deb. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch`. Fixtures reviewed by a human: yes. Mode: assess and select.

Grade: steering (fewer than 9 runs; steering only, not a basis for a table or fixture change, D37).

Overall agreement 3/3 (100.0%, 95% Wilson [43.8%, 100.0%]). Mean cost per run: USD 0.1209; total across 3 costed of 3 runs: USD 0.3627.

0 of 1 fixtures clear the 70% Wilson lower bound, but this is steering grade (fewer than 9 runs): a fixture clearing the bar here is not yet reporting-grade confirmation.

| Fixture | Agreements | Runs | Rate | 95% Wilson interval | Clears 0.7 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | 3 | 3 | 100% | [44%, 100%] | no |

A wide interval on a fixture run only a few times is sample noise, not necessarily a wrong rule; widen --runs before concluding the rubric is wrong for that cell (ROUTING.md section 4 still wants three or more disagreements on one starting cell). "Clears 0.7" is the same reporting bar benchmark.py uses; below nine runs it cannot read yes at all, even for a perfect record (eight of eight gives a lower bound of 67.6 percent, nine of nine is the smallest perfect record that clears 70 percent), so a "no" at steering grade is structural, not evidence the rubric is wrong.
