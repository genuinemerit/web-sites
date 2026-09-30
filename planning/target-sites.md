# Target site vision

Started from David's notes appended to `legacy/content-inventory.md`
2026-09-30, refined through discussion the same day. This is now largely
confirmed for site *shape and naming*; domain/URL assignment and build
order are explicitly deferred (see below).

## Confirmed target properties

| Site | Status | Notes |
|---|---|---|
| `taiji` | **Fully standalone** (content/design), treated like the other `genuinemerit` sites for domain purposes | Used by a friend (Louise) who teaches a taiji class — David deliberately does NOT want it mixed into any other property. May get a link *from* `movement`, but stays independent otherwise. **Confirmed 2026-09-30:** subject to the *same* redesign protocols as every other site (Frozen-Flask, Markdown content, the whole pipeline) — the only hard constraint is that the current URL must keep working. Domain: `taiji.genuinemerit.org` becomes canonical, `taiji.genuinemerit.com` redirects there (same pattern as `spain`/`play`/`comunidad`) — a proper path-preserving 301 keeps existing bookmarks/printed links working; `.com` still needs its own valid TLS cert to serve the redirect. David will give Louise a heads-up. |
| `movement` | New | Health/exercise property. Replaces the earlier "fold qigong into a health site" idea — confirmed `taiji` is NOT part of this, despite the topical overlap. Source content: `qigong`. |
| `spain` | New | Public-facing, general. Absorbs `music/spain/` and `music/merida/` (school-project, Spanish-language-and-culture content). |
| `callejerez` | New | Private-facing, more particular/personal. Absorbs the Calle Jerez content currently in `music/videos/`. |
| `play` | New (renamed from `games` 2026-09-30) | Absorbs `sfp`. **Not related to `sask`/Saskan Lands** — `sfp` is David's *eRepublik* (an online browser game) player-group/"party," entirely separate from the "Enclosures" novel and its `sask`/`saskan` world. The old `saskan/` asset folder under `sfp` (now deleted) was there opportunistically, not because of any real content connection. |
| `music` | Redesigned, name unchanged | Stays music-focused — David's own work + resources. Keeps `music/sounds/` (the ~35 audio/video files) once `spain`/`callejerez` content is split out. |
| `comunidad` | New (confirmed 2026-09-30) | Community property, replaces `openmic`. Absorbs legacy Sandwich, MA Open Mic material + the Intercambio de Idiomas Inglés-Español (Alcalá de Henares) + future community projects. |

## Repo shape — effectively decided

**Single GitHub repo, `web-sites`**, covering all properties, used as a
simple archive (not a CI/CD trigger) — large media files handled
separately from the repo. This directly answers the long-open "one repo
vs. per-site" question from earlier in the project. *(The "mechanism
TBD" note this section used to have is stale — resolved in
`architecture.md`'s Backup/rollback section: media stays un-versioned,
not in git at all, covered by the Dropbox backup instead.)*

## Deploy approach — confirmed

Direct deploy from this local VM to the droplet, the same pattern David
already uses for `sask` — not a GitHub Actions-triggered pipeline. GitHub
is purely source-of-record/archive.

## Domain assignment — confirmed 2026-09-30

Two-group split, by domain "family":

- **`davidstitt.net`** (+ subdomains) — personal/private/experimental.
  Covers `music`, `callejerez`, `movement`.
- **`genuinemerit.{org,com,net}`** (+ subdomains) — public-facing. Covers
  `taiji`, `spain`, `play`, `comunidad`.
  - `.org` is the **primary front-end** for all four.
  - `.com` is kept (auto-renews) but simply **redirects** to the `.org`
    site for each — see open question below re: `taiji`.
  - `.net` is reserved for **admin/"world editor" functions** (tools that
    let a user modify, monitor, or administer one of the other sites) —
    likely mainly under `play`, possibly others. Not an immediate build
    need, just a namespace reservation for later.

**`genuinemerit.info`'s fate is now fully resolved:** auto-renew was
cancelled first, then **2026-10-01, David actively deleted the domain
and all its records from the DO account** rather than waiting out the
Nov 7 natural expiry. Resolves the long-open question from
`legacy/domain-audit.md`/`decisions.md` completely — it's no longer part
of the account at all.

**All other domains** (`davidstitt.net`, `genuinemerit.com/.org/.net`)
are set to auto-renew — no lapse risk to plan around.

**Out of scope, noted for context only:** David has reserved
`saskan.net`/`saskan.org` (not yet on DO nameservers) and will "very
likely" move the `sask` app there — but explicitly as part of the `sask`
project, not this one.

## Open questions

1. Build order/sequencing — not yet discussed; David wants pipeline/
   tooling design (next) to inform this, plus the security-findings
   review, before deciding.

## Resolved (site shape/naming/repo/deploy — no longer open)

- Health/exercise scope: `taiji` excluded, confirmed standalone.
- Music split: two new sites (`spain`, `callejerez`), not one.
- Naming: `movement`, `spain`, `callejerez`, `play` (renamed from `games`
  2026-09-30), `comunidad` confirmed; `music` keeps its name.
- `comunidad` (replaces `openmic`): confirmed, absorbs legacy Sandwich, MA
  Open Mic material + Intercambio de Idiomas (Alcalá de Henares) + future
  community projects.
- Deploy/pipeline approach: confirmed direct-VM-deploy, GitHub-as-archive.
- Repo shape: confirmed single repo, `web-sites`.
- **Large media: confirmed un-versioned.** Not put in git at all (no LFS,
  no object storage plan for now) — David already backs everything up to
  Dropbox, so that serves as the media backup; git only holds site
  code/content, not the multi-GB media folders.
- **`taiji` shares the single `web-sites` repo** with everything else — no
  separate repo. Its "keep separate" requirement is about content/design
  independence, not repo/access separation.
- **`taiji` domain: treated the same as the other `genuinemerit` sites.**
  `taiji.genuinemerit.org` is canonical, `taiji.genuinemerit.com`
  path-preserving 301-redirects there — confirmed this fully supports
  existing users/bookmarks/printed links, no exception needed. David will
  notify Louise (runs the taiji class this site supports) of the change.

===

David's Notes on use of domain names

- use `play` instead of `games`

- I have reserved the rights to `saskan.net` and `saskan.org`, but have not yet set them up on the Digital Ocean nameserver. Will deal with that in the `sask` project, not here.

- I have cancelled auto-renew for genuinemerit.info (expires Nov. 7, 2026)

- All other domains are set to auto-renew.

- The general breakdown is that...

  - davidstitt.net, with appropriate sub-domains, will be useed for more personal and private and experimental works. These will include:  `music`, `callejerez` and `movement`

  - genuinemerit.xxx, with appropriate sub-domains, will be used for more public facing works. These will include: `taiji`, `spain`, `games` --> `play`, and `comunidad`
    - genuinemerit.org will be the primary front-end for all of these works
    - genuinemerit.com will be supported for all of them as well, but simply redirect to the .org sites
    - genuinemerit.net will be used only in cases, likely to be found mainly in the `play` realm, but possibly others, where "admin" or "world editor" types of functions are provided that allow the user to modify, monitor or otherwise administer one of the other sites.

- Very likely will go ahead and transfer the `sask` game to saskan.org and saskan.net, but not as part of this project.
