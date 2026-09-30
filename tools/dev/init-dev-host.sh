#!/usr/bin/env bash
# tools/dev/init-dev-host.sh — dev-host bootstrap for web-sites.
#
# Mirrors sask's tools/dev/init-dev-host.sh pattern: apt prereqs only,
# safe to commit, no secrets. Run once on a fresh Ubuntu host (or to
# catch up an existing one, like ubuvm right now — most of this may
# already be satisfied there).
#
# NOTE: on ubuvm, `sudo` requires interactive password auth (no
# NOPASSWD configured), so Claude Code cannot run this unattended —
# David runs it directly.
#
# Usage:
#   bash tools/dev/init-dev-host.sh

set -euo pipefail

echo "[1/3] nginx (local dev vhost-per-site, mirrors prod)"
sudo apt-get update -qq
sudo apt-get install -y nginx

echo "[2/3] gh CLI (GitHub repo automation)"
if ! command -v gh >/dev/null; then
    type -p wget >/dev/null || sudo apt-get install -y wget
    sudo mkdir -p -m 755 /etc/apt/keyrings
    out=$(mktemp)
    wget -nv -O "$out" https://cli.github.com/packages/githubcli-archive-keyring.gpg
    sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg < "$out" > /dev/null
    sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update -qq
fi
sudo apt-get install -y gh

echo "[3/3] poetry, shellcheck — already present on ubuvm as of 2026-09-30, skipping"
# poetry:    /home/dave/.local/bin/poetry (2.4.1)
# checker:   /usr/bin/shellcheck (0.11.0)
# Python: system /usr/bin/python3 (3.14.x) used directly — no pyenv for
# this project (see CLAUDE.md's Environment section for why).

echo
echo "[DONE] nginx: $(nginx -v 2>&1 || echo 'not found')"
echo "[DONE] gh:    $(gh --version 2>&1 | head -1 || echo 'not found')"
