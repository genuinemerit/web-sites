# Site build checklist (template)

Started 2026-10-01, drafted while scoping `taiji`'s build — the first
real site, so this is also the first real test of whether our prior
planning actually holds together end-to-end. Meant to be reused for
every site thereafter (and eventually for David's stated goal of a
repeatable workflow for *new* sites too, e.g. a school project).

Organized around David's four aspects — development architecture,
hosting architecture, testing/ops, content — but sequenced as an actual
dependency-ordered flow, not four parallel buckets, since several steps
block later ones.

**Revised 2026-10-01** to add Phase B (Detailed design) — the first
draft jumped straight from "confirm scope" to "build it," with no named
place for the actual hands-on creative work (real color/font values, a
splash page or nav structure, drafted text) or for deciding whether a
structural element like a splash page is even in scope. David's own
question surfaced the gap; see that phase's intro for the full reasoning.

## MVP vs. big ideas — a standing discipline, added 2026-10-01

David's own ask, explicitly: he's prone to "big ideas" that are
genuinely good but never quite get finished, and wants active,
pragmatic pushback to keep each build round small and shippable rather
than quietly ballooning into a grand redesign. Mechanism, applied from
`taiji` onward:

- **Define the MVP before opening the floor to big ideas, not after.**
  Write the small, concrete "what we're actually building this round"
  list first (Phase A, step 1). Only then let ideas surface.
- **Two separate lists, not one** — they're different psychological
  categories. `design/tech-debt.md` is for known imperfections to
  eventually fix (bug-like). A **"Future ideas / parking lot" section in
  each site's own design doc** (e.g. `design/taiji.md`) is for exciting-
  but-not-now scope expansions (feature-like). Conflating them makes
  both less useful.
- **Default response to a new idea mid-work**: name it as parking-lot
  material out loud — "good idea, let's park that rather than fold it
  into this round" — rather than quietly going along with scope growth.
  David can always override and pull it into the current round
  explicitly; the point is the *default* is capture-don't-build, not
  silence.
- **Review cadence**: tied to an existing checkpoint rather than a new
  ritual — the start of each site's turn in the Phase 3 build order is
  a natural moment to ask whether anything parked is worth pulling in.

## Division of labor, added 2026-10-01

David's proposal, maps cleanly onto the Phase B/C split above:

- **David's domain**: Phase B's creative decisions — favicon design,
  error-page copy/imagery, investigating/doing manual media
  compression. May involve specialized AI tools (image generators/
  editors, etc.) outside this session entirely, not just manual work.
- **Claude's domain**: Phase C implementation — templates, i18n
  plumbing, Frozen-Flask wiring, the more obvious technical work, plus
  a first pass at tokenization and full-page translations. David
  reviews code and test results rather than writing the implementation
  himself.
