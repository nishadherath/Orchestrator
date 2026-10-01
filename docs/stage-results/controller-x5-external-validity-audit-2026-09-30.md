# X5 external-validity audit and next admission rule

Date: 2026-09-30 Australia/Sydney. Status: **provider-free development
decision**. No new provider call, frozen benchmark, or promotion claim. B0
remains the shipping default; X6 remains sealed.

## What the completed experiments establish

The v7 development comparison had four Controller-suitable tasks. A and S
each passed all four protected checks at quality 100; A cost 2.67 times S
and took 1.84 times as long on average. Six later first-failure screens
all passed their public checks on the first B0 attempt, so none admitted a
matched recovery pair. K01 reached a real post-success review with a
source-cited but generic Controller handoff, then lost A's worker to a
pre-provider mount failure. K02's B0 producer closed its predeclared public
risk, so S and A correctly made no calls. None of those results measures a
positive A-minus-S quality effect. The K01 and K02 mechanism repairs have
provider-free validation only.

The relevant question is now entry frequency and *incremental value on
genuine unfinished work*. A case cannot become eligible because its hidden
score is poor; entry must be decided from frozen public evidence. The
producer, direct S review and Controller A review must receive identical
public task bytes and separate single-use roots. A's incremental spend and
elapsed time must be counted even when its handoff is unactionable.

## External case audit

These are primary upstream reports, not actor fixtures. The audit assessed
whether the *available issue text and environment* support a blind,
deterministic, independently graded X5 test. No repository was copied or
provider call made.

