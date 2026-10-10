# Structure — "Bożena Polok" (version of 2026-10-10)

Source: shared artifact https://claude.ai/artifact/BLup8P24VeWbH4hJMK9yFf (version 1791139922-3c40),
copied in `_artifact/source/index.html`; its 13 embedded JPEGs are in `_artifact/assets/`.
Single static HTML page, English, one inline script (display settings, disclosures, gallery).
`<title>`: `Bożena Polok`. Texts: `content.yaml`. Tokens: `tokens.css`. Components: `components.md`.

The site implements it as several URLs, not one page: see `docs/site-architecture.md` (the
anchors below become pages, the legal disclosures become the pages `/legal-notice/` and `/privacy/`).

## What changed since the 2026-09 version

- **Positioning**: consulting first. Hero eyebrow "Medical Affairs Consulting & Coaching", new role
  and thesis, a "Today: …" line instead of the status badge, buttons *Discuss a project* · *How I
  can help* · *LinkedIn ↗*.
- **Accessibility layer**: skip link to `#main`; a **Display settings** bar (text size in 5 steps,
  high contrast, dark mode, remembered in `localStorage`); `rem` text sizes; smallest text 15px;
  darker palette (AA everywhere); high-contrast theme; forced-colours and print rules; links in
  running text underlined; 44px touch targets; screen-reader-only texts ("to" in periods,
  "(opens in a new tab)", "in French", "Date unknown"); `lang="pl"` on the name, `lang="fr"` on
  French titles.
- **About**: new heading; a two-image figure (zebrafish eye) beside it; six paragraphs; the
  language pills are gone (caption only).
- **Quote**: Antonie van Leeuwenhoek replaces Hippocrates, with a comment line under the citation.
- **Services** (was "Expertise", anchor unchanged `#services`): three **offer cards first**, then
  "What I bring": therapeutic areas as a dot-separated line, six service cards (h4), a CTA band.
  Named prescription products are gone.
- **Experience**: dates in sentence case ("Dec 2022 — present"), no organisation descriptions,
  "In parallel: Patient Ambassador EMEA", one achievement links to the new featured paper; the
  research timeline and education are folded under a **"show more" disclosure**; the IRO + PhD
  entries share a column of two figures (`tl-pair`); one education card ("First degree", with a
  description).
- **Publications**: a featured medical-affairs paper (★, Munk et al. 2022, with a note), then the
  ten research papers (three visible, seven under "Show 7 more research papers"); TV & press
  under another disclosure; media dates "19 May 2008".
- **Personal**: the photo is a rounded square (not rotated); new card texts; a **"Through my lens"**
  gallery of six photos (copyright note, right-click and drag discouraged); asides get titles.
- **Footer**: "Let's talk." with a lede, "Working in …" line (no language-code pills), an
  **Accessibility** statement, links to the **Legal notice (Impressum)** and **Privacy statement**
  (disclosures holding the texts, with placeholders to fill), longer copyright line.

## Section order

| # | Block | Element / id | Background | Nav label → anchor |
|---|---|---|---|---|
| — | Skip link | `a.skip-link` → `#main` | — | — |
| — | Display settings | `div.a11y-bar` | `--surface-tint`, full bleed | — |
| 0 | Navigation | `<nav aria-label="Main">` (sticky; static at ≤ 480px wide, ≤ 640px high, text size ≥ 150 %) | translucent `--bg` | — |
| 1 | Hero | `<header class="hero">` inside `<main id="main">` | `--bg` | — |
| 2 | About | `section#about` | `--bg` | About → `#about` |
| 3 | Pull quote | `blockquote.pull-quote` | `--bg` | — |
| 4 | Services | `section#services.tint` | `--surface-tint` | Services → `#services` |
| 5 | Experience (+ research, education) | `section#experience` | `--bg` | Experience → `#experience` |
| 6 | Publications & Media | `section#publications.tint` | `--surface-tint` | Publications → `#publications` |
| 7 | Personal ("Off the clock") | `section#personal` | `--bg` | Personal → `#personal` |
| 8 | Contact / footer (+ legal texts) | `footer#contact` | `--bg`, top hairline | Contact → `#contact` |

Tinted sections extend past the text column by the page gutter (`margin: 0 -20px` inside the 840px
wrap): on screens wider than ~880px they are a centred band, not full-bleed.

## Heading hierarchy

- `h1` — once, in the hero: "Bożena *Polok*" (`<span lang="pl">`, surname in italic accent colour).
- `h2` — one per section (About, Services, Experience, Publications & Media, Personal) and the
  footer's "Let's talk.".
- `h3` — offer cards; sub-headings "What I bring", "From my medical affairs work", "From the research
  years", "Through my lens" (`.subhead`); timeline group labels; "First degree", "Television",
  "Press"; off-duty cards; aside-note titles; footer "Accessibility" and the legal sub-headings.
- `h4` — service cards (under "What I bring"), timeline roles, publication titles.
- Eyebrows (`p.eyebrow`, mono uppercase) precede section `h2`s and some `h3`s; they are paragraphs.

