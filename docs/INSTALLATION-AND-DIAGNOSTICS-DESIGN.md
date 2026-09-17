# Installation and diagnostics design

Date: 2026-09-17. Scope: improvement Stage 6. Decision: D89.

## Ownership boundary

`dist/bundle-manifest.json` is the install contract. It carries the bundle
version, SHA-256 digest of every copied payload file, owned configuration
paths, instruction markers, state path and backup root. Package support files
such as the README, installer, template and settings fragment remain in the
bundle but are not copied into a consumer project.

The installer owns:

- payload files named and hashed by the manifest;
- `promptCacheTtl`, `autoCompactWindow`, `statusLine` and
  `subagentStatusLine` in `.claude/settings.json`;
- exact bundle entries added to `permissions.allow` and
  `hooks.SessionStart`;
- the text between the two orchestrator markers in `CLAUDE.md`;
- `mcpServers.graft` only when the operator supplies its command;
- its state file and operation backups under
  `.claude/orchestrator-install/`.

It does not own other settings, permissions, hooks, MCP servers or
`CLAUDE.md` text. Routing ledgers, acceptance evidence, run records and
handoffs are project data. Uninstall leaves them in place.

## Transaction

`install.py plan` verifies the manifest and payload before inspecting the
target. The plan reports the resolved target, version, exact backup location,
changes and conflicts. Existing unowned payload paths and same-name scalar
configuration values are conflicts. Malformed JSON is a conflict. No conflict
path is changed.

`apply` computes the same plan and then writes preimages, semantic JSON
operations and instruction-block operations before using atomic file
replacement. Reapplying an unchanged bundle produces `NO_CHANGES`; it does not
duplicate list entries or create another backup.

An upgrade may replace an owned file only when its current digest equals the
previous state. It may update an owned configuration value only when the
current value equals the previously installed value. A manually installed
older bundle has no ownership state and must be reviewed rather than silently
adopted.

## Rollback and uninstall

Each operation backup contains the original bytes for touched files and a
machine-readable reversal recipe. Rollback requires every owned post-operation
value to remain unchanged. Payload drift, an edited instruction block or an
edited owned JSON value stops the whole rollback and names the conflict.
The backup root carries its own deny-by-default `.gitignore` because preimages
can contain machine-local settings or credentials.

JSON reversal is semantic. Added values are removed and prior owned values are
restored while later unrelated keys and list entries remain. Full preimages
remain available for manual recovery. Rolling back a first installation
removes its payload. Rolling back an upgrade restores the earlier bundle and
state. Uninstall uses the same conflict rules and records a reversible backup.

## Operational diagnostics

`preflight.py --status` reads authoritative files without changing them. Its
stable JSON schema separates:

- requested worker cells from observed actual model and effort evidence;
- unresolved attempts and ledger parse errors;
- acceptance status counts and outstanding evidence;
- routing-ledger known spend and unknown attempts;
- Controller known spend, reservations and unresolved invocation IDs;
- prior generation date, age and a labelled 90-day staleness advisory;
- Claude and Codex Graft configuration plus local graph presence.

Routing and Controller cost scopes remain separate because one Controller
charge may appear in both. Graft availability still requires an in-session
`graft_check_freshness` call; configuration is not presented as proof that the
server is running. `--explain` adds individual rows and `--json` keeps field
names stable for automation.

## Qualification and release boundary

The offline install suite covers a clean project whose path contains spaces,
repeat install, upgrade, uninstall, install and uninstall rollback, malformed
settings, unrelated-setting preservation, payload tampering and rollback
conflicts. The clean consumer also runs the installed router selftest, freezes
acceptance, records fake work, verifies it, creates an incomplete attempt,
recovers it and reads installed diagnostics. These tests made no model or
provider calls.

Windows was exercised directly. The GitHub Actions workflow defines the same
offline checks for Windows and Ubuntu, but this development session did not
run the hosted workflow and does not claim Linux results.

`tools/release_check.py` verifies source-to-bundle equivalence, generated
workers, payload exclusions and absence of credential-like text or personal
machine home paths. Publication remains blocked on explicit operator actions:
the repository has no selected licence or notice, the current development
bundle has a dirty stamp, and no publishing action is automated.

## Limits

The installer cannot infer a portable Graft executable. A caller must supply
it or configure Graft separately. The 90-day prior advisory is a maintenance
policy, not measured capability decay. Offline fixture success does not prove
compatibility with a future Claude Code, Codex, Python or operating-system
release. Live-model compatibility remains part of the deferred evaluation.
