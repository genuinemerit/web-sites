# Design docs

Started 2026-09-30, once actual building began (as opposed to
preparation). This folder is for design docs written *during* build —
decisions made while implementing a specific site, template, or pipeline
piece.

**Distinction from `planning/`**: `planning/` holds the pre-build
discussion record — architecture, aesthetics, target-site vision,
roadmap, housekeeping rules, all worked out before any code existed.
That folder stays as the historical archive of how those decisions were
reached; it doesn't get new entries for build-phase work. `design/` is
where new, ongoing design docs land from here forward.

Same conventions as `planning/` otherwise: plain markdown, one topic per
file, dated, with rationale — no TOML schema, no validator script
(still deliberately lighter than `sask`'s dd/req/spec system).
