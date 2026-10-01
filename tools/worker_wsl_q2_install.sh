#!/usr/bin/env bash
# Add the provider-free Q2 case runner without modifying the N5 or Q1 binaries.
set -euo pipefail
runtime=/opt/orchestrator-worker-runtime
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) == 0 && -x $runtime/bin/worker-wsl-namespace-q1 ]] || exit 1
install -o root -g root -m 644 "$source_root/worker_wsl_q2_case.py" "$runtime/worker_wsl_q2_case.py"
install -o root -g root -m 644 "$source_root/worker_wsl_q2_verify.py" "$runtime/worker_wsl_q2_verify.py"
