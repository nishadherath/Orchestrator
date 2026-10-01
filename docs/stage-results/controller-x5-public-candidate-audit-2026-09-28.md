# X5 provider-free public candidate audit

Date: 2026-09-28 Australia/Sydney. The first pass read the known 24
development `issue.md` files and three public traces (the original C06-D1
trace and X5-only C03-D1/C04-D1 overlays). A second read-only pass used the
refreshed local Graft structural graph to locate the exact C01/C03/C04/C06/C07
baseline files, inspected those public sources and ran three baseline probes.
No protected oracle, reserved task or AI provider was accessed. Graft MCP
still times out at this live session's 60-second limit; CLI retrieval with
`--no-refresh` is a disclosed temporary fallback, not proof of MCP health.

## Eligibility rule before routing is observed

A Controller-suitable task needs a consequential *unresolved* premise or
competing material causes, a reproducible public observation that separates
them, and an investigation whose answer changes the repair or safety check.
Complex code, several modules, or an incident narrative alone are
insufficient. A task with a specified cause and fix is a worker control; a
task requiring an unavailable product decision is a clarification control.
These labels describe the public task, not what the current router outputs.

| Public family | Development tasks | Issue-text assessment before new overlays |
| --- | --- | --- |
| C01 | D1, D2 | D1 blames queue reorder but supplies alias rules; a new observed trace would be needed to leave materially competing causes. D2 states a composite-key collision and repair. |
| C02 | D1, D2 | Both specify migration/envelope repair rules; no competing live premise is documented. |
| C03 | D1, D2 | D1's X5 overlay has a reproduced same-key committed retry that contradicts the support diagnosis; v3 auto-selected Controller. D2 specifies the lease race and fencing repair; v3 correctly selected worker. |
| C04 | D1, D2 | D1's X5 overlay has a reproduced cross-tenant warm-cache leak that contradicts support's backend diagnosis; unassessed. D2 specifies request-context preservation on retries. |
| C05 | D1, D2 | Both specify the required bounded-streaming or page-fetch repair. Difficulty alone does not warrant Controller. |
| C06 | D1, D2 | D1 has a public trace contradicting database saturation, but the issue itself announces the clock cause and server-time fix. Rewrite would be needed to retain genuine uncertainty; unassessed. D2 specifies queue-slot scheduling. |
| C07 | D1, D2 | Both specify the exact rounding or timezone rule. A financial discrepancy might become a candidate only with a reproduced trace and unresolved materially different causes; no such trace exists yet. |
| C08 | D1, D2 | Both contain unresolved authority/contract conflicts that require a human decision; clarification controls, not automatic Controller-repair candidates. |
| N01–N04 | Eight tasks | Ordinary repairs, missing-decision controls and established procedures. These support false-positive and clarification checks. |

The current public corpus therefore does **not** already contain four
well-supported Controller-suitable development tasks. C03-D1 has one live
Controller admission, but its source header says every committed retry
charges again. C04-D1's source header says cache keys omit the tenant.
C01-D1, C06-D1 and C07-D1 likewise announce raw-ID equality, worker-local
lease time and per-line/binary-float aggregation in their source comments.
Their faults are inspectable without a multi-hypothesis investigation. The
v3 four-of-four failure is consistent with this audit. It would be unsound
to lower the frozen v3 threshold or to modify the router so that C03-D2
invokes Controller. C03-D1's routing decision proves automatic invocation,
not that its added cost improved task quality.

The [provider-free baseline probe]
(../../test/results/2026-09-28-controller-x5-candidate-baseline-probe.json)
binds public source hashes and reproduces three behaviors: C01-D1 leaves
both differently formatted same-account and other-account orders pending;
C06-D1 uses worker clocks, expiring `w-east` while renewing `w-slow` despite
the opposite server-time relation; C07-D1 returns ledger `0.00` and
statement `0.01` for two `0.005` amounts. These are useful task facts, but
they do not by themselves establish material uncertainty or Controller value.

For a new prospective development screen, do not merely relabel or add
`trace.json` to these simple actors. Design genuinely competing public
failure hypotheses, remove diagnosis leakage from both issue and source,
and make the actor require discriminating checks before a consequential
repair. This can be done with new X5-only synthetic actors or suitable
open-source cases, while keeping X3's original fixtures and protected
oracles untouched. Publish baseline inputs/outputs, independent acceptance
and exclusion criteria, then freeze the task set and dated spend notice.
Reject any candidate whose repair is already determined by public text.
Do not spend on a new screen until the pending programme decision is
resolved.

The [prospective redesign brief](controller-x5-redesign-brief-2026-09-28.md)
specifies four X5-only multi-hypothesis actors, ordinary/clarification
controls and the frozen quality and cost gates. It is a proposal, not a
campaign manifest.

This audit covers public prose, public code and observed baseline behavior.
It does not adjudicate Controller quality. X5 remains development tuning; an
independent reserved comparison and X7 adjudication would still be required
for any shipping change. A fresh session is still needed for working Graft
MCP and for full source-index freshness at its configured 180-second limit.
