# TLS certificates on the new droplet — proposal for discussion

2026-10-02. Status: **proposed, not decided.** Picks up the "thorough
discussion on cert handling" item from `design/tech-debt.md`. Constraint
from David: the legacy droplet will be destroyed, so everything —
issuance, renewal, redirects — must live on the new droplet, with no
lasting dependency on the old one.

## What's changed since the legacy setup (verified 2026-10-02)

- **Let's Encrypt stopped sending expiry emails** (June 2025). Nothing
  warns us if renewal quietly breaks — we have to check ourselves.
- **Certificate lifetimes are shrinking**: 90 days today, 64 days from
  Feb 2027, 45 days from Feb 2028. Renewal must be fully automatic;
  anything manual or fragile gets exercised twice as often.
- **Let's Encrypt has retired OCSP**, so old `ssl_stapling` config is
  now dead weight.
- **Ubuntu 26.04's packages**: `nginx` 1.28.3, `certbot` 4.0.0, and
  `caddy` **2.6.2** — Ubuntu's Caddy is a 2022 release, too stale for a
  public server (relevant to option B below).

## Names that need certificates

From `planning/target-sites.md`:

- Public, on `genuinemerit.org` with a `.com` twin that redirects:
  `taiji`, `comunidad`, `play`, `spain` — 8 names.
- Personal, on `davidstitt.net`: `music`, `movement`, `callejerez` — 3
  names.
- **Undecided** (questions below): the bare apex domains, and the
  legacy names being retired (`sandwichopenmic.genuinemerit.com`,
  `qigong.genuinemerit.com`, `sfp.genuinemerit.org`).

## Options considered

### A. nginx + certbot, HTTP-01 "webroot" — recommended

certbot proves domain ownership by writing a token file under one shared
directory, which nginx serves on plain HTTP. No secrets on the server,
no DNS API access.

Why I recommend it:

- **Everything comes from Ubuntu's own archive**, so the droplet's
  existing unattended security upgrades patch nginx and certbot with no
  extra repositories trusted as root.
- Keeps the confirmed architecture: nginx on the droplet, the
  already-built local nginx dev vhosts (prod/dev parity), and GoAccess
  reading nginx's standard logs.
- Visible, learnable mechanics (project goal #1), and the pattern David
  already ran for years on the legacy box — minus its weaknesses.

Cost: more moving parts than Caddy. The design below keeps them small
and entirely Ansible-owned.

### B. Caddy — the serious alternative

Caddy obtains and renews certificates by itself, redirects HTTP→HTTPS by
itself, and a `.com`→`.org` redirect is three lines. David already runs
it for `sask`. Since the nginx role has never touched a real droplet,
switching now costs little.

Why not first choice: Ubuntu's Caddy is years stale, so we'd trust
Caddy's own apt repository (Cloudsmith-hosted) with root on the server
and opt it into unattended upgrades; local dev would switch from nginx
to Caddy for parity; GoAccess would read Caddy's JSON log format. All
workable — a reasonable choice if "fewest moving parts" outweighs
"everything from the Ubuntu archive" for you.

### C. DNS-01 via the DigitalOcean API — rejected

Ownership is proven by creating DNS records through DO's API, which
allows wildcard certificates and issuance before DNS moves. But the
droplet would hold a DO token able to edit DNS for **every** domain in
the account, `sask`'s included — a compromised web server could
silently redirect all of them. Not worth it for ~11 names. Running it on
`ubuvm` and copying certs over instead makes `ubuvm` a renewal
dependency (it's off whenever the laptop is).

## Proposed design (option A)

1. **One catch-all port-80 server** for every hostname: serves
   `/.well-known/acme-challenge/` from a shared directory, and
   permanently redirects everything else to `https://$host$request_uri`.
   Per-site configs are then HTTPS-only and only get enabled once their
   certificate exists. This removes the usual chicken-and-egg problem.
2. **One certificate per site**, named after it, covering that site's
   names (e.g. `--cert-name taiji -d taiji.genuinemerit.org -d
   taiji.genuinemerit.com`). One giant multi-name certificate is avoided
   deliberately: any one name failing validation would block renewal
   for all sites.
3. **`certbot certonly --webroot` only — never `certbot --nginx`**, which
   rewrites nginx config that Ansible owns and causes drift.
4. **Renewal**: certbot's packaged systemd timer, plus a deploy hook that
   reloads nginx after a renewal. `certbot renew --dry-run` is part of
   post-deploy verification.
5. **Staging during test cycles**: destroy/recreate testing uses Let's
   Encrypt's staging service. Production allows only 5 identical
   certificates per week, which repeated recreates would exhaust.
6. **No certificate backups.** Certificates are reissued on a fresh
   droplet in seconds, so private keys never leave the droplet. This
   retires the legacy `backup_certbots.sh` rather than porting it.
7. **TLS settings**: Mozilla's "intermediate" profile (TLS 1.2 + 1.3), no
   OCSP stapling. HSTS added only after a site is verified, starting
   with a short max-age and raising it later; no preload list.
8. **CAA DNS records** on all four domains, allowing only
   `letsencrypt.org` to issue certificates for them — a cheap guard
   against mis-issuance. Compatible with the legacy box, which also uses
   Let's Encrypt.
9. **Expiry monitoring** (replacing the emails Let's Encrypt dropped):
   the post-deploy smoke test fails if any certificate has fewer than
   21 days left. A recurring check is a question below.

## Cutover, per name

- **Brand-new names** (e.g. `taiji.genuinemerit.org`, `comunidad…`):
  point DNS at the new droplet, issue the certificate, and verify over
  real HTTPS before anyone uses them. No effect on the legacy sites.
- **Names live on legacy today** (`taiji.genuinemerit.com`,
  `music.davidstitt.net`): lower the DNS TTL from 12 hours to 5 minutes
  a day ahead (it's 43200 s today), then switch at a quiet hour. Two
  ways to handle the certificate:
  - *Simple*: switch DNS, issue immediately. Leaves a window of a
    minute or two where some visitors could see a certificate warning.
  - *No-gap*: before switching, add a temporary redirect on the legacy
    server for `/.well-known/acme-challenge/` pointing at the new
    droplet. Let's Encrypt follows it, so the new server gets its
    certificate while DNS still points at legacy, and the switch has
    no gap. A small, reviewed, temporary edit to a box that's being
    destroyed anyway.
  - Proposal: no-gap for `taiji.genuinemerit.com` (Louise's class),
    simple for `music.davidstitt.net`.

## Questions for David

1. **A or B?** nginx + certbot (recommended) or Caddy.
2. **Apex domains** (`genuinemerit.org/.com/.net`, `davidstitt.net`):
   what should the bare domain serve once legacy is gone — a small
   landing page, a redirect somewhere, or nothing (remove the record)?
3. **Retired legacy names** (`sandwichopenmic`, `qigong`, `sfp`):
   redirect to their new homes (`comunidad`, `movement`, `play`) — which
   means keeping certificates for them indefinitely — or let them lapse?
4. **Recurring expiry check**: is the post-deploy check enough, or do you
   want a weekly check as well (e.g. a free external monitor, or a timer
   on the droplet)?
