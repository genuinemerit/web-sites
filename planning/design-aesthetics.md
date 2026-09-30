# Aesthetics, style, look-and-feel

Opened as its own topic 2026-09-30, at David's explicit request — "this
deserves its own place in design review," distinct from the CSS-variables/
architecture discussion in `architecture.md`. Current legacy sites read as
bare-bones; David wants to elevate the look without abandoning the
"simple, robust, no Node" values driving the rest of this project. Nothing
decided yet — this file is the discussion starting point.

## Starting menu of options (Claude's first pass, for reaction)

- **Type first.** A well-chosen, small type system (1-2 quality
  typefaces, deliberate line-height/measure) is usually the single
  highest-impact, lowest-cost move away from "bare-bones" — plain CSS,
  no tooling.
- **Restrained color system**, via the CSS custom properties already
  agreed in `architecture.md` — including `prefers-color-scheme` dark
  mode support, which is cheap in plain CSS and reads as "modern" for
  free.
- **Native CSS layout** (Grid/Flexbox) rather than reaching for a
  framework — avoids Node/build tooling entirely, and modern CSS is
  capable enough on its own for this kind of site.
- **A classless or near-classless CSS framework** (single stylesheet, no
  JS, no build step — e.g. the Pico.css style of thing) as a possible
  starting baseline to reskin from, rather than hand-rolling every base
  element from scratch. Worth naming as an option even though it cuts
  against David's usual "roll my own" instinct — could be evaluated and
  rejected, but worth actually looking at given the explicit goal of
  *elevating* the look with minimum new complexity.
- **Shared structural partials, per-site skin.** Given 7 properties with
  different personalities (public vs. private, community vs. game vs.
  music vs. reference docs), the likely right mental model is one shared
  foundation (Jinja2 macros for header/nav/footer, gallery/card layouts,
  type & spacing scale) with per-site theming (accent colors, imagery
  style) — a family resemblance, not one identical template stamped
  across everything. Worth confirming this is the right frame before
  building any of it.
- **Accessibility as part of "elevated," not bolted on after** — semantic
  HTML, real alt text, sufficient contrast. Cheap to hold as a bar from
  the start; expensive to retrofit later. Some legacy content (bare
  filenames, likely missing alt text) will need real authoring work here
  regardless of visual design, since it's being rebuilt in Markdown anyway.

## Confirmed 2026-09-30

David likes the shared-core/per-site-skin model (question 1 below,
resolved). Wants help/guidance evaluating a classless CSS framework —
specifically hasn't used Pico.css and would like an orientation before
deciding whether to adopt it as the starting baseline.

**Pico.css orientation (Claude, for when David wants to look at it):**
a single stylesheet, no JS, no build step — link it and semantic HTML
(`<button>`, `<article>`, `<nav>`, etc.) already looks reasonably
polished with sensible type/spacing/color defaults, including built-in
dark-mode support via `prefers-color-scheme` or a class toggle. You
override via CSS custom properties (`--pico-primary`, etc.) rather than
fighting specificity, which fits the "shared core, per-site skin" model
directly — the "core" could literally be Pico plus a small custom
properties file, "skin" is just different variable values per site. Worth
a hands-on look (a throwaway single HTML file with a few components) once
ready to evaluate rather than deciding from description alone.

