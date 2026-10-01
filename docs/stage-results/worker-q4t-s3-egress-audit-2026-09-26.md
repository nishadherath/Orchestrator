# Q4T S3 prospective screen: provider payload audit

Date: 2026-09-26 UTC. This audit was performed after automatic approval
review stopped the first campaign launch **before execution**. No S3 campaign
directory, provider intent, or provider invocation existed at that point.

The frozen manifest is
`6b5b5d92bab2360494dfc9c7501f4dd7044baec81ec07dc1742f73a46ba263d6`.
Its 18 episodes reuse six actor inventories: five snapshots of public GitHub
projects and one project-authored synthetic task. The upstream projects are
attrs (MIT), pluggy (MIT), sortedcontainers (Apache-2.0), more-itertools
(MIT), and idna (BSD-3-Clause), each at the commit recorded in its
`test/fixtures/worker_q4s_public/S*/provenance.json`. T07 is the authored
`eventbox` regression. The actor inventories total 89 files and 1,000,587
bytes across the six distinct tasks. They contain public source, issue text,
public checks, acceptance JSON, and license files. The protected oracles,
reference overlays, private repository implementation, local configuration,
and saved credentials are not actor files.

`tools/worker_q4t_screen_live.py` copies only each manifest-listed actor file
into a fresh root-owned WSL seed. `tools/worker_wsl_q3_adapter.py` packages
only that allowlisted inventory for the Claude Code actor. The installed Q4T
launcher isolates that actor in a mount namespace, unmounts Windows drives,
and exposes the actor directory and a dedicated Claude.ai subscription
credential session. The actor can send its copied public or synthetic task
content, prompt, edits, and diagnostic metadata to Claude.ai. The credential
itself is needed for authentication and is not an intended task payload.

The frozen inventory reproduced under `tools/worker_q4t_screen_live.py
--check`; the provider-free WSL host proof, authentication probe, and 12-check
capability probe passed. A bounded scan of every inventoried actor file found
no API-key, bearer-token, password/cookie assignment, private-key header, or
local Windows/WSL user path patterns. This scan is an additional signal, not
a proof that arbitrary text cannot be sensitive. The public provenance and
fixed actor-file boundary are the main reason this screen does not require
sending private project source to Claude.ai.

The approved campaign limit remains 18 episodes, 54 Claude Code subscription
calls, and USD 72 in local allocations; the separate API-equivalent planning
range is USD 5–40 over 2–8 hours. No provider call may be replayed after an
uncertain start.
