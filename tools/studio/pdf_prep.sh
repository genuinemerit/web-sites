#!/usr/bin/env bash
# pdf_prep.sh — make web-ready copies of PDF files.
#
# Written 2026-10-15 from David's two starting commands (a Ghostscript
# /ebook rewrite and qpdf linearization), in the style of av_prep.sh.
#
# Writes to sites/<site>/static/docs/ - the site given by --site, or the one
# the sources are in; -o DIR for anywhere else (rules: common.sh).
#
# Never touches the originals. Never overwrites an output. Never writes
# into the folder a source PDF lives in.
#
# Per file:
#   - output name: ASCII, lowercase, words joined by "_" (URL-safe)
#   - password-protected PDFs are refused (nothing sensible to do)
#   - Ghostscript rewrites the PDF (pdfwrite, PDF 1.7, --preset ebook by
#     default: images downsampled to 150 dpi, fonts subset, duplicate
#     images shared). PDF 1.7 rather than 1.4: 1.4 has no transparency,
#     so Ghostscript would flatten it, sometimes into bitmaps.
#   - skipped for PDFs with fillable forms (Ghostscript can lose form
#     fields) and with --lossless; those get only the qpdf step
#   - if the rewrite is no smaller than the source, the source is used
#     instead (keep the smaller file)
#   - qpdf then: drops the document information (title, author, creating
#     software, creation date) and XMP metadata, packs objects into
#     compressed object streams, and linearizes ("fast web view": the
#     first page shows before the download ends). --keep-info keeps the
#     title (browsers show it in the tab) and nothing else.
#   - the result is checked with `qpdf --check` before it is kept
#
# Two inputs that would produce the same output name are an error (the
# second is never silently dropped). An output that already exists is an
# error too, unless --skip-existing (handy when re-running over a folder).
#
# qpdf on Ubuntu runs under an AppArmor profile (/etc/apparmor.d/qpdf):
# it can only open files ending in .pdf under $HOME (not in hidden
# folders directly under it), /tmp, /var/tmp, /mnt or /media. Inputs and
# the output folder must be in those places, or qpdf fails with
# "Permission denied".
#
# Exit status: 0 if every file succeeded (or was skipped on purpose),
# 1 if any failed, 2 for usage errors.

set -uo pipefail

# shellcheck source=tools/studio/common.sh
source "$(dirname -- "${BASH_SOURCE[0]}")/common.sh" || exit 1

OUTDIR=""
SITE=""
PRESET=ebook
LOSSLESS=0
KEEP_INFO=0
DRY_RUN=0
SKIP_EXISTING=0
MAP_FILE=""

usage() {
  cat <<'HELP'
Usage: pdf_prep.sh [options] FILE_OR_DIR [FILE_OR_DIR ...]

Makes smaller, web-ready copies of PDF files (see the comments at the
top of the script for exactly what happens to each file). Folders are
searched recursively for *.pdf; hidden files are ignored.

  --site NAME       Write to sites/NAME/static/docs/ (default: the site
                    the sources are in, e.g. sites/NAME/raw/)
  -o DIR            Write to DIR instead (one-off jobs outside the sites);
                    must not be a folder any source PDF is in
  --dry-run         Show what would be done, change nothing
  --map FILE        Also write "source<TAB>output" file names to FILE
  --skip-existing   Skip inputs whose output already exists (default: error)
  --preset NAME     Ghostscript quality: screen (72 dpi images),
                    ebook (150 dpi, default) or printer (300 dpi)
  --lossless        Skip Ghostscript: no image downsampling, only the
                    qpdf clean-up (metadata, object streams, linearize)
  --keep-info       Keep the document title (shown in the browser tab);
                    everything else (author, software, dates, XMP) goes
  -h, --help        Show this help

Examples:
  pdf_prep.sh sites/movement/raw/            # -> sites/movement/static/docs/
  pdf_prep.sh --site movement --map renames.tsv ~/scans/
  pdf_prep.sh -o ~/print-copies --preset printer --dry-run *.pdf
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
    --preset) need_arg "$@"; PRESET=$2; shift 2 ;;
    --lossless) LOSSLESS=1; shift ;;
    --keep-info) KEEP_INFO=1; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; INPUTS+=("$@"); break ;;
    -*) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
    *) INPUTS+=("$1"); shift ;;
  esac
