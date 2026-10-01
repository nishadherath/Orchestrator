# Q4U U3: disjoint corpus inventory

Date: 2026-09-26 UTC. Status: **inventory frozen; canary complete**. Two upstream
development families each have frozen weak and strong public-check variants:
D01W/D01S and B02W/B02S. Two authored synthetic no-edit investigations,
C03 and C04, two missing-facts investigations, M05 and M06, a synthetic
two-module encoding family, F07W/F07S, and a synthetic single-module state
family, H08W/H08S, are also frozen.
Four disjoint reserved mechanisms, R09-R12, are frozen and remain untouched.
The [paid canary](worker-q4u-u3-canary-2026-09-26.md) completed with no quality
gain for the experimental arms. B0 remains the shipping default. The versioned
Q4U WSL one-editable boundary passed both zero-provider probes and ten paid
development episodes.

The earlier public upstream screens used cachetools, itsdangerous, click,
urllib3, tenacity, PyJWT, packaging, platformdirs, attrs, pluggy, h11,
sortedcontainers, more-itertools and idna. This inventory comes from
`tools/worker_q2_public.py`, `tools/worker_q3_public_source.py` and
`tools/worker_q4s_public_source.py`; Q4T reused five Q4S sources. U3 must
exclude these repository/task pairs and all N5 and N4 generated task
instances. The N4 R-series generator and oracle were inspected during U0,
so those cases cannot be a blind reserve.

Upstream development source and leads:

