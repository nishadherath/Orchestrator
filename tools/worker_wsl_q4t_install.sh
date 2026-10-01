#!/usr/bin/env bash
# Install the prospective Q4T launcher and exact report schema without
# modifying attested Q4, Q4R or Q4S runtime snapshots.
set -euo pipefail
runtime=/opt/orchestrator-worker-runtime
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
[[ $(id -u) == 0 && -x $runtime/bin/worker-wsl-namespace-q4 &&
   -f $runtime/worker_wsl_q3_auth.py ]] || exit 1

schema_tmp=$(mktemp)
trap 'rm -f -- "$schema_tmp"' EXIT
PYTHONPATH="$source_root" python3 -B -c \
    'from worker_q4r_structured import schema_argument; print(schema_argument().split("=", 1)[1])' \
    >"$schema_tmp"
install -o root -g root -m 644 "$schema_tmp" "$runtime/q4t-report-schema.json"
install -o root -g root -m 755 "$source_root/worker_wsl_namespace_q4t.sh" \
    "$runtime/bin/worker-wsl-namespace-q4t"
