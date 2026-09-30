#!/usr/bin/env bash
# tools/dev/backup-to-laptop.sh — occasional backup of the working tree
# to David's laptop (wingchun), landing in a Dropbox-synced folder there.
#
# Manual and deliberate by design (see planning/architecture.md's
# Backup/rollback section) — NOT a cron job. Run this at the same
# "significant build" moments that already trigger a GitHub push.
#
# Excludes .git/ (GitHub already covers version-history backup).
# Includes sites/*/media/ deliberately — that's the one thing with no
# other backup, since it's intentionally un-versioned in git.
#
# Usage:
#   bash tools/dev/backup-to-laptop.sh [--dry-run]

set -euo pipefail

cd "$(dirname "$0")/../.." || exit 1

REMOTE="${REMOTE:-wingchun}"
DEST="${DEST:-/home/dave/Dropbox/Code/web_sites/}"

RSYNC_FLAGS="-avz --delete --exclude=.git/ --exclude=__pycache__/ --exclude=.venv/ --exclude=.pytest_cache/ --exclude=.ruff_cache/"

if [[ "${1:-}" == "--dry-run" ]]; then
    RSYNC_FLAGS="$RSYNC_FLAGS --dry-run"
    echo "[DRY RUN] no files will actually be copied"
fi

echo "Backing up $(pwd) -> $REMOTE:$DEST"
# shellcheck disable=SC2086
rsync $RSYNC_FLAGS ./ "$REMOTE:$DEST"

echo "[DONE] backup complete."
