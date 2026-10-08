# CLAUDE.md — web-sites project instructions

David's static-site properties (`taiji`, `comunidad`, `movement`, `play`,
`music`, `callejerez`, `spain`), rebuilt on Frozen-Flask and moving off
the legacy DigitalOcean droplet onto a new one. Rationale for the rules
below lives in `planning/housekeeping.md`; this file is the terse,
actionable version.

## Where things are

- `planning/` — pre-build discussion archive (architecture, aesthetics,
  target sites, roadmap, site-build checklist). Frozen: read it, don't
  add to it.
- `design/` — build-phase design docs, one topic per file, dated, with
  rationale. `tech-debt.md` holds known imperfections; each site's doc
  has a "parking lot" for not-now ideas.
- `legacy/` — review of the legacy droplet (inventory, DNS, nginx,
  certs, security findings).
- `docs/` — operational guides (e.g. `local-dev-testing.md`).
- `src/websites/<site>/` — thin per-site Flask app (`create_app()`,
  routes, `LOCALES`). `src/websites/common/` — shared i18n,
  Markdown/front-matter loading, freeze orchestration.
- `sites/<site>/` — `content/<locale>/*.md`, `templates/`, `static/`
  (versioned), `media/` (large, gitignored), `heirloom/` (raw legacy
  copy, gitignored), `build/` (frozen output, gitignored).
  `sites/_shared/` — `error-pages/` (404/50x) and `static/tokens.css`,
  copied into every build.
- `config/i18n/<site>/<locale>.toml` — short UI-string catalogs; `en-US`
  is the completeness floor.
- Sites that aren't content sites: `genuinemerit` and `davidstitt` (hub
  pages for the bare domains, sharing `sites/_shared/templates/hub.html`
  and `/shared/hub.css`) and `default` (the page for requests naming none
  of our hostnames). One-page bilingual apps built with
  `websites.common.single_page`.
- `ansible/vhosts.yml` — **every hostname the droplet serves**: canonical
  names, aliases, legacy redirects, locales, plus the `acme_staging`,
  `hsts_max_age` and `media_max_mb` switches. Domain rules:
  `design/domains.md`; certificates: `design/certificates.md`.
- `infra/tofu/`, `ansible/`, `tools/ops/` — droplet provisioning
  (OpenTofu), configuration (Ansible roles `base`, `nginx`, `sites`), and
  the scripts that drive them. `tools/ops/smoke_test.py` verifies a live
  deploy; `docs/cutover-runbook.md` is the switch-over procedure.
- `tools/dev/` — dev-host setup, checks, backup. `init-dev-host.sh` is
  the record of every apt install on `ubuvm`; add to it as packages are
  added.

Build order and phase status: `planning/roadmap.md`. Per-site build
steps: `planning/site-build-checklist.md`.

## Environment

- **Dev host `ubuvm`**: Ubuntu 26.04 LTS, server-only (no GUI), a
  libvirt guest on David's laptop **`wingchun`** (`192.168.122.173`).
  Builds are viewed from `wingchun` over an SSH port-forward into
  `ubuvm`'s nginx — see `docs/local-dev-testing.md`.
- **`sudo` on `ubuvm` needs David's password** — Claude can't run it.
  Write the script, David runs it (e.g. `init-dev-host.sh`,
  `setup-local-nginx.sh`). Never pipe `sudo a | sudo b`: both prompt
  at once on one terminal.
- **Python**: system `/usr/bin/python3` (>=3.14), single Poetry venv, no
  `pyenv` — a deliberate divergence from `sask`.
- **HTML validator**: `~/.local/bin/vnu`, installed/updated by
  `bash tools/dev/install-vnu.sh` (no sudo).
- **Legacy droplet**: `ssh genuinemerit` (root; `gmerit-nyc2`). Will be
  snapshotted and destroyed after cutover — nothing new may depend on it.
- **New droplet**: `web-sites-droplet`, `fra1`, 2GB/1vCPU/70GB, Ubuntu
  26.04, plus a reserved IP that survives `recreate-droplet.sh` but not
  `destroy.sh` (a full destroy releases it; the next provision gets a new
  one). SSH key `~/.ssh/ws_ed25519`, registered on DO as `ubuvm_ws` (ID
  `59722532`, outlives droplets). Alias `web-sites-droplet`, written by
  OpenTofu to `~/.ssh/config.d/ubuvm_ws`. As of 2026-10-02 the droplet
  **exists and is deployed** (runbook Stage 0 done; reserved IP
  `157.245.25.141`, no DNS pointed at it yet) — check `doctl` before
  assuming either way.
