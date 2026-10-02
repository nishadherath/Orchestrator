# Development model allocation: Astra versus Sol 6.1

**Historical rationale, not current selection authority.** Current task rules,
stage settings and escalation policy live only in
[development model calibration](DEVELOPMENT-MODEL-CALIBRATION.md). The decisions
and estimates below record the 2026-10-02 review and must not be used to override
a later calibration revision.

Date: 2026-10-02. Scope: development sessions for the offline qualification
package, including its design and independent review. This does not alter
Anthropic worker routing or establish Controller uplift.

## Decision

Use GPT-6.1 Sol High for O0 and a fresh GPT-6.1 Sol Extra high review session
for O5. Retain the Luna assignments for O2/O3/O6 and Sol for O1/O4. No offline
stage requires Astra by default. Keep Astra as a targeted escalation when
observable reasoning or review failures justify it. Manual handovers and all
qualification requirements remain in force.

This replaces a conservative allocation based on stage importance with one
based on the actual uncertainty and available verification. It does not claim
that Sol equals Astra on every task, or that either model has passed this
project's new qualification work. No comparative model runs were performed.

## What the evidence establishes

| Dimension | Current evidence | Limit of the conclusion |
| :--- | :--- | :--- |
| Complex coding and agent work | Official Codex guidance recommends Sol 6.1 when available and describes its performance as close to Astra's | Vendor guidance supports a default; it is not a measured success rate for O0 or O5 |
| Hardest reasoning | Astra remains the vendor's highest-capability offering | Importance or difficulty labels alone do not show its extra capability is needed for a specific stage |
| Context and output capacity | Both list a 1,050,000-token context and 128,000-token output limit | Equal capacity does not imply equal use of context or equal reasoning quality |
| Tools | Both support function calling, structured outputs and image input through their documented interfaces | Tool availability is not tool-use reliability; host exposure still governs this session |
| Effort | Both support High and Extra high | Equal effort labels do not imply equal compute, latency or capability across models |
| Cost | Standard Astra rates exceed Sol rates by 5x for ordinary input, cache writes and output, and 10x for cache reads | Per-token prices do not measure total cost per successful task |
| Latency and success rates | The reviewed official pages do not provide a controlled numerical comparison for our design/review workload | No defensible percentage quality gap, speed ratio or expected rework rate can be assigned |

