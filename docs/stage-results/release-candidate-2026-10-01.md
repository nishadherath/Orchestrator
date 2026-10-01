# Bounded RC result, 2026-10-01

## Disposition

Bounded RC verification is complete: the final full offline harness passed 83/83
checks, and exact-bundle installation, upgrade and rollback passed.
B0 remains the default; Controller remains experimental. Controller uplift is
an explicit unfinished qualification goal and is not a condition silently waived
by this RC. No paid experiment ran during RC work.

This is an unpublished candidate from the existing dirty checkout, not a
clean-source publication. The release checker retains `clean_build_stamp` and
`publication` as operator actions. No commit, tag, remote push or publication
was performed, and local configuration and prior research were preserved.

## Artefact and provenance

| Item | Value |
| :--- | :--- |
| Bundle version | `2026-10-01-15ecf66-dirty` |
| Bundle files | 84 |
| Frozen bundle | `test/results/2026-10-01-rc/orchestrator-rc-df52358a030c8d0f.zip` |
| Bundle SHA-256 | `df52358a030c8d0f5ad70eccb38f3f6f94070014baaa509efda19c148834e1e3` |
| Frozen source inputs | `test/results/2026-10-01-rc/orchestrator-source-3a8e86127cffbd5f.zip` |
| Source archive SHA-256 | `3a8e86127cffbd5fe16c18ae40e80664a4b398d6b74bafa0b6bfd03b35377946` |
| Source inputs | 90 allowlisted files, with per-file hashes |
| Git baseline | `15ecf6621d158299ed278659a769d03729ee50e0` |
| Upgrade baseline bundle | `2026-09-24-0407ce7`, obtained from that Git commit |

The source archive preserves bundle assembly inputs, not the complete research
repository or its offline harness. Pure assembly from those archived inputs
reproduced every bundle byte at the frozen stamp. The ZIP was deterministic on
the recorded Python runtime. Full harness verification runs in the source
checkout. The JSON evidence also binds the verification script and fake-workflow
fixtures by hash. Per-machine settings, credentials, personal ledgers and research
campaign outputs are not consumer payload.

## Changes made for this RC

- Build stamping now stops on unavailable or failed Git inspection. Previously,
  a failed status command could look like a clean tree, and missing revision
  output became a misleading `no-git` stamp.
- The clean-stamp check rejects unknown, arbitrary, dirty and rationale-only
  versions. Four added provenance tests reproduced the old behaviour before
  repair and passed after it; all 12 installer/provenance tests passed.
- Root and consumer documentation now reflects the X4 live integration and X5
  development results, removes stale claims that the handoff bridge is closed,
  and keeps uplift, automatic Controller routing and frontier qualification open.
- The active RC scope is recorded in `docs/RELEASE-CANDIDATE-2026-10-01.md`,
  `CLAUDE.md` and `handoffs/2026-10-01-bounded-rc.md`.

The focused review inspected acceptance freeze, all three Framer correction
entries, public assessment accounting, Controller admission and handoff,
worker receipts, cancellation, continuation, operator controls, model identity
and bundle ownership. It is not an independent security audit. Review coverage
and the distinction between observations and inferences are recorded in the RC
scope document. No B0 policy, worker cell or paid experiment was changed.

## Verification

Commands use the configured Python 3 runtime; this host used the bundled Codex
Python. Normal local subprocess and temporary Git access was required. No global
Git trust setting was changed.

| Command | Observed result |
| :--- | :--- |
| `python test/harness/install_tests.py ProvenanceTests` | 4 tests pass after failing before the fix |
| `python test/harness/install_tests.py` | 12 tests pass in 16.834 seconds |
| `python tools/build_dist.py` | Exit 0 after its full offline gate; 84 files built |
| `python test/results/2026-10-01-rc-freeze.py` | PASS; exact artefact, reproduction and lifecycle checks |
| `python test/harness/check.py --json` | PASS, 83/83 checks on the rebuilt bundle |
| `python tools/release_check.py --json` | Mechanical PASS, with clean stamp and publication still required |

The archive verification exercised both a clean consumer and an upgrade from
the actual prior committed bundle. It checked exact owned-file bytes, repeat
installation as a no-op, installed fake B0/N2/N3/CLI execution, cancellation and
linked continuation, provider-free Controller status, rollback refusal after a
consumer edit, byte-exact restoration and retention of user configuration,
unrelated files and durable task records. Fake managed-child success does not
qualify live managed-child execution.

Evidence:

- `test/results/2026-10-01-rc-build.log`
- `test/results/2026-10-01-rc-freeze.log`
- `test/results/2026-10-01-rc/verification.json`
- `test/results/2026-10-01-rc-final-harness.json`

## Remaining qualification and publication work

Controller uplift remains unproved. Future work needs a sound frozen evaluator,
prospective matched comparisons and independently protected acceptance. Keep
all closed X5 no-replay decisions; H03b's frozen private score remains unavailable.
General filesystem isolation, descendant termination, served effort and frontier
profile suitability remain unqualified. Interactive Agent calls outside the
durable API remain unmanaged. No new live Claude natural-language command test
was performed for this RC.

For publication, review and commit the intended source changes without local
configuration or credentials, rebuild from that clean source commit, verify the
resulting new stamped artefact, and explicitly authorise publication. The frozen
candidate can be evaluated locally without representing it as that later build.

RC provider calls: 0. Paid RC experiment spend: USD 0. Development session cost
is unknown because the active model and billed token/cache usage are not exposed;
it is not represented as zero.
