# Install and redistribute

This skill is distributed as a ZIP containing one `graft-setup/` directory.
It includes Python scripts, references, UI metadata, a version and the Apache
2.0 licence, plus a guarded Graft source patch under its own MIT licence.
It contains no Graft executable, graph cache, machine-specific
configuration, keys, provider adapter or project source snapshots.

Verify the ZIP SHA-256 against its adjacent manifest before extracting it.
Inspect the listed members: they all begin with `graft-setup/` and have no
absolute or parent-traversal paths. Extract to a temporary location first.

Copy the complete `graft-setup/` folder to the skill directory your host uses.
For an existing installation, preserve its old folder first and review local
customisations. Replace only this skill; do not run Graft `init`, edit MCP
settings or overwrite other skills as part of installation. A new session may
be needed for the host to refresh skill descriptions.

Prerequisites are Python 3.12 or newer and a separately installed compatible
`@nanonets/graft` with its required Node runtime. The scripts have no pip
dependencies. `python` is an example executable name: use the actual interpreter
on that host. Windows users can supply a direct Node/CLI launcher JSON array.

Examples, run from this skill directory:

```sh
python scripts/diagnose.py --repo /absolute/project --check
python scripts/refresh.py --repo /absolute/project --only-dir app --only-dir tests --dry-run
python scripts/refresh.py --repo /absolute/project --only-dir app --only-dir tests
python scripts/probe_mcp.py --repo /absolute/project --file app/core.py --symbol compute --needle distinctive_literal
python scripts/trace.py diagnose --repo /absolute/project --check 2> /approved/diagnostic.trace.jsonl
```

For an optional corpus, use `--cache .graft/corpus` consistently on refresh,
diagnosis and probe. Ordinary Graft CLI queries use `graft --dir
/absolute/project/.graft/corpus ask "query" /absolute/project`. Host registration
for the default graph remains separate from a corpus index.

The source package's outer README explains deterministic release builds and
tests. Platform evidence states which environments were actually exercised.
Cross-platform paths and subprocess APIs are implemented without shell scripts;
that design is not a claim that every Unix variant or host has been tested.
