# `movement` — rebuild plan (evaluation of the qigong prototype)

2026-10-15. Status: **decided; in progress** (decisions below, David's
answers at the end). Source: David's prototype `sites/movement/heirloom/qigong/`
(a one-page static site, its README, 7 images, 33 PDFs, favicons).

## Target shape (from David's brief)

- `movement.davidstitt.net/<locale>/`: a new hub, same aesthetics as
  the other hubs, listing sub-sites. For now only **Qigong**.
- `movement.davidstitt.net/<locale>/qigong/`: the prototype's page, in
  its own aesthetic, which David considers an excellent starting point
  for layout and design.
- English and Spanish, with much more Spanish than before: the PDFs get
  translated too.
- Every resource file goes through the studio tools (`tools/studio/`,
  `docs/media-prep.md`). Published files follow the standard layout
  (`static/img/`, `static/docs/`), not the prototype's `img/` and
  `sets/` folders.
- Typography follows the established standards, using fonts we already
  host.

## Decisions (David, 2026-10-15)

- **The PDFs become pages**, one per set and reference, in both
  languages, at `/<locale>/qigong/<set>/`. URL rule (David, after step
  1): where a set has both a Chinese (romanized) and an English name,
  the URL uses the Chinese one, e.g. `daoyin-tu`, `wuqinxi`,
  `lian-gong-shi-ba-fa`, `si-zheng`.
- **The original PDFs are dropped** from the new build; the pages
  replace them. A print stylesheet makes each page a clean handout, so
  the browser's "Save as PDF" gives a PDF in either language. The
  prototype's PDFs stay in `heirloom/` as source material only.
- **The pictures inside the PDFs move onto the pages**: extracted,
  prepped with `img_prep.sh`, and given alt text.
- **The hub** (`/<locale>/`) lists **Qigong** (live) plus **Taiji,
  Xingyi, Pilates, Stretching** as "coming soon", not linked.
  - Taiji here is David's own future sub-site, separate from Louise's
    standalone `taiji.genuinemerit.com`.
  - The hub image is the prototype's ink-style tree (`taiji-tree.jpg`).
- **The sub-site is called "Qigong"** (not "Qigong & Stretching", since
  Stretching will be its own sub-site). The About text still names the
  original class.
- **A short "not medical advice" note** on the index and every set
  page, in both languages.
- **`image61.jpg` stays** in both places (Seasonal and References).
- **No link to the taiji site** from the About text.
- **The "Breathe. Move. Practice." tagline and the category names stay.**
- **Spanish arrives in batches, committed locally; nothing is pushed
  until all of it is done** (David, after step 3). Declaring `es-ES`
  makes the i18n check fail until every page exists, and pushes need a
  passing check. GitHub lags until step 6 is finished.
- **Agreed as recommended**:
  - a catalog (TOML) plus a Spanish overlay with fingerprints;
  - DM Sans and Libre Baskerville (already hosted);
  - light-only colours, with the greys fixed for AA;
  - no JavaScript;
  - a Spanish glossary before the set translations;
  - the fixes listed under "Findings".

## What's in the prototype (verified)

- **One page**: hero, 6 exercise-set categories (Standard, Ancient,
  Focus, Healing, Seasonal, Dragon Spirit) linking all **28 set PDFs**,
  a References section with **5 background PDFs**, and "About the class"
  (the original introduction), with a sticky category sidebar on desktop
  and a jump menu on mobile.
- **The PDFs are real text, not scans**: about 17,000 words, 1-4 pages
  each.
  - The structure is simple: a title, a source line or link, headings,
    nested numbered and bulleted lists, italic terms, Chinese characters
    (八段錦), YouTube links.
  - 5 PDFs carry pictures: Five Animal Frolics (a yin-yang/bagua
    diagram), Types of Qigong (a dharma wheel and yin-yang), Preserve
    and Strengthen, Qigong and ATP, and the References list.
- **Images**: 7, from 600 to 1900 px, mostly JPEG.
  - `yin_yang_pond.png` is 1.7 MB.
  - `image61.jpg` is used twice: as the Seasonal picture, and in
    References with the alt text "bagua and yin-yang diagram".
- **Favicons**: a complete set (SVG yin-yang, ICO, 32/192/512 PNG,
  apple-touch) plus `site.webmanifest`.
