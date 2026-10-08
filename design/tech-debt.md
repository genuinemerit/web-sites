# Tech debt

Consciously deferred work — lightweight markdown equivalent of `sask`'s
`design/debt/tech-debt.toml` (no schema/validator, per the same
"lighter than `sask`" principle as the rest of `design/`/`planning/`).
One entry per item: what it is, why it's deferred, when to revisit.
Mark `[resolved 2026-...]` in place rather than deleting, so there's a
record of what got done.

**Distinct from each site's "Future ideas / parking lot" section**
(e.g. `design/taiji.md`) — this file is for known imperfections to
eventually fix (bug-like: cert handling, video compression, cosmetic
cleanup). Parking lots are for exciting-but-not-now scope expansions
(feature-like: "broaden this site's whole content focus"). See
`planning/site-build-checklist.md`'s MVP-vs-big-ideas section for the
reasoning behind keeping these separate.

**Two tiers, added 2026-10-01**: `High priority` vs. `Open` — kept
deliberately simple (just two headings, no numeric scoring/schema) per
the same lightweight principle as everything else here.

## High priority

- **Media-processing tooling: size checking, compression, format/size
  normalization for images/video/sound.** Raised to high priority
  2026-10-01, during `taiji`'s MVP scoping — David wants this to stay
  visible, not quietly sink to the bottom of an undifferentiated list.
  Consolidates three previously-separate notes into one real ask:
  automated checking of file size/format, applying compression, and
  normalizing to a standard set (originally logged piecemeal as "video
  compression options" and the "1GB-per-file media routing rule" — both
  superseded by this single, clearer item). **Deliberately NOT built
  for `taiji`** — its one image and two videos were compressed by hand
  with simple one-off commands instead, specifically to avoid building
  generalized tooling before we've done the manual version enough times
  to know what it actually needs to do. Revisit once 2-3 sites' media
  has been handled manually and the real patterns are clear — that's
  when this tooling should actually get designed, not before.
  **Manual pass #2 (2026-10-04, `comunidad`'s Open Mic, 29 images)** —
  patterns emerging: two widths (800 + up to 1600), WebP q75, a small
  JSON manifest of variant dimensions feeding a template macro for
  `srcset`/`width`/`height`. The hub pages (pass #1½) used fixed
  600/1200 square variants instead. One more site, then design the
  tool around the manifest approach.
  **Home and scope, from David 2026-10-04**: `tools/studio/` (same name
  as `sask`'s `tools/studio/`) is where he's collecting his own clean-up
  scripts for images, sound and video — first one `fb-prep.sh`
  (resize, EXIF-orient, strip metadata incl. GPS, keep colour profile,
  progressive JPEG). When this item is picked up, as a deliberate
  tangent: gather his scripts, review `sask`'s studio tooling, add what's
  missing (proposals welcome), and draw on ImageMagick's toolbox — then
  decide what's versioned. Until then `tools/studio/` stays untracked
  unless David says otherwise.

## Open

- **Certificate handling strategy for the new droplet/architecture —
  needs a thorough discussion.** [in discussion 2026-10-02 — proposal
  in `design/certificates.md`] Noted 2026-10-01
  while surveying the legacy droplet for anything else worth pulling:
  found `/root/backup_certbots.sh` + a `letsencrypt-backup-20251011.tgz`
  archive there — a pattern for backing up Let's Encrypt certs that
  David had already built for the legacy box, worth reviewing as a
  reference point, not copying blind. The real scope of this discussion
  is bigger than just backup, though: certbot/renewal mechanics are
  already documented as healthy on the legacy droplet
  (`legacy/certificates.md`), but the new droplet's cert *count and
  shape* changes with the confirmed domain assignment
  (`planning/target-sites.md`) — `.org` primary per public site, `.com`
  redirects (which still need their own valid certs to serve the
  redirect over HTTPS), `.net` reserved for later. Worth a dedicated
  design pass once we're building the actual deploy/nginx-per-site
  tooling, not now.
- **Public deployment of guides/references/changelog docs.** Confirmed
  2026-10-01: belayed for now. Content stays as local Markdown in the
  dev tree (pandoc-rendered when needed, not deployed), backed up via
  `tools/dev/backup-to-laptop.sh` to Dropbox — same treatment as
  everything else, just not published anywhere public. Revisit once
  there's an actual reason to (e.g. the `.net` admin/editor tooling
  becoming real, or wanting these genuinely public). See
  `planning/architecture.md`'s Docs section.
- **Replace the default nginx welcome page on `ubuvm`.** [resolved
  2026-10-02 — David's `default` site, installed by
  `tools/dev/setup-local-nginx.sh`, also the droplet's default page] Currently the
  stock `/var/www/html/index.nginx-debian.html` "Welcome to nginx!" page
  still serves for any request to `ubuvm`'s nginx that doesn't match one
  of the 7 site vhosts (e.g. plain `http://localhost/` or `http://
  127.0.0.1/`). David wants to swap in something more fun. Not urgent —
  purely cosmetic, local-dev-only, explicitly **not** part of `taiji`'s
  MVP (descoped 2026-10-01 — it has zero bearing on any site going
  live, pulling it in would've been an unrelated item riding along for
  no reason). To do it: create `/var/www/html/index.html` (needs
  `sudo`, that directory is root-owned) — nginx's `index` directive
  checks `index.html` before falling back to the stock
  `index.nginx-debian.html`, so a new file there takes over
  automatically, no need to touch or delete the original. No nginx
  reload needed, just a static file change.
- **Readability check not wired into `pre-build-check.sh`.** Added
  2026-10-02 alongside the HTML/link/contrast/i18n checks, but
  deliberately left out: `textstat`'s readability formulas are tuned
  for English, and every site here is bilingual — a gate that scores
  Spanish pages with English formulas would produce noise, not signal.
  Revisit when there's more prose to judge (e.g. `comunidad`), and decide
  then whether it's a gate, an advisory report, or English-only.
- **Removing a site from `ansible/vhosts.yml` doesn't remove it from the
  droplet.** Added 2026-10-02 with `roles/sites`: deploy adds and updates
  vhosts, content and certificates, but never deletes them, so a removed
  entry's nginx vhost, files and certificate linger (and certbot keeps
  trying to renew it). Fine while sites are only being added; handle it
  (a small cleanup task, or a documented manual step) before the first
  real removal.