| Source | Relevant reality | X5 admission assessment |
| --- | --- | --- |
| [urllib3 GHSA-qccp-gfcp-xxvc](https://github.com/urllib3/urllib3/security/advisories/GHSA-qccp-gfcp-xxvc) | Real proxy/redirect credential exposure with a specific low-level versus high-level API boundary. | Reject as a blind repair case: the published advisory names the failing API, affected versions, and direct remediation. An actor that restates the report would leak the answer; removing those details would create an authored task. |
| [Requests #6981](https://github.com/psf/requests/issues/6981) | Real environment-proxy reintroduction after a redirect despite explicit `None` proxy settings. | Reject for a blind repair case: the issue includes a one-line suggested patch. The report has no independent protected acceptance for related proxy precedence and credential safety. |
| [Go #79792](https://github.com/golang/go/issues/79792) | Real proxy-boundary credential concern with positive and negative controls and a standard-library PoC. | Reject for this Python/WSL worker campaign: the report itself explains the exact failing predicate and proposes two fixes. It is also an open compatibility-policy discussion, so an independent correct-fix oracle is not settled. |
| [SQLAlchemy #13439](https://github.com/sqlalchemy/sqlalchemy/issues/13439) | Real concurrent ORM/compiled-cache symptom with a detailed MCVE. | Hold as research only: the report says the race appears in roughly 35–40% of three-way runs, requires asyncpg/PostgreSQL, and points to suspected functions. A single public pass is not a reliable entry or acceptance signal; the issue is labelled as likely LLM-located by the project. |
| [pytest #14800](https://github.com/pytest-dev/pytest/issues/14800) | Deterministic regression in fixture cleanup, with a minimal plugin-free reproducer and real `pytest-lazy-fixtures` impact. | Reject the published report as a blind task: it bisects two commits, traces the failing state transition, and gives two concrete fixes. Removing its diagnosis after selection would make a new authored prompt and invite selection bias. |
| [pytest-asyncio #1501](https://github.com/pytest-dev/pytest-asyncio/issues/1501) | Order-dependent teardown of shared-scope async fixtures used by sync tests, with a compact reproducer. | Provider-free reproduction and one isolated proposed repair succeeded on pinned v1.4.0/pytest 9.1.1. An executable two-factory coverage check accepts that repair and rejects a disposable single-factory negative control that passes the original issue. Reject as a blind paid case: the issue states the fix layer and links a detailed open PR. Independent protected acceptance and an alternative complete repair are also missing. See [E01 preflight](controller-x5-external-e01-preflight-2026-09-30.md). |
| [Alembic #1768](https://github.com/sqlalchemy/alembic/issues/1768) | SQLite batch migration produces duplicate Boolean CHECK constraints. | A reduced version-pinned reproduction produced two constraints on Windows and WSL, while direct table creation produced one. An invalid value was still rejected. Reject for paid X5: the consequential residual risk is unobserved, and later related issues cannot be selected as a blinded holdout after inspection. See [E02 preflight](controller-x5-external-e02-preflight-2026-09-30.md). |
| [HTTPX #3782](https://github.com/encode/httpx/issues/3782) | Repeated cancellation of a streaming task retains active connections until the pool times out. | The pinned stack reproduced `[1, 2, 3, PoolTimeout]` after double cancellation on Windows and WSL. A cancellation-only repair passed that symptom but failed an injected close-retry probe; two repair variants passed both and concurrent-close control. Reject for blind paid X5 because the later public PR already publishes the diagnosis, failed-close tests and repair. See [E03 preflight](controller-x5-external-e03-preflight-2026-09-30.md). |

SWE-bench Verified is not an automatic substitute for these rejected cases.
Its [official dataset](https://github.com/SWE-bench/SWE-bench) provides real
repository issues, but [OpenAI's Verified audit](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
reports contamination and design problems that weaken a current frontier
model comparison. A selected task would still require its own source commit,
dependency isolation, independent oracle review and public-only entry rule.

## Revised X5 entry and evaluation contract

1. Start with a **natural issue and untouched source revision**. Preserve
   the original issue text available at that revision; do not add a hidden
   fault, solution hint or manufactured incident. Record provenance and
   license. Exclude cases whose public issue or source comments give the
   repair outright.
2. Reproduce the reported symptom deterministically in the worker's tool
   environment. Freeze a distinct public follow-up check for a consequential
   invariant that could remain broken after the first repair. Its result,
   not a protected oracle, decides whether a post-success review opens.
   If B0 passes this check, close the case before S/A spend, as in K02.
3. Independently freeze protected functionality and safety checks, including
   credible wrong repairs and compatibility cases. Verify baseline, narrow
   repair and at least two complete repairs provider-free. A narrow public
   patch should plausibly pass the original check while failing a separate
   invariant; this must be demonstrated, not merely described.
4. Record the intended target population and sample plan *before* producer
   calls. Count all screened producers, public passes, failed admissions,
   generic handoffs and interrupted runs. Stop if the entry rate is too low
   to obtain a useful pair sample within the authorised cost ceiling.
5. On an eligible accepted root, clone exact public bytes to S/A and give
   them the same frozen review goal and worker cell. A alone receives the
   bounded Controller. Require an actionable, source-cited next check before
   A's worker call. Report a generic handoff as a Controller failure rather
   than converting its spend into a quality success.
6. Blindly grade S/A on protected acceptance, critical violations, honest
   claims, useful partial work, cost and elapsed time. Predeclare an economic
   threshold: incremental A quality must outweigh its extra cost and delay
   in the target population. A single development pair is a feasibility
   result; production promotion requires a powered reserve and independent
   review. Do not open X6 based on this audit.

## Decision and remaining uncertainty

No audited external report currently satisfies all of deterministic entry,
blind public issue, suitable local runtime and independent acceptance. No
further paid screen is warranted on K01/K02 or another short authored
regression. The provider-free E01 research on
[pytest-asyncio #1501](https://github.com/pytest-dev/pytest-asyncio/issues/1501)
reproduced both test orders on the signed v1.4.0 tag and passed the untouched
release's 40-test loop-factory suite. One unmerged repair passed an
independently authored two-factory check, while a disposable single-factory
control passed the issue and failed that check. E01 is now rejected for a
blind paid comparison because the natural issue and linked proposal expose
the fix layer. See the [E01 preflight](controller-x5-external-e01-preflight-2026-09-30.md).
The [E02 Alembic preflight](controller-x5-external-e02-preflight-2026-09-30.md)
also reproduced its reported symptom on both hosts but did not demonstrate
a consequential residual risk, so it is not a paid case.
The [E03 HTTPX preflight](controller-x5-external-e03-preflight-2026-09-30.md)
reproduced pool exhaustion four times on the worker host using a local server.
The disposable negative and repair variants calibrated a distinct close-retry
gap, but the later public PR already describes and tests it. E03 is rejected
for a blind paid comparison; the injected retry probe is not an independent
protected oracle and later-fix contamination cannot be bounded here.
The subsequent [external intake B](controller-x5-external-intake-b-2026-09-30.md)
screened eight more recent open issues. E06 AnyIO's interpreter shutdown hang
reproduced under a process watchdog on Windows and WSL, but its linked PR is
already public and correct lifecycle policy remains under review. The other
seven reports disclose the fault path or repair in their issue bodies. None
entered paid X5; the convenience sample does not estimate a population rate.
The next concrete work is to qualify a real issue package with the six
properties above **provider-free**, then freeze its
manifest, analysis and dated spend notice before any producer. If natural
issues cannot supply such a package, the honest X5 result is that Controller
uplift is unmeasured for this host/task mix; keep B0 and leave X6 sealed.

Observed facts above are from recorded X5 receipts and linked upstream
reports. The prediction that natural issues will create more Controller
headroom is an inference. Untested risks include model memory of public
fixes, nondeterministic upstream tests, tool/runtime differences and a
Controller that remains generic even on a genuine residual risk.
