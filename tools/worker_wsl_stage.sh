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
install -m 644 "$source_root/worker_wsl_materialize.py" "$runtime/worker_wsl_materialize.py"
install -m 644 "$source_root/worker_wsl_collect.py" "$runtime/worker_wsl_collect.py"
install -m 644 "$source_root/worker_wsl_transport_probe.py" "$runtime/transport-probe.py"
rm -f -- "$runtime/materialize.py" "$runtime/collect.py"
cat > "$runtime/actor-mcp.json" <<'JSON'
{"mcpServers":{"graft":{"type":"stdio","command":"/opt/orchestrator-worker-runtime/bin/node","args":["/opt/orchestrator-worker-runtime/lib/node_modules/@nanonets/graft/dist/cli.js","mcp","${CLAUDE_PROJECT_DIR:-.}"]}}}
JSON
chmod 644 "$runtime/actor-mcp.json"
chown root:root "$runtime/bin/claude" "$runtime/bin/worker-wsl-namespace" \
    "$runtime/actor-probe.py" "$runtime/worker_wsl_materialize.py" \
    "$runtime/worker_wsl_collect.py" \
    "$runtime/transport-probe.py" \
    "$runtime/actor-mcp.json"

install -d -m 711 "$base" "$base/actors"
install -d -m 700 "$base/evaluator"
install -d -m 700 "$base/seed"
if [[ ! -e $base/evaluator/oracle.py ]]; then
    printf 'ORACLE_MARKER = "N4_EVALUATOR_SECRET_%s"\n' "$(cat /proc/sys/kernel/random/uuid)" \
        > "$base/evaluator/oracle.py"
    chmod 600 "$base/evaluator/oracle.py"
fi
seed=$(mktemp -d "$base/seed/input-XXXXXXXX")
[[ $seed == "$base/seed/"* ]] || exit 1
trap 'rm -rf -- "$seed"' EXIT
printf 'ACTOR_MARKER = "N4_ACTOR_VISIBLE_%s"\n' "$(cat /proc/sys/kernel/random/uuid)" \
    > "$seed/app.py"
printf 'assert True\n' > "$seed/public_check.py"
printf 'Probe the actor boundary.\n' > "$seed/ISSUE.md"
printf '{"schema_version":1}\n' > "$seed/acceptance.json"
uuid=$(cat /proc/sys/kernel/random/uuid)
python3 "$runtime/worker_wsl_materialize.py" --source "$seed" --name "probe-${uuid:0:8}" |
    python3 -c 'import json,sys; print(json.load(sys.stdin)["actor_root"])'
