#!/usr/bin/env bash
# Install only the Q3 paid multi-file launcher and credential-name wrapper.
set -euo pipefail
runtime=/opt/orchestrator-worker-runtime
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) == 0 && -x $runtime/bin/worker-wsl-namespace-q1 &&
   -f $runtime/worker_wsl_auth.py && -f $runtime/actor-mcp.json ]] || exit 1
install -o root -g root -m 755 "$source_root/worker_wsl_namespace_q3.sh" \
    "$runtime/bin/worker-wsl-namespace-q3"
install -o root -g root -m 644 "$source_root/worker_wsl_q3_auth.py" \
    "$runtime/worker_wsl_q3_auth.py"
install -o root -g root -m 644 "$source_root/worker_wsl_q3_probe.py" \
    "$runtime/worker_wsl_q3_probe.py"