- **Fonts**: DM Sans (body) and Libre Baskerville (headings) from Google
  Fonts, with Georgia for the About text. We already host DM Sans and
  Libre Baskerville (roman and italic) ourselves (`tokens.css`, added for
  music), so no Google request and no new font files are needed.

## Findings to fix (not design questions)

- **Contrast**: on the paper colour, `--muted` `#69736c` is 4.39:1 and
  the sidebar footer grey `#777d73` is 3.78:1; both fail WCAG AA (4.5).
  They need darkening, as music's greys did. The other colours pass.
- **Small text**: much of it is 10-12 px (counts, descriptions, file
  info, the mobile menu). Raise it as for music.
- **Inline JavaScript**: the mobile jump menu uses
  `onchange="location.hash=..."`. Our CSP (`script-src 'self'`) blocks
  inline handlers. A plain-HTML disclosure (`<details>`) of category
  links does the same with no script at all.
- **The counts are wrong**:
  - The sidebar says 5 sets per category; the real numbers are 4, 3, 7,
    5, 4 and 5.
  - The "Exercise sets / 04" eyebrows don't match either.
  - Built from data, they'll always be right.
- **Typos**: "Barstable, MA." should be Barnstable, MA.; the file
  `Conserving_Nuturing.pdf` has "Nuturing"; `QIgong_for_Cold_and_Flu.pdf`
  has a capital I. The file names disappear anyway (the tools rename
  them).
- **Medical claims**: the README notes that the PDFs contain some
  traditional medical claims, kept as source material and not checked.

## Recommendation: translating the PDFs

**Each PDF becomes a page on the site, in both languages; the original
English PDFs stay available.**

- **Pages, one per set and reference:**
  `/<locale>/qigong/<set>/`, 33 pages × 2 languages.
- **Content** in `sites/movement/content/<locale>/qigong/<set>.md`. That
  is the same Markdown and front matter as taiji's pages, so the
  existing i18n check (every content page in every locale) covers the
  Spanish for free, and the translation flow is the usual one: Claude
  drafts, David reviews, nothing ships unreviewed.
- **Print**: a print stylesheet makes each page a clean handout. The
  browser's "Print / Save as PDF" then gives a Spanish PDF without any
  PDF-making tool on our side.
- **Original PDFs**: each set's page links its original English PDF
  (prepped by `pdf_prep.sh`, in `static/docs/`) as "Original handout
  (PDF, English)".
- **Why pages rather than Spanish PDFs**:
  - Pages are readable on a phone, searchable, accessible to screen
    readers, and use the site's own type.
  - They go through the checks we already have (HTML validity, links,
    contrast, i18n).
  - Making Spanish PDFs instead would need a PDF generator, a new tool
    to install, test and maintain (WeasyPrint or LibreOffice). It would
    also leave the English as PDFs only, not pages.
- **The work itself**: transcribing the 33 PDFs into Markdown, checked
  against the rendered pages. I'd do one category first, for David to
  check fidelity and format, before the rest.

## Other recommendations

- **Data**: a small catalog (`sites/movement/content/qigong.toml`) with
  categories, sets (title, one-line description, original PDF, page
  count), images and their alt text, and the Spanish strings in an
  overlay with fingerprints, as music has. The index, counts, sidebar
  and mobile menu are all built from it.
- **Typography**:
  - Body text in **DM Sans**, headings and the About text in **Libre
    Baskerville** (instead of Georgia, which visitors may not have).
    Both are already hosted, so this adds no new files.
  - Page titles use the shared `fit_title` rule (standing rule).
  - The hub uses the shared hub layout, like the other hubs.
- **Light-only, like music**: the prototype's palette is light. The
  contrast check still checks every token.
- **No JavaScript at all** on the qigong pages (the `<details>` menu
  above).
- **Spanish glossary first**: before translating the sets, a short
  glossary for David to approve. It would cover the terms kept in
  Chinese or pinyin (qi, dantian, wuji, Ba Duan Jin...), stances
  ("horse stance" → "postura del jinete"?) and recurring phrases. That
  keeps 33 pages consistent.
- **Go-live**:
  - a new DNS record and certificate for `movement.davidstitt.net`;
  - a `vhosts.yml` entry;
  - flip "Movement" from "coming soon" to live on the `davidstitt.net`
    hub;
  - add the hostname to Red Sift.

  The old `qigong.genuinemerit.com` is retired (`design/domains.md`), so
  there are no redirects.

## Dev plan

