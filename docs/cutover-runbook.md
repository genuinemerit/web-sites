# Cutover runbook: taiji + bare domains onto the new droplet

Written 2026-10-02. Design behind it: `design/certificates.md`, `design/domains.md`. Every stage is reviewed and
run deliberately (CLAUDE.md, "Human review") — nothing here is automatic.

Legacy droplet IP: `162.243.111.56`. New droplet IP: whatever `tofu output -raw reserved_ip` prints after
provisioning (the old reserved IP was released by the last `destroy.sh`). Below, `NEW_IP` means that value.

For ad-hoc DNS commands, export the shared token for the shell session first (never print it):

```bash
export DIGITALOCEAN_ACCESS_TOKEN="$(grep -E '^(export )?DIGITALOCEAN_TOKEN=' ~/.config/sask/infra.env \
    | sed 's/^export //; s/^DIGITALOCEAN_TOKEN=//; s/^"//; s/"$//')"
doctl compute domain records list genuinemerit.com    # shows record IDs, needed for update/delete
```

## The quiet window

taiji's users are on US Eastern time. Switch at **22:00–05:00 New York**, which in Madrid is:

| Dates (2026) | Madrid |
| --- | --- |
| until Oct 24 | 04:00–11:00 |
| Oct 25 – Oct 31 (Europe has changed clocks, the US hasn't) | 03:00–10:00 |
| from Nov 1 | 04:00–11:00 |

Stages 1 and 4 change records that live sites depend on — do them in the window. Stages 0, 2 and 3 are
invisible to taiji's users and can run any time. David sends Louise a note beforehand.

## Stage 0 — droplet up, content published (any time)

1. `bash tools/ops/provision.sh` — note `NEW_IP`.
2. `ansible/vhosts.yml` has `acme_staging: true` (test certificates first).
3. `bash tools/ops/deploy.sh` — runs every pre-build check, hardens the droplet, publishes all content.
   Every site is reported "not live yet" (no DNS points here), which is expected.

**Known provider bug** (hit on both 2026-10-01 and 2026-10-02): `tofu apply` can fail with "Provider produced
inconsistent result after apply" on `digitalocean_reserved_ip`, after the droplet and firewall were created. The
reserved IP does exist — it just isn't recorded. Don't re-run blind (that creates a second IP). Instead:
`doctl compute reserved-ip list` to find the unassigned IP, then from `infra/tofu/` (with `infra.env` sourced)
`tofu import digitalocean_reserved_ip.web_sites <ip>`, then `bash tools/ops/provision.sh` again — it then only
adds the IP assignment and the SSH alias.

**Done 2026-10-02**: droplet `605595400`, reserved IP `157.245.25.141`. Deploy `failed=0`; verified root and
password logins refused, `sshd -T` hardened, nginx/fail2ban/certbot timer/unattended-upgrades active, only
22/80/443 listening, default page answering by IP (smoke test `--only default --resolve 157.245.25.141`).

## Stage 1 — pin the legacy names (in the window, no visible change)

Today `taiji`, `sandwichopenmic`, `qigong` (genuinemerit.com), `music` (davidstitt.net) and `sfp`
(genuinemerit.org) are CNAMEs to `@` — they follow wherever the bare domain points. Before any bare domain
moves, replace each with an A record to the legacy IP, so they stay on legacy:

```bash
doctl compute domain records delete genuinemerit.com <taiji-cname-id> --force
doctl compute domain records create genuinemerit.com --record-type A --record-name taiji \
    --record-data 162.243.111.56 --record-ttl 300
# same for sandwichopenmic, qigong (genuinemerit.com), music (davidstitt.net), sfp (genuinemerit.org)
```

Same IP either way, so nothing visible changes; the short TTL (300 s, was 43200) also prepares Stage 4. The
seconds between delete and create are why this is done in the window. Also:

- Lower the bare-domain A records' TTL to 300 (`genuinemerit.com`, `genuinemerit.org`, `davidstitt.net`).
- Add CAA records so only Let's Encrypt may issue for these domains:

```bash
for d in genuinemerit.com genuinemerit.org davidstitt.net; do
    doctl compute domain records create "$d" --record-type CAA --record-name @ \
        --record-data letsencrypt.org --record-tag issue --record-flags 0 --record-ttl 3600
done
```

Verify: `dig +short taiji.genuinemerit.com` still prints `162.243.111.56`; the taiji site still loads.

## Stage 2 — new names to the new droplet, staging certificates (any time)

The bare domains serve only a 404 / certificate error on legacy today, so moving them is an improvement.

1. Point `@` of `genuinemerit.com`, `genuinemerit.org`, `davidstitt.net` at `NEW_IP`
   (`doctl compute domain records update <domain> --record-id <id> --record-data NEW_IP`).
2. Create `taiji.genuinemerit.org` → `NEW_IP` (A, TTL 300).
3. On the legacy droplet, forward taiji's certificate challenge to the new droplet, so the new droplet can
   get `taiji.genuinemerit.com`'s certificate while that name still points at legacy. In
   `/etc/nginx/sites-available/taiji.conf`, replace the whole port-80 `server { ... }` block (the one with
   the certbot `if ($host = ...)`) with the block below, then `nginx -t && systemctl reload nginx`. The
   server-level `if` must go: it runs before any `location` is matched, so a location added beside it never
   fires. Keep a copy of the original block to restore in Stage 4.

   ```nginx
   server {
       listen 80;
       server_name taiji.genuinemerit.com;
       # TEMPORARY (cutover): Let's Encrypt follows this to the new droplet.
       location ^~ /.well-known/acme-challenge/ {
           return 302 http://taiji.genuinemerit.org$request_uri;
       }
       location / {
           return 301 https://$host$request_uri;
       }
   }
   ```

4. `bash tools/ops/deploy.sh` — all three sites should now get staging certificates and go live on the new
   droplet.
5. Verify:

```bash
python3 tools/ops/smoke_test.py --staging --only genuinemerit davidstitt default
python3 tools/ops/smoke_test.py --staging --only taiji --resolve NEW_IP   # taiji's .com still on legacy
```

## Stage 3 — production certificates (any time)

1. Set `acme_staging: false` in `ansible/vhosts.yml`; `bash tools/ops/deploy.sh` replaces the staging
   certificates with real ones (taiji's `.com` via the forward again).
2. Verify, now without `--staging`:

   ```bash
   python3 tools/ops/smoke_test.py --only genuinemerit davidstitt default
   python3 tools/ops/smoke_test.py --only taiji --resolve NEW_IP
   ```

3. Optional: browse it from `wingchun` before switching, by adding `NEW_IP taiji.genuinemerit.com` to
   `wingchun`'s `/etc/hosts` temporarily.

## Stage 4 — switch taiji (in the window)

1. Point `taiji.genuinemerit.com`'s A record at `NEW_IP`. With TTL 300, most visitors move within ~5 minutes.
   The new droplet already holds the real certificate, so there is no certificate gap.
2. After ~10 minutes: `python3 tools/ops/smoke_test.py --only taiji` (public DNS, no `--resolve`), and check
   `https://taiji.genuinemerit.com/taiji.html` in a browser.
3. Restore the original port-80 block on the legacy box (the forward is no longer needed).

**Rollback** (any time up to legacy teardown): point `taiji.genuinemerit.com` back at `162.243.111.56`;
legacy is untouched and still has its own valid certificate until 2026-12-11.

## Stage 5 — settle in (a few days later)

- Sign up for Red Sift Certificates Lite (free) and add `genuinemerit.com`, `genuinemerit.org`,
  `davidstitt.net`, `taiji.genuinemerit.com`, `taiji.genuinemerit.org` — the recurring expiry check.
- Turn on HSTS in steps: `hsts_max_age: 86400` and deploy; after a week or two without trouble, `31536000`.
- Raise the TTLs back to 3600 for records that are settled.

## Later: legacy teardown (roadmap Phase 4)

Not before `music` has moved (it stays on legacy until its own rebuild). Then: final snapshot of
`gmerit-nyc2`, delete the DNS records of the retired names (`sandwichopenmic`, `qigong`, `sfp`) and the
`genuinemerit.net` A record (unresolved, per `design/domains.md`), destroy the droplet.
