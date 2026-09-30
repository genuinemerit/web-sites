# secrets/

This directory holds local credentials and environment-specific secrets.

**Git policy:** only `README.md` and `*.example` files are tracked. All
other contents are git-ignored. Never commit real credentials.

**This project shares `sask`'s secrets cache** rather than keeping a
separate one — confirmed 2026-09-30 (see `planning/architecture.md`'s
Secrets/credentials section). DigitalOcean API access uses
`~/.config/sask/infra.env` directly; there is no `web-sites`-specific
equivalent at this time. If that changes, add a `<name>.example` file
here as a template with placeholder values, matching `sask`'s convention.
