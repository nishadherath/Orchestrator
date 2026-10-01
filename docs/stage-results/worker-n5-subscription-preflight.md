# N5 subscription preflight, 2026-09-25

Status: **subscription sentinel and approved screen complete**. The
operator requires Claude Code's Claude.ai Max login inside Kali WSL rather than
an Anthropic API key. The shipping B0 router and redistributable are unchanged.

The root-owned credential handoff copies a fresh WSL login into a private
per-invocation directory, binds it outside the actor tree, and serialises
use so a stopped invocation can commit a refreshed token without racing a
second worker. The worker runs as UID 65534 with only the fixed Read/Edit/
Write/Glob/Grep and Graft retrieval surface. Restricted file tools and
explicit deny rules block the auth mount. The credential is absent from the
actor package, Windows transport environment and generated distribution.

Provider-free evidence: the N4 WSL host attestation has been extended from
51 to 55 checks, including isolated public verification. Its current digest
must be read from `test/results/2026-09-24-worker-n4-wsl-host.json` after the
final bundle rebuild and attestation refresh; earlier digests are stale.
The renewed isolated subscription status attestation passed eight checks.
Eleven root credential-store tests pass, including token
refresh commit, interruption blocking, empty-copy discard and expiry refusal.

The first bounded Sonnet-low Read-denial sentinel was attempted. Claude Code
returned a `<synthetic>` response with zero input/output tokens and USD 0
reported API-equivalent cost. It made no observable Read call and served no
model. The per-invocation credential's two token fields were empty afterward;
the root store rejected them and preserved its master. Inspection showed the
Windows and WSL access tokens had expired, though their refresh tokens had
not. The failed private copy was verified empty and discarded. This is
consistent with a headless refresh failure, but the exact cause is unproven.
The handoff now rejects access and refresh tokens with less than five minutes
of stated validity before launching an actor. No screen call or N6 reserved
task had run at that point.

After a fresh Claude.ai browser login, `worker_wsl_sync_login.ps1` promoted
the WSL credential into the root master and updated the ignored backup with
its ACL unchanged. WSL Claude Code reported a Max subscription and the
private-store freshness check passed. The second bounded sentinel **passed**
all seven checks: one denied Read attempt, served `claude-sonnet-5`, requested
low effort and unchanged actor. Claude Code reported **USD 0.053081
API-equivalent cost** with 11,277 cache-creation, 21,880 cache-read, six other
input and 247 output tokens. The master, WSL user copy and ignored backup
matched by digest afterward. This probe establishes one access boundary and
one served cell, not the full fifteen-cell screen.

The N5 public acceptance bridge now runs `public_check.py` in a fresh,
credential-free WSL copy of the stopped actor. The 55-check host probe covers
the Windows bridge, evaluator read denial, source preservation and rejection
of a self-modifying check. Focused acceptance tests cover evidence binding,
timeout blocking and refusal to reuse local command evidence as isolated
evidence. The live development runner has not yet been implemented; these
checks establish the verifier path, not an episode campaign.
The current `TaskExecutor` still dispatches B0 even after `shadow_select()`
records a candidate. N5 must add and test explicit experimental arm dispatch
before candidate or alternative development episodes can be validly compared.

While the first browser sign-in was pending, Claude Code emptied both token
fields in the WSL user's copy. The checked helper rejected that intermediate
state without writing the backup. A new login through Claude.ai email
verification completed, and the helper's successful renewal path was verified.

The [dated screen spend notice](worker-n5-screen-spend-notice-2026-09-25.md)
and [current 60-row manifest](../../test/results/2026-09-25-worker-n5-screen-manifest.json)
were prepared, validated against the live host and approved by the operator
for the exact digest
`1dbb33f603f756998e30c48346b89b3359de0330b78c70c4a49bc33b9e065e94`.
The [approval record](../../test/results/2026-09-25-worker-n5-screen-approval.json)
authorises USD 48.75 in local admission allocations, which is not a provider
bill cap. The [live screen checkpoint](../../test/results/2026-09-25-worker-n5-screen-run/campaign.json)
is complete with all 60 calls settled. The [screen result](worker-n5-screen-2026-09-25.md)
records USD 7.410898 provider-reported API-equivalent usage. N6 reserved tasks
remain closed.

Verification on this Windows host: the focused N5 manifest tests passed 6/6,
the live screen driver tests passed 8/8 without provider traffic, the sentinel
parser and sealed-evidence tests passed 4/4, and
`release_check.py` found all 75 distribution files source-equivalent with no
mechanical failure. The complete offline harness **passed 61/61** in 476.7
seconds with normal host permissions on the rebuilt tree. The bundle rebuild
also passed its pre-build harness gate, excluding only the expected pre-build
bundle parity checks. The post-build release check passed source equivalence,
generated workers, sensitive-material and licence checks. A restricted-sandbox run failed its
N4 fake-campaign call-count assertion (`24 != 72`), real-world grader check,
and compaction benchmark `uv` spawn; those failures did not reproduce in the
clean host run. No offline check establishes that N5 live dispatch works.
