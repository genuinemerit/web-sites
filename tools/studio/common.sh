# shellcheck shell=bash
# tools/studio/common.sh — shared by the prep tools (sourced, not run).
#
# Output folder rules (design/studio.md, 2026-10-15):
#   -o DIR       wins, for one-off jobs outside the sites
#   --site NAME  sites/NAME/<type folder>
#   otherwise    the site all the sources are inside (sites/NAME/...)
#   none of these: a usage error - there is no default folder.
# Type folders: images static/img, PDFs static/docs (both in git),
# audio/video media (gitignored, deployed separately).

STUDIO_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)

# normalize NAME [FALLBACK] - ASCII, lowercase, words joined by "_".
normalize() {
  local s=$1
  s=$(printf '%s' "$s" | LC_ALL=C.UTF-8 iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null || printf '%s' "$s")
  s=$(printf '%s' "$s" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//')
  printf '%s' "${s:-${2:-file}}"
}

# site_of FILE - print the site a file is inside (sites/NAME/...), or
# nothing. sites/_shared and sites/heirloom are not sites.
site_of() {
  local path rel name
  path=$(realpath -m -- "$1")
  [[ "$path" == "$STUDIO_REPO/sites/"?* ]] || return 0
  rel=${path#"$STUDIO_REPO/sites/"}
  name=${rel%%/*}
  [[ "$name" == _* || "$name" == heirloom ]] || printf '%s' "$name"
}

# resolve_outdir TYPE_FOLDER FILE... - set OUTDIR from -o (OUTDIR),
# --site (SITE) or the files' site; exit 2 if none of them decides it.
resolve_outdir() {
  local type_dir=$1 f s
  shift
  if [[ -n "$OUTDIR" ]]; then
    OUTDIR=$(realpath -m -- "$OUTDIR"); return 0
  fi
  if [[ -z "$SITE" ]]; then
    for f in "$@"; do
      s=$(site_of "$f")
      if [[ -z "$s" ]]; then SITE=""; break; fi
      if [[ -n "$SITE" && "$s" != "$SITE" ]]; then SITE=""; break; fi
      SITE=$s
    done
    if [[ -z "$SITE" ]]; then
      echo "Can't tell which site these are for: use --site NAME or -o DIR" >&2
      exit 2
    fi
  fi
  if ! [[ "$SITE" =~ ^[a-z0-9][a-z0-9_-]*$ && "$SITE" != heirloom \
          && -d "$STUDIO_REPO/sites/$SITE" ]]; then
    echo "No such site: $SITE (a folder in sites/)" >&2
    exit 2
  fi
  OUTDIR="$STUDIO_REPO/sites/$SITE/$type_dir"
}
