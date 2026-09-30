# Tech debt

Consciously deferred work — lightweight markdown equivalent of `sask`'s
`design/debt/tech-debt.toml` (no schema/validator, per the same
"lighter than `sask`" principle as the rest of `design/`/`planning/`).
One entry per item: what it is, why it's deferred, when to revisit.
Mark `[resolved 2026-...]` in place rather than deleting, so there's a
record of what got done.

## Open

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
