# CLAUDE.md — web-sites project instructions

Rationale and the mapping from `sask`'s housekeeping rules live in
`planning/housekeeping.md` — this file is the terse, actionable version,
same relationship `sask/CLAUDE.md` has to its own design docs.

## Environment (intended; not yet scaffolded)

- Dev host: **`ubuvm`**, Ubuntu 26.04 LTS (392G disk, 362G free).
- Single Poetry-managed venv for all sites in this repo (Frozen-Flask —
  see `planning/architecture.md`). Python: system `/usr/bin/python3`
  directly (`>=3.14`, currently 3.14.4) — **no `pyenv`**, unlike `sask`
  (which pins 3.12 specifically to avoid the system's 3.14). Deliberate:
  this project wants latest Python, `sask` deliberately doesn't.
- Deploy target: a new DigitalOcean droplet, Ubuntu 26.04 LTS, `fra1`,
  same size as the legacy box (2GB/1vCPU/70GB). SSH key: reuse
  `ubuvm_gm` (DO key ID `59687099`, local `~/.ssh/gm_ed25519`).

## Before any build, push, or deploy

Run the check script; every check must exit 0:

```bash
bash tools/dev/pre-build-check.sh
```

Currently wired up: ruff lint/format, shellcheck, pymarkdown. Still to be
added as their underlying pieces come online (see the script's own
comments):

- HTML validity
- Internal link check (no 404s)
- Color-contrast check (WCAG AA, against the shared CSS custom-properties
  file)
- Readability check
- i18n completeness (`en-US` is the floor — see `planning/
  architecture.md`'s Internationalization section)
- The Frozen-Flask build itself (fails on template errors — this is a
  real check, not just a build step)

## Design docs

`planning/` is the pre-build discussion archive (architecture,
aesthetics, target-site vision, roadmap, housekeeping) — already
populated, not where new entries go. **New design docs, written during
actual build work, go under `design/`** (see `design/README.md`). Same
format either way: plain markdown, one topic per file, dated, with
rationale. No TOML schema, no validator script — deliberately lighter
than `sask`'s dd/req/spec system, per David's explicit request.

## Human review

All generated code and config files require human review before
execution. Present files for inspection; do not auto-run infrastructure
or destructive commands (droplet changes, DNS changes, deploys).

## Collaboration on impactful design decisions

Surface architecture/design forks as explicit questions rather than
deciding unilaterally — especially anything touching URL structure,
domain/DNS, site architecture, or the shared component/theme system.

## Review checkpoint per dev cycle

After each reasonably-sized chunk of work (a site's initial build, a
template/theme change, a pipeline script), pause for David's review and
approval before moving on to the next chunk.

## Git identity

Same as `sask`: `David` / `david.stitt@pm.me`.

## `.net` dynamic tooling / auth

Out of scope for this repo's normal workflow. Any future auth/authn need
gets built inside the `sask` project and imported here — not developed
independently in `web-sites`.
