#!/usr/bin/env bash
# prep.sh — prep every media file for one site, then check the result.
#
# design/studio.md, step 5. Sends each file to the right tool by type:
#   images (JPEG, PNG, WebP, HEIC/HEIF, AVIF, TIFF, GIF, BMP) -> img_prep.sh
#     -> sites/<site>/static/img/
#   PDFs                                                      -> pdf_prep.sh
#     -> sites/<site>/static/docs/
#   sound and video (MP3, M4A, AAC, WAV, FLAC, OGG, Opus, WMA, AIFF,
#     MP4, MOV, M4V, MKV, WebM, AVI)                          -> av_prep.sh
#     -> sites/<site>/media/
# then runs tools/dev/check_media.py over the whole site, so anything
# unprepped - new or old - shows up straight away.
#
# Inputs default to sites/<site>/raw/ (the originals inbox: gitignored,
# backed up to Dropbox). Any other type of file is reported and counts
# as a failure; nothing is silently left behind. Each tool's own rules
# apply: originals untouched, no overwriting, no writing beside a source.
# For a tool's special options (--preset, --keep-info, --max-edge,
# --loudnorm, ...) run that tool directly with --site.
#
# Exit status: 0 if every file was prepped (or skipped on purpose) and
# the site passes the media check, 1 otherwise, 2 for usage errors.

set -uo pipefail

# shellcheck source=tools/studio/common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh" || exit 1
STUDIO_DIR="$STUDIO_REPO/tools/studio"

DRY_RUN=0
SKIP_EXISTING=0
MAP_FILE=""

usage() {
  cat <<'HELP'
Usage: prep.sh [options] SITE [FILE_OR_DIR ...]

Preps every image, PDF, sound and video file for SITE into the site's
folders (static/img/, static/docs/, media/), then checks the site's
media. Inputs default to sites/SITE/raw/. Folders are searched
recursively; hidden files are ignored.

  --dry-run         Show what would be done, change nothing (no check)
  --map FILE        Also write "source<TAB>output" file names to FILE
  --skip-existing   Skip inputs whose output already exists (default: error)
  -h, --help        Show this help

Examples:
  prep.sh taiji                       # everything in sites/taiji/raw/
  prep.sh --dry-run music ~/recordings/new/
HELP
}

need_arg() {
  if (($# < 2)); then echo "Missing value for $1" >&2; exit 2; fi
}

ARGS=()
while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --map) need_arg "$@"; MAP_FILE=$2; shift 2 ;;
    --skip-existing) SKIP_EXISTING=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; ARGS+=("$@"); break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
if ((${#ARGS[@]} == 0)); then usage >&2; exit 2; fi
SITE=${ARGS[0]}
INPUTS=("${ARGS[@]:1}")
# Validates SITE (exit 2 if unknown); the folder itself isn't used here.
# shellcheck disable=SC2034 # OUTDIR is read by resolve_outdir (common.sh)
OUTDIR=""
resolve_outdir media
if ((${#INPUTS[@]} == 0)); then
  INPUTS=("$STUDIO_REPO/sites/$SITE/raw")
  if [[ ! -d "${INPUTS[0]}" ]]; then
    echo "Nothing to do: sites/$SITE/raw/ doesn't exist" >&2; exit 1
  fi
fi

# Expand folders (recursively, hidden files skipped, sorted) into files.
FILES=()
for input in "${INPUTS[@]}"; do
  if [[ -d "$input" ]]; then
    while IFS= read -r -d '' f; do FILES+=("$f"); done \
      < <(find "$input" -type f ! -name '.*' -print0 | sort -z)
  else
    FILES+=("$input")
  fi
done

IMAGES=() PDFS=() AV=() failures=0
for f in "${FILES[@]}"; do
  base=${f##*/}; ext=""
  [[ "$base" == *.* ]] && ext=${base##*.} && ext=${ext,,}
  case "$ext" in
    jpg|jpeg|png|webp|heic|heif|avif|tif|tiff|gif|bmp) IMAGES+=("$f") ;;
    pdf) PDFS+=("$f") ;;
    mp3|m4a|aac|wav|flac|ogg|opus|wma|aif|aiff|mp4|mov|m4v|mkv|webm|avi) AV+=("$f") ;;
    *)
      if [[ -f "$f" ]]; then
        echo "UNSUPPORTED (not an image, PDF, sound or video file): $f" >&2
      else
        echo "FAILED (not a file): $f" >&2
      fi
      failures=$((failures + 1)) ;;
  esac
done

COMMON=(--site "$SITE")
((DRY_RUN)) && COMMON+=(--dry-run)
((SKIP_EXISTING)) && COMMON+=(--skip-existing)
if [[ -n "$MAP_FILE" ]]; then
  printf 'source\toutput\n' > "$MAP_FILE" || exit 1
fi

# run_tool TOOL FILE... - one call per tool; its map rows are appended.
run_tool() {
  local tool=$1 status map
  shift
  (($#)) || return 0
  echo "== $tool ($# file(s))"
  if [[ -n "$MAP_FILE" ]]; then
    map=$(mktemp) || return 1
    bash "$STUDIO_DIR/$tool" "${COMMON[@]}" --map "$map" -- "$@"
    status=$?
    tail -n +2 -- "$map" >> "$MAP_FILE"
    rm -f -- "$map"
    return "$status"
  fi
  bash "$STUDIO_DIR/$tool" "${COMMON[@]}" -- "$@"
}

run_tool img_prep.sh "${IMAGES[@]}" || failures=$((failures + 1))
run_tool pdf_prep.sh "${PDFS[@]}" || failures=$((failures + 1))
run_tool av_prep.sh "${AV[@]}" || failures=$((failures + 1))

if ((DRY_RUN)); then
  echo "Dry run: ${#FILES[@]} file(s) for $SITE; nothing written, no check run."
  ((failures == 0)); exit
fi

echo "== media check (sites/$SITE)"
# The project's Poetry environment has Pillow. The tests' throwaway repo
# has no pyproject.toml - they already run inside that environment.
CHECK=(python3 "$STUDIO_REPO/tools/dev/check_media.py" "$STUDIO_REPO/sites/$SITE")
if [[ -f "$STUDIO_REPO/pyproject.toml" ]]; then
  PATH="$HOME/.local/bin:$PATH"
  CHECK=(poetry -C "$STUDIO_REPO" run "${CHECK[@]}")
fi
"${CHECK[@]}" || failures=$((failures + 1))

if ((failures)); then
  echo "prep.sh: $failures problem(s) - see above." >&2
  exit 1
fi
echo "prep.sh: $SITE done, all media prepped."
