#!/usr/bin/env bash
# Install the Q4 launcher alongside frozen Q1/Q3 runtime files.
set -euo pipefail
runtime=/opt/orchestrator-worker-runtime
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) == 0 && -x $runtime/bin/worker-wsl-namespace-q1 &&
   -x $runtime/bin/worker-wsl-namespace-q3 &&
   -f $runtime/worker_wsl_q3_auth.py ]] || exit 1
install -o root -g root -m 755 "$source_root/worker_wsl_namespace_q4.sh" \
    "$runtime/bin/worker-wsl-namespace-q4"
