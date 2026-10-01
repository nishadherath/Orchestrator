#!/usr/bin/env bash
# Q1 snapshot of the N4 namespace boundary for a multi-file actor.
# Kept separate so the frozen N5 launcher and its historical hashes do not move.
# The evaluator and Windows host mounts are removed before dropping privilege.
set -euo pipefail
IFS=$'\n\t'
umask 077

runtime=/opt/orchestrator-worker-runtime
base=/var/lib/orchestrator-worker-n4/actors
auth_base=/var/lib/orchestrator-worker-n4/auth

subscription=0
if [[ ${1:-} == --subscription ]]; then
    echo 'Q1 qualification does not admit provider credentials' >&2
    exit 64
fi

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

    if [[ $subscription == 1 ]]; then
        auth_session="$auth_base/sessions/${actor##*/}"
        [[ $(stat -c %u:%a "$auth_session") == 65534:700 ]] || exit 70
        [[ $(stat -c %u:%a "$auth_session/.credentials.json") == 65534:600 ]] || exit 70
        mkdir -m 700 /run/claude-auth
        mount --bind "$auth_session" /run/claude-auth
    fi

    # Keep this actor's original path while hiding every sibling invocation.
    # Otherwise all actors share UID 65534 and could edit another actor's
    # app.py if its directory name became known.
    mkdir -m 700 /run/actor-bind
    mount --bind "$actor" /run/actor-bind
    mount -t tmpfs -o mode=711,nosuid,nodev tmpfs "$base"
    mkdir -m 755 "$actor"
    mount --bind /run/actor-bind "$actor"
    umount /run/actor-bind
    rmdir /run/actor-bind

    for path in /mnt/c /mnt/d /usr/lib/wsl/drivers; do
        ! mountpoint -q "$path" || { echo "Host mount remains visible: $path" >&2; exit 70; }
    done
    [[ ! -e /run/WSL ]] || exit 70
    [[ $(find "$base" -mindepth 1 -maxdepth 1 -type d | wc -l) == 1 ]] || exit 70
    [[ -f /mnt/wsl/resolv.conf ]] || exit 70
    [[ $(stat -c %a /var/lib/orchestrator-worker-n4/evaluator) == 700 ]] || exit 70

    cd "$actor"
    environment=(PATH="$runtime/bin:/usr/bin:/bin" HOME="$actor/.home"
                 TMPDIR=/tmp XDG_CACHE_HOME="$actor/.cache"
                 CLAUDE_PROJECT_DIR="$actor" CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192
                 NO_COLOR=1)
    if [[ $subscription == 1 ]]; then
        environment+=(CLAUDE_CONFIG_DIR=/run/claude-auth)
    fi
    exec setpriv --reuid=65534 --regid=65534 --clear-groups \
        --no-new-privs --bounding-set=-all --inh-caps=-all -- \
        env -i "${environment[@]}" "$@" 9>&-
fi

actor=$(realpath -e -- "$1")
shift
[[ $1 == -- ]]
shift
[[ $actor == "$base/"* && -d $actor && ! -L $actor ]] || exit 64
[[ $(stat -c %u:%a "$actor") == 0:755 ]] || exit 64
name=${actor##*/}
[[ $name == q1-* ]] || exit 64
python3 "$runtime/worker_wsl_q1.py" preflight --name "$name" >/dev/null || exit 64
[[ -d /var/lib/orchestrator-worker-n4/evaluator ]] || exit 64
[[ -x $runtime/bin/claude && -x $runtime/bin/node ]] || exit 69

if [[ $subscription == 1 ]]; then
    [[ ${actor##*/} == inv-* && $1 == "$runtime/bin/claude" ]] || exit 64
    # The root launcher never grants a credential to an arbitrary command.
    # The Windows transport separately validates every option and budget.
    if [[ $# == 5 && $2 == --restricted && $3 == auth &&
          $4 == status && $5 == --json ]]; then
        : # A provider-free check of the actual isolated Claude login.
    else
        required=(--restricted --strict-mcp-config --no-session-persistence
                  --permission-prompts=none --tools=Read,Edit,Write,Glob,Grep
                  "--settings=$runtime/actor-settings.json")
        for flag in "${required[@]}"; do
            found=0
            for argument in "$@"; do
                if [[ $argument == "$flag" ]]; then found=1; break; fi
            done
            [[ $found == 1 ]] || exit 64
        done
        for argument in "$@"; do
            [[ $argument != --dangerously-skip-permissions ]] || exit 64
        done
    fi
    [[ $(stat -c %u:%a "$runtime/actor-settings.json") == 0:644 ]] || exit 70
    exec 9>"$auth_base/.lock"
    flock -n 9 || { printf 'subscription credential is in use\n' >&2; exit 75; }
    python3 "$runtime/worker_wsl_auth.py" begin "${actor##*/}" || exit 70
fi

cd /
python3 "$runtime/worker_wsl_q1.py" start --name "$name" >/dev/null || exit 70
inside=("$runtime/bin/worker-wsl-namespace-q1")
if [[ $subscription == 1 ]]; then inside+=(--subscription); fi
inside+=(--inside "$actor" -- "$@")
set +e
unshare --mount --pid --fork --kill-child -- "${inside[@]}"
status=$?
set -e
python3 "$runtime/worker_wsl_q1.py" stop --name "$name" --status "$status" >/dev/null || exit 70
if [[ $subscription == 1 ]]; then
    python3 "$runtime/worker_wsl_auth.py" finish "${actor##*/}" || exit 70
fi
exit "$status"
