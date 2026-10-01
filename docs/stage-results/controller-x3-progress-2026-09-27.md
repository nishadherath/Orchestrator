# X3 progress: development split complete, reserved split underway

Date: 2026-09-27 Australia/Sydney. Status: **in progress, not an X3 exit**.
The operator confirmed GPT-5.6 Sol / High; the host does not independently
expose its active model or effort. B0 remains the shipping default.

The first mechanism-distinct task, C03-D1 (ambiguous payment retry), has
an actor-visible issue and two editable files, an evaluator-only oracle with
four behavioural milestones, reference and equivalent repairs, a useful
partial repair, baseline, label-copy and child-process JSON-poisoning controls.
`tools/controller_x3_grade.py` runs actor commands under the existing Q1 WSL
UID/mount/PID boundary and computes M/E/D/N/H in a separate root-owned parent.
It never imports actor code into the scorer. Actor output and claimed probes
are compared with protected observations; critical double-charge failures
force quality zero. C03-D2 adds a distinct outbox-delivery-lease race, with
overlapping claims, expiry fencing, stale acknowledgement and duplicate
acknowledgement checks. C01-D1 adds a false-premise order/receipt incident:
client-version ID aliases must reconcile while account and ID-prefix boundaries
hold. C02-D1 adds an online migration where reads must fall back to legacy
data and backfill must preserve newer values. C04-D1 adds a tenant cache
boundary with a separate update edge case. N02-D1 adds an ordinary local slice
repair as a low-rigour negative control; it has no critical safety milestone
and retains nonzero credit for incomplete work. N03-D1 adds a missing operator
retention decision: an accepted clarification leaves the policy byte-for-byte
unchanged; a concealed edit forces quality zero. C06-D1 adds a misleading queue
incident with actor-visible trace data and opposing clock-skew probes. C07-D1
adds a coupled decimal-rounding invariant across ledger and statement modules,
including half-even ties and negative refunds. C08-D1 adds opposing lock-order
contracts where the accepted outcome is a clarification with no code edit.
C05-D1 adds a one-pass streaming-window join with sparse late matches and a
fixture-observed cap on retained live rows.
N01-D1 adds a cross-module money-symbol rename; the public smoke passes with
stale imports, while the protected check requires the old export to be removed
and both consumers updated. N04-D1 adds a known release-pin procedure across
deploy and audit manifests; its public check covers only an unchanged pin.
N02-D2 adds a local nullable-profile repair distinct from the slice-boundary
bug. N03-D2 adds a missing approved target region: pilot routing must stay
unchanged, and accepted clarification asks for the specific operator decision.
N01-D2 adds a configuration-key move from milliseconds to seconds across the
client and scheduler. Protected runtime overrides expose stale readers even
when the visible default still works.
N04-D2 adds a synthetic staged signing-key rotation: both old and new IDs
must validate while new signatures use the new ID. C01-D2 separates composite
cache-key concatenation collisions from punctuation collisions left by a
naive delimiter. C02-D2 checks that a versioned envelope rewrite preserves
known audit metadata and unknown future extensions. C04-D2 makes tenant
context on retried jobs a critical requirement while scoring trace propagation
separately. C08-D2 is an immutable version-one API conflict whose accepted
result is a no-edit clarification. C07-D2 tests Sydney reporting-window
boundaries in winter and daylight-saving time. C06-D2 checks that a pool
reserves one foreground slot without starving retries. C05-D2 checks actual
index-row fetch counts for offset and narrow pages. These eight mechanisms
complete the 24-case development split.
Fifteen new reserved mechanisms are separately registered. C01-R1 scopes event
sequence deduplication by feed and epoch, C01-R2 reconciles a stale search
index against authoritative row revisions and tombstones, and C02-R1
preserves shadow-column write parity for a rollback reader during cutover.
C02-R2 checks that checkpoint compaction replays additive events once and
retains a prefix tombstone rather than resurrecting a deleted key.
C03-R1 fences a former lease owner after transfer while preserving healthy
takeover; C03-R2 deduplicates webhook delivery IDs without dropping distinct
events that arrive out of sequence. C04-R1 denies a guessed report ID
belonging to another tenant while retaining archived owner access.
C04-R2 resets tenant session state on connection checkout and all return
paths, including exceptions. C05-R1 bounds the pending batch queue
under producer bursts and preserves FIFO order and explicit backpressure.
C05-R2 restores published big-endian frame headers across the encoder and
both decoder paths, distinct from C07-R1's Unicode character-count case.
C06-R1 targets cache invalidation and shares hot-key refills while
deferring other changed keys without returning stale values. C06-R2
dual-writes schema fields while the old and new readers coexist. C07-R1
counts UTF-8 bytes and retains message boundaries across a frame stream.
C07-R2 applies state revisions independently of transport sequence,
rather than deduplicating webhook delivery IDs as C03-R2 does. C08-R1
bounds a sequence-gap replay buffer and emits records in order.
Their [sequence](../../test/results/2026-09-27-controller-x3-sequence-probe.json),
[stale-index](../../test/results/2026-09-27-controller-x3-stale-index-probe.json)
and [cutover](../../test/results/2026-09-27-controller-x3-shadow-cutover-probe.json)
receipts each pass six protected WSL controls. The
[compaction receipt](../../test/results/2026-09-27-controller-x3-compaction-probe.json)
passes another six: both complete repairs score 100, the useful but incomplete
boundary repair scores 73, and baseline, label copy and forged output score
zero with false completion. The matching
[compaction isolation receipt](../../test/results/2026-09-27-controller-x3-compaction-isolation.json)
passes 14 actor-boundary checks with oracle reads denied. The
[lease-transfer](../../test/results/2026-09-27-controller-x3-lease-transfer-probe.json)
and [webhook](../../test/results/2026-09-27-controller-x3-webhook-probe.json)
receipts each pass six protected controls. Their complete repairs score 100;
the safe incomplete repairs score 92 and 71. Baseline, label-copy and forged
output controls score zero because the stale commit and duplicate effect are
critical violations. Both [lease](../../test/results/2026-09-27-controller-x3-lease-transfer-isolation.json)
and [webhook](../../test/results/2026-09-27-controller-x3-webhook-isolation.json)
isolation receipts pass 14 checks with oracle reads denied. The webhook's first
forged-output design overlapped a critical expected value and scored 38.5;
the critical case was made distinct from the public smoke before its six-control
rerun passed. A later WSL startup timeout occurred before its receipt run;
the host recovered and the unchanged receipt run passed. No policy or prompt
was tuned on these outcomes. The [tenant-lookup receipt](../../test/results/2026-09-27-controller-x3-tenant-lookup-probe.json) passes six controls: complete repairs score 100, a safe but incomplete
archived-owner repair scores 75, and leaking or forged-completion controls
score zero. Its [isolation receipt](../../test/results/2026-09-27-controller-x3-tenant-lookup-isolation.json) passes 14 checks with oracle reads denied. The
[pooled-tenant receipt](../../test/results/2026-09-27-controller-x3-pooled-tenant-probe.json) passes six more controls: both complete repairs score 100; quarantining
after an error scores 67 but loses recovery; leaking or forged-completion
controls score zero. Its [isolation receipt](../../test/results/2026-09-27-controller-x3-pooled-tenant-isolation.json) passes 14 checks with oracle reads denied. The
[batch-queue receipt](../../test/results/2026-09-27-controller-x3-batch-queue-probe.json) passes six more controls: complete repairs score 100, a conservative
capacity repair scores 94 but remains incomplete, and unbounded or forged
completion scores zero. Its [isolation receipt](../../test/results/2026-09-27-controller-x3-batch-queue-isolation.json) passes 14 checks with oracle reads denied. The
[wire-frame receipt](../../test/results/2026-09-27-controller-x3-wire-frame-probe.json) passes six more controls: complete repairs score 100; the safe repair
that rejects a valid empty frame scores 79; private byte-order or forged
completion scores zero. Its [isolation receipt](../../test/results/2026-09-27-controller-x3-wire-frame-isolation.json) passes 14 checks with oracle reads denied. The first C05-R2 design
duplicated C07-R1's Unicode-length mechanism, so it was replaced before
the reserved freeze. A WSL preflight timeout during the superseded design
ended before actor staging; the redesigned case passed its final controls.
The [cache-refill receipt](../../test/results/2026-09-27-controller-x3-cache-refill-probe.json) passes six controls: complete repairs score 100, targeted invalidation
without coalescing scores 61, and broad eviction or forged completion
scores zero. Its [isolation receipt](../../test/results/2026-09-27-controller-x3-cache-refill-isolation.json) passes 14 checks with oracle reads denied. The
[mixed-schema receipt](../../test/results/2026-09-27-controller-x3-mixed-schema-probe.json) passes six controls: complete repairs score 100, a new-reader-only
fallback scores 67 but leaves old deployments unable to read new writes,
and silent-zero or forged completion scores zero. Its
[isolation receipt](../../test/results/2026-09-27-controller-x3-mixed-schema-isolation.json) passes 14 checks with oracle reads denied. The
[Unicode-stream receipt](../../test/results/2026-09-27-controller-x3-unicode-stream-probe.json) passes six controls: complete repairs score 100, a single-frame-only
repair scores 71 and remains incomplete, and character-count or forged
completion scores zero. Its [isolation receipt](../../test/results/2026-09-27-controller-x3-unicode-stream-isolation.json) passes 14 checks with oracle reads denied. The
[state-revision receipt](../../test/results/2026-09-27-controller-x3-state-revision-probe.json) passes six controls: complete repairs score 100, a safe stale-revision
guard with a remaining transport watermark scores 67, and stale-value
or forged completion scores zero. Its
[isolation receipt](../../test/results/2026-09-27-controller-x3-state-revision-isolation.json) passes 14 checks with oracle reads denied. The
[ordered-replay receipt](../../test/results/2026-09-27-controller-x3-ordered-replay-probe.json) passes six controls: complete repairs score 100, a bounded but stalled
gap drain scores 67, and unbounded or forged completion scores zero. Its
[isolation receipt](../../test/results/2026-09-27-controller-x3-ordered-replay-isolation.json) passes 14 checks with oracle reads denied. The other nine reserved
mechanisms remain unbuilt. Each registered case has its own causal-probe
rubric; an unregistered case cannot inherit one. The grader currently
handles 24 development and 24 reserved tasks and does not yet
constitute a sealed corpus.

