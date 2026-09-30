# Architecture, pipeline, and workflow

Confirmed 2026-09-30 across two rounds of discussion. Covers everything
except aesthetics/look-and-feel (its own file, `design-aesthetics.md` —
explicitly called out as deserving separate treatment) and build
order/sequencing (still open, deferred until this and the aesthetics
discussion settle).

## Site architecture — confirmed

**Frozen-Flask.** A real Flask app for local development (Jinja2
templates, shared macros/includes, `url_for`) that `freeze()`s to pure
static HTML for deployment — no Python process running in production.
Matches David's own framing ("Flask project with adjacent raw Jinja2
files") and avoids repeating the `mint` pattern (an orphaned, crashable
live service for a fundamentally static need).

**One Poetry project/venv for all sites** — single `pyproject.toml`, one
dependency set, all site "apps" underneath it in the single `web-sites`
repo. The natural home for a future site-scaffolding script once the
pattern is proven on 1-2 real sites (not built yet — don't build ahead of
having a working example).

**`.net`/dynamic tooling is an explicit, separate exception** — confirmed
aspirational, not part of the Frozen-Flask architecture. First real `.net`
content will itself be static (references/guides/changelogs — see
Docs below) or possibly analytics (see Analytics below) — actual
dynamic "admin/world editor" tooling is further out and hasn't started.

**Content authoring: Markdown, not hand-written HTML/Jinja2.** Confirmed
2026-09-30 — "everything is up for redesign... let's fix it" regarding the
legacy hand-written-HTML pattern. Content-heavy pages (the `sfp`-style
constitution/platform/handbook pattern, docs, guides) become Markdown
rendered through shared templates, not hand-authored markup per page.

**CSS:** plain, hand-authored, no build step. A small shared stylesheet of
CSS custom properties (color, spacing, type scale) that each site's own
CSS draws from, for visual family resemblance without a framework. Overall
look-and-feel approach is its own discussion — see `design-aesthetics.md`.

## Build-output path convention — confirmed 2026-09-30

`sites/<site>/build/` — Frozen-Flask's generated output for each site
lands here. Already anticipated in `.gitignore` from the first commit
(`sites/*/build/`), now made explicit rather than just implied. Same
per-site-nested shape as `heirloom/`/`static/`/`media/` — logical (one
more sibling folder in an already-established pattern), robust (no
shared/global build directory for sites to collide in), and extendable
(a new site automatically gets the same shape with zero extra
convention-inventing). Both the eventual Flask app's `freeze()` config
and the local nginx dev vhosts (see below) point here.

## Dev environment (`ubuvm`) — confirmed

Already Ubuntu 26.04 LTS, matching the droplet target. Add local nginx
serving the frozen static output through the same vhost-per-site pattern
used in prod, so real nginx/redirect behavior gets caught before deploy —
not relying on Flask's dev server alone. Deliberately NOT replicating
Let's Encrypt or UFW/fail2ban locally (plain HTTP on localhost is fine for
dev) — matches David's "mimic without going too nuts" framing. Python
version pinned via `pyenv`, mirroring `sask`'s own pattern, for
consistency across David's projects (not strictly required, just
convenient/familiar). *(Superseded above: this project ended up using
system Python 3.14 directly, no `pyenv` — see the confirmed decision
earlier in this doc.)*

**Local nginx vhosts — scaffolded 2026-09-30, not yet enabled.**
`tools/dev/nginx-site.conf.template` + `tools/dev/setup-local-nginx.sh`
generate and enable one vhost per site, server-name-based
(`<site>.web-sites.test` → `127.0.0.1`, `.test` per RFC 2606 rather than
`.local`, which mDNS/Avahi can intercept) rather than port-based, to
mirror prod's actual domain-routing behavior. Idempotent and
extendable — the site list lives as one array at the top of the script;
adding a new property later is a one-line addition. Needs `sudo`
(writes `/etc/nginx/`, `/etc/hosts`), so David runs it directly, same as
`init-dev-host.sh`. **Run and verified 2026-09-30** (full detail, including a mid-run script
bug fix, in `roadmap.md`) — all 7 vhosts live, `/etc/hosts` entries in
place, nginx active, confirmed 404 on a test `curl` (correct — nginx is
wired up end-to-end, there's just no Frozen-Flask build output yet for
any site).

