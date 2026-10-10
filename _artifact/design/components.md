# Components (version of 2026-10-10)

The repeated components of the "Bożena Polok" artifact: markup, variants, behaviour and
accessibility rules. Class names are the source's (`_artifact/source/index.html`) unless the site
renamed them (noted). Values are the tokens of `tokens.css`.

The CSS of record is the site's: one stylesheet per component in `static/css/components/<name>.css`,
one template in `templates/includes/<name>.html` (parameters documented at the top of each). Every
component can be seen on the DEBUG-only page `/_composants`.

## Base (applies to everything)

- `html` font size 100 %, raised by the text-size control (`data-textsize` 1–4 → 112.5 / 125 / 150 /
  175 %); every text size is in `rem`, spacing stays in `px`. Smallest text: 15px (`--fs-sm`).
- Body: Source Sans 3, 18px, line-height 1.6; headings Fraunces 600, `text-wrap: balance`;
  `overflow-wrap: break-word` on headings, paragraphs, list items and links.
- Focus: 3px `--accent` outline, 3px offset, plus a 6px `--bg` halo (`--ring-focus`), on every
  interactive element.
- Skip link: "Skip to main content", hidden above the viewport until focused; moves focus to
  `<main id="main" tabindex="-1">`.
- Links inside running text are underlined (offset 0.18em, 1.5px), never colour-only; in high
  contrast every link is underlined.
- Anchors land below the sticky nav: `scroll-padding-top` / `scroll-margin-top` 140px.
- Screen-reader-only text: `.sr-only` in the source, `.visually-hidden` in the site.
- `prefers-reduced-motion`: no smooth scroll, no transition or animation.
- Print: settings bar, nav, ring and disclosure summaries hidden; disclosures opened; external
  publication links spelled out.
- Forced colours: buttons, pills, badges, cards and notes get a `CanvasText` border; dots and bullets
  turn `CanvasText`; pressed settings buttons use `Highlight`.
- **Display font roles** (new): mono only for eyebrows, pills, badge and the footer contact links;
  dates, numbers, group labels and captions use the body face with tabular figures (`.tabular`).

## 1. Display settings bar — `display_settings` (new)

