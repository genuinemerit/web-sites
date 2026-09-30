# Site content inventory

Full directory trees pulled 2026-09-29 (4 levels deep) for all 5 live
sites. This file summarizes structure and flags anything that reads as a
distinct "sub-site" (a folder with its own `index.html`/named entry page
and, usually, its own `styles.css` — i.e. content that was built as a
semi-independent unit rather than just an asset subfolder) per David's
request. Raw `find` output isn't reproduced in full here for the two
huge media sites; structure is summarized instead.

## `music` (2.9G) — has 3 genuine sub-sites

Top level: `music.html` (main page), `styles.css`, `favicon.ico`, plus:

- **`merida/`** — sub-site. Own `index.html` + `images/` (5 photos). Reads
  like a dedicated page for a Mérida trip/event.
- **`spain/`** — sub-site. Own `index.html`, own `styles.css` (distinct
  from the top-level one), 7 photos + 2 PDFs. Content looks
  political/labor-related (`CGT_demo.jpg`, union figures) rather than
  music — this folder may be topically unrelated to "music" as a site and
  worth a naming/placement decision during the rebuild. One file has a
  malformed name: `zapatista-girl-da.jpgoriginal.jpeg` (looks like a
  botched "save as" — `.jpg` accidentally concatenated with `original.jpeg`
  rather than replaced).
- **`videos/`** — sub-site. Own `index.html` **and** a second entry page
  `index_calle_jerez.html`, own `styles.css`, 9 videos. The two index
  pages suggest this may actually be two related-but-distinct galleries
  sharing one folder.
- `sounds/` — NOT a sub-site, just a flat folder of ~35 audio/video files
  (covers, originals — includes `Saskan_Theme.mp3`, interesting given the
  `sask`/`saskan` universe connection seen elsewhere). No index page, no
  own styling.

## `openmic` (2.3G) — 1 clear sub-site, a couple of borderline cases

Top level: `openmic.html`, `styles.css`, `gallery.html` +
`gallery_0624/0724/0824/0924/1024.html` (5 monthly gallery pages — a
recurring pattern, not a sub-site each, more like a hand-maintained series).

- **`images/stickers/`** — sub-site. Own `index.html` + own `styles.css`,
  14 sticker images. Clearest second sub-site on this domain.
- `images/photos/june_2025/june_2025.html` — a named page inside a dated
  photo folder, same pattern as the other `photos/<month>_<year>/` folders
  but this is the only one with its own HTML page rather than being pure
  images referenced from elsewhere. Borderline — flagging, not calling it
  a full sub-site.
- `images/video/dan_ralph.html` — a single standalone page mixed in with
  video assets. Not a sub-site, just an oddly-placed page.
- Otherwise: `images/flyers/`, `images/graphics/`, `images/photos/<7 dated
  subfolders, 2024-2025>`, `images/signs/` — plain asset folders, no
  index pages, no own styling.

## `qigong` (19M) — no sub-sites

Flat: `qigong.html`, `styles.css`, `img/` (11 images/PDFs), `sets/` (26
PDF exercise sheets). Simple, single-page site with reference documents.

## `sfp` (13M) — no content sub-sites, but one important non-content folder

Flat content: `sfp.html`, `constitution.html`, `platform.html`,
`handbook.html`, `cool_scripts.html`, `styles.css`, `images/` (~40 files).
**Correction (David, 2026-09-30, and a correction to my own first
correction):** this is fictional/game content, not real-world political
material — but it has **nothing to do with `sask` or "Saskan Lands."**
"SFP" is the name of a player-group ("party") in the online browser game
*eRepublik*, entirely separate from the novel (working title
"Enclosures") David is writing, which is the actual source of the
`sask`/`saskan` fictional world. The `saskan/` asset-publishing folder
that lived under this site (deleted 2026-09-30, see below) was there
**purely opportunistically** — reusing `sfp`'s disk space as a convenient
publish target, not because the two are thematically connected. My first
correction (guessing a `sask` connection from the folder name alone) was
itself wrong — noting both corrections rather than silently rewriting
history.

- **`docs/`** — not a sub-site (no index page), contains
  `cool_scripts.html` and `using_scripts.html`. The top-level
  `sfp/cool_scripts.html` was a different, stale duplicate of
  `docs/cool_scripts.html` — confirmed by David and **deleted** 2026-09-30;
  `docs/cool_scripts.html` is the one that remains.
- **`saskan/`** — was an asset-publishing target from a dev project being
  subsumed into the `sask` app (confirmed by David 2026-09-30). **Deleted**
  (`rm -rf /usr/share/nginx/html/sfp/saskan`).

## `taiji` (1.9G) — no sub-sites

Flat: `taiji.html`, `styles.css`, `img/` (1 image), `vid/` (2 videos).
Simplest site of the five.

## Cross-site observations

- Every site's actual page content (HTML/CSS excluding media) is small —
  the multi-GB footprints on `music`/`openmic`/`taiji` are entirely large
  media files (video/audio/photo), matching what David already flagged for
  the separate "what to carry forward vs. archive" review.
- No site uses any build tooling, template includes, or shared components
  today — each `styles.css` is hand-maintained per site (and per sub-site,
  where those exist), fully independent of the others.

===

**Synthesized into `web-sites/planning/target-sites.md`** (2026-09-30) —
that file has the organized version of the notes below, plus the
questions they raised. Raw notes kept here as-written, unedited.

David's notes:

Regarding web sites, what will be ported and possibly refactored:

- taiji site. Pretty much as is. May add some additional content and look at improving design. Needs to keep the same URL.

Sites where the domain name could change (TBD):

- qigong site. Possible design improvement. Possibly subsumed into a broader health and exercise site.

- sfp site.  This is for a game. Not actually political. Very likely to be redesigned, possibly removed. Possibly subsumed into a broad site covering game-related and world-building topics and tools, including potentially materials relating to the "Saskan Lands" (the book and game David is working on developing).

- openmic site. Likely to be decommissioned, or possibly subsumed into something like a "community" site, including some legacy materials from the Sandwich, MA Open Mic that David used to manage, but also newer materials, possibly relating to the Intercambio de Idiomas: Inglés-Español in Alcalá de Henares and maybe eventually other projects.

- music site. Likely to be completely re-designed to feature both David's work and other resources. The "sub-sites" dealing with topics like merida, spain and calle jerez are likely to moved to a new site altogether, or possibly two new sites.  One focused on school projects and learning about Spanish language and culture, the other more specifically about home, family and friends (Calle Jerez)

In all cases, we want to look at using a clean, modern style; tooling that is robust and consistent and matches other "requirements" noted for this project; and methods that can be automated easily, via a pipeline that let's us test thinngs out on a local VM, then deploy (probably directly, not via GitHub)

For server-level notes, see other documents.