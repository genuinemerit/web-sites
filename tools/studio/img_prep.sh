#!/usr/bin/env bash
# img_prep.sh — make web-ready copies of images.
#
# David's fb-prep.sh (web/Facebook-ready JPEGs), renamed 2026-10-15 and
# brought in line with av_prep.sh and pdf_prep.sh the same day
# (design/studio.md): files or folders in, one output folder, URL-safe
# names, never overwrites, and no metadata left in "kept original"
# copies. The image processing itself is unchanged.
#
# Writes to sites/<site>/static/img/ - the site given by --site, or the one
# the sources are in; -o DIR for anywhere else (rules: common.sh).
#
# Never touches the originals. Never overwrites an output. Never writes
# into the folder a source image lives in.
#
# Per image:
#   - output name: ASCII, lowercase, words joined by "_" (URL-safe)
#   - output format: JPEG, or PNG if the image has transparency
#   - applies EXIF rotation (-auto-orient) so nothing comes out sideways
#   - shrinks so the long edge is at most MAX_EDGE px (never enlarges)
#   - light sharpen, only on images that were actually shrunk
#   - strips metadata (EXIF, GPS, XMP, comments, PNG dates) but keeps the
#     colour profile
#   - saves JPEG as progressive at QUALITY
#   - optional (--enhance): gentle auto contrast/levels, handy for faded
#     scans
#   - if a JPEG would come out *bigger* than the original JPEG (and was
#     not shrunk or enhanced), the original is kept instead - its pixels
#     untouched, its metadata stripped losslessly by jpegtran. Not when
#     the original needs EXIF rotation: that is only applied by the
#     re-save.
#   - multi-frame images (animated GIF, multi-page TIFF) are refused
#
# Inputs: JPEG, PNG, WebP, HEIC/HEIF, AVIF, TIFF, GIF, BMP. Folders are
# searched recursively for those; hidden files are ignored.
#
# Two inputs that would produce the same output name are an error (the
# second is never silently dropped). An output that already exists is an
# error too, unless --skip-existing (handy when re-running over a folder).
#
# Exit status: 0 if every file succeeded (or was skipped on purpose),
# 1 if any failed, 2 for usage errors.

set -uo pipefail

# shellcheck source=tools/studio/common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh" || exit 1

OUTDIR=""
SITE=""
MAX_EDGE=2048
QUALITY=85
ENHANCE=0
DRY_RUN=0
SKIP_EXISTING=0
MAP_FILE=""

usage() {
  cat <<'HELP'
Usage: img_prep.sh [options] FILE_OR_DIR [FILE_OR_DIR ...]

Makes web-ready copies of images (see the comments at the top of the
script for exactly what happens to each one). Folders are searched
recursively for images; hidden files are ignored.

  --site NAME         Write to sites/NAME/static/img/ (default: the site
                      the sources are in, e.g. sites/NAME/raw/)
  -o DIR              Write to DIR instead (one-off jobs outside the sites);
                      must not be a folder any source image is in
  --dry-run           Show what would be done, change nothing
  --map FILE          Also write "source<TAB>output" file names to FILE
  --skip-existing     Skip inputs whose output already exists (default: error)
  -s, --max-edge N    Max length of the long edge in px (default: 2048)
  -q, --quality N     JPEG quality 1-100 (default: 85)
  -e, --enhance       Gentle auto contrast/levels (try on a few first)
  -h, --help          Show this help

Examples:
  img_prep.sh sites/taiji/raw/               # -> sites/taiji/static/img/
  img_prep.sh --site taiji --map renames.tsv ~/Pictures/trip/
  img_prep.sh -o ~/facebook -s 1600 --dry-run *.png
HELP
}

need_arg() {
  if (($# < 2)); then echo "Missing value for $1" >&2; exit 2; fi
}

INPUTS=()
while (($#)); do
  case "$1" in
    -o) need_arg "$@"; OUTDIR=$2; shift 2 ;;
    --site) need_arg "$@"; SITE=$2; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --map) need_arg "$@"; MAP_FILE=$2; shift 2 ;;
    --skip-existing) SKIP_EXISTING=1; shift ;;
    -s|--max-edge) need_arg "$@"; MAX_EDGE=$2; shift 2 ;;
    -q|--quality) need_arg "$@"; QUALITY=$2; shift 2 ;;
    -e|--enhance) ENHANCE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; INPUTS+=("$@"); break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) INPUTS+=("$1"); shift ;;
  esac