**To resume**: read this section, take the first unticked step, check
the log. **When stopping**: tick what's done and add a log line. Each
step ends at a review point. Nothing is committed without David's OK,
and nothing deploys before step 8.

- [x] **1. Scaffold** (English, local only):
  - the `movement` site package (`LOCALES = ["en-US"]` until step 4);
  - the hub (Qigong live, four "coming soon");
  - the qigong index, built from a catalog: the prototype's layout
    with hosted fonts, AA greys, larger small text, the no-script
    category menu, correct counts, and the medical note.
  - The prototype images and favicons went in here (`raw/` +
    `img_prep.sh`), because `static/` must pass the media check. The
    `vhosts.yml` entry waits for go-live (step 8): there is no
    local-only switch, and the dev nginx already has a movement vhost.
- [x] **2. PDF pictures**: extract the pictures inside the 5 PDFs into
  `raw/`, prep them, and note where each belongs (used in step 3):

  | Picture (`static/img/`) | Goes on |
  | --- | --- |
  | `bagua_yin_yang.png` (transparent) | `wuqinxi`, `types-of-qigong`, `preserve-and-strengthen` |
  | `dharma_wheel.jpg` | `types-of-qigong`, `preserve-and-strengthen` |
  | `qigong_atp_diagram.jpg` | `qigong-and-atp` |
  | `meridians_chart.jpg` | `references-and-links` |
- [x] **3. Set pages, English**:
  - page template plus print stylesheet;
  - one category transcribed from the PDFs, for David to check fidelity
    and format;
  - then the other 27 sets plus the 5 references.
- [x] **4. Spanish interface**: UI strings, catalog overlay (titles,
  descriptions), hub, About, and the medical note.
- [x] **5. Spanish glossary**, for David to approve:
  `design/movement-glossary.md`.
- [x] **6. Spanish set pages**, one category per review batch.
- [ ] **7. Polish**: accessibility, contrast, narrow screens, print
  check, David's manual review.
- [ ] **8. Go-live**:
  - DNS `movement.davidstitt.net` and its certificate;
  - deploy and smoke test;
  - the `davidstitt.net` hub entry goes live;
  - Red Sift.

## Log

- 2026-10-15: prototype evaluated; David answered the questions (below)
  and three follow-ups: hub image, the hub's taiji entry, the sub-site
  name. Decisions recorded above.
- 2026-10-15: step 1 done, waiting for David's review.
  - Built in `src/websites/movement/` (with `catalog.py`),
    `sites/movement/content/qigong.toml` and `content/en-US/qigong-about.md`,
    templates `hub_index.html`, `qigong_base.html` and
    `qigong_index.html`, `static/css/qigong.css`, and
    `config/i18n/movement/en-US.toml`.
  - Images were prepped at a 1200 px long edge, except `taiji_tree`:
    its 1500 px original was smaller than any re-save.
  - Sets and references show "page in preparation" until their pages
    exist (step 3).
  - The About text says "presents the exercise sets" instead of
    "downloadable lists", since the PDFs are gone.
  - The full pre-build check passes (vnu, links, contrast included).
- 2026-10-15: step 1 reviewed (David: looks good). Slugs follow the
  Chinese-name rule: `wuqinxi`, `lian-gong-shi-ba-fa` and `si-zheng`
  replace their English forms.
- 2026-10-15: committed and pushed step 1 (`230fc32`). Step 2 done.
  - The 5 PDFs hold 7 embedded images but only 4 distinct pictures (the
    bagua and dharma wheel appear in several).
  - Extracted with qpdf: the JPEG streams were dumped as is, and the
    transparency masks rebuilt from raw pixels. Gotcha: every mask is
    stored inverted (`/Decode [1 0]`), so it has to be flipped, or the
    pictures come out as black squares or fully transparent.
  - The largest copy of each went to `raw/pdf/` under a descriptive
    name, then through `img_prep.sh`. The meridians chart went from
    1.2 MB to 194 KB, the ATP diagram from 420 KB to 77 KB; the bagua
    stays a transparent PNG.