```
a.skip-link "Skip to main content"
div.a11y-bar
  button.a11y-toggle "Display settings" (aria-expanded, controls #a11y-panel)
  div#a11y-panel[hidden] role=region
    group "Text size": A− · A · A+     (5 steps: 100 / 112.5 / 125 / 150 / 175 %)
    group: "High contrast" · "Dark mode" (aria-pressed)
  p.sr-only role=status aria-live=polite   (announces each change)

nav  brand "B. Polok" · About · Services · Experience · Publications · Personal · Contact

main#main
  header.hero
    p.eyebrow · h1 · p.hero-role · p.hero-thesis · p.hero-now
    .hero-cta    Discuss a project (primary) · How I can help (ghost) · LinkedIn ↗ (ghost, new tab)
    .iris        portrait in an SVG ring (stays visible on phones, above the name, 200/128px)

  section#about
    .section-head.about-head   eyebrow · h2  |  figure.video-card.eye-pair (2 × 4:3 image, title, caption)
    .about-grid                6 paragraphs + p.lang-caption

  blockquote.pull-quote        quote · cite · p.quote-note

  section#services.tint
    .section-head              eyebrow · h2 · lede
    .offer-grid                3 × .offer-card (h3 · p)
    h3.subhead "What I bring"  · p.ta-line (sr-only "Therapeutic areas: " + 7 areas joined by " · ")
    .service-grid              6 × .service (icon · h4 · p)
    .cta-band                  p · button "Let's talk" → #contact

  section#experience
    .section-head              eyebrow · h2
    h3.group-label "Industry — 2011 to present"
    .timeline                  5 × .tl-item (Santen · Allergan · Sanofi · UCB · Olympus + solo thumb)
    details.more "Research career & education, 2000–2011"
      h3.group-label "Research — 2000 to 2011"
      .timeline                CMU Geneva · BIDMC · .tl-pair (IRO Sion + PhD, 2 thumbs in a column)
      .section-head            eyebrow "Education" · h3 "First degree"
      .edu-grid                1 × .edu-card.edu-card-wide (degree · institution · description)

  section#publications.tint
    .section-head              eyebrow · h2 · lede
    h3.subhead "From my medical affairs work"
    .pub.pub-featured#pub-ma   ★ · h4 · meta · p.pub-note
    h3.subhead "From the research years"
    ol.pub-list                01–03
    details.more "Show 7 more research papers"   ol.pub-list[start=4] 04–10
    .pub-source                "Full record on PubMed →"
    details.more "TV & press coverage, 2008–2009"
      eyebrow "Media" · h3 "Television" · ul.media-list (2) · p.media-note
      h3 "Press" · ul.media-list (2) · p.media-note

  section#personal
    .section-head.personal-head  eyebrow · h2 · lede | img.personal-photo (rounded square)
    .off-duty-grid               5 × .off-card (icon · h3 · p); "Mentoring" is .wide
    .lens                        h3.subhead "Through my lens" · ul.lens-grid (6 photos) · p.lens-note
    .aside-row                   2 × .aside-note (h3.note-title · p)

footer#contact
  .footer-grid   eyebrow · h2 · p.contact-lede · email · LinkedIn  |  p.footer-langs
  .a11y-statement  h3 "Accessibility" · p (mailto link with subject)
  nav.legal-links  "Legal notice (Impressum)" → #legal-notice · "Privacy statement" → #privacy
  details.more.legal#legal-notice   six h3 sections (address, phone, VAT placeholders)
  details.more.legal#privacy        intro + nine h3 sections (hosting, retention, email placeholders)
  p.copyright

script                 display settings, disclosure opening, gallery protection, skip-link focus
script[ld+json]        schema.org Person (unchanged)
```

## Behaviour (inline script)

- **Text size**: `<html data-textsize="0…4">`, buttons disabled at the ends, stored as `bp-textsize`.
- **Theme**: `<html data-theme="light|dark">`, default = system, stored as `bp-theme` once chosen;
  follows the system live until then.
- **High contrast**: `<html data-contrast="high|normal">`, default `high` when the system asks for more
  contrast, stored as `bp-contrast`.
- Each change is announced in the live region ("Text size 125%", "Dark mode on", …). Opening the
  panel moves focus to its first enabled button.
- A link (or the URL hash) pointing inside a closed `<details>` opens it; all disclosures open before
  printing.
- Gallery photos: context menu and dragging are blocked.
- The skip link moves focus to `<main tabindex="-1">`.

## Anchors / cross-links

- `#pub-ma` (featured paper) ← Allergan achievement "Munk et al. (2022)".
- `#pub-02` (Kotkamp et al., 2014) ← the two research thumbnails "FIG. 1", "FIG. 5".
- Hero CTAs `#contact`, `#services`; CTA band `#contact`; footer `#legal-notice`, `#privacy`.
- External links: `target="_blank" rel="noopener"` + sr-only "(opens in a new tab)"
  (+ "in French" for French media).

## Images (`_artifact/assets/`)

| File | Where | Displayed |
|---|---|---|
| `portrait.jpg` (832²) | Hero | 204px circle (128px on phones) |
| `zebrafish-eye-light-microscope.jpg`, `zebrafish-eye-stained-section.jpg` | About figure | 4:3, cover |
| `olympus-ixplore-spinsr.jpg` (520²) | Olympus entry | 84px circle |
| `kotkamp-2014-fig1.jpg`, `kotkamp-2014-fig5.jpg` | IRO + PhD pair | 76px circles, `object-position` 50% 20% / 20% 50% |
| `ski-guide-matterhorn.jpg` (640²) | Personal head | 320px rounded square |
| `lens-*.jpg` (6 × 960×720) | "Through my lens" | 4:3 grid |

Alt texts are in `content.yaml`. Decorative SVGs (`aria-hidden`): hero ring, line icons.

## Responsive behaviour

Single fluid column, max width 840px, 20px gutter. Breakpoints in `tokens.css`. Phones: portrait
above the name; grids fall to 2 then 1 column; the personal photo goes full width (max 360px);
timeline thumbnails move above their text; the lens grid has 2 columns. Large text (≥ 125 / 150 %)
collapses more layouts to one column.

## Theming

Light by default; dark via `prefers-color-scheme` or `data-theme`; high contrast via
`data-contrast="high"` (black on white, or white on black in dark mode) or `prefers-contrast: more`;
Windows forced colours supported.
