# bkpolok — Site architecture

How the design in `_artifact/design/` is implemented. Written 2026-09-20.

## Pages (URLs)

Created as **unpublished drafts** by `python manage.py create_site_pages` (idempotent; also
`apps.pages.services.create_site_pages`). Publish each one in the Wagtail admin once it has content.

| URL | Type | Notes |
|---|---|---|
| `/` | `HomePage` | hero, quote, cards, call to action |
| `/about/` | `StandardPage` | |
| `/expertise/` | `ServiceIndexPage` | lists its live `ServicePage` children automatically |
| `/expertise/medical-affairs-consulting/` `…/patient-programs-advocacy/` `…/coaching/` | `ServicePage` | the three offers; `summary` allows 600 characters |
| `/experience/` | `StandardPage` | timeline + education blocks |
| `/publications/` | `StandardPage` | publication + media blocks |
| `/personal/` | `StandardPage` | card grid ("off the clock" layout) + aside notes |
| `/contact/` | `ContactPage` | page fields override the site profile |

The nav lists live, "show in menus" pages under the home page, in tree order; the label is the page title.

## Data (`apps/profile`)

Site setting **Site profile** (name, short name, legal name, job title, employer, email, LinkedIn,
PubMed URL, publications page, footer heading, meta description) and snippets under the admin menu
**Profile**: Experience (+ achievements, images), Publication, Education, Media appearance, Language.
Logic lives in `apps/profile/services.py` (periods such as `DEC 2022 — PRESENT`, group labels
derived from the data, language caption, JSON-LD). Publications and media use an explicit
`sort_order`; the number shown beside a paper follows it.

## Blocks (`apps/pages/blocks.py`, `apps/profile/blocks.py`)

Editorial: hero, section heading (eyebrow, lede, pills, round photo), rich text, image, pull quote,
call to action, card grid (service / off-duty), aside notes (1 or 2), service offers, FAQ, and a
**Section** wrapper (anchor + default/tinted background). Dynamic (filled from the models):
timeline, education, publication list, media list, languages.
Icons come from the fixed set in `apps/pages/icons.py` (`{% icon "name" %}`).

## Front end

`static/css/tokens.css` (design tokens, light/dark) → `fonts.css` (self-hosted Fraunces, Source Sans 3,
IBM Plex Mono, latin + latin-ext, OFL licences in `static/fonts/LICENSES.txt`) → `site.css` (uses only
tokens; a test enforces it). Wagtail wraps each stream block in `<div class="block-<type>">`; the CSS
relies on that.

## Language and formats

`LANGUAGE_CODE = "en"`. Swiss formats are forced for the `en` locale by `config/formats/en/formats.py`
(dates `19.05.2008`, times `14:30`, numbers `1’234.50`). `USE_THOUSAND_SEPARATOR` is deliberately off
(it would print the year 2009 as `2’009`); use the `intcomma` filter for displayed quantities.

## Deviations from the design

- **Timeline pairs** (`tl-pair`, two entries sharing a photo column) are not implemented: an entry shows
  its own images beside its text.
- **Contrast**: `tokens.css` keeps the design's exact values. Light `--ink-faint` (#647268) and `--accent-2`
  (#9c5c1b) reach only 4.26:1 and 4.46:1 on `--surface-tint` (below the 4.5:1 AA threshold for small text).
- **Hero portrait** stays visible on narrow screens (smaller) instead of being hidden.
- **Icons** in aside notes get `stroke: currentColor`; the source page left them without a stroke.
- **Language caption** groups consecutive levels: "French, English & German (full professional)".
- **Footer heading** ("Let's talk…") is a site-profile field, since the footer appears on every page.
- **Anchors** in figure captions point to `<publications page>#pub-<id>` (set in the site profile).

## Not done yet (waiting for validation)

No content is imported: no profile, no experience, publication, media, language or education
records, and every page body is empty. Claims flagged in the review (career figures, product names,
quote attribution, images) are to be validated before import.
