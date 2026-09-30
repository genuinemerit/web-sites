# Droplet security review

`gmerit-nyc2`, read-only review 2026-09-29. Findings only — nothing here has
been changed. Ordered roughly by significance.

## 1. Root-only access, with both password auth and root SSH login enabled

- `ssh genuinemerit` connects directly **as root** — confirmed via `whoami`.
- **No non-root user account exists on the box at all.** `/etc/passwd` has
  no entries in the human UID range (1000+); every account is a system/
  service account (`postgres`, `do-agent`, `sshd`, etc.).
- Effective `sshd` config (via `sshd -T`, the authoritative merged view —
  not just reading the files, since `sshd_config.d/*.conf` are order-
  sensitive and two files disagree, see below):
  - `permitrootlogin yes`
  - `passwordauthentication yes`
  - `pubkeyauthentication yes`
  - `kbdinteractiveauthentication no`
- **The two `sshd_config.d` drop-ins actively conflict:**
  `50-cloud-init.conf` sets `PasswordAuthentication yes`;
  `60-cloudimg-settings.conf` sets `PasswordAuthentication no`. OpenSSH
  takes the *first* value it encounters for a given keyword, and `Include`
  expands the glob in sorted order, so `50-...` wins — confirmed by
  `sshd -T` showing `yes`. This reads like `60-cloudimg-settings.conf` was
  meant to harden this and silently doesn't, because of file ordering.
- **No `fail2ban`, no UFW rate-limiting on SSH.** Combined with the above,
  the box currently accepts password-based root login from anywhere on the
  internet with no brute-force mitigation at all.
- `root`'s `~/.ssh/authorized_keys` has **3 keys**:
  - One with a comment embedding `"expire_at":"2025-11-05T15:33:23Z"` —
    **that date was already in the past** relative to today. Preceded by
    `# Added and Managed by DigitalOcean Droplet Agent (code name: DOTTY)`
    — this is DO's own web-console/recovery-access mechanism, added by the
    `do-agent` service, not a third-party credential. That expiry is just
    JSON text in the SSH comment field — OpenSSH doesn't parse or enforce
    it, so the key remained usable indefinitely despite looking expired.
    David didn't recognize it and asked for it to be removed — **removed
    2026-09-30** (see `decisions.md`). Since `do-agent` actively manages
    this entry, it may reappear on its own; if so, the durable fix is
    disabling web-console access for this droplet in the DO dashboard, not
    another file edit.
  - Two `ed25519` keys with informal comments (`pq_rfw@pm.me`,
    `from_ubuvm`) — David's own, left in place.

**Net effect:** anyone who obtains (or guesses) the root password, or who
still holds a valid copy of that DO console key, has unrestricted root
access, with no lockout/rate-limit layer. This is the single highest-value
hardening item for the new droplet.

## 2. Orphaned `deployer` sudoers rule

`/etc/sudoers` (main file, line 59-60) has:

```text
# Allow deployer sudo without password
deployer ALL=(ALL) NOPASSWD:ALL
```

**No `deployer` account exists** — not in `/etc/passwd`, no home directory.
David's recollection: this was associated with the defunct `mint` app.
**Removed 2026-09-30** (see `decisions.md`) — `/etc/sudoers` backed up
first, `visudo -c` confirmed valid afterward.

## 3. Firewall (UFW) — sane default, minor redundancy

- Active, default **deny incoming / allow outgoing**, logging on.
- Allows: `22/tcp`, `80,443/tcp` (both IPv4 and IPv6).
- Curious but harmless: port 22 is allowed by **two separate, redundant
  rules** — a bare `22/tcp` rule and the `OpenSSH` app-profile rule, doing
  the same thing twice (same for IPv6). Cosmetic cleanup, not a security
  gap by itself.

## 4. Listening ports — nothing unexpected

`ss -tulpn` shows only: `sshd` (22), `nginx` (80, 443), `systemd-resolve`'s
local stub resolver (127.0.0.x:53, loopback-only), and a `code-04c0d99f4f`
process on `127.0.0.1:39235` — a VS Code / editor remote-server helper,
loopback-only, not internet-reachable. Nothing else exposed. Postgres is
now stopped/disabled (see `decisions.md`, `mint` decommission) and wasn't
listening externally even before that.

## 5. Patching

`unattended-upgrades` is enabled (`APT::Periodic::Unattended-Upgrade "1"`)
— the box does get automatic security updates. This part is in good shape.

## 6. chkrootkit and Lynis scan (2026-09-30)

Ran both at David's request as an integrity/hardening check. Neither
installed before; both installed via apt, both read-only scans, nothing on
the box was changed by running them (aside from the packages themselves).

**chkrootkit — clean.** Two flags raised, both well-known false positives
on any modern systemd-based Ubuntu box, not evidence of compromise:
`.build-id` files under `/usr/lib/modules/*/vdso/` (standard kernel build
artifact), and "packet sniffer" on `eth0`/`eth1` (systemd-networkd's normal
DHCP/RA handling trips this specific heuristic on every systemd host).

**Lynis — hardening index 61/100.** Mostly cross-validates this document
rather than surfacing new ground — SSH came back with the same
`PermitRootLogin` issue already flagged above, plus several smaller SSH
knobs worth carrying into the new droplet's baseline config directly:
`MaxAuthTries` (default 6, tighten to ~3), `AllowAgentForwarding`/
`AllowTcpForwarding`/`X11Forwarding` (all default `yes`, not needed for
this use case), `TCPKeepAlive`, `ClientAliveCountMax`, `LogLevel` (raise to
`VERBOSE`).

One genuinely new finding, missed in the manual pass above because the
service wasn't running at the time I checked `ss -tulpn`: **Postfix is
listening on `0.0.0.0:25`/`[::]:25`** (`inet_interfaces = all` in its
config — this has been the config all along, just wasn't an active
process during the earlier check; it restarted as a side effect of
today's `apt install`). `mynetworks` is correctly restricted to
`127.0.0.0/8`, so it's **not an open relay** — but it does let anyone on
the internet banner-grab the hostname and "Postfix (Ubuntu)" via an
unauthenticated `EHLO`. For the new droplet: bind the local MTA to
loopback only (`inet_interfaces = loopback-only`) unless outbound mail
genuinely needs to be reachable from outside, which is unlikely for a
static-site box that just wants local mail for cron/system notifications.

Everything else Lynis raised is the standard long tail you'd get on any
stock, unmanaged Ubuntu box — PAM password-aging/complexity modules not
installed, no GRUB password, no file-integrity monitoring (AIDE-style), no
auditd, no legal login banner, a handful of sysctl values at their
defaults. None of these are specific to *this* box or its history; they're
generic "would be nice on a hardened box" items. Full detail is in
`/var/log/lynis-report.dat` and `/var/log/lynis.log` on the droplet itself
if any of them turn out to matter later — not reproduced here to avoid
padding this doc with boilerplate.

**Patching:** confirmed separately (`apt list --upgradable`) — **zero**
packages currently pending. Lynis's "found vulnerable packages" warning
isn't actionable right now; the box is fully current, `unattended-upgrades`
is doing its job.

## Summary for the new droplet (not yet actioned, just noting the target)

The new Ubuntu 26.04 LTS droplet should start from a materially different
baseline: a non-root admin account with key-only SSH, `PermitRootLogin no`,
`PasswordAuthentication no`, `fail2ban` (or at least UFW SSH rate-limiting),
and no orphaned sudoers entries. None of this has been done yet — this is a
findings document, not a remediation.
