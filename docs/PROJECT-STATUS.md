# Project status

Updated: 2026-10-13, Australia/Sydney. Status: assessment and Graft retrieval
repair scopes complete.

## Completed work

- Analysed the full project and saved
  [the assessment and staged recommendations](PROJECT-ASSESSMENT-2026-10-13.md).
- Recorded the operator's UI/UX and Apps choices and autonomous continuation
  within agreed scope in [standing preferences](OPERATOR-PREFERENCES.md).
- Linked preferences and this live status from both project startup files.
- Updated consumer source instructions and regenerated the bundle through the
  normal checked builder. Runtime Python and the shipping policy are unchanged.
- Reviewed the final scope and retained successful and failed verification logs.
  The Git commit containing this record records task completion.
- Repaired everyday Graft retrieval with a scoped structural index and a
  repeatable local refresh helper. Preserved the old semantic cache and added
  a separate, opt-in evaluation-corpus index. See [the runbook](GRAFT.md) and
  [verified findings](FINDINGS.md#graft-retrieval-repair-2026-10-13).

## Verification

- Normal-host `tools/build_dist.py`: PASS, approximately 24 minutes, with the
  existing full offline harness gate and its documented pre-build exceptions.
- Post-build distribution parity: PASS, 85 files match planned output.
- Post-build release mechanical checks: PASS; clean stamping and publication
  remain separate operator actions.
- Context contract: PASS, all six tests. Prose: PASS, 925 authored files.
- Historical frozen RC archive SHA-256 matches its recorded value.
- Results: [verification record](../test/results/2026-10-13-project-assessment-verification.json)
  and [build log](../test/results/2026-10-13-project-assessment-build.log).
- The initial restricted-shell X0 timeout is retained in the failure log.
  Normal-host isolated X0 passed 6/6 in 11.4 seconds; no gate was weakened.
- Graft repair: fresh MCP processes for both configured launchers passed source
  retrieval. All six tools, edit detection, automatic refresh, deletion and
  retained scope passed. The relevant offline harness checks passed on the
  normal host; the full harness was not rerun for this local setup change.
- Repair evidence: [MCP verification](../test/results/2026-10-13-graft-mcp-verification.json)
  and [offline checks](../test/results/2026-10-13-graft-offline-normal.json).
- The live commit-time freshness recheck passed in 111.939 seconds. Its latency
  remains variable; this result is below the existing 180-second timeout.

## Current and remaining work

No implementation stage is running. Remaining work in the agreed assessment
and Graft retrieval repair scopes: none. Remaining-time estimate for those
scopes: zero after delivery. The commit containing this record includes the
Graft retrieval repair and its verification evidence.
No session/model switch, agent launch or new experimental provider call occurred.
Actual development-session API-equivalent cost is unavailable, not zero.

The recommended next scope is instruction-history cleanup, followed by the
existing O0-O6 offline qualification plan. These remain recommendations; the
Graft repair did not start them. The report contains model
assignments, dependencies, blast radius and dated cost/time assumptions.

## Product baseline and unresolved limits

B0 remains default. Controller remains experimental with no established uplift.
O0-O6 is planned and has not started. Publication is not established here.
The frozen RC remains `2026-10-02-f9f141c`; this task generated the distinct
working bundle `2026-10-13-82a077a-dirty`.

Graft MCP structural retrieval is repaired. The core index covers 346 Python
files with 3,948 nodes and 12,453 edges; evaluation source uses a separate local
index. The active index has no semantic tier, and the old stale semantic cache
is preserved. Its historical paid-summary failure remains unresolved. No paid
deep pass was run. General host isolation,
live managed children and served effort are not newly qualified by these checks.