An audit of the first scorer found that full acceptance required exact hidden
diagnosis and next-step slugs. A real actor could repair a task and provide
verified observations but fail for writing the same conclusion in ordinary
language. `tools/controller_x3_language.py` now accepts bounded, task-specific
plain-language equivalents; exact historical slugs remain valid controls.
Actor-chosen bounded probe inputs are retained even when they do not match a
predefined diagnostic shape. Such probes can earn evidence only after the
protected child reruns them; diagnosis still requires the task-specific causal
shapes and observations. Focused tests accept natural descriptions for all
48 task rubrics and exercise two complete scorer paths, while rejecting
vague ones. An unrelated actor-chosen probe can earn evidence if reproduced
but cannot replace the required causal contrast. Confident completion cannot
receive continuation credit from wording intended for a partial result.
This lexical rubric remains gameable and requires broader wording calibration
before X3 exit; it is not a general semantic judge.

`tools/controller_x3_corpus.py` inventories all 48 frozen task IDs and checks
public/protected package layout, safe paths, exact editable overlays and source
hashes. Its [current result](../../test/results/2026-09-27-controller-x3-inventory.json)
is **48 ready, 0 pending**. Every frozen family has two development and two
reserved cases. This is not a quality sample and has no promotion
authority. The existing R5 label-based corpus remains a historical plumbing
fixture.

