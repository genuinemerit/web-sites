#!/usr/bin/env bash
# Install (or update) the W3C Nu HTML Checker ("vnu") used by
# tools/dev/pre-build-check.sh's HTML-validity check.
#
#   bash tools/dev/install-vnu.sh
#
# Why this build: vnu.linux.zip is a self-contained runtime image (its
# own bundled Java runtime) - no system Java, no Node, no sudo. It
# installs under ~/.local, user-owned, so unlike init-dev-host.sh this
# needs no password.
#
# Upstream only publishes current builds under a rolling `latest` tag
# (the last numbered release is from 2020). So this verifies integrity
# rather than pinning: the download's sha256 must match the digest
# GitHub publishes for that asset, or nothing is installed. Re-run to
# update; `vnu --version` reports what's installed.

set -euo pipefail

ASSET="vnu.linux.zip"
RELEASE_API="https://api.github.com/repos/validator/validator/releases/tags/latest"
DOWNLOAD_URL="https://github.com/validator/validator/releases/download/latest/$ASSET"
INSTALL_DIR="$HOME/.local/share/vnu"
BIN_LINK="$HOME/.local/bin/vnu"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

printf '[INFO] Looking up the published digest for %s...\n' "$ASSET"
EXPECTED="$(curl -fsSL "$RELEASE_API" | python3 -c '
import json, sys
for asset in json.load(sys.stdin)["assets"]:
    if asset["name"] == sys.argv[1]:
        print((asset.get("digest") or "").removeprefix("sha256:"))
' "$ASSET")"
if [[ -z "$EXPECTED" ]]; then
    printf '[FAIL] No published sha256 digest found for %s.\n' "$ASSET" >&2
    exit 1
fi

printf '[INFO] Downloading %s (~65 MB)...\n' "$ASSET"
curl -fsSL -o "$WORK/$ASSET" "$DOWNLOAD_URL"

ACTUAL="$(sha256sum "$WORK/$ASSET" | cut -d' ' -f1)"
if [[ "$ACTUAL" != "$EXPECTED" ]]; then
    printf '[FAIL] sha256 mismatch: expected %s, got %s.\n' "$EXPECTED" "$ACTUAL" >&2
    exit 1
fi
printf '[PASS] sha256 verified: %s\n' "$ACTUAL"

# Python's zipfile, not unzip (not installed on ubuvm). zipfile drops
# Unix permission bits on extract, so restore them from each entry's
# external_attr - the runtime image's bin/ and lib/ helpers must stay
# executable.
python3 - "$WORK/$ASSET" "$WORK/extract" <<'PY'
import sys
import zipfile
from pathlib import Path

archive, dest = sys.argv[1], Path(sys.argv[2])
with zipfile.ZipFile(archive) as z:
    for info in z.infolist():
        z.extract(info, dest)
        mode = (info.external_attr >> 16) & 0o777
        if mode:
            (dest / info.filename).chmod(mode)
PY

rm -rf "$INSTALL_DIR"
mkdir -p "$(dirname "$INSTALL_DIR")" "$(dirname "$BIN_LINK")"
mv "$WORK/extract/vnu-runtime-image" "$INSTALL_DIR"
# A wrapper, not a symlink: the bundled bin/vnu launcher locates its
# java binary relative to its own invocation path, which a symlink in
# ~/.local/bin breaks.
rm -f "$BIN_LINK"
printf '#!/bin/sh\nexec "%s/bin/vnu" "$@"\n' "$INSTALL_DIR" > "$BIN_LINK"
chmod 0755 "$BIN_LINK"

printf '[DONE] Installed vnu %s -> %s\n' "$("$BIN_LINK" --version)" "$BIN_LINK"
