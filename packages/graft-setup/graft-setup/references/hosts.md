# Preserve host configuration and checkout identity

Install `@nanonets/graft` only when needed and authorised; confirm `graft
--version` and the actual executable path. On Windows, direct Node plus Graft's
`dist/cli.js` is reliable across shells. The helpers resolve ordinary npm shims
or accept an explicit launcher array. They do not use `npx` to download tools
implicitly or issue shell-composed process commands.

For instruction wiring, preview `graft init --dry-run` before any write. Choose
only the hosts the operator uses, and keep machine-global changes out of a
project-only setup. For an AGENTS.md-only setup on the tested version:

```sh
graft init --agents agents --no-mcp --no-hooks --no-global --no-build --dry-run /absolute/project
graft init --agents agents --no-mcp --no-hooks --no-global --no-build /absolute/project
```

Do not rerun `init` just to repair a slow index when host wiring already works.
Do not hand-edit Graft's fenced `<!-- graft:start -->` managed section. Keep
project-specific retrieval guidance outside that section and respect existing
instructions. Inspect a prior wiring stamp when upgrading or cleaning a cache:
MCP upkeep can replay its selected global/host options at startup.

## Project-local registrations

Read the existing config, then merge only the Graft server. Use the host's
current supported schema. Below, executable and CLI paths are placeholders to
resolve on that machine; they are not literal installation destinations.

Codex project `.codex/config.toml`, following the locally verified stdio shape:

```toml
[mcp_servers.graft]
command = "/absolute/path/to/node"
args = ["/absolute/path/to/graft/dist/cli.js", "mcp", "/absolute/project"]
cwd = "/absolute/project"
enabled = true
startup_timeout_sec = 30
tool_timeout_sec = 180
```

These timeouts are example bounds, not prescribed universal values. Choose
them from observed startup/freshness costs. Preserve any existing `required`
policy and unrelated fields rather than forcing all users into required startup.
Project trust and a host restart may be needed before changed settings load.

Claude project `.mcp.json` can use an explicit project root or its supported
`${CLAUDE_PROJECT_DIR:-.}` expansion:

```json
{
  "mcpServers": {
    "graft": {
      "type": "stdio",
      "command": "/absolute/path/to/node",
      "args": ["/absolute/path/to/graft/dist/cli.js", "mcp", "${CLAUDE_PROJECT_DIR:-.}"]
    }
  }
}
```

Review the host's project-server approval and narrow retrieval permissions.
Do not grant blanket permission to unrelated future servers/tools.

For ZCode, merge the server under `.zcode/config.json` → `mcp.servers` using
the installed host's schema. Use a directly resolved Node/CLI launcher on
Windows, or an executable `graft` on Unix. Verify the target host actually
loads this entry; a generic stdio smoke is a different piece of evidence.

## Global registrations and worktrees

A machine-global registration must follow the active session's project root.
Omit a fixed project argument when the host launches the server in the correct
checkout, and verify that behaviour with two distinct roots. If the host does
not supply a trustworthy cwd, use its supported per-project registration or
explicit root mechanism instead. Never make every project query one fixed repo.

Each worktree needs an index for its own current source. Graft can seed worktree
caches, but the receiving checkout's freshness and source spans must still pass.
Only index a broad workspace parent when multi-project federation was actually
requested; do not initialise Graft over a home directory or unrelated projects.

After wiring, prove host tool access, selected root and a real scoped source
query in that host. `probe_mcp.py` proves a fresh local MCP process; it does not
prove that a new editor/chat has loaded the intended configuration or that a
worker is confined to the repository filesystem.