| Public source | Potential mechanism | Unresolved before inclusion |
| --- | --- | --- |
| [python-dotenv issue 661](https://github.com/theskumar/python-dotenv/issues/661) and [fix PR 680](https://github.com/theskumar/python-dotenv/pull/680) | Parser boundary and write/read state round-trip | Weak and strong public-check variants are frozen below; independent mechanisms remain to build. |
| [boltons fix commit](https://github.com/mahmoud/boltons/commit/f1034b07ddf71f4d9285134a47a4ade16fe40789) | JSON Lines iterator nontermination at EOF and negative relative seek | Frozen as B02W/B02S below; further resource mechanisms remain to build. |
| [python-dateutil issue 1508](https://github.com/dateutil/dateutil/issues/1508) | Invalid timezone offset and error boundary | It is an open issue, so an authored reference would need independent review and must be labelled as such. Confirm no duplicate mechanism and stable runtime. |
| [YARL changelog](https://github.com/aio-libs/yarl/blob/master/CHANGES.rst) | URL query or cache behaviour | Check whether a pinned version can run without compiled extensions and whether a compact actor package preserves semantics. |

The next selection pass should prefer pinned, self-contained Python source
with permissive redistribution terms, low setup cost and an objective oracle.
Do not infer suitability from a changelog or issue alone. A candidate is
admitted only after source/fix provenance, licence bytes, public actor
inventory and independent baseline/reference/partial calibration are frozen.

The python-dotenv development task uses pre-fix parent
`751f8c148222e58aa173c83c4e5e6cfccb2cc124` and fix
`f7b18d9c72d1abcc2ad4023424b84f5bee30d266`. The exact parent contains
nine `src/dotenv` package files and a BSD-style licence with SHA-256
`80619b7049f08c81683ad0e01f08f257a840652dd71ee83146d36658c7d2c2b9`.
The ignored local staging script and clone are under `pilot-runs/q4u-pilot/`
and `pilot-runs/q4u-sources/`. The frozen
[D01W task](../../test/fixtures/worker_q4u_public/D01W/task.json) has task digest
`a8ef18a035bc6ac2d929e898c1aaa517771d3920d5c9bfe64dd37b20fb348669`.
It binds 13 public actor files and changed-output acceptance metadata. A future
episode runner must apply this metadata to the version-1 acceptance contract;
the metadata itself does not enforce a worker change. It binds
the [sealed evaluator](../../test/oracles/worker_q4u_public/D01W.zip) at
SHA-256 `0f53d077bfeb37ab98ee4fd493b369af4de7ed68b15525b93ba8f5cf8f7e3032`.
The evaluator ZIP holds the hidden grader and source overlays, and only actor
files are copied into a worker workspace. A scoped Graft search found no
hidden grader definition in the source graph. The archive must still be kept
outside any future actor mount.
[D01S](../../test/fixtures/worker_q4u_public/D01S/task.json) uses the same
upstream source and evaluator with a direct public check of doubled-backslash
round-trip and both single- and double-quote parser boundaries. Its final task
digest is `d902180a0446ffcc5859ba4eea251d6ccbc15098bf59c8c7b87d573fc9e969c7`.
These are two public-check variants of **one task family**, not two independent
examples.
The saved [pilot calibration](../../test/results/2026-09-26-worker-q4u-dotenv-pilot.json)
has a useful three-way separation: the baseline fails doubled-backslash
round-trip and a two-binding parser boundary; applying only the fixed writer
passes the round-trip but still fails the parser boundary; applying both
upstream modules passes both. Ordinary single-backslash and plain-value
controls pass all three variants. The first exploratory probe used only
single-backslash examples and was non-discriminating; it was corrected before
this saved pilot. The parser-boundary case checks the exact parsed values,
binding count, line positions and error flags.

`tools/worker_q4u_public.py --check` verified both actor inventories and the
shared ZIP seal. Its optional upstream check matched source, licence and
overlays to exact Git objects. The repeatable
[D01W calibration](../../test/results/2026-09-26-worker-q4u-d01w-wsl-calibration.json)
and [D01S calibration](../../test/results/2026-09-26-worker-q4u-d01s-wsl-calibration.json)
ran the same sealed hidden grader on each source variant. Both have hidden
scores of baseline **15/100**, writer-only partial **55/100**, and full
reference **100/100**. D01W's weak public check passes all three; D01S's
direct public check rejects baseline and partial and passes reference. The
Windows Python 3.12 and WSL Python 3.14.7 grade records match exactly apart
from interpreter version. The fixture was corrected before any paid use so
that `python3 -B public_check.py` imports
its own `src/dotenv` package without an environment-supplied `PYTHONPATH`;
the final task digest above binds that correction. The five focused
`worker_q4u_public_tests.py` checks pass, including actor/evaluator tamper
rejection. The [weak](../../test/fixtures/worker_q4u_public/D01W/public_assessment.json)
and [strong](../../test/fixtures/worker_q4u_public/D01S/public_assessment.json)
public assessments are frozen from cited issue and check lines: D01W is `partial`, D01S is
`direct`. Fifteen focused Q4U tests pass across the coverage, corpus and
assessment modules. Provider-free WSL execution does not prove a complete
U3 corpus or actor isolation in a live episode.

The boltons development family uses pre-fix parent
`435774ef8b10c1355bf77483a837945034011754` and fix
`f1034b07ddf71f4d9285134a47a4ade16fe40789`. Its source is the single
upstream `boltons/jsonutils.py` module and package initialiser. The parent
licence SHA-256 is
`c301912653a8d8c99eab6212aa3aea8d164ea249d8ad53c941e0558a0a5ac1e3`.
An ignored pilot uses a capped-read file wrapper so the pre-fix infinite
loop becomes a bounded failure. The [saved pilot](../../test/results/2026-09-26-worker-q4u-boltons-pilot.json)
separates baseline **30/100**, EOF-only partial **65/100**, and full upstream
fix **100/100**. It covers both EOF alignment and negative relative-seek
normalisation, plus positive-seek and ordinary-forward controls. An initial
reverse-iteration control was removed because `StringIO` is incompatible
with that unrelated byte-oriented path; it never entered the saved pilot.
The final [B02W task](../../test/fixtures/worker_q4u_public/B02W/task.json)
has digest `d2147f43b79e67546a49c0dc531b858d6a20dddcde7871a1dd9bc4dcacbb2004`;
[B02S](../../test/fixtures/worker_q4u_public/B02S/task.json) has digest
`749d55a6584f224ea535b1b22c1aaab07fbbe4ef4a8`. They bind six actor
files each and share a [sealed evaluator](../../test/oracles/worker_q4u_public/B02.zip)
at SHA-256 `e997e6d9d34288a71279d6e89ff19476957ffeb04033fe7280e1cbafcc6da847`.
Only `boltons/jsonutils.py` is editable. The changed-output flag is actor
metadata that must be applied by a future episode runner. Exact upstream Git
objects verified source, licence, and partial/reference overlays.

The [B02W WSL calibration](../../test/results/2026-09-26-worker-q4u-b02w-wsl-calibration.json)
and [B02S WSL calibration](../../test/results/2026-09-26-worker-q4u-b02s-wsl-calibration.json)
match Windows calibration on hidden scores of baseline **30/100**, EOF-only
partial **65/100**, and full fix **100/100**. B02W's ordinary/positive smoke
check passes all three. B02S's bounded EOF and negative-seek checks reject
baseline and partial, and pass reference. The [weak public assessment](../../test/fixtures/worker_q4u_public/B02W/public_assessment.json)
is `partial`; the [strong assessment](../../test/fixtures/worker_q4u_public/B02S/public_assessment.json)
is `direct`, both with cited public lines. Four B02 fixture tests and the
expanded assessment tests pass. The full focused Q4U suite now passes 35/35.
These are variants of **one second task family**, not independent examples.

`tools/worker_q4u_contract.py` now validates each sealed task and converts
its metadata into a real version-1 command contract with protected actor
files and named editable outputs. It requires changed output on D01/B02 and
does not require it on C03/C04/M05/M06/R11/R12. A focused test loads all
sixteen
contracts against staged actor copies and confirms pre-dispatch required-output baselines exist
only for change-required tasks. The live runner still needs to use this
builder before a provider call.

The two synthetic controls test separate already-correct mechanisms:
[C03](../../test/fixtures/worker_q4u_public/C03/task.json) uses stable integer
largest-remainder allocation; [C04](../../test/fixtures/worker_q4u_public/C04/task.json)
uses Unicode NFKC/case-folded label keys. Both issues ask for investigation
and a patch only on a demonstrated defect. They have Apache-2.0 licence
copies, five sealed public actor files each and hidden evaluators outside the
actor tree: [C03](../../test/oracles/worker_q4u_public/C03.zip) and
[C04](../../test/oracles/worker_q4u_public/C04.zip). The ignored local builder
under `pilot-runs/q4u-pilot/` kept hidden grader source out of the indexed
repository. On [Windows C03](../../test/results/2026-09-26-worker-q4u-c03-calibration.json),
[Windows C04](../../test/results/2026-09-26-worker-q4u-c04-calibration.json),
[WSL C03](../../test/results/2026-09-26-worker-q4u-c03-wsl-calibration.json)
and [WSL C04](../../test/results/2026-09-26-worker-q4u-c04-wsl-calibration.json),
the baseline/reference score **100/100** and a behaviour-preserving but
unnecessary source edit scores **0/100**. Public checks pass all three. Their
public-only assessments are `partial` for edge coverage, but classify them as
investigations with `change_required: false`; an accepted low-effort no-edit
result stops instead of triggering a stronger repair. This is offline
calibration, not a measured worker outcome.

The two authored missing-facts investigations are
[M05](../../test/fixtures/worker_q4u_public/M05/task.json), which lacks the
jurisdiction required to select a tenant retention schedule, and
[M06](../../test/fixtures/worker_q4u_public/M06/task.json), which lacks both
the source timezone and a policy for daylight-saving gaps or repeats. Each
actor now has an invalid `{}` `decision.json` placeholder, so the isolated
host can safely permit its edit. The public check validates its
envelope without revealing the needed fields. Sealed evaluators outside the
actor tree grade an uncompleted placeholder **0/100**, a stop that identifies only
some or wrong missing facts **40/100**, and an exact justified stop **100/100**.
A false `ready` claim or source edit scores zero. The
[M05 Windows calibration](../../test/results/2026-09-26-worker-q4u-m05-calibration.json),
[M06 Windows calibration](../../test/results/2026-09-26-worker-q4u-m06-calibration.json),
[M05 WSL calibration](../../test/results/2026-09-26-worker-q4u-m05-wsl-calibration-v2.json)
and [M06 WSL calibration](../../test/results/2026-09-26-worker-q4u-m06-wsl-calibration-v2.json)
agree apart from Python version. This demonstrates an evaluation distinction;
it does not show that a worker will ask the right question. Both public-only
assessments are `partial` and their command contracts allow an investigation
without a source edit, while requiring `decision.json` before public acceptance.

The authored [F07W](../../test/fixtures/worker_q4u_public/F07W/task.json)
and [F07S](../../test/fixtures/worker_q4u_public/F07S/task.json) variants
share a two-module event-reference escaping regression and one
[sealed evaluator](../../test/oracles/worker_q4u_public/F07.zip). Their
baseline, encoder-only partial and full reference score **30/65/100** on both
[Windows weak](../../test/results/2026-09-26-worker-q4u-f07w-calibration.json)
and [WSL weak](../../test/results/2026-09-26-worker-q4u-f07w-wsl-calibration.json)
calibration, with matching strong-variant grades. The weak public check passes
all three, while the strong check rejects baseline and partial. Public-only
assessments cite the escaping and malformed-input lines and label F07W
`partial`, F07S `direct`. This is a second multi-file candidate, but its
measured worker difficulty is unknown. Synthetic origin is explicit.

The authored [H08W](../../test/fixtures/worker_q4u_public/H08W/task.json)
and [H08S](../../test/fixtures/worker_q4u_public/H08S/task.json) variants
share a single-module event-reconciliation regression. The issue requires
strictly increasing revisions and retained delete tombstones. The
[sealed evaluator](../../test/oracles/worker_q4u_public/H08.zip) scores the
baseline, stale-filter-only partial and full fix **30/65/100** on
[Windows](../../test/results/2026-09-26-worker-q4u-h08w-calibration.json) and
[WSL](../../test/results/2026-09-26-worker-q4u-h08w-wsl-calibration.json).
The weak public check passes all three; the strong one rejects baseline and
partial. Public-only assessments are `partial` and `direct` respectively.
This is a second single-module candidate, but no worker difficulty has been
measured. Synthetic origin is explicit.

Before any Q4U provider outcome, a public-only assessment review found that
the assessor had set `cross_component: false` for every task. That erased the
cross-component candidate's prospective difference on D01's writer/parser
and F07's encoder/decoder. The four affected development assessment files were
re-frozen with `cross_component: true`; R10's coupled tax/invoice files are
also true, while B02, H08, R09 and investigations remain false. The
superseded D01W/D01S assessment digests were
`0e1e8654e0a9f0e668cafe6189d941b99bbf310c341e5338a86d54e68bc6a49f`
and `66f1546237bfd415da01c3dcf446ac3a14933f25b2eb06cbb6b194c22899e03b`;
the superseded F07W/F07S digests were
`5f394cbcebb75ee23d6df150b2bb47c8519c2ffa47d820752a652e5376d50970`
and `2c52eed1fd97f2fb0cb2519eaef28db67386cbe13fb9039e5f9c5d8622618942`.
No paid manifest or outcome used them. The current D01W/D01S digests are
`832f0294580decda60a2149cd613cd1c402b24b8263fe0660c2588782a96ad47`
and `0b16146276fdcb22afc8e0605d39f1700522d17046d1aa79816188312cfe79ed`;
the current F07W/F07S digests are
`72bc52149645fa6e08521b728b3f43399a1ac5149f720b22012d04a1df08a91f`
and `b2cc0f3434fa260922607f56d813b012420638b85d1dd055203cd756f3dab105`.

The corpus matrix must contain at least two distinct mechanisms in each
tested category: resource/state invariants with weak public checks, easy
multi-file changes, hard single-module changes, genuinely correct no-edit
controls and missing-facts stop cases. The development matrix now has two
mechanisms in each category, with worker difficulty still unmeasured. The
reserved cases were chosen and sealed before development outcomes. Authored
synthetic cases are labelled and are never presented as upstream regressions.
Strong and weak
public-check variants should share the same hidden grader, so a coverage
effect is distinguishable from task difficulty.

| Required category | Frozen development mechanisms | Still needed |
| --- | --- | --- |
| Resource/state with weak public check | D01 round-trip and parser boundary; B02 bounded EOF and negative seeking | Confirm the category classification in prospective review. |
| Easy multi-file change | D01 two-module round-trip; F07 two-module escaping | Evidence that either case is easy for workers. |
| Hard single-module change | B02 bounded JSONL seek; H08 revision/tombstone reconciliation | Evidence that either case is hard for workers. |
| Correct no-edit investigation | C03 integer allocation; C04 Unicode label normalisation | Live no-edit behaviour remains unmeasured. |
| Missing-facts stop | M05 retention jurisdiction; M06 timezone and DST policy | Live stop/clarification quality remains unmeasured. |
| Disjoint reserve | R09 byte-frame boundaries; R10 invoice rounding; R11 correct interval coalescing; R12 currency-quote clarification | Four independent mechanisms permit exploration, not a promotion claim. |

The current [reserved manifest](../../test/fixtures/worker_q4u_public/reserve_manifest_v2.json)
is frozen at canonical reserve digest
`dbe805fdf4a7b3a9319aed496b265f720befd5a993b680a25e0448851f6cc6a4`.
The [v1 manifest](../../test/fixtures/worker_q4u_public/reserve_manifest.json)
with digest `d69516552f4ce0c4cd9f7c05fe65928a922e448dee5d3ff8fa3c3affb7d326b6`
is preserved, but was superseded before provider outcomes because R12 needed
an existing editable decision file. Only v2 is current.
It binds each reserved task, sealed evaluator, public-only assessment, command
contract and supporting source tools. R09/R10 have hidden baseline, partial
and reference scores of **30/65/100**; R11 has **100/0/100** for untouched,
unnecessary-edit and untouched reference states; R12 has **0/40/100** for
absent, incomplete and exact clarification. Windows and WSL calibration
records match apart from interpreter version. The reserve is explicitly
exploratory: four independent mechanisms are too few for a credible uplift
promotion under the existing quality gate. No reserved provider outcome has
been viewed. A canary may inform a later, separately powered campaign, but
cannot itself promote a new default.

The canary incurred USD 1.022577203 in measured API-equivalent worker usage
over ten Claude Code subscription calls. The development session's direct API
cost and incremental subscription invoice impact are unobservable here. The
[ten-episode manifest](../../test/results/2026-09-26-worker-q4u-u3-canary-manifest.json)
is frozen at digest
`33e0cb0d85a04071ead319cce24385b4bdcb7df8b77de33d6e5f6fdc881838be`,
with a [dated spend notice](worker-q4u-u3-canary-spend-notice-2026-09-26.md),
30-call ceiling, USD 40 local allocation and a matching standing-approval
record. The WSL source/runtime proof passed. Claude Code subscription login
was refreshed before the zero-provider auth preflight and paid episodes.

The Q4U host change is side by side with the historical Q1/Q4T snapshots.
`tools/worker_wsl_q4u.py` allows one to eight **existing** editables while
pinning the Q1 base hash. Its launcher and adapter retain namespace,
subscription, stop-receipt, protected-file and structured-report checks.
The provider-free [probe](../../tools/worker_wsl_q4u_probe.py) passed for a
single-file edit (B02W), correct no-edit (C03) and completed decision stub
(M05), including protected-file integrity, collected revision binding and
proof that historical Q1 still rejects one editable. Windows and WSL
recalibration of M05/M06/R12 remain **0/40/100**. Prior public assessments
and local calibrations are preserved under
`test/fixtures/worker_q4u_public/history/` and `test/results/q4u-history/`;
WSL v1 and v2 calibrations coexist. The dedicated
`tools/worker_q4u_executor.py` v3 experimental wrapper maps B0,
cross-component-medium and coverage-repair to distinct bounded ladders without
altering the shared, historically sealed TaskExecutor source. The repair is
dispatched only after an actual failed first attempt. The provider-free WSL
probe now includes an integrated M05 TaskExecutor acceptance and passes all
cases; 40 focused Q4U tests pass, including canary schedule and incomplete
result accounting. The full offline harness passed as part of the successful
redistributable build. This is not a shipping selector change.