**Review cadence — confirmed 2026-09-30:** aesthetics gets a recurring
review/approve checkpoint every dev cycle, not a one-time decision.
Combined with automated checks where they genuinely apply (color-contrast
and readability linting, see `architecture.md`'s Testing section) —
subjective visual judgment stays manual by design, the automation is a
floor, not a replacement for David's own review.

**Visual reference points — resolved 2026-10-01.** Rather than naming
specific external sites/print-design examples up front, David's answer
was structural: the recurring dev-cycle checkpoints above *are* the
mechanism — each one explicitly reviews style/look-and-feel/alignment
against the "calm" design model in the governing brief below, rather
than needing a separate reference-site list as a one-time deliverable.

## Governing design brief — adopted 2026-09-30

David's notes (appended below, kept verbatim) are now the working
reference for aesthetic direction — a well-sourced "content-first"/"calm"
design brief, not a trend-chasing one. Concrete, actionable specifics
pulled out for the architecture/build:

- **Reference models**: GOV.UK, U.S. Web Design System
  (designsystem.digital.gov) — content-first, evidence-backed, built for
  the widest possible audience. **Explicitly not** Awwwards/CSS Design
  Awards (visual-spectacle-oriented, opposite of this brief).
- **Trusted sources for ongoing guidance**: Nielsen Norman Group
  (usability), WebAIM (accessibility + contrast checker), GOV.UK Service
  Manual, Smashing Magazine, Baymard (mainly e-commerce, less relevant
  here).
- **Nav**: one clear primary bar, 5-7 top-level items, plain-word labels
  (not clever ones), collapses to a labeled "Menu" button on mobile (not
  an unlabeled icon alone).
- **Typography**: body 16-18px minimum, line-height ~1.5, 60-75 character
  measure, sans-serif, avoid weights ≤300 for body text. **Atkinson
  Hyperlegible** (free, Google Fonts, designed by the Braille Institute
  for low-vision readers) named as a strong concrete candidate — worth
  trying first rather than searching further.
- **Contrast**: 4.5:1 minimum (WCAG AA) for body text — matches the
  contrast-checker already planned in `architecture.md`; WebAIM's
  checker implements the same WCAG formula, so our own small script and
  WebAIM's tool should agree. Named failure mode to specifically catch:
  light-gray-on-white body text.
- **Color-blindness**: never use color alone to carry meaning (pair with
  icon/label/underline); avoid red/green pairings. WebAIM/Coblis/browser
  devtools can simulate this for spot-checks.
- **Dark mode**: system-preference-following (`prefers-color-scheme`),
  never forced — already the plan.
- **i18n, revising the switcher plan**: `lang="es"`/`lang="en"` must be
  set correctly per locale build (a concrete requirement for the
  freeze-per-locale mechanism in `architecture.md`); layouts must allow
  for text expansion (Spanish runs ~20-30% longer than English — no
  fixed-width buttons); **switcher labeled in each language's own name
  ("Español"/"English"), not flags** — supersedes the flags-or-names
  framing from the original i18n discussion, see contradiction note
  above.
- **Mobile**: tap targets ≥44px, never hover-only, verify both phone and
  desktop layouts before publishing.
- **Legal context**: EU Accessibility Act (effective June 2025) generally
  requires WCAG 2.1/2.2 AA for consumer-facing businesses — doesn't cover
  a personal site, but a good benchmark regardless, and relevant given
  David is in Spain.

Resolves `open-questions.md` item 1.

===

David's Notes:

The following discussion with Claude adequately encompasses my concerns for design aesthetics and should be taken a a general guide:

Here's a practical overview. One caveat first: the annual "trend" articles mostly push flashy things. This year's lists lean toward bolder ideas, mixed mediums, and interfaces pushed in playful, unexpected directions, including glassmorphism and immersive 3D/AR. What you're describing is less a trend than a durable school of design, and it's well represented.

## The style you're after

The mainstream version is usually called content-first or "calm" design. It is also what the better government and institutional design systems produce. Its main traits are:

- **One clear primary navigation bar** with about 5–7 top-level items. Labels are plain words like "Recipes" or "About," not clever ones. On mobile, those items collapse into a menu button labeled "Menu," not only an icon.
- **Generous whitespace** and a single readable column for text.
- **Visible structure.** Headings actually look like headings, links look like links (underlined or clearly colored), and buttons look like buttons.
- **Restraint.** There's one accent color, few animations, and no modal pop-ups interrupting reading.

Even the trend writers concede that clean, uncluttered layouts that focus on essential elements remain the baseline. The "too lean" failure you mention usually comes from hiding navigation behind unlabeled icons or ultra-faint gray text. Avoiding those two things solves most of it.

Good real-world models are GOV.UK and the U.S. Web Design System (designsystem.digital.gov). Both were built for the widest possible audience, including older and non-technical users, and both publish their reasoning openly.

## Trusted reviewers and references

- **Nielsen Norman Group (nngroup.com)** is the closest thing to a gold standard. Its usability guidance is research-based rather than fashion-driven.
- **Baymard Institute** does deep usability research, strongest on e-commerce.
- **Smashing Magazine** has practical, well-edited articles for designers and developers.
- **WebAIM** is the go-to for accessibility, including its contrast checker and annual accessibility survey of top websites.
- **GOV.UK Service Manual and Design System** are free, evidence-backed guidance on plain, usable design.
- **Awwwards and CSS Design Awards** are worth knowing about, but they mostly reward visual spectacle, which is the opposite of your brief.

## Multi-platform: still essential

Mobile now accounts for well over half of web traffic, so responsive design (one site that adapts to any screen) is simply expected. Some practical points:

- Make tap targets at least about 44 px.
- Never rely on hover to reveal things.
- Check both phone and desktop layouts before publishing.

## Localization and locale sensitivity

This matters more than people think, especially in Europe:

- **Declare the page language** in the code (`lang="es"`). Screen readers and translation tools depend on it.
- **Allow for text expansion.** Spanish typically runs 20–30% longer than English, so fixed-width buttons break.
- **Label the language switcher in each language's own name** ("Español," "English"). Don't use flags, because languages aren't countries.
- **Respect local formats** for dates (30/09/2026 vs. 9/30/2026), decimals (3,5 vs. 3.5), and currency placement.

Since you're in Spain, one legal note: the **European Accessibility Act** took effect in June 2025. It requires many consumer-facing businesses to meet accessibility standards, generally WCAG 2.1/2.2 AA. A personal site isn't covered, but it's a good benchmark regardless.

## Colors and fonts that don't drive people away

**Contrast.** Body text needs at least a 4.5:1 contrast ratio against its background (WCAG AA). The most common modern sin is light-gray text on white. WebAIM's contrast checker makes this a 10-second test.

**Color blindness.**
- Never use color alone to carry meaning. Add an icon, label, or underline.
- Avoid red/green pairings for things like good/bad.
- Chrome and Firefox dev tools can simulate color-vision deficiencies. Coblis is a free online simulator.

**Fonts.**
- Use a body size of 16–18 px minimum, a line height around 1.5, and lines of roughly 60–75 characters.
- Plain sans-serifs work well: system fonts, Inter, Source Sans, or **Atkinson Hyperlegible**. The Braille Institute designed Atkinson Hyperlegible specifically for low-vision readers, and it's free on Google Fonts.
- Avoid thin weights (300 and below) for body text. They can look elegant on a designer's retina screen and be unreadable for a 70-year-old on a laptop.

**Dark mode** is popular, but offer it as an option that follows the user's system setting rather than forcing it. Many older readers find light text on dark backgrounds harder to read for long passages.
