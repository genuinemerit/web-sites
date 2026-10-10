# Legacy droplet inventory

> **The droplet was destroyed 2026-10-10** (`docs/legacy-teardown.md`). These notes
> are the historical record of what it ran.

Review of the production droplet (`genuinemerit`, DigitalOcean, host
`gmerit-nyc2`) and its DNS/DO account context, 2026-09-29 through
2026-09-30, over SSH (`ssh genuinemerit`, root) and the DO API (`doctl`,
reusing `sask`'s existing token). Source-of-truth for the web-site
migration project.

**Files, in the order they were produced:**

- `inventory.md` — first-pass droplet inventory: OS, nginx vhosts/domains,
  disk usage per site, which configs are live vs. dormant.
- `open-questions.md` — David's answers to the first round of questions
  (windfallhouse/mint/old_sfp disposition, domain ownership, OS drift,
  large-media handling).
- `decisions.md` — accepted decisions distilled from the above, plus what's
  actually been executed on the droplet/DNS so far (not just decided).
- `domain-audit.md` — DNS record audit across all 5 of David's domains,
  cross-referenced against what's actually live on the droplet.
- `do-resources-status.md` — account-wide DO snapshot (both droplets, all
  5 domains' full DNS records) for overall-layout context.
- `content-inventory.md` — per-site directory trees, sub-sites flagged,
  the `sfp/saskan/` cross-project asset question.
- `nginx-review.md` — config-level review of `nginx.conf` and every vhost.
- `certificates.md` — TLS/certbot setup and renewal mechanism.
- `security-review.md` — droplet-level security posture (accounts, SSH,
  firewall, ports).

Everything through 2026-09-29 was read-only. A small number of explicitly
authorized changes were made 2026-09-29/30 (the `mint` decommission, and
removal of confirmed-unused DNS records) — see `decisions.md` for exactly
what and when.
