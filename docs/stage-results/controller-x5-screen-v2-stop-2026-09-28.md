# X5 v2 host canary stopped before provider launch

Date: 2026-09-28 Australia/Sydney. The v2 manifest is
`d5b8c015f2945518f9d806de9b03b0ea7b6ca197a8c84d6edbdf0600296652c2`.
The six public assessment actors were prepared, but **none was assessed**.
One separate Sonnet High host canary was attempted on C03-D1. Its adapter
returned an incomplete receipt with no terminal provider event or cost.
The canary ledger retains its USD 1.00 local hold as `uncertain`; it was not
replayed. The v1 settled assessment remains USD 0.0330442 separately.

The Q1 stage record exists for actor
`q1-a4cbcbe94af591785346d440ac2bbc62`, but its root-owned Q1 launch
`start` and `stop` records are absent. The installed Q3 namespace launcher
checks the whole command before starting the Q1 launch and accepts Sonnet
Low or Opus High only. The v2 adapter advertised Sonnet High while still
calling that launcher. This exactly explains the prelaunch rejection. No
Claude Code process or credential issue is evidenced for this canary; its
provider cost is **unreported**, not recorded as zero in the ledger. The
record and hold remain available for manual reconciliation. The v2
manifest and prepared actors are historical evidence, not valid v3 roots.
The later [read-only prelaunch proof]
(controller-x5-v2-prelaunch-proof-2026-09-28.md) also checks the frozen
source and installed launcher hash, launcher age and absent auth session;
it supports zero provider invocations while leaving the ledger hold intact.

The prior Q4R launcher already admits the three N3 cells and requires a
schema-bound report. Its installed and source SHA-256 both equal
`3d6137654b6a9121f81651fa5a917f525ee384863f4075edac2afb4913e08b4e`.
The new X5 adapter pins that installed launcher and schema to the source
package. A provider-free capability check passed for Sonnet High with
isolation and budget enforcement. A new single-use v3 manifest, actor and
spend notice are required before another canary or assessment.

The v2 driver, adapter and canary source snapshots are under `test/results/`
with `-v2-source.py` suffixes. These snapshots preserve the failure even
though the active X5 files advance to v3.
