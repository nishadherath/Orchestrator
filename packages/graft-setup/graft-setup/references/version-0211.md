# Installed Graft 0.21.1: verified behaviour

Verified on 2026-10-13 using the installed package's CLI help and implementation,
then exercised against isolated repositories on Windows and, on 2026-10-14,
native WSL/Linux Node. These are version-specific notes;
read the current CLI help after changing installations. The existing Windows
installation carries a local fork's compiled output; Linux initially used the
published npm package. Both report 0.21.1. Their optional capability difference
comes from build contents, rather than the operating system.

- `build` produces the local wiring graph and cards without an LLM call.
  `--deep` separately requests concept reads/synthesis and symbol meanings.
- `--only-dir` is repeatable. Its source prefixes live in graph fingerprints.
  Automatic query refresh preserves them. A bare manual build can widen the
  graph; every scripted/manual refresh should pass its intended scope explicitly.
- `--include-dir` takes a bare directory name, not a path. Overrides live in
  `.graft/config.json`. They lift Graft's skip policy, not Git ignore rules.
- The tested local fork's skip set contains `node_modules`, `dist`, `build`, `_build`,
  `out`, `target`, `vendor`, `coverage`, `__pycache__` and `venv`. It does not
  contain `tools`. Ordinary dot directories remain excluded. Structured mode
  narrowly admits workflow YAML under `.github/workflows`.
- Git-visible files are preferred when Git works. Filesystem fallback has
  different ignore behaviour. Keep caches hidden or explicitly outside source
  scope when Git visibility is unavailable.
- Where available, `--structured` admits Markdown, JSON, YAML, TOML and INI and
  is persisted. The local fork also exposes `--documents` and `--deep-documents`.
  The published npm 0.21.1 exposes none of these three flags on Windows or Linux.
  The helper rejects `--structured` before project mutation when help lacks
  support. Acceptance tests optional features only when the selected build
  advertises them, otherwise verifying refusal without project mutation.
  Document rendering needs additional upstream dependencies; this package does
  not install or exercise them. The helpers do not request document deep passes.
- `--no-gitignore` and `--no-ignore` prevent build-time ignore-file changes.
  The refresh helper manages narrow `.gitignore` entries itself and leaves
  `.ignore` alone, so an optional corpus does not silently enter broad searches.
- Freshness re-extracts source. Ordinary retrieval first probes fingerprints
  and only structurally rebuilds when needed. A fast query does not imply a
  fast complete freshness check.
- `check --json` reports `context` and `graph`. An absent concept manifest is
  acceptable for a structural-only build. Stale semantic summaries can make
  the overall CLI exit non-zero even when added/removed/changed lists are empty.
  Helpers expose these states separately and never conceal structural drift.
- `graft_check_freshness` may print `graft check: NO GRAPH` for the optional
  concept manifest alongside a healthy wiring result. Its `isError: false`
  alone does not establish freshness; inspect the structural result.
- Extraction/fingerprint sidecars are keyed by extractor identity. Two Graft
  installations can carry different identities even with the same version
  label. Align the host launcher with the build launcher and inspect sidecars
  when every query triggers rebuilding.
- MCP boot invokes Graft upkeep. An old/missing wiring stamp can replay existing
  tool-managed host rules, including previously selected global writes. A clean
  refresh should preserve this stamp; inspect legacy wiring before booting MCP.
  The script's detection covers this tested version, not arbitrary future hosts.
- Global MCP registrations must resolve the active session checkout; never pin
  a machine-global server to one fixed project. An explicit root is appropriate
  for a project-local launcher or a bounded diagnostic process.

Primary upstream project: [NanoNets context-graph-engine](https://github.com/NanoNets/context-graph-engine).
The package does not equate the local fork with a published upstream release.
CLI flags and graph layouts are probed locally; semantics and portability are
covered by the packaged tests and recorded platform evidence.

## Build provenance

Investigation on 2026-10-14 verified the npm 0.21.1 archive's registry SHA-512
integrity and SHA-1. Its metadata records Git head
`375a37e0b6a21d28f12fce2d220d692726bb0730`. The Linux installation matches all
620 published files. Running the same published CLI on Windows also lacks the
three optional flags, isolating package contents from OS behaviour.

The Windows installation instead matches all 739 `dist/` files from the
operator's `fork_graft` checkout at observed head
`d7c656c1f8b4a8101b054593f508405b53c6799d`. That checkout adds the optional
tiers and keeps `package.json` version 0.21.1. Its `scripts/sync-global.mjs`
copies compiled output into an existing npm install, preserves its package
metadata and dependencies, and checks that version labels agree. The CLI reads
that metadata for `--version`. This explains why different code reports the
same label. The checkout head is context for the observed build, not an embedded
or independently stamped build revision.

The published `dist/cli.js` SHA-256 is
`5d744a3aad0bb9580e3ae6ecd9a06c1e818521bb331acb4f457732554bcbf2af`.
The tested fork entry SHA-256 is
`f04afe2f33502213425895e33e55baf5235045270941611ba46fc7e7612e6dfc`.
These are recorded reference bytes, not fingerprints of every installation.
Do not reinstall or overwrite an intentional fork merely to equalise flags.

For another same-version mismatch, diagnose both actual launchers. Helpers
record the resolved CLI/package paths, entry and package JSON SHA-256, and
optional build flags in `capabilities`. A wrapper can leave identity unavailable;
use an explicit Node/CLI launcher to make it observable. These two hashes detect
many substitutions but do not verify every runtime module or dependency.
If release provenance matters, compare all package members against a separately
integrity-verified archive, excluding installed dependencies. Check any local
fork's sync/build instructions and compare its compiled tree. Timestamps and
version labels alone do not establish origin. Diagnose capabilities separately
from archive identity, preserving the operator's intended installation.

Primary publication metadata: [npm Graft 0.21.1](https://registry.npmjs.org/@nanonets/graft/0.21.1).
