# Q3 public B0 canary: two independent families

Date: 2026-09-25 UTC. Status: **two-task diagnostic canary complete; the
eight-family Q3 admission gate is not complete**. The shipped B0 route and the
sealed N6 R material were not changed or run.

## Bound run and measured outcome

The operator's standing approval through Q4 covered the [one-call Read-denial
sentinel notice](worker-q3-sentinel-spend-notice-2026-09-25.md) and the
[two-task canary notice](worker-q3-canary-spend-notice-2026-09-25.md). Their
exact approval records and manifests are in `test/results/`. The sentinel
passed on the isolated WSL Claude Code subscription host: its attempted read
was denied, the actor remained unchanged, the served model was
`claude-sonnet-5`, and the reported API-equivalent usage cost was **USD
0.0530436**. The provider did not report a separately verifiable served
effort level.

The canary manifest digest was
`ecdb71d90de67fbdef559d9e815c13935236bf446f378ddb98edb3867f9fd3b7`.
It fixed the P01 cachetools and P02 ItsDangerous actor and oracle digests,
P01-before-P02 order, B0 ladder, WSL evidence, timeout/no-replay probe,
six-call ceiling and USD 6 local allocation per episode. The dated notice
projected USD 0.1-6 API-equivalent usage and 0.5-2 hours. No candidate route,
Controller, reference overlay or reserved task ran.

| Public task | B0 result | Hidden grade | Sonnet-low calls | Reported API-equivalent USD | Sum of provider call times |
| :--- | :--- | :--- | ---: | ---: | ---: |
| P01 cachetools | accepted on first attempt | accepted, 100/100 | 1 | 0.0850796 | 29.405 s |
| P02 ItsDangerous | first public check failed; accepted after one local repair | accepted, 100/100 | 2 | 0.355438002 | 164.622 s |
| **Total** | 2/2 accepted | no critical error or false success | **3** | **0.440517602** | **194.027 s** |

The campaign checkpoint was created at 09:14:49 UTC and completed by its
09:20:40 UTC file timestamp. An [exact reader-accessible copy](../../test/results/2026-09-25-worker-q3-canary-evidence.json)
has SHA-256
`bb10427bb003977db02c02e327d1e496fb8bbf2e17edb081c7f47ad5f95f4c0f`;
the original one-shot run directory remains private. Every attempt had a terminal event, stopped
writer, expected `claude-sonnet-5` identity and valid Q1 stop/collect hashes.
All three calls requested low effort; **served effort remained unreported**.
No Opus call was needed. The USD figures are Claude Code's reported API
equivalent, **not** a measured subscription invoice. Including the separate
sentinel, reported API-equivalent usage was USD **0.493561202** across four
calls. The local canary allocation was USD 12; it was an admission reserve,
not provider billing.

## Independent patch and grader review

I compared each stopped actor's two editable files with the frozen starting
source. P01 added a cache `Condition()` to prevent simultaneous cold-key
computation and included the value types of sorted keyword arguments in the
typed key. P02 restored decompression for the compressed-token marker and
rejected negative signed-token age. No other source path changed according
to the Q1 collection records. These edits address the reported mechanisms;
the hidden checks also passed ordinary eviction, alternate key shapes, small
payloads, expiry and tamper cases. This review does not prove correctness for
all inputs outside the frozen tests.

P01's timer-sensitive grader was repeated **ten times on the unchanged
baseline and ten times on the stopped candidate**, with zero provider calls.
The baseline failed public and hidden acceptance at 10/100 in all ten runs;
the candidate passed both at 100/100 in all ten. The actor-file inventory
was unchanged. The [digest-bound repeat record](../../test/results/2026-09-25-worker-q3-stability.json)
contains each case result and the campaign and grader source hashes. Ten
stable repetitions constrain observed local flakiness; they cannot prove a
zero flake rate on other hosts or loads.

## Decision and next gate

This run validates the bounded paid adapter, accounting and two public
graders on this host. It does **not** validate task-sensitive routing. Both
tasks reached 100/100 under B0, leaving no final-quality or acceptance room
for a stronger first cell in this sample. P02's repair shows a first-attempt
failure but does not establish that a different cell would improve the final
quality at a worthwhile premium. Running a candidate screen on these two
tasks is therefore a poor use of paid calls.

The original Q0 ceiling/floor rule needs **eight independent public families**;
these two cannot be repeated or counted as eight. The next authorised work is
to [prospectively inventory](../WORKER-Q3-EXPANSION-INVENTORY-2026-09-25.md)
and build six additional, distinct public tasks
with more diagnosis uncertainty and coordinated edits, validate their source
licences and offline grading, then freeze a separate six-task B0 manifest and
spend notice. Only after that public gate can Q4 freeze a reserved corpus and
candidate policy. P01 and P02 remain public calibration units and are excluded
from reserved inference.

Reproduction: `python3 tools/worker_q3_canary.py --check --spend-notice
docs/stage-results/worker-q3-canary-spend-notice-2026-09-25.md` validates the
frozen material while its host evidence is current. The completed one-shot
campaign is at `test/results/2026-09-25-worker-q3-canary-run/campaign.json`;
**do not rerun** `tools/worker_q3_live.py --run`. The provider-free stability
command is `wsl.exe -d kali-linux -u root -- python3 -B
/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator/tools/worker_q3_stability.py
--repeats 10`. It passed with stable baseline/candidate and unchanged actor.
`python3 test/harness/check.py` passed **66/66** offline checks after the
canary and stability script; `git diff --check` was clean. This harness does
not replace the live receipt and independent patch review above.