Focused `test/harness/controller_x3_tests.py` passed 22/22. The explicit
provider-free [WSL vertical probe](../../test/results/2026-09-27-controller-x3-wsl-vertical-probe.json)
passed C03-D1's six controls: reference and alternative 100/accepted, partial
75/useful and incomplete, baseline/label copy/JSON poisoning 0/rejected with
false completion flagged. The independent
[C03-D2 WSL probe](../../test/results/2026-09-27-controller-x3-outbox-probe.json)
passed its six controls with reference and alternative 100/accepted, partial
92/useful and incomplete, and three false-completion controls 0/rejected.
The [C01-D1 WSL probe](../../test/results/2026-09-27-controller-x3-order-alias-probe.json)
also passed six controls: references 100, useful partial 92, and three false
completion controls zero. Direct actor reads of the protected oracles were
denied on all eighteen controls. The
[C02-D1 WSL probe](../../test/results/2026-09-27-controller-x3-migration-probe.json)
passed six more controls: references 100, useful partial 92, and false
completion controls zero. Oracle reads were denied on all 24 controls.
The [C04-D1 WSL probe](../../test/results/2026-09-27-controller-x3-cache-probe.json)
passed six more, with the same accepted/partial/false-completion pattern;
oracle reads were denied on all 30 controls.
The [N02-D1 WSL probe](../../test/results/2026-09-27-controller-x3-slice-probe.json)
passed six controls: references 100, useful partial 76, baseline and label
copy 16/rejected with false completion, JSON poisoning 0/rejected. Oracle
reads were denied on all 36 controls.
The [N03-D1 WSL probe](../../test/results/2026-09-27-controller-x3-retention-probe.json)
passed six controls: two accepted clarifications score 100 without a policy
edit, one useful partial scores 72.5, a confident unsupported completion
scores 40/rejected, and two concealed edits score zero/rejected. Oracle reads
were denied on all 42 controls.
The [C06-D1 WSL probe](../../test/results/2026-09-27-controller-x3-clock-probe.json)
passed six more: references 100, useful partial 92, false-completion controls
zero. Oracle reads were denied on all 48 controls.
The [C07-D1 WSL probe](../../test/results/2026-09-27-controller-x3-money-probe.json)
passed six more: references 100, useful partial 92, false-completion controls
zero. Oracle reads were denied on all 54 controls.
The [C08-D1 WSL probe](../../test/results/2026-09-27-controller-x3-lock-order-probe.json)
passed six more: two accepted clarifications 100, useful partial 72.5, and
concealed order changes zero/rejected. Oracle reads were denied on all 60
controls.
The [C05-D1 WSL probe](../../test/results/2026-09-27-controller-x3-stream-join-probe.json)
passed six controls: reference and alternative 100, useful partial 92, three
false-completion controls zero. Actor oracle reads were denied on all six.
The live-row cap is a fixture-level observation; it does not establish total
process memory use or resistance to a malicious actor monkeypatch.
The [N01-D1 WSL probe](../../test/results/2026-09-27-controller-x3-symbol-rename-probe.json)
passed six controls: two accepted repairs 100, useful incomplete rename 92,
baseline and label copy 16/rejected, and JSON poisoning zero/rejected.
The [N04-D1 WSL probe](../../test/results/2026-09-27-controller-x3-manifest-probe.json)
passed six controls: two accepted repairs 100, useful one-manifest update 88,
baseline 16/rejected, label copy 28.5/rejected, JSON poisoning zero/rejected.
All twelve new actor oracle reads were denied. The label copy earned credit for
an unchanged worker-pin probe; the unsupported completion was still rejected.
The [N02-D2 WSL probe](../../test/results/2026-09-27-controller-x3-null-profile-probe.json)
passed six controls: two accepted repairs 100, useful partial 80,
baseline 10/rejected, label copy 22.5/rejected, JSON poisoning zero/rejected.
The [N03-D2 WSL probe](../../test/results/2026-09-27-controller-x3-region-probe.json)
passed six controls: two accepted no-edit clarifications 100, useful partial
72.5, confident baseline 40/rejected, concealed routing edit and JSON forgery
zero/rejected. All twelve new actor oracle reads were denied.
The [N01-D2 WSL probe](../../test/results/2026-09-27-controller-x3-config-key-probe.json)
passed six controls: two accepted repairs 100, useful partial 61, baseline
16/rejected, label copy 28.5/rejected, JSON poisoning zero/rejected. All six
actor oracle reads were denied.
The first JSON-poison overlays had patched `json.dumps` too late to forge
application output. They were fixed to patch at module import. The subsequent
[all-task forged-output run](../../test/results/2026-09-27-controller-x3-forged-output-controls.json)
passed 16/16 controls: each public check passed, each protected score was zero
and rejected, and each oracle read was denied. Earlier six-control files are
evidence for their other variants; their original poison result alone did not
demonstrate successful output forgery.
The [post-fix full WSL sweep](../../test/results/2026-09-27-controller-x3-fair-prose-regression.json)
passed all 96 controls across the 16 tasks. Its 32 reference/equivalent
solutions were accepted; all actor oracle reads were denied and provider calls
were zero. An earlier sweep exposed a label-copy score increase: wording for a
partial next step had earned credit on a confident complete claim. The scorer
now requires a partial or blocked claim for that credit, and the full rerun
passed the frozen expectations.
Four actor-visible issues then received repository-required British spelling
corrections. Their [24-control refresh](../../test/results/2026-09-27-controller-x3-prose-fix-probe.json)
passed, and the refreshed corpus inventory still reports 16/48 ready. The
[host-permission offline harness](../../test/results/2026-09-27-controller-x3-offline-harness.json)
passed **81/81 checks** after the targeted prose check passed 838 files. Its
first sandboxed run had a child-process permission error; the first complete
host run isolated only the four spelling failures, which were corrected before
the final clean run.
The eight subsequent development cases each passed six provider-free WSL
controls and 14 actor-isolation checks. Their protected receipts are
[rotation](../../test/results/2026-09-27-controller-x3-rotation-probe.json),
[composite key](../../test/results/2026-09-27-controller-x3-composite-key-probe.json),
[envelope](../../test/results/2026-09-27-controller-x3-envelope-probe.json),
[job context](../../test/results/2026-09-27-controller-x3-job-context-probe.json),
[API compatibility](../../test/results/2026-09-27-controller-x3-api-compat-probe.json),
[timezone](../../test/results/2026-09-27-controller-x3-timezone-probe.json),
[pool](../../test/results/2026-09-27-controller-x3-pool-probe.json) and
[index](../../test/results/2026-09-27-controller-x3-index-probe.json).
The matching `-isolation.json` receipts are in the same result directory.
Both complete variants scored 100 for each case; useful partials scored
73-88 without acceptance. False-completion controls were rejected, and
all actor oracle reads were denied. C04-D2's missing tenant on retry and
C08-D2's concealed API edit triggered critical-score dominance. A first
C08-D2 partial report asked an insufficiently specific question; a first
C07-D2 score expectation was miscalculated. Both were corrected before
their six-control reruns passed. These corrections do not establish broader
natural-language grading accuracy.
The [development sweep](../../test/results/2026-09-27-controller-x3-development-sweep.json)
passed all 144 protected controls across 24 tasks. All 144 actor oracle reads
were denied and the sweep made zero provider calls. The targeted prose check
passed 848 authored files. The
[full offline gate](../../test/results/2026-09-27-controller-x3-development-offline-harness.json)
passed 81/81 checks at this checkpoint, before registering the three reserved
cases. A subsequent
[reserved checkpoint gate](../../test/results/2026-09-27-controller-x3-reserved-checkpoint-harness.json)
also passed 81/81 after the first three reserved registrations. A subsequent
full gate after C02-R2 passed 80/81; the unrelated worker N4 concurrent-start
test hit its 10-second ledger-lock wait under host load. Its isolated rerun
passed 6/6. A second full gate also passed 80/81, but its Q4 screen setup
could not validate WSL host evidence during the run. The stored source hashes,
evidence digest and installed launcher hash matched when checked separately;
the Q4 host check then passed, as did its isolated suite (4/4). Both full-gate
failures remain recorded. There is no green full-gate result at 28 cases. The subsequent [30-case full gate](../../test/results/2026-09-27-controller-x3-30case-offline-harness.json) passed 81/81. The subsequent [31-case full gate](../../test/results/2026-09-27-controller-x3-31case-offline-harness.json) also passed 81/81 after C04-R1 registration. C04-R2, C05-R1 and the redesigned C05-R2 have passed focused and
protected checks. The first 34-case full gate was stopped after its
corpus input became obsolete; no result file was produced. The
[corrected 34-case full gate](../../test/results/2026-09-27-controller-x3-34case-offline-harness.json) passed 81/81. C06-R1 and C06-R2 passed focused and protected checks.
The [36-case full gate](../../test/results/2026-09-27-controller-x3-36case-offline-harness.json) passed 81/81. C07-R1 and C07-R2 passed focused and protected checks.
The [38-case full gate](../../test/results/2026-09-27-controller-x3-38case-offline-harness.json) passed 81/81. C08-R1 and C08-R2 passed focused and protected controls; C08-R2's
[six-control probe](../../test/results/2026-09-27-controller-x3-writer-failover-probe.json)
separated complete 100-point repairs from a safe 75-point partial and rejected
three false-completion variants. Its
[actor isolation](../../test/results/2026-09-27-controller-x3-writer-failover-isolation.json)
passed 14 checks. The
[40-case full gate](../../test/results/2026-09-27-controller-x3-40case-offline-harness.json)
passed 81/81. N01-R1's
[six-control probe](../../test/results/2026-09-27-controller-x3-package-path-probe.json)
accepted two complete package migrations at 100, credited the honest partial
at 80, and rejected three false-completion controls at zero. Its
[actor isolation](../../test/results/2026-09-27-controller-x3-package-path-isolation.json)
passed 14 checks. N01-R2's
[six-control probe](../../test/results/2026-09-27-controller-x3-generated-header-probe.json)
accepted two reproducible generators at 100, credited the header-only patch
at 70, and rejected three false-completion controls at zero. Its
[actor isolation](../../test/results/2026-09-27-controller-x3-generated-header-isolation.json)
passed 14 checks. The
[42-case full gate](../../test/results/2026-09-27-controller-x3-42case-offline-harness.json)
passed 81/81. N02-R1's
[six-control probe](../../test/results/2026-09-27-controller-x3-ui-threshold-probe.json)
accepted two complete comparators at 100, credited the early-warning partial
at 88, and rejected three false-completion controls at zero. Its
[actor isolation](../../test/results/2026-09-27-controller-x3-ui-threshold-isolation.json)
passed 14 checks. N02-R2's
[six-control probe](../../test/results/2026-09-27-controller-x3-mutable-default-probe.json)
accepted two complete independent-call repairs at 100, credited the one-path
partial at 88, and rejected three false-completion controls at zero. Its
[actor isolation](../../test/results/2026-09-27-controller-x3-mutable-default-isolation.json)
passed 14 checks. The
[44-case full gate](../../test/results/2026-09-27-controller-x3-44case-offline-harness.json)
passed 81/81. N03-R1 and N03-R2 each passed
[six protected controls](../../test/results/2026-09-27-controller-x3-client-floor-probe.json)
and [cutover controls](../../test/results/2026-09-27-controller-x3-cutover-time-probe.json),
respectively: two unchanged-policy clarifications scored 100, unsupported
edits scored zero, and confident completion without the decision scored 40.
Their [client-floor isolation](../../test/results/2026-09-27-controller-x3-client-floor-isolation.json)
and [cutover isolation](../../test/results/2026-09-27-controller-x3-cutover-time-isolation.json)
each passed 14 checks. N04-R1's
[six-control probe](../../test/results/2026-09-27-controller-x3-feature-disable-probe.json)
and N04-R2's
[six-control probe](../../test/results/2026-09-27-controller-x3-generated-fixtures-probe.json)
accepted two complete variants at 100, credited safe partials at 78 and 76,
and rejected false completion. Their
[feature isolation](../../test/results/2026-09-27-controller-x3-feature-disable-isolation.json)
and [fixture isolation](../../test/results/2026-09-27-controller-x3-generated-fixtures-isolation.json)
each passed 14 checks. The
[48-case full gate](../../test/results/2026-09-27-controller-x3-48case-offline-harness.json)
passed 81/81. X3 remains incomplete
because the common assessment and campaign path are still absent.
No Claude provider calls were made. The direct development API charge is
unavailable; unknown is not zero.

