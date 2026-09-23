# Orchestrator audit summary

Audit date: 2026-09-17. Reviewed branch: `v1.0-beta`, commit `4fb4682`.

This summarises the completed audit and its reported findings. The detailed
analysis, source references and reproduction examples are in
[the assessment](ASSESSMENT-2026-09-17.md); the final offline results are in
[the verification record](ASSESSMENT-2026-09-17-checks.json).

## Overall conclusion

This is a useful research beta, but its adaptive routing and cost controls
need correction before unattended production use. Its strongest asset is
the evaluation framework. Its general cost-saving benefit remains unproven.

The audit examined the architecture, routing and accounting logic, Controller,
handoffs, consumer configuration, build process, documentation and selected
historical evidence. Historical live experiments were inspected, not rerun.
The review did not independently audit every historical transcript.

## 1. Project deliverables

- An installable Claude Code configuration with **15 workers**: three model
  families across five effort levels.
- A Python resolver that selects workers using task assessments, benchmark
  priors and project outcomes.
- A separate **Controller** that coordinates structured problem-solving roles.
- Context monitoring, task recovery and validated session handoffs.
- Benchmark fixtures, offline checks, historical experiments and decision records.

The product is a local developer workflow with CLI and Markdown interfaces.
There is no deployed application or cloud service in the reviewed project.

## 2. How it works

The normal cycle is:

**Task → assessment → deterministic resolver → worker → acceptance check → outcome ledger.**

The orchestrator assesses the task; Python selects the worker. Most tasks
initially go to `worker-sonnet-low`. Open, consequential tasks can instead
invoke the Controller under an explicitly labelled risk policy.

The ledger adjusts estimated success rates and costs for later tasks. This
"self-learning" is Bayesian arithmetic over local records, not model training.

The Controller runs separate Claude CLI calls for framing, verification,
generation, critique and selection. Python manages their state and validates
their records. Context hooks and handoff files preserve work across session
boundaries. Valid record structure does not establish factual correctness.

## 3. Engineering assessment and findings

Sound choices include deterministic resolution, generated worker definitions,
explicit provenance, offline verification and documented negative results.

The evidence supports a narrower claim than a general-purpose cost optimiser:

- Ten of eleven historical capability tasks passed at the cheapest tested worker.
- Routing overhead was measured at roughly the cost of a floor task.
- The Controller completed six of nine measured T10 runs and cost substantially
  more per solved task.
- Repeated trials on authored fixtures do not establish performance across
  real development backlogs.

Four implementation problems were reproduced without API calls:

| Finding | Verified behaviour |
| :--- | :--- |
| Pending work corrupts cost estimates | Five pending records replace the floor's cost and duration estimates with zero. |
| Elevated starting workers do not learn from their outcomes | Twenty direct `worker-opus-high` failures leave its estimated success rate at 90%, with zero failures counted. |
| Controller budget is not a hard aggregate cap | With USD 0.60 remaining, a mocked role call still receives a USD 2.00 allowance. Code inspection also shows concurrent calls share an unreserved balance. |
| Projection does not follow the selected starting worker | The resolver selects a worker with a recorded unit cost of USD 0.9217 while projecting USD 0.7979 using the original ladder. |

Additional concerns identified through code and document inspection:

- Total task cost is divided equally across attempted models, producing
  misleading per-model costs when attempts have different costs.
- Outcome recording depends on the orchestrator following instructions;
  successful outcomes lack mandatory independent verification.
- Ledger replacement is not protected against concurrent sessions, despite
  the schema assuming a single writer.
- Learned evidence does not expire or partition automatically by model version.
- Some documentation describes outdated check counts and project state.

The detailed assessment distinguishes reproduced defects from untested risks.
Runtime repairs were proposed, not implemented during the audit.

## 4. Status and verification

At the reviewed commit, Plans 1-6 were recorded complete, including the
previous audit remediation. That historical completion does not close the
new findings in this audit.

Fresh verification finished with **33 checks passing, zero failures and zero
skips**. The initial run encountered a permission-blocked Python launcher;
the bundled Python runtime and temporary shell configuration resolved that
environment issue. No persistent user configuration was changed.

The four reproduced defects remain present despite the green suite. The
existing checks do not cover those failure cases, and passing them does not
establish current live model behaviour.

The updated 49-file bundle was rebuilt successfully through its normal gate.
At audit completion, changes were uncommitted and its stamp correctly read
`2026-09-17-4fb4682-dirty`. `git diff --check` passed. No paid model experiments
were launched; this does not imply that the audit session itself was free.

## 5. Proposed improvements

The operator's subsequent [action plan](IMPROVEMENTS-ACTION-PLAN-2026-09-17.md)
sets execution order to 1, 2, 3, 5, 6, 4, with real-world evaluation last.
The numbered recommendations below retain their original identities.

In priority order:

1. **Correct accounting and learning.** Introduce per-attempt records with
   actual model, outcome, cost, duration and validation evidence. Separate
   unknown measurements from zero and direct-start outcomes from outcomes
   conditional on cheaper attempts failing.
2. **Enforce spending limits.** Reserve budgets before concurrent dispatch
   and retain accounting for aborted calls.
3. **Strengthen acceptance verification.** Detect missing completion records
   and require evidence for successful outcomes.
4. **Evaluate real tasks.** Compare cheapest-worker-plus-verification,
   adaptive routing and narrowly scoped Controller use on held-out work.
   Include failed attempts and operator effort in the cost.
   The [detailed evaluation proposal](REAL-WORLD-EVALUATION-PLAN.md) defines
   24 task blueprints, implementation stages, spending limits and release gates.
5. **Reduce recurring context.** Shorten the always-loaded charter and
   retrieve specialised guidance when needed. Measure cache behaviour before
   changing session strategy. Claude Code documents that model switches lose
   cache reuse on the next request: [official caching documentation](https://code.claude.com/docs/en/prompt-caching),
   checked during the audit on 2026-09-17.
6. **Improve installation and diagnostics.** Add reversible configuration
   merging, clean-install checks and a concise status command showing pending
   work, evidence freshness and cost uncertainty.

The first correction stage was estimated at **1-3 engineering days**, including
schema migration and verification. This is planning judgement, not measured
throughput or a commitment. Paid evaluation costs require a separate projection
once the tasks, models and run counts are selected.

## Standing handoff requirements implemented

The audit added [AGENTS.md](../AGENTS.md) and updated the project charter,
consumer template and lifecycle instructions. The rebuilt bundle carries
the consumer changes.

The instructions now require concise handoffs and operator notices for every
agent launch or session transition, with target model and effort, API cost
assumptions and time ranges. They separate session API-equivalent estimates
from paid experiment subtotals and require unknown costs to be labelled.
Future consumer installs inherit these instructions; existing installs need
the updated instructions merged.

Enforcement remains instruction-based. No runtime guarantee of future agent
compliance was added. No model switch or subagent was needed for the audit.
