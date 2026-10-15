#!/usr/bin/env bash
# tools/dev/pre-commit-hook.sh — git pre-commit hook: refuse a commit
# that stages an unprepped media file (image, sound, video, PDF).
#
# Installed by tools/dev/install-git-hooks.sh as a link, so edits here
# take effect without reinstalling. Checks the staged version of each
# file, not the working copy. design/studio.md, step 4.
#
# `git commit --no-verify` skips it; pre-build-check.sh still checks
# every media file before any push or deploy.

set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1
# Commits from an editor may not have ~/.local/bin (poetry) on PATH.
PATH="$HOME/.local/bin:$PATH"

if ! poetry run python tools/dev/check_media.py --staged; then
  echo >&2
  echo "Commit refused: prep the files above (tools/studio/), then stage them again." >&2
  exit 1
fi