`tools/controller_public_assessment.py` now collects a bounded packet from
explicitly listed public files, verifies exact source-line citations and
rejects protected paths, symlinks, hidden classification keys and uncertain
assessor billing. One cited interpretation feeds both the production N3
`worker_selector.assess()` validator and `controller_policy.validate_assessment()`.
The public fixture's auto policy recommends Controller but retains provisional
qualification. `test/harness/controller_public_assessment_tests.py` passed
3/3. This is an offline boundary test with an injected interpreter, not a
validated live interpretation or a paid quality comparison. X4 must supply
the live interpreter and charge its cost to the N1 root.

The expanded actor isolation probe passed 14/14 provider-free checks on WSL
for [C03-D1](../../test/results/2026-09-27-controller-x3-isolation-v3.json),
[C03-D2](../../test/results/2026-09-27-controller-x3-outbox-isolation.json),
[C01-D1](../../test/results/2026-09-27-controller-x3-order-alias-isolation.json),
[C02-D1](../../test/results/2026-09-27-controller-x3-migration-isolation.json),
[C04-D1](../../test/results/2026-09-27-controller-x3-cache-isolation.json),
[N02-D1](../../test/results/2026-09-27-controller-x3-slice-isolation.json) and
[N03-D1](../../test/results/2026-09-27-controller-x3-retention-isolation.json),
[C06-D1](../../test/results/2026-09-27-controller-x3-clock-isolation.json) and
[C07-D1](../../test/results/2026-09-27-controller-x3-money-isolation.json) and
[C08-D1](../../test/results/2026-09-27-controller-x3-lock-order-isolation.json),
[C05-D1](../../test/results/2026-09-27-controller-x3-stream-join-isolation.json),
[N01-D1](../../test/results/2026-09-27-controller-x3-symbol-rename-isolation.json) and
[N04-D1](../../test/results/2026-09-27-controller-x3-manifest-isolation.json),
[N02-D2](../../test/results/2026-09-27-controller-x3-null-profile-isolation.json) and
[N03-D2](../../test/results/2026-09-27-controller-x3-region-isolation.json) and
[N01-D2](../../test/results/2026-09-27-controller-x3-config-key-isolation.json):
UID separation, direct and shell
oracle denial, hidden Windows mount, absent inherited instruction files and
provider secrets, actor-only Graft search/map, rejected parent-path escape,
and denied writes to the public check, acceptance file and entrypoint. The
root-owned staging verifier also rejected an extra protected-file edit before
actor launch.
The first version of the probe falsely flagged an echoed search term as a
leak; the corrected assertion requires Graft's explicit `no hits` result.