Full-bleed tinted strip above the nav, right-aligned. A disclosure button (sun icon, "Display
settings", `aria-expanded`, `aria-controls`) opens a panel (`role="region"`) with:
a "Text size" group (A− · A · A+, `aria-label`s "Decrease / Reset / Increase text size"; A− and A+
disabled at the ends) and two toggles "High contrast", "Dark mode" (`aria-pressed`).
Buttons: 44px minimum, 2px `--line-strong` border, `--surface` background; pressed = `--ink`
background, `--bg` text. A polite live region announces each change. Choices are stored in
`localStorage` (`bp-textsize`, `bp-theme`, `bp-contrast`).
Site: the bar is `hidden` until the script runs (`static/js/preferences.js`, loaded in `<head>` so
stored choices apply before the first paint).

## 2. Navigation bar — `nav`

Sticky, translucent (`--nav-bg`), blurred, hairline bottom. Brand left (Fraunces), links right.
Links: 44px tall (padding 10px 4px), `--ink-muted`; hover/focus/current: `--accent` + underline.
Becomes `position: static` at ≤ 480px wide, ≤ 640px high, or text size ≥ 150 %.
Site: the brand links to `/`; the current page is marked `aria-current="page"`.

## 3. Eyebrow — `eyebrow`

`<p class="eyebrow">` — IBM Plex Mono 500, `--fs-sm`, uppercase, tracking 0.11em, `--accent-2`.

## 4. Section head — `section_head`

Eyebrow + `h2` (`--fs-h2`) + optional lede (`--fs-lg`, `--ink-muted`, 60ch) + optional pills.
Variants:
- **sub-section**: `h3` 1.5rem ("First degree") or 1.375rem ("Television", "Press"); site class
  `section-head--sub`.
- **with photo** (`.personal-head`): two columns, the photo right (see 15).
- **with figure** (`.about-head`, new): columns 0.85fr / 1.15fr, the figure right (see 6); one column
  under 760px and at text size ≥ 125 %.
- **subhead** (new): a lone `h3.subhead` — sans 700, `--fs-body`, margin 44px 0 10px (8px when it
  directly follows the section head).

## 5. Section — `section`

`padding: 64px 0`; `.tint` = `--surface-tint` band bleeding by the gutter. In high contrast the
tint is white, so the band gets 2px top and bottom rules.

## 6. Figure (image pair) — `figure_pair` (new)

`figure.video-card.eye-pair` in the source. One or two 4:3 frames side by side (gap 10px; frame:
4px radius, hairline border, `--shadow`, image `object-fit: cover`), then a caption: a bold title
(`--fs-lg`) and a muted line (`--fs-sm`). The source's unused "video poster" styles are not carried
over.

## 7. Button — `button`

`.btn` 44px minimum, padding 11px 20px, radius 2px, 600 `--fs-ui`.
`.btn-primary`: `--accent` background, `--bg` text, hover opacity 0.92; in high contrast a 2px
`--ink` outline. `.btn-ghost`: **2px** `--line-strong` border, `--ink`; hover `--accent`.
External: label + "↗" (`aria-hidden`) + sr-only "(opens in a new tab)".

## 8. Status badge — `status_badge`

Pill with a pulsing dot. No longer used by the hero (kept as an optional hero field).

## 9. Pills and caption — `pill`

Mono `--fs-sm` pills with a `--line-strong` border. The language pills are gone from the design;
the language **caption** stays (`p.lang-caption`, `--fs-sm`, `--ink-faint`).

## 10. Tag line — `tag_line` (new)

`p.ta-line`: items joined by " · " (`--fs-md`, `--ink-muted`), preceded by an sr-only label
("Therapeutic areas: ").

## 11. Hero + iris portrait — `hero`, `iris`

Grid 1.3fr / auto. Eyebrow · `h1` (`<span lang="pl">Bożena <em>Polok</em></span>`, `--fs-h1`) ·
`p.hero-role` (`--fs-body`, 500, 38ch) · `p.hero-thesis` (`--fs-thesis`, 54ch) ·
`p.hero-now` (new, `--fs-md`, `--ink-muted`) · buttons. Portrait: 204px circle, 5px `--accent`
border, 8px `--bg` ring, inside the 374px SVG ring.
Phones (≤ 640px): one column, top padding 40px, the portrait **stays visible above the name**
(ring 200px, photo 128px, 4px border, 6px ring). Text size ≥ 150 %: one column. High contrast: the
surname is not italic.

## 12. Pull quote — `pull_quote`

Centred, 640px max, a 32px teal rule above. Quote: Fraunces italic 500, `--fs-quote`.
Cite: **body face** 600 `--fs-sm`, `--accent-2`, no longer uppercase. New `p.quote-note`: body
face, `--fs-md`, `--ink-muted`. High contrast: not italic.

## 13. Offer cards — `offer_cards` (new; replaces the "offer note")

`.offer-grid`: three columns (gap 18px), one under 760px and at text size ≥ 125 %.
`.offer-card`: `--surface`, hairline border, **4px `--accent` top rule**, padding 24px 22px; `h3`
`--fs-2xl`; `p` `--fs-md`, `--ink-muted`. Site: titles link to the service pages.

## 14. Hairline card grids — `card_grid`

`.service-grid` / `.off-duty-grid`, 3 → 2 → 1 columns (760 / 520 or 480px), one column at text size
≥ 150 %. `.service`: teal 26px icon, title **h4** sans 600 `--fs-lg` (under "What I bring"), text
`--fs-ui`. `.off-card`: amber 28px icon, title h3 Fraunces `--fs-xl`, text `--fs-md`; `.wide` spans 2
columns. High contrast: each cell gets a border.

## 15. Personal photo — `personal_photo`

**Rounded square** (12px radius), 320px, 5px `--accent-2` border, `--shadow`, **no rotation**.
Phones: full width, max 360px, square.

## 16. Aside note — `aside_note`

`--accent-soft` box, `--fs-md`. New: an optional title `h3.note-title` (sans 700 `--fs-lg`). The
icons of the previous version are gone (still supported). Two notes sit side by side
(`.aside-row`), stacked under 700px and at text size ≥ 150 %.

## 17. Call-to-action band — `cta` (new design)

`.cta-band`: a `--surface` card with a `--line-strong` border, a Fraunces 600 `--fs-2xl` sentence
(a `<p>`, not a heading) and a primary button, wrapping on small screens. Hidden in print.

## 18. Timeline — `timeline` (+ `timeline_item`, `timeline_text`)

Rail (`--line-strong`), a 9px teal dot per entry. `h3.group-label` (sans 700 `--fs-lg`, `--ink`) ·
`.tl-date` (sans 600 `--fs-sm`, `--accent-2`, tabular; "Dec 2022 <span aria-hidden>—</span><sr>to</sr>
present") · `h4` role (sans 600 `--fs-body`) · `.org` · new `.org-extra` ("In parallel: …", 600,
`--ink`) · `.org-desc` (no longer italic; unused by the current content) · `p` · bulleted
achievements (amber bullets; a link inside is underlined).
Variants: **solo thumb** (`.tl-photos-solo`, 84px, moves above the text under 560px);
**pair** (`.tl-pair`, now implemented by the site): two entries in column 1, a column of 76px
thumbs spanning both rows in column 2; under 640px the thumbs go above, in a row.

## 19. Research thumbnail — `research_thumb`

108px circle (84 solo, 76 in a pair), teal border, `--surface-tint` ring. Caption in the body face
`--fs-sm`; the link (amber, underlined, no wrap) ends with "→" (`aria-hidden`).

## 20. Education card — `education`

Two-column grid; the source marks a lone card `.edu-card-wide` (the site makes the last odd card
span both columns). Degree 600 `--fs-md-plus`, institution `--fs-sm`, new `p.edu-desc` (`--fs-sm`,
line-height 1.55).

## 21. Publication — `publication` (+ `publication_reference`)

Row: 34px number column (`aria-hidden`, tabular) + `h4.pub-title` (sans 600 `--fs-md-plus`) +
`.pub-meta` (`--fs-sm`; "<abbr title="PubMed identifier">PMID</abbr> n" link, underlined, sr-only
"on PubMed (opens in a new tab)"). Variants: **featured** (`.pub-featured`, new): `--surface` card
with a `--line-strong` border, amber "★" instead of the number, `p.pub-note`; **continued list**
inside a disclosure (`<ol start="4">`). `.pub-source` link underlined.

## 22. Media list — `media_list`

`<time class="media-date" datetime="2008-05-19">19 May 2008</time>` (body face, `--fs-sm`, amber,
7.5rem minimum), outlet, "quoted title" (link underlined; `lang="fr"` on French titles; sr-only
"(in French, opens in a new tab)"). Unknown date: "—" (`aria-hidden`) + sr-only "Date unknown:".
`.media-note`: `--fs-sm`, left rule.

## 23. Show more (disclosure) — `disclosure` (new)

`<details class="more">` between two `--line-strong` rules; summary 48px tall, bold `--fs-lg`,
`--accent`, with a 26px circled "+" that becomes "−" when open; body padding 12px 0 24px.
Opened automatically when a link targets something inside, and before printing.

## 24. Photo gallery — `gallery` (new; "Through my lens")

`h3.subhead`, `ul.lens-grid` (site: `.gallery-grid`) labelled by it: 3 columns, 2 under 640px,
gap 12px, 4:3 `cover` images with an 8px radius, lazy-loaded; a copyright note (`--fs-sm`).
Saving discouraged: no drag, no callout, context menu blocked by script.

## 25. Footer / contact — `footer`

`footer#contact`: eyebrow "Contact" · `h2` ("Let's talk.", `--fs-5xl`) · `p.contact-lede` (46ch) ·
email and LinkedIn (mono `--fs-md`, sr-only prefixes "Email:", "LinkedIn profile:") ·
`p.footer-langs` ("Working in …", replaces the language-code pills) · `.a11y-statement` (h3 +
text with a mailto link) · `nav.legal-links` (44px links) · `p.copyright`. All footer links are
underlined. In the source the two legal texts are disclosures (`details.more.legal`, text
`--fs-ui`, 70ch) under the links; the site makes them pages.

## 26. Line icons

24×24, stroke 1.6, round caps and joins, `currentColor`: compass, document, chat, network, flask,
globe (service cards); fish, target, ballet, camera, flame (off-duty cards); new UI icon
"settings" (sun-like, stroke 1.8) on the Display settings button.
