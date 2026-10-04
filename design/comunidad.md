# `comunidad` — redesign decisions

Started 2026-10-04, second site in the Phase 3 build order. Community
projects: the Sandwich Open Mic first, later the UAH / Alcalingua class
material (`heirloom/uah/`) and the Intercambio de Idiomas.

## Confirmed

- **Domain**: `comunidad.genuinemerit.com`, `.org` redirecting
  (public family, `design/domains.md`) — David briefly suggested
  `davidstitt.net`, then confirmed `genuinemerit` 2026-10-04.
- **Structure**: a collection of collections. `/<locale>/` lists them;
  each collection is a path under it, starting with `/<locale>/openmic/`.
- **Open Mic content**: David's own prototype
  (`heirloom/openmic/openmic-prototype/`, 2026-10-03) — he reviewed all
  the legacy openmic material and selected/edited the 29 images himself.
  The legacy `sandwichopenmic.genuinemerit.com` URLs are retired, not
  redirected (`design/domains.md`).

## Built and live 2026-10-04

- `/<locale>/openmic/`: the prototype, faithfully — same layout, motion
  and text. Changes: colour palette moved inline under the shared token
  names (`--paper` → `--background`, `--ink` → `--text`) so the contrast
  check can verify it; reset/font/link/focus rules now come from
  `/shared/tokens.css`; layout and motion in
  `sites/comunidad/static/css/openmic.css`; every string and alt text a
  catalog tag (`config/i18n/comunidad/`); Spanish draft; a top bar with
  a link back to the index and the language switch (the prototype had
  neither). Animation comments that named individual performers were
  made neutral — the stylesheet is public.
- **Images**: WebP at quality 75, an 800 px variant plus one up to
  1600 px (or the original width, if smaller), served with `srcset` so
  phones fetch the small one; dimensions in
  `static/img/openmic/manifest.json`. 6.5 MB of JPEGs became 4.1 MB
  (both sets), ~1.6 MB on a phone. Versioned under `static/` (curated
  content, moderate size) rather than gitignored `media/`.
- **`/<locale>/` index: a stand-in**, on the shared hub layout with the
  Open Mic palette and opening artwork: Open Mic live; UAH · Alcalingua
  and Intercambio de Idiomas "coming soon". Replace when David designs
  the real one.
- `vnu`'s CSS checker doesn't know `animation-timeline` /
  `animation-range` (real, shipping, used inside `@supports`); those two
  messages are filtered in `pre-build-check.sh`, verified not to hide
  other CSS errors.

**Live 2026-10-04 ~11:35 UTC** at `https://comunidad.genuinemerit.com/`
(`.org` redirects): David reviewed the pages locally and approved the
Spanish with no changes; DNS A records for `comunidad` on `.com` and
`.org` (TTL 300, new names — nothing displaced); production certificate
for both; Comunidad flipped to live on the `genuinemerit` hub. Full
public-DNS smoke test 86/86, plus the new per-locale sub-page checks
(`pages:` in `vhosts.yml`).

## Open — for David

- The real `comunidad` index page (the stand-in is live meanwhile), and
  a favicon (none yet; the legacy `heirloom/openmic/favicon.ico` exists
  if wanted).

## Future ideas / parking lot

- UAH / Alcalingua and Intercambio collections (next comunidad rounds).
