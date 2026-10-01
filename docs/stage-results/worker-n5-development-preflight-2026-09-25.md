# N5 development preflight, 2026-09-25

Later status: the exact campaign was approved and completed. See the
[N5 stage result](worker-n5.md) for reconciled outcomes. The remainder of
this document preserves the pre-launch evidence and decision point.

Status: **corpus and campaign ready for exact paid authorisation; no N5
development episode launched**. The shipping B0 policy is unchanged. The
[completed cell screen](worker-n5-screen-2026-09-25.md) is historical evidence,
not a substitute for this task-sensitive comparison.

The older N4 corpus labelled all 24 tasks `moderate`, so a complexity-sensitive
selector would send every development task to Sonnet high. N5 now has a
[separate generated corpus](../../test/fixtures/worker_n5_realworld/catalogue.json)
of 12 D and 12 sealed R tasks. Both splits have four tasks at each of routine,
moderate and complex complexity and two mechanisms in each of six service
families. The actors have only `app.py`, `public_check.py`, `ISSUE.md` and
`acceptance.json`; the hidden oracles never enter them. A reference
implementation scored 100 on all 24 oracles. A public-example lookup failed
all hidden oracles. This is synthetic single-file work, not a claim that
multi-file repository tasks are qualified.

The [frozen development manifest](../../test/results/2026-09-25-worker-n5-development-manifest.json)
has digest `cd88664ef034fc982e27fc99386ca140e32127f78ab65d6982d91232555ddc09`.
It binds all 121 corpus files, complete screen evidence, source dependencies,
the host, subscription and fresh sentinel proofs, the [dated spend notice](worker-n5-development-spend-notice-2026-09-25.md)
and a balanced 36-row B0/candidate/alternative schedule. The first cells are:

| Assessment | B0 | Candidate | Alternative |
| :--- | :--- | :--- | :--- |
| Routine | Sonnet low | Sonnet low | Sonnet medium |
| Moderate | Sonnet low | Sonnet high | Sonnet xhigh |
| Complex | Sonnet low | Opus high | Fable high |

The candidate and alternative cells are actual, explicitly admitted
`TaskExecutor` dispatches, not shadow labels. Fable high's served model
identity is screen-observed but its per-run cost projection is unknown; its
alternative selection requires an explicit USD 3 root ceiling. A fake campaign
verified the first three arms and showed that a fourth uncertain invocation
blocks on restart without replay. Root admission, input and policy integrity,
campaign ledger cardinality, settled cost reconciliation, public acceptance
isolation and independent hidden grading are checked before recording grades.
Partial quality, critical errors and false success are retained.

Verification: the corpus drift check passed. Corpus, experimental-dispatch
and development-driver suites passed provider-free, including reference and
public-only attack cases, Fable cap selection, policy tamper, missing budget,
altered row and uncertain-call recovery. The normal-host `tools/build_dist.py`
pre-build offline harness passed and rebuilt the bundle. `tools/release_check.py`
found all 75 distributed files source-equivalent, all 15 worker definitions
generated and no sensitive material in the package. The bundle stamp is dirty
because repository work is uncommitted; publication remains an operator action.
The WSL host attestation passed 55 checks, the subscription attestation eight,
and the fresh Sonnet-low denied-Read sentinel passed at **USD 0.053023**
provider-reported API-equivalent usage. The requested effort was low; served
effort was not independently reported.

One restricted-sandbox harness run failed on Windows CRLF in newly generated
issues, a historically frozen Controller registry hash, and known WSL/`uv`
process restrictions. The CRLF generation was fixed; the shared registry was
restored and Fable observation moved to the campaign host capability. The
normal-host full pre-build gate then passed. Graft's structural graph is in
sync. Two DeepSeek-backed semantic rebuild attempts returned an unparseable
tool-call response for `tools/task_executor.py`; eight summaries remain stale.
No exact DeepSeek usage or charge was returned, so its cost is unknown, not
zero.

The 36-episode campaign has **USD 108 local admission allocations**, with a
low-confidence USD 10–60 API-equivalent projection and 2–8 hours elapsed.
Those allocations are not a provider hard cap or a subscription invoice.
The prior screen approval names a different manifest and does not authorise
this campaign. The [live runner](../../tools/worker_n5_live_development.py)
will reject launch without an approval record naming this exact digest,
notice and USD 108 ceiling. Exact next action: obtain that approval, save its
record, validate it against the current host and manifest, run only the 12 D
tasks in the frozen order, then reconcile cost and grade data before tuning
or freezing a candidate for N6. Do not run the R tasks in N5.
