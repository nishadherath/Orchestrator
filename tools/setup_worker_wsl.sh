#!/usr/bin/env bash
# Install pinned Linux-only tools used by the disposable N4 worker host probe.
# Run as root in WSL; this never imports the Windows host's Node or Graft runtime.
set -euo pipefail

version=22.22.0
archive="node-v${version}-linux-x64.tar.gz"
base="https://nodejs.org/dist/v${version}"
runtime=/opt/orchestrator-worker-runtime
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT

if [[ $(id -u) -ne 0 ]]; then
    echo 'Run this installer as WSL root.' >&2
    exit 1
fi
if [[ $(uname -m) != x86_64 ]]; then
    echo 'This pinned runtime supports x86_64 only.' >&2
    exit 1
fi
for tool in gcc g++ make python3; do
    command -v "$tool" >/dev/null || { echo "Missing WSL build prerequisite: $tool" >&2; exit 1; }
done

curl --fail --location --silent --show-error "$base/SHASUMS256.txt" -o "$scratch/SHASUMS256.txt"
curl --fail --location --silent --show-error "$base/$archive" -o "$scratch/$archive"
awk -v file="$archive" '$2 == file {print}' "$scratch/SHASUMS256.txt" > "$scratch/checksum"
[[ $(wc -l < "$scratch/checksum") -eq 1 ]]
(cd "$scratch" && sha256sum --check checksum)

install -d -m 755 "$runtime"
tar -xzf "$scratch/$archive" -C "$runtime" --strip-components=1
export PATH="$runtime/bin:/usr/bin:/bin"
"$runtime/bin/node" --version
"$runtime/bin/npm" --version
"$runtime/bin/npm" install --global --prefix "$runtime" \
    '@nanonets/graft@0.18.0'
"$runtime/bin/node" "$runtime/lib/node_modules/@nanonets/graft/dist/cli.js" --version

# Workers may execute but cannot modify runtime code or package metadata.
chown -R root:root "$runtime"
chmod -R a+rX,go-w "$runtime"
