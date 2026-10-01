#!/usr/bin/env bash
# Q4T evaluation snapshot: Q3 isolation plus bounded structured reports.
set -euo pipefail
IFS=$'\n\t'
umask 077

runtime=/opt/orchestrator-worker-runtime
base=/var/lib/orchestrator-worker-n4/actors
auth_base=/var/lib/orchestrator-worker-n4/auth

subscription=0
if [[ ${1:-} == --subscription ]]; then
    subscription=1
    shift
fi

if [[ $(id -u) -ne 0 || $# -lt 3 ]]; then
    echo 'Usage (as WSL root): worker-wsl-namespace-q4t [--subscription] ACTOR_DIR -- COMMAND [ARG...]' >&2
    exit 64
fi

if [[ ${1:-} == --inside ]]; then
    shift
    actor=$1
    shift
    [[ $1 == -- ]]
    shift
    cd /
    mount --make-rprivate /
    mount -t proc proc /proc
    for drive in /mnt/c /mnt/d /usr/lib/wsl/drivers; do
        if mountpoint -q "$drive"; then umount "$drive"; fi
        ! mountpoint -q "$drive" || exit 70
    done
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

    mkdir -m 700 /run/actor-bind
    mount --bind "$actor" /run/actor-bind
    mount -t tmpfs -o mode=711,nosuid,nodev tmpfs "$base"
    mkdir -m 755 "$actor"
    mount --bind /run/actor-bind "$actor"
    umount /run/actor-bind
    rmdir /run/actor-bind

    for path in /mnt/c /mnt/d /usr/lib/wsl/drivers; do
        ! mountpoint -q "$path" || exit 70
    done
    [[ ! -e /run/WSL ]] || exit 70
    [[ $(find "$base" -mindepth 1 -maxdepth 1 -type d | wc -l) == 1 ]] || exit 70
    [[ -f /mnt/wsl/resolv.conf ]] || exit 70
    [[ $(stat -c %a /var/lib/orchestrator-worker-n4/evaluator) == 700 ]] || exit 70

    cd "$actor"
    environment=(PATH="$runtime/bin:/usr/bin:/bin" HOME="$actor/.home"
                 TMPDIR=/tmp XDG_CACHE_HOME="$actor/.cache"
                 CLAUDE_PROJECT_DIR="$actor" CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192
                 CLAUDE_CODE_MAX_TURNS=20
                 MAX_STRUCTURED_OUTPUT_RETRIES=5
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
    [[ $1 == "$runtime/bin/claude" ]] || exit 64
    if [[ $# == 5 && $2 == --restricted && $3 == auth &&
          $4 == status && $5 == --json ]]; then
        :
    else
        expected_schema=$(cat "$runtime/q4t-report-schema.json")
        [[ $# == 21 &&
           $2 == -p && -n $3 && $4 == --output-format=stream-json &&
           $5 == --verbose && $6 == --model && $8 == --effort &&
           ${10} == --max-budget-usd && ${12} == --restricted &&
           ${13} == --strict-mcp-config &&
           ${14} == "--mcp-config=$runtime/actor-mcp.json" &&
           ${15} == "--settings=$runtime/actor-settings.json" &&
           ${16} == --no-session-persistence &&
           ${17} == --permission-mode=acceptEdits &&
           ${18} == --permission-prompts=none &&
           ${19} == --tools=Read,Edit,Write,Glob,Grep &&
           ${20} == --allowedTools=mcp__graft__graft_check_freshness,mcp__graft__graft_repo_map,mcp__graft__graft_find_code,mcp__graft__graft_file_api,mcp__graft__graft_trace_calls,mcp__graft__graft_find_all &&
           ${21} == "--json-schema=$expected_schema" ]] || exit 64
        [[ $7 =~ ^claude-(sonnet|opus)-[0-9]+(-[0-9]+)*$ ]] || exit 64
        model_class=${BASH_REMATCH[1]}
        [[ ( $model_class == sonnet && $9 == low ) ||
           ( $model_class == sonnet && $9 == medium ) ||
           ( $model_class == opus && $9 == high ) ]] || exit 64
        python3 -c 'import math,sys; x=float(sys.argv[1]); assert math.isfinite(x) and 0 < x <= 4' "${11}" || exit 64
    fi
    [[ $(stat -c %u:%a "$runtime/actor-settings.json") == 0:644 ]] || exit 70
    [[ $(stat -c %u:%a "$runtime/actor-mcp.json") == 0:644 ]] || exit 70
    exec 9>"$auth_base/.lock"
    flock -n 9 || { printf 'subscription credential is in use\n' >&2; exit 75; }
    python3 "$runtime/worker_wsl_q3_auth.py" begin "${actor##*/}" || exit 70
fi

cd /
python3 "$runtime/worker_wsl_q1.py" start --name "$name" >/dev/null || exit 70
inside=("$runtime/bin/worker-wsl-namespace-q4t")
if [[ $subscription == 1 ]]; then inside+=(--subscription); fi
inside+=(--inside "$actor" -- "$@")
set +e
unshare --mount --pid --fork --kill-child -- "${inside[@]}"
status=$?
set -e
python3 "$runtime/worker_wsl_q1.py" stop --name "$name" --status "$status" >/dev/null || exit 70
if [[ $subscription == 1 ]]; then
    python3 "$runtime/worker_wsl_q3_auth.py" finish "${actor##*/}" || exit 70
fi
exit "$status"
