# Studio tools — media prep in the dev pipeline

2026-10-15. Status: **decided, in progress** (dev plan below). Covers
`tools/studio/` (`av_prep.sh`, `img_prep.sh`, `pdf_prep.sh`, and the
planned `prep.sh`), the media check and the tools' tests.

## Goal

Media of any kind (sound, video, image, PDF) reaches the build, git and
GitHub only after it has been prepped. Originals are backed up only
through the Dropbox push (`tools/dev/backup-to-laptop.sh`). David can
also run any tool by hand at any time.

## Decisions (David, 2026-10-15)

- **`img_prep.sh`**: its basic clean-up is enough for this project (no
  `sask`-level rigor). Changed only where it broke the shared rules:
  - **The GPS leak.** When re-saving wasn't smaller, it copied the
    original with its metadata (GPS included). Kept originals now have
    their metadata stripped losslessly with `jpegtran`.
  - **The interface.** It now takes files or folders, writes to `-o`,
    uses lowercase names joined by `_`, and never overwrites.

  Resize and quality behaviour are unchanged.
- **`pdf_prep.sh --keep-info`**: keeps only the title, the one useful
  field because browsers show it in the tab. Author, creating software,
  dates and XMP always go.
- **Originals inbox: `sites/<site>/raw/`**. It's gitignored, never
  deployed, and backed up via the Dropbox push. `heirloom/` stays the
  staging area for the rebuild; `raw/` is the place for new work after
  it.
- **The media check analyses each file**, not a log or manifest. A log
  only records that a tool ran, can drift, and can't see a raw file
  copied in beside it. The file itself is the truth, and checking about
  100 files is cheap.
- **Unit tests for every tool**, run on every pre-build check ("better
  safe than sorry"). They use generated sample files, never real media.
- **`prep.sh`** handles every supported type: it sends each file to the
  right tool, writes into `sites/<site>/media/`, then runs the media
  check.

## Dev plan

David reviews after steps 2, 3 and 5.

- [x] 1. Align `img_prep.sh` (above); `pdf_prep.sh --keep-info` keeps
  the title only.
- [x] 2. Tests: pytest (dev dependency), `tests/studio/`, generated
  samples. Wired into `pre-build-check.sh`.
- [ ] 3. `tools/dev/check_media.py`: per-type rules for every media file
  under `sites/*/media/` and `sites/*/static/`. Wired into
  `pre-build-check.sh`, plus a git pre-commit hook (staged files) that
  `tools/dev/install-git-hooks.sh` installs.
- [ ] 4. `tools/studio/prep.sh SITE [FILES_OR_DIRS]`, defaulting to
  `sites/<site>/raw/`; `raw/` added to `.gitignore`.
- [ ] 5. `docs/media-prep.md`: how to run the tools, and how unprepped
  files are kept out.

## Log

- 2026-10-15: `fb-prep.sh` renamed `img_prep.sh`; `pdf_prep.sh` added
  (`e4c9adc`). Decisions above agreed.
- 2026-10-15: step 1 done. `img_prep.sh` now accepts any common image
  type and writes JPEG, or PNG for transparency. Multi-frame images are
  refused. `pdf_prep --keep-info` keeps only the title. It needs a plain
  qpdf pass first, because `--update-from-json` silently skips objects
  inside object streams, which is where Ghostscript puts the document
  information.
- 2026-10-15: step 2 done. 63 tests in `tests/studio/` (about 9 s),
  wired into `pre-build-check.sh` after shellcheck; ruff now covers
  `tests/` too.
  - The shared rules are tested for all three tools.
  - `av_prep.sh` gained the same "never write beside a source" refusal.
  - Proved the tests can fail: five deliberate breakages were each
    caught (the old GPS leak, PDF info kept, audio/video tags kept,
    overwriting allowed, no EXIF rotation).
