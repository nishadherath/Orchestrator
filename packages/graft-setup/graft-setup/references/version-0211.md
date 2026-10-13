# Installed Graft 0.21.1: verified behaviour

Verified on 2026-10-13 using the installed package's CLI help and implementation,
then exercised against isolated repositories. These are version-specific notes;
read the current CLI help after changing installations.

- `build` produces the local wiring graph and cards without an LLM call.
  `--deep` separately requests concept reads/synthesis and symbol meanings.
- `--only-dir` is repeatable. Its source prefixes live in graph fingerprints.
  Automatic query refresh preserves them. A bare manual build can widen the
  graph; every scripted/manual refresh should pass its intended scope explicitly.
- `--include-dir` takes a bare directory name, not a path. Overrides live in
  `.graft/config.json`. They lift Graft's skip policy, not Git ignore rules.
- The installed skip set contains `node_modules`, `dist`, `build`, `_build`,
  `out`, `target`, `vendor`, `coverage`, `__pycache__` and `venv`. It does not
  contain `tools`. Ordinary dot directories remain excluded. Structured mode
  narrowly admits workflow YAML under `.github/workflows`.
- Git-visible files are preferred when Git works. Filesystem fallback has
  different ignore behaviour. Keep caches hidden or explicitly outside source
  scope when Git visibility is unavailable.
- `--structured` admits Markdown, JSON, YAML, TOML and INI and is persisted.
  The installed help also exposes optional `--documents` and `--deep-documents`.
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
The package does not claim that the installed build matches a particular
upstream commit. CLI flags and graph layouts are probed locally; semantics and
portability are covered by the packaged tests and recorded platform evidence.
