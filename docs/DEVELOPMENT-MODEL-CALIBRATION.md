# Development model and effort calibration

**Authority:** single source of truth for development-task model and effort
selection in this project. **Revision:** DMC-1. **Reviewed:** 2026-10-02,
Australia/Sydney. **Status:** operator-accepted selection policy informed by
official guidance and task analysis; comparative project performance is unmeasured.

## 1. Read this before assigning work

Consult this file before recommending a development model, assigning a stage,
preparing a model/effort handoff or launching an authorised development agent.
Use the current rows below rather than reconstructing the decision from old
chats, dated reviews, persona class names or general flagship recommendations.

This file owns the selection policy, current model identifiers, effort defaults,
stage assignments, escalation rules and calibration status. Plans own task
scope and acceptance gates. Handoffs contain dated resolved selections for one
transition, with this revision and row ID; they are not another calibration
table. Dated analyses remain evidence and do not override the current rows.

Explicit operator instructions take precedence. If an old plan or pending
handoff disagrees with this file without an explicit operator override, resolve
and update that pending handoff before use. Preserve historical executed
handoffs and receipts. Do not silently change a setting the operator explicitly
selected; explain any proposed change and follow the normal handover protocol.

This is development-session calibration for the exposed Codex host. It is
separate from [the Anthropic worker registry](../src/model_registry.json),
which remains the sole source for current Anthropic provider model mappings.
Do not add OpenAI development choices to that registry, infer Claude-equivalent
classes, or change shipping B0/Controller behaviour from this document.

## 2. Model identities and evidence status

| Development name | Host model identifier | Role in this calibration |
| :--- | :--- | :--- |
| GPT-6 Luna | `gpt-6-luna` | First choice for bounded work with explicit expected outcomes |
| GPT-6.1 Sol | `gpt-6.1-sol` | First choice for design, complex implementation, integration and review |
| GPT-6 Astra | `gpt-6-astra` | Targeted escalation for a demonstrated unresolved reasoning problem |

Effort names used here map to `medium`, `high` and `xhigh` for Medium, High and
Extra high. The host exposed these combinations when reviewed. Availability
must be checked at the actual transition; exposure is not successful execution
or provider-side effort telemetry. Do not silently replace Sol 6.1 with Sol 6
or another generation. An unavailable calibrated model requires a documented
alternative assessment and, where needed, operator selection.

The evidence has four distinct levels:

- **Observed host capability:** the available control schemas accept these
  model/effort combinations. No launch was performed to prove access.
- **External guidance:** OpenAI positions Luna for focused work and Sol 6.1
  for complex coding and agent workflows with performance close to Astra's.
  These are provider descriptions, not this project's measured results.
- **Accepted engineering judgement:** the operator accepted the Luna-first and
  Sol-first revisions on 2026-10-02 and requested this durable source of truth.
- **Unmeasured:** no controlled Luna/Sol/Astra comparison, stage completion
  rate, latency ratio, reasoning-effort comparison or realised cost saving has
  been established by this calibration work.

## 3. Task selection rules

| Row | Work characteristics | Default selection | Conditions |
| :--- | :--- | :--- | :--- |
| C1 | Assemble evidence, format reports, make straightforward documentation changes or execute a prescribed check | Luna / Medium | Decisions and expected output are already fixed; report ambiguity instead of inventing a conclusion |
| C2 | Implement a bounded module, schema, validator, fixture or deterministic decision table | Luna / High | Frozen interface, named dependencies, explicit negative controls and reviewable output |
| C3 | Resolve contracts, design within an established architecture, implement interacting mechanisms or diagnose substantive defects | Sol 6.1 / High | Scope is defined but judgement is needed across requirements and code |
| C4 | Integrate interacting state machines, investigate difficult recovery/accounting behaviour, or conduct independent adversarial review | Sol 6.1 / Extra high | Extra reasoning is justified by connected invariants; independent review also requires a fresh context and separate responsibility |
| C5 | Resolve one difficult question after concrete lower-cost reasoning/review failures | Astra / High | An escalation trigger in section 5 is met and the handoff identifies the unresolved question |
| C6 | Sustained adversarial or architectural reasoning remains unresolved and warrants additional deliberation | Astra / Extra high | Explain why C5 or the preceding investigation is insufficient; no automatic whole-programme upgrade |

