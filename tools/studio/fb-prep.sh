#!/usr/bin/env bash
# fb-prep.sh — make web/Facebook-ready copies of a folder of JPEGs.
#
# Never touches the originals. Mirrors the source folder structure into the
# output folder. Safe to re-run: existing outputs are skipped unless -f.
#
# Per image:
#   - applies EXIF rotation (-auto-orient) so nothing comes out sideways
#   - shrinks so the long edge is at most MAX_EDGE px (never enlarges)
#   - light sharpen, only on images that were actually shrunk
#   - strips metadata (EXIF, GPS, thumbnails) but keeps the color profile
#   - saves as progressive JPEG at QUALITY
#   - optional (-e): gentle auto contrast/levels, handy for faded scans
#   - if a small image would come out *bigger* than the original, the
#     original is copied instead (unless -e was used)

set -euo pipefail

MAX_EDGE=2048
QUALITY=85
ENHANCE=0
FORCE=0

usage() {
  cat <<EOF
Usage: ${0##*/} [-s max_edge] [-q quality] [-e] [-f] SOURCE_DIR OUTPUT_DIR

  -s N   max length of the long edge in px   (default: $MAX_EDGE)
  -q N   JPEG quality 1-100                  (default: $QUALITY)
  -e     enhance: gentle auto contrast/levels (try on a few first)
  -f     force: overwrite existing outputs
  -h     this help
EOF
}

die() { echo "Error: $*" >&2; exit 1; }

while getopts ":s:q:efh" opt; do
  case $opt in
    s) MAX_EDGE=$OPTARG ;;
    q) QUALITY=$OPTARG ;;
    e) ENHANCE=1 ;;
    f) FORCE=1 ;;
    h) usage; exit 0 ;;
    *) usage >&2; exit 1 ;;
  esac
done
shift $((OPTIND - 1))
[[ $# -eq 2 ]] || { usage >&2; exit 1; }

[[ $MAX_EDGE =~ ^[0-9]+$ ]] || die "-s must be a number"
[[ $QUALITY  =~ ^[0-9]+$ && $QUALITY -ge 1 && $QUALITY -le 100 ]] || die "-q must be 1-100"

SRC=$(realpath -- "$1")
DST=$(realpath -m -- "$2")
[[ -d $SRC ]] || die "source '$1' is not a directory"
case "$DST/" in
  "$SRC/"*) die "output folder must not be the source folder or inside it" ;;
esac

# ImageMagick 7 uses 'magick'; 6 uses 'convert'/'identify'.
if command -v magick >/dev/null 2>&1; then
  IM=(magick); ID=(magick identify)
elif command -v convert >/dev/null 2>&1; then
  IM=(convert); ID=(identify)
else
  die "ImageMagick not found"
fi

mkdir -p -- "$DST"

done_n=0; skipped=0; kept=0; failed=0

while IFS= read -r -d '' in; do
  rel=${in#"$SRC"/}
  out="$DST/$rel"

  if [[ -e $out && $FORCE -eq 0 ]]; then
    skipped=$((skipped + 1)); continue
  fi
  mkdir -p -- "$(dirname -- "$out")"

  if ! read -r w h < <("${ID[@]}" -format '%w %h\n' "${in}[0]" 2>/dev/null); then
    echo "  FAILED (unreadable): $rel" >&2
    failed=$((failed + 1)); continue
  fi
  long=$(( w > h ? w : h ))

  args=( "${in}[0]" -auto-orient +profile '!icc,*' )
  if (( ENHANCE )); then
    args+=( -contrast-stretch 0.3%x0.3% )
  fi
  resized=0
  if (( long > MAX_EDGE )); then
    args+=( -resize "${MAX_EDGE}x${MAX_EDGE}>" -unsharp 0x0.75+0.75+0.008 )
    resized=1
  fi
  args+=( -sampling-factor 4:2:0 -interlace Plane -quality "$QUALITY" "$out" )

  if ! "${IM[@]}" "${args[@]}"; then
    echo "  FAILED: $rel" >&2
    rm -f -- "$out"
    failed=$((failed + 1)); continue
  fi

  in_sz=$(stat -c %s -- "$in")
  out_sz=$(stat -c %s -- "$out")
  if (( !resized && !ENHANCE && out_sz >= in_sz )); then
    cp -- "$in" "$out"
    kept=$((kept + 1))
    printf '  kept original  %-50s %5d KB\n' "$rel" $((in_sz / 1024))
  else
    printf '  %4dx%-4d -> ok %-50s %5d KB -> %5d KB\n' \
      "$w" "$h" "$rel" $((in_sz / 1024)) $((out_sz / 1024))
  fi
  done_n=$((done_n + 1))
done < <(find "$SRC" -type f \( -iname '*.jpg' -o -iname '*.jpeg' \) -print0 | sort -z)

echo
echo "Processed: $done_n  (originals kept as-is: $kept)  Skipped existing: $skipped  Failed: $failed"
echo "Source size: $(du -sh -- "$SRC" | cut -f1)   Output size: $(du -sh -- "$DST" | cut -f1)"
