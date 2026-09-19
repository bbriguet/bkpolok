# Structure — "Bożena Polok"

Source: shared artifact `f461231a-537c-4c98-a850-eff07e9cd3b9` (single static HTML page, English, no runtime scripts).
`<title>`: `Bożena Polok`. Language of the copy: English.

## Pages

One page only: **home** (`/`). Navigation is anchor-based (smooth scroll, `scroll-padding` not set; the nav is sticky).

## Section order

| # | Block | Element / id | Background | Nav label → anchor |
|---|---|---|---|---|
| 0 | Navigation | `<nav>` (sticky) | translucent `--bg` | — |
| 1 | Hero | `<header class="hero">` | `--bg` | — |
| 2 | About | `<section id="about">` | `--bg` | About → `#about` |
| 3 | Pull quote | `<blockquote class="pull-quote">` | `--bg` | — |
| 4 | Expertise | `<section id="services" class="tint">` | `--surface-tint` | Expertise → `#services` |
| 5 | Experience (+ Education) | `<section id="experience">` | `--bg` | Experience → `#experience` |
| 6 | Publications & Media | `<section id="publications" class="tint">` | `--surface-tint` | Publications → `#publications` |
| 7 | Personal ("Off the clock") | `<section id="personal">` | `--bg` | Personal → `#personal` |
| 8 | Contact / footer | `<footer id="contact">` | `--bg`, top hairline | Contact → `#contact` |

Backgrounds alternate `--bg` / `--surface-tint` for sections 4 and 6 (tint sections bleed to the viewport edges: `margin: 0 -20px`).
Note: the anchor is `#services` but the visible label is "Expertise".

## Heading hierarchy

- `h1` — once, in the hero: "Bożena *Polok*" (surname in italic accent colour).
- `h2` — one per section (About, Expertise, Experience, Publications & Media, Personal) and one in the footer ("Let's talk medical affairs.").
- `h3` — everything below a section title: service cards, timeline roles, offer items, off-duty cards, and sub-section titles.
- Every `h2` (except the footer's) and the sub-section `h3`s are preceded by an **eyebrow** (`<p class="eyebrow">`, mono uppercase). Eyebrows are paragraphs, not headings.

```
nav
  brand "B. Polok"
  links: About · Expertise · Experience · Publications · Personal · Contact

header.hero
  p.eyebrow        Medical Affairs Leadership — Multiple Therapeutic Areas
  h1               Bożena Polok
  p.hero-role
  p.status-badge
  p.hero-thesis
  .hero-cta        3 buttons: Get in touch (primary) · LinkedIn ↗ (ghost) · See publications (ghost)
  .iris            circular portrait inside an SVG ring (hidden ≤ 640px)

section#about
  .section-head    p.eyebrow "About" · h2
  .about-grid      4 paragraphs
  .lang-row        5 language pills (full names)
  p.lang-caption   proficiency levels

blockquote.pull-quote   quote + cite (Hippocrates)

section#services.tint
  .section-head    p.eyebrow "Expertise" · h2 · p.lede · .pill-row (7 therapeutic areas)
  .service-grid    6 × .service  (icon · h3 · p)
  .aside-note.offer-note
    p.offer-lead   (with icon)
    dl.offer-list  3 × .offer-item (dt · dd)

section#experience
  .section-head    p.eyebrow "Experience" · h2
  p.group-label    "Industry — 2011 to present"
  .timeline        5 × .tl-item   (Santen · Allergan · Sanofi · UCB · Olympus)
  p.group-label    "Research — 2000 to 2011"
  .timeline        3 entries      (CMU Geneva · BIDMC Boston · .tl-pair: IRO Sion + PhD, with 2 spanning thumbnails)
  .section-head    p.eyebrow "Education" · h3 "Research training"
  .edu-grid        2 × .edu-card

section#publications.tint
  .section-head    p.eyebrow "Publications & Media" · h2 · p.lede
  ol.pub-list      10 × .pub  (number · title · meta)
  .pub-source      link to PubMed record
  .section-head    p.eyebrow "Media" · h3 "Television"
  ul.media-list    2 items
  p.media-note
  .section-head    h3 "Press"            (no eyebrow)
  ul.media-list    2 items
  p.media-note

section#personal
  .section-head.personal-head
    p.eyebrow "Off the clock" · h2 · p.lede
    img.personal-photo   (rotated −3°)
  .off-duty-grid   5 × .off-card (icon · h3 · p); the 5th ("Mentoring") is .wide (spans 2 columns)
  .aside-row       2 × .aside-note (icon · text): GRSA ski guiding, school microscopy sessions

footer#contact
  .footer-grid
    p.eyebrow "Contact" · h2 · mailto link · LinkedIn link
    .lang-row      5 pills (PL FR EN DE IT)
  p.copyright

script[type="application/ld+json"]   schema.org Person (name, jobTitle, employer, email, sameAs, languages, alumniOf, description)
```

## Anchors / cross-links

- `#pub-02` (publication 02) is linked from the two research thumbnails ("FIG. 1", "FIG. 5", Kotkamp et al., 2014).
- Hero CTAs: `#contact`, `#publications`, plus external LinkedIn.
- External links use `target="_blank" rel="noopener"`.

## Images (embedded as base64 in the source, not extracted here)

| Where | Alt text |
|---|---|
| Hero portrait (204 × 204, circular) | Portrait of Bożena Polok |
| Olympus timeline item (84 × 84) | Olympus IXplore SpinSR spinning-disk confocal super-resolution microscope system |
| PhD thumbnail "FIG. 1" (76 × 76, `object-position: 50% 20%`) | Whole-mount in situ hybridization of zebrafish myc-family genes in wildtype and Pou5f1-deficient embryos at 60% epiboly |
| PhD thumbnail "FIG. 5" (76 × 76, `object-position: 20% 50%`) | Morphological analysis of mych knockdown and mRNA rescue in zebrafish embryos and larvae |
| Personal photo (294 × 294, circular, rotated) | Bożena Polok |

Decorative SVGs (`aria-hidden`): hero ring (viewBox 168, two circles + 4 tick marks) and one 24×24 line icon per service / off-card / aside note.

## Responsive behaviour

Single fluid column, max width 840px, 20px side gutter. See `tokens.css` header for breakpoints. Key changes: hero and personal head go to one column at 640px (hero ring hidden), 3-column grids fall to 2 then 1, timeline photos move above their text on narrow screens.

## Theming

Light by default, dark via `prefers-color-scheme` or `data-theme="dark"|"light"` on `<html>`. No theme toggle is present in the page.