Use the smallest applicable row that can meet the unchanged acceptance bar.
Task importance, a large repository, the words architecture or security, and
the presence of a final review do not automatically select Astra. Test-running
time alone does not justify a stronger model. Increasing effort is not a
substitute for a missing specification, unavailable tool or absent evidence.

Max and Ultra have no default assignment. Do not create a new default because
the host exposes a setting. Low is also not needed by the currently agreed
stage plan; future use should be justified by the task and recorded here rather
than inferred from a generic recommendation. Effort labels are not equivalent
compute or quality guarantees across models.

## 4. Current offline qualification assignments

These rows are the authoritative assignments for the
[implementation plan](OFFLINE-QUALIFICATION-IMPLEMENTATION-PLAN-2026-10-02.md).
The plan controls deliverables and gates; it refers here for model selection.

| Stage row | Calibration row | Selection | Why this is sufficient to try first |
| :--- | :--- | :--- | :--- |
| O0 | C3 | Sol 6.1 / High | Known failure analysis and existing mechanisms bound the contract-design problem |
| O1 | C3 | Sol 6.1 / High | Evaluator attribution and OS isolation interact; simple fixture work can be separated later |
| O2 | C2 | Luna / High | Canonical accounting, admission and packet rules become deterministic after O0 |
| O3 | C2 | Luna / High | Identity validation is bounded once provenance, freshness and trust rules are frozen |
| O4 | C4 | Sol 6.1 / Extra high | Combined recovery, source binding and accounting need cross-module reasoning |
| O5 | C4 | Sol 6.1 / Extra high, fresh reviewer | Derive counterexamples independently from original requirements and inspect the integrated candidate |
| O6 | C1 | Luna / Medium | Assemble reviewed evidence and decisions; unresolved design/readiness judgements return to their owner |

No stage requires Astra by default. O2/O3 may escalate to C3 when the triggers
below occur. An unfinished O0 contract does not pass simply because Luna or
Sol could attempt to guess the missing design. Start each bounded implementation
with one vertical slice and a meaningful negative control, inspect the result,
then extend it. Preserve all integration and independent-review gates.

Optional parallel work remains O1/O2/O3 after O0 passes, with disjoint ownership,
followed by sequential O4 and O5. Model calibration is not permission to spawn.
Use [session controls](DEVELOPMENT-SESSION-CONTROLS-2026-10-02.md) for launch
capabilities and authorisation, and the project handoff contract for transitions.
No benchmark, paid pilot, agent or new chat is authorised by this file.

Future live-feasibility execution, experimental design and consumer integration
start with C3 when their work characteristics match. Difficult confirmation
analysis and independent promotion review start with C4. Those future stages
remain conditional and require their own task and spending gates; this is not
an instruction to start them.

## 5. Escalation, review and return to a smaller setting

Distinguish a reasoning problem from a missing prerequisite first. Missing
telemetry, permissions, account access, host isolation or an operator's business
decision requires direct resolution. A larger model cannot supply those facts.

Consider C2 to C3 when the bounded task reveals an unresolved contract choice,
cross-module scope expansion, two failed evidence-based diagnostic hypotheses,
or a reviewed semantic defect showing the contract was misunderstood. Return
missing design choices to O0 and new experimental/readiness judgements to the
appropriate design/review owner. Do not loosen acceptance to keep the smaller
model assigned.

Consider C3/C4 to C5/C6 for a specific unresolved question when:

1. Two distinct diagnostic hypotheses fail despite usable reproductions.
2. Design and review disagree over a critical trust, scoring, charge or replay
   invariant and concrete tests do not resolve the disagreement.
3. An independent counterexample reveals a critical reasoning omission or the
   reviewer cannot substantiate a required boundary.
4. Necessary work introduces a novel architecture, threat model or statistical
   claim beyond the frozen scope and existing verification cannot settle it.

