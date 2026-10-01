# N5 task-sensitive development comparison

Status, 2026-09-25: the new corpus, experimental dispatch and approved live
development campaign are complete. The [N5 result](stage-results/worker-n5.md)
records all 36 reconciled episodes, their hidden grades and the selection
decision. The shipping B0 ladder remains unchanged. The earlier
[preflight result](stage-results/worker-n5-development-preflight-2026-09-25.md)
records the checks before the paid campaign.

The [completed 15-cell screen](stage-results/worker-n5-screen-2026-09-25.md)
used three tiny mechanics tasks per cell. The older N4 corpus also gave every
task a `moderate` assessment, so it could not test a selector whose prior
depends on task complexity. N5 therefore freezes a separate, fully synthetic
[24-task corpus](../test/fixtures/worker_n5_realworld/catalogue.json), generated
by [worker_n5_corpus.py](../tools/worker_n5_corpus.py). Twelve D tasks are
development data; twelve R tasks are sealed for N6. Each split has four
routine, four moderate and four complex tasks, and two distinct mechanisms
within each of six families: configuration, resilience, integrity,
concurrency, protocol and diagnosis. All have executable behavioural
contracts, two public examples and three hidden cases. The hidden oracles are
outside the actor directories. A reference implementation passes all 24
oracles; a public-example lookup fails every task's hidden checks.

These are synthetic service behaviours, not a sample of open-source issues.
Each is a bounded single-file Python edit because the attested WSL host permits
only `app.py` writes. They improve variation in task kind, algorithmic state,
failure modes and assessed complexity, but do not measure cross-repository
integration, large-context retrieval or human maintainability. A later
multi-file corpus needs a separately attested actor boundary.

The [planner](../tools/worker_n5_development.py) predeclares 12 D tasks by
three arms, balanced in within-task order. Every arm receives the same public
files, neutral worker prompt, acceptance contract and USD 3 root allocation:

| Complexity | B0 first cell | Candidate first cell | Alternative first cell |
| :--- | :--- | :--- | :--- |
| Routine | Sonnet low | Sonnet low | Sonnet medium |
| Moderate | Sonnet low | Sonnet high | Sonnet xhigh |
| Complex | Sonnet low | Opus high | Fable high |

Each ladder allows one same-cell repair followed by Opus high, subject to the
single root allocation. B0 retains its qualified default path. Candidate and
alternative require an exact manifest-bound experimental admission, and the
resolved assessment, selection, eligible cells, policy digest, ladder and cost
ceiling are frozen into each root and attempt decision. Fable 5.1's served
identity was observed in the screen. N5's host capability binds that screen
observation without rewriting the shared registry, which is bound into older
frozen campaigns. Its per-run cost projection remains unknown. The alternative
arm therefore uses an explicit USD 3 ceiling rather than asserting a price
estimate.

The [live driver](../tools/worker_n5_live_development.py) reserves campaign
and root budget before each worker side effect, persists intent, refuses
automatic replay of uncertain work, runs public acceptance in a credential-free
WSL copy, and grades the stopped actor with a separate hidden oracle. It
records acceptance, partial quality, critical errors and false success even
when a root does not achieve complete acceptance. Restart validation checks
the frozen row, root goal and inputs, budget inventory and settled charges.
Only D tasks are scheduled; R actor files and grades never enter N5 workers.

The frozen campaign has at most 36 episodes and USD 108 in local admission
allocations. This is neither a bill forecast nor a provider-side hard cap.
Before live execution, the full offline harness and distribution build passed;
the WSL and subscription attestations, fresh credential sentinel, dated spend
notice and exact manifest approval were recorded. A changed corpus, source,
host or notice creates a new digest. Development evidence may tune a small
rule table, but must not change the shipping default or inspect R grades.

The completed campaign used 50 Claude Code calls across the 36 episodes. All
budget allocations settled; the provider reported USD 3.36177041 in
API-equivalent usage. B0 passed 11/12 hidden task oracles, while candidate and
alternative passed 12/12 each. Routine B0 and candidate start in the same
Sonnet-low cell, so the observed routine difference cannot establish a routing
benefit. All three arms passed the moderate and complex tasks; stronger first
cells increased cost there. This synthetic corpus does not qualify a new
default or establish real-world readiness. The 12 R tasks remain sealed for N6.

Focused provider-free checks:

```text
python tools/worker_n5_corpus.py --check
python test/harness/worker_n5_corpus_tests.py
python test/harness/worker_experimental_dispatch_tests.py
python test/harness/worker_n5_development_tests.py
```
