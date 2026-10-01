#!/usr/bin/env bash
# Install the Q4U one-editable boundary alongside frozen Q1/Q4T snapshots.
set -euo pipefail
runtime=/opt/orchestrator-worker-runtime
source_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
q1_sha=33bd2985ac688680e90417db58c5b7e61e41748af284e3ce85b649e6b978b259
[[ $(id -u) == 0 && -x $runtime/bin/worker-wsl-namespace-q4t &&
   -f $runtime/worker_wsl_q3_auth.py ]] || exit 1
[[ $(sha256sum "$runtime/worker_wsl_q1.py" | cut -d' ' -f1) == "$q1_sha" ]] || {
    echo 'Q1 runtime differs from the Q4U pinned base' >&2
    exit 1
}

schema_tmp=$(mktemp)
trap 'rm -f -- "$schema_tmp"' EXIT
PYTHONPATH="$source_root" python3 -B -c \
    'from worker_q4r_structured import schema_argument; print(schema_argument().split("=", 1)[1])' \
    >"$schema_tmp"
install -o root -g root -m 644 "$schema_tmp" "$runtime/q4u-report-schema.json"
install -o root -g root -m 644 "$source_root/worker_wsl_q4u.py" \
    "$runtime/worker_wsl_q4u.py"
install -o root -g root -m 755 "$source_root/worker_wsl_namespace_q4u.sh" \
    "$runtime/bin/worker-wsl-namespace-q4u"
