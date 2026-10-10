# Legacy droplet teardown

Written 2026-10-10 (music plan step 11 / roadmap Phase 4). Status: **done, 2026-10-10 ~20:20 UTC** (results at the
end). Irreversible by David's choice: no snapshot kept.

## What's being removed (inventory, verified read-only 2026-10-10)

- **Droplet** `gmerit-nyc2` (ID `470058219`), `nyc2`, Ubuntu 24.10, IP `162.243.111.56`, 18 GB used of 67 GB.
  Running: nginx (5 site configs), postfix (listening on port 25), DigitalOcean's agents. Postgres 16 is
  installed but inactive (a 39 MB leftover cluster from the removed `mint` service).
- **Nothing else is attached**: no volumes, no backups, no reserved IP, no cloud firewall, no monitoring
  alerts or uptime checks. One **old snapshot** exists: `gmerit-nyc2-1760195461125` (13.95 GiB, taken
  2025-10-11).
- **DNS records still pointing at it** (all to be deleted):

  | Domain | Record | Why it still exists |
  | --- | --- | --- |
  | `genuinemerit.com` | `sandwichopenmic` A | retired name (`design/domains.md`) |
  | `genuinemerit.com` | `qigong` A | retired name |
  | `genuinemerit.org` | `sfp` A | retired name |
  | `genuinemerit.net` | `@` A | `.net` left unresolved by David's decision |

- **Content**: every site's files were staged into `sites/*/heirloom/` in Phase 2 (backed up to Dropbox);
  taiji, comunidad/Open Mic and music now run on the new droplet. `/root` holds only shell/editor history,
  apt backups and the old `backup_certbots.sh` + `letsencrypt-backup-20251011.tgz` (superseded by the new
  certificate design). The final snapshot keeps all of it regardless.

## Effects to accept

- `sandwichopenmic.genuinemerit.com`, `qigong.genuinemerit.com` and `sfp.genuinemerit.org` stop resolving
  (retired, no redirects). `qigong` and `sfp` content returns later as `movement` and `play`.
- `genuinemerit.net` stops resolving.
- The legacy droplet's monthly cost (~$16) stops, and so does the old snapshot's (~$0.84/month).
- **Nothing is recoverable afterwards**: no final snapshot, and the 2025 snapshot is deleted too (David's
  decision - he has pulled everything he wants; site content is also in `sites/*/heirloom/` and Dropbox).

## Procedure

1. **DNS first.** Delete the four records above. This comes *before* destroying the droplet: once destroyed,
   DigitalOcean can give `162.243.111.56` to another customer, and any record still pointing there would hand
   that stranger our subdomain ("dangling DNS" / subdomain takeover). Verify each name returns no address from
   the authoritative nameservers. Note: the `genuinemerit` SSH alias (`~/.ssh/config.d/ubuvm_gm`) reaches the
   box *through* `genuinemerit.net`, so SSH stops working here - anything to copy off the box happens before
   this step. Steps 2-4 use the DigitalOcean API, not SSH.
2. ~~Power off~~ and ~~final snapshot~~ - dropped (David, 2026-10-10: no snapshot needed).
3. **Delete the old snapshot** `gmerit-nyc2-1760195461125` (ID `202792001`). Verify it's gone from
   `doctl compute snapshot list`.
4. **Destroy** the droplet (`doctl compute droplet delete 470058219`). Verify it's gone from
   `doctl compute droplet list`.
5. **Clean up locally**: remove the `genuinemerit` SSH alias and its `known_hosts` entries on `ubuvm` (David
   may want to keep the key itself if used elsewhere).
6. **Verify the live sites**: full smoke test through public DNS (expect 110/110, unchanged); `sask` untouched.
7. **Record**: this file (results), `legacy/README.md`, `planning/roadmap.md` Phase 4, `design/music.md`
   step 11, the runbook's teardown section; commit after David's OK.

## Decisions (David, 2026-10-10)

- No final snapshot - he has already pulled everything he wants from the server.
- The 2025 snapshot is deleted as well.

## Results (2026-10-10 ~20:20 UTC)

- DNS: the four records deleted after re-checking each ID still pointed at `162.243.111.56`
  (`sandwichopenmic`, `qigong`, `sfp` now NXDOMAIN; `genuinemerit.net` has no address). No record in any
  domain points at the old IP.
- Snapshot `gmerit-nyc2-1760195461125` deleted; the account has no snapshots.
- Droplet `gmerit-nyc2` destroyed; remaining droplets: `sask-droplet`, `web-sites-droplet`.
- `ubuvm`: `~/.ssh/config.d/ubuvm_gm` (the `genuinemerit` alias) removed, `genuinemerit.net` known_hosts
  entry removed (backup in `~/.ssh/known_hosts.old`), stale connection socket removed; key
  `~/.ssh/gm_ed25519` kept. SSH to `web-sites-droplet` verified.
- Live sites: full public smoke test 110/110; `sask.davidstitt.net` unaffected (200).
