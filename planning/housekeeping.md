# Housekeeping rules — adapted from `sask`, relaxed

David asked 2026-09-30 to carry over `sask`'s housekeeping discipline
here, "pretty much the same, but may be able to relax it a bit." Read
`sask`'s actual current rules directly (`sask/CLAUDE.md` +
`sask/tools/dev/pre-commit-check.sh`) rather than from memory — the real
script has more in it than `CLAUDE.md`'s own prose summary mentions
(`validate_i18n`, `check_page_staleness`, `check_api_reference_staleness`
aren't described in the doc text, only in the script itself).

The actionable version of this lives in `web-sites/CLAUDE.md` — this file
is the rationale/mapping record, not duplicated instruction text.

## What `sask` actually does

- **Pre-commit script**, every check must exit 0 before staging: `ruff`
  lint+format, `shellcheck`, `pymarkdown` (docs linting), design-spec
  TOML validation + its own pytest suite, i18n completeness validation
  (permissive at commit time — missing non-base translations only warn;
  strict mode is deploy-time only), and two "page-is-code" staleness
  checks (rendered docs/API-reference must match a fresh regeneration
  from source, hard-fail if stale).
- **Human review**: all generated code/config requires human review
  before execution; Claude presents for inspection rather than
  auto-running infrastructure or destructive commands; `[manual]` spec
  steps are David's alone.
- **Design-decision discipline** (from prior work in this project, not
  restated in `CLAUDE.md` itself): structured TOML dd/req/spec docs with
  acceptance criteria and rejected-alternatives, explicit UAT/acceptance
  testing per feature (often including live-droplet verification) before
  a decision gets marked accepted — David flips that status himself, not
  Claude.
- **Technical debt tracking**: `design/debt/tech-debt.toml`, consciously
  deferred work, reviewed near the end of each dev iteration.

## What's relaxed here, and why

| `sask` | `web-sites` | Why relaxed |
|---|---|---|
| TOML dd/req/spec schema, validator script | Plain markdown files in `planning/`, one topic per file, dated | Already agreed earlier (`architecture.md`) — David explicitly asked for something lighter than `sask`'s system. |
| pytest suite + coverage config | No pytest/coverage gates for the static sites | Already agreed — static content doesn't carry the same correctness-risk profile as `sask`'s engine code. Would apply once/if the `.net` dynamic tooling becomes real. |
| Formal per-spec UAT with numbered test cases (`TC-xxx`) | Informal review/approve checkpoint after each reasonably-sized chunk of work | Same underlying principle (nothing ships without David's eyes on it), less ceremony around documenting the check itself. |
| `pymarkdown`/`ruff`/`shellcheck` as a hard-gated multi-tool suite | A smaller, static-site-appropriate set: HTML validator, internal link checker, color-contrast checker, readability checker, i18n completeness check, plus the Frozen-Flask build itself (fails on template errors) | Different artifact shape — no Python application logic to lint beyond the (thin) build scripts themselves; the real content-correctness risks here are broken links/markup/contrast/readability, not application bugs. |
| Technical-debt TOML | Not carried over (not requested, and would be the first piece of schema/tooling overhead in an otherwise deliberately schema-free docs setup) | Flagging as available if wanted later — a plain `planning/tech-debt.md` list would be the lightweight equivalent, not proposed unprompted. |

## Carried over unchanged (same spirit, not relaxed)

- **Human review before any generated code/config gets executed** —
  present for inspection, never auto-run infrastructure or destructive
  commands. This has been the working pattern all session already
  (every droplet/DNS change presented and confirmed before running).
- **Collaboration on impactful design decisions** — also already the
  working pattern (every architecture fork this session has been raised
  as a question, not decided unilaterally).
- **Everything gets tested, checked before build/push/deploy** — same
  principle as `sask`'s pre-commit gate, adapted to this project's
  lighter git cadence (push after significant builds, not per-commit) —
  the check script runs before build, before push, and before deploy,
  not tied to commit granularity the way `sask`'s is.

## Resolved

- **Git identity for `web-sites`** — confirmed 2026-09-30: same as
  `sask` (`David` / `david.stitt@pm.me`).
