# Decisions (from open-questions.md, David's answers 2026-09-29)

- **`windfallhouse`** — drop. Abandoned project, not carried forward.
- **`old_sfp.conf`** — drop. Confirmed dead predecessor of `sfp.conf`.
- **`mint`** — fully decommissioned on the legacy droplet, 2026-09-29.
  Removed: `mint.service` (unit + enablement), `mintdb` database, `mintuser`
  Postgres role, `mintuser` OS account + home dir (31M), and
  `/etc/nginx/sites-available/mint.conf`. `postgresql.service` was stopped
  and disabled (it had no other consumer) but the `postgresql` package
  itself was left installed, not purged — left as optional further cleanup,
  not assumed.
- **OS target** — confirmed: new droplet on the latest fully-supported
  Ubuntu LTS (26.04 LTS as of today). The 24.10-vs-24-LTS mismatch on the
  legacy box was just drift/a mistake, not intentional — no change to the
  original project target.
- **Large media (`music`/`openmic`/`taiji`)** — will review file-by-file
  later to decide keep/archive/drop; CDN/object storage is a maybe, not a
  given — David's note: a minimally-sized droplet has been sufficient up to
  now, so this isn't a forced move, just worth reviewing.

## Domain audit (done 2026-09-29 — see `domain-audit.md`)

David owns **5 domains total** (`davidstitt.net`, `genuinemerit.com`,
`genuinemerit.org`, plus `genuinemerit.info` and `genuinemerit.net`, both
confirmed via the DO API), all on DigitalOcean nameservers, most with
sub-domains already carved out. **Only `taiji.genuinemerit.com` is required
to keep its current domain** — the other live sites' domains/sub-domains are
open to being reorganized as part of the rebuild. This bears directly on the
repo-shape question (one repo vs. per-site) — sequencing the domain
questions (see `domain-audit.md`) before locking that in, per David's
explicit agreement.

The audit surfaced unexplained DNS records not accounted for anywhere in the
droplet inventory: `admin`/`auth` on `genuinemerit.org`, `story`/`wiki`/`docs`
on `genuinemerit.info`.

**Resolved 2026-09-30:**

- `admin`/`auth` on `genuinemerit.org` — confirmed aspirational/unused,
  **removed**.
- `story`/`wiki`/`docs` on `genuinemerit.info` — same, confirmed
  aspirational/unused, **removed**. Whether `genuinemerit.info` continues
  to be used at all is deferred to a later decision (David's call).
- `mint.genuinemerit.net` CNAME — dangling after the `mint` decommission,
  **removed**.
- `sask.davidstitt.net` → `46.101.68.21` — **not stale**, confirmed by
  David as `sask`'s active, operational deployment. Not touched, not this
  project's concern; recorded in `do-resources-status.md` for context only.

**Resolved 2026-09-30 (domain planning session):**

- `genuinemerit.info` — auto-renew cancelled by David; then, **2026-10-01,
  actively deleted** (DNS records and the domain itself removed from the
  DO account, ahead of its Nov 7 natural expiry). Resolves the long-open
  "keep or drop this domain" question. See
  `planning/target-sites.md` for the full new-site domain assignment
  (`davidstitt.net` for personal/private sites, `genuinemerit.org` as
  public-facing primary, `.com` redirecting, `.net` reserved for future
  admin/editor tooling).

**Resolved 2026-09-30 (second round):**

- `sfp/saskan/` — confirmed by David: leftover from a dev project now
  being subsumed into the `sask` app. **Deleted** (`rm -rf
  /usr/share/nginx/html/sfp/saskan`).
- `sfp/cool_scripts.html` (the top-level one, outside `docs/`) — confirmed
  stale by David. **Deleted**; `sfp/docs/cool_scripts.html` is the one
  that remains/is current.
- `deployer` orphaned sudoers rule — David's recollection: associated with
  the defunct `mint` app. **Removed** from `/etc/sudoers` (backed up first
  as `/etc/sudoers.bak.<timestamp>`; `visudo -c` confirmed the file still
  parses correctly afterward).
- The `ecdsa-sha2-nistp256 ... expire_at ...` key in root's
  `authorized_keys` — David didn't recognize it and asked for removal.
  **Removed** (backed up first as
  `/root/.ssh/authorized_keys.bak.<timestamp>`). Important context found
  while removing it: the key's own comment says
  `# Added and Managed by DigitalOcean Droplet Agent (code name: DOTTY)` —
  this is DigitalOcean's own web-console/"recovery console" access
  mechanism, added automatically by the `do-agent` service (confirmed
  running/enabled on this droplet), not a mystery third-party credential.
  Because `do-agent` actively manages this entry, **it may get re-added
  automatically** (e.g. next time someone uses the DO dashboard's web
  console, or on an agent check-in) — a one-time file edit may not be
  durable. If it reappears, the actual fix is disabling web-console access
  for this droplet in the DigitalOcean dashboard (or stopping/disabling
  `do-agent`), not re-editing the file again. SSH access re-verified
  working immediately after this change (fresh connection, not reusing an
  already-open one).

Droplet security posture (`security-review.md`) otherwise unchanged —
root-only SSH access, password auth + root login both still enabled, no
fail2ban. These remain findings for the *new* droplet's baseline; no
further droplet surgery done this round.
