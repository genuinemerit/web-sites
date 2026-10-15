#!/usr/bin/env bash
# tools/dev/install-git-hooks.sh — link this repo's git hooks into
# .git/hooks (git doesn't version that folder). Run once per clone; safe
# to re-run. No sudo.
#
#   pre-commit -> tools/dev/pre-commit-hook.sh (unprepped media check)

set -euo pipefail

cd "$(dirname "$0")/../.."

hooks_dir=$(git rev-parse --git-path hooks)
link="$hooks_dir/pre-commit"
target="../../tools/dev/pre-commit-hook.sh"

if [[ -L "$link" && "$(readlink -- "$link")" == "$target" ]]; then
  echo "pre-commit hook already installed."
  exit 0
fi
if [[ -e "$link" || -L "$link" ]]; then
  echo "Refusing to replace the existing $link - look at it, move it aside, re-run." >&2
  exit 1
fi
mkdir -p -- "$hooks_dir"
ln -s -- "$target" "$link"
echo "Installed: $link -> $target"
