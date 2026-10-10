#!/usr/bin/env bash
# av_prep.sh — make web-ready copies of audio and video files.
#
# David's prototype (2026-10-10), revised the same day after review
# (design/music.md, step 9). The standard prep step for any audio or
# video published on these sites.
#
# Never touches the originals. Never overwrites an output. Decides by
# the real codec (ffprobe), not the file extension.
#
# Run it on ORIGINALS, not on its own outputs: a re-encoded video can
# still sit above the copy threshold and would be re-encoded again,
# losing a little quality each time.
#
# Per file:
#   - output name: ASCII, lowercase, words joined by "_" (URL-safe);
#     videos get a "_video" suffix
#   - all metadata and chapters are dropped (tags, dates, and phone
#     location data in particular) - only the media itself is kept
#   - video -> MP4 (H.264 + AAC, yuv420p, "faststart" so playback starts
#     before the download ends). H.264 that is already web-ready - within
#     the height cap AND at or below COPY_MAX_BPP bits per pixel per frame
#     (0.045, about what CRF 23 produces; ~1 Mbps at 720p25) - is copied
#     as-is (remuxed), not re-encoded. Higher-bitrate H.264 (typical phone
#     video) is re-encoded. Taller video is scaled down to --max-height
#     (default 1080).
#   - MP3 / AAC audio at 192 kbps or less -> copied as-is (no quality
#     loss from re-encoding); higher bit rates are re-encoded
#   - any other audio (WAV, FLAC, ALAC, Opus, Vorbis, WMA, ...) -> MP3
#     (LAME V2, ~190 kbps). Masters stay wherever they live (Dropbox);
#     these are web copies.
#   - album art embedded in audio is dropped (it is not the recording)
#   - if a re-encode comes out no smaller than the source and the source
#     is already web-ready, the source's streams are copied instead
#   - optional --loudnorm: EBU R128 loudness normalization of the audio
#     (forces audio re-encoding)
#
# Two inputs that would produce the same output name are an error (the
# second is never silently dropped). An output that already exists is an
# error too, unless --skip-existing (handy when re-running over a folder).
#
# Exit status: 0 if every file succeeded (or was skipped on purpose),
# 1 if any failed, 2 for usage errors.

set -uo pipefail

OUTDIR="${WEBMEDIA_DIR:-$HOME/webmedia}"
FORCE=0
CRF=23
MAX_HEIGHT=1080
DRY_RUN=0
SKIP_EXISTING=0
LOUDNORM=0
MAP_FILE=""
# Copy H.264 as-is only at or below this many bits per pixel per frame
# (in thousandths: 45 = 0.045). Chosen 2026-10-10 from music's videos:
# 720p sources at 0.050-0.081 re-encoded at CRF 23 to ~0.040, 18%+
# smaller with no visible loss (David's check).
COPY_MAX_BPP_MILLI=45

usage() {
  cat <<'HELP'
Usage: av_prep.sh [options] FILE_OR_DIR [FILE_OR_DIR ...]

Makes web-ready copies of audio/video files (see the comments at the top
of the script for exactly what happens to each kind of file). Folders
are searched recursively; hidden files are ignored.

  -o DIR            Output folder (default: ~/webmedia or $WEBMEDIA_DIR)
  --dry-run         Show what would be done, change nothing
  --map FILE        Also write "source<TAB>output" file names to FILE
  --skip-existing   Skip inputs whose output already exists (default: error)
  --force           Re-encode even when the source could be copied as-is
                    (by default: modest MP3/AAC and low-bitrate H.264 are copied)
  --crf N           H.264 quality, 18-28 (default 23; lower = better/larger)
  --max-height N    Scale taller video down to N pixels (default 1080;
                    0 = never scale)
  --loudnorm        Normalize audio loudness (EBU R128, -16 LUFS)
  -h, --help        Show this help

Examples:
  av_prep.sh song.wav
  av_prep.sh -o ~/web/music --map renames.tsv ~/recordings/
  av_prep.sh --dry-run *.mp4
HELP
}

