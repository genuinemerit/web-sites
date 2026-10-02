# Domains and hostnames — decisions

2026-10-02, David. **Supersedes** the domain assignment in
`planning/target-sites.md` ("Domain assignment — confirmed 2026-09-30"),
which made `.org` primary with `.com` redirecting. The hostnames in use
at any moment are whatever `ansible/vhosts.yml` lists; this file records
the rules behind it.

## Rules

- **`genuinemerit.com` is canonical** for the public family: every site
  lives at `<site>.genuinemerit.com` (`taiji`, `comunidad`, `play`,
  `spain`). So `taiji.genuinemerit.com` — the address Louise's class
  already uses — keeps its domain; only legacy *paths* change, and those
  redirect (`ansible/vhosts.yml`).
- **`genuinemerit.org` mirrors `.com` by redirect**: the bare `.org` and
  every `<site>.genuinemerit.org` permanently (301) redirect to the same
  path on `.com`. One canonical URL per page: no duplicate content for
  search engines, one set of analytics. Each `.org` name rides on its
  site's certificate.
- **`davidstitt.net`** keeps the personal family: `music`, `movement`,
  `callejerez` as `<site>.davidstitt.net`.
- **`genuinemerit.net` stays unresolved** — David is reconsidering
  whether to use it at all. No site, no certificate; its legacy `A`
  record is removed when the legacy droplet goes (docs/cutover-runbook.md).
- **Bare domains get hub pages**: `genuinemerit.com` (with `.org`
  redirecting to it) and `davidstitt.net` each serve an index of their
  family's sites — built 2026-10-02 from David's prototypes as the
  `genuinemerit` and `davidstitt` sites (bilingual, shared hub layout).
  A site not yet live is listed as "coming soon" text, not a dead link;
  flip its `live` flag in `src/websites/<hub>/__init__.py` when it goes up.
- **Requests naming none of our hostnames** (a bare-IP visit, a stale
  DNS record) get the `default` site's page over plain HTTP — David's
  replacement for "Welcome to nginx!", on the droplet and on `ubuvm`.
- **Legacy names retire with the legacy droplet**: `sandwichopenmic.
  genuinemerit.com`, `qigong.genuinemerit.com`, `sfp.genuinemerit.org`.
  No redirects, no certificates — the new architecture supports only the
  new names. Their DNS records are removed at legacy teardown.
- **A site's root `/` follows the browser language**, falling back to
  `en-US` (`design/taiji.md`, 2026-10-02) — a 302 with
  `Vary: Accept-Language`; deep links are never language-redirected.

## Certificates per this layout

One certificate per `vhosts.yml` entry, covering its canonical name and
aliases: `genuinemerit` (`genuinemerit.com`, `genuinemerit.org`),
`davidstitt` (`davidstitt.net`), and one per site (e.g. `taiji`:
`taiji.genuinemerit.com`, `taiji.genuinemerit.org`). A site joins only
when it's actually built and listed in `vhosts.yml`.
