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

echo "[1/2] nginx (local dev vhost-per-site, mirrors prod) + gh CLI (GitHub repo automation)"
# Both are available straight from Ubuntu's own repos on 26.04 (checked
# 2026-09-30: gh 2.46.0-4 is in universe) — no need for GitHub's own apt
# repo/keyring dance.
sudo apt-get update -qq
# ffmpeg (2026-10-10): tools/studio/av_prep.sh - web-ready copies of
# audio/video (ffmpeg + ffprobe; iconv is in the base system).
sudo apt-get install -y gh nginx ffmpeg

echo "[2/2] poetry, shellcheck — already present on ubuvm as of 2026-09-30, skipping"
# poetry:    /home/dave/.local/bin/poetry (2.4.1)
# checker:   /usr/bin/shellcheck (0.11.0)
# Python: system /usr/bin/python3 (3.14.x) used directly — no pyenv for
# this project (see CLAUDE.md's Environment section for why).

echo
echo "[DONE] nginx: $(nginx -v 2>&1 || echo 'not found')"
echo "[DONE] gh:    $(gh --version 2>&1 | head -1 || echo 'not found')"
