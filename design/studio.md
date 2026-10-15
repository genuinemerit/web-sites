# Studio tools — media prep in the dev pipeline

2026-10-15. Status: **done** (dev plan below, all steps ticked). Covers
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
- **Output folders (added 2026-10-15)**: no more `~/webmedia` default.
  The tools write to the site's own folders:
  - images to `sites/<site>/static/img/`
  - PDFs to `sites/<site>/static/docs/` ("docs" leaves room for other
    document formats later)
  - audio/video to `sites/<site>/media/`. Not `static/`, because that is
    in git: music's media alone is 342 MB, and git would keep it in its
    history for good.

  The site comes from `--site NAME`, or from where the sources are
  (`sites/NAME/...`, e.g. `raw/`). `-o DIR` overrides it for one-off
  jobs. If none of these applies, it's a usage error; the tools never
  fall back to a default folder. The shared logic is in
  `tools/studio/common.sh`.
- **`prep.sh`** handles every supported type: it sends each file to the
  right tool, which writes into the site's folders (above), then runs
  the media check.

## Dev plan

David reviews after steps 2, 4 and 6.

- [x] 1. Align `img_prep.sh` (above); `pdf_prep.sh --keep-info` keeps
  the title only.
- [x] 2. Tests: pytest (dev dependency), `tests/studio/`, generated
  samples. Wired into `pre-build-check.sh`.
- [x] 3. Output folders by site and type (added 2026-10-15, below).
- [x] 4. `tools/dev/check_media.py`: per-type rules for every media file
  under `sites/*/media/` and `sites/*/static/`. Wired into
  `pre-build-check.sh`, plus a git pre-commit hook (staged files) that
  `tools/dev/install-git-hooks.sh` installs.
- [x] 5. `tools/studio/prep.sh SITE [FILES_OR_DIRS]`, defaulting to
  `sites/<site>/raw/`; `raw/` added to `.gitignore`.
- [x] 6. `docs/media-prep.md`: how to run the tools, and how unprepped
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
- 2026-10-15: steps 1-2 committed (`60d71db`). Step 3 done.
  - Output folders follow the site and the file type, through the new
    `tools/studio/common.sh`, which also holds the shared `normalize`.
  - 36 new tests in `test_destination.py` (99 in total, about 11 s).
    They run the tools from a fake repo in a temp folder, so the real
    `sites/` is never written to.
  - The tests caught the deliberate breakage, a silent fallback folder.
- 2026-10-15: step 3 committed (`e8aee6e`). Step 4 done.
  - `tools/dev/check_media.py` checks every media file under `sites/`
    (97 today) in about 2 s. It skips `raw/`, `heirloom/`, `build/`,
    `_shared` and favicons. `--staged` checks the staged version of
    files staged anywhere in the repo.
  - `pre-commit-hook.sh` is linked into `.git/hooks` by
    `install-git-hooks.sh`. It is installed on `ubuvm`, and was tested in
    a throwaway clone: it refused a JPEG with GPS data and accepted the
    prepped copy.
  - 40 tests in `test_check_media.py`, 138 in total. The main one is a
    round trip: each tool's output passes and the raw samples fail.
  - Shown to fail when they should: dropping the linearization,
    faststart or PDF-info rules each failed a test. Dropping the EXIF
    rule at first didn't, because the only EXIF samples also had GPS; an
    EXIF-only test was added.
  - Real finding: taiji's two videos (`media/vid/Taiji_for_Balance*.mp4`)
    fail. They have capitals in their names and no faststart (the index
    is at the end, so playback waits for the whole download). The fix
    changes live URLs, so it waits for David's decision. Until then
    `pre-build-check.sh` fails, which blocks deploys.
- 2026-10-15: step 4 committed (`ee65e29`). Taiji videos fixed with
  option A (David):
  - originals moved to `sites/taiji/raw/` (the first real use of `raw/`,
    now gitignored);
  - `av_prep.sh` copied them losslessly with faststart, as
    `media/taiji_for_balance{,_rear_view}_720p_video.mp4`;
  - links updated in both languages;
  - the legacy `/vid/` redirects now point at the new names, and the
    `/media/vid/` URLs (live from 2026-10-02) redirect too.

  Deployed: failed=0, public smoke test 119/119. On the droplet only the
  new files are left, and the index is in the first 64 KB, so playback
  starts straight away.
- 2026-10-15: taiji fix committed (`d129257`). Step 5 done.
  `tools/studio/prep.sh SITE [FILES_OR_DIRS]`:
  - It reads `sites/<site>/raw/` by default, sends images, PDFs and
    audio/video to their tools with `--site`, then runs `check_media.py`
    over the whole site. That means anything unprepped already in the
    site also fails the run.
  - Other file types are reported as UNSUPPORTED and count as a failure.
  - It passes `--dry-run`, `--skip-existing` and `--map` through (map
    rows from every tool go into one file). A tool's special options
    mean running that tool directly with `--site`.
  - 12 tests (151 in total); dropping the check or ignoring unsupported
    files each failed a test.
  - Gotcha: David's shell sets `VIRTUAL_ENV` (pyenv), so the check
    always goes through `poetry -C <repo> run`, except in the tests'
    throwaway repo.
- 2026-10-15: step 5 committed (`6fdd84f`). Step 6 done: `docs/media-prep.md`
  (where things live, `prep.sh`, single tools, the four barriers,
  backups, setup, gotchas). Plan complete.
- 2026-10-15: found while writing the guide: the Dropbox backup uses
  `rsync --delete`, so removing an original from `raw/` would also remove
  it from Dropbox at the next backup. David: originals must never be
  pruned there. `backup-to-laptop.sh` now protects `sites/*/raw/` with
  `--filter='P /sites/*/raw/***'`; deletions still mirror everywhere
  else. Tested on a local copy: the raw originals, subfolders included,
  were kept, while a removed `media/` file and a stray file were
  deleted.
