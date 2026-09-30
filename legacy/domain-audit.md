# Domain audit

Pulled 2026-09-29 via the DigitalOcean API (`doctl`, using the existing token
at `~/.config/sask/infra.env` — read-only calls only: `account get`,
`compute droplet list`, `compute domain list/records list`). Account: David
Stitt, team "Genuine Merit".

## Droplets on the account

| Name | Public IPv4 | Region | Status | Memory | VCPUs | Disk |
|---|---|---|---|---|---|---|
| `gmerit-nyc2` | 162.243.111.56 | nyc2 | active | 2GB | 1 | 70GB |
| `sask-droplet` | 104.248.22.105 | fra1 | active | 1GB | 1 | 25GB |

Only `gmerit-nyc2` is in scope for this project (the legacy static-sites
box). `sask-droplet` belongs to the unrelated `sask` project.

## The 5 domains (all on DigitalOcean nameservers, as David said)

All 5 have an `A @` record pointing at `162.243.111.56` (`gmerit-nyc2`), with
per-site CNAMEs layered on top:

| Domain | Subdomains (CNAME) | Matches an inventoried site? |
|---|---|---|
| `davidstitt.net` | `music` | Yes — `music.davidstitt.net`. |
| | `sask` → **`A 46.101.68.21`** (not a CNAME, separate record) | Not this project — belongs to `sask`, and that IP does **not** match `sask-droplet`'s current IP (104.248.22.105). Looks stale. Flagging only; not touching it, out of scope here. |
| `genuinemerit.com` | `taiji`, `sandwichopenmic`, `qigong` | Yes, all 3 match live sites. |
| `genuinemerit.org` | `sfp`, plus **`admin`, `auth`** | `sfp` matches. `admin` and `auth` don't correspond to anything found on the droplet (no matching nginx vhost). Unexplained. |
| `genuinemerit.net` | `mint` | Matches the now-decommissioned mint site. DNS record still exists — traffic to `mint.genuinemerit.net` now falls through to nginx's default catch-all rather than 404ing cleanly, since the vhost is gone but the DNS record isn't. |
| `genuinemerit.info` | **`story`, `wiki`, `docs`** | None of these correspond to anything found on `gmerit-nyc2`. Unexplained — not in the nginx inventory at all. |

`windfallhouse.genuinemerit.com` (the config we decided to drop) has **no
DNS record at all** — consistent with it having been an abandoned config
that never actually went live.

## Resolved (2026-09-29)

1. **`genuinemerit.org`: `admin`, `auth`** — confirmed aspirational, never
   used. **Removed** (CNAME records `61067894`/`75089185` deleted via the
   DO API). `genuinemerit.org` now only carries `sfp` plus boilerplate
   NS/SOA/A.
2. **`sask.davidstitt.net` → `46.101.68.21`** — confirmed this is `sask`'s
   active, operational deployment (different droplet, different project).
   Not a mistake to fix here. Recorded in `do-resources-status.md` for
   overall-DO-layout context only; any repair happens inside the `sask`
   project.

## Resolved (2026-09-30, second round)

3. **`genuinemerit.info`: `story`, `wiki`, `docs`** — confirmed
   aspirational/unused, **removed**.
4. **`mint.genuinemerit.net` DNS record** — **removed** (site
   decommissioned).
5. **`genuinemerit.info`'s overall fate** — confirmed (planning session,
   see `planning/target-sites.md`): auto-renew **cancelled**, domain
   expires **2026-11-07** and will lapse. No longer an open question —
   don't add anything new there, nothing should depend on it.

## Domain plan for the rebuild

See `planning/target-sites.md` for the full assignment (`davidstitt.net`
for personal/private sites, `genuinemerit.org` as primary public front-end
with `.com` redirecting and `.net` reserved for admin/editor tooling) —
this file remains the legacy-state record; that one is the forward plan.
