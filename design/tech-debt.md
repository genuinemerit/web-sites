# Tech debt

Consciously deferred work — lightweight markdown equivalent of `sask`'s
`design/debt/tech-debt.toml` (no schema/validator, per the same
"lighter than `sask`" principle as the rest of `design/`/`planning/`).
One entry per item: what it is, why it's deferred, when to revisit.
Mark `[resolved 2026-...]` in place rather than deleting, so there's a
record of what got done.

## Open

- **Certificate handling strategy for the new droplet/architecture —
  needs a thorough discussion, coming up (not yet).** Noted 2026-10-01
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
- **Video compression options.** Noted 2026-10-01 while pulling `taiji`'s
  ~1.9GB of legacy video over the network (slow enough to prompt the
  thought). Worth investigating once the pipeline work reaches
  image/sound optimization (`planning/architecture.md`'s Image/sound
  optimization section) — that section currently leans on `sask`'s
  `build_assets.py` approach for images specifically; video compression
  is a related but distinct question not yet covered there.
- **1GB-per-file media routing rule, for the future build pipeline.**
  David's idea (2026-10-01, during the legacy content pull): once the
  real pipeline exists, any individual image/sound/video file over 1GB
  should route to `sites/<site>/media/` rather than wherever smaller
  files land, as an automated categorization rule. Explicitly **not**
  applied during the Phase 2 raw-material pull itself — everything
  pulled there goes into `sites/<site>/heirloom/` regardless of size,
  this is a note for later pipeline design, not a rule in effect now.
- **Public deployment of guides/references/changelog docs.** Confirmed
  2026-10-01: belayed for now. Content stays as local Markdown in the
  dev tree (pandoc-rendered when needed, not deployed), backed up via
  `tools/dev/backup-to-laptop.sh` to Dropbox — same treatment as
  everything else, just not published anywhere public. Revisit once
  there's an actual reason to (e.g. the `.net` admin/editor tooling
  becoming real, or wanting these genuinely public). See
  `planning/architecture.md`'s Docs section.
- **Replace the default nginx welcome page on `ubuvm`.** Currently the
  stock `/var/www/html/index.nginx-debian.html` "Welcome to nginx!" page
  still serves for any request to `ubuvm`'s nginx that doesn't match one
  of the 7 site vhosts (e.g. plain `http://localhost/` or `http://
  127.0.0.1/`). David wants to swap in something more fun. Not urgent —
  purely cosmetic, local-dev-only. To do it: create `/var/www/html/
  index.html` (needs `sudo`, that directory is root-owned) — nginx's
  `index` directive checks `index.html` before falling back to the
  stock `index.nginx-debian.html`, so a new file there takes over
  automatically, no need to touch or delete the original. No nginx
  reload needed, just a static file change.