## Deploy/ops tooling — confirmed, adapted from `sask`

Clone-and-adapt from `sask`'s existing, working DO tooling:
`sask/infra/tofu/` (OpenTofu provisioning), `sask/ansible/` (config),
`tools/ops/{provision,destroy,recreate-droplet,check-ip-drift}.sh`.

**Key adaptation point:** `sask` deploys one app; `web-sites` deploys N
independent static sites behind one nginx. Two distinct operations, not
one:

- **One-off content change** — rsync freshly-frozen static output for a
  single site.
- **New site bring-up** — new nginx vhost + cert issuance (certbot) + DNS
  record creation. Since DO API access (`doctl`, via `sask`'s existing
  token) is already proven working this session, this script can create
  the DNS CNAME automatically too — directly serving the "repeatable
  workflow for new sites" project goal.

**Hardening role built from `legacy/security-review.md`'s findings**:
non-root admin account, `PermitRootLogin no`, `PasswordAuthentication no`,
`fail2ban`, `server_tokens off`, loopback-only mail — the review
essentially already wrote this role's checklist.

## Testing — confirmed, deliberately light

- HTML validator + internal link checker (no 404s) — highest value,
  lowest effort, especially given real link-hygiene issues already found
  in the legacy content (duplicate `cool_scripts.html`, etc.).
- Frozen-Flask's build step is itself a free smoke test — fails if a
  template errors.
- Post-deploy: a small curl-based script (expected 200s, `.com`→`.org`
  redirects correct, valid TLS) — same shape as `sask`'s existing
  `verify-do-secrets.sh`, worth reusing that pattern directly.
- No pytest suite/coverage gates for the static sites. Normal Flask-app
  testing conventions would apply if/when the `.net` dynamic tooling
  becomes real — not now.

**Aesthetics/design QA — confirmed 2026-09-30, see also
`design-aesthetics.md`.** David wants aesthetics treated as a **recurring
review/approve checkpoint every dev cycle**, not a one-time sign-off — and
asked specifically what's automatable vs. what needs manual eyes. Answer,
by category:

- **Automatable, pure Python, worth adding from the start:** a small
  custom **color-contrast checker** reading the shared CSS custom-
  properties file directly and flagging any foreground/background pair
  that fails WCAG AA — cheap to write given the color system is already
  centralized there. **Readability scoring** (`textstat` or similar,
  Flesch-Kincaid etc.) over the Markdown content — also cheap, pure
  Python. Both fold naturally into the same lint pass as the HTML
  validator/link checker above.
- **Automatable but heavier, optional/later:** real accessibility
  auditing (contrast is only one piece — also semantic structure, ARIA,
  focus order) needs something like `axe-core`, which is a JS library —
  the way to use it without pulling Node into the build pipeline is via
  Playwright's **Python** package (drives a real browser, injects
  `axe-core` for the check, no npm/Node toolchain required for the site
  itself). Worth adding once there's real content to audit, not needed
  for initial scaffolding.
- **Not automatable, stays manual:** actual visual/aesthetic judgment —
  "does this look good," color choices as a *design* decision rather than
  a contrast-ratio pass/fail, overall composition. This is the
  recurring human review/approve step David wants — the automated checks
  above are a floor (catch objectively bad outcomes), not a substitute for
  it.

## Image/sound optimization — confirmed requirement, not yet designed

David is actively building skills here and wants automated resizing/
compression for both images and audio/video worked into the pipeline,
plus a settled small set of standard formats/thresholds. **Existing
precedent worth adapting**: `sask/tools/studio/build_assets.py` already
does exactly this shape of thing — generates hashed WebP variants at
multiple resolution tiers (1920x1080/960x540/480x270/thumb), enforces a
size budget (≤1MiB/file), maintains aspect ratio. Not copied, just a
concrete reference point. Formats/thresholds/tooling choice still open —
David's own area of active interest, not something to prescribe for him.