- **DigitalOcean API**: shares `sask`'s token at
  `~/.config/sask/infra.env` (`DIGITALOCEAN_TOKEN`). The `tools/ops/`
  scripts source it; for ad-hoc `doctl`, export it per command as
  `DIGITALOCEAN_ACCESS_TOKEN`. Never print the token.
- **GitHub**: public repo `genuinemerit/web-sites`, `gh` authenticated as
  `genuinemerit`. GitHub is an archive only — deploys go directly from
  `ubuvm`.
- **Git identity**: same as `sask` (`David` / `david.stitt@pm.me`), set
  locally in this repo.
- **SSH firewall vs. dynamic IP**: the droplet's firewall admits SSH only
  from this machine's public IP, and the ISP (DIGI) changes it without
  notice. `deploy.sh` self-heals via `check-ip-drift.sh --fix`, which
  applies a tofu plan only if it changes nothing but that firewall rule.
- **Gotchas seen before**: files in `~/.ssh/config.d/` must be mode
  `600` or OpenSSH rejects the whole Include (breaks SSH to *every*
  host). `ansible-playbook` here can hit a "blocking IO" error on piped
  output — redirect to a file instead.

## The `sask` sibling project

`../sask` (`/home/dave/code/sask`) is a *reference model* for tooling,
layout, and infra patterns — read it directly when a pattern is needed,
never from memory. **Never modify it from this project.** Where `sask`'s
approach has a weakness, fix it here rather than copy it (e.g. Ansible
`host_key_checking = False`, editing `sshd_config` instead of a
precedence-safe drop-in — both repaired in this repo's Ansible).

## Standing principles

- **Clean, robust, streamlined, secure** deployment — David's standing
  rule. Prefer fewer moving parts, verify effects (not just that a
  command ran), and no secrets on the droplet that it doesn't need.
- **No guessing.** Read the actual code/config/state before asserting
  anything. When cloud state and tool state may differ (e.g. `tofu`
  after a failed apply), check ground truth with `doctl`/`ssh` first.
- **Tooling values**: Python-first, no Node/npm toolchains, no PHP;
  durable, widely-maintained tools over novel ones.
- **MVP first** (`planning/site-build-checklist.md`): define the round's
  MVP before discussing big ideas; new ideas mid-work default to the
  site's parking lot, out loud, unless David pulls them in.
- **Pacing**: Phase 3 site builds go one deliberate step at a time;
  David leads the pace.
- **Translations** ship only after David reviews them.
- **Page titles** — hub and section titles and every content page's main
  title — use the shared `fit_title` macro (`sites/_shared/templates/
  macros.html`) and `.fit-title` (`tokens.css`); the layout only sets
  `--title-col`, its title column's width. Sized to fit the column,
  2–5.4rem (4.5rem on narrow screens), never broken mid-word. David's
  standing rule, 2026-10-08.
- Remove `.gitkeep` from any folder once it has real content (no need
  to ask).

## Before any build, push, or deploy

```bash
bash tools/dev/pre-build-check.sh
```

Every check must pass. In order: ruff lint + format, shellcheck,
pymarkdown (`README.md`, `CLAUDE.md`, `docs/` only), i18n completeness
(catalogs + content pages, all locales), the Frozen-Flask build of every
site, HTML/CSS validity (W3C vnu), internal links (including `/media/`),
WCAG AA colour contrast on every page's tokens in light and dark mode,
and the droplet's real nginx config served locally
(`tools/dev/test-nginx-local.sh`) and smoke-tested — every redirect,
header and certificate name in `ansible/vhosts.yml`. Not yet wired:
readability scoring (see `design/tech-debt.md`).

`tools/ops/deploy.sh` runs this script itself before publishing anything,
then `python3 tools/ops/smoke_test.py` checks the live result.

Colour tokens (`--text`, `--muted`, `--accent`, `--accent-hover`,
`--background`, `--surface`) must be literal hex values so the contrast
check can verify them.

## Human review

All generated code and config require David's review before they run.
Present files for inspection; never auto-run infrastructure or
destructive commands (droplet changes, DNS changes, deploys, anything on
the legacy droplet).

**Always pause and ask before `git commit`, and separately before `git
push`** — every time, even mid-task, even under a broad "go ahead" for
the surrounding work.

## Collaboration on design decisions

Surface design forks as explicit questions rather than deciding
unilaterally — especially URL structure, domains/DNS, certificates, site
architecture, and the shared style system. Record decisions in
`design/` with date and rationale.

## Review checkpoint per dev cycle

After each reasonably-sized chunk (a site build, a template/theme change,
a pipeline script), pause for David's review before the next chunk.
Design/aesthetics review against `planning/design-aesthetics.md`'s
"calm" brief is part of every cycle.

## Out of scope here

Auth/authn and other dynamic `.net` tooling get built in `sask` first and
imported later. Forms are `mailto:` only.
