# Q4S transport and execution investigation

Date: 2026-09-26 Australia/Sydney. Scope: read-only analysis of the frozen
Q4R P08 screen and provider-free source inspection. No new Claude model call
was made for this investigation. The Q4R manifest, receipts, grades and
decision remain unchanged.

## Observed evidence

| P08 arm | Root | Quality-v2 | Permitted source edits | Report | Calls | Provider-reported API-equivalent USD |
| :--- | :--- | ---: | ---: | :--- | ---: | ---: |
| B0 A, Sonnet-low | accepted | 85 | present | structured and valid | 1 | 0.484867 |
| B0 B, Sonnet-low | accepted | 85 | present | structured and valid | 1 | 0.491983 |
| Sonnet-high | blocked | 15 | 0 of 4 paths | transport-invalid | 1 settled | 0.6894318 |

The [Q4R result](worker-q4r-r1-2026-09-26.md) and [terminal reconciliation](../../test/results/2026-09-25-worker-q4r-r1-reconciliation.json)
bind the stopped patch, executable grade and settled budget. The high-effort
receipt records 38,948 output tokens in aggregate, 56,806 cache-created input
tokens, 356,789 cache-read input tokens and 20 ordinary input tokens. Its
wall time was 358.586 seconds. The final stream event had subtype `success`
but no `structured_output`; the process returned code 1. The final report was
correctly classified as transport-invalid. The stopped actor contained no
changes to any of its four permitted source files, and its executable grade
passed two of eight cases. Removing the report penalty alone would not make
this patch competitive with either B0 repetition.

The same schema produced valid structured reports in both B0 calls, so it is
satisfiable for this task. The high-effort stream recorded root model markers
`<synthetic>` and `claude-sonnet-5`, no child model marker, and billed-model
entries for Haiku 4.5 and Sonnet 5. The generic adapter requires exactly one
root model marker, so it could not assert identity or served effort. The only
non-synthetic root marker was Sonnet 5; this does not prove which model produced
every billed token or that the requested `high` effort was served.

The WSL CLI was Claude Code 2.1.273. The evaluation adapter's
[`_receipt_extensions`](../../tools/worker_q4r_structured.py) retains the
final subtype, structured-output presence and hashes, but not the final
event's `errors`, turn count or full stderr. The common
[`WorkerAdapter.run`](../../tools/worker_adapter.py) retains a stream hash and
invalid-line count, then discards raw stdout. Its CLI command includes
`--no-session-persistence`. No raw model transcript is available in the
stopped actor; the actor contains only a short Graft MCP diagnostic log.

Anthropic's [structured-output documentation](https://code.claude.com/docs/en/agent-sdk/structured-outputs)
explicitly says a terminal `success` can lack `structured_output` and must be
treated as failure. Its [troubleshooting guide](https://code.claude.com/docs/en/agent-sdk/troubleshooting)
lists an unsatisfiable schema as one possible cause, not the only cause. The
[CLI reference](https://code.claude.com/docs/en/cli-reference) describes
`--json-schema`, and the [environment reference](https://code.claude.com/docs/en/env-vars)
states that structured-output validation permits five attempts by default.
These pages were checked on 2026-09-26. The saved Q4R receipt does not record
how many validation attempts occurred.

## Interpretation and limits

The known failure is **no validated final report and no source edit after a
long, settled call**. The available evidence does not identify why the agent
made no edit, why Claude Code produced no structured object, or whether a
validation retry, output ceiling, fallback, internal auxiliary call or other
CLI condition caused the terminal state. Aggregate output tokens do not prove
that any single request exceeded the 8,192-token per-request setting.

Two separate design gaps are visible. First, successful CLI termination is
insufficient evidence of a usable report. The Q4R adapter already fails
closed, but its compact receipt discards diagnostic fields that could classify
the failure. Second, the campaign marks a settled terminal failure as
`uncertain`, leaving cost and stopped-patch grading to manual reconciliation.
The earlier expired-login preflight also showed that authentication should be
checked before a campaign writes its first provider-call intent. None of these
gaps authorises changing the frozen Q4R score or replaying its call.

The [prospective Q4S plan](../WORKER-Q4S-PROSPECTIVE-CANDIDATE-SCREEN-2026-09-26.md)
addresses those gaps before any new paid screen.
