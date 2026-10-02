# `taiji` — redesign decisions

Started 2026-10-01, first site in the Phase 3 build order. Site-specific
design decisions live here as they're made; see `planning/target-
sites.md` for the original scope/constraints, `planning/roadmap.md` for
sequencing, and `planning/site-build-checklist.md` for the reusable
per-site build template this is following.

## MVP for this round — finalized 2026-10-01

David's proposal, reviewed item-by-item against the MVP-vs-parking-lot
discipline (`planning/site-build-checklist.md`) — two items adjusted,
rest confirmed as-is:

- Technical modernization: Frozen-Flask conversion, i18n machinery
  (EN/ES — Iberian Spanish specifically, real translated content, not
  just plumbing), content converted to Markdown + front-matter. All per
  the confirmed architecture, applied to `taiji` for the first time.
- A new favicon.
- A **splash/intro page** — a fun, modern intro image plus exactly two
  nav items: language switch, and a link into the existing "Taiji for
  Balance" page. Deliberately minimal scope (not a new information
  architecture, just one new entry page). Worth naming plainly: this
  *is* a small, real expansion beyond "pure port" — legacy `taiji` was
  a single page — but it's small and well-contained enough to belong in
  this round rather than the parking lot.
- Review/tweak the existing "Taiji for Balance" page's presentation
  against the governing "calm" design brief (`design-aesthetics.md`).
- Shared `404`/`50x` error pages (`sites/heirloom/`), redesigned to match
  the new aesthetic — **not actually `taiji`-specific**: this is shared/
  global hosting infrastructure every site's production vhost will need.
  `taiji` is just first in line to need it; the other six sites get it
  for free once this is done.
- **Media**: the one image and two videos compressed/resized by hand,
  specific one-off commands — **not** generalized automated tooling.
  Building real check-size/compress/normalize tooling for images, video,
  and sound was descoped from this round (too large relative to the
  rest of the MVP, and no approach chosen yet for video/audio
  specifically) and raised to **high priority** in `design/tech-debt.md`
  instead — revisit once 2-3 sites' media has been handled manually.
- Descoped entirely, not `taiji`'s to carry: `ubuvm`'s local-dev nginx
  welcome page — zero bearing on `taiji` going live, stays its own
  unrelated low-priority `tech-debt.md` item.
- **Content itself otherwise stays substantially what it already is** —
  aside from the new splash page, this round is a faithful,
  technically-modernized, lightly-polished, bilingual port, not a
  broader content expansion. (Contrast with the "broaden scope" idea
  below, explicitly parked, not MVP.)

## Future ideas / parking lot

Captured here when they come up, not acted on until a deliberate
decision to pull one into a build round — see `planning/site-build-
checklist.md`'s notes on the MVP-vs-big-ideas discipline for why this
list exists and how it gets used.

- **Broaden `taiji`'s content scope** beyond promoting Louise's "Taiji
  for Balance" class specifically, into something of wider interest.
  Context: Louise teaches on Cape Cod, which has a modest Spanish-
  speaking population and a larger Portuguese-speaking one; David is
  also thinking of friends in Spain as a future audience. Genuinely
  good idea, explicitly **not** this round's MVP — parked 2026-10-01
  after review, per David's own request to be held to a pragmatic
  MVP-first discipline rather than let "big ideas" balloon the current
  build. Still fully standalone either way — doesn't change `taiji`'s
  "don't mix with `movement`" constraint regardless of when/whether this
  happens.
- **Portuguese locale support.** Real demographic reason (Cape Cod's
  Portuguese-speaking community), not decided or being built now. The
  locale-list-as-config design already makes this a one-line addition
  whenever it's pulled off the parking lot — nothing to build in advance.

## i18n — confirmed in scope for this redesign, 2026-10-01

David: "yes, it means translating into Spanish." EN/ES now, for the
*existing* content (translated, not expanded — see MVP scope above).
Matches the project-wide i18n decision (`planning/architecture.md`) —
`taiji` is simply where it gets implemented first.

## Open for Phase D (hosting) — found 2026-10-02

- **Root URL and legacy URLs.** The frozen build has no
  `build/index.html`: the site lives at `/en-US/` and `/es-ES/`, so a
  bare `https://taiji.genuinemerit.org/` currently has nothing to
  serve. Separately, the URLs people already have (Louise's printed
  and emailed links, bookmarks) are the legacy ones. **Corrected
  2026-10-02**: the first version of this note listed them from
  `sites/taiji/heirloom/`, but that copy was reworked locally on
  2026-10-01; the live legacy server has a single page, `taiji.html`,
  served at `/`, plus `/vid/Taiji_for_Balance.mp4`,
  `/vid/Taiji_for_Balance_rear_view.mp4`, `/img/taiji-tree.jpg`,
  `/styles.css`, `/favicon.ico`. Redirect map now in
  `ansible/vhosts.yml` (done 2026-10-02); `/styles.css` is
  deliberately not redirected (no new equivalent), `/favicon.ico` is
  served directly.
- **Behaviour change to be aware of**: legacy `/` showed the class page
  itself; new `/` goes to the splash page, one click from it (the
  splash is part of the confirmed MVP). `/taiji.html` goes straight to
  the class page.
  **Decided 2026-10-02 (David), applies to every site, not just
  taiji:** `/` follows the visitor's browser language setting
  (`Accept-Language`); no supported match → `en-US`. Implementation
  notes for the server config: a *temporary* (302) redirect, not a
  permanent one, since the target depends on the visitor; mark the
  response `Vary: Accept-Language`; the visible language switcher
  stays on every page so a wrong guess is one click to fix; deeper
  URLs are never auto-redirected by language. The legacy-URL map
  (redirects to the matching new pages) is still to be written.
- **Not the same thing as the bare domain** (`genuinemerit.org/`
  itself, as opposed to `taiji.genuinemerit.org/`). What the bare
  domains serve is undecided — David is considering a hub/menu page
  for the sites in that domain; a 404 is acceptable until then. See
  question 2 in `design/certificates.md`.
