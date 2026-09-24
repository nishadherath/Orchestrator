#!/usr/bin/env bash
# Stage disposable N4 probe material on WSL's ext4 filesystem, not /mnt/c.
set -euo pipefail

runtime=/opt/orchestrator-worker-runtime
base=/var/lib/orchestrator-worker-n4
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) == 0 && -x $runtime/bin/node ]] || exit 1

install -m 755 /home/wsl/.local/share/claude/versions/2.1.273 "$runtime/bin/claude"
install -m 755 "$source_root/worker_wsl_namespace.sh" "$runtime/bin/worker-wsl-namespace"
install -m 644 "$source_root/worker_wsl_actor_probe.py" "$runtime/actor-probe.py"
cat > "$runtime/actor-mcp.json" <<'JSON'
{"mcpServers":{"graft":{"type":"stdio","command":"/opt/orchestrator-worker-runtime/bin/node","args":["/opt/orchestrator-worker-runtime/lib/node_modules/@nanonets/graft/dist/cli.js","mcp","${CLAUDE_PROJECT_DIR:-.}"]}}}
JSON
chmod 644 "$runtime/actor-mcp.json"
chown root:root "$runtime/bin/claude" "$runtime/bin/worker-wsl-namespace" \
    "$runtime/actor-probe.py" "$runtime/actor-mcp.json"

install -d -m 711 "$base" "$base/actors"
install -d -m 700 "$base/evaluator"
if [[ ! -e $base/evaluator/oracle.py ]]; then
    printf 'ORACLE_MARKER = "N4_EVALUATOR_SECRET_%s"\n' "$(cat /proc/sys/kernel/random/uuid)" \
        > "$base/evaluator/oracle.py"
    chmod 600 "$base/evaluator/oracle.py"
fi
actor=$(mktemp -d "$base/actors/probe-XXXXXXXX")
printf 'ACTOR_MARKER = "N4_ACTOR_VISIBLE_%s"\n' "$(cat /proc/sys/kernel/random/uuid)" \
    > "$actor/app.py"
install -d -m 700 "$actor/.home" "$actor/.cache"
chown -R 65534:65534 "$actor"
printf '%s\n' "$actor"