Record the question, evidence, attempted explanations, scope and acceptance test
before escalating. Produce and validate the handoff with refreshed cost/time
assumptions. An escalation applies to the question, not automatically to the
rest of the programme. Return to its ordinary owner when the question is closed.

A fresh reviewer using the same model can provide a separate review process,
but correlated model blind spots remain possible. Require independent test
derivation and inspect raw artefacts. A different model is not proof of
independence, and a stronger model is not permission to skip verification.
Do not use the same implementation context to claim independent approval of
its own changes. The O5 contract governs finding closure and rechecking fixes.

Retain or reduce the setting when required outcomes pass without excessive
review/rework. Do not force a switch within an active stage solely to save a
small estimated amount. The operator's stage handovers remain the default.

## 6. Rationale to preserve

The initial plan assigned all substantive implementation to Sol and design/
review to Astra. It lacked evidence that Luna could not handle frozen-rule
implementation, so O2/O3/O6 were reassigned to Luna. Further review found no
demonstrated need for Astra in O0/O5: their boundaries and verification were
sufficiently defined to try Sol first. Avoid repeating the initial mistake of
treating consequential work as a reason to select the largest model by default.

Sol's documented performance is close to Astra's for complex work, with lower
token rates. The reviewed sources did not establish a numerical quality or
latency gap on our tasks. Equal context limits and tool support do not establish
equal reasoning quality. These observations support a cost-conscious starting
policy with escalation, not a guarantee of equivalence.

Historical price arithmetic and token assumptions are in the
[dated allocation review](MODEL-ALLOCATION-REVIEW-2026-10-02.md). Treat those as
dated estimates and refresh actual provider/tier prices when projecting a new
session. Do not equate token-price ratios with cost per successful task or
desktop billing. Review, repair and failure costs can outweigh cheaper tokens.
No paid model-comparison campaign is needed merely to use this initial policy.

## 7. Maintaining this source of truth

Update this file when new evidence changes a row. Increase the revision,
record date and reason, and link the evidence. Keep rationale and observations
separate. A single successful task can support that bounded assignment; it
does not establish general model superiority. New vendor releases, changed
host controls, repeated task failures or a material shift in task scope are
reassessment triggers. Do not silently substitute a newer alias, and do not
reopen settled calibration on every turn without changed evidence.

For each assignment record in its handoff or result:

| Field | Required content |
| :--- | :--- |
| Calibration | Path, revision and task/stage row, or explicit operator override |
| Task and setting | Scope, requested model/effort, and separately observed host acceptance when available |
| Evidence | Source revision, acceptance checks and links to results |
| Outcome | Pass/fail/inconclusive, substantive review findings and repair cycles |
| Cost and time | Available usage and elapsed time; estimates labelled; unknown is not zero |
| Disposition | Keep assignment, targeted escalation or proposed calibration update |

Keep raw evidence in stage results, not copied into the standing rule. Plans
link to rows instead of maintaining parallel model tables. A handoff must still
spell out the exact target because it is an executable transition brief; mark
it as a snapshot and compare its revision/row before use. A discrepancy is
resolved before launch, not ignored because the old handoff passes syntax checks.

## 8. Sources and revision record

Official guidance reviewed on 2026-10-02:

- [Model selection](https://developers.openai.com/api/docs/guides/model-selection).
- [Codex models](https://learn.chatgpt.com/docs/models).
- [Sol 6.1 specification](https://developers.openai.com/api/docs/models/gpt-6.1-sol).
- [Luna specification](https://developers.openai.com/api/docs/models/gpt-6-luna).
- [Astra and Sol comparison](https://developers.openai.com/api/docs/models/compare).

| Revision | Date | Basis and change | Measurement status |
| :--- | :--- | :--- | :--- |
| DMC-1 | 2026-10-02 | Consolidates operator-accepted Luna-first and Sol-first assignments, with Astra as targeted escalation | Documentary and task-scope calibration only; no controlled project comparison or launch |

The dated review explains the reasoning at that time. This file alone owns
current selection calibration. Root project instructions require consultation
so a resumed session can recover the decision without conversation history.
