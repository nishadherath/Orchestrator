# Portable Graft setup and repair skill

This source package updates the existing `graft-setup` skill for the installed
Graft 0.21.1 and generalises the structural retrieval repair into configurable
Python helpers. It is independent of Orchestrator's consumer bundle and its
machine-specific Graft launchers. The skill is version 1.0.0.

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
