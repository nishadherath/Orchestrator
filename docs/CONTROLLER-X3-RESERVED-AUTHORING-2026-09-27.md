# X3 reserved corpus authoring brief

Date: 2026-09-27 Australia/Sydney. Status: 6 of 24 reserved cases registered;
18 rows below remain design only. A case is not eligible for a Controller comparison until its actor package,
protected oracle, equivalent repairs, partial and adversarial controls pass
the same isolated checks as the development split.

The 24 frozen IDs and mechanism names come from
`src/controller_evaluation_contract.json`. Each reserved task must use a new
failure mechanism, not a renamed development case. The actor sees its own
public package only. A public smoke check must not reveal the protected
edge case, and a complete-looking report alone must never earn acceptance.
Keep reserved outcomes out of policy selection and prompt tuning. Freeze the
package and source inventory before X6 arm outcomes are observed.

| ID | Actor-visible setting and protected distinction | Useful incomplete control |
| :--- | :--- | :--- |
| C01-R1 | Event replay across two feeds; deduplicate by stream and sequence without merging equal numbers from different feeds. | Fix duplicate delivery within one feed, miss a cross-feed collision. |
| C01-R2 | Search index trails an authoritative row revision after delete and recreate; reconcile by revision, not stale key presence. | Repair update lag but leave recreate stale. |
| C02-R1 | Shadow-column cutover with mixed old/new writes; read precedence and rollback must preserve the latest value. | Make reads use the shadow but lose rollback fallback. |
| C02-R2 | Append-log compaction with tombstones and checkpoint boundaries; preserve final visible state and replayability. | Compact ordinary updates but resurrect a deleted key. |
| C03-R1 | Leased job changes owner; a stale worker's fencing token must not commit after transfer. | Fence stale completion but conservatively block the healthy new owner's completion. This preserves the critical safety invariant while leaving a liveness gap. |
| C03-R2 | Webhook receipts arrive twice or out of order; apply one business effect per delivery identity while retaining separate identities. | Deduplicate exact repeats but merge distinct events. |
| C04-R1 | Report object lookup crosses tenant ownership; deny a guessed object ID while preserving owner access, including archived reports. | Reject cross-tenant IDs but also hide a legitimate owner's archived report. This preserves confidentiality while leaving an availability gap. |
| C04-R2 | A pooled connection carries prior tenant session state; reset at checkout and on error paths. | Reset normal return and quarantine the connection after an exception. This prevents a cross-tenant leak but loses safe recovery and pool capacity. |
| C05-R1 | Producer burst exceeds consumer rate; bound pending batches while retaining order and explicit backpressure. | Bound pending batches conservatively at two even when configured capacity is three. This avoids data loss but rejects work unnecessarily. |
| C05-R2 | A new encoder writes the published two-byte big-endian length header in little-endian order; legacy and current readers must share the published frame. This is distinct from C07-R1's UTF-8 character-count failure. | Restore the big-endian header and nonempty reader paths, but reject a valid empty frame in the current reader. This fails safely without corrupting bytes. |
| C06-R1 | Broad cache eviction causes a load spike; target affected keys and stagger refill without returning stale data. | Limit evictions but leave a hot-key herd. |
| C06-R2 | A partial deploy mixes schema readers and writers; preserve compatibility in both directions until all nodes upgrade. | Make the new reader understand old rows but omit the legacy field from new writes. Old readers reject those writes explicitly, leaving an availability gap without fabricating values. |
| C07-R1 | Length-prefixed transport counts Unicode characters instead of UTF-8 bytes; frame boundaries must survive multiple messages. | Fix byte lengths for a single message but explicitly reject a following frame. This avoids silent corruption while leaving stream support incomplete. |
| C07-R2 | Out-of-order updates advance a transport-sequence watermark incorrectly; use state revision to accept new values and reject late stale ones. | Reject stale revisions but still advance the transport watermark, safely skipping a later valid revision with a lower transport sequence. This differs from delivery-ID deduplication in C03-R2. |
| C08-R1 | Replay must retain order and a bounded live state; neither unlimited buffering nor reordered output is acceptable. | Bound the future-record buffer and preserve order, but fail to drain a buffered record after its gap closes. This loses progress without emitting out of order. |
| C08-R2 | Failover may briefly nominate two writers; enforce one fenced writer without blocking healthy takeover. | Block overlap but prevent takeover after expiry. |
| N01-R1 | Package import path moves; update every active consumer and remove the stale export. | Fix one consumer only. |
| N01-R2 | A generated header is stale after source-schema change; regenerate from source and keep the generator reproducible. | Patch generated output only. |
| N02-R1 | A local threshold comparator excludes the exact boundary. | Fix the boundary but regress neighbouring values. |
| N02-R2 | A mutable default argument carries data between independent calls. | Fix one call path but leave a second shared default. |
| N03-R1 | A change requires a minimum supported client version that the request does not supply. | Name the missing version but make an unsupported edit. |
| N03-R2 | A destructive cutover lacks an approved time; preserve state and ask for the precise decision. | Explain the risk but guess a date. |
| N04-R1 | Follow a supplied feature-disable procedure, preserving audit and unaffected flags. | Disable the feature but omit audit state. |
| N04-R2 | Refresh generated fixtures from their declared source without editing protected generator output by hand. | Update only one generated fixture. |

For every row, author the actor-visible issue, fixed adapter and public check;
an evaluator-only oracle with task-specific behavioural milestones; two
equivalent complete controls; one useful incomplete control; baseline,
confident label copy and a forged-public-output control. Register a distinct
causal-probe rubric. Run six protected WSL controls and the actor/Graft isolation
probe, then record content hashes. The reserved set is not a target for
post-outcome score or routing-policy adjustment.

The table specifies intended test shapes, not verified defects or results.
Its mechanisms can be refined before the corresponding packages are sealed,
provided the frozen family and split remain unchanged and the reserved cases
stay independent of development cases.
