# Diagnose the failure class

| Observation | Next discriminating check | Repair supported by that evidence |
| :--- | :--- | :--- |
| Executable cannot start | Resolve the actual Node/CLI or native launcher; inspect host startup logs | Correct only the selected server's launcher/root |
| Server initialises, tool call times out | Measure freshness separately from lookup; inspect graph file groups and repeated refresh | Select relevant source scope, align extractor identities, then retest |
| Graph points outside the current checkout | Check root, worktree and indexed paths | Build a cache for this checkout; correct project-local root binding |
| Build fails on atomic rename or permission | Test the same bounded build in the appropriate normal host environment | Preserve cache, use the host permission mechanism; retain the failed result |
| Structure is fresh but meanings are stale | Inspect semantic state and previous deep-pass errors | Preserve meanings or choose an explicit structural-only fallback; investigate provider separately |
| Every lookup rebuilds | Compare selected launcher and fingerprint/extractor identities; inspect missing sidecars | Use matching executables and regenerate verified fingerprints |
| Same version exposes different flags | Compare entry digests, package provenance and actual help; inspect local fork syncs | Select the intended build and test its capabilities; preserve an intentional fork |
| WSL mounted files intermittently stall | Inspect actual transport; compare metadata, reads and runtime startup with native controls | Review a backed-up transport change when supported, then verify mounted source and caches at unchanged deadlines |
| No files are indexed | Check source prefixes, Git visibility, skip names and parser support | Correct scope or include a real skipped source directory; do not label an empty graph healthy |

## Diagnostic and refresh contracts

`diagnose.py` reads cache metadata and invokes only version/help by default.
It records build flags and, for a directly resolved Graft entry, local CLI and
package JSON digests. `version_matches` compares only the reported label.
Entry digests do not attest the whole installation; wrappers can remain unknown.
Graph path safety is checked for every distinct indexed path once per snapshot,
so many symbols in one file do not multiply mounted-filesystem resolution work.
`--check` adds bounded structural re-extraction. It does not start MCP or
rebuild the cache. The report identifies missing meanings independently of
structural freshness. Graph layouts outside the tested contract produce a
failure instead of an invented successful result.

`refresh.py` requires either repeated `--only-dir` or explicit `--whole-repo`.
It rejects home/filesystem roots, traversal, escaped source/cache paths and
replacement of a non-empty arbitrary directory. Symlinked/junction caches
require manual inspection. The script does not follow them for replacement.

Builds occur under `.graft/staging-<unique-id>`. A normal refresh reuses a copy
of the existing cache; `--clean` keeps only the wiring stamp. The original
cache stays active until the staged graph has real files, the intended
fingerprint scope and a fresh structure. Semantic drift is reported separately.
Successful publication renames the original into `.graft/backups/`, then moves
the staged graph into place. If publication fails, the helper tries to restore
the original. Inspect the preserved backup if the host also blocks restoration.
Backups are not deleted automatically; choose retention after reviewing them.

The helper writes `.gitignore` entries for `.graft/` and the selected cache.
An explicitly requested include/structured option may update Graft's local
`.graft/config.json`; existing unrelated options are left to Graft's merge.
Staged build failure leaves the active cache intact but can leave these local
settings/ignore entries changed. This is not a transaction over the entire repo.
Full `.ignore` overrides, global configuration and credentials are untouched.

Close or pause automatic MCP/hook refresh during replacement. The helper lock
coordinates these scripts, not every upstream process. Native refresh locks
are checked before copying and publishing. Never remove a lock merely because
it inconveniences the repair; verify its owner and stale state first.

Run `--dry-run` to validate scope and print the plan. Version/help are still
executed, but no project files are written by the helper unless an `--output`
report was explicitly requested. The helper never invokes `init` or `--deep`.
It disables child-process telemetry through `DO_NOT_TRACK`, without changing
the user's persistent telemetry preference. Upstream startup/update behaviour
is not a general network or filesystem sandbox.

## MCP acceptance and cleanup

`probe_mcp.py` requires an indexed file, a definition name and a literal in that
definition. It uses a fresh explicitly rooted process, drains stderr, bounds
each JSON-RPC request and rejects malformed/oversized protocol lines. Reports
contain outcomes and timings, not raw source replies or stderr.

Default snapshot mode sets `GRAFT_NO_REFRESH=1` only in the child. It checks
freshness and source evidence without repairing drift automatically.
`--exercise-refresh DIR` enables upstream refresh, creates one unique Python
file in a recorded indexed directory, verifies addition, removes that exact
file, verifies removal from graph nodes, checks scope and checks freshness.
It changes the selected cache. It never modifies an existing source file.

If the probe fails during addition, it still attempts deletion and graph
refresh. If that refresh also fails, the unique source file is removed but
its index entry may remain. Rerun a scoped refresh and final freshness before
claiming completion. A killed process can leave its temporary file; use the
reported `graft_skill_probe_*.py` name and inspect ownership before cleanup.

`--allow-startup-upkeep` acknowledges a prior review of Graft-managed wiring.
It is not authority to change unrelated host settings. The skill must use the
operator's existing authorisation or obtain it for the actual affected scope.

## Interpreting results

Report structural and semantic health separately. A deliberately absent meaning
tier is a supported fallback, not a successful paid refresh. Single timings
are observations, not a guaranteed performance claim. Cache scoping contributed
to the original project's repair, but the complete historical timeout cause
was not isolated. Its historical semantic-provider failure was not fixed.