- 2026-10-15: committed and pushed step 2 (`302526a`). Step 3, first
  part, waiting for David's check:
  - Built the set page (`qigong_page.html`): breadcrumb, fitted title,
    summary, medical note, the transcription, previous/next links, and a
    print stylesheet. In print, only the title, summary, note, the set
    and its source address remain.
  - Transcribed the Standard category: `ba-duan-jin`, `daily-routine`,
    `morning-routine`, `qigong-and-stretch`.
  - Conventions: the PDF's sections become subheadings; run-in exercise
    names are bold; Chinese terms are italic (as in the PDFs); the
    nesting follows the PDF; page headers and numbers are dropped; "w/"
    is spelled "with".
  - Typos fixed: vigrous → vigorous; Spinal Chord → Spinal Cord; Strork
    → Stork; sqaut → squat; Nuture → Nurture; "left left foot" / "left
    right foot" → lift; a stray ". .".
  - Kept as in the PDFs: "Tai Qi Opening", "Stork Spreads Its Feather".
    "(see separate notes)" under the Samurai form was removed (David: the
    notes aren't part of the collection).
  - The i18n check now compares content pages in sub-folders too. The
    movement catalog check rejects a page file with no catalog entry.
- 2026-10-15: David checked the Standard pages: format and print preview
  fine, previous/next links liked. On to the other 29.
- 2026-10-15: committed and pushed step 3 part 1 (`67863c9`). Step 3
  done: all 28 sets and 5 references transcribed (33 pages, nothing "in
  preparation" any more).
  - Pictures are sized in the Markdown: `{: .small }` for the emblems,
    `{: .wide }` for the meridians chart and ATP diagram. That needed
    `attr_list` in the shared content loader; taiji and comunidad build
    unchanged.
  - Every page's word count is within 5% of its PDF's (headers dropped,
    "w/" spelled out, a few articles added).
  - Typo and spelling fixes, per page (content left as in the PDFs):
    - daoyin-tu: Zaragosa → Zaragoza; "Gwang Zhou Gung Fu" → "Gwong Zau Kung Fu" (as the school's own address spells it); Foward → Forward; degress → degrees; lifing → lifting; Thursting → Thrusting
    - wuqinxi: "Lift both hand" → hands
    - yi-jin-jing: "eyes slowly being to glare" → begin; sqaut → squat; thorasic → thoracic; hyper-tension → hypertension; "continued.." note dropped (the two columns are merged)
    - conserve-and-nurture: "12 time" → times; "Tap at Top Spine" → "Top of Spine"; degress → degrees
    - dredge-tone-root-relax: "back of neck neck" → neck
    - flex-and-stretch: sligthtly → slightly
    - preserve-and-strengthen: nuture → nurture; elixier → elixir; "thenc omb" → "then comb"; "Bell,and" spacing
    - stretchy-qigong: foreams → forearms
    - shake-out-the-kinks: "either standing or sitting or standing" → "either standing or sitting"
    - back-and-leg-pain: tarsul → tarsal; "knee.Repeat" spacing
    - kidney-qigong: "Lay on back" → Lie; hell → heel ("from toes to heel"); vertebrae → vertebra (one vertebra); missing closing bracket
    - cold-and-flu: practicising → practicing; lifing → lifting; strenghtening → strengthening; "fend of" → off; phoenxi → phoenix; "draws arms" → draw
    - elbow-and-balance: transtions → transitions; sidess → sides; simulaneously → simultaneously; "left the heavy hand" → lift; "only really move only" → once
    - ready-for-summer: "laying on back" → lying
    - high-energy-day: conepts → concepts; "[see p. 2 for details …]" → "the acupressure points are listed below" (no pages any more)
    - wake-up-the-earth: "Ankle rolls and circle" → circles
    - preparing-for-autumn: impermanance → impermanence; Streatch → Stretch; "is the good to augment" → "is good to"; "In Part One noted" → "Part One noted"
    - lian-gong-shi-ba-fa: "watch first right" → fist; "Hands on at side" → "Hands at side"
    - lift-the-spirit: lifing → lifting; "left both hands" → lift; "Pol stance" → Pole; "hand forward and back" → hands
    - shaolin-qigong: "on leg forward" → one; "down to onto knee" → "down onto knee"; "If can" → "If you can"
    - taiji-jiangan: Tun → Turn; "alternatingly" → alternately; ".." → "."; ORDER: the PDF's page 2 "Warm-up: extended 8 treasures" now comes first, before exercise 1 (it's a warm-up)
    - taijiquan-qigong: Presss → Press; "the the horizons" → the
    - types-of-qigong: "according the" → "according to"; "Buddhist, Daoism and Confucianism" → Buddhism; aides → aids; "starting the 1960s" → "starting in"; "focus strengthening" → "focus on strengthening"
    - references-and-links: "etc.." → "etc."; "My favorite 2.." → "My favorite 2:"
    - seven-corrections: Sprit → Spirit; synch → sync
    - qigong-and-atp: Shenzen → Shenzhen; "UCal/Irvine" → UC Irvine; O2 and Ca2+ written with proper sub/superscripts; the article's quoted text otherwise untouched
  - Content questions, answered by David the same day: Lian Gong no. 16
    now lifts the left hand; Kidney Stimulation keeps "repeat on left";
    the Shaolin splits are swapped (Shu Cha forward split, Hen Cha side
    split). The questions were:
    - lian-gong-shi-ba-fa, no. 16: "grasp left knee with both hands. Keeping right hand on knee, lift right hand up" - should the lifted hand be the left?
    - kidney-qigong, Kidney Stimulation: "rotate hands left ... Repeat on left side" - should the repeat be the right side?
    - shaolin-qigong, Splits: Shu Cha is called a side split, Hen Cha a forward split - usually it's the other way round (shu = vertical/forward, heng = horizontal/side)?
- 2026-10-15: committed and pushed step 3 (`36884b5`). Step 4 done,
  waiting for David's review of the Spanish:
  - `LOCALES` is now en-US and es-ES.
  - `config/i18n/movement/es-ES.toml` holds the interface: hub, index,
    pages, medical note. `content/es-ES/qigong-about.md` is the About
    text.
  - `content/qigong.es-ES.toml` translates every category, set and
    reference title and summary. Each block carries a fingerprint of
    its English. A deliberate test confirmed that changing an English
    summary makes `websites.movement.check` report the block "out of
    date".
  - The new `websites.movement.check` (with `--status`) runs in
    `pre-build-check.sh` after the music catalog check.
  - Language switch: a set page whose Spanish isn't written yet links to
    the Spanish index instead (no dead link).
  - As decided, the i18n check fails until step 6 (33 Spanish pages);
    HTML, links and contrast pass when run directly.
- 2026-10-15: David approved the Spanish so far. Three English titles
  gained their Chinese names: "Wuqinxi — Five Animal Frolics", "Lian
  Gong Shi Ba Fa — 18 Beneficial Exercises", "Si Zheng — Four Uprights".
  The Spanish follows the same form. Committed locally, not pushed.
- 2026-10-15: step 4 committed locally (`6a74602`). Step 5 drafted:
  `design/movement-glossary.md` covers style conventions, concepts,
  stances and hands, recurring exercises, and acupressure point names,
  built from the terms that recur across the 33 English pages. Four
  questions for David.
- 2026-10-15: glossary approved: imperative; the ATP quotations are
  translated with a note; book descriptions are translated, with titles
  kept in English; the terms stand.
- 2026-10-15: glossary committed locally (`6fb48a3`). Step 6 started.
  - Each Spanish page now records `translated_from`, the fingerprint of
    its English page, and `websites.movement.check` reports a page as
    out of date when its English changes (as the catalog overlay already
    did). The approved About page got its fingerprint.
  - Batch 1, Standard: `ba-duan-jin`, `daily-routine`,
    `morning-routine`, `qigong-and-stretch`, following the glossary.
    Approved by David; 29 pages to go.
  - Batch 1 committed locally (`1ec9a1a`). Batch 2, Ancient:
    `daoyin-tu` (44 exercises), `wuqinxi`, `yi-jin-jing`. Waiting for
    Approved by David; 26 pages to go. Pushed at David's request
    (session end), with the i18n check still failing on the 26 missing
    pages; deploy.sh would refuse until they exist.
- 2026-10-16: batch 3, Focus: `conserve-and-nurture`,
  `dredge-tone-root-relax`, `flex-and-stretch`, `preserve-and-strengthen`,
  `stretchy-qigong`, `seven-stretches`, `shake-out-the-kinks`. Approved
  by David, who now has high confidence in the Spanish and asked for all
  remaining 19 pages in one round.
- 2026-10-16: batch 3 committed locally (`c9285f5`). Final round: the
  other 19 pages, covering Healing, Seasonal, Dragon Spirit and
  References.
  - Qigong and ATP: the article's quotations are translated, with a note
    saying so («traducción nuestra») and the links to the original.
  - References: book descriptions translated, titles kept in English.
  - All 33 Spanish pages exist, and the full pre-build check passes again
    (all 15 checks). Each Spanish page is 1.09-1.38 times its English's
    word count, so nothing was dropped.
  - Approved by David (with the Lian Gong correction below). Step 6
    done; the backlog was pushed.
- 2026-10-16: David's correction. Lian Gong Shi Ba Fa is the complete
  set of 18 exercises (Dr. Zhuang and his successors have two further
  sets of 18, not mentioned here); it was developed in the 1980s,
  officially approved, hence its pragmatic language.
  - Its summary ("The first part of an 18-exercise…") is now empty, in
    both languages. The templates leave an empty summary out (no line on
    the index, no lead on the page; the meta description falls back to
    the title).
  - "part 1" / "primera parte" was dropped from the page's opening line.
  - The fingerprint checks flagged the Spanish as out of date until it
    was updated, as designed. All 15 checks pass.
- 2026-10-16: committed and pushed (`e893ed2`), so GitHub is current.
  Step 7 started.
  - Automated audit of all 70 movement pages: one h1 each, no
    heading-level jumps, every image has alt text, every page has a
    title, the skip link has its target, and `lang` matches the locale.
    Only gap: the two hub pages have no meta description. That comes
    from the shared hub layout, so all four hubs lack one.
  - External links (21): 18 fine.
    - `www.mdpi.com` and `www.ymaa.com` answer 403 to scripts (bot
      blocking, probably fine in a browser).
    - `www.liangong.org` is gone: https doesn't answer, and http serves
      a "404 Not Found" page.
    - A web search found no official replacement, only academic
      articles and a Qigong Institute abstract.
  - David's decisions (2026-10-16), in both languages:
    - The liangong.org link is dropped; the credit to Dr. Zhuang Yuan
      Ming stays. (His clinics were closed in the general crackdown on
      qigong groups; the site was probably run by followers in India.)
    - The Singing Dragon link goes straight to Michael Davies' book, with
      the shop's tracking parameters removed.
    - The Scott Meredith entry is removed from References: his other
      books stray too far, and David doesn't want to seem to endorse
      them.
    - David checked YMAA, MDPI, Ilchi Lee, Michael Davies, Mimi
      Kuo-Deemer and Alex Hui in a browser: all fine.
  - Hub descriptions (David: "best judgement"). The shared hub layout
    now writes a meta description from a new `hub.description` string.
    It covers five pages: the genuinemerit and davidstitt hubs and the
    music, movement and comunidad indexes, each in both languages. The
    sentences are written to stay true as "coming soon" items go live.
    The four already-live sites pick it up at the movement go-live
    deploy.

## Questions for David (answered 2026-10-15)

1. **PDF translation**: pages in both languages, plus the original
   English PDFs as downloads (recommended above)? Or something else,
   such as Spanish PDFs?

A: Agree with this approach, but drop the original PDFs.

2. **Keep the original PDFs** at all, once every set has its own page?
   Recommended: yes, as the authentic handouts.

A: Drop the original PDFs from new build.

3. **URLs**: `/<locale>/qigong/` for the index and
   `/<locale>/qigong/<set>/` for each set (e.g.
   `/es-ES/qigong/ba-duan-jin/`). OK?

A: Yes. May tweak some set names if needed.

4. **The hub**:
   - Is Qigong the only entry for now, or are other sub-sites planned
     to show as "coming soon"?
   - Which image should the hub use? (music's uses your photo; I can
     make a stand-in, or reuse one of the qigong images.)

A: Other possible sub-sites are: taiji, xingyi, pilates, and stretching

5. **Medical claims**: add a short, calm note ("traditional practice
   notes, not medical advice; adapt to your own body")? It would sit on
   the index and the set pages, in both languages.

A: Yes, good idea. Thanks.

6. **Images**:
   - `image61.jpg` appears twice (Seasonal and References). Keep both,
     or would you rather pick a different Seasonal image?
   - The pictures inside the 5 PDFs: carry them onto the set pages,
     where they help, or leave them in the original PDFs only?

A: OK to use it twice.  Carry PDF images onto the pages.

7. **The About text** mentions the YMCA class. Should it link to the
   taiji site (Louise's class), as `planning/target-sites.md`
   anticipated ("may get a link *from* `movement`")?

A: No.

8. **Anything in the prototype to drop or change** beyond the fixes
   above, e.g. the "Breathe. Move. Practice." tagline or the
   category names?

A: No, that tagline is OK.