need_arg() {
  if (($# < 2)); then echo "Missing value for $1" >&2; exit 2; fi
}

INPUTS=()
while (($#)); do
  case "$1" in
    -o) need_arg "$@"; OUTDIR=$2; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --map) need_arg "$@"; MAP_FILE=$2; shift 2 ;;
    --skip-existing) SKIP_EXISTING=1; shift ;;
    --force) FORCE=1; shift ;;
    --crf) need_arg "$@"; CRF=$2; shift 2 ;;
    --max-height) need_arg "$@"; MAX_HEIGHT=$2; shift 2 ;;
    --loudnorm) LOUDNORM=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; INPUTS+=("$@"); break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) INPUTS+=("$1"); shift ;;
  esac
done
if ((${#INPUTS[@]} == 0)); then usage >&2; exit 2; fi
if ! [[ "$CRF" =~ ^(1[89]|2[0-8])$ ]]; then echo 'CRF must be 18-28' >&2; exit 2; fi
if ! [[ "$MAX_HEIGHT" =~ ^(0|[1-9][0-9]{2,3})$ ]]; then echo 'max-height must be 0 or 100-9999' >&2; exit 2; fi
for cmd in ffmpeg ffprobe iconv; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing dependency: $cmd" >&2; exit 1; }
done

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

if ((DRY_RUN == 0)); then
  mkdir -p -- "$OUTDIR" || exit 1
  OUTDIR=$(cd -- "$OUTDIR" && pwd -P)
fi
if [[ -n "$MAP_FILE" ]]; then
  printf 'source\toutput\n' > "$MAP_FILE" || exit 1
fi

normalize() {
  local s=$1
  s=$(printf '%s' "$s" | LC_ALL=C.UTF-8 iconv -f UTF-8 -t ASCII//TRANSLIT 2>/dev/null || printf '%s' "$s")
  s=$(printf '%s' "$s" | LC_ALL=C tr '[:upper:]' '[:lower:]' | LC_ALL=C sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//')
  printf '%s' "${s:-media}"
}

# probe FILE STREAM_SPECIFIER FIELD - first value, or empty.
# "V" (capital) selects real video, never embedded cover art/thumbnails.
probe() {
  ffprobe -v error -select_streams "$2" -show_entries "stream=$3" \
    -of default=noprint_wrappers=1:nokey=1 "$1" 2>/dev/null | head -n 1
}

size_of() { stat -c %s -- "$1"; }

# run_ffmpeg SRC DEST ARGS... - write DEST (refusing to overwrite);
# on failure remove the partial output this call created.
run_ffmpeg() {
  local src=$1 dest=$2; shift 2
  # -nostdin keeps FFmpeg from consuming input meant for the loop.
  if ffmpeg -hide_banner -nostdin -loglevel error -stats -n -i "$src" "$@" "$dest"; then
    return 0
  fi
  rm -f -- "$dest"
  return 1
}

declare -A CLAIMED=()   # output path -> source that claimed it this run
done_count=0 copied=0 encoded=0 skipped=0 failures=0

process() {
  local src=$1 base stem safe audio video height width pix vbr fps abr ext dest
  local vmode="" amode="" web_ready=0 action
  if [[ ! -f "$src" ]]; then echo "FAILED (not a file): $src" >&2; return 1; fi
  base=${src##*/}; stem=${base%.*}; safe=$(normalize "$stem")
  audio=$(probe "$src" a:0 codec_name)
  video=$(probe "$src" V:0 codec_name)
  abr=$(probe "$src" a:0 bit_rate)
  [[ "$abr" =~ ^[0-9]+$ ]] || abr=0

  local -a args=(-map_metadata -1 -map_chapters -1)
  local -a copy_args=()   # stream-copy fallback for keep-smaller

  if [[ -n "$video" ]]; then
    ext=mp4
    [[ "$safe" == *_video ]] || safe="${safe}_video"
    height=$(probe "$src" V:0 height); [[ "$height" =~ ^[0-9]+$ ]] || height=0
    width=$(probe "$src" V:0 width); [[ "$width" =~ ^[0-9]+$ ]] || width=0
    pix=$(probe "$src" V:0 pix_fmt)
    vbr=$(probe "$src" V:0 bit_rate); [[ "$vbr" =~ ^[0-9]+$ ]] || vbr=0
    fps=$(probe "$src" V:0 avg_frame_rate)
    # Bit-rate ceiling for copying, in bits/s: bpp x width x height x fps.
    # An unknown bit rate or frame rate means "not web-ready" (re-encode;
    # keep-the-smaller-file still protects against growth).
    local ceiling=0 num=0 den=1
    if [[ "$fps" =~ ^([0-9]+)/([0-9]+)$ ]] && ((BASH_REMATCH[2] > 0)); then
      num=${BASH_REMATCH[1]}; den=${BASH_REMATCH[2]}
      ceiling=$((COPY_MAX_BPP_MILLI * width * height * num / den / 1000))
    fi
    local too_tall=0
    if ((MAX_HEIGHT > 0 && height > MAX_HEIGHT)); then too_tall=1; fi
    if [[ "$video" == h264 && "$pix" == yuv420p ]] && ((too_tall == 0)) \
       && ((vbr > 0 && ceiling > 0 && vbr <= ceiling)) \
       && [[ -z "$audio" || "$audio" == aac ]]; then
      web_ready=1
    fi
    args+=(-map 0:V:0 -map '0:a:0?')
    if ((FORCE == 0 && web_ready == 1 && LOUDNORM == 0)); then
      vmode=copy; args+=(-c copy)
    else
      vmode=encode
      args+=(-c:v libx264 -preset medium -crf "$CRF" -pix_fmt yuv420p)
      ((too_tall)) && args+=(-vf "scale=-2:${MAX_HEIGHT}")
      if [[ "$audio" == aac ]] && ((LOUDNORM == 0)); then
        args+=(-c:a copy)
      else
        args+=(-c:a aac -b:a 160k)
        ((LOUDNORM)) && args+=(-af loudnorm=I=-16:LRA=11:TP=-1.5)
      fi
    fi
    args+=(-movflags +faststart)
    copy_args=(-map_metadata -1 -map_chapters -1 -map 0:V:0 -map '0:a:0?' -c copy -movflags +faststart)
  elif [[ -n "$audio" ]]; then
    case "$audio" in
      mp3) ext=mp3; web_ready=1 ;;
      aac) ext=m4a; web_ready=1 ;;
      *)   ext=mp3 ;;   # WAV/FLAC/ALAC/Opus/Vorbis/WMA/...: encode to MP3
    esac
    args+=(-map 0:a:0 -vn)
    if ((FORCE == 0 && web_ready == 1 && LOUDNORM == 0 && abr > 0 && abr <= 192000)); then
      amode=copy; args+=(-c:a copy)
    else
      amode=encode
      if [[ "$ext" == m4a ]]; then args+=(-c:a aac -b:a 160k); else args+=(-c:a libmp3lame -q:a 2); fi
      ((LOUDNORM)) && args+=(-af loudnorm=I=-16:LRA=11:TP=-1.5)
    fi
    copy_args=(-map_metadata -1 -map_chapters -1 -map 0:a:0 -vn -c:a copy)
  else
    echo "FAILED (no audio or video found): $src" >&2; return 1
  fi

  dest="$OUTDIR/$safe.$ext"
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

  if [[ "$vmode" == copy || "$amode" == copy ]]; then action=copy; else action=encode; fi
  echo "${action^^}: $src -> $dest"
  [[ -n "$MAP_FILE" ]] && printf '%s\t%s\n' "$base" "$safe.$ext" >> "$MAP_FILE"
  if ((DRY_RUN)); then return 0; fi

  run_ffmpeg "$src" "$dest" "${args[@]}" || { echo "FAILED: $src" >&2; return 1; }

  # Keep the smaller file: a re-encode of an already web-ready source
  # that came out no smaller is replaced by a plain copy of its streams.
  if [[ "$action" == encode ]] && ((web_ready == 1 && LOUDNORM == 0)) \
     && (($(size_of "$dest") >= $(size_of "$src"))); then
    rm -f -- "$dest"
    run_ffmpeg "$src" "$dest" "${copy_args[@]}" || { echo "FAILED: $src" >&2; return 1; }
    action=copy
    echo "  (re-encode was not smaller - kept the original streams)"
  fi
  if [[ "$action" == copy ]]; then copied=$((copied + 1)); else encoded=$((encoded + 1)); fi
  done_count=$((done_count + 1))
}

for src in "${FILES[@]}"; do
  process "$src" || failures=$((failures + 1))
done

if ((DRY_RUN)); then
  echo "Dry run: ${#FILES[@]} input(s), $failures problem(s); nothing written."
else
  echo "Done: $done_count ($encoded encoded, $copied copied), $skipped skipped, $failures failed."
fi
((failures == 0))
