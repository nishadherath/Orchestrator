# W08 reserved comparison

Result: **PASS**. All 48 authorised episodes completed with
valid identity, accounting, event chains, actor boundaries and protected oracles.

Reconciled spend was **USD 1.053580005** of the
USD 200 ceiling.

| Policy | Accepted | Attempts | False successes | Spend | Cost/accepted |
| :--- | ---: | ---: | ---: | ---: | ---: |
| B0 | 12/24 | 25 | 12 | USD 0.524667002 | USD 0.043722250 |
| B1 | 10/24 | 24 | 14 | USD 0.528913003 | USD 0.052891300 |

Paired outcomes: B0 2 wins, B1 0 wins and 22 ties. B1 completed 5 of 11 ordinary task families in both repetitions; the gate required 10.
Neither arm passed H11 in either repetition. B1 had more false successes
and a higher cost per accepted episode. No Opus or Controller path ran.

## Release-gate decision

B1 failed the predeclared reserved promotion gates: it accepted fewer episodes, increased false successes, cost more per accepted episode, completed only five ordinary task families twice and did not pass H11. B0 recorded two paired wins, no paired losses and slightly lower total spend. Package the simpler B0 policy as the qualified default without retuning on reserved outcomes.