done
if ((${#INPUTS[@]} == 0)); then usage >&2; exit 2; fi
if ! [[ "$MAX_EDGE" =~ ^[1-9][0-9]{1,4}$ ]]; then echo 'max-edge must be 10-99999' >&2; exit 2; fi
if ! [[ "$QUALITY" =~ ^([1-9][0-9]?|100)$ ]]; then echo 'quality must be 1-100' >&2; exit 2; fi

# ImageMagick 7 uses 'magick'; 6 uses 'convert'/'identify'.
if command -v magick >/dev/null 2>&1; then
  IM=(magick); ID=(magick identify)
elif command -v convert >/dev/null 2>&1; then
  IM=(convert); ID=(identify)
else
  echo "Missing dependency: ImageMagick" >&2; exit 1
fi
for cmd in jpegtran iconv; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing dependency: $cmd" >&2; exit 1; }
done

# Expand folders (recursively, hidden files skipped, sorted) into images.
FILES=()
for input in "${INPUTS[@]}"; do
  if [[ -d "$input" ]]; then
    while IFS= read -r -d '' f; do FILES+=("$f"); done < <(
      find "$input" -type f ! -name '.*' \( -iname '*.jpg' -o -iname '*.jpeg' \
        -o -iname '*.png' -o -iname '*.webp' -o -iname '*.heic' -o -iname '*.heif' \
        -o -iname '*.avif' -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.gif' \
        -o -iname '*.bmp' \) -print0 | sort -z)
  else
    FILES+=("$input")
  fi
done

resolve_outdir static/img "${INPUTS[@]}"
OUTDIR_REAL=$(realpath -m -- "$OUTDIR")
if ((DRY_RUN == 0)); then
  mkdir -p -- "$OUTDIR" || exit 1
fi
if [[ -n "$MAP_FILE" ]]; then
  printf 'source\toutput\n' > "$MAP_FILE" || exit 1
fi


size_of() { stat -c %s -- "$1"; }
kb() { echo $(( ($1 + 1023) / 1024 )); }

declare -A CLAIMED=()   # output path -> source that claimed it this run
TMP_OUT=""
cleanup() { rm -f -- "$TMP_OUT"; TMP_OUT=""; }
trap cleanup EXIT

done_count=0 kept=0 skipped=0 failures=0

process() {
  local src=$1 base stem safe src_dir info w h frames opaque magic orient
  local ext dest long resized=0 in_sz out_sz note=""
  if [[ ! -f "$src" ]]; then echo "FAILED (not a file): $src" >&2; return 1; fi
  src_dir=$(realpath -- "$(dirname -- "$src")")
  if [[ "$src_dir" == "$OUTDIR_REAL" || "$src_dir" == "$OUTDIR_REAL"/* ]]; then
    echo "FAILED (source is inside the output folder - use another -o): $src" >&2
    return 1
  fi
  # One line per frame: "format width height opaque orientation".
  if ! info=$("${ID[@]}" -format '%m %w %h %[opaque] %[EXIF:Orientation]\n' -- "$src" 2>/dev/null); then
    echo "FAILED (not an image ImageMagick can read): $src" >&2; return 1
  fi
  frames=$(printf '%s\n' "$info" | grep -c .)
  if ((frames != 1)); then
    echo "FAILED (multi-frame image - animated GIF or multi-page TIFF): $src" >&2; return 1
  fi
  read -r magic w h opaque orient <<<"$info"

  base=${src##*/}; stem=${base%.*}; safe=$(normalize "$stem" image)
  if [[ "$opaque" == False ]]; then ext=png; else ext=jpg; fi
  dest="$OUTDIR_REAL/$safe.$ext"
  if [[ -n "${CLAIMED[$dest]:-}" ]]; then
    echo "FAILED (name clash: $src and ${CLAIMED[$dest]} both become $safe.$ext)" >&2
    return 1
  fi
  CLAIMED[$dest]=$src
  if [[ -e "$dest" ]]; then
    if ((SKIP_EXISTING)); then
      echo "SKIP (output exists): $dest"; skipped=$((skipped + 1)); return 0
    fi
    echo "FAILED (output exists - remove it or use --skip-existing): $dest" >&2
    return 1
  fi

  echo "PREP: $src -> $dest"
  [[ -n "$MAP_FILE" ]] && printf '%s\t%s\n' "$base" "$safe.$ext" >> "$MAP_FILE"
  if ((DRY_RUN)); then return 0; fi

  long=$(( w > h ? w : h ))
  local -a args=( "${src}[0]" -auto-orient +profile '!icc,*' )
  ((ENHANCE)) && args+=( -contrast-stretch 0.3%x0.3% )
  if ((long > MAX_EDGE)); then
    args+=( -resize "${MAX_EDGE}x${MAX_EDGE}>" -unsharp 0x0.75+0.75+0.008 )
    resized=1
  fi
  if [[ "$ext" == jpg ]]; then
    args+=( -sampling-factor 4:2:0 -interlace Plane -quality "$QUALITY" )
  else
    args+=( -define 'png:exclude-chunks=date,time' )
  fi

  # Write a hidden temp file beside the output, then link it into place:
  # ln refuses to replace an existing file.
  TMP_OUT=$(mktemp -p "$OUTDIR_REAL" --suffix=".$ext" .img_prep.XXXXXX) || return 1
  if ! "${IM[@]}" "${args[@]}" "${ext^^}:$TMP_OUT"; then
    echo "FAILED (ImageMagick): $src" >&2; cleanup; return 1
  fi

  in_sz=$(size_of "$src"); out_sz=$(size_of "$TMP_OUT")
  if [[ "$magic" == JPEG && "$ext" == jpg ]] && ((!resized && !ENHANCE && out_sz >= in_sz)) \
     && [[ -z "$orient" || "$orient" == 1 ]]; then
    # Keep the original pixels; drop everything but the colour profile.
    if ! jpegtran -copy icc -optimize -progressive -outfile "$TMP_OUT" "$src"; then
      echo "FAILED (jpegtran): $src" >&2; cleanup; return 1
    fi
    out_sz=$(size_of "$TMP_OUT")
    note=" (kept original, metadata stripped)"
    kept=$((kept + 1))
  fi
  # mktemp makes owner-only files; give the output the usual umask mode.
  chmod -- "$(printf '%o' $((0666 & ~0$(umask))))" "$TMP_OUT" || { cleanup; return 1; }
  if ! ln -- "$TMP_OUT" "$dest"; then
    echo "FAILED (could not create $dest)" >&2; cleanup; return 1
  fi
  cleanup
  echo "  ${w}x${h}: $(kb "$in_sz") KB -> $(kb "$out_sz") KB$note"
  done_count=$((done_count + 1))
}

for src in "${FILES[@]}"; do
  process "$src" || failures=$((failures + 1))
done

if ((DRY_RUN)); then
  echo "Dry run: ${#FILES[@]} input(s), $failures problem(s); nothing written."
else
  echo "Done: $done_count ($kept kept as original), $skipped skipped, $failures failed."
fi
((failures == 0))
