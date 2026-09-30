# Roadmap / build order

David's proposal, 2026-09-30, given as `open-questions.md` item 7's
answer — recorded here as its own doc since it's the culmination of all
the preceding design discussion. Explicitly invited feedback.

## Phase 1 — scaffolding (David's A1, expanded into concrete tasks 2026-09-30)

`ubuvm` storage: **done** (392G total, 362G available — see below, no
longer a constraint on anything in this phase).

### 1a. Repo skeleton

- `git init` in `/home/dave/code/web-sites` (not yet a repo).
- **Git identity — confirmed 2026-09-30: same as `sask`** (`David` /
  `david.stitt@pm.me`).
- Install `gh` CLI first (not currently on `ubuvm` — checked) — a single
  apt-installable Go binary, consistent with David's tooling preferences.
  Then create the GitHub repo (`web-sites`) via `gh repo create` —
  automated, per David's "ideally via automation."
- `.gitignore`: per-site `media/` dirs (large, un-versioned — see
  `architecture.md`), Frozen-Flask's generated output, Python/Poetry
  cruft, anything under `secrets/`-equivalent paths (secrets themselves
  live outside the tree per the confirmed convention, but belt-and-braces).

### 1b. Poetry/Python project

- `pyproject.toml`, single Poetry-managed venv for all sites (confirmed
  architecture).
- **Python version — confirmed 2026-09-30: latest, no `pyenv`.** David
  wants the newest available (3.15 expected soon; today that's 3.14) —
  checked `ubuvm`'s **system** `/usr/bin/python3` and it's already
  **3.14.4**, so this project uses the system interpreter directly rather
  than `sask`'s pyenv-pinned-3.12 approach (deliberate divergence, not an
  oversight — `sask` pins 3.12 specifically *to avoid* the system's 3.14;
  `web-sites` wants exactly that). `pyproject.toml`:
  `python = ">=3.14"`. Open item for later, not now: when 3.15 actually
  ships, whether it arrives via plain `apt upgrade` or needs a PPA/
  `pyenv` at that point isn't yet known — revisit then.
- Core deps: `flask`, `frozen-flask`, `python-frontmatter`, a Markdown
  renderer (`markdown` or `mistune`), `ruff` (lint/format, matches
  `sask`'s choice).
- Dev/check deps (feed `tools/dev/pre-build-check.sh`, see 1d): an HTML
  validator, `textstat` (readability). Link-checker and color-contrast
  checker are small enough to write in-house rather than pull a
  dependency for.

### 1c. Dev environment

- **Done 2026-09-30.** Local nginx on `ubuvm`, vhost-per-site pattern
  mirroring prod. `setup-local-nginx.sh` run successfully (after one
  fix — see below) and verified: all 7 vhosts in `sites-available`/
  `sites-enabled`, all 7 `/etc/hosts` entries present, nginx active,
  `curl http://taiji.web-sites.test/` returns `404` as expected (no
  build output yet, but the full DNS → nginx → filesystem chain is
  confirmed working). Full detail in `architecture.md`'s Dev environment
  section.
  - **Bug found and fixed mid-run**: the script originally piped two
    separate `sudo` calls together (`sudo sed ... | sudo tee ...`) —
    `sed` never needed `sudo` at all (just reading a file David owns).
    Bash starts both sides of a pipe concurrently, so this produced two
    overlapping password prompts on one terminal, which is what caused
    the "stuck," "asked twice," and "displayed in plain text" symptoms
    David hit. Fixed to a single `sudo` call per site. Separately, two
    genuinely-wrong password attempts also happened around the same
    time (confirmed via `/var/log/auth.log` — `unix_chkpwd: password
    check failed`, not a script artifact) — likely Caps Lock or a
    terminal-reconnect-related keyboard hiccup, resolved once he
    re-typed carefully. Checked `pam_faillock`/`pam_tally` first — not
    configured on `ubuvm`, so no lockout risk from the retries.
- No `.python-version` needed — this project uses system Python
  directly, no `pyenv` (see 1b above).
- **Environment/install tracking — added 2026-09-30, David's request.**
  Mirror `sask`'s `tools/dev/init-dev-host.sh` (dev-host bootstrap
  script: apt prereqs, etc. — safe to commit, no secrets) — same
  filename/location, not a differently-named equivalent, per the
  tree-structure note below. Every apt-install/setup step done on
  `ubuvm` for this project (nginx, `gh` CLI, anything else) gets added to
  this script as it happens, built up incrementally rather than written
  speculatively up front — so the dev-host setup is reproducible from a
  fresh Ubuntu host, same guarantee `sask`'s version provides.