## Internationalization — confirmed required from the start, model proposed

David: "definitely want localization baked in from the start... should
apply to all of my sites, even if at present they are English only... the
`sask` project provides a reasonable model to follow."

Read `sask`'s actual implementation rather than working from memory
(DD-0022, `src/sask/i18n/`, `config/i18n/*.toml`,
`tools/dev/build_i18n_pages.py`) to ground this properly:

- **Two content shapes, two mechanisms.** Short UI strings (nav labels,
  buttons) resolve via **tag substitution** against a shared **TOML
  catalog** (`config/i18n/en-US.toml`, `es-ES.toml`, one `[tags]` table
  each, e.g. `"nav.pulse" = "Pulse"`). Long-form prose (help pages, and by
  extension this project's content pages) uses **parallel per-locale
  documents**, not sentence-by-sentence tag substitution.
- **`en-US` is the completeness floor** — every tag any other locale uses
  must exist there first, enforced at load time. Missing translations
  degrade gracefully rather than crash.
- **Translation review discipline worth carrying over directly**:
  `sask` never ships unreviewed translated prose. Its `es-ES` build writes
  to an intermediate `.drafts/` file first — tag-substituted, but the
  surrounding prose still needs human (or human-reviewed LLM) translation
  before promotion to the actually-served file. Good practice to keep for
  `web-sites` too, especially for public-facing content on `spain`/
  `comunidad` where translation quality actually matters to the audience.

**Adapting to Frozen-Flask (the real design fork):** `sask` localizes at
request time (a live app resolves locale per-request via `SASK_LOCALE`/
`--lang`). `web-sites` has no live request cycle — freezing happens at
build time. The natural adaptation: **freeze once per locale**, each pass
binding the corresponding TOML catalog and writing to a locale-specific
output path.

**URL scheme — confirmed 2026-09-30:** path prefix, `/en/...`/`/es/...`.
No locale-specific path *variations* (same path shape under each prefix,
just different prefix — not translated URL slugs). **Locale list must be
config-driven, not hardcoded to two** — David expects `/fr/` to likely
follow later, so the freeze-per-locale loop and the switcher should both
read from a locale list rather than assuming exactly `en`/`es`.

**Language switcher — revised per the aesthetics design brief
(`design-aesthetics.md`), superseding the original "flags and/or names"
framing:** label each option in its own language's own name
("Español"/"English"), not flags — languages aren't countries, flags
don't map cleanly to languages (this is real accessibility/i18n practice,
not a style call). Also: every locale build must set `<html lang="es">`/
`lang="en"` correctly (screen readers and translation tools depend on
it), and layouts must tolerate Spanish text running ~20-30% longer than
English — no fixed-width buttons/nav items.

## Content organization, front-matter, and the doc-tooling split — confirmed 2026-09-30

**What front-matter is**, since David asked directly: a small block of
structured metadata at the top of a Markdown file, delimited by `---`
lines, e.g.:

```markdown
---
title: "Welcome to Spain"
date: 2026-10-01
locale: en
tags: [travel, culture]
---

Actual page content starts here...
```

It's the standard convention across nearly every static-site tool (Jekyll
popularized it; Hugo/Pelican/Eleventy all use it) for attaching
per-page metadata a build script can read programmatically — populating
`<title>`, sorting by date, filtering by locale/tag — without that
metadata showing up as visible page text. For this project: parse it with
`python-frontmatter` (small, pure-Python, does exactly this one job),
render the Markdown body with a library like `markdown` or `mistune`, and
hand both to the Jinja2 template as context.

**Separate dirs for source `.md` vs. generated HTML — yes, confirmed.**
Source content lives under something like `content/` (versioned in git);
Frozen-Flask's output is a *generated artifact*, never hand-edited, never
committed as the thing being edited (mirrors `sask`'s own "page-is-code"
discipline — source generates output, output must match a fresh
regeneration, not diverge from it).

**Three different tools, three different jobs — not competing, David's
question conflated them a bit:**

