# Q2 public material and prospective task sampling

Later status: the [Q3 eight-family public B0 gate](stage-results/worker-q3-public-2026-09-25.md)
completed with six additional upstream families. The Q3 admission amendment
below is retained as the original decision record.

The [Q4 measurement and freeze contract](WORKER-Q4-MEASUREMENT-AND-FREEZE-2026-09-25.md)
now specifies the implementation sequence after the Q3 contract audit. This
document's independent-family sampling and source limits still apply.

Date: 2026-09-25. Status at proposal: **Q2 provider-free calibration complete; Q3 is a
separate paid gate**. This specifies how public development tasks and future
reserved task units are selected under the [Q0 protocol](WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md).
It does not change B0, the sealed N6 R set or the worker execution contract.

## Public material and what it proves

The two [frozen public tasks](../test/fixtures/worker_q2_public/catalogue.json)
are authored regressions on complete, pinned, permissively licensed upstream
Python packages. They are **not** upstream issues or independent held-out
evidence. The source and licence bytes were compared with the pinned commits
before freezing the catalogue. Each package has an issue, a protected public
check, a two-file edit contract, a clean reference and a partial variant. The
[hidden oracles](../test/oracles/worker_q2_public/) remain outside the actor.

| Task | Pinned source | Clean Python source | Mechanism | Licence |
| :--- | :--- | ---: | :--- | :--- |
| P01 | [cachetools](https://github.com/tkem/cachetools), `3c082c654c2804b9354e4b62dbd2994f1aac464d` | 1,647 lines | Concurrent cold-key computation and typed keyword keys | MIT, included `LICENSE` |
| P02 | [ItsDangerous](https://github.com/pallets/itsdangerous), `672971d66a2ef9f85151e53283113f33d642dabd` | 1,176 lines | Signed-token clock boundary and compressed payload decoding | BSD-3-Clause, included `LICENSE.txt` |

Both use Python 3.10+ and the standard library for their isolated checks; no
service, secret or network is needed during grading. Their reference and
partial variants are calibration material visible to developers and must
never be sent to a candidate or counted as distinct task units. The existing
historical D/H fixture codebases are about 13-90 Python lines, below Q0's
1,000-line lower bound. They may test transport or graders, but cannot count
as target-stratum pilot or reserved tasks.

The [Q2 result](stage-results/worker-q2.md) records six isolated grades:
baseline, partial and reference for each project. It shows that the grader
detects useful incomplete progress and that its two reference patches pass.
It says nothing yet about B0 difficulty, a router benefit or a population
effect. Timer-based concurrency checks need repeated public calibration to
measure flakiness before they support any paid comparison.

## Prospective source and issue frame for Q4

The independent sampling unit is one project family and one issue. Eligible
units must satisfy all of these public properties before a model response is
seen:

1. A pinned source commit or independently authored synthetic repository with
   1,000-20,000 clean Python source lines, an included redistributable licence
   (MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause or individually reviewed
   equivalent) and an exact source-file hash inventory.
2. A deterministic local Python 3.10+ setup, frozen dependencies or standard
   library only, no live service, external secret or grading-time network, and
   a Q1-compatible package of no more than 200 files/5 MB with 2-8 existing
   editable source files. Any proposed expansion of Q1 limits is a separate
   boundary stage.
3. An issue whose public trigger requires coordinated edits or diagnosis of
   state, recovery, protocol, concurrency or conflicting evidence. Record
   whether the issue is upstream, authored on upstream source or synthetic;
   never relabel an authored regression as an upstream report.
4. Public issue, acceptance contract and tests that a worker may see; a
   separate root-owned hidden oracle, checked clean reference, materially
   different correct variant where feasible, partial variant and attack
   variants. The grader must credit truthful diagnosis and partial progress
   while flagging false completion and critical errors separately.

Before Q4 grading, publish a candidate inventory with repository URL, exact
commit, licence, source-line count, dependencies, issue origin, mechanism,
package size, eligibility decision and reason for every exclusion. Canonicalise
URL and commit, sort eligible families by SHA-256 of
`worker-q2-2026-09-25|canonical-url|commit`, and take the first eligible family
in each predeclared mechanism quota. Define the quotas, task count, and fixed
replacement order **before** seeing any reserved outcomes. A failed setup or
invalid licence permits only the next item in that frozen order; preserve the
excluded unit and reason. A new issue from the same source family is a
replacement only if the entire family was excluded. Repeated runs, sibling
issues, variants and template copies never increase the independent task count.

The proposed diversity targets within Q0's **single primary stratum** are
cross-module contract, state/recovery, concurrency/protocol, and
diagnosis-versus-evidence mechanisms. They are coverage cells, not four
separate confirmatory claims. Q4 must set their exact quotas and recalculate
power and total cost before freezing a reserved sample. No N5, N6, R, P01 or
P02 source family can enter that sample. No hidden result, reference patch,
family label or task ID may reach the router. The actor receives only the
issue and allowed package; the root grader runs after the actor stops, outside
its filesystem and Graft index. All exclusions and abstentions remain in the
intent-to-route record.

## Q3 admission amendment to review

The [Q0 Q3 gate](WORKER-QUALIFICATION-PROTOCOL-Q0-2026-09-25.md) specifies
eight B0 episodes on public task units, with acceptance ceiling/floor
thresholds of more than six and fewer than two. Only **two** eligible public
families exist after Q2. Repeating either task or using its partial/reference
variant cannot manufacture six more independent units. The eight-task gate
therefore cannot run as written yet.

The least-cost next option is a separately authorised **two-task B0 canary**
on P01 and P02, with an exact manifest, dated spend ceiling, provider identity
and effort evidence, and no candidate route. Its purpose is to measure task
difficulty, cost and grader stability. A two-task result is diagnostic only:
it cannot invoke Q0's eight-task ceiling/floor thresholds, qualify routing or
justify a reserved campaign. After that result, either curate six additional
independent public families and seek a new eight-task approval, or stop if the
cost/utility is poor. This amendment is proposed for operator review; no Q3
paid call is authorised by Q2.

## Reproduction and limits

Run `tools/worker_q2_public.py --check` and `--check-evidence` with the project
Python runtime for provider-free catalogue and recorded-result validation.
`--run` needs the Q1-attested WSL root host and the installed Q2 runtime; it
runs six fresh isolated grades with zero provider calls. The saved result is
digest-bound to source and oracle bytes, but a local digest is not a signature
against a user who can rewrite both files. Q2 verifies fixture behaviour and
isolation on this host; it does not verify a paid multi-file Claude adapter,
served model identity, a third-party source registry or a routing decision.
