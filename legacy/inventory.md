# Legacy droplet inventory — details

Verified 2026-09-29 via `ssh genuinemerit`, read-only.

## Server environment

- Hostname: `gmerit-nyc2` (DigitalOcean).
- OS: **Ubuntu 24.10 "oracular"** — not 24.04 LTS. 24.10 is a standard
  9-month-support release, already past or near end of life, *not* an LTS
  release. Worth confirming with David whether this was intentional or the
  droplet just drifted; either way the new droplet should deliberately be
  24.04 LTS or 26.04 LTS, not another interim release.
- nginx 1.26.0 (Ubuntu package).
- Disk: 67G total, 16G used, 51G free.
- Certs: Let's Encrypt via certbot, renewal via `certbot.timer` (systemd
  timer, not cron — root crontab is empty). All 5 live certs valid,
  expiring 2026-12-11/12/22 (auto-renewal should keep them current until
  then).
- No config management tool (no Ansible/etc. found) — site changes appear to
  have been made by hand directly on the box, matching what David described.

## Sites — enabled and live (5)

All served straight from `/usr/share/nginx/html/<name>/`, HTTPS via
Let's Encrypt, HTTP→HTTPS redirect. Pure static content, no app server
involved for any of these.

| Site (nginx conf) | Domain | Size | Notes |
|---|---|---|---|
| `music.conf` | music.davidstitt.net | 2.9G | Photo/video/audio subfolders (`merida`, `spain`, `sounds`, `videos`) — most of the disk footprint. |
| `openmic.conf` | sandwichopenmic.genuinemerit.com | 2.3G | Monthly gallery pages (`gallery_0624.html` … `gallery_1024.html`), image-heavy. |
| `taiji.conf` | taiji.genuinemerit.com | 1.9G | `img/`, `vid/` — video-heavy. |
| `qigong.conf` | qigong.genuinemerit.com | 19M | Small — `img/`, `sets/`. |
| `sfp.conf` | sfp.genuinemerit.org | 13M | Small, doc/text-heavy (`constitution.html`, `handbook.html`, `platform.html`, `docs/`). |

Note the domain inconsistency across sites: `davidstitt.net` (music),
`genuinemerit.com` (openmic, qigong, taiji), `genuinemerit.org` (sfp) — three
different registered domains in play, not one umbrella domain with
subdomains. Relevant for the "port existing domains" step of the migration —
will need registrar/DNS access for all three, not just one.

## Sites — config present but NOT enabled / NOT live (3)

- **`mint.conf`** → `mint.genuinemerit.net`. This is the one David flagged
  as retired. Confirmed dead, not just disabled:
  - Not symlinked in `sites-enabled/`.
  - `/usr/share/nginx/html/mint` doesn't exist.
  - No Let's Encrypt cert currently issued for this domain (the conf
    references one, but `certbot certificates` doesn't list it).
  - It was a real dynamic app, not static: `mint.conf` proxied to a Unix
    socket (`/home/mintuser/mint/mint.sock`) backed by **`mint.service`**, a
    systemd unit running Gunicorn + a Flask app (`test_wsgi:app`) as user
    `mintuser`, with a PostgreSQL database (`.psql_history` present in
    `mintuser`'s home).
  - **Both `mint.service` and `postgresql.service` are still `enabled`** (boot-start) on this droplet, even though the app is retired.
    `mint.service` is currently in a **failed** state (crashed 2026-09-18,
    `/home/mintuser/mint` source tree is gone so it can't restart) and
    `postgresql.service` is running with nothing left to serve it. This is
    live attack-surface/cruft that should be disabled, not just left
    crashed — flagging for the hardening pass, not acting on it yet.
- **`old_sfp.conf`** → same domain and same html root
  (`/usr/share/nginx/html/sfp`) as the live `sfp.conf`. Reads like a
  superseded predecessor config left behind after `sfp.conf` replaced it —
  not enabled, no separate content. Likely safe to just not carry forward,
  but flagging rather than assuming.
- **`windfallhouse.conf`** → `windfallhouse.genuinemerit.com`. Not enabled,
  `/usr/share/nginx/html/windfallhouse` doesn't exist, and there's no
  Let's Encrypt cert for it either. Unclear if this was ever actually
  launched or is a placeholder for something not yet built — see
  open-questions.md.

## Other

- `sites-available/default` — the stock Ubuntu nginx placeholder
  (`server_name _;`, `root /var/www/html`), not one of David's sites.
- No other unexpected services found running (checked `systemctl
  list-unit-files --state=enabled` and `ps aux`) beyond the mint/postgres
  item above — the rest is standard Ubuntu/DigitalOcean droplet baseline
  (do-agent, cloud-init, unattended-upgrades, etc.).