done
if ((${#INPUTS[@]} == 0)); then usage >&2; exit 2; fi
if ! [[ "$PRESET" =~ ^(screen|ebook|printer)$ ]]; then echo 'preset must be screen, ebook or printer' >&2; exit 2; fi
for cmd in gs qpdf python3 iconv; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "Missing dependency: $cmd" >&2; exit 1; }
done

# Expand folders (recursively, hidden files skipped, sorted) into PDFs.
FILES=()
for input in "${INPUTS[@]}"; do
  if [[ -d "$input" ]]; then
    while IFS= read -r -d '' f; do FILES+=("$f"); done \
      < <(find "$input" -type f -iname '*.pdf' ! -name '.*' -print0 | sort -z)
  else
    FILES+=("$input")
  fi
done

# The output folder's real path (it may not exist yet on a dry run).
resolve_outdir static/docs "${INPUTS[@]}"
OUTDIR_REAL=$(realpath -m -- "$OUTDIR")
if ((DRY_RUN == 0)); then
  mkdir -p -- "$OUTDIR" || exit 1
fi
if [[ -n "$MAP_FILE" ]]; then
  printf 'source\toutput\n' > "$MAP_FILE" || exit 1
fi


size_of() { stat -c %s -- "$1"; }
human() { numfmt --to=iec --suffix=B --format='%.1f' "$1"; }

has_form() {
  qpdf --json=2 --json-key=acroform -- "$1" 2>/dev/null | grep -q '"hasacroform": true'
}

# run_gs SRC DEST - Ghostscript rewrite. "%" in the output path is
# doubled: Ghostscript reads it as a page-number pattern.
run_gs() {
  gs -q -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pdfwrite \
    -dCompatibilityLevel=1.7 -dPDFSETTINGS="/$PRESET" \
    -dDetectDuplicateImages=true \
    -sOutputFile="${2//%/%%}" -f "$1" </dev/null
}

# title_update PDF - print a qpdf --update-from-json document that
# replaces the document information with just its title; print nothing
# if the PDF has no title.
title_update() {
  qpdf --json=2 --json-key=qpdf --json-object=trailer -- "$1" 2>/dev/null \
    | python3 -I -c '
import json, subprocess, sys
head, objs = json.load(sys.stdin)["qpdf"]
info = objs["trailer"]["value"].get("/Info")
if not isinstance(info, str):
    sys.exit()
out = subprocess.run(
    ["qpdf", "--json=2", "--json-key=qpdf", f"--json-object={info}", "--", sys.argv[1]],
    capture_output=True, text=True, check=True).stdout
title = json.loads(out)["qpdf"][1][f"obj:{info}"]["value"].get("/Title")
if title:
    json.dump({"qpdf": [head, {f"obj:{info}": {"value": {"/Title": title}}}]}, sys.stdout)
' "$1"
}

# run_qpdf SRC DEST - linearize, object streams, metadata removal.
# --warning-exit-0: warnings alone are not a failure.
run_qpdf() {
  local src=$1 update
  local -a args=(--linearize --object-streams=generate --compress-streams=y --remove-metadata)
  if ((KEEP_INFO)); then
    # --update-from-json silently skips objects stored inside object
    # streams (where Ghostscript puts the document information), so
    # unpack them first.
    qpdf --warning-exit-0 --object-streams=disable -- "$src" "$TMP_PLAIN" || return 1
    src=$TMP_PLAIN
  fi
  if ((KEEP_INFO)) && update=$(title_update "$src") && [[ -n "$update" ]]; then
    printf '%s' "$update" > "$TMP_JSON" || return 1
    args+=(--update-from-json="$TMP_JSON")
  else
    args+=(--remove-info)
  fi
  qpdf --warning-exit-0 "${args[@]}" -- "$src" "$2"
}

declare -A CLAIMED=()   # output path -> source that claimed it this run
TMP_GS="" TMP_PLAIN="" TMP_OUT="" TMP_JSON=""
cleanup() {
  rm -f -- "$TMP_GS" "$TMP_PLAIN" "$TMP_OUT" "$TMP_JSON"
  TMP_GS="" TMP_PLAIN="" TMP_OUT="" TMP_JSON=""
}
trap cleanup EXIT

done_count=0 rewritten=0 cleaned=0 skipped=0 failures=0

process() {
  local src=$1 base stem safe dest src_dir mode base_pdf before after
  if [[ ! -f "$src" ]]; then echo "FAILED (not a file): $src" >&2; return 1; fi
  if [[ "$(head -c 5 -- "$src")" != "%PDF-" ]]; then
    echo "FAILED (not a PDF): $src" >&2; return 1
  fi
  src_dir=$(realpath -- "$(dirname -- "$src")")
  if [[ "$src_dir" == "$OUTDIR_REAL" || "$src_dir" == "$OUTDIR_REAL"/* ]]; then
    echo "FAILED (source is inside the output folder - use another -o): $src" >&2
    return 1
  fi
  # Exit 0 means "a password is required"; 2 and 3 mean it can be read.
  if qpdf --requires-password -- "$src"; then
    echo "FAILED (password-protected): $src" >&2; return 1
  fi

  base=${src##*/}; stem=${base%.*}; safe=$(normalize "$stem" document)
  dest="$OUTDIR_REAL/$safe.pdf"
  if [[ -n "${CLAIMED[$dest]:-}" ]]; then
    echo "FAILED (name clash: $src and ${CLAIMED[$dest]} both become $safe.pdf)" >&2
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

  mode=rewrite
  if ((LOSSLESS)); then
    mode=clean
  elif has_form "$src"; then
    mode=clean; echo "  (fillable form: skipping the Ghostscript rewrite)"
  fi
  echo "${mode^^}: $src -> $dest"
  [[ -n "$MAP_FILE" ]] && printf '%s\t%s\n' "$base" "$safe.pdf" >> "$MAP_FILE"
  if ((DRY_RUN)); then return 0; fi

  # Work in hidden temp files beside the output, then link the result
  # into place: ln refuses to replace an existing file.
  # Temp names end in .pdf/.json: Ubuntu's AppArmor profile for qpdf
  # only lets it open files with those extensions.
  TMP_GS=$(mktemp -p "$OUTDIR_REAL" --suffix=.pdf .pdf_prep.XXXXXX) || return 1
  TMP_OUT=$(mktemp -p "$OUTDIR_REAL" --suffix=.pdf .pdf_prep.XXXXXX) || { cleanup; return 1; }
  TMP_PLAIN=$(mktemp -p "$OUTDIR_REAL" --suffix=.pdf .pdf_prep.XXXXXX) || { cleanup; return 1; }
  TMP_JSON=$(mktemp -p "$OUTDIR_REAL" --suffix=.json .pdf_prep.XXXXXX) || { cleanup; return 1; }
  base_pdf=$src
  if [[ "$mode" == rewrite ]]; then
    if ! run_gs "$src" "$TMP_GS"; then
      echo "FAILED (Ghostscript; try --lossless): $src" >&2; cleanup; return 1
    fi
    if (($(size_of "$TMP_GS") < $(size_of "$src"))); then
      base_pdf=$TMP_GS
    else
      mode=clean
      echo "  (rewrite was not smaller - kept the original content)"
    fi
  fi
  if ! run_qpdf "$base_pdf" "$TMP_OUT"; then
    echo "FAILED (qpdf; see the AppArmor note at the top if \"Permission denied\"): $src" >&2
    cleanup; return 1
  fi
  if ! qpdf --check -- "$TMP_OUT" >/dev/null 2>&1; then
    echo "FAILED (output did not pass qpdf --check): $src" >&2; cleanup; return 1
  fi
  # mktemp makes owner-only files; give the output the usual umask mode
  # (the web server must be able to read it).
  chmod -- "$(printf '%o' $((0666 & ~0$(umask))))" "$TMP_OUT" || { cleanup; return 1; }
  if ! ln -- "$TMP_OUT" "$dest"; then
    echo "FAILED (could not create $dest)" >&2; cleanup; return 1
  fi
  cleanup

  before=$(size_of "$src"); after=$(size_of "$dest")
  echo "  $(human "$before") -> $(human "$after") ($(( (after - before) * 100 / before ))%)"
  if [[ "$mode" == rewrite ]]; then rewritten=$((rewritten + 1)); else cleaned=$((cleaned + 1)); fi
  done_count=$((done_count + 1))
}

for src in "${FILES[@]}"; do
  process "$src" || failures=$((failures + 1))
done

if ((DRY_RUN)); then
  echo "Dry run: ${#FILES[@]} input(s), $failures problem(s); nothing written."
else
  echo "Done: $done_count ($rewritten rewritten, $cleaned cleaned only), $skipped skipped, $failures failed."
fi
((failures == 0))
