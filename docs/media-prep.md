# Preparing media for the sites

How images, sound, video and PDFs get onto the sites, and how unprepped
files are kept out of the build, git and GitHub. Design and history:
`design/studio.md`.

## Where everything lives

| What | Where | In git? | Deployed? |
| --- | --- | --- | --- |
| Originals, waiting to be prepped | `sites/<site>/raw/` | no | no |
| Prepped images | `sites/<site>/static/img/` | yes | yes, with the build |
| Prepped PDFs | `sites/<site>/static/docs/` | yes | yes, with the build |
| Prepped sound and video | `sites/<site>/media/` | no | yes, copied separately |

Sound and video stay out of git because of their size: git keeps
everything ever committed in its history for good. `sites/<site>/heirloom/`
is the staging area for the legacy rebuild; new material goes into
`raw/`.

## The usual way: one command per site

1. Put the originals in `sites/<site>/raw/` (subfolders are fine).
2. Run:

   ```bash
   tools/studio/prep.sh <site>              # or --dry-run first to preview
   ```

   Each file goes to the right tool and ends up in the right folder,
   with a URL-safe name: lowercase, words joined by `_`
   (`My Photo.JPG` becomes `my_photo.jpg`). The run ends with the media
   check over the whole site.
3. Look at the results in a local build, use them in the site's
   templates or content (`/static/img/...`, `/static/docs/...`,
   `/media/...`), then commit and deploy as usual.

Re-running is safe: an output that already exists is an error, never
overwritten. `--skip-existing` skips those files instead. Other
options: `--map FILE` writes an "original name / new name" list.

## Running a single tool

Use a tool directly for its special options, or for a one-off job.
Each one takes files or folders, and writes to the site given by
`--site`, or to the site the files are in:

- **`tools/studio/img_prep.sh`**: JPEG (PNG if transparent), rotated
  upright, long edge at most 2048 px, metadata stripped. Options: `-s N`
  long edge, `-q N` JPEG quality, `-e` gentle contrast boost for faded
  scans.
- **`tools/studio/pdf_prep.sh`**: Ghostscript size reduction, metadata
  stripped, "fast web view" (the first page shows while the rest loads).
  Options: `--preset screen|ebook|printer` image quality, `--lossless`
  no image reduction, `--keep-info` keep the title.
- **`tools/studio/av_prep.sh`**: MP3 / AAC audio, H.264 MP4 video at
  most 1080 px tall, tags and location stripped, starts playing while
  loading. Options: `--max-height N`, `--crf N` video quality,
  `--loudnorm` even out loudness.

```bash
tools/studio/pdf_prep.sh --site movement --keep-info ~/scans/handout.pdf
tools/studio/img_prep.sh -o ~/facebook -s 1600 ~/Pictures/trip/   # not for a site
```

`-o DIR` writes anywhere else, which is handy for Facebook or email
copies. Every tool has `-h` for the full option list, and comments at
the top of the script explaining exactly what it does. All of them:

- never change the originals;
- never overwrite an output;
- never write into a folder that holds a source file;
- refuse two inputs that would end up with the same name.

## How unprepped files are kept out

1. **`raw/` is gitignored and never deployed.** Originals can't reach
   GitHub or the droplet from there.
2. **The git pre-commit hook** checks every image, sound, video and PDF
   staged for a commit, anywhere in the repo, as staged. If any isn't
   prepped, the commit is refused and the message names the tool that
   fixes it.
3. **`tools/dev/pre-build-check.sh`** ("media prepped") checks every
   media file in the site folders before any build, push or deploy, and
   `deploy.sh` runs it first. This also covers `media/`, which git never
   sees.
4. **The deploy refuses files over 100 MB** unless told otherwise
   (`media_max_mb` in `ansible/vhosts.yml`).

`git commit --no-verify` skips the hook, but step 3 still catches the
file before it goes anywhere public.

The check (`tools/dev/check_media.py`) analyses each file itself. It
doesn't trust a log, so a raw file copied straight into `static/img/` is
caught. Run it any time:

```bash
poetry run python tools/dev/check_media.py                 # every site
poetry run python tools/dev/check_media.py sites/taiji     # one site
```

## Backups

`tools/dev/backup-to-laptop.sh` copies the whole working tree to
Dropbox, `raw/` and `media/` included. That is the only backup of the
originals and of the sound and video. The copy mirrors deletions,
**except in `raw/`**: an original you remove locally (once prepped, say)
stays in the Dropbox copy. To drop one from Dropbox for good, delete it
there by hand.

## Setup (once per machine or clone)

- Packages: `tools/dev/init-dev-host.sh` lists them: ffmpeg,
  ImageMagick, Ghostscript, qpdf and jpegtran (`libjpeg-turbo-progs`).
- The hook: `bash tools/dev/install-git-hooks.sh` (safe to re-run).

## Gotchas

- **qpdf and AppArmor.** Ubuntu only lets `qpdf` open `.pdf` files
  under your home folder, `/tmp`, `/mnt` or `/media`. A PDF anywhere
  else fails with "Permission denied".
- **Fillable PDF forms** are untested (`design/tech-debt.md`).
  `pdf_prep.sh` leaves their content alone, but check the result by
  hand.
- **Animated GIFs and multi-page TIFFs** are refused by `img_prep.sh`.
- **Favicons** (`.ico`, `.svg`) are made by hand and skipped by the
  check.
