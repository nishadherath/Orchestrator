# Portable Graft setup and repair skill

This source package updates the existing `graft-setup` skill for the installed
Graft 0.21.1 and generalises the structural retrieval repair into configurable
Python helpers. It is independent of Orchestrator's consumer bundle and its
machine-specific Graft launchers. The skill is version 1.0.3.

## Contents and installation

- `graft-setup/` is the complete installable skill and authoritative source.
- `tests/` exercises successful and adverse helper behaviour in isolated roots.
- `build_package.py` makes a deterministic ZIP and SHA-256 manifest from an
  explicit file allowlist; no cache or local configuration enters the archive.
- `releases/` contains the tracked redistributable ZIP and integrity manifest.
- `verification.json` records tested environments, outcomes and limitations.

Extract the release ZIP to a temporary directory, verify its manifest and copy
the whole `graft-setup/` folder into the receiving host's skill directory.
Back up an existing installation and preserve unrelated local customisations.
See the skill's [installation reference](graft-setup/references/installation.md)
for prerequisites and commands, and [SKILL.md](graft-setup/SKILL.md) for usage.

The scripts require Python 3.12 or newer, use its standard library, and request
no model API calls. Graft/Node must be installed separately. Diagnostics do not
provision credentials, install dependencies or rewrite host registrations.
Upstream Graft can perform startup upkeep/update checks; these helpers are not
a general network or filesystem isolation mechanism.

## Build and test

From this package directory:

```sh
python -m unittest discover -s tests -v
python tests/integration.py --launcher-json '["node","/absolute/path/to/graft/dist/cli.js"]'
python build_package.py
python build_package.py --check
```

The offline suite uses a controlled fake CLI to test failures and invariants;
it does not substitute for the real-Graft integration run. The integration
runner creates isolated repositories, runs source scoping and MCP probes and
removes only its own temporary workspace. It accepts `--parent` for a host
whose default temporary directory is restricted. Neither suite makes a paid
provider request. Run filesystem-mutating tests in a permitted normal shell.

For native POSIX acceptance, run with native Python and Node. Supply `--node`
when Node is outside PATH and use that same executable as the first launcher
argument. The runner records Node's platform and rejects Windows shims inside
WSL. See [WSL diagnostics](graft-setup/references/hosts.md#wsl-startup-and-native-posix-verification)
for the separate VM startup boundary and bounded recovery checks.

Validate skill frontmatter with the host's skill-creator validator when
available. The release builder also checks the required frontmatter, internal
reference links and file allowlist. Changing source requires rebuilding the
archive; `--check` detects stale release bytes or manifests.

## Design and limitations

The refresh helper stages a copy or clean graph, verifies scope and structure,
preserves the prior active cache and publishes by local rename. It retains the
host-wiring stamp even on a clean build, to avoid unintended startup defaults.
See [the repair contract](graft-setup/references/repair.md) for ignore/settings
side effects, concurrency assumptions, rollback and cleanup limits.

The original project's oversized mixed index, filesystem restrictions and
stale optional meanings were distinct failures. Scope reduction contributed
to successful retrieval; variable freshness latency remains. This package
neither promises a universal speedup nor fixes that historical provider issue.
It preserves authorisation boundaries for any later paid deep pass.

Licensing follows this repository's Apache-2.0 licence, included with the skill.
Graft is a separate upstream dependency and is not bundled or relicensed here.

## Version 1.0.1 verification, 2026-10-14

Version 1.0.1 passed 19 offline tests on Windows and 19 on native WSL/Linux
Python 3.14.7. Real Graft 0.21.1 passed 14 Windows acceptance steps and 13 Linux
steps with native Node 22.23.0. Linux acceptance covers 12 source/MCP scenarios
and one unsupported-option refusal, including retained scope, separate caches,
clean replacement and actual automatic source addition/removal. The npm Linux
build lacks `--structured`; that run verified its safe refusal. Both report
0.21.1, so capability checks remain necessary.

The historical WSL startup timeout was no longer reproducible on the first
probe. After resetting the idle shared VM, three bounded cold starts passed in
6.7-6.9 seconds. Its root cause and permanent prevention are not established.
The missing native runtime and inherited Windows shim were corrected using an
isolated Linux installation; no VM configuration or Windows runtime was changed.

The same 1.0.1 archive passed deterministic checks on Windows and Linux, and
all 13 installed skill files match the source. Detailed results, the initial
POSIX capability failure and SHA-256 evidence are in [verification.json](verification.json)
and `test-results/`. The original 1.0.0 release remains available for comparison.

## Version 1.0.2 build provenance

The [investigation](PROVENANCE.md) established that the Windows global install
contains the operator's local fork output: all 739 compiled files match.
The Linux install matches all 620 published npm files. The fork's sync preserves
package metadata at version 0.21.1, which explains the identical version labels.
The published CLI lacks the extra flags on Windows too. An isolated copy of the
fork passed all 14 native Linux acceptance steps, including structured Markdown.

Diagnostics now report CLI/package digests, resolved paths and optional flags.
These identify the selected entry; full archive provenance remains a separate
comparison. The intentional fork and active Graft installations are preserved.
The package's verification record includes the regression suite, both builds,
the control probes, retained initial failures and the 1.0.2 release manifest.

All 20 offline tests passed on Windows and native Linux. The Linux suite used
byte-identical source on the native filesystem with its original deadlines;
two runs from mounted Windows source hit timeouts, and both failure logs remain.
The underlying mounted-filesystem stalls were not repaired or fully diagnosed
by that build-provenance investigation; the separate 1.0.3 work is documented
in [the mounted-filesystem report](MOUNTED-FILESYSTEM.md).

## Version 1.0.3 mounted-project verification

WSL now uses the backed-up, experimental VirtioFS setting on the tested host.
The project remains Windows-mounted. Two runs passed all 22 offline tests with
mounted helper source and fixtures, at unchanged deadlines. Real fork Graft
passed 14 mounted-project acceptance steps; the published build passed 13,
including safe refusal of its unsupported structured option. Cross-host edit,
atomic replacement, creation and deletion checks passed. The setting survived
two cold starts; Windows regressions and archive parity also passed.

Diagnostics report the actual project mount type. The skill explains a reviewed
transport trial and rollback; it does not set WSL configuration on other hosts.
The old spikes were intermittent and were not reproduced in the serial baseline.
The recorded results qualify this remediation, not an internal kernel diagnosis
or a universal latency guarantee.

The helper also eliminates duplicate symbol-path resolution: diagnostics on
the actual mounted index improved from 30.560 to 2.266 seconds while retaining
escape checks. A separate explicitly scoped native project cache passed fresh
structure checks; the original Windows cache was preserved.