- **Translation drafts specifically**: always reviewed before shipping,
  never auto-published — same discipline `sask`'s own i18n design
  already established (DD-0022's human-reviewed-draft step), just
  applied here for the first time.
- **Real but limited coupling, named honestly**: Claude can *start*
  Phase C with placeholders standing in for favicon/error-page content/
  compressed media — nothing blocks beginning the coding work. The
  truly finished build needs David's actual pieces, though — Claude
  flags explicitly if a placeholder genuinely can't stand in any
  longer, rather than guessing at creative content.
- **Handoff locations**: favicon → `sites/<site>/static/` (small,
  versioned); compressed media → `sites/<site>/media/` (large,
  gitignored, can replace or sit alongside `heirloom/` originals);
  error-page text/imagery → either told directly or edited straight
  into `sites/heirloom/404.html`/`50x.html`.
- **Checkpoints**: no new ceremony — the existing review-checkpoint
  rhythm (`CLAUDE.md`) already covers this; file-change notifications
  already surface either side's edits to the other automatically.
- **Expected to get refined as we actually do it** — David's own
  framing, recorded rather than treated as a final, fixed protocol.

## Phase A — Scope (per-site, before any detail work)

Deliberately abstract — this is where the MVP-vs-parking-lot discipline
above actually gets applied, before any real design/creative effort is
spent. Getting this phase's output too detailed defeats its purpose.

1. Confirm content scope/direction (audience, what the site is actually
   for) — e.g. `taiji`'s MVP-vs-parking-lot split in `design/taiji.md`.
2. Confirm locale requirements for this site (which languages now,
   which are plausible future candidates).
3. Confirm, at a checklist level only, which structural elements are
   even in scope this round (e.g. "is a splash page in scope?", "is a
   standard nav menu in scope?") — a yes/no scope call per element, not
   the actual design of that element. That happens in Phase B.

## Phase B — Detailed design (per-site, before implementation)

**Added 2026-10-01** — this phase was missing from the first draft, and
its absence was exactly the gap David's question surfaced: Phase A
decides *whether* something's in scope, but nothing named *where* the
actual hands-on creative work happens — the real favicon artwork, actual
color/font values (not just "apply the brief" in the abstract), page/
nav structure, and the real content text. This phase is that home.

4. **Information architecture**: what pages this site actually has
   (home/splash? others?), nav/menu structure and labels. For `taiji`
   specifically, right now, this is "basically what's already there" —
   but for a site built from scratch (`spain`, possibly), this is where
   that gets decided for the first time.
5. **Visual design, made concrete**: actual typography choice, actual
   accent color value(s), favicon artwork — applying the governing
   design brief's *principles* (`design-aesthetics.md`) to this site's
   *specifics*, not just citing the brief. Expect iteration — a color
   that reads fine in the abstract sometimes doesn't once it's actually
   rendered, which is fine; loop back here from Phase C (implementation)
   as needed rather than treating this as strictly one-way.
6. **Content drafting**: write/adapt the actual text, decide what
   becomes which front-matter field (title, date, tags, etc.) — real
   authoring work, not a mechanical format conversion. The mechanical
   Markdown conversion itself happens in Phase C once this is settled.
7. **Review checkpoint** before moving to implementation — same
   standing "pause for review" principle as everywhere else in this
   project, made an explicit, named step here specifically because
   detailed design is exactly where scope tends to quietly grow if it
   isn't checked before code gets written.

## Phase C — Implementation

8. Per-site Flask app code location/structure — **confirmed 2026-10-01**:
   `src/websites/<site>/` holds a thin `create_app()` factory + any
   genuinely site-specific routes; a new `src/websites/common/` (or
   `_shared/`) module holds everything reusable across sites — the i18n
   catalog loader, the Markdown/front-matter rendering helper, the
   freeze-per-locale orchestration — so each site's own code stays small
   and the shared mechanics live in exactly one place. Jinja2
   *templates* live under `sites/<site>/templates/` (a new sibling to
   `heirloom/static/media`), with a `sites/_shared/templates/` for the
   common base/macros — keeping the code/content split clean: `src/` is
   logic, `sites/` is content+templates+assets, matching the project's
   existing per-site-folder philosophy.
9. Per-site i18n catalog structure — **confirmed 2026-10-01**:
   `config/i18n/<site>/en-US.toml` + `es-ES.toml` per site (one level
   deeper than `sask`'s single-site `config/i18n/en-US.toml` pattern) —
   avoids tag-namespace collisions, keeps each site genuinely self-
   contained, and a new site just gets its own `config/i18n/<newsite>/`
   folder as a trivial copy-paste starting point.
10. Content → Markdown: the *mechanical* conversion of Phase B's drafted
    text into Markdown + front-matter files (per `architecture.md`'s
    front-matter section) — the authoring/decisions already happened in
    Phase B, this is just the format transformation.
11. Build Jinja2 templates implementing Phase B's information
    architecture: shared base/macros (nav, footer, language switcher) +
    this site's own skin (Phase B's concrete color/font/favicon choices).
12. Wire up Frozen-Flask: routes, freeze-per-locale loop reading the
    config-driven locale list, `<html lang>` set correctly per build.
13. Local verification over plain HTTP: point `tools/dev/
    setup-local-nginx.sh`'s vhost at this site's real `build/` output
    (it currently points at an empty placeholder) and check it in a
    browser at `<site>.web-sites.test`.
14. Run `tools/dev/pre-build-check.sh` — currently only lints the repo
    itself (ruff/shellcheck/pymarkdown); the HTML validator, link
    checker, color-contrast checker, readability checker, and i18n
    completeness check are all still unwired (`architecture.md`'s
    Testing section listed them as "add once the underlying pieces
    exist" — they now do, for the first time, with real content/
    templates/catalogs about to exist).

## Phase D — Hosting/infra architecture (remote)

15. Ensure the droplet exists (`tools/ops/provision.sh`) — currently
    torn down from the destroy.sh test, nothing is running.
16. Run `tools/ops/deploy.sh` for real — **to do, not an open decision**
    (confirmed 2026-10-01, will be resolved by actually implementing it,
    not pre-decided in the abstract). We proved `provision`/`recreate`/
    `destroy` against real DigitalOcean infrastructure, but never
    actually ran the Ansible layer (`base` + `nginx` roles) against a
    live droplet. Needs to happen and be verified before anything else
    in this phase.
17. The "new site bring-up" tooling — **to do, not an open decision**
    (same as above). `architecture.md` named this as a distinct,
    separate script from day one (new nginx vhost + certbot cert
    issuance + DNS record) but it's never been written. `taiji` is the
    first site that will actually need it — its design will be driven
    by how `taiji`'s bring-up actually goes, not decided ahead of time.
18. DNS cutover for `taiji.genuinemerit.org`/`.com` — the one site
    where this needs the most care (Louise's class depends on
    continuity; see `target-sites.md`'s redirect-pattern decision).
    Deliberately its own reviewed step, not bundled into anything else.
19. Verify over real HTTPS remotely (valid cert, correct redirect
    behavior `.com` → `.org`).

## Phase E — Testing / ops / monitoring / security (deliberately light)

20. Post-deploy smoke test — planned (`architecture.md`'s Testing
    section, modeled on `sask`'s `verify-do-secrets.sh` pattern) but
    not yet written. Checks: expected 200s, redirect correctness, valid
    TLS.
21. GoAccess analytics — confirmed desired (`architecture.md`), but
    where it lives and how it's reached hasn't been designed yet. Not
    blocking `taiji`'s launch, but worth a decision at some point soon
    rather than indefinitely deferred.
22. Security: covered once per droplet via the Ansible `base` role, not
    per-site — nothing additional needed here per-site.

## Phase F — Content refactoring (iterative, ongoing)

23. Design/aesthetics review checkpoint — the recurring per-dev-cycle
    checkpoint already confirmed in `design-aesthetics.md`, not a
    one-time gate. Also where a Phase B loop-back (design decision
    didn't survive contact with the real rendered page) would surface.
24. Backup (`tools/dev/backup-to-laptop.sh`) and commit/push, per the
    standing housekeeping rules — pause for review before each, same as
    always.

## Resolved (2026-10-01)

Items 8 and 9 (code/template location, i18n catalog structure)
confirmed as proposed — structural decisions, settled before any code
exists rather than left to drift. Items 16 and 17 were never actually
open decisions, just undone work — confirmed they'll be resolved by
doing them as part of `taiji`'s build, not pre-designed in the abstract.
