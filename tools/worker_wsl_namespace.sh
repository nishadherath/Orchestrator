#!/usr/bin/env bash
# Root-owned WSL launcher for one unprivileged actor process tree.
# The evaluator and Windows host mounts are removed before dropping privilege.
set -euo pipefail

runtime=/opt/orchestrator-worker-runtime
base=/var/lib/orchestrator-worker-n4/actors

if [[ $(id -u) -ne 0 || $# -lt 3 ]]; then
    echo 'Usage (as WSL root): worker_wsl_namespace.sh ACTOR_DIR -- COMMAND [ARG...]' >&2
    exit 64
fi

if [[ ${1:-} == --inside ]]; then
    shift
    actor=$1
    shift
    [[ $1 == -- ]]
    shift

    # Only this PID/mount namespace sees the changes. A fresh proc mount hides
    # host processes and /proc/1/root; neither Windows drive survives here.
    cd /
    mount --make-rprivate /
    mount -t proc proc /proc
    for drive in /mnt/c /mnt/d /usr/lib/wsl/drivers; do
        if mountpoint -q "$drive"; then umount "$drive"; fi
        ! mountpoint -q "$drive" || exit 70
    done
    # WSL puts DNS in /mnt/wsl and its Windows interop sockets in /run/WSL.
    # Preserve only DNS, then cover the remaining host integration surfaces.
    cp -L /etc/resolv.conf /tmp/orchestrator-worker-resolv.conf
    mount -t tmpfs -o mode=755,nosuid,nodev tmpfs /mnt/wsl
    cp /tmp/orchestrator-worker-resolv.conf /mnt/wsl/resolv.conf
    chmod 644 /mnt/wsl/resolv.conf
    mount -t tmpfs -o mode=755,nosuid,nodev tmpfs /mnt/wslg
    mount -t tmpfs -o mode=755,nosuid,nodev tmpfs /run
    mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp
    mount --bind /dev/null /init

    for path in /mnt/c /mnt/d /usr/lib/wsl/drivers; do
        ! mountpoint -q "$path" || { echo "Host mount remains visible: $path" >&2; exit 70; }
    done
    [[ ! -e /run/WSL ]] || exit 70
    [[ -f /mnt/wsl/resolv.conf ]] || exit 70
    [[ $(stat -c %a /var/lib/orchestrator-worker-n4/evaluator) == 700 ]] || exit 70

    cd "$actor"
    exec setpriv --reuid=65534 --regid=65534 --clear-groups \
        --no-new-privs --bounding-set=-all --inh-caps=-all -- \
        env -i PATH="$runtime/bin:/usr/bin:/bin" HOME="$actor/.home" \
        TMPDIR=/tmp XDG_CACHE_HOME="$actor/.cache" \
        CLAUDE_PROJECT_DIR="$actor" CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192 \
        NO_COLOR=1 "$@"
fi

actor=$(realpath -e -- "$1")
shift
[[ $1 == -- ]]
shift
[[ $actor == "$base/"* && -d $actor && ! -L $actor ]] || exit 64
[[ $(stat -c %u "$actor") == 65534 ]] || exit 64
[[ -d /var/lib/orchestrator-worker-n4/evaluator ]] || exit 64
[[ -x $runtime/bin/claude && -x $runtime/bin/node ]] || exit 69

cd /
exec unshare --mount --pid --fork --kill-child -- "$runtime/bin/worker-wsl-namespace" \
    --inside "$actor" -- "$@"