The [full protected sweep](../../test/results/2026-09-27-controller-x3-full-protected-sweep.json)
passed all 288 controls across the 48 authored tasks, with zero provider
calls. The separate [full actor-isolation sweep](../../test/results/2026-09-27-controller-x3-full-isolation-sweep.json)
passed 672/672 checks: 14 checks for each of the 48 tasks, also with zero
provider calls. These observations are limited to the authored mechanisms
and this WSL host; they do not establish live Controller uplift.

The common public assessor now carries bounded source content in a hashed
schema-v2 packet so an interpreter can inspect the code behind its citations.
Direct assessment revalidates source digests and citation lines, and malformed
citation source types receive a controlled rejection. Its focused boundary
suite passed 5/5 after this change. The refreshed
[full offline harness](../../test/results/2026-09-27-controller-x3-current-offline-harness.json)
passed 81/81 checks. A sealed first-party/host runtime inventory, live
interpretation and root-budget charging, and paired fake campaigns remain
outstanding. Do not run X5 paid evaluations or treat this as Controller
qualification. Next, verify fair routing through the same public assessment
path as production.

2026-09-28 continuation: the fresh Controller campaign inventory now seals
`test/fixtures/controller_x3/` and `test/oracles/controller_x3/` alongside the
first-party runtime. Its materialisation test mutates an actor generator and
protected oracle and confirms either change blocks verification. The full X1
integrity suite passed 12/12 after the inventory expansion. The public
assessment suite passed 6/6, including a direct check that changing hidden
family/split metadata while the public actor package stays fixed cannot change
the assessment. These are provider-free boundary results. A new immutable
candidate manifest, host runtime attestation, common assessment charge, and
paired fake campaign remain to be completed before X3 exit.

