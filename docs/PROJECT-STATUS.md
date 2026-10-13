# Project status

Updated: 2026-10-14, Australia/Sydney. Status: assessment and Graft retrieval
repair scopes complete.
The separately requested portable Graft skill package is also complete.

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
- Updated the installed `graft-setup` skill for Graft 0.21.1 and created the
  independent [portable skill source package](../packages/graft-setup/README.md),
  including bounded diagnostic/refresh/MCP scripts, documentation, tests,
  licensing and a deterministic redistributable ZIP with an integrity manifest.
  The old installed skill is preserved in the ignored local backup area.
- Recovered and verified WSL startup with three bounded cold starts after an
  idle VM reset. Installed an isolated native Linux runtime and verified the
  skill against real npm-distributed Graft 0.21.1. Updated the package and
  installed skill to 1.0.1, including WSL guidance and platform identity checks.
- Established the cause of Graft's same-version capability mismatch: Windows
  uses locally synced fork output while Linux uses the published npm archive.
  Updated the installed skill and package to 1.0.2 with build identity diagnostics
  and [the provenance investigation](../packages/graft-setup/PROVENANCE.md).

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
- Portable skill 1.0.2: 20 offline tests passed on Windows and 20 on native
  WSL/Linux Python. The Linux suite used byte-identical source on the native
  filesystem at unchanged deadlines after mounted-source timeout failures.
  Real Windows fork Graft 0.21.1 passed 14 acceptance steps; the published
  Linux package passed 12 source/MCP scenarios and one unsupported-option refusal.
  An isolated Linux fork snapshot passed 14 steps, including structured Markdown.
  Stock skill validation, 13-file installed parity and identical deterministic
  archive checks on Windows and Linux passed. Results and limits are in
  [package verification](../packages/graft-setup/verification.json).
- Build provenance: all 620 published Linux package members match the verified
  npm archive; all 739 Windows compiled files match the fork's built output.
  The published CLI on Windows also lacks the optional flags. An isolated fork
  snapshot passed all 14 native Linux acceptance steps, including structured
  Markdown. Active Graft installs and fork source were preserved.

## Current and remaining work

No implementation stage is running. The requested portable Graft skill is
installed, packaged and included in the commit containing this record. Remaining
work in that scope: none; remaining-time estimate is zero after delivery.
No consumer bundle implementation or O0-O6 stage has started.

Remaining work in the prior assessment and Graft retrieval repair scopes: none.
The earlier commit includes the retrieval repair and its verification evidence.
No session/model switch, agent launch or new experimental provider call occurred.
Actual development-session API-equivalent cost is unavailable, not zero.

The 2026-10-14 WSL verification scope is complete. The startup timeout had
already disappeared before intervention; three post-reset cold starts passed
in 6.7-6.9 seconds. Its root cause and permanent prevention remain unproven.
The separate native-runtime gap was corrected without changing VM settings.
The same-version capability investigation is also complete. The fork's compiled
output replaces npm `dist/` while preserving package version metadata; the
observed capability difference is explained. The 1.0.2 package preserves the
intentional fork and records build identity rather than equalising installations.

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
