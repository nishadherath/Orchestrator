# Full-project freshness costs and saved scope

The tested 0.21.1 fork has two distinct causes of unnecessary check work.
Its source enumerator filters `--only-dir` after Git/filesystem enumeration and
metadata calls. A changed extractor also rejects its old fingerprint, including
the saved scope, so an old build can silently check excluded fixture sources.
The version label alone cannot detect either condition.

Diagnostics now query the actual selected runtime's extractor stamp and source
repair features through local modules. An old runtime with foreign fingerprints
is refused before the expensive check. The report does not call that cache
fresh. Rebuild it with the same reviewed explicit source prefixes and launcher;
preserve the old cache. Missing module introspection is reported as unavailable.

The bundled source patch moves scope filtering before Git metadata enumeration
and filesystem descent. Git pathspecs are literal, so spaces and glob characters
in directory names retain their meaning. Existing skip, ignore, size and parser
rules still apply. New files inside the scope remain discoverable.

It also preserves validated, unanimous scope policy from foreign fingerprints.
It never accepts their parse results or cached source hashes. Conflicting or
malformed foreign scopes refuse the operation and require an explicit rebuild.
The check still reads and hashes every current textual source using Graft's
normal source decoding. After a build with the repaired runtime, it can reuse
parses only when the extractor and current content hash both match. Malformed
entries, missing file-hash witnesses, foreign extractors and prior failures
fall back to parsing. Same-size edits with restored timestamps still drift.
Diagnostics report reused/parsed file counts; older builds report unavailable.

For an independent parser/cache audit, set `GRAFT_CHECK_REPARSE=1` for the
Graft check. This retains the previous full re-extraction behaviour and cost.
Parse memoisation trusts the local cache produced by the matching extractor;
it is not an integrity guarantee against deliberate cache tampering. Rebuild
after runtime/dependency changes and do not reuse untrusted transferred caches.

## Apply to a matching Graft source checkout

```sh
python scripts/apply_source_patch.py --source /absolute/graft-source
python scripts/apply_source_patch.py --source /absolute/graft-source --apply
```

The first command checks exact normalised source hashes and Git patch applicability.
The second backs up the affected files and applies the same checked source patch.
It requires Graft's own Git root, rejects links/escaped paths and fails on a
different source base. Inspect or port the change when that check fails. The
asset manifest records the source revision and SHA-256 values. Graft-derived
source is covered by the bundled MIT licence, separate from this skill's licence.

Run the Graft source project's required build and test gate before installing
compiled output through its reviewed sync workflow. This script never patches
installed `dist/`, upgrades dependencies, changes antivirus settings or changes
host registrations. Backups are local source copies; keep them ignored.

After installation, use the chosen runtime to rebuild the same scope, then run
`diagnose.py --check` and real MCP retrieval. Verify addition, edit and removal in
an owned fixture. A scope repair does not guarantee completion under arbitrary
host saturation. Preserve the original timeout and compare matched concurrent
load, runtime identity, file set and filesystem placement.