- **A Markdown-rendering library** (`markdown`/`mistune`) — parses site
  *content* `.md` files into HTML fragments, called from inside the
  Frozen-Flask app itself, feeding into Jinja2 templates. This is what
  actually builds `spain.html`, `callejerez.html`, etc.
- **`pandoc`** — for the separate docs/guides/changelog pipeline (local
  `.md` → standalone HTML, possibly deployed under `.net`) discussed
  earlier. Not part of site-content rendering; pandoc has no Jinja2/
  template integration, it converts whole documents.
- **`glow`** — a terminal Markdown previewer (mentioned favorably in
  `sask`'s own devlog for its CLI help output). Purely a personal
  authoring convenience — "view this `.md` file nicely while I'm writing
  it" — has nothing to do with the build pipeline at all.

## Project tree — align with `sask`'s naming/structure, added 2026-09-30

David: "in general, follow the project tree naming and structure of the
`sask` project." Applying where it's unambiguous; one genuine open
question flagged rather than guessed.

**Adopting directly, matches `sask` exactly:**

- `tools/dev/` and `tools/ops/` — same split already planned (dev-host
  bootstrap + checks vs. deploy/infra operations).
- `tools/dev/init-dev-host.sh` — same filename, same purpose (see Dev
  environment section above).
- `config/` — for the i18n TOML catalogs (`config/i18n/en-US.toml`,
  `es-ES.toml`, etc.), same path shape as `sask`'s.
- `secrets/` — a `secrets/README.md` (+ maybe an `infra.env.example`)
  documenting that this project shares `sask`'s actual secrets cache
  (`~/.config/sask/infra.env`, already confirmed) — mirrors `sask`'s own
  `secrets/README.md` + `.example` pattern even though the real secret
  lives in `sask`'s file, not a `web-sites`-specific one.
- `docs/` — the local-Markdown-+-pandoc guides/references/changelog
  content already planned gets this name, matching `sask`'s `docs/`.
- `infra/` — OpenTofu config lives here (`infra/tofu/`), matching
  `sask`'s `infra/tofu/` exactly.
- `src/` — a shared Python package (Jinja2 macro helpers, the
  frontmatter/Markdown rendering wrapper, the i18n catalog loader, the
  freeze-per-locale orchestration) lives here, analogous to `src/sask/`,
  even though `web-sites` has no single "engine" the way `sask` does.

**Deliberately NOT changing** (already-settled, different in kind, not
an oversight):

- `sites/<site>/static/` + `sites/<site>/media/` — `sask` has one global
  `assets/` because it's one app; `web-sites` has seven independent
  sites, which is why the per-site split exists at all. Keeping this as
  designed.

**Resolved 2026-09-30 — not a rename, a new sibling folder.** `planning/`
stays exactly as-is (the pre-build discussion archive — architecture,
aesthetics, target-site vision, roadmap, housekeeping, all already
populated, no files moved). A new `design/` folder is where *build-phase*
design docs land going forward, now that actual building has started —
same plain-markdown convention, no TOML schema, per `design/README.md`.

## Media path convention — refined 2026-09-30

David's proposal: keep media inside the project tree, split into a
`.gitignore`d "big" directory and a versioned "small" one (`/media` +
`/bigmedia`), open to suggestions on the split itself.

**Claude's refinement, for reaction:**

- **Naming swap** — call the versioned, small, code-adjacent stuff
  `static/` (favicons, icons, small UI-chrome images — genuinely small
  enough that git handles it fine) and the large, un-versioned stuff
  `media/` (photos/video/audio — gitignored). Matches what "media"
  intuitively means, rather than `bigmedia` reading as an afterthought.
- **Per-site nesting, not one shared top-level split** — `sites/<site>/
  static/` and `sites/<site>/media/` rather than one flat `static/`/
  `media/` covering every property. Keeps each site fully self-contained
  (matches the "new site = copy a template folder" workflow goal from
  early in this project) and makes per-site rsync trivial.
- **Two separate concerns, worth keeping distinct**: where source files
  live in the dev tree (the question David asked) vs. what URL path the
  *deployed* site serves them at. The served URL path can and should stay
  simple and consistent (e.g. always `/media/...` on every site) even
  though the naming/nesting above is about the authoring-side tree, not
  the runtime URL.

**Confirmed 2026-09-30** — naming swap and per-site nesting both agreed
as proposed.

## Secrets/credentials — confirmed 2026-09-30

Share `sask`'s existing secrets cache (`~/.config/sask/infra.env`) rather
than creating a separate `web-sites`-specific one, for now. Same rules
apply: never displayed, never versioned, lives outside the project tree.
Resolves `open-questions.md` item 4.

## Pico.css evaluation — confirmed 2026-09-30

Fold hands-on evaluation into building the first real site, rather than a
separate throwaway demo page first. Resolves `open-questions.md` item 6.

## Auth/authn — confirmed: build in `sask`, import here later

David: any future forms/contact beyond `mailto:`, and any auth/authz need
(mainly relevant once the `.net` admin/editor tooling becomes real) will
be developed inside the `sask` project first and imported into
`web-sites` as/when needed — not built independently here. Keeps
`web-sites` from duplicating infrastructure `sask` will own.

## Docs — confirmed: local Markdown + pandoc, not GitHub wiki

Reasoning already agreed: wiki is a separate git history, invisible to PR
review, cuts against the doc-in-repo pattern `sask` already uses. First
`.net` content is likely to be exactly this — references/guides/change
logs, rendered to static HTML via pandoc and possibly deployed. Whether
public deployment is actually wanted (vs. GitHub's native `.md` rendering
being sufficient) — flagged, not yet answered by David directly, but his
"first `.net` content" framing suggests deployment is intended.

## Analytics — confirmed desired, mechanism proposed not yet decided

David: "would love to have something... perhaps this is our real first
`.net` effort... simple, straightforward would be key." See discussion in
chat 2026-09-30 — GoAccess (reads existing nginx access logs directly, no
client-side JS/tracking, no server process to maintain) proposed as the
lean starting option, consistent with avoiding another `mint`-style
orphanable live service. Not yet confirmed by David.

## Design-decision record — confirmed

Continue the pattern already used throughout this project's own planning
docs: a `web-sites/planning/` folder, one short markdown file per topic,
each dated with a plain rationale — no TOML schema, no validator script
(explicitly lighter than `sask`'s dd/req/spec system, per David's
request).

## Backup/rollback — corrected 2026-09-30

**Correction:** the working repo actually lives on `ubuvm` itself, not in
a Dropbox-synced folder (David mis-spoke earlier). He wants a way to also
get it into Dropbox without installing the Dropbox client/sync daemon
directly on `ubuvm` (avoids background-process complexity and
sync lag on the dev VM) — leaning toward an **occasional `rsync` over SSH
from `ubuvm` to his laptop**, where Dropbox is already installed and
syncing, rather than a continuous VM-side sync.

**Claude's recommendation:** `rsync` (not `scp`) — incremental, only
transfers changed files, safe to re-run. Set up passwordless SSH from
`ubuvm` to the laptop the same way `ssh genuinemerit` was set up for the
droplet (a named alias, key-based). Keep it a **manual, deliberate
script** (e.g. `tools/backup-to-laptop.sh`), not a cron job — a scheduled
background job on the VM reintroduces exactly the kind of unattended
sync complexity David is trying to avoid by not running the Dropbox
daemon here. Natural cadence: run it at the same "significant build"
moments that already trigger a GitHub push, rather than inventing a
separate schedule. **Confirmed 2026-09-30: design/build of this script is
in scope for the initial scaffolding build-out**, not a later add-on.

Otherwise as before: push to GitHub after significant builds only, no PR
process, no dev/main/fix branch discipline — consistent with
[[user-solo-hobbyist-workflow]]. OpenTofu/Ansible destroy-and-rebuild
still covers infra rollback.

## Still open

See `open-questions.md` for the consolidated, current list across
architecture, aesthetics, and everything else — kept in one place rather
than scattered per-file "still open" sections like this one used to be.