Sources: [Codex model guidance](https://learn.chatgpt.com/docs/models),
[GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model),
[Sol 6.1 model specification](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
and [side-by-side model specifications](https://developers.openai.com/api/docs/models/compare).
These sources were searched and opened on the date above. Descriptions such as
performance close to Astra's are vendor claims, not independently measured
results from this repository. No relevant numerical head-to-head benchmark was
found in the reviewed sources. That is not a claim that none exists anywhere.

The GPT-6 guide notes that Astra sometimes used fewer output tokens and had
lower task costs than earlier models. That observation cannot establish its
cost advantage over Sol 6.1: the comparison model, effort, workload and total
accounting must match. Similarly, Sol's lower token price cannot establish that
it finishes this work faster or with fewer defects.

## Why O0 can start with Sol High

O0 is substantive design work, but its problem has already been reduced by the
post-RC analysis. The known failures, desired two-branch admission, shared
feedback, canonical accounting, scoped identity and immutable history are
specified. Existing execution and registry mechanisms can be inspected. The
task is to resolve and express these boundaries in an executable contract,
not to discover a new general orchestration architecture.

Sol High is therefore a reasonable starting point. Require a requirement-to-
state/test map, concrete negative controls and explicit unresolved decisions.
The exit gate must reject vague promises such as secure isolation without a
host-specific test. If the design expands to a new isolation mechanism or an
unresolved trust model, evaluate that particular problem for escalation rather
than silently expanding O0.

The risk is that Sol misses an assumption which its own tests then preserve.
Reduce it with original failure reproductions, counterexamples and the separate
O5 review. Choosing Astra at the start would not remove this risk or replace
those checks. There is no observed Sol failure that currently requires Astra.

## Why O5 can start with Sol Extra high

Independent review describes the process and evidence, not the model name.
A fresh Sol reviewer can work from the original requirements, historical
failure evidence and frozen candidate without inheriting the implementation
discussion. First derive expected failure conditions, then inspect the code,
tests and result artefacts. Require reproducers for findings and independently
derived tests for the highest-consequence boundaries.

Extra high is a proposed allowance for the connected trust, accounting and
recovery analysis. It has not been benchmarked against High here and must not
be described as equivalent to Astra. Review independence also requires separate
authorship responsibility and rechecking fixes. A same-context second pass is
self-review regardless of the selected model.

Using the same model for authoring and review may leave correlated blind spots.
Astra may contribute a different diagnosis or notice a missed assumption, but
model switching alone does not guarantee error independence. The appropriate
first control is an independent test derivation anchored in the requirements.
Use a targeted Astra challenge when review exposes an unresolved contradiction
or fails to substantiate a critical boundary. A broad automatic second review
would spend money without a specified question or acceptance condition.

## Escalation policy

The following evidence justifies considering an Astra High or Extra high
handoff, scoped to the unresolved question:

- Two distinct, evidence-based diagnostic hypotheses fail to explain a
  correctness or isolation problem after reproductions are available.
- Design and review disagree about a critical trust, scoring, charge or replay
  invariant and a concrete test does not resolve the disagreement.
- The reviewer cannot demonstrate a required boundary, or an independently
  supplied counterexample reveals a critical omission in its reasoning.
- Work necessarily introduces a new architecture, threat model or statistical
  claim beyond the frozen contract and current verification can no longer
  settle correctness.

First distinguish missing evidence or host capability from reasoning difficulty.
No larger model can manufacture provider telemetry, grant filesystem isolation,
decide an operator's business preference or turn a flawed oracle into evidence.
Those conditions need data, engineering or an operator decision. Increasing
effort is not their remedy.

Keep an escalation record: question, attempted explanations, observed failure,
files, acceptance criterion, target setting and refreshed cost/time projection.
Use the normal validated handoff and manual selection. No automatic launch is
authorised by this document. Return to the ordinary stage owner after resolution;
an Astra escalation does not promote the whole programme to Astra.

## Economics and what to measure

Official Standard short-context rates per million tokens are Astra USD
10/1/12.5/50 and Sol USD 2/0.1/2.5/10 for ordinary input/cache reads/cache
writes/output respectively. At equal billed token quantities and processing
tier, Sol is 80% cheaper for the first, third and fourth categories, and 90%
cheaper for cache reads. These are arithmetic comparisons of published rates.
They are not observed savings or desktop subscription billing.
[Pricing source](https://developers.openai.com/api/docs/models/compare).

Using the stage plan's unchanged token assumptions, a Sol stage costs USD
0.47-1.65 at Standard versus Astra USD 2.45-8.75. Substituting Sol for the two
Astra stages gives four Sol and three Luna stages: approximately USD 1.95-6.86
before retries. The preceding allocation was USD 5.91-21.06. That is about a
67% reduction in this illustrative base estimate, driven by unchanged token
assumptions. Up to 25% retry overhead with Fast pricing raises the new upper
estimate to USD 17.16; the no-cache upper sensitivity case is about USD 42.02.
Extra reviews, escalation, long requests and different token usage require a
new estimate. The existing time allowances remain unchanged and unmeasured.

In a simplified uncached-input/output-only comparison, Astra must use less than
one fifth of Sol's billed tokens to break even on token charges alone. Mixed
cache usage, tool fees, human review, defect severity and rework change that
calculation. One avoided serious defect can outweigh a small API difference;
we should pay for a demonstrated need rather than use the price ratio as the
sole quality decision.

Record observed stage completion, substantive defects found, review/repair
cycles, elapsed time and available usage. Ordinary stage work is the first
source of evidence. Do not launch an additional paid benchmark merely to make
this allocation decision. Keep the smallest setting that meets the unchanged
acceptance bar, and escalate on specific failure evidence.

## Result and next action

The [stage plan](OFFLINE-QUALIFICATION-IMPLEMENTATION-PLAN-2026-10-02.md),
[session controls](DEVELOPMENT-SESSION-CONTROLS-2026-10-02.md) and
[O0 handoff](../handoffs/2026-10-02-offline-qualification-o0.md) now use Sol High
for the next stage. Later study design and confirmation also start with Sol at
the documented effort, with Astra reserved for unresolved difficult questions.
No current session was switched, no agent launched and no experiment executed.