### 1d. Pre-build/push/deploy check script

- `tools/dev/pre-build-check.sh` (referenced but not yet written in
  `web-sites/CLAUDE.md`). Some checks (ruff, shellcheck) can be wired up
  immediately; others (color-contrast, i18n completeness) depend on the
  CSS-variables file and locale catalog existing, which won't happen
  until the first real site (`taiji`) is built — fine to stub now and
  fill in as those pieces come online, not a blocker to starting.

### 1e. Laptop backup script

- **Tested end-to-end 2026-09-30 — done.** Dry-run previewed correctly
  (full tree, `.git/` excluded, `sites/*/media/` included per design),
  then a real run confirmed landing at `wingchun:/home/dave/Dropbox/
  Code/web_sites/` — verified directly on `wingchun` afterward (full
  tree present, `.git/` correctly absent).
- **Destination path confirmed 2026-09-30**: `/home/dave/Dropbox/Code/
  web_sites` on `wingchun` — set as `tools/dev/backup-to-laptop.sh`'s
  default `DEST`.

- SSH alias `ubuvm` → laptop (`wingchun` — David's laptop, name
  confirmed 2026-09-30; matches the `dave@wingchun` key already
  registered in the DO account, ID `59627849`, so the key side may
  already exist — David is checking whether the `ubuvm`→`wingchun` SSH
  path itself is actually set up and working). Then
  `tools/backup-to-laptop.sh` (`rsync`, manual/deliberate, not cron — see
  `architecture.md`'s Backup/rollback section, already confirmed in
  scope for this phase).
- **SSH confirmed working 2026-09-30** — David verified `ubuvm`→
  `wingchun` is set up. He's mid-reboot for a firmware upgrade when this
  was confirmed ("be right back") — execution starts once he's back and
  says go, not before, even though every decision in Phase 1 is now
  settled.

### 1f. New droplet create/destroy tooling

- Adapt `sask/infra/tofu/` (OpenTofu), `sask/ansible/`, and
  `sask/tools/ops/{provision,destroy,recreate-droplet,check-ip-drift}.sh`
  — per `architecture.md`'s Deploy/ops tooling section, split into
  one-off-content-sync vs. new-site-bring-up operations.
- Ansible hardening role built from `legacy/security-review.md`'s
  findings (non-root admin, `PermitRootLogin no`, `PasswordAuthentication
  no`, `fail2ban`, `server_tokens off`, loopback-only mail).
- **Droplet region/size — confirmed 2026-09-30**: same size as legacy
  (2GB/1vCPU/70GB), region **`fra1`** instead of `nyc2` (closer to
  David; he judged the difference otherwise immaterial). Incidental nice
  alignment: `sask-droplet` is also in `fra1` — both projects' droplets
  end up in the same DC, though that wasn't the deciding factor.
- **SSH key strategy — revised 2026-10-01: dedicated key, not reused.**
  The 2026-09-30 choice to reuse the `genuinemerit` key
  (`ubuvm_gm`/`gm_ed25519`) was reconsidered — generated a **new**
  keypair instead, `~/.ssh/ws_ed25519`, registered with DigitalOcean as
  **`ubuvm_ws`** (ID `59722532`, fingerprint
  `MD5:fa:11:67:04:a7:71:5b:20:64:20:06:fd:89:4f:7c:8d`, confirmed
  matching via `doctl compute ssh-key list`). SSH config alias file:
  `~/.ssh/config.d/ubuvm_ws`. Updated everywhere the old key was
  referenced: `infra/tofu/{variables,main}.tf`,
  `terraform.tfvars.example`, `README.md`, `ansible/group_vars/all.yml`.
  Re-ran `tofu validate` + a read-only `tofu plan` afterward — the new
  key's data-source lookup resolves correctly (plan showed a clean
  5-resources-to-add with no errors); nothing created yet.
- Initial pass: actually stand up and tear down a test droplet to prove
  the pipeline works end-to-end, before any real site content depends on
  it.