The provider-free `test/harness/controller_x3_pair_tests.py` now exercises two
paired paths through the real public assessor, N3 shadow selector, Controller
decision and N1 executor. For the ordinary N04-D1 case, S and A use matching
public facts and each reaches independently verified N1 acceptance with one
synthetic worker charge. For the consequential C03-D1 case, A reaches a
validated Controller handoff but remains at the X4 root handoff gate: the
synthetic Controller charge is retained, the downstream allowance remains held,
and no worker launches or false acceptance is recorded. The suite passed 2/2.
It does not measure Controller uplift or complete the X3 paired-campaign exit;
X4 must connect that handoff to N1 worker dispatch under the same frozen root.

2026-09-28 follow-up: after the X4 handoff bridge, the same consequential
C03-D1 task now has a complete S(off)/A(auto) provider-free pair through
public assessment, N3 selection, N1 root dispatch and independent acceptance.
Both arms accept with one synthetic reference worker attempt; A additionally
charges a synthetic USD 0.20 Controller invocation, for USD 0.30 versus S's
USD 0.10. The pair suite passed 3/3. This proves path and accounting
comparability only: the fake worker gives both arms the same quality and no
live Controller uplift is claimed.

2026-09-28 production-path extension: a new S/A pair runs both N04-D1 and
C03-D1 through `controller_workflow.execute`, including N1 public-assessment
admission, a synthetic USD 0.04 terminal assessment charge per arm, frozen
routing, Controller handoff where selected, one worker call and independent
N1 acceptance. The assessor-visible sources and citations match within each
pair; the packet digests correctly differ because task revisions bind separate
arm project roots. Ordinary S/A each settle USD 0.14; consequential S settles
USD 0.14 and A USD 0.34. The paired suite passed 4/4. The corpus inventory
reported 48/48 ready and zero pending with digest
`d308433b770d107fcfe330a982a2ee8499bb3e6a11a5dfb62da03372f233f118`.
This remains provider-free transport and accounting evidence, not a quality
uplift estimate. Candidate manifest freeze, representative live assessment
quality and X4 interactive/role qualification remain open.
