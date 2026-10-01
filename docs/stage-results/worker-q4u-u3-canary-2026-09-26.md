# Q4U U3: prospective worker-policy canary

Date: 2026-09-26 UTC. Status: **complete; B0 retained; no promotion**.

## Decision

The ten-episode development canary found **no quality advantage** for either
experimental routing arm. All ten episodes reached hidden score 100, passed
the public check and were accepted in one call. All six paired policy
comparisons therefore had quality delta zero. The coverage-repair arm never
had to make its conditional second call, so this run did not test its intended
rescue mechanism. Keep B0 as the shipping worker policy and stop the proposed
paid expansion under the [predeclared spend notice](worker-q4u-u3-canary-spend-notice-2026-09-26.md).
The four reserved mechanisms R09-R12 remain untouched. This canary has no
qualification or promotion authority.

## Frozen evidence and accounting

The [manifest](../../test/results/2026-09-26-worker-q4u-u3-canary-manifest.json)
was frozen before provider outcomes at SHA-256
`33e0cb0d85a04071ead319cce24385b4bdcb7df8b77de33d6e5f6fdc881838be`.
It bound source, task, public assessment, sealed evaluator, Claude Code CLI,
WSL launcher, structured-report schema, schedule and limits. The dated,
manifest-bound standing approval permitted at most 30 Claude Code subscription
calls and USD 40 in local allocation. The provider-free WSL source, auth and
integration probes passed before the first persisted call intent.

The [campaign journal](../../test/results/2026-09-26-worker-q4u-u3-canary-run/campaign.json)
and [paired analysis](../../test/results/2026-09-26-worker-q4u-u3-canary-run/analysis.json)
record **10 settled episodes, 10 calls and USD 1.022577203 API-equivalent
usage**. No call replay, uncertainty stop, protected-source drift, missing
structured report, false success or critical error was observed. The actual
incremental Claude.ai subscription invoice impact is unknown and is separate
from this API-equivalent usage figure. The development session's own API cost
is also not measured by this campaign.

| Arm | Episodes | Hidden scores | Calls | API-equivalent USD |
| :--- | ---: | :--- | ---: | ---: |
| B0 | 4 | 100, 100, 100, 100 | 4 | 0.351739202 |
| Cross-component medium | 2 | 100, 100 | 2 | 0.297827001 |
| Coverage repair | 4 | 100, 100, 100, 100 | 4 | 0.373011 |

The arm totals above are grouped by the frozen schedule; the journal is the
source of truth for exact per-episode charges. Pair cost and latency deltas
vary by task, but no arm improved the hidden score. An independent provider-free
audit re-ran all ten sealed hidden graders, rechecked each episode's source,
identity and settlement, and recomputed the paired analysis; all matched the
retained records. The 40 focused Q4U tests and WSL fake-worker probe passed.
The redistributable build passed its full offline harness before the paid run.
The worker calls requested `worker-sonnet-low` or `worker-sonnet-medium` and
reported served model `claude-sonnet-5` with identity validation true. No Opus
fallback was invoked. The requested effort came from the CLI cell arguments;
served reasoning effort is not independently attested. The host does not expose
this Codex development session's actual model and effort for verification.

## Interpretation and next gate

These four mechanisms produced a quality ceiling for every arm; they do not
show that either policy is broadly safe or useless. The conditional repair
path is tested offline but has no live treatment observation here. Larger
reserved comparison would spend more without a development signal, and the
four reserved mechanisms are too few for the predeclared uplift claim anyway.
Do not expose the candidate as an automatic default. Preserve the frozen
receipts for the worker N7 review, then complete N8 packaging with B0 unless
an independent review finds a concrete reason to reopen worker selection.
Controller stages X0-X8 remain separate and unstarted; X0 must use this actual
worker result rather than assuming an improved worker policy.

Graft's structural rebuild completed after U3 source changes. Its deep
semantic refresh remained partial: three files returned unparseable symbol
summaries (`worker_q4s_structured.py`, `worker_q4u_executor.py`, and
`task_executor.py`). The same paid request should not be repeated unchanged.
This semantic limitation does not affect the sealed canary grading.

The subsequent N7 review found additional limits that reinforce this
non-promotion decision. The canary manifest omitted directly imported local
runtime modules, and the D01 in-process hidden grader can be made to report a
false score of 100 from a disposable allowed actor edit. A sampled paid D01
output made a substantive repair and all recorded cases passed, but the scorer is not
adversarially sound. See the [N7 review](worker-n7-2026-09-26.md) and its
provider-free probes. The frozen paid manifest and receipts were not changed.
