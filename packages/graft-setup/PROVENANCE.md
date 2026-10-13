# Why two Graft 0.21.1 installations had different capabilities

Investigation: 2026-10-14. The Windows installation uses the operator's local
`fork_graft` build; the Linux installation uses the published npm release.
The local fork retains package version 0.21.1 while adding structured and
document indexing. This is a build provenance difference, rather than an OS
limitation.

## Verified cause

The npm archive was downloaded from its version-specific registry metadata and
verified against both its SHA-512 integrity and SHA-1. Its recorded publication
Git head is `375a37e0b6a21d28f12fce2d220d692726bb0730`. All 620 installed Linux
package members match the archive byte-for-byte, excluding dependency trees.

The Windows package differs from that archive in 82 existing files and adds
128 files. Its package JSON still matches the published package. All 739
compiled `dist/` files instead match the local fork's current built output,
with no missing, extra or different dist files. The observed fork checkout head
is `d7c656c1f8b4a8101b054593f508405b53c6799d`.

The fork's documented `scripts/sync-global.mjs` copies only `dist/` into the
global npm package and removes obsolete compiled files. It requires equal
package version labels and preserves the installed package JSON and working
native dependencies. This avoids rebuilding a Kotlin grammar that its local
Windows toolchain cannot compile. Graft's `readCurrentVersion` reads package
JSON, so the fork additions do not change what `--version` prints.

The fork introduced `--structured` in commit
`8d4395ba8aa8f4edad06e099459a5b60ca8dd791`, and the document CLI flags in
`8f7afe0b5be9f16a0c31ca6f13b39236c0abf7b4`. The source/build relationship is
confirmed by current byte parity and the recorded sync procedure; the precise
historical sync invocation was not recovered. The checkout head is not an
embedded build attestation.

## Control and reproducibility

The verified published CLI was run in an isolated project-local extraction on
the same Windows Node 26.7.0 and existing Windows dependency directory. It
reports 0.21.1 and lacks `--structured`, `--documents` and `--deep-documents`,
just as the published Linux package does. The active installation was preserved.

A byte-verified snapshot of the fork's 739 compiled files was also run with
native Linux Node 22.23.0 and existing Linux dependencies. All 14 real-Graft
acceptance steps passed, including structured Markdown indexing, MCP retrieval,
automatic addition/removal and retained scope. The first fixture layout missed
a nested npm dependency; that setup failure is retained, and the corrected
layout passed without installing new dependencies. Binary-document rendering
and its optional dependencies were not exercised.

To reproduce the comparison, fetch the version-specific
[npm metadata](https://registry.npmjs.org/@nanonets/graft/0.21.1), verify the
named tarball's integrity, and compare its regular package members with each
installation, excluding `node_modules`. Compare a suspected fork's compiled
tree separately and read its install/sync procedure. Keep the archive and
test extractions outside indexed source. Inspect paths before following a
dependency link or stopping any runtime.

The updated helper reports actual build flags and resolved CLI/package paths,
plus SHA-256 for the CLI entry and package JSON. These are local observations;
they do not authenticate the whole runtime or imply that an intentional fork
should be replaced. A same-version repair should select the intended build,
then verify its capabilities and retrieval. Ordinary diagnosis remains offline.

Detailed member hashes, counts, source evidence hashes and the Windows control
are in [build-provenance.json](test-results/build-provenance.json). The upstream
code is neither copied into nor bundled with the skill archive. The fork and
both active Graft installations were not modified by this investigation.
