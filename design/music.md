# `music` — rebuild plan (evaluation of the workbench prototype)

2026-10-10. Status: **evaluated; David answered 2026-10-10** (his notes
under each question at the end; summary in "Decisions" just below). Source: David's prototype
`sites/music/heirloom/music-workbench-refined-v2/` (built in another
environment) and the media in `sites/music/heirloom/david/`.

## Target shape (from David's brief)

- `music.davidstitt.net/<locale>/` — a hub page, same aesthetics as the
  other hubs, listing sub-sites; for now only **Workbench**.
- `music.davidstitt.net/<locale>/workbench/` — the prototype's
  "working notebook", in its own aesthetic.
- Configuration-driven: content lives in a catalog file; building
  produces the HTML in both languages.
- English and Spanish, Spanish reviewed and approved as always.

## Decisions (David, 2026-10-10)

- **Architecture**: static pages built from the catalog (one per piece,
  both languages) + one small enhancement script. Not the SPA.
- **Translation**: same flow as every other site — Claude drafts, David
  reviews. No machine translation at build or deploy; the build blocks
  missing or stale Spanish.
- **Fonts**: start self-hosting now (DM Sans, Libre Baskerville, and
  Atkinson Hyperlegible for the other sites).
- **Accessibility**: raise the smallest text sizes, make the light greys
  tokens that pass AA. **Light-only by design** — no dark mode for music.