- **Drafted and validated 2026-10-01 — not yet applied to real
  infrastructure, awaiting David's review per `CLAUDE.md`'s human-review
  rule.** Read `sask`'s actual `infra/tofu/`, `ansible/`, and `tools/ops/`
  in full before adapting anything (not from memory/summary). Key
  findings and adaptations, not a blind copy:
  - **`sask` uses Caddy, not nginx** (fits its single-app-behind-a-
    reverse-proxy shape) — wrote a new `nginx` role instead, no Caddy
    equivalent needed.
  - **No live app service exists for `web-sites`** (Frozen-Flask means
    static output only) — dropped `sask`'s `app_user`/`app_group`/
    gunicorn/systemd-service machinery entirely from the `base` role;
    kept only genuine platform hardening (sshd config matching
    `legacy/security-review.md`'s findings exactly, `fail2ban`,
    unattended-upgrades, journald caps).
  - **SSH key looked up, not created** — `data "digitalocean_ssh_key"`
    referencing the already-registered `ubuvm_gm` (confirmed above),
    not `sask`'s pattern of registering a fresh key each time.
  - **Droplet size slug traced precisely**: `s-1vcpu-2gb-70gb-intel`,
    confirmed via `doctl compute droplet get gmerit-nyc2` against the
    real legacy droplet, not guessed from its RAM/disk numbers.
  - **Ubuntu image**: `ubuntu-26-04-x64`, confirmed available via
    `doctl compute image list-distribution`.
  - **nginx role hardening**: `server_tokens off` (confirmed the stock
    Ubuntu 26.04 nginx package really does ship `server_tokens build`
    by checking `ubuvm`'s own freshly-installed nginx, not assumed from
    the legacy droplet alone) + a baseline security-headers snippet
    (`X-Content-Type-Options`, `X-Frame-Options`,
    `Referrer-Policy`) included globally — addresses the exact gaps
    `legacy/nginx-review.md` found. No per-site vhosts yet — that's
    later, separate "new site bring-up" tooling once a real site build
    exists.
  - **DNS deliberately NOT wired up** — unlike `sask`'s `main.tf` (which
    creates a DNS record in the same `apply`), this config creates no
    DNS records at all. The production domains still point at the
    *legacy* droplet serving real live sites; pointing a domain at this
    new droplet is a separate, later, deliberately-reviewed step once
    an actual site (`taiji` first) is ready to go live. See
    `infra/tofu/README.md`.
  - **Validated, not yet run for real**: `tofu init -backend=false` +
    `tofu validate` — config is syntactically/internally valid.
    `ansible-playbook --syntax-check` on both `bootstrap.yml` and
    `site.yml` — both valid. None of this has touched DigitalOcean or
    created any real resource; `tofu apply`/`ansible-playbook` (the
    actual execution) awaits explicit review and go-ahead.

**Claude's feedback on the phase as a whole: sound, no structural changes
suggested.** Proving the infra skeleton (can we stand up and tear down a
droplet, repeatably) before any real site content is a good instinct — it
validates the riskiest, hardest-to-debug-later part first, while nothing
real is riding on it yet.

**Progress, 2026-09-30 afternoon:** 1a (repo skeleton, minus the actual
GitHub repo itself), 1b (Poetry project, all deps installed clean on
3.14), 1c (pre-build-check.sh's wired-up checks), and 1d (the check
script itself) are done — first commit made (`77a1bdd`). 1e
(backup-to-laptop.sh) is written, not yet run for real. Blocked on two
things, both needing David:

- **`nginx` and `gh` CLI — done 2026-09-30.** David ran the install
  himself (both available directly from Ubuntu's own repos, no custom
  GitHub apt repo needed — simplified `init-dev-host.sh` accordingly).
  Confirmed: `gh 2.46.0`, `nginx/1.28.3`.
- **GitHub repo — done 2026-09-30.** Public, created via `gh repo create`
  (`gh` authenticated as `genuinemerit`, SSH protocol). Live at
  https://github.com/genuinemerit/web-sites. `main` pushed (2 commits,
  `77a1bdd` + `f5073d1`), tracking set up. **1a is now fully complete.**

1f (OpenTofu/Ansible/new-droplet tooling) not started yet — genuinely the
biggest, highest-stakes remaining piece; per `CLAUDE.md`'s human-review
rule, any generated infra config gets presented before anything is
actually applied.

