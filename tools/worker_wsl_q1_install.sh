#!/usr/bin/env bash
# Install only the experimental Q1 boundary, leaving N5 runtime files intact.
set -euo pipefail
runtime=/opt/orchestrator-worker-runtime
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) == 0 && -x $runtime/bin/node && -x $runtime/bin/worker-wsl-namespace ]] || exit 1
install -o root -g root -m 644 "$source_root/worker_wsl_q1.py" "$runtime/worker_wsl_q1.py"
install -o root -g root -m 644 "$source_root/worker_wsl_q1_actor_probe.py" \
    "$runtime/worker_wsl_q1_actor_probe.py"
install -o root -g root -m 644 "$source_root/worker_wsl_q1_probe.py" \
    "$runtime/worker_wsl_q1_probe.py"
install -o root -g root -m 755 "$source_root/worker_wsl_namespace_q1.sh" \
    "$runtime/bin/worker-wsl-namespace-q1"
install -d -o root -g root -m 700 /var/lib/orchestrator-worker-n4/qualification-manifests
install -d -o root -g root -m 700 /var/lib/orchestrator-worker-n4/qualification-collected