- **Catalog format**: TOML (easier for David to edit, allows comments).
- **Status/checklist controls**: fine for any visitor to see (it's a
  personal site; state stays in each visitor's own browser).
- **Hub image**: Claude makes a stand-in.
- **Media**: all 35 files hosted on the new server. David will optimize
  the audio/video himself before the deploy.
- **Status/checklist controls stay visible** (no "owner mode").
- **Old addresses are not preserved**: `/music.html` and
  `/sounds/<file>` simply stop working at cutover — no redirects. The new
  site uses the standard pattern every site follows: large media in
  `sites/<site>/media/` (gitignored), served at `/media/<file>`, and
  referenced from content by filename only, so the build and link check
  can verify every reference.
- **Atkinson Hyperlegible**: the original (as named in the design brief),
  Claude's call — David had no preference.
- **Media prep (2026-10-10)**: every audio/video file published goes
  through `tools/studio/av_prep.sh` (David's script, revised after
  review): web copies are MP3/AAC audio and H.264 MP4 video with all
  metadata stripped; masters stay in Dropbox. This replaces the earlier
  "audio defaults to .wav" note for what the sites serve. Output names
  are normalized (lowercase, `_`, `_video` suffix for videos), so a
  first pass renames catalog files.

## Dev plan

Expected to span several sessions. **To resume**: read this section,
take the first unticked step, check the log at the bottom. **When
stopping**: tick what's done, add a log line saying where things stand.
Each step ends at a natural review point; nothing is committed without
David's OK, nothing deploys before step 10.

- [x] **1. Media staging** — copy `heirloom/david/` to `sites/music/media/`
  (gitignored) so the site can be built and reviewed with the current
  files. Done when: the 35 files are in place. *(David's optimized files
  replace them in step 9.)*
- [x] **2. Self-hosted fonts** — Atkinson Hyperlegible (regular, bold),
  DM Sans and Libre Baskerville (the weights the prototype uses) as WOFF2
  in `sites/_shared/static/fonts/` with their OFL licence files;
  `@font-face` rules; the build copies shared sub-folders (today it only
  copies top-level files); re-measure the title-fitting factor with the
  real Atkinson. Done when: fonts load locally on every site, checks
  pass. Benefits all sites, not just music.
- [x] **3. TOML catalog** — convert `catalog.json` to
  `sites/music/content/catalog.toml`: hosted files by `file` name,
  external links by `url`, dates as `2021-09`, `featured` pieces and
  per-piece section headings moved out of the code. Plus a catalog check
  in `pre-build-check.sh`: unique ids, known vocabulary, `http(s)` links
  only, every `file` present in `media/`. Done when: David has looked at
  the TOML and finds it comfortable to edit.
- [x] **4. Workbench pages** — Flask app `src/websites/music/`, routes
  `/<locale>/workbench/` (welcome + index) and
  `/<locale>/workbench/<id>/` (one page per piece); templates and CSS
  from the prototype, colours as tokens (light-only), smallest text
  raised, greys passing AA; favicon set and web manifest; footer date
  from the build. Done when: all pages build and pass checks, viewable
  locally.
- [x] **5. Enhancement script** — `sites/music/static/js/workbench.js`,
  readable source served as-is: search, filters, recent pieces,
  status/checklist in `localStorage`, `/` shortcut. No `innerHTML`.
  Done when: works locally, pages still fully usable without it, Claude's
  security/efficiency notes written up here for David's review.
- [x] **6. Music hub** — `/<locale>/` on the shared hub layout, Workbench
  listed live, stand-in image by Claude. Done when: builds and passes.
- [x] **7. Spanish** — UI and vocabulary in `config/i18n/music/`; content
  translations in a parallel Spanish catalog file, each entry recording
  the English it came from; the i18n check fails on missing or stale
  entries. Claude drafts, **David reviews and approves**. Done when:
  approved.
- [x] **8. David's review of the whole site locally** — layout,
  wording, both languages, phone and desktop. Loop back to steps 3–7 as
  needed. Then commit.
- [x] **9. Optimized media** — David's optimized files into
  `sites/music/media/`; catalog updated for any renamed/re-encoded files;
  checks pass (every reference resolves; 100 MB deploy gate). Done when:
  David confirms the media set is final.
- [x] **10. Deploy and cutover** — `vhosts.yml` entry for
  `music.davidstitt.net`; deploy; point the (pinned, legacy) `music` DNS
  record at the new droplet; certificate; full smoke test; David's live
  check; commit. The cutover method (no-gap forward as for taiji, or a
  simple flip) is decided at that point.
- [ ] **11. Then: legacy droplet teardown** (separate plan, runbook
  "Later: legacy teardown").

### Log

- 2026-10-10 — prototype evaluated, questions answered, plan written. Next: step 1.
- 2026-10-10 — step 1 done: 35 files (538 MB) copied to `sites/music/media/`, checksums identical to
  `heirloom/david/`; gitignored. Paused for David's review. Next: step 2.
- 2026-10-10 — step 2 done: Atkinson Hyperlegible 400/700, DM Sans (variable 100–1000), Libre Baskerville
  (variable 400–700 + italic) as latin-subset WOFF2 from Google's servers, OFL 1.1 licences from
  google/fonts, in `sites/_shared/static/fonts/` (5 files, ~125 KB); `@font-face` in `tokens.css`;
  `freeze.py` copies the shared tree; fonttools + brotli added as dev deps. Title factor kept at 0.66
  (Atkinson measures 0.37–0.55 em/char, so approved title sizes are unchanged, with margin if a font
  fails to load). Not deployed: every live site will switch to Atkinson on the next deploy. Paused for
  David's local review. Next: step 3.
- 2026-10-10 — step 3 done: `sites/music/content/catalog.toml` (578 lines), converted from catalog.json
  with a verified field-by-field round trip. Simplified: vocabulary defined once at the top (keys +
  English labels, display order); default checklist (24 of 25 pieces shared one); `subtitle` only
  where custom (Woodshed); the never-displayed working note became a comment; featured pieces and
  special headings moved out of code. Check `websites.music.catalog` runs in pre-build-check before
  the build (9 mistake types tested, all caught). pre-build-check now treats only packages with an
  `__init__.py` as sites. Paused for David to try editing the TOML. Next: step 4.
- 2026-10-10 — David reviewed the TOML (likes the format, tested the checker). Steps 1–3 committed
  and pushed as `e789d5d`. Fonts not yet deployed. Next: step 4.
- 2026-10-10 — step 4 done (English only): `src/websites/music/` builds `/en-US/workbench/` + 25 piece
  pages (26) from the catalog; templates `workbench_base/index/piece.html`; `static/css/workbench.css`
  (the prototype's three CSS passes merged, sizes raised to 16px base / 12px minimum, all text colours
  tokens passing AA - muted `#72756e` -> `#6d7069`, faint greys -> muted); UI strings in
  `config/i18n/music/en-US.toml`; favicon set; web manifest renamed `manifest.json` (nginx has no
  `.webmanifest` type, and adding one safely isn't possible at that level). Piece titles use the
  shared fit-title rule restyled serif/400 with the prototype's ~3.1rem maximum. Script-only parts
  (search, filters, recent, status) are in the HTML, `hidden` until step 5. `freeze.py` gained a
  per-site `freeze_urls()` hook for pages with more than the locale in their URL. All checks pass.
  Paused for David's local review. Next: step 5.
- 2026-10-10 — step 5 done: `static/js/workbench.js` (review notes in "Enhancement script — review
  notes" above). David's changes: no fixed `featured` list (removed from catalog, checker, code) - the
  welcome tiles are the visitor's 3 most recently opened pieces, hidden until there is one; the
  sidebar "Recently opened" list dropped. New check `tools/dev/check_js.py` (esprima dev dep): ES2017
  syntax + no HTML/code from strings, each forbidden construct tested. No JS engine/browser on ubuvm,
  so behaviour is for David to test in his browser. Paused for David's review. Next: step 6.
- 2026-10-10 — David's browser checks of step 5: all green. Step 6 done: hub at `/<locale>/` on the
  shared hub layout (`templates/hub_index.html`, light-only workbench palette), title "Music",
  Workbench listed live; image David's `heirloom/sus_dave.jpg` (529×587) as
  `static/img/david-suspicious-529.webp` (24 KB, no upscaling - a ~1100 px original would be crisper),
  alt text drafted by Claude. All checks pass. Paused for David's review. Next: step 7 (Spanish).
- 2026-10-10 — David approved step 6 (title "Music", alt text). Step 7 drafted, awaiting David's review:
  `config/i18n/music/es-ES.toml` (interface) and `sites/music/content/catalog.es-ES.toml` (vocabulary,
  default checklist, all 25 pieces). Each block records a fingerprint of its English; the catalog check
  fails on missing or out-of-date Spanish (tested: edited summary, removed block, renamed vocabulary
  label - each caught by name). `python -m websites.music.check --status` lists fingerprints for future
  drafts. App loads the catalog lazily (clean error lists instead of tracebacks); CLI moved to
  `websites.music.check`. 54 pages build (hub + workbench + 25 pieces, x2). Next: David's review of
  the Spanish, then commit.
- 2026-10-10 — David approved the Spanish (no flaws found); step 7 done. Steps 4-7 committed and pushed.
  Next: step 8 (David's full local review).
- 2026-10-10 — step 8 done: David's manual checks throughout steps 4–7 covered the full review. Next:
  step 9 (David's optimized media).
- 2026-10-10 — step 9 in progress: David's `tools/studio/av_prep.sh` reviewed and revised (findings and
  changes in `design/tech-debt.md`, media item), tested on synthetic media for every path. Run over the 35
  originals into `sites/music/media/`: 12 encoded, 23 copied, 0 failed; 538 MB -> 474 MB (audio up to
  87% smaller; videos copied unchanged - already 720p H.264 at 1.2-1.9 Mbps). All metadata gone (the
  originals carried dates, artist, GarageBand tags). Catalog: 33 file names updated from the run's map.
  Open: whether to re-encode the 6 videos too (test: one went 30.8 -> 25.1 MB, -18%, ~1.75 min).
- 2026-10-10 — David chose: automatic by default, and re-encode these six. `av_prep.sh` now copies H.264
  only at <= 0.045 bits/pixel/frame (~1 Mbps at 720p25); the six (0.050-0.081) re-encode without
  `--force`.
- 2026-10-10 — six videos re-encoded: 369 -> 238 MB (18-47% each). Media total 538 -> 342 MB (-36%), no
  metadata left, all checks pass. Waiting on David: listening/viewing check, then commit. Then step 10.
- 2026-10-10 — David: audio and video are fine; step 9 done and committed. Next: step 10 (deploy and cutover).
- 2026-10-10 — step 10 done: `vhosts.yml` entry (smoke pages `workbench/`, `workbench/bella/`); deploy
  uploaded 342 MB media (and first published the self-hosted fonts to every live site); DNS `music` A ->
  157.245.25.141 at 19:59 UTC (simple flip, David's choice); certificate issued 20:06 UTC (~7 min gap for
  early resolvers); full public smoke test 110/110; renewal dry run OK for all certificates. Old
  `/music.html` and `/sounds/` addresses retired (404), as decided. **music.davidstitt.net is live on the
  new droplet.** Next: step 11, legacy droplet teardown.
- 2026-10-10 — David's manual check of the live site: green. Committed and pushed.

## What's in the prototype (verified)

- `catalog.json`: 25 pieces, 43 resources — 35 hosted files, 7 YouTube
  links, 1 external page. Every piece has id, title, kind, subtitle,
  activity/instrument/genre lists, status, summary, resources,
  checklist, note.
- The 35 hosted files match `heirloom/david/` exactly, both ways
  (537 MB; mp3 ×26, mp4 ×6, m4a ×2, wav ×1; largest 90 MB — under the
  100 MB deploy gate). Catalog URLs still point at the legacy
  `https://music.davidstitt.net/sounds/<file>`.
- `index.html` + `style.css` + `app.js` (17 dense lines): a
  single-page app. It fetches `catalog.json`, renders the sidebar
  (search, filter chips, recent list, piece index) and the selected
  piece into `<main>` via `innerHTML`, routes on `#piece-id`, and keeps
  per-browser state (recent pieces, status, checklist ticks) in
  `localStorage`.
- A full favicon set + `site.webmanifest`.

## JavaScript review

**Security** — sound basics, a few gaps:

- An `esc()` HTML-escape is applied to almost every interpolated value,
  links use `rel="noopener noreferrer"`, `localStorage` access is
  wrapped in try/catch and namespaced. Good.
- Not escaped: piece ids in `data-piece`/`data-recent` attributes and
  `r.type`. Catalog data is author-controlled, so not exploitable today,
  but it's the kind of gap that bites when content changes hands.
- URLs are escaped but **not scheme-checked**: a `javascript:` URL in the
  catalog would run on click. Build-time validation (http/https/local
  only) closes this.
- Everything goes through `innerHTML` — the whole HTML-injection surface
  exists only because the page is built in the browser.
- Works under our Content-Security-Policy (`script-src 'self'`,
  same-origin `fetch` and media) — no inline scripts.

**Efficiency** — fine at 25 pieces: full re-render per keystroke and
re-attached handlers are wasteful but invisible at this size;
`preload="none"` on audio/video is right (nothing downloads until play).

**Maintainability / i18n** — the real issues:

- All UI text is hard-coded English inside the JS (labels, status names,
  filter groups, "resources", "Saved in this browser"…).
- Content decisions are hard-coded in code: the three welcome tiles
  (`woodshed`, `bella`, `king-phillip`), per-piece section headings,
  "video if the URL contains `/sounds/`".
- Content only exists after JavaScript runs: no per-piece URL to share,
  nothing for our HTML/link/i18n checks to validate, nothing without JS.

## Recommendation: static pages + a small enhancement script

A pure Python/Flask version **without** JavaScript can't do the live
features — search-as-you-type, multi-filter, and per-browser status/
checklist need code in the browser, and our sites are frozen static
files (no running server, by design). But most of the page doesn't need
JS at all. Proposed split:

- **Built in Python (Frozen-Flask + Jinja), from the catalog**: the
  workbench index, one real page per piece
  (`/<locale>/workbench/<id>/`), every resource with its player, all in
  both languages. Shareable URLs; works without JS; validated by
  `pre-build-check.sh` like every other page.
- **One small, readable script** (~80–100 lines, no build step needed)
  only *enhances* those pages: search and filter (show/hide existing
  items), the recent list, status and checklist saved in `localStorage`,
  and the `/` keyboard shortcut. It never builds HTML from strings —
  `textContent`, `hidden` and attributes only — so the injection surface
  disappears entirely.
- **Minify for deployment?** Not needed: at ~3 KB gzip already makes it
  small, and nginx compresses text. Keeping the deployed file identical
  to the readable source avoids a JS build tool (no Node) and keeps what's
  served auditable. Can revisit if it grows.

## Enhancement script — review notes (step 5, 2026-10-10)

`sites/music/static/js/workbench.js` replaces the prototype's `app.js`.
Readable source, served as-is (no minifying: 8.6 KB, 2.9 KB gzipped —
the prototype's denser `app.js` gzips to 3.2 KB).

**What it does**: reveals the search/filter UI and filters the existing
index links; `/` focuses search; records the open piece and shows the
three most recent as welcome tiles (section hidden until there is one —
David, 2026-10-10: no fixed "featured" list, no sidebar recent list);
restores and saves per-piece status and checklist ticks.

**Security**

- No HTML from strings anywhere: only `textContent`, the `hidden`
  property, attributes and moving existing elements. All visible text is
  server-built, in the page's language. This removes the prototype's
  whole HTML-injection surface rather than escaping around it.
- `tools/dev/check_js.py` (in `pre-build-check.sh`) enforces it: rejects
  `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`,
  `eval`, `new Function` and string timers, using parser tokens (so
  comments and strings don't count). Tested on each construct.
- Stored data is untrusted: every value read from `localStorage` /
  `sessionStorage` is type-checked and limited to piece ids present on
  the page and statuses in the embedded label list; anything else is
  ignored. Selectors built from ids use `CSS.escape`.
- Status labels reach the script as a JSON data block
  (`<script type="application/json">`, rendered by Jinja's `tojson`) —
  never executed, so the Content-Security-Policy stays at
  `script-src 'self'` with no exceptions.
- Storage is namespaced (`music-workbench:`) and failures are silent.
  Nothing leaves the browser: no requests, no third parties.

**Efficiency**

- One small deferred script per page; no catalog download (the
  prototype fetched all of `catalog.json` on every visit) and no
  re-rendering — filtering toggles `hidden` on 25 existing links.
- Media still loads nothing until played (`preload="none"`).

**Behaviour changes from the prototype**

- Each piece is its own page, so filters and search are remembered for
  the browser tab (`sessionStorage`) while moving between pieces.
- Checklist ticks are stored by position: if a piece's checklist is
  reordered in the catalog, old ticks may land on different items —
  acceptable for a personal checklist.
- Plain ES2017 — wide browser support, and checkable without Node.

## Translation in a configuration-driven site

The project rule — translations ship only after David reviews them —
means "deploy generates the Spanish" can't be literal machine
translation at deploy time. Proposed instead:

- `catalog` (English) stays the single source of content.
- A parallel Spanish file holds, per piece and resource, the translated
  fields (summary, subtitle, desc, checklist, note…), each with a
  fingerprint of the English text it was translated from.
- Shared vocabulary (kinds, activities, instruments, genres, statuses,
  resource types) is translated once, in the TOML catalog like other
  sites. Song titles stay as titles.
- Dates stored as `2021-09` and formatted per language
  ("September 2021" / "septiembre de 2021").
- The i18n check fails the build — and so the deploy — when a Spanish
  entry is **missing or stale** (English changed since it was
  translated), listing exactly which. Then: Claude drafts, David
  reviews, deploy proceeds.

## Other findings

- **Fonts**: `style.css` imports DM Sans and Libre Baskerville from
  Google Fonts. Our security policy blocks that — the live site would
  silently fall back to system fonts. Fix: host the font files
  ourselves (free licences), which also solves the deferred Atkinson
  Hyperlegible item in one go.
- **Text sizes**: base 14px, many labels 10–11px — small next to the
  "calm" design brief (16–18px body).
- **Contrast** (measured on the `#f8f6f0` paper): the main `--muted`
  grey is 4.33:1, just under WCAG AA's 4.5:1; six hard-coded lighter
  greys (`#9b9b92`, `#98978d`, `#99988e`, `#96988e`, `#a5a49d`,
  `#92968e` — dates, footer, hints, ticked items) are 2.3–2.8:1. Accent
  (7.5:1) and green (4.95:1) pass. Our contrast check doesn't see the
  hard-coded ones because they aren't tokens; making them tokens fixes
  both.
- **No dark mode** (`color-scheme: light`); every other site has one.
- **Footer date** "October 2026" is hard-coded — should come from the
  build.
- **Legacy URLs** (live server, checked): `/` and `/music.html` (the old
  page), `/sounds/<file>` (all 35 media files), `/favicon.ico`. Propose
  redirects `/music.html` → workbench and `/sounds/<file>` →
  `/media/<file>` (needs a small prefix-redirect feature in
  `vhosts.yml`). The legacy `/merida`, `/spain`, `/videos` folders moved
  to `comunidad`/`callejerez` and retire.
- **Media**: copied to `sites/music/media/` (gitignored, 537 MB). No
  re-encoding in this round — the six videos (30–90 MB) are a candidate
  for the media-tooling item in `tech-debt.md`.
- **Cutover**: `music.davidstitt.net` is still on the legacy droplet;
  same no-gap certificate pattern as taiji. Legacy teardown follows.

## Questions for David

1. Static pages + small script (recommended), or keep the prototype's
   single-page app?

A: static pages + small script.

1. Translation flow as above (Claude drafts, you review, build blocks
   stale Spanish)? Or do you want machine drafting at build time (needs
   a translation service and an API key)?

A: Follow same translation flow as other pages. (I think I mis-spoke - do NOT want auto-translate at deploy time.) Claude drafts, I review.

1. Fonts: self-host DM Sans + Libre Baskerville now (and Atkinson
   Hyperlegible with them)?

A: Yes, let's go ahead and start self-hosting the fonts.

1. OK to raise the smallest text sizes and turn the light greys into
   tokens that pass AA? And: dark mode, or deliberately light-only?

A: OK to raise smallest size and adjust light greys. This site is deliberately light-only.

1. Catalog format: keep JSON (with the tweaks above: `file` instead of
   legacy URLs, ISO dates, `featured` and section headings moved out of
   the code), or switch to TOML/YAML, which allow comments?

A: Let's switch to TOML. I find it easier to work with.

1. The workbench is public: any visitor sees status controls and
   checklists, saved only in *their* browser. Intended, or should those
   be hidden?

A: Hmm. Intersting question. This is really intended as personal site. I am OK with anyone seeing status controls and checklists. How would it work to hide them? Would that require some level of auth/auth?

1. The music hub page: image and palette from you (like the other hubs),
   or a stand-in until you have one?

A: Come up with stand-in image for now.

1. Legacy redirects for `/music.html` and `/sounds/<file>` — yes?

A: I am not sure I entirely understand what this is getting at. What do you mean by "legacy redirects"?  My expectation is that all of the resources (sound files) will be hosted on the new server.  Once this site is built out, deployed, we are going to decommission the legacy server. 


One additional note: I have not yet optimized the sound and video files. I will do that before we are ready for deploy to DO server. 
