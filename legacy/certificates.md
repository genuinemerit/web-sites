# TLS certificates

Reviewed 2026-09-29. All 5 live sites use Let's Encrypt via `certbot`,
auto-renewed — this part of the setup is healthy and needs no urgent
attention.

## Renewal mechanism

- `certbot.timer` (systemd timer, not cron): runs `certbot.service` twice
  daily (`00:00` and `12:00`, ±12h random delay to spread load across
  Let's Encrypt's infrastructure). Enabled, active, last ran without issue.
- `/etc/letsencrypt/renewal/*.conf` — one per live domain (`music`,
  `qigong`, `sandwichopenmic`, `sfp`, `taiji`). No leftover renewal config
  for `mint`, `old_sfp`, or `windfallhouse` — consistent with those never
  having had a cert, or (for `mint`) not currently reflected there since it
  was checked separately (see `inventory.md` — `mint` never had a live cert
  either).

## Cert detail (sampled: `sfp.genuinemerit.org`, representative of all 5)

- Issuer: Let's Encrypt (`CN=YE1` intermediate).
- Algorithm: ECDSA (256-bit) — modern, fine.
- Validity: 90-day Let's Encrypt standard window, auto-renewed well before
  expiry by the timer above.
- File layout: standard certbot symlink structure
  (`/etc/letsencrypt/live/<domain>/{cert,chain,fullchain,privkey}.pem` →
  `../../archive/<domain>/...N.pem`), default permissions, nothing unusual.

## nginx TLS config

- Shared `options-ssl-nginx.conf` (certbot-managed, based on the Mozilla
  "intermediate" cipher/protocol profile): `TLSv1.2`/`TLSv1.3` only,
  reasonable modern cipher list, session cache tuned. This part follows
  current best practice and doesn't need changing.
- `server_tokens build;` in `nginx.conf` — **not** a TLS issue per se, but
  related disclosure hygiene: this leaks the nginx version/build tag in
  error pages and the `Server` header. The stock Ubuntu config file even
  has its own comment noting "Recommended practice is to turn this off" —
  and it's still set to `build`, not `off`. Small, easy hardening item for
  the new droplet.
- No HSTS (`Strict-Transport-Security`) header is sent by any site, despite
  all of them force-redirecting HTTP→HTTPS already. Cheap addition once
  redirect behavior is confirmed correct on the new droplet.