## Phase 2 — raw-material import (new, proposed by David 2026-09-30)

David's idea: right after scaffolding, create the `sites/<site>/`
container for all seven properties immediately (even though most are
empty until their own build turn), and move legacy resources into a
per-site bucket in each one — get all the "raw material" physically into
the dev tree before starting redesign work, rather than pulling it
piecemeal later. **Confirmed 2026-09-30: per-site nesting, explicitly not
a single shared top-level container** — matches the `static`/`media`
per-site pattern already agreed.

**Naming — changed 2026-09-30: `sites/<site>/heirloom/`, not
`sites/<site>/legacy/`.** David's call, specifically to avoid any
confusion with the existing top-level `web-sites/legacy/` (the droplet
*review* docs — inventory, decisions, security review, etc., already
populated) — different thing entirely (raw staged content vs. analysis
docs about the old droplet), and a different word removes the ambiguity
outright rather than relying on context to disambiguate.

**Claude's refinement — checked `ubuvm`'s disk space before agreeing to
"pull everything," and it doesn't fit as-is**: only **4.6GB free**
(19GB disk, 75% used already). The legacy content totals roughly **7.1GB**
(`music` 2.9G + `openmic` 2.3G + `taiji` 1.9G + `qigong`/`sfp` ~32M
combined) — mostly large media. Proposed split:

- **Pull ALL small/structural content now** (every site's HTML/CSS/docs —
  negligible total size) — gives full visibility into every site's actual
  text/markup/structure immediately, which is genuinely useful before any
  redesign work starts.
- **Pull large media lazily, per site, right before that site's own
  Phase 3 turn** — rather than all seven sites' media upfront. Naturally
  spreads disk usage over time in step with the build order below, and
  avoids hitting the space ceiling on day one. Also fits the earlier
  agreed plan to review media file-by-file (keep/archive/drop) rather
  than assume everything gets carried forward — no need to have media
  sitting on `ubuvm` for a site whose media review hasn't happened yet.

**Reconsidered given disk space is no longer tight, then confirmed
2026-09-30: keep the lazy per-site pull.** David's reasoning stands
independently of storage — he doesn't want to review all the big video
files right now (some will likely get dropped), so there's no benefit to
having unreviewed media sitting on `ubuvm` for sites whose turn hasn't
come up yet. Disk space was never the only reason for this design.

## Phase 3 — site build order (David's A2)

a. `taiji` → b. `spain` → c. `comunidad` → d. `movement` → e. `play` →
f. `music` → g. `callejerez`

**Claude's feedback:**

- **`taiji` first is the right call**, and for a good reason beyond
  "it's simple": it's also the one site with a real external stakeholder
  (Louise's class) depending on continuity, and content-wise it's the
  lowest-risk of the seven. Building the *entire* pipeline (Frozen-Flask,
  i18n scaffold, deploy tooling, DNS/redirect, TLS) against the safest
  content first, before anything unexpected happens, is sound risk
  management.
- **`spain` second exercises i18n on real content early** — good, since
  problems with the localization approach are cheaper to catch before
  five more sites are built on the same pattern.
- **One small heads-up, not a reordering suggestion**: `callejerez`'s
  source content lives in the legacy `music/videos/` folder, but `music`
  itself gets rebuilt 6th, one step *before* `callejerez` (7th, last).
  That's fine — rebuilding `music` doesn't require `callejerez`'s site to
  already exist, it just means the Calle Jerez material needs to be set
  aside somewhere (not simply left out and lost) when `music` gets
  rebuilt, pending `callejerez`'s own turn. Worth keeping in mind when you
  get to `music`, not a problem with the order itself.
- Otherwise no changes suggested — the ordering reads as "public/
  dependency-bearing first, private/lowest-pressure last," which is a
  sensible principle to sequence by.

## Phase 4 — destroy legacy droplet (David's A3)

**Confirmed 2026-09-30: no rush.** David agreed with the suggested final
snapshot + soak-period approach — destruction happens once everything's
verified on the new droplet and there's no pressure to rush the legacy
box's teardown.

## Open

Reaction to the Phase 2 refinement (small content now, media lazily per
site) — everything else in this roadmap is now confirmed. David is
reviewing `open-questions.md` again and hopes to close it out before a
break (lunch/gym/siesta).
